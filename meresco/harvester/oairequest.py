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
# Copyright (C) 2011-2013 Seecr (Seek You Too B.V.) http://seecr.nl
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

import os
from urllib import urlencode, urlopen
from urlparse import urlparse, urlunparse
from cgi import parse_qsl 

from slowfoot import binderytools
from slowfoot.wrappers import wrapp
from meresco.harvester.namespaces import xpathFirst, xpath


class OaiRequestException(Exception):
    def __init__(self, url, message):
        Exception.__init__(self, 'occurred with repository at "%s", message: "%s"' % (url, message))
        self.url = url


class OAIError(OaiRequestException):
    def __init__(self, url, error, errorCode):
        OaiRequestException.__init__(self, url, error)
        self.errorMessage = lambda: error
        self.errorCode = lambda: errorCode

    @classmethod
    def create(cls, url, response):
        error = xpathFirst(response, '/oai:OAI-PMH/oai:error/text()')
        errorCode = xpathFirst(response, '/oai:OAI-PMH/oai:error/@code')
        return cls(url=url,
                error='Unknown error' if error is None else str(error),
                errorCode='' if errorCode is None else str(errorCode),
            )

QUERY_POSITION_WITHIN_URLPARSE_RESULT=4

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
            response = self.request(kwargs)
        except OAIError, e:
            if e.errorCode() != 'noRecordsMatch':
                raise e
            response = e.response
        listRecords = xpathFirst(response, '/oai:OAI-PMH/oai:ListRecords')
        return xpath(listRecords, 'oai:record'), xpathFirst(listRecords, 'oai:resumptionToken/text()'), xpathFirst(response, '/oai:OAI-PMH/oai:responseDate/text()').strip()

    def getRecord(self, **kwargs):
        kwargs['verb'] = 'GetRecord'
        response = self.request(kwargs)
        return wrapp(response).OAI_PMH.GetRecord.record
    
    def identify(self):
        response = self.request({'verb':'Identify'})
        return wrapp(response.OAI_PMH.Identify)
    
    def request(self, args):
        try:
            argslist = [(k,v) for k,v in args.items() if v]
            result = self._request(argslist)
        except Exception, e:
            raise OaiRequestException(self._buildRequestUrl(argslist), message=repr(e))
        if xpathFirst(result, '/oai:OAI-PMH/oai:error') is not None:
            raise OAIError.create(self._buildRequestUrl(argslist), result)
        return result
    
    def _request(self, argslist):
        return binderytools.bind_uri(self._buildRequestUrl(argslist))
    
    def _buildRequestUrl(self, argslist):
        """Builds the url from the repository's base url + query parameters.
            Special case (not actually allowed by OAI-PMH specification): if query parameters 
            occur in the baseurl, they are kept. Origin: Rijksmuseum OAI-PMH repository insists 
            on 'apikey' query parameter to go with ListRecords."""
        urlElements = list(self._urlElements)
        urlElements[QUERY_POSITION_WITHIN_URLPARSE_RESULT] = urlencode(self._argslist + argslist)
        return urlunparse(urlElements)


class LoggingOaiRequest(OaiRequest):
    def __init__(self, url, tempdir):
        OaiRequest.__init__(self, url)
        self.tempdir = tempdir
        self.numberfilename = os.path.join(self.tempdir, 'number')
        
    def getNumber(self):
        number = os.path.isfile(self.numberfilename) and int(open(self.numberfilename).read()) or 0
        try:
            return str(number)
        finally:
            number += 1
            f = open(self.numberfilename, 'w')
            f.write(str(number))
            f.close()
        
    def _request(self, argslist):
        requesturl = binderytools.Uri.MakeUrllibSafe(self._buildRequestUrl(argslist))
        filename = os.path.join(self.tempdir, 'oairequest.' + self.getNumber() + '.xml')
        opened = urlopen(requesturl)
        writefile = file(filename, 'w')
        try:
            for l in opened:
                writefile.write(l)
        finally:
            opened.close()
            writefile.close()
        return binderytools.bind_file(filename)


def loggingListRecords(url, tempdir, **kwargs):
    """loggingListRecords(url, tempdir, **listRecordsArgs)"""
    loair = LoggingOaiRequest(url, tempdir)
    listRecords = loair.listRecords(**kwargs)
    resumptionToken = str(listRecords.parentNode.resumptionToken)
    print resumptionToken
    while resumptionToken:
        listRecords = loair.listRecords(resumptionToken=resumptionToken)
        resumptionToken = str(listRecords.parentNode.resumptionToken)
        print resumptionToken

