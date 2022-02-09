## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
# Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2011-2014, 2017, 2019-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2011-2012, 2019-2021 Stichting Kennisnet https://www.kennisnet.nl
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

from seecr.test import SeecrTestCase, CallTrace

from lxml.etree import parse, XML

from meresco.harvester import VERSION
from meresco.harvester.namespaces import xpathFirst, namespaces
from meresco.harvester.oairequest import OaiRequest, OAIError, OaiResponse

from mockoairequest import MockOaiRequest
from io import StringIO

class OaiRequestTest(SeecrTestCase):
    def setUp(self):
        super(OaiRequestTest, self).setUp()
        self.request = MockOaiRequest('mocktud')

    def testUserAgentDefault(self):
        args = {}
        def myOwnUrlOpen(*fArgs, **fKwargs):
            args['args'] = fArgs
            args['kwargs'] = fKwargs
            return StringIO(oaiResponseXML())

        request = OaiRequest("http://harvest.me", _urlopen=myOwnUrlOpen)
        request.identify()

        self.assertEqual("Meresco Harvester {}".format(VERSION), args['args'][0].headers['User-agent'])

    def testHeaders(self):
        self.assertEqual({"User-Agent": "Meresco Harvester {}".format(VERSION)},
                OaiRequest('http://example.com')._headers())
        self.assertEqual({"User-Agent": "User Agent 3.0"},
                OaiRequest('http://example.com', userAgent="User Agent 3.0")._headers())
        self.assertEqual({"User-Agent": "Meresco Harvester {}".format(VERSION)},
                OaiRequest('http://example.com', userAgent='')._headers())
        self.assertEqual({"User-Agent": "Meresco Harvester {}".format(VERSION)},
                OaiRequest('http://example.com', userAgent=' ')._headers())
        self.assertEqual({"User-Agent": "Meresco Harvester {}".format(VERSION),
                "Authorization": "Bearer GivenKey"},
                OaiRequest('http://example.com', authorizationKey='GivenKey')._headers())

    def testContextSetToTLS12(self):
        from ssl import SSLError, PROTOCOL_TLSv1_2
        calls = []
        def loggingUrlOpen(*fArgs, **fKwargs):
            calls.append(fKwargs)
            raise SSLError("Some error")
        request = OaiRequest("http://harvest.me", _urlopen=loggingUrlOpen)
        try:
            request.identify()
            self.fail("Should have failed")
        except:
            pass
        self.assertEqual(2, len(calls))
        self.assertEqual(None, calls[0]['context'])
        context=calls[1]['context']
        self.assertEqual(PROTOCOL_TLSv1_2, context.protocol)



    def testMockOaiRequest(self):
        response = self.request.request({'verb': 'ListRecords', 'metadataPrefix': 'oai_dc'})
        self.assertEqual('2004-12-29T13:19:27Z', xpathFirst(response.response, '/oai:OAI-PMH/oai:responseDate/text()'))

    def testOtherOaiRequest(self):
        response = self.request.request({'verb': 'GetRecord', 'metadataPrefix': 'oai_dc', 'identifier': 'oai:rep:12345'})
        self.assertEqual('2005-04-28T12:16:27Z', xpathFirst(response.response, '/oai:OAI-PMH/oai:responseDate/text()'))

    def testListRecordsError(self):
        try:
            self.request.listRecords(resumptionToken='BadResumptionToken')
            self.fail()
        except OAIError as e:
            self.assertEqual('The value of the resumptionToken argument is invalid or expired.',e.errorMessage())
            self.assertEqual('badResumptionToken', e.errorCode())

    def testListRecords(self):
        response = self.request.listRecords(metadataPrefix='oai_dc')
        self.assertEqual("TestToken", response.resumptionToken)
        self.assertEqual("2004-12-29T13:19:27Z", response.responseDate)
        self.assertEqual(3, len(response.records))
        self.assertEqual('oai:tudelft.nl:007087', xpathFirst(response.records[0], 'oai:header/oai:identifier/text()'))
        self.assertEqual(None, xpathFirst(response.records[0], 'oai:header/@status'))

    def mockRequest(self, args):
        self.mockRequest_args = args
        with open('mocktud/00001.xml') as fp:
            return parse(fp)

    def testListRecordArgs(self):
        self.request._request = self.mockRequest

        self.request.listRecords(metadataPrefix='kaas')
        kwargs = dict(self.mockRequest_args)
        self.assertEqual('kaas', kwargs['metadataPrefix'])
        self.assertTrue('resumptionToken' not in kwargs)
        self.assertEqual(('verb', 'ListRecords'), self.mockRequest_args[0])

        self.request.listRecords(from_='from', until='until',set='set', metadataPrefix='prefix')
        kwargs = dict(self.mockRequest_args)
        self.assertEqual(('verb', 'ListRecords'), self.mockRequest_args[0])
        self.assertEqual('from', kwargs['from'])
        self.assertEqual('until', kwargs['until'])
        self.assertEqual('set', kwargs['set'])
        self.assertEqual('prefix', kwargs['metadataPrefix'])

    def testGetRecord(self):
        response = self.request.getRecord(identifier='oai:rep:12345', metadataPrefix='oai_dc')
        self.assertEqual('oai:rep:12345', xpathFirst(response.record, 'oai:header/oai:identifier/text()'))

    def testListRecordsWithAnEmptyList(self):
        response = self.request.listRecords(resumptionToken='EmptyListToken')
        self.assertEqual(0, len(response.records))
        self.assertEqual("", response.resumptionToken)
        self.assertEqual("2005-01-12T14:34:49Z", response.responseDate)

    def testBuildRequestUrl(self):
        oaiRequest = OaiRequest("http://x.y.z/oai")
        self.assertEqual("http://x.y.z/oai?verb=ListRecords&metadataPrefix=oai_dc", oaiRequest._buildRequestUrl([('verb', 'ListRecords'), ('metadataPrefix', 'oai_dc')]))

        oaiRequest = OaiRequest("http://x.y.z/oai?apikey=xyz123")
        self.assertEqual("http://x.y.z/oai?apikey=xyz123&verb=ListRecords&metadataPrefix=oai_dc", oaiRequest._buildRequestUrl([('verb', 'ListRecords'), ('metadataPrefix', 'oai_dc')]))

    def testShouldUseOwnClockTimeAsResponseDateIfNonePresent(self):
        originalZuluMethod = OaiResponse._zulu
        OaiResponse._zulu = staticmethod(lambda: '2020-12-12T12:12:12Z')
        try:
            response = oaiResponse(responseDate='')
            self.assertEqual('2020-12-12T12:12:12Z', response.responseDate)
        finally:
            OaiResponse._zulu = originalZuluMethod

def oaiResponse(**kwargs):
    return OaiResponse(XML(oaiResponseXML(**kwargs)))

def oaiResponseXML(responseDate='2000-01-02T03:04:05Z', verb='ListRecords', identifier='oai:ident:321', deleted=False, about=None):
    about = '<about/>' if about is None else about
    return """<OAI-PMH xmlns="{namespaces.oai}"><responseDate>{responseDate}</responseDate><{verb}><record><header{statusDeleted}><identifier>{identifier}</identifier><datestamp>2005-08-29T07:08:09Z</datestamp></header>{metadata}{about}</record></{verb}></OAI-PMH>""".format(
        namespaces=namespaces,
        verb=verb,
        responseDate=responseDate,
        identifier=identifier,
        statusDeleted=' status="deleted"' if deleted else '',
        metadata='<metadata></metadata>' if not deleted else '',
        about=about if not deleted else '',
    )
