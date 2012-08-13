## begin license ##
# 
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for 
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl 
# 
# Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2011 Tilburg University http://www.uvt.nl
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

from os.path import join, isfile
from os import SEEK_END
from time import strftime, gmtime
import re
from simplejson import load as jsonLoad, dump as jsonDump


class State(object):
    def __init__(self, stateDir, name):
        self._filename = join(stateDir, '%s.stats' % name)
        self._resumptionFilename = join(stateDir, '%s.next' % name)
        self.startdate = None
        self.token = None
        self.total = 0
        self._readState()
        self._newlineIfMissing()

    def close(self):
        self._newlineIfMissing()
        self._statsfile.close()

    def markStarted(self):
        self._write('Started: %s, Harvested/Uploaded/Deleted/Total: ' % self.getTime())

    def markHarvested(self, countsSummary, token, responseDate):
        self._write(countsSummary)
        self._write(', Done: %s, ResumptionToken: %s' % (self.getTime(), token))
        self._writeResumptionValues(token, responseDate)

    def markDeleted(self):
        self._write("Started: %s, Harvested/Uploaded/Deleted/Total: 0/0/0/0, Done: Deleted all ids." % self.getTime())
        self._writeResumptionValues(None, None)

    def markException(self, exType, exValue, countsSummary):
        error = str(exType) + ': ' + str(exValue)
        self._write(countsSummary)
        self._write( ', Error: ' + error)

    def getTime(self):
        return strftime('%Y-%m-%d %H:%M:%S', self._gmtime())

    def setToLastCleanState(self):
        self._write("Started: %s, Harvested/Uploaded/Deleted/Total: 0/0/0/%s, Done: Reset to last clean state. ResumptionToken: \n" % (self.getTime(), self.total))
        self.token = None
        self._writeResumptionValues(None, self.startdate)

    def _readState(self):
        open(self._filename, 'a').close()
        self._statsfile = open(self._filename, 'r+')
        logline = None
        for logline in self._filterNonErrorLogLine(self._statsfile):
            if not self.token:
                # necessary because of: http://www.openarchives.org/OAI/2.0/guidelines-harvester.htm#Datestamps
                # (last alinea of that paragraph)
                self.startdate = getStartDate(logline)
            self.token = getResumptionToken(logline)
        if logline:
            if self._isDeleted(logline):
                self.startdate = None
                self.token = None
            else:
                harvested, uploaded, deleted, total = getHarvestedUploadedRecords(logline)
                self.total = int(total)

        if isfile(self._resumptionFilename):
            values = jsonLoad(open(self._resumptionFilename))
            self.token = values.get('resumptionToken', None) or None
            self.startdate = values.get('from', '').split('T')[0] or None

    def _newlineIfMissing(self):
        if self._statsfile.tell() == 0:
            return
        self._statsfile.seek(-1, SEEK_END)
        lastchar = self._statsfile.read()
        if lastchar != '\n':
            self._write('\n')
    
    def _write(self, *args):
        self._statsfile.write(*args)
        self._statsfile.flush()

    def _writeResumptionValues(self, token, responseDate):
        newToken = str(token or '')
        newFrom = ''
        if responseDate:
            newFrom = self.startdate if self.token else responseDate
        jsonDump({'resumptionToken': newToken, 'from': newFrom}, open(self._resumptionFilename, 'w'))

    @staticmethod
    def _filterNonErrorLogLine(iterator):
        return (line for line in iterator if 'Done:' in line)

    @staticmethod
    def _isDeleted(logline):
        return "Done: Deleted all id's" in logline

    @staticmethod
    def _gmtime():
        return gmtime()
                

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
   
