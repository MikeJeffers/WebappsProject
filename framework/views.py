from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.db import transaction
from django.contrib.auth.decorators import login_required
from forms import RegisterForm, SignInForm
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from mimetypes import guess_type
from django.core import serializers
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from models import CalendarUser
import jsonschema
from appForms import convertJsonToForm
# s3
from s3 import s3_upload

# google OAuthStuff
import os
import httplib2
from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.django_orm import Storage
from apiclient.discovery import build
from django.conf import settings

from .models import CredentialsModel, FlowModel
import datetime

CLIENT_SECRETS = os.path.join(
    os.path.dirname(__file__), 'client_secrets.json')

# Create your views here


def home(request):
    context = {}
    context['errors'] = []
    context['messages'] = []
    context['user'] = request.user
    return render(request, 'main.html', context)


@login_required
def viewCalendar(request):
    context = {}
    context['errors'] = []
    context['messages'] = []
    context['events'] = []
    context['user'] = request.user
    service = checkAuth(request)
    if isinstance(service, HttpResponse):
        return service
    #now = datetime.datetime.utcnow().isoformat() + 'Z'
    now = datetime.datetime.utcnow()
    now = now.replace(day=1, hour=0, minute=0)
    now = now.isoformat() + "Z"
    print now

    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=100, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    if not events:
        context['errors'].append("no events to show!")
        return render(request, 'main.html', context)
    for event in events:
        start = event['start'].get(
            'dateTime', event['start'].get('date'))
        print(start, event['summary'])
        context['events'].append(start + " " + event['summary'])
    return render(request, 'main.html', context)


@login_required
def getEventsJSON(request):
    checkAuth(request)
    pass


def get_accounts_ids(service):
    accounts = service.management().accounts().list().execute()
    ids = []
    if accounts.get('items'):
        for account in accounts['items']:
            ids.append(account['id'])
    return ids


@login_required
def checkAuth(request):
    """
    checks the OAuth of the requesting user
    if user has not allowed app access to their google account calendar,
    this will redirect them to do so
    then will return Google API Service object to be queried
    """
    REDIRECT_URI = "http://%s%s" % (request.get_host(),
                                    reverse("oauth2return"))
    FLOW = flow_from_clientsecrets(
        CLIENT_SECRETS,
        scope='https://www.googleapis.com/auth/calendar.readonly',
        redirect_uri=REDIRECT_URI
    )
    user = request.user
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    credential = storage.get()
    if credential is None or credential.invalid is True:
        FLOW.params['state'] = xsrfutil.generate_token(
            settings.SECRET_KEY, user)
        authorize_url = FLOW.step1_get_authorize_url()
        f = FlowModel(id=user, flow=FLOW)
        f.save()
        return HttpResponseRedirect(authorize_url)
    else:
        http = httplib2.Http()
        http = credential.authorize(http)
        service = build('calendar', 'v3', http=http)
        return service


@login_required
def auth_return(request):
    user = request.user
    if not xsrfutil.validate_token(
            settings.SECRET_KEY, request.GET['state'], user):
        return HttpResponseBadRequest()
    FLOW = FlowModel.objects.get(id=user).flow
    credential = FLOW.step2_exchange(request.GET)
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    storage.put(credential)
    return HttpResponseRedirect(reverse('checkAuth'))


def about(request):
    context = {}
    context['errors'] = []
    context['messages'] = []
    context['user'] = request.user
    return render(request, 'about.html', context)


def signIn(request):
    context = {}
    if (request.method == "GET"):
        context['form'] = SignInForm()
        return render(request, 'login.html', context)

    form = SignInForm(request.POST)
    if (not form.is_valid()):
        context['form'] = form
        return render(request, 'login.html', context)

    login(request, form.user)
    return redirect(reverse('main'))


@login_required
def profile(request, userArg):
    context = {}
    context['errors'] = []
    try:
        userMatch = User.objects.get(username__exact=userArg)
    except ObjectDoesNotExist:
        context['errors'].append("could not find object")
        return render(request, 'main.html', context)
    except MultipleObjectsReturned:
        context['errors'].append("multiple objects returned")
        return render(request, 'main.html', context)
    context['author'] = userArg
    context['firstname'] = userMatch.first_name
    context['lastname'] = userMatch.last_name
    try:
        profMatch = CalendarUser.objects.get(user=userMatch)
    except ObjectDoesNotExist:
        context['errors'].append("You dont have a profile yet!")
        return redirect(reverse("editprofile"))
    except MultipleObjectsReturned:
        context['errors'].append("multiple objects returned")
        return render(request, 'main.html', context)
    # These fields are not yet in CalendarUser
    # TODO?
    #context['bio'] = profMatch.bio
    #context['age'] = profMatch.age
    context['profile'] = profMatch
    return render(request, 'profile.html', context)


@transaction.atomic
def register(request):
    context = {}
    context['errors'] = []
    context['messages'] = []
    if request.method == 'GET':
        context['form'] = RegisterForm()
        return render(request, 'registration.html', context)
    form = RegisterForm(request.POST)
    context['form'] = form

    if not form.is_valid():
        return render(request, 'registration.html', context)

    registeredUser = User.objects.create_user(username=form.cleaned_data['username'],
                                              password=form.cleaned_data[
                                                  'password1'],
                                              first_name=form.cleaned_data[
                                                  'first_name'],
                                              last_name=form.cleaned_data[
                                                  'last_name'],
                                              email=form.cleaned_data['email'])

    registeredUser.backend = 'django.contrib.auth.backends.ModelBackend'
    registeredUser.is_active = False

    registeredUser.save()
    newUserProfile = CalendarUser.objects.create(user=registeredUser)
    newUserProfile.save()

    token = default_token_generator.make_token(registeredUser)
    email_body = """
    Please click the link below to
    verify your email address and complete the registration of your account:
    http://%s%s VERIFY!""" % (request.get_host(), reverse('confirm', args=(registeredUser.username, token)))
    if False:
        send_mail(subject="Verify your email address",
                  message=email_body,
                  from_email="placeholder@email.com",
                  recipient_list=[registeredUser.email])
    else:
        context['messages'].append(email_body)
        context['link'] = "http://%s%s" % (
            request.get_host(), reverse('confirm', args=(registeredUser.username, token)))

    context['email'] = form.cleaned_data['email']
    context['errors'].append("Needs confirmation!")
    return render(request, 'main.html', context)


@transaction.atomic
def confirm_registration(request, username, token):
    user = get_object_or_404(User, username=username)

    # Send 404 error if token is invalid
    if not default_token_generator.check_token(user, token):
        raise Http404

    # Otherwise token was valid, activate the user.
    user.is_active = True
    user.save()
    return render(request, 'main.html', {'errors': ["confirmed!"]})


def testAppForm(request):
    context = {}
    context['form_errors'] = []
    context['generated_form'] = ''

    if request.method == 'GET':
        context['json_string'] = '{\n\
  "fields": [\n\
                 {"type": "boolean", "name": "field1", "required": true, "default": true},\n\
                 {"type": "boolean", "name": "field2", "required": true, "default": false},\n\
                 {"type": "text", "name": "field3", "required": false, "default": "Hello"},\n\
                 {"type": "choice", "name": "field4", "required": true, "choices": ["1", "2", "3"], "default": "2"}, \n\
                 {"type": "date", "name": "field5", "required": true, "default": "05/27/1994"},\n\
                 {"type": "time", "name": "field6", "required": true, "default": "05:27"},\n\
                 {"type": "number", "name": "field7", "required": true, "default": 27} \n\
  ]\n\
}'
        return render(request, 'form-generator.html', context)

    json_string = request.POST.get('json_string', '')
    context['json_string'] = json_string

    try:
        context['generated_form'] = convertJsonToForm(json_string)
    except ValueError:
        context['form_errors'].append("Invalid JSON!")
    except jsonschema.ValidationError:
        context['form_errors'].append("JSON does not follow schema!")

    return render(request, 'form-generator.html', context)
