## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
#
# This file is part of "Meresco Harvester"
#
# "Meresco Harvester" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Harvester" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Harvester"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from meresco.components.http.utils import redirectHttp
from meresco.html import PostActions
from urllib import urlencode
from urlparse import parse_qs, urlparse
from functools import partial

class HarvesterDataActions(PostActions):

    def __init__(self, **kwargs):
        PostActions.__init__(self, **kwargs)
        self._register('addDomain', self._addDomain)
        self._register('updateDomain', self._updateDomain)
        self._register('addRepositoryGroup', self._addRepositoryGroup)
        self._register('deleteRepositoryGroup', self._deleteRepositoryGroup)
        self._register('updateRepositoryGroup', self._updateRepositoryGroup)

    def _addDomain(self, identifier, arguments):
        self.call.addDomain(identifier=identifier)

    def _updateDomain(self, identifier, arguments):
        self.call.updateDomain(
                identifier=identifier,
                description=arguments.get('description', [''])[0],
            )

    def _addRepositoryGroup(self, identifier, arguments):
        self.call.addRepositoryGroup(
                identifier=identifier,
                domainId=arguments.get('domainId', [''])[0],
            )

    def _updateRepositoryGroup(self, identifier, arguments):
        self.call.updateRepositoryGroup(
                identifier=identifier,
                domainId=arguments.get('domainId', [''])[0],
                name={
                    'nl': arguments.get('nl_name', [''])[0],
                    'en': arguments.get('en_name', [''])[0],
                },
            )

    def _deleteRepositoryGroup(self, identifier, arguments):
        self.call.deleteRepositoryGroup(
                identifier=identifier,
                domainId=arguments.get('domainId', [''])[0],
            )

    def _register(self, name, actionMethod):
        self.registerAction(name, partial(self._do, actionMethod=actionMethod))

    def _do(self, actionMethod, Body, **kwargs):
        arguments = parse_qs(Body)
        identifier = arguments.pop('identifier', [None])[0]
        referer = arguments.pop('referer', ['/error'])[0]
        redirectUri = arguments.pop('redirectUri', ['/'])[0]
        try:
            actionMethod(identifier=identifier, arguments=arguments)
        except ValueError, e:
            return redirectHttp % self._link(referer, error=str(e))
        return redirectHttp % self._link(redirectUri, identifier=identifier)

    def _link(self, link, **kwargs):
        u = urlparse(link)
        args = parse_qs(u.query)
        if 'identifier' in args:
            kwargs.pop('identifier', None)
        args.update(kwargs)
        return '{0.path}?{1}'.format(u, urlencode(args, doseq=True))