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
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from project import settings


urlpatterns = [
    url(r'^login/$', views.signIn, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login',
        name='logout'),
    url(r'^profile/(?P<userArg>\w{0,50})/$', views.profile, name='profile'),
    url(r'^register/$', views.register, name='register'),
    url(r'^confirm-registration/(?P<username>[a-zA-Z0-9_@\+\-]+)/(?P<token>[a-z0-9\-]+)$',
        views.confirm_registration, name='confirm'),
    url(r'^about/$', views.about, name='about'),
    url(r'^calendar/$', views.viewCalendar, name='calendar'),
    url(r'checkAuth', views.checkAuth, name='checkAuth'),
    url(r'oauth2callback', views.auth_return, name='oauth2return'),
    url(r'^$', views.home, name='main'),
    url(r'^json-test/$', views.testAppForm, name='json_test'),
    url(r'^', views.home),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()
