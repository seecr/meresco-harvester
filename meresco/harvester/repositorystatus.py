## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2011-2012, 2015, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2012, 2015, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
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

from os.path import join, isfile
from lxml.etree import parse
from re import compile
from itertools import islice
from meresco.components.json import JsonDict, JsonList
from meresco.core import Observable
from escaping import escapeFilename, unescapeFilename
from simplejson import load as jsonLoad

from .harvesterlog import INVALID_DATA_MESSAGES_DIR
from weightless.core import asList


NUMBERS_RE = compile(r'.*Harvested/Uploaded/Deleted/Total:\s*(\d+)/(\d+)/(\d+)/(\d+).*')

class RepositoryStatus(Observable):
    def __init__(self, logPath, statePath, name=None):
        Observable.__init__(self, name)
        self._logPath = logPath
        self._statePath = statePath

    def getStatus(self, **kwargs):
        return JsonList([x for x in asList(self._getStatus(**kwargs))])

    def _getStatus(self, domainId, repositoryGroupId=None, repositoryId=None):
        if repositoryId:
            groupId = self.call.getRepositoryGroupId(domainId=domainId, repositoryId=repositoryId)
            yield self._getRepositoryStatus(domainId, groupId, repositoryId)
        else:
            groupIds = [repositoryGroupId] if repositoryGroupId else self.call.getRepositoryGroupIds(domainId=domainId)
            for groupId in groupIds:
                repositoryIds = self.call.getRepositoryIds(domainId=domainId, repositoryGroupId=groupId)
                for repoId in repositoryIds:
                    yield self._getRepositoryStatus(domainId, groupId, repoId)

    def getRunningStatesForDomain(self, domainId):
        def _jsonLoad(filename):
            with open(filename) as fp:
                return jsonLoad(fp)

        return sorted([
            mergeDicts(_jsonLoad(filepath), {'repositoryId': repoId})
            for groupId in self.call.getRepositoryGroupIds(domainId=domainId)
            for repoId in self.call.getRepositoryIds(domainId=domainId, repositoryGroupId=groupId)
            for filepath in [join(self._statePath, domainId, escapeFilename("%s.running" % repoId))]
            if isfile(filepath)
        ], key=lambda d: d['changedate'], reverse=True)

    def invalidRecords(self, domainId, repositoryId):
        invalidFile = join(self._statePath, domainId, escapeFilename("%s_invalid.ids" % repositoryId))
        if not isfile(invalidFile):
            return []
        with open(invalidFile) as fp:
            return reversed(
                [x[:-1] if x[-1] == '\n' else x for x in
                    (unescapeFilename(line) for line in fp if line.strip())
                ]
            )

    def getInvalidRecord(self, domainId, repositoryId, recordId):
        invalidDir = join(self._logPath, domainId, INVALID_DATA_MESSAGES_DIR)
        with open(join(invalidDir, escapeFilename(repositoryId), escapeFilename(recordId))) as fp:
            return parse(fp)

    def _getRepositoryStatus(self, domainId, groupId, repoId):
        stats = self._parseEventsFile(domainId, repoId)
        return JsonDict(
                repositoryId=repoId,
                repositoryGroupId=groupId,
                lastHarvestDate=stats.get('lastHarvestDate'),
                harvested=int(stats.get('harvested', 0)),
                uploaded=int(stats.get('uploaded', 0)),
                deleted=int(stats.get('deleted', 0)),
                total=int(stats.get('total', 0)),
                totalerrors=int(stats.get('totalerrors', 0)),
                recenterrors=[dict(date=error[0], error=error[1]) for error in stats['recenterrors']],
                invalid=int(self._invalidCount(domainId, repoId)),
                recentinvalids=list(islice(self.invalidRecords(domainId, repoId), 10)),
                lastHarvestAttempt=stats.get('lastHarvestAttempt')
            )

    def _invalidCount(self, domainId, repositoryId):
        invalidFile = join(self._statePath, domainId, escapeFilename("%s_invalid.ids" % repositoryId))
        if not isfile(invalidFile):
            return 0

        with open(invalidFile) as fp:
            return len(fp.readlines())

    def _parseEventsFile(self, domainId, repositoryId):
        parseState = {'errors': []}
        eventsfile = join(self._logPath, domainId, "%s.events" % repositoryId)
        if isfile(eventsfile):
            with open(eventsfile) as fp:
                for i, line in enumerate(reversed(fp.readlines())):
                    stateLine = line.strip().split('\t')
                    if len(stateLine) != 4:
                        continue
                    date, event, id, comments = stateLine
                    date = date[1:-1]
                    if not 'lastHarvestAttempt' in parseState:
                        parseState['lastHarvestAttempt'] = _reformatDate(date)
                    if event == 'SUCCES':
                        _succes(parseState, date, comments)
                        break
                    elif event == 'ERROR':
                        _error(parseState, date, comments)
                        if len(parseState["errors"]) > 100:
                            break

        recenterrors = parseState["errors"][-10:]
        recenterrors.reverse()
        stats = {}
        for k,v in filter(lambda k_v: k_v[0] != 'errors', list(parseState.items())):
            stats[k] = v
        stats["totalerrors"] = len(parseState["errors"])
        stats["recenterrors"] = recenterrors
        return stats

def _succes(parseState, date, comments):
    parseState["lastHarvestDate"] = _reformatDate(date)
    match = NUMBERS_RE.match(comments)
    if match:
        parseState["harvested"], parseState["uploaded"], parseState["deleted"], parseState["total"] = match.groups()

def _error(parseState, date, comments):
    parseState["errors"].insert(0, (_reformatDate(date), comments))

def _reformatDate(aDate):
    return aDate[0:len('YYYY-MM-DD')] + 'T' + aDate[len('YYYY-MM-DD '):len('YYYY-MM-DD HH:MM:SS')] + 'Z'

def mergeDicts(dict1, dict2):
    newDict = dict1.copy()
    newDict.update(dict2)
    return newDict
