## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2015, 2017 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2015 Stichting Kennisnet http://www.kennisnet.nl
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

from urllib import urlencode
from urlparse import parse_qs, urlparse
from functools import partial

from meresco.components.http.utils import redirectHttp, badRequestHtml, Ok
from meresco.html import PostActions

from meresco.harvester.timeslot import Timeslot


class HarvesterDataActions(PostActions):
    def __init__(self, **kwargs):
        PostActions.__init__(self, **kwargs)
        self._registerFormAction('addDomain', self._addDomain)
        self._registerFormAction('updateDomain', self._updateDomain)
        self._registerFormAction('addRepositoryGroup', self._addRepositoryGroup)
        self._registerFormAction('deleteRepositoryGroup', self._deleteRepositoryGroup)
        self._registerFormAction('updateRepositoryGroup', self._updateRepositoryGroup)
        self._registerFormAction('addRepository', self._addRepository)
        self._registerFormAction('deleteRepository', self._deleteRepository)
        self._registerFormAction('updateRepository', self._updateRepository)
        self._registerFormAction('addMapping', self._addMapping)
        self._registerFormAction('updateMapping', self._updateMapping)
        self._registerFormAction('deleteMapping', self._deleteMapping)
        self._registerFormAction('addTarget', self._addTarget)
        self._registerFormAction('updateTarget', self._updateTarget)
        self._registerFormAction('deleteTarget', self._deleteTarget)
        self.registerAction('repositoryDone', self._repositoryDone)
        self.defaultAction(lambda path, **kwargs: badRequestHtml + "Invalid action: " + path)

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

    def _addRepository(self, identifier, arguments):
        self.call.addRepository(
                identifier=identifier,
                domainId=arguments.get('domainId', [''])[0],
                repositoryGroupId=arguments.get('repositoryGroupId', [''])[0],
            )

    def _updateRepository(self, identifier, arguments):
        shopclosed = []
        shopStart = 0 if 'addTimeslot' in arguments else 1
        shopEnd = 1 + int(arguments.get('numberOfTimeslots', [''])[0] or '0')
        for i in xrange(shopStart, shopEnd):
            if arguments.get('deleteTimeslot_%s.x' % i, [None])[0]:
                continue
            shopclosed.append(str(Timeslot('{week}:{weekday}:{begin}:00-{week}:{weekday}:{end}:00'.format(
                    week=arguments.get('shopclosedWeek_%s' % i, ['*'])[0],
                    weekday=arguments.get('shopclosedWeekDay_%s' % i, ['*'])[0],
                    begin=arguments.get('shopclosedBegin_%s' % i, ['*'])[0],
                    end=arguments.get('shopclosedEnd_%s' % i, ['*'])[0],
                ))))

        self.call.updateRepository(
                identifier=identifier,
                domainId=arguments['domainId'][0],
                baseurl=arguments.get('baseurl', [None])[0],
                set=arguments.get('set', [None])[0],
                metadataPrefix=arguments.get('metadataPrefix', [None])[0],
                mappingId=arguments.get('mappingId', [None])[0],
                targetId=arguments.get('targetId', [None])[0],
                collection=arguments.get('collection', [None])[0],
                maximumIgnore=int(arguments.get('maximumIgnore', [None])[0] or '0'),
                use='use' in arguments,
                continuous=int(arguments.get('continuous', ['0'])[0]) or None,
                complete='complete' in arguments,
                action=arguments.get('repositoryAction', [None])[0],
                shopclosed=shopclosed,
            )

    def _deleteRepository(self, identifier, arguments):
        self.call.deleteRepository(
                identifier=identifier,
                domainId=arguments.get('domainId', [''])[0],
                repositoryGroupId=arguments.get('repositoryGroupId', [''])[0],
            )

    def _addMapping(self, arguments, **ignored):
        return self.call.addMapping(
                name=arguments.get('name', [''])[0],
                domainId=arguments.get('domainId', [''])[0],
            )

    def _updateMapping(self, identifier, arguments):
        self.call.updateMapping(
                identifier=identifier,
                name=arguments.get('name', [''])[0],
                description=arguments.get('description', [''])[0],
                code=arguments.get('code', [''])[0].replace('\r', ''),
            )

    def _deleteMapping(self, identifier, arguments):
        self.call.deleteMapping(
                identifier=identifier,
                domainId=arguments.get('domainId', [''])[0],
            )

    def _addTarget(self, arguments, **ignored):
        return self.call.addTarget(
                name=arguments.get('name', [''])[0],
                domainId=arguments.get('domainId', [''])[0],
                targetType=arguments.get('targetType', [''])[0],
            )

    def _updateTarget(self, identifier, arguments):
        self.call.updateTarget(
                identifier=identifier,
                name=arguments.get('name', [''])[0],
                username=arguments.get('username', [''])[0],
                port=int(arguments.get('port', [''])[0] or '0'),
                targetType=arguments.get('targetType', [''])[0],
                path=arguments.get('path', [''])[0],
                baseurl=arguments.get('baseurl', [''])[0],
                oaiEnvelope='oaiEnvelope' in arguments,
                delegateIds=arguments.get('delegate',[]),
            )

    def _deleteTarget(self, identifier, arguments):
        self.call.deleteTarget(
                identifier=identifier,
                domainId=arguments.get('domainId', [''])[0],
            )

    def _repositoryDone(self, Body, **kwargs):
        arguments = parse_qs(Body)
        identifier = arguments.pop('identifier', [None])[0]
        domainId = arguments.pop('domainId', [None])[0]
        self.call.repositoryDone(identifier=identifier, domainId=domainId)
        yield Ok

    def _registerFormAction(self, name, actionMethod):
        self.registerAction(name, partial(self._do, actionMethod=actionMethod))

    def _do(self, actionMethod, Body, **kwargs):
        arguments = parse_qs(Body)
        identifier = arguments.pop('identifier', [None])[0]
        referer = arguments.pop('referer', ['/error'])[0]
        redirectUri = arguments.pop('redirectUri', ['/'])[0]
        try:
            result = actionMethod(identifier=identifier, arguments=arguments)
        except ValueError, e:
            return redirectHttp % self._link(referer, error=str(e))
        return redirectHttp % self._link(redirectUri, identifier=identifier or result)

    def _link(self, link, **kwargs):
        u = urlparse(link)
        args = parse_qs(u.query)
        if 'identifier' in args:
            kwargs.pop('identifier', None)
        args.update(kwargs)
        return '{0.path}?{1}'.format(u, urlencode(args, doseq=True))