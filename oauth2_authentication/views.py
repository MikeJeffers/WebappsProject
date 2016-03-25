# Based on code provided by :
# http://www.marinamele.com/use-the-google-analytics-api-with-django
# https://developers.google.com/api-client-library/python/guide/django
# using google python api library:
# https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/index.html

import os
import httplib2
from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.django_orm import Storage

from apiclient.discovery import build

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse

from .models import CredentialsModel, FlowModel

from framework.views import viewCalendar

CLIENT_SECRETS = os.path.join(
    os.path.dirname(__file__), 'client_secrets.json')


def get_accounts_ids(service):
    accounts = service.management().accounts().list().execute()
    ids = []
    if accounts.get('items'):
        for account in accounts['items']:
            ids.append(account['id'])
    return ids


@login_required
def index(request):
    REDIRECT_URI = "http://%s%s" % (request.get_host(),
                                    reverse("oauth2:return"))
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
        return viewCalendar(request, service)


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
    return HttpResponseRedirect("/oauth2")
