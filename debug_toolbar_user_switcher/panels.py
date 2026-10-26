"""
:mod:`django-debug-toolbar-user-panel`
======================================

Panel for the `Django Debug Toolbar <https://github.com/jazzband/django-debug-toolbar>`_
to easily and quickly switch between users.

 * View details on the currently logged in user.
 * Login as any user from an arbitrary email address, username or user ID.
 * Easily switch between recently logged in users.

Installation
------------

Add ``debug_toolbar_user_switcher`` to your ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        ...
        'debug_toolbar_user_switcher',
        ...
    )

Add ``debug_toolbar_user_switcher.panels.UserPanel`` to ``DEBUG_TOOLBAR_PANELS``::

    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar_user_switcher.panels.UserPanel'
        'debug_toolbar.panels.version.VersionDebugPanel',
        'debug_toolbar.panels.timer.TimerDebugPanel',
        'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
        'debug_toolbar.panels.headers.HeaderDebugPanel',
        'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
        'debug_toolbar.panels.sql.SQLDebugPanel',
        'debug_toolbar.panels.template.TemplateDebugPanel',
        'debug_toolbar.panels.signals.SignalDebugPanel',
        'debug_toolbar.panels.logger.LoggingPanel',
    )

"""

from django import VERSION
from django.conf import settings
from django.http import HttpResponseForbidden
from django.urls import path
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from django.contrib.auth import get_user_model

from debug_toolbar.panels import Panel

from . import views
from .forms import UserForm


class UserPanel(Panel):
    """
    Panel that allows you to login as other recently-logged in users.
    """

    name = "User"
    has_content = True
    template = "debug_toolbar_user_switcher/panel.html"

    @property
    def nav_title(self):
        return _("User")

    @property
    def url(self):
        return ""

    @property
    def title(self):
        return _("User")

    @property
    def nav_subtitle(self):
        return self.get_stats().get("username", "")

    @property
    def content(self):
        if not getattr(settings, "DEBUG_TOOLBAR_USER_DEBUG", settings.DEBUG):
            return HttpResponseForbidden()

        return render_to_string(
            self.template, {**self.get_stats(), "form": UserForm()}
        )

    def generate_stats(self, request, response):
        user = request.user
        current = []

        if user.is_authenticated:
            for field in get_user_model()._meta.fields:
                if field.name == "password":
                    continue
                current.append((field.attname, str(getattr(user, field.attname))))

        self.record_stats(
            {
                "is_authenticated": user.is_authenticated,
                "username": str(user) if user.is_authenticated else "",
                "current": current,
                "next": request.GET.get("next"),
                "users": [
                    (str(u.pk), str(u))
                    for u in get_user_model().objects.order_by("-last_login")[:20]
                ],
            }
        )

    @classmethod
    def get_urls(cls):
        return (
            path("users/login/", views.login_form, name="debug-userpanel-login-form"),
            path(
                "users/login/<uuid:pk>",
                views.login,
                name="debug-userpanel-login",
            ),
            path("users/logout", views.logout, name="debug-userpanel-logout"),
        )
