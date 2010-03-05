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
import re

class State(object):
    def __init__(self, stateDir, name):
        self._filename = join(stateDir, '%s.stats' % name)
    
    def readFromStatsFileAndOpenForWriting(self):
        startdate = None
        token = None
        total = 0
        if isfile(self._filename):
            lines = open(self._filename).readlines()
            logline = self._findLastNonErrorLogLine(lines)
            if logline and not self._isDeleted(logline):
                startdate = getStartDate(logline)
                token = getResumptionToken(logline)
                harvested, uploaded, deleted, total = getHarvestedUploadedRecords(logline)
            statsfile = open(self._filename, 'w')
            statsfile.writelines(line.strip() + '\n' for line in lines if line.strip()) #filters empty lines and every line has \n
            #statsfile.writelines(map(lambda line:line.strip()+'\n',filter(string.strip,lines))) 
            statsfile.flush()
        else:
            statsfile = open(self._filename, 'w')
        return startdate, statsfile, token, int(total)

    @staticmethod
    def _findLastNonErrorLogLine(lines):
        reversedlines = lines[:]
        reversedlines.reverse()
        for line in reversedlines:
            if line.find('Done:') >= 0:
                return line

    @staticmethod
    def _isDeleted(logline):
        return "Done: Deleted all id's" in logline
                
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
    
