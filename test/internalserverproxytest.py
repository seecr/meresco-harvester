## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import SeecrTestCase
from meresco.components.json import JsonDict
from meresco.harvester.internalserverproxy import InternalServerProxy
from StringIO import StringIO

class InternalServerProxyTest(SeecrTestCase):

    def setUp(self):
        SeecrTestCase.setUp(self)
        self.proxy = InternalServerProxy("http://localhost")
        self.requests = []
        def _urlopen(url, data=None):
            if data:
                self.requests.append((url, data))
            else:
                self.requests.append(url)
            return StringIO(JsonDict(self.response).dumps())
        self.proxy._urlopen = _urlopen

    def testGetRepository(self):
        self.response = {
                'request': {'verb': 'GetRepository'},
                'response': {'GetRepository': {
                    'identifier': 'repo1',
                    'use': True,
                    'complete': False,
                }}
            }
        repoDict = self.proxy.getRepository(identifier='repo1', domainId='domainId')
        self.assertEqual('http://localhost/get?verb=GetRepository&identifier=repo1&domainId=domainId', self.requests[0])
        repo = self.proxy.getRepositoryObject(identifier='repo1', domainId='domainId')
        self.assertEqual(self.requests[0], self.requests[-1])
        self.assertEqual({'complete': False, 'identifier': 'repo1', 'use': True}, repoDict)
        self.assertEqual('repo1', repo.id)
        self.assertFalse(repo.complete)
        self.assertTrue(repo.use)

    def testGetStatus(self):
        self.response = {'response': {'GetStatus': '?'}}
        self.proxy.getStatus(domainId='domainId')
        self.assertEqual('http://localhost/get?verb=GetStatus&domainId=domainId', self.requests[0])

    def testErrorInResponse(self):
        self.response = {'request': {'verb': 'getUnknown'}, 'error': {'code': 'badVerb', 'message': 'Bad verb'}}
        try:
            self.proxy.getStatus(domainId='domainId')
            self.fail()
        except ValueError, e:
            self.assertEqual('Bad verb', str(e))

    def testSetActionDone(self):
        self.response = {}
        self.proxy.repositoryActionDone(domainId='adomain', repositoryId='repo1')
        self.assertEqual(('http://localhost/action/repositoryDone', 'domainId=adomain&identifier=repo1'), self.requests[0])