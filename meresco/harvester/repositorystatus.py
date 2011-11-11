## begin license ##
# 
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for 
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl 
# 
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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

from os.path import join, isfile, isdir
from os import listdir
from lxml.etree import parse
from xml.sax.saxutils import escape as escapeXml
from re import compile
from itertools import ifilter, islice
from meresco.core import Observable

from harvesterlog import INVALID_DATA_MESSAGES_DIR


NUMBERS_RE = compile(r'.*Harvested/Uploaded/Deleted/Total:\s*(\d+)/(\d+)/(\d+)/(\d+).*')

class RepositoryStatus(Observable):

    def __init__(self, logPath, statePath, name=None):
        Observable.__init__(self, name)
        self._logPath = logPath
        self._statePath = statePath

    def getStatus(self, domainId, repositoryGroupId=None, repositoryId=None):
        yield "<GetStatus>"
        if repositoryId:
            groupId = self.any.getRepositoryGroupId(domainId=domainId, repositoryId=repositoryId)
            yield self._getRepositoryStatus(domainId, groupId, repositoryId)
        else:
            groupIds = [repositoryGroupId] if repositoryGroupId else self.any.getRepositoryGroupIds(domainId=domainId)
            for groupId in groupIds:
                repositoryIds = self.any.getRepositoryIds(domainId=domainId, repositoryGroupId=groupId)
                for repoId in repositoryIds:
                    yield self._getRepositoryStatus(domainId, groupId, repoId)
        yield "</GetStatus>"

    def invalidRecords(self, domainId, repositoryId):
        ignoredFile = join(self._statePath, domainId, "%s_ignored.ids" % repositoryId)
        if not isfile(ignoredFile):
            return []
        return reversed([line.strip() for line in open(ignoredFile) if line.strip()])

    def getInvalidRecord(self, domainId, repositoryId, recordId):
        invalidDir = join(self._logPath, domainId, INVALID_DATA_MESSAGES_DIR)
        return parse(open(join(invalidDir, repositoryId, recordId)))

    def _getRepositoryStatus(self, domainId, groupId, repoId):
        stats = self._parseEventsFile(domainId, repoId)
        yield '<status repositoryId="%s" repositoryGroupId="%s">\n' % (repoId, groupId)
        yield '<lastHarvestDate>%s</lastHarvestDate>\n' % stats.get('lastHarvestDate', '')
        yield '<harvested>%s</harvested>\n' % stats.get('harvested', '')
        yield '<uploaded>%s</uploaded>\n' % stats.get('uploaded', '')
        yield '<deleted>%s</deleted>\n' % stats.get('deleted', '')
        yield '<total>%s</total>\n' % stats.get('total', '')
        yield '<totalerrors>%s</totalerrors>\n' % stats.get('totalerrors', '')
        yield '<recenterrors>\n'
        for error in stats['recenterrors']:
            yield '<error date="%s">%s</error>\n' % (error[0], escapeXml(error[1])) 
        yield '</recenterrors>\n'
        yield '<ignored>%s</ignored>\n' % self._ignoredCount(domainId, repoId)
        yield '<recentinvalids>\n'
        for invalidRecord in islice(self.invalidRecords(domainId, repoId), 10):
            yield '<invalidId>%s</invalidId>\n' % invalidRecord
        yield '</recentinvalids>\n'
        yield '<lastHarvestAttempt>%s</lastHarvestAttempt>\n' % stats.get('lastHarvestAttempt', '')
        yield '</status>\n'

    def _ignoredCount(self, domainId, repositoryId):
        ignoredFile = join(self._statePath, domainId, "%s_ignored.ids" % repositoryId)
        return len(open(ignoredFile).readlines()) if isfile(ignoredFile) else 0

    def _parseEventsFile(self, domainId, repositoryId):
        parseState = {'errors': []}
        eventsfile = join(self._logPath, domainId, "%s.events" % repositoryId)
        if isfile(eventsfile):
            for line in open(eventsfile):
                stateLine = line.strip().split('\t')
                if len(stateLine) != 4:
                    continue
                date, event, id, comments = stateLine
                date = date[1:-1]
                if event == 'SUCCES':
                    _succes(parseState, date, comments)
                elif event == 'ERROR':
                    _error(parseState, date, comments)
        recenterrors = parseState["errors"][-10:]
        recenterrors.reverse()
        stats = {}
        for k,v in ifilter(lambda (k,v): k != 'errors', parseState.items()):
            stats[k] = v
        stats["totalerrors"] = len(parseState["errors"])
        stats["recenterrors"] = recenterrors
        return stats

def _succes(parseState, date, comments):
    parseState["lastHarvestDate"] = _reformatDate(date)
    parseState["lastHarvestAttempt"] = _reformatDate(date)
    parseState["errors"] = []
    match = NUMBERS_RE.match(comments)
    if match:
        parseState["harvested"], parseState["uploaded"], parseState["deleted"], parseState["total"] = match.groups()

def _error(parseState, date, comments):
    parseState["errors"].append((_reformatDate(date), comments))
    parseState["lastHarvestAttempt"] = _reformatDate(date)

def _reformatDate(aDate):
    return aDate[0:len('YYYY-MM-DD')] + 'T' + aDate[len('YYYY-MM-DD '):len('YYYY-MM-DD HH:MM:SS')] + 'Z'
        
