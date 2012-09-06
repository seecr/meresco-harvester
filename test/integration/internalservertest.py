#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
## begin license ##
# 
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for 
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl 
# 
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2012 Stichting Kennisnet http://www.kennisnet.nl
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

from os import system
from utils import getRequest
from lxml.etree import tostring
from integrationtestcase import IntegrationTestCase
from meresco.harvester.namespaces import xpath

REPOSITORY = 'integrationtest'
class InternalServerTest(IntegrationTestCase):

    def setUp(self):
        IntegrationTestCase.setUp(self)
        system("rm -rf %s/*" % self.dumpDir)
        system("rm -rf %s" % self.harvesterLogDir)
        system("rm -rf %s" % self.harvesterStateDir)

    def testListInvalidRecordsForOneRepository(self):
        self.controlHelper(action='allInvalid')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/invalid', {'domainId': 'adomain', 'repositoryId': 'integrationtest'}, parse='lxml')
        self.assertEquals(['oai:record:08', 'oai:record:07', 'oai:record:05', 'oai:record:04', '\n oai:record:02/&gkn', 'oai:record:01'], result.xpath("/div/table/tr/td[@class='link']/a/text()"))
        self.assertEquals("/page/invalidRecord/?recordId=oai%3Arecord%3A08&domainId=adomain&repositoryId=integrationtest", result.xpath("/div/table/tr/td[@class='link']/a")[0].attrib['href'])
        self.assertEquals("/page/showHarvesterStatus/show?domainId=adomain&repositoryId=integrationtest", result.xpath("/div/p/a/@href")[0])

    def testViewInvalidRecordWithoutDetails(self):
        self.controlHelper(action='allInvalid')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/invalidRecord', {'domainId': 'adomain', 'repositoryId': 'integrationtest', 'recordId': '\n oai:record:02/&gkn'}, parse='lxml')
        self.assertEquals("Repository integrationtest - Record \n oai:record:02/&gkn", result.xpath("//h3/text()")[0])
        self.assertEquals("/page/invalid/?domainId=adomain&repositoryId=integrationtest", result.xpath("/div/p/a/@href")[0])
        self.assertEquals(["No error message."], result.xpath("/div/pre/text()"))

    def testViewInvalidRecord(self):
        self.controlHelper(action='allInvalid')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/invalidRecord', {'domainId': 'adomain', 'repositoryId': 'integrationtest', 'recordId': 'oai:record:01'}, parse='lxml')
        self.assertEquals("Repository integrationtest - Record oai:record:01", result.xpath("//h3/text()")[0])
        self.assertEquals("/page/invalid/?domainId=adomain&repositoryId=integrationtest", result.xpath("/div/p/a/@href")[0])
        self.assertEquals(["Invalid data"], result.xpath("/div/pre/text()"))

    def testGetStatusForDomainAndRepositoryId(self):
        self.controlHelper(action='allInvalid')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/get', {'verb': 'GetStatus', 'domainId': 'adomain', 'repositoryId': 'integrationtest'}, parse='lxml')
        self.assertEquals("GetStatus", xpath(result, "/status:saharaget/status:request/status:verb/text()")[0])
        self.assertEquals("adomain", xpath(result, "/status:saharaget/status:request/status:domainId/text()")[0])
        self.assertEquals("integrationtest", xpath(result, "/status:saharaget/status:request/status:repositoryId/text()")[0])
        self.assertEquals("IntegrationTest", xpath(result, "/status:saharaget/status:GetStatus/status:status/@repositoryGroupId")[0])
        self.assertEquals("6", xpath(result, "/status:saharaget/status:GetStatus/status:status[@repositoryId='integrationtest']/status:invalid/text()")[0])
        
    def testGetStatusForDomain(self):
        self.controlHelper(action='allInvalid')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/get', {'verb': 'GetStatus', 'domainId': 'adomain'}, parse='lxml')
        self.assertEquals(2, len(xpath(result, "/status:saharaget/status:GetStatus/status:status")))
        self.assertEquals("adomain", xpath(result, "/status:saharaget/status:request/status:domainId/text()")[0])

    def testGetStatusForDomainAndRepositoryGroup(self):
        self.controlHelper(action='allInvalid')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/get', {'verb': 'GetStatus', 'domainId': 'adomain', 'repositoryGroupId': 'IntegrationTest'}, parse='lxml')
        self.assertEquals(1, len(xpath(result, "/status:saharaget/status:GetStatus/status:status")))
        self.assertEquals("adomain", xpath(result, "/status:saharaget/status:request/status:domainId/text()")[0])
        self.assertEquals("IntegrationTest", xpath(result, "/status:saharaget/status:request/status:repositoryGroupId/text()")[0])

    def testGetRepositoriesForDomain(self):
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/get', {'verb': 'GetRepositories', 'domainId': 'adomain'}, parse='lxml')
        self.assertEquals(2, len(xpath(result, "/status:saharaget/status:GetRepositories/status:repository")))
        self.assertEquals(['integrationtest', 'repository2'], xpath(result, "/status:saharaget/status:GetRepositories/status:repository/status:id/text()"))

    def testGetRepositoriesForDomainAndRepositoryGroup(self):
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/get', {'verb': 'GetRepositories', 'domainId': 'adomain', 'repositoryGroupId': 'IntegrationTest'}, parse='lxml')
        self.assertEquals(1, len(xpath(result, "/status:saharaget/status:GetRepositories/status:repository")))
        self.assertEquals(["integrationtest"], xpath(result, "/status:saharaget/status:GetRepositories/status:repository/status:id/text()"))

    def testGetRepository(self):
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/get', {'verb': 'GetRepository', 'domainId': 'adomain', 'repositoryId': 'integrationtest'}, parse='lxml')
        self.assertEquals(['IntegrationTest'], xpath(result, "/status:saharaget/status:GetRepository/status:repository/status:repositoryGroupId/text()"))

    def testRssForHarvesterStatus(self):
        self.controlHelper(action="noneInvalid")
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/rss', {'domainId': 'adomain', 'repositoryId': 'integrationtest'}, parse='lxml')
        self.assertEquals("Harvester status voor integrationtest", xpath(result, "/rss/channel/title/text()")[0])
        self.assertEquals("Recente repository harvest status voor integrationtest in adomain", xpath(result, "/rss/channel/description/text()")[0])
        self.assertEquals("http://localhost:9999/harvesterStatus.page?domainId=adomain&repositoryId=integrationtest", xpath(result, "/rss/channel/link/text()")[0])
        self.assertEquals(str(60 * 6), xpath(result, "/rss/channel/ttl/text()")[0])

        self.assertEquals("Harvester status voor integrationtest", xpath(result, "/rss/channel/item[1]/title/text()")[0])
        description = xpath(result, "/rss/channel/item[1]/description/text()")[0]
        self.assertTrue("Last harvest date: " in description, description)
        self.assertTrue("Total records: 8" in description, description)
        self.assertTrue("Harvested records: 10" in description, description)
        self.assertTrue("Uploaded records: 8" in description, description)
        self.assertTrue("Deleted records: 2" in description, description)
        self.assertTrue("Validation errors: 0" in description, description)
        self.assertTrue("Errors: 0" in description, description)
        self.assertEquals("http://localhost:9999/harvesterStatus.page?domainId=adomain&repositoryId=integrationtest", xpath(result, "/rss/channel/item[1]/link/text()")[0])

    def testRssForNeverHarvestedRepository(self):
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/rss', {'domainId': 'adomain', 'repositoryId': 'repository2'}, parse='lxml')
        self.assertEquals("Harvester status voor repository2", xpath(result, "/rss/channel/title/text()")[0])
        self.assertEquals(0, len(xpath(result, "/rss/channel/item")))

