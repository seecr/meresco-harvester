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

from utils import getRequest

from integrationtestcase import IntegrationTestCase

def xpath(node, xpath):
    return node.xpath(xpath, namespaces={'s': 'http://sahara.cq2.org/xsd/saharaget.xsd'})

class PortalTest(IntegrationTestCase):

    def testListAllRepositories(self):
        header, result = getRequest(self.harvesterPortalPortNumber, '/index.html', {'domainId': 'integrationtest'}, parse=False)
        self.assertTrue("""<a href="/repository?domain=integrationtest&repositoryId=integrationtest">integrationtest</a>""" in result, result)

    def testGetStatus(self):
        self.startHarvester()
        header, result = getRequest(self.harvesterPortalPortNumber, '/getStatus', {'domainId': 'adomain', 'repositoryId': 'integrationtest'}, parse='lxml')
        self.assertEquals("GetStatus", xpath(result, "/s:saharaget/s:request/s:verb/text()")[0])
        self.assertEquals("adomain", xpath(result, "/s:saharaget/s:request/s:domainId/text()")[0])
        self.assertEquals("integrationtest", xpath(result, "/s:saharaget/s:request/s:repositoryId/text()")[0])
        self.assertEquals("5", xpath(result, "/s:saharaget/s:GetStatus/s:status[@repositoryId='integrationtest']/s:ignored/text()")[0])
        

