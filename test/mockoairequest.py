## begin license ##
# 
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for 
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl 
# 
# Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
# 
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

from slowfoot import binderytools
from os.path import join
from urllib import urlencode

from meresco.harvester.oairequest import OaiRequest

class MockOaiRequest(OaiRequest):
    def __init__(self, url):
        OaiRequest.__init__(self,url)
        self._createMapping()
        
    def _request(self, argslist):
        filename = self.findFile(argslist)
        return binderytools.bind_file(filename)

    def findFile(self, argslist):
        argslist.sort()
        return self._mapping[urlencode(argslist)]
        
    def _createMapping(self):
        f = open(join(self._url, 'mapping.txt'), 'r')
        self._mapping = {}
        while 1:
            request = f.readline().strip()
            responsefile = f.readline().strip()
            if not request or not responsefile:
                break
            self._mapping[request] = join(self._url, responsefile)
        
