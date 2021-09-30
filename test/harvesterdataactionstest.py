## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2015, 2019-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2015, 2019-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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
from urllib.parse import urlencode

bUrlencode = lambda *args, **kwargs: urlencode(*args, **kwargs).encode()

class HarvesterDataActionsTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.hd = HarvesterData(self.tempdir)
        self.hd.addDomain('domain')
        self.hd.addRepositoryGroup('group', domainId='domain')
        self.hd.addRepository('repository', repositoryGroupId='group', domainId='domain')
        self.hda = HarvesterDataActions(fieldDefinitions={'repository_fields':[
                {'name': 'name', 'label':'Label', 'type':'text', 'export': False},
                {'name': 'choice_1', 'label':'Keuze', 'type':'bool', 'export': False},
                {'name': 'choice_2', 'label':'Keuze', 'type':'bool', 'export': False},
            ]})
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
            "continuous": "60",
            "repositoryAction": "clear",
            "numberOfTimeslots": "0",
            "extra_name": "Name for this object",
            "extra_choice_1": '1',
        }
        consume(self.hda.handleRequest(Method='POST', path='/somewhere/updateRepository', Body=bUrlencode(data, doseq=True)))
        repository = self.hd.getRepository('repository', 'domain')
        self.assertEqual('group', repository["repositoryGroupId"])
        self.assertEqual("repository", repository["identifier"])
        self.assertEqual("http://example.org/oai", repository["baseurl"])
        self.assertEqual("ASET", repository["set"])
        self.assertEqual("oai_dc", repository["metadataPrefix"])
        self.assertEqual("mapping_identifier", repository["mappingId"])
        self.assertEqual(None, repository["targetId"])
        self.assertEqual("the collection", repository["collection"])
        self.assertEqual(23, repository["maximumIgnore"])
        self.assertEqual(True, repository["complete"])
        self.assertEqual(60, repository["continuous"])
        self.assertEqual(False, repository["use"])
        self.assertEqual("clear", repository["action"])
        self.assertEqual([], repository['shopclosed'])
        self.assertEqual({
            "name": "Name for this object",
            "choice_1": True,
            "choice_2": False
            }, repository['extra'])

    def testMinimalInfo(self):
        data = {
            'redirectUri': 'http://example.org',
            "repositoryGroupId": "ignored",
            "identifier": "repository",
            "domainId": "domain",
        }
        consume(self.hda.handleRequest(Method='POST', path='/somewhere/updateRepository', Body=bUrlencode(data, doseq=True)))
        repository = self.hd.getRepository('repository', 'domain')
        self.assertEqual('group', repository["repositoryGroupId"])
        self.assertEqual("repository", repository["identifier"])
        self.assertEqual(None, repository["baseurl"])
        self.assertEqual(None, repository["set"])
        self.assertEqual(None, repository["metadataPrefix"])
        self.assertEqual(None, repository["mappingId"])
        self.assertEqual(None, repository["targetId"])
        self.assertEqual(None, repository["collection"])
        self.assertEqual(0, repository["maximumIgnore"])
        self.assertEqual(None, repository["continuous"])
        self.assertEqual(False, repository["complete"])
        self.assertEqual(False, repository["use"])
        self.assertEqual(None, repository["action"])
        self.assertEqual([], repository['shopclosed'])

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
        consume(self.hda.handleRequest(Method='POST', path='/somewhere/updateRepository', Body=bUrlencode(data, doseq=True)))
        repository = self.hd.getRepository('repository', 'domain')
        self.assertEqual([], repository['shopclosed'])

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
        consume(self.hda.handleRequest(Method='POST', path='/somewhere/updateRepository', Body=bUrlencode(data, doseq=True)))
        repository = self.hd.getRepository('repository', 'domain')
        self.assertEqual(['*:*:7:0-*:*:9:0'], repository['shopclosed'])

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
        consume(self.hda.handleRequest(Method='POST', path='/somewhere/updateRepository', Body=bUrlencode(data, doseq=True)))
        repository = self.hd.getRepository('repository', 'domain')
        self.assertEqual(['3:*:17:0-3:*:19:0', '4:5:9:0-4:5:10:0',], repository['shopclosed'])

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
        consume(self.hda.handleRequest(Method='POST', path='/somewhere/updateRepository', Body=bUrlencode(data, doseq=True)))
        repository = self.hd.getRepository('repository', 'domain')
        self.assertEqual(['4:5:9:0-4:5:10:0',], repository['shopclosed'])

    def testSetRepositoryDone(self):
        self.updateTheRepository(action='refresh')
        repository = self.hd.getRepository('repository', 'domain')
        self.assertEqual('refresh', repository['action'])

        data = dict(domainId='domain', identifier='repository')
        consume(self.hda.handleRequest(Method='POST', path='/somewhere/repositoryDone', Body=bUrlencode(data, doseq=True)))
        repository = self.hd.getRepository('repository', 'domain')
        self.assertEqual(None, repository['action'])

    def updateTheRepository(self, baseurl='', set='', metadataPrefix='', mappingId='', targetId='', collection='', maximumIgnore=0, use=False, continuous=False, complete=True, action='', shopclosed=None):
        self.hd.updateRepository('repository', domainId='domain',
            baseurl=baseurl,
            set=set,
            metadataPrefix=metadataPrefix,
            mappingId=mappingId,
            targetId=targetId,
            collection=collection,
            maximumIgnore=maximumIgnore,
            use=use,
            continuous=continuous,
            complete=complete,
            action=action,
            shopclosed=shopclosed or [],
            userAgent='',
            authorizationKey='',
        )


