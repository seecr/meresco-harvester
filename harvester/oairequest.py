#!/usr/bin/env python
## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for 
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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
#
# Copyright (C) 2005 Seek You Too B.V. http://www.cq2.nl
#
# $Id: oairequest.py 4825 2007-04-16 13:36:24Z TJ $

from cq2utils import binderytools
from urllib import urlencode, urlopen
import os
from cq2utils.wrappers import wrapp

class OAIError(Exception):
    def code(self):
        error = self.args[0]
        return getattr(error,'code','')

class OAIRequest:
    def __init__(self, url):
        self._url = url

    def listRecords(self, **args):
        if args.has_key('from_'):
            args['from']=args['from_']
            del args['from_']
        args['verb']='ListRecords'
        response = self.request(args)
        if not hasattr(response.OAI_PMH,'ListRecords'):
            error = OAIError(getattr(response.OAI_PMH,'error','Unknown Error.'))
            if error.code() != 'noRecordsMatch':
                raise error
        return wrapp(response.OAI_PMH).ListRecords.record
        
    def getRecord(self, **args):
        args['verb'] = 'GetRecord'
        response = self.request(args)
        if not hasattr(response.OAI_PMH,'GetRecord'):
            raise OAIError(getattr(response.OAI_PMH,'error','Unknown Error.'))
        return wrapp(response.OAI_PMH.GetRecord.record)
        
    def identify(self):
        response = self.request({'verb':'Identify'})
        return wrapp(response.OAI_PMH.Identify)
    
    def request(self, args):
        return self._request(filter(lambda (k,v):v,args.items()))
    
    def _request(self, argslist):
        return binderytools.bind_uri(self._url + '?' + urlencode(argslist))
    
class LoggingOAIRequest(OAIRequest):
    def __init__(self, url, tempdir):
        OAIRequest.__init__(self, url)
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
        requesturl = binderytools.Uri.MakeUrllibSafe(self._url + '?' + urlencode(argslist))
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
    
class MockOAIRequest(OAIRequest):
    def __init__(self, url):
        OAIRequest.__init__(self,url)
        self._createMapping()
        
    def _request(self, argslist):
        filename = self.findFile(argslist)
        return binderytools.bind_file(filename)

    def findFile(self, argslist):
        argslist.sort()
        return self._mapping[urlencode(argslist)]
        
    def _createMapping(self):
        f = open(os.path.join(self._url, 'mapping.txt'), 'r')
        self._mapping = {}
        while 1:
            request = f.readline().strip()
            responsefile = f.readline().strip()
            if not request or not responsefile:
                break
            self._mapping[request] = os.path.join(self._url, responsefile)
        
def loggingListRecords(url, tempdir, **args):
    """loggingListRecords(url, tempdir, **listRecordsArgs"""
    loair = LoggingOAIRequest(url, tempdir)
    listRecords = loair.listRecords(**args)
    resumptionToken = str(listRecords.parentNode.resumptionToken)
    print resumptionToken
    while resumptionToken:
        listRecords = loair.listRecords(resumptionToken=resumptionToken)
        resumptionToken = str(listRecords.parentNode.resumptionToken)
        print resumptionToken
    
        
