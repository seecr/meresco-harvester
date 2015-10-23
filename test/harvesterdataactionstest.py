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
from meresco.harvester.harvesterdataactions import HarvesterDataActions
from meresco.harvester.harvesterdata import HarvesterData
from weightless.core import consume
from urllib import urlencode

class HarvesterDataActionsTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.hd = HarvesterData(self.tempdir)
        self.hd.addDomain('domain')
        self.hd.addRepositoryGroup('group', domainId='domain')
        self.hd.addRepository('repository', repositoryGroupId='group', domainId='domain')
        self.hda = HarvesterDataActions()
        self.hda.addObserver(self.hd)

    def testUpdateRepository(self):
        data = {
            'redirectUri': 'http://example.org',
            "repositoryGroupId": "ignored",
            "identifier": "repository",
            "domainId": "domain",
            "baseurl": "http://example.org/oai",
            "set": "ASET",
            "metadataPrefix": "oai_dc",
            "mappingId": "mapping_identifier",
            "targetId": "",
            "collection": "the collection",
            "maximumIgnore": "23",
            "complete": "1",
            "repositoryAction": "clear",
            "numberOfTimeslots": "0"
        }
        consume(self.hda.handleRequest(Method='POST', path='/somewhere/updateRepository', Body=urlencode(data, doseq=True)))
        repository = self.hd.getRepository('repository', 'domain')
        self.assertEquals('group', repository["repositoryGroupId"])
        self.assertEquals("repository", repository["identifier"])
        self.assertEquals("http://example.org/oai", repository["baseurl"])
        self.assertEquals("ASET", repository["set"])
        self.assertEquals("oai_dc", repository["metadataPrefix"])
        self.assertEquals("mapping_identifier", repository["mappingId"])
        self.assertEquals("", repository["targetId"])
        self.assertEquals("the collection", repository["collection"])
        self.assertEquals(23, repository["maximumIgnore"])
        self.assertEquals(True, repository["complete"])
        self.assertEquals(False, repository["use"])
        self.assertEquals("clear", repository["action"])
        self.assertEquals([], repository['shopclosed'])

    def testMinimalInfo(self):
        data = {
            'redirectUri': 'http://example.org',
            "repositoryGroupId": "ignored",
            "identifier": "repository",
            "domainId": "domain",
        }
        consume(self.hda.handleRequest(Method='POST', path='/somewhere/updateRepository', Body=urlencode(data, doseq=True)))
        repository = self.hd.getRepository('repository', 'domain')
        self.assertEquals('group', repository["repositoryGroupId"])
        self.assertEquals("repository", repository["identifier"])
        self.assertEquals('', repository["baseurl"])
        self.assertEquals("", repository["set"])
        self.assertEquals("", repository["metadataPrefix"])
        self.assertEquals("", repository["mappingId"])
        self.assertEquals("", repository["targetId"])
        self.assertEquals("", repository["collection"])
        self.assertEquals(0, repository["maximumIgnore"])
        self.assertEquals(False, repository["complete"])
        self.assertEquals(False, repository["use"])
        self.assertEquals("", repository["action"])
        self.assertEquals([], repository['shopclosed'])

    def testShopClosedButNotAdded(self):
        data = {
            'redirectUri': 'http://example.org',
            "repositoryGroupId": "ignored",
            "identifier": "repository",
            "domainId": "domain",
            "numberOfTimeslots": "0",
            'shopclosedWeek_0': '*',
            'shopclosedWeekDay_0': '*',
            'shopclosedBegin_0': '7',
            'shopclosedEnd_0': '9',
        }
        consume(self.hda.handleRequest(Method='POST', path='/somewhere/updateRepository', Body=urlencode(data, doseq=True)))
        repository = self.hd.getRepository('repository', 'domain')
        self.assertEquals([], repository['shopclosed'])

    def testShopClosedAdded(self):
        data = {
            'redirectUri': 'http://example.org',
            "repositoryGroupId": "ignored",
            "identifier": "repository",
            "domainId": "domain",
            "numberOfTimeslots": "0",
            'shopclosedWeek_0': '*',
            'shopclosedWeekDay_0': '*',
            'shopclosedBegin_0': '7',
            'shopclosedEnd_0': '9',
            "addTimeslot": "button pressed",
        }
        consume(self.hda.handleRequest(Method='POST', path='/somewhere/updateRepository', Body=urlencode(data, doseq=True)))
        repository = self.hd.getRepository('repository', 'domain')
        self.assertEquals(['*:*:7:0-*:*:9:0'], repository['shopclosed'])

    def testModifyShopClosed(self):
        self.updateTheRepository(shopclosed=['1:2:7:0-1:2:9:0', '2:*:7:0-2:*:9:0',])
        data = {
            'redirectUri': 'http://example.org',
            "repositoryGroupId": "ignored",
            "identifier": "repository",
            "domainId": "domain",
            "numberOfTimeslots": "2",
            'shopclosedWeek_0': '*',
            'shopclosedWeekDay_0': '*',
            'shopclosedBegin_0': '7',
            'shopclosedEnd_0': '9',
            'shopclosedWeek_1': '3',
            'shopclosedWeekDay_1': '*',
            'shopclosedBegin_1': '17',
            'shopclosedEnd_1': '19',
            'shopclosedWeek_2': '4',
            'shopclosedWeekDay_2': '5',
            'shopclosedBegin_2': '9',
            'shopclosedEnd_2': '10',
        }
        consume(self.hda.handleRequest(Method='POST', path='/somewhere/updateRepository', Body=urlencode(data, doseq=True)))
        repository = self.hd.getRepository('repository', 'domain')
        self.assertEquals(['3:*:17:0-3:*:19:0', '4:5:9:0-4:5:10:0',], repository['shopclosed'])

    def testDeleteShopClosed(self):
        self.updateTheRepository(shopclosed=['1:2:7:0-1:2:9:0', '2:*:7:0-2:*:9:0',])
        data = {
            'redirectUri': 'http://example.org',
            "repositoryGroupId": "ignored",
            "identifier": "repository",
            "domainId": "domain",
            "numberOfTimeslots": "2",
            'shopclosedWeek_0': '*',
            'shopclosedWeekDay_0': '*',
            'shopclosedBegin_0': '7',
            'shopclosedEnd_0': '9',
            'shopclosedWeek_1': '3',
            'shopclosedWeekDay_1': '*',
            'shopclosedBegin_1': '17',
            'shopclosedEnd_1': '19',
            'shopclosedWeek_2': '4',
            'shopclosedWeekDay_2': '5',
            'shopclosedBegin_2': '9',
            'shopclosedEnd_2': '10',
            'deleteTimeslot_1.x': '10',
            'deleteTimeslot_1.y': '20',
        }
        consume(self.hda.handleRequest(Method='POST', path='/somewhere/updateRepository', Body=urlencode(data, doseq=True)))
        repository = self.hd.getRepository('repository', 'domain')
        self.assertEquals(['4:5:9:0-4:5:10:0',], repository['shopclosed'])


    def updateTheRepository(self, baseurl='', set='', metadataPrefix='', mappingId='', targetId='', collection='', maximumIgnore=0, use=False, complete=True, action='', shopclosed=None):
        self.hd.updateRepository('repository', domainId='domain',
            baseurl=baseurl,
            set=set,
            metadataPrefix=metadataPrefix,
            mappingId=mappingId,
            targetId=targetId,
            collection=collection,
            maximumIgnore=maximumIgnore,
            use=use,
            complete=complete,
            action=action,
            shopclosed=shopclosed or []
        )

