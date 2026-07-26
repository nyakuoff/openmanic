#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic.test_supporter_restrictions_removed.py

    Written by:               Openmanic
    Date:                     26 Jul 2026

    Copyright:
           Copyright (C) Josh Sunnex - All Rights Reserved

           Permission is hereby granted, free of charge, to any person obtaining a copy
           of this software and associated documentation files (the "Software"), to deal
           in the Software without restriction, including without limitation the rights
           to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
           copies of the Software, and to permit persons to whom the Software is
           furnished to do so, subject to the following conditions:

           The above copyright notice and this permission notice shall be included in all
           copies or substantial portions of the Software.

           THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
           EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
           MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
           IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
           DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
           OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
           OR OTHER DEALINGS IN THE SOFTWARE.

    This test suite proves that Openmanic's locally-enforced Unmanic supporter-tier
    restrictions (library count limits, linked installation limits, and plugin-setting
    "req_lev" gating) have been removed, and that checking those limits no longer
    contacts the Unmanic-operated supporter-validation API.

"""
import tempfile
from unittest.mock import patch, MagicMock

import pytest


@pytest.mark.unittest
class TestLibraryCountLimitsRemoved:

    def test_within_library_count_limits_always_true(self):
        from unmanic.libs.library import Library
        assert Library.within_library_count_limits() is True

    def test_within_library_count_limits_does_not_touch_session(self):
        from unmanic.libs.library import Library
        with patch("unmanic.libs.session.Session.__init__", side_effect=AssertionError(
                "Session should not be instantiated by within_library_count_limits")):
            assert Library.within_library_count_limits() is True


@pytest.mark.unittest
class TestInstallationLinkLimitsRemoved:

    def test_within_enabled_link_limits_always_true(self):
        from unmanic.libs.installation_link import Links
        # Bypass __init__ (which builds config/session objects we don't need for this check)
        links = Links.__new__(Links)
        assert links.within_enabled_link_limits() is True

    def test_within_enabled_link_limits_does_not_touch_session(self):
        from unmanic.libs.installation_link import Links
        links = Links.__new__(Links)
        with patch("unmanic.libs.session.Session.__init__", side_effect=AssertionError(
                "Session should not be instantiated by within_enabled_link_limits")):
            assert links.within_enabled_link_limits() is True


def _make_fake_plugin_module(req_lev=5, default_value="default_value"):
    """
    Build a minimal fake plugin module with a Settings class declaring one
    setting gated behind a supporter "req_lev", for exercising the plugin
    settings save/read code paths without needing a real plugin on disk.
    """
    saved = {}

    class FakeSettings:
        def __init__(self, *args, **kwargs):
            self.library_id = kwargs.get('library_id')

        def get_form_settings(self):
            return {
                'my_option': {
                    'label':       'My Option',
                    'description': 'A setting reserved for supporters',
                    'req_lev':     req_lev,
                }
            }

        def set_setting(self, key, value):
            saved[key] = value
            return True

        def get_default_setting(self, key=None):
            return default_value

    module = MagicMock()
    module.Settings = FakeSettings
    return module, saved


@pytest.mark.unittest
class TestPluginSettingsSupporterGateRemoved:

    def test_save_plugin_settings_keeps_submitted_value(self):
        from unmanic.libs.unplugins.executor import PluginExecutor

        fake_module, saved = _make_fake_plugin_module(req_lev=5)

        plugins_directory = tempfile.mkdtemp(prefix='openmanic_tests_plugins_')
        executor = PluginExecutor(plugins_directory=plugins_directory)

        with patch.object(PluginExecutor, "_PluginExecutor__load_plugin_module", return_value=fake_module), \
             patch("unmanic.libs.session.Session.__init__", side_effect=AssertionError(
                 "Session should not be instantiated by save_plugin_settings")):
            result = executor.save_plugin_settings('test_plugin', {'my_option': 'user_submitted_value'})

        assert result is True
        # The submitted value must be saved as-is - not silently reset to the
        # plugin's default because the (removed) supporter level check failed.
        assert saved.get('my_option') == 'user_submitted_value'


@pytest.mark.unittest
class TestPluginSettingsFormNotDisabledForSupporters:

    def test_get_plugin_settings_form_field_not_disabled(self):
        from unmanic.webserver.helpers import plugins as plugins_helper
        from unmanic.libs.unplugins.executor import PluginExecutor

        req_lev_settings = {'my_option': 'user_submitted_value'}
        req_lev_meta = {'my_option': {'req_lev': 5, 'label': 'My Option', 'description': 'desc'}}

        with patch.object(PluginExecutor, "get_plugin_settings", return_value=(req_lev_settings, req_lev_meta)), \
             patch("unmanic.libs.session.Session.__init__", side_effect=AssertionError(
                 "Session should not be instantiated by get_plugin_settings")):
            form_settings = plugins_helper.get_plugin_settings('test_plugin')

        my_option = next(f for f in form_settings if f['key'] == 'my_option')
        assert my_option['display'] == 'visible'
        assert 'reserved for supporters' not in my_option['description']


@pytest.mark.unittest
class TestNoOutboundSupporterValidationCallsDuringNormalUse:
    """
    Proves that the four supporter-gate code paths exercised above never reach out
    to the Unmanic-operated supporter-validation API (api.unmanic.app) during normal
    local operation, by making any outbound HTTP request raise if attempted.
    """

    def test_gate_checks_never_perform_http_requests(self):
        import requests
        from unmanic.libs.library import Library
        from unmanic.libs.installation_link import Links

        def _fail(*args, **kwargs):
            raise AssertionError("No outbound HTTP request should be made during normal supporter-gate checks")

        with patch.object(requests.Session, "get", side_effect=_fail), \
             patch.object(requests.Session, "post", side_effect=_fail):
            assert Library.within_library_count_limits() is True
            links = Links.__new__(Links)
            assert links.within_enabled_link_limits() is True
