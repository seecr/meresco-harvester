#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
#
#    This file is part of "Meresco Harvester"
#
#    "Meresco Harvester" is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    "Meresco Harvester" is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with "Meresco Harvester"; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from os import system
from utils import getRequest
from lxml.etree import tostring
from integrationtestcase import IntegrationTestCase

def xpath(node, xpath):
    return node.xpath(xpath, namespaces={'s': 'http://sahara.cq2.org/xsd/saharaget.xsd'})

REPOSITORY = 'integrationtest'
class InternalServerTest(IntegrationTestCase):

    def setUp(self):
        IntegrationTestCase.setUp(self)
        system("rm -rf %s/*" % self.dumpDir)
        system("rm -rf %s" % self.harvesterLogDir)
        system("rm -rf %s" % self.harvesterStateDir)

    def testListIgnoredRecordsForOneRepository(self):
        self.controlHelper(action='ignoreAll')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/ignored', {'domainId': 'adomain', 'repositoryId': 'integrationtest'}, parse='lxml')
        self.assertEquals(['oai:record:07', 'oai:record:05', 'oai:record:04', 'oai:record:02', 'oai:record:01'], result.xpath("/div/table/tr/td[@class='link']/a/text()"))
        self.assertEquals("/page/ignoredRecord/?recordId=oai%3Arecord%3A07&domainId=adomain&repositoryId=integrationtest", result.xpath("/div/table/tr/td[@class='link']/a")[0].attrib['href'])
        self.assertEquals("/page/showHarvesterStatus/show?domainId=adomain&repositoryId=integrationtest", result.xpath("/div/p/a/@href")[0])

    def testViewIgnoredRecord(self):
        self.controlHelper(action='ignoreAll')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/ignoredRecord', {'domainId': 'adomain', 'repositoryId': 'integrationtest', 'recordId': 'oai:record:02'}, parse='lxml')
        self.assertEquals("Repository integrationtest - Record oai:record:02", result.xpath("//h3/text()")[0])
        self.assertEquals("/page/ignored/?domainId=adomain&repositoryId=integrationtest", result.xpath("/div/p/a/@href")[0])

    def testGetStatusForDomainAndRepositoryId(self):
        self.controlHelper(action='ignoreAll')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/getStatus', {'domainId': 'adomain', 'repositoryId': 'integrationtest'}, parse='lxml')
        self.assertEquals("GetStatus", xpath(result, "/s:saharaget/s:request/s:verb/text()")[0])
        self.assertEquals("adomain", xpath(result, "/s:saharaget/s:request/s:domainId/text()")[0])
        self.assertEquals("integrationtest", xpath(result, "/s:saharaget/s:request/s:repositoryId/text()")[0])
        self.assertEquals("IntegrationTest", xpath(result, "/s:saharaget/s:GetStatus/s:status/@repositoryGroupId")[0])
        self.assertEquals("5", xpath(result, "/s:saharaget/s:GetStatus/s:status[@repositoryId='integrationtest']/s:ignored/text()")[0])
        
    def testGetStatusForDomain(self):
        self.controlHelper(action='ignoreAll')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/getStatus', {'domainId': 'adomain'}, parse='lxml')
        self.assertEquals(2, len(xpath(result, "/s:saharaget/s:GetStatus/s:status")))
        self.assertEquals("adomain", xpath(result, "/s:saharaget/s:request/s:domainId/text()")[0])

    def testGetStatusForDomainAndRepositoryGroup(self):
        self.controlHelper(action='ignoreAll')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/getStatus', {'domainId': 'adomain', 'repositoryGroupId': 'IntegrationTest'}, parse='lxml')
        self.assertEquals(1, len(xpath(result, "/s:saharaget/s:GetStatus/s:status")))
        self.assertEquals("adomain", xpath(result, "/s:saharaget/s:request/s:domainId/text()")[0])
        self.assertEquals("IntegrationTest", xpath(result, "/s:saharaget/s:request/s:repositoryGroupId/text()")[0])

