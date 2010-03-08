## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
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

from os.path import join, isfile
from os import SEEK_END
from time import strftime, localtime
import re

class State(object):
    def __init__(self, stateDir, name):
        self._filename = join(stateDir, '%s.stats' % name)
        open(self._filename, 'a').close()
        self._statsfile = open(self._filename, 'r+')
        self._readState()
        self._prepareForWriting()

    def close(self):
        self._write('\n')
        self._statsfile.close()

    def setToLastCleanState(self):
        cleanState = self._getLastCleanState()
        if cleanState != None:
            self._write(self._getLastCleanState())
        else:
            self.markDeleted()

    def markDeleted(self):
        self._write("Started: %s, Harvested/Uploaded/Deleted/Total: 0/0/0/0, Done: Deleted all id's." % self.getTime())

    def _getLastCleanState(self):
        result = None
        self._statsfile.seek(0)
        for line in self._filterNonErrorLogLine(self._statsfile):
            token = getResumptionToken(line)
            if token == None:
                result = line
        self._statsfile.seek(0, SEEK_END)
        return result

    def _getLastDoneState(self):
        result = None
        self._statsfile.seek(0)
        for line in self._filterNonErrorLogLine(self._statsfile):
            result = line
        self._statsfile.seek(0, SEEK_END)
        return result

    def _readState(self):
        self.startdate = None
        self.token = None
        self.total = 0
        if isfile(self._filename):
            logline = self._getLastDoneState()
            if logline and not self._isDeleted(logline):
                self.startdate = getStartDate(logline)
                self.token = getResumptionToken(logline)
                harvested, uploaded, deleted, total = getHarvestedUploadedRecords(logline)
                self.total = int(total)

    def _prepareForWriting(self):
        """Make sure writing always starts on newline."""
        if self._statsfile.tell() == 0:
            return
        self._statsfile.seek(-1, SEEK_END)
        lastchar = self._statsfile.read()
        if lastchar != '\n':
            self._write('\n')
    
    def _write(self, *args):
        self._statsfile.write(*args)

    @staticmethod
    def _filterNonErrorLogLine(iterator):
        return (line for line in iterator if 'Done:' in line)
    
    @staticmethod
    def _isDeleted(logline):
        return "Done: Deleted all id's" in logline

    def getTime(self):
        return strftime('%Y-%m-%d %H:%M:%S', self._localtime())

    @staticmethod
    def _localtime():
        return localtime()
                
def getStartDate(logline):
    matches = re.search('Started: (\d{4}-\d{2}-\d{2})', logline)
    return matches.group(1)

def getResumptionToken(logline):
    matches=re.search('ResumptionToken: (.*)', logline.strip())
    if matches and matches.group(1) != 'None': 
        return matches.group(1)
    return None

def getHarvestedUploadedRecords(logline):
    matches=re.search('Harvested/Uploaded/(?:Deleted/)?Total: \s*(\d*)/\s*(\d*)(?:/\s*(\d*))?/\s*(\d*)', logline)
    return matches.groups('0')
   
