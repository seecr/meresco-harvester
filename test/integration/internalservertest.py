# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2011-2013, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2012, 2015 Stichting Kennisnet http://www.kennisnet.nl
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
from time import gmtime, strftime

from seecr.test import IntegrationTestCase
from seecr.test.utils import getRequest
from meresco.components.json import JsonDict
from meresco.harvester.namespaces import xpath
from simplejson import loads

REPOSITORY = 'integrationtest'
class InternalServerTest(IntegrationTestCase):

    def setUp(self):
        IntegrationTestCase.setUp(self)
        self.controlHelper(action='reset')
        system("rm -rf %s/*" % self.dumpDir)
        system("rm -rf %s" % self.harvesterLogDir)
        system("rm -rf %s" % self.harvesterStateDir)

    def testListInvalidRecordsForOneRepository(self):
        self.controlHelper(action='allInvalid')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/invalid', {'domainId': 'adomain', 'repositoryId': 'integrationtest'}, parse=True)
        self.assertEqual([
            'oai:record:08', 'oai:record:07',
            'oai:record:05', 'oai:record:04',
            'oai:record:02/&gkn', 'oai:record:01'],
            result.xpath("/html/body/div/table/tr/td[@class='link']/a/text()"))

        self.assertEqual("/page/invalidRecord/?recordId=oai%3Arecord%3A08&domainId=adomain&repositoryId=integrationtest", result.xpath("/html/body/div/table/tr/td[@class='link']/a")[0].attrib['href'])
        self.assertEqual("/page/showHarvesterStatus/show?domainId=adomain&repositoryId=integrationtest", result.xpath("/html/body/div/p/a/@href")[0])

    def testViewInvalidRecordWithoutDetails(self):
        self.controlHelper(action='allInvalid')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/invalidRecord', {'domainId': 'adomain', 'repositoryId': 'integrationtest', 'recordId': 'oai:record:02/&gkn'}, parse='lxml')
        self.assertEqual("Repository integrationtest - Record oai:record:02/&gkn", result.xpath("//h3/text()")[0])
        self.assertEqual("/page/invalid/?domainId=adomain&repositoryId=integrationtest", result.xpath("/html/body/div/p/a/@href")[0])
        self.assertEqual(["No error message."], result.xpath("/html/body/div/pre/text()"))

    def testViewInvalidRecord(self):
        self.controlHelper(action='allInvalid')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/invalidRecord', {'domainId': 'adomain', 'repositoryId': 'integrationtest', 'recordId': 'oai:record:01'}, parse=True)
        self.assertEqual("Repository integrationtest - Record oai:record:01", result.xpath("//h3/text()")[0])
        self.assertEqual("/page/invalid/?domainId=adomain&repositoryId=integrationtest", result.xpath("/html/body/div/p/a/@href")[0])
        self.assertEqual(["Invalid data"], result.xpath("/html/body/div/pre/text()"))

    def testGetStatusForDomainAndRepositoryId(self):
        self.controlHelper(action='allInvalid')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/get', {'verb': 'GetStatus', 'domainId': 'adomain', 'repositoryId': 'integrationtest'}, parse=False)
        data = JsonDict.loads(result)
        self.assertEqual("GetStatus", data['request']['verb'])
        self.assertEqual("adomain", data['request']['domainId'])
        self.assertEqual("integrationtest", data['request']['repositoryId'])
        self.assertEqual("IntegrationTest", data['response']['GetStatus'][0]['repositoryGroupId'])
        self.assertEqual(6, data['response']['GetStatus'][0]['invalid'])

    def testGetStatusForDomain(self):
        self.controlHelper(action='allInvalid')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/get', {'verb': 'GetStatus', 'domainId': 'adomain'}, parse=False)
        data = JsonDict.loads(result)
        self.assertEqual(2, len(data['response']['GetStatus']))
        self.assertEqual("adomain", data['request']['domainId'])

    def testGetStatusForDomainAndRepositoryGroup(self):
        self.controlHelper(action='allInvalid')
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/get', {'verb': 'GetStatus', 'domainId': 'adomain', 'repositoryGroupId': 'IntegrationTest'}, parse=False)
        data = JsonDict.loads(result)
        self.assertEqual(1, len(data['response']['GetStatus']))
        self.assertEqual("adomain", data['request']['domainId'])
        self.assertEqual("IntegrationTest", data['response']['GetStatus'][0]['repositoryGroupId'])

    def testGetDomains(self):
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/get', {'verb': 'GetDomainIds'}, parse=False)
        data = loads(result)
        self.assertEqual(1, len(data['response']['GetDomainIds']))
        self.assertEqual(['adomain'], data['response']['GetDomainIds'])

    def testGetRepositoriesForDomain(self):
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/get', {'verb': 'GetRepositories', 'domainId': 'adomain'}, parse=False)
        data = loads(result)
        self.assertEqual(2, len(data['response']['GetRepositories']))
        self.assertEqual(['integrationtest', 'repository2'], [r['identifier'] for r in data['response']['GetRepositories']])

    def testGetRepositoriesForDomainAndRepositoryGroup(self):
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/get', {'verb': 'GetRepositories', 'domainId': 'adomain', 'repositoryGroupId': 'IntegrationTest'}, parse=False)
        data = loads(result)
        self.assertEqual(1, len(data['response']['GetRepositories']))
        self.assertEqual(['integrationtest'], [r['identifier'] for r in data['response']['GetRepositories']])

    def testGetRepository(self):
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/get', {'verb': 'GetRepository', 'domainId': 'adomain', 'identifier': 'integrationtest'}, parse=False)
        data = JsonDict.loads(result)
        self.assertEqual("IntegrationTest", data['response']['GetRepository']['repositoryGroupId'])

    def testRssForHarvesterStatus(self):
        self.controlHelper(action="noneInvalid")
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/rss', {'domainId': 'adomain', 'repositoryId': 'integrationtest'}, parse='lxml')
        self.assertEqual("Harvester status voor integrationtest", xpath(result, "/rss/channel/title/text()")[0])
        self.assertEqual("Recente repository harvest status voor integrationtest in adomain", xpath(result, "/rss/channel/description/text()")[0])
        self.assertEqual("http://localhost:9999/showHarvesterStatus?domainId=adomain&repositoryId=integrationtest", xpath(result, "/rss/channel/link/text()")[0])
        self.assertEqual(str(60 * 6), xpath(result, "/rss/channel/ttl/text()")[0])

        self.assertEqual("Harvester status voor integrationtest", xpath(result, "/rss/channel/item[1]/title/text()")[0])
        description = xpath(result, "/rss/channel/item[1]/description/text()")[0]
        self.assertTrue("Last harvest date: " in description, description)
        self.assertTrue("Total records: 8" in description, description)
        self.assertTrue("Harvested records: 10" in description, description)
        self.assertTrue("Uploaded records: 8" in description, description)
        self.assertTrue("Deleted records: 2" in description, description)
        self.assertTrue("Validation errors: 0" in description, description)
        self.assertTrue("Errors: 0" in description, description)
        self.assertEqual("http://localhost:9999/showHarvesterStatus?domainId=adomain&repositoryId=integrationtest", xpath(result, "/rss/channel/item[1]/link/text()")[0])

    def testRssForNeverHarvestedRepository(self):
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/rss', {'domainId': 'adomain', 'repositoryId': 'repository2'}, parse='lxml')
        self.assertEqual("Harvester status voor repository2", xpath(result, "/rss/channel/title/text()")[0])
        self.assertEqual(0, len(xpath(result, "/rss/channel/item")))

    def testRssForStatusChangesOk(self):
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/running.rss', {'domainId': 'adomain'}, parse='lxml')
        self.assertEqual("Harvest status changes for domain 'adomain'", xpath(result, "/rss/channel/title/text()")[0])
        self.assertEqual("Status changes per repository for domain 'adomain'", xpath(result, "/rss/channel/description/text()")[0])
        self.assertEqual("http://localhost:9999/showHarvesterStatus?domainId=adomain", xpath(result, "/rss/channel/link/text()")[0])
        self.assertEqual(str(60 * 6), xpath(result, "/rss/channel/ttl/text()")[0])
        TODAY = strftime("%Y-%m-%d", gmtime())
        items = xpath(result, "/rss/channel/item")
        self.assertEqual(1, len(items))
        self.assertEqual("integrationtest: Ok", ''.join(xpath(items[0], "title/text()")))
        description = ''.join(xpath(items[0], "description/text()"))
        self.assertTrue(description.startswith("Harvest time: %s" % TODAY), description)
        self.assertEqual('integrationtest:%s' % TODAY, ''.join(xpath(items[0], "guid/text()")).split('T')[0])
        self.assertEqual("http://localhost:9999/showHarvesterStatus?domainId=adomain&repositoryId=integrationtest", xpath(items[0], "link/text()")[0])

    def testRssForStatusChangesError(self):
        self.controlHelper(action="raiseExceptionOnIds", id=['%s:oai:record:01' % REPOSITORY] )
        self.startHarvester(repository=REPOSITORY)
        header, result = getRequest(self.harvesterInternalServerPortNumber, '/running.rss', {'domainId': 'adomain'}, parse='lxml')
        TODAY = strftime("%Y-%m-%d", gmtime())
        items = xpath(result, "/rss/channel/item")
        self.assertEqual(1, len(items))
        self.assertEqual("integrationtest: Error", ''.join(xpath(items[0], "title/text()")))
        description = ''.join(xpath(items[0], "description/text()"))
        self.assertTrue(description.startswith("Harvest time: %s" % TODAY), description)
        self.assertTrue("Exception: ERROR" in description, description)
        self.assertEqual('integrationtest:%s' % TODAY, ''.join(xpath(items[0], "guid/text()")).split('T')[0])
        self.assertEqual("http://localhost:9999/showHarvesterStatus?domainId=adomain&repositoryId=integrationtest", xpath(items[0], "link/text()")[0])
