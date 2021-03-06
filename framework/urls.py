"""webapps URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^login/$', views.signIn, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login',
        name='logout'),
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^register/$', views.register, name='register'),
    url(r'^registerapp/$', views.registerApp, name='addapp'),
    url(r'^devcenter/$', views.devCenterPage, name='devcenter'),
    url(r'^deleteapp/(?P<idOfApp>\d+)/$', views.deleteApp, name='deleteapp'),
    url(r'^editapp/(?P<idOfApp>\d+)/$', views.editApp, name='editapp'),
    url(r'^editprofile/$', views.editProfile, name='editprofile'),
    url(r'^calendar/$', views.viewCalendar, name='calendar'),
    url(r'^appstore/$', views.appStore, name='appstore'),
    url(r'^editsettings/$', views.viewAppForms, name='editapp_settings'),
    url(r'^savesettings/$', views.saveSettings, name='save_settings'),
    url(r'^removeapp/$', views.removeApp, name='removeapp'),
    url(r'^revokeOAuth/$', views.removeUserOAuth, name='removeUserOAuth'),
    url(r'checkAuth', views.checkAuth, name='checkAuth'),
    url(r'oauth2callback', views.auth_return, name='oauth2return'),
    url(r'^$', views.home, name='main'),
    url(r'^json-form-gen/$', views.testAppForm, name='json_form_generator'),
    url(r'^json-test/$', views.testAppForm, name='json_test'),
    url(r'^json-events/$', views.getEventsJSON, name='json_events'),
    url(r'^form-to-json/$', views.getFormJson, name='form_to_json'),
    url(r'^json-to-form/$', views.getFormFromJson, name='json-to-form'),
    url(r'^', views.home),

]
