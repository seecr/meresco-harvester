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
# Copyright (C) 2011-2017 Seecr (Seek You Too B.V.) http://seecr.nl
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

from urllib import urlencode
from urllib2 import urlopen, install_opener, build_opener
from urlparse import urlparse, urlunparse
from cgi import parse_qsl
from httpsconnection import HTTPSHandlerTLS

from lxml.etree import parse

from seecr.zulutime import ZuluTime

from meresco.harvester.namespaces import xpathFirst, xpath


install_opener(build_opener(HTTPSHandlerTLS()))


class OaiRequest(object):
    def __init__(self, url):
        self._url = url
        self._urlElements = urlparse(url)
        self._argslist = parse_qsl(self._urlElements[QUERY_POSITION_WITHIN_URLPARSE_RESULT])

    def listRecords(self, **kwargs):
        if kwargs.has_key('from_'):
            kwargs['from'] = kwargs['from_']
            del kwargs['from_']
        kwargs['verb'] = 'ListRecords'
        try:
            return self.request(kwargs)
        except OAIError, e:
            if e.errorCode() != 'noRecordsMatch':
                raise e
            return e.response

    def getRecord(self, **kwargs):
        kwargs['verb'] = 'GetRecord'
        return self.request(kwargs)

    def identify(self):
        return self.request({'verb':'Identify'})

    def request(self, args=None):
        args = {} if args is None else args
        try:
            argslist = [(k,v) for k,v in args.items() if v]
            result = self._request(argslist)
        except Exception, e:
            raise OaiRequestException(self._buildRequestUrl(argslist), message=repr(e))
        if xpathFirst(result, '/oai:OAI-PMH/oai:error') is not None:
            raise OAIError.create(self._buildRequestUrl(argslist), OaiResponse(result))
        return OaiResponse(result)

    def _request(self, argslist):
        return parse(urlopen(self._buildRequestUrl(argslist), timeout=5*60))

    def _buildRequestUrl(self, argslist):
        """Builds the url from the repository's base url + query parameters.
            Special case (not actually allowed by OAI-PMH specification): if query parameters
            occur in the baseurl, they are kept. Origin: Rijksmuseum OAI-PMH repository insists
            on 'apikey' query parameter to go with ListRecords."""
        urlElements = list(self._urlElements)
        urlElements[QUERY_POSITION_WITHIN_URLPARSE_RESULT] = urlencode(self._argslist + argslist)
        return urlunparse(urlElements)


class OaiResponse(object):
    def __init__(self, response):
        self.response = response
        self.records = xpath(response, '/oai:OAI-PMH/oai:ListRecords/oai:record')
        self.resumptionToken = xpathFirst(response, '/oai:OAI-PMH/oai:ListRecords/oai:resumptionToken/text()') or ''
        self.responseDate = xpathFirst(response, '/oai:OAI-PMH/oai:responseDate/text()')
        if not self.responseDate is None:  # should be there, happens to be absent for some repositories
            self.responseDate = self.responseDate.strip()
        if not self.responseDate:
            self.responseDate = self._zulu()
        self.selectRecord(xpathFirst(response, '/oai:OAI-PMH/oai:*/oai:record'))

    def selectRecord(self, record):
        self.record = record

    @staticmethod
    def _zulu():
        return ZuluTime().zulu()


class OaiRequestException(Exception):
    def __init__(self, url, message):
        Exception.__init__(self, 'occurred with repository at "%s", message: "%s"' % (url, message))
        self.url = url


class OAIError(OaiRequestException):
    def __init__(self, url, error, errorCode, response):
        OaiRequestException.__init__(self, url, error)
        self.errorMessage = lambda: error
        self.errorCode = lambda: errorCode
        self.response = response

    @classmethod
    def create(cls, url, response):
        error = xpathFirst(response.response, '/oai:OAI-PMH/oai:error/text()')
        errorCode = xpathFirst(response.response, '/oai:OAI-PMH/oai:error/@code')
        return cls(url=url,
            error='Unknown error' if error is None else str(error),
            errorCode='' if errorCode is None else str(errorCode),
            response=response
        )

QUERY_POSITION_WITHIN_URLPARSE_RESULT=4
