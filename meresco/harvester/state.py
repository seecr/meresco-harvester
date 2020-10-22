## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010-2012, 2015, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2011 Tilburg University http://www.uvt.nl
# Copyright (C) 2012, 2015, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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
from os import SEEK_END, SEEK_SET
import re
from meresco.components.json import JsonDict
from seecr.zulutime import ZuluTime

class State(object):
    def __init__(self, stateDir, name):
        self._statsfilename = join(stateDir, '%s.stats' % name)
        self._forceFinalNewlineOnStatsFile()
        self._resumptionFilename = join(stateDir, '%s.next' % name)
        self._runningFilename = join(stateDir, '%s.running' % name)
        self.from_ = None
        self.token = None
        self.lastSuccessfulHarvest = None
        self._readState()
        self._statsfile = open(self._statsfilename, 'a')

    def close(self):
        self._statsfile.close()
        self._forceFinalNewlineOnStatsFile()

    def markStarted(self):
        self._write('Started: %s, Harvested/Uploaded/Deleted/Total: ' % self.getTime())

    def markHarvested(self, countsSummary, token, responseDate):
        self._write(countsSummary)
        self._write(', Done: %s, ResumptionToken: %s' % (self.getTime(), token))
        self._writeResumptionValues(token, responseDate)
        self._markRunningState("Ok")

    def markDeleted(self):
        self._write("Started: %s, Harvested/Uploaded/Deleted/Total: 0/0/0/0, Done: Deleted all ids." % self.getTime())
        self._writeResumptionValues(None, None)
        self._markRunningState("Ok")

    def markException(self, exType, exValue, countsSummary):
        error = str(exType) + ': ' + str(exValue)
        self._write(countsSummary)
        self._write( ', Error: ' + error)
        self._markRunningState("Error", str(exValue))

    def _markRunningState(self, status, message=""):
        runningDict = JsonDict.load(self._runningFilename) if isfile(self._runningFilename) else {}
        if status != runningDict.get('status', None) or message != runningDict.get('message', None):
            JsonDict({'changedate': self.getTime(),'status': status, 'message': message}).dump(self._runningFilename)

    def getLastSuccessfulHarvestTime(self):
        if self.lastSuccessfulHarvest:
            return ZuluTime(self.lastSuccessfulHarvest)
        if self.from_:
            if 'T' not in self.from_:
                return ZuluTime(self.from_ + "T00:00:00Z")
            return ZuluTime(self.from_)
        return None

    def getTime(self):
        return self.getZTime().display('%Y-%m-%d %H:%M:%S')

    def setToLastCleanState(self):
        self._write("Started: %s, Done: Reset to last clean state. ResumptionToken: \n" % self.getTime())
        self.token = None
        self._writeResumptionValues(None, self.from_)

    def _readState(self):
        if isfile(self._resumptionFilename):
            values = JsonDict.load(self._resumptionFilename)
            self.token = values.get('resumptionToken', None) or None
            self.from_ = values.get('from', '') or None
            self.lastSuccessfulHarvest = values.get('lastSuccessfulHarvest', '') or None
            return

        # The mechanism below will only be carried out once in case the resumption file does not yet exist.
        if isfile(self._statsfilename):
            self._statsfile = open(self._statsfilename)
            logline = None
            for logline in self._filterNonErrorLogLine(self._statsfile):
                if not self.token:
                    self.from_ = getStartDate(logline)
                self.token = getResumptionToken(logline)
            if logline and self._isDeleted(logline):
                self.from_ = None
                self.token = None
            self._statsfile.close()

    def _forceFinalNewlineOnStatsFile(self):
        if isfile(self._statsfilename):
            with open(self._statsfilename, 'r+') as statsfile:
                statsfile.seek(0, SEEK_END)
                if statsfile.tell() == 0:
                    return
                statsfile.seek(statsfile.tell()-1, SEEK_SET)
                lastchar = statsfile.read()
                if lastchar != '\n':
                    statsfile.write('\n')

    def _write(self, *args):
        self._statsfile.write(*args)
        self._statsfile.flush()

    def _writeResumptionValues(self, token, responseDate):
        newToken = str(token or '')
        newFrom = ''
        lastSuccessfulHarvest = self.lastSuccessfulHarvest #keep value if not successful
        if responseDate:
            newFrom = self.from_ if self.token else responseDate
        if token is None and responseDate is None:
            lastSuccessfulHarvest = None
        else:
            lastSuccessfulHarvest = self.getZTime().zulu()
        JsonDict({'resumptionToken': newToken, 'from': newFrom, 'lastSuccessfulHarvest': lastSuccessfulHarvest}).dump(self._resumptionFilename)

    @staticmethod
    def _filterNonErrorLogLine(iterator):
        return (line for line in iterator if 'Done:' in line)

    @staticmethod
    def _isDeleted(logline):
        return "Done: Deleted all ids" in logline or \
               "Done: Deleted all id's" in logline

    @staticmethod
    def getZTime():
        return ZuluTime()


def getStartDate(logline):
    matches = re.search('Started: (\d{4}-\d{2}-\d{2})', logline)
    return matches.group(1)

def getResumptionToken(logline):
    matches=re.search('ResumptionToken: (.*)', logline.strip())
    if matches and matches.group(1) != 'None':
        return matches.group(1)
    return None

