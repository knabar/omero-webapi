#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2012 University of Dundee & Open Microscopy Environment.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import logging

from django.http import HttpResponseForbidden

import omeroweb.decorators


logger = logging.getLogger(__name__)


class login_required(omeroweb.decorators.login_required):

    def on_not_logged_in(self, request, url, error=None):
        """Called whenever the user is not logged in."""

        logger.debug("webapi: Could not log in - always 403")

        return HttpResponseForbidden()


# Use these utility decorators to use any decorator designed for classic views
# on class-based view methods.
# Example:
#
# class ViewClass(django.views.generic.View):
#     @cloak_self
#     @login_required()
#     @uncloak_self
#     def protected_view(self, request, *args, **kwargs):
#         ...

def cloak_self(function):
    def decorated(self, *args, **kwargs):
        kwargs['__self__'] = self
        return function(*args, **kwargs)
    return decorated

def uncloak_self(function):
    def decorated(*args, **kwargs):
        self = kwargs.pop('__self__', None)
        return function(self, *args, **kwargs)
    return decorated
