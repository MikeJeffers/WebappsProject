from jsonValidation import *
import os
from framework.forms import AppSettingsForm
from django import forms
from django.conf import settings
import datetime

FORM_SCHEMA_FILE = os.path.join(
    settings.PROJECT_ROOT, '../framework/static/formSchema.json')
SETTINGS_SCHEMA_FILE = os.path.join(
    settings.PROJECT_ROOT, '../framework/static/settingsSchema.json')
FORM_SCHEMA = getSchemaFromFile(FORM_SCHEMA_FILE)
SETTINGS_SCHEMA = getSchemaFromFile(SETTINGS_SCHEMA_FILE)

def createBooleanField(params):
    if 'default' in params:
        field = forms.BooleanField(required=False, initial=params['default'])
    else:
        field = forms.BooleanField(required=False)
    return field


def createTextField(params):
    if 'default' in params:
        field = forms.CharField(
            required=params['required'], initial=params['default'])
    else:
        field = forms.CharField(required=params['required'])
    return field


def createChoiceField(params):
    cs = [(c, c) for c in params['choices']]
    if 'default' in params:
        field = forms.ChoiceField(
            choices=cs, required=params['required'], initial=params['default'])
    else:
        field = forms.ChoiceField(choices=cs, required=params['required'])
    return field


def createDateField(params):
    wid = forms.TextInput(attrs={'class': 'datepicker'})
    if 'default' in params:
        date = params['default']
        dateStr = datetime.date(
            day=date['day'], month=date['month'],
            year=date['year']).strftime("%m/%d/%Y")
        field = forms.CharField(
            required=params['required'], initial=dateStr, widget=wid)
    else:
        field = forms.CharField(required=params['required'], widget=wid)
    return field


def createTimeField(params):
    wid = forms.TextInput(attrs={'class': 'timepicker'})
    if 'default' in params:
        time = params['default']
        hr = time['hour']
        if not time['am']:
            hr += 12
        dateStr = datetime.time(
            hour=hr, minute=time['minute']).strftime("%I:%M%p")
        field = forms.CharField(
            required=params['required'], initial=dateStr, widget=wid)
    else:
        field = forms.CharField(required=params['required'], widget=wid)
    return field


def createDecimalField(params):
    if 'default' in params:
        field = forms.DecimalField(
            required=params['required'], initial=params['default'])
    else:
        field = forms.DecimalField(required=params['required'])
    return field


def convertJsonToForm(jsonString, curSettings=None):
    jsonDict = validateFromString(FORM_SCHEMA, jsonString)

    fieldFuncs = {
        "boolean": createBooleanField,
        "text": createTextField,
        "choice": createChoiceField,
        "date": createDateField,
        "time": createTimeField,
        "number": createDecimalField
    }

    form = AppSettingsForm()
    form.required_css_class = 'required_field'

    for field in jsonDict['fields']:
        form.fields[field['name']] = fieldFuncs[field['type']](field)

    if curSettings:
        curSettingsDict = validateFromString(SETTINGS_SCHEMA, curSettings)
        for field in curSettingsDict:
            if field in form.fields:
                form.fields[field].initial = curSettingsDict[field]['value']

    return form


def convertRequestToJson(params, ignoreList=[]):
    jsonDict = {}
    for field in params:
        if field not in ignoreList:
            jsonChunk = {}
            jsonChunk['value'] = params[field]
            jsonDict[field] = jsonChunk

    return jsonDict
