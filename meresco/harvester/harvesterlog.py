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
# Copyright (C) 2010-2012, 2015 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2011-2012, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from eventlogger import EventLogger
from ids import Ids
import traceback
from os.path import join, isdir, isfile, dirname
from os import makedirs, remove
from shutil import rmtree
from state import State
from escaping import escapeFilename
from seecr.zulutime import ZuluTime


INVALID_DATA_MESSAGES_DIR = "invalid"

def idfilename(stateDir, repositorykey):
    return join(stateDir, repositorykey+'.ids')

def ensureDirectory(directoryPath):
    isdir(directoryPath) or makedirs(directoryPath)

class HarvesterLog(object):
    def __init__(self, stateDir, logDir, name):
        self._name = name
        self._logDir = logDir
        ensureDirectory(logDir)
        ensureDirectory(stateDir)
        self._ids = Ids(stateDir, name)
        self._invalidIds = Ids(stateDir, name + "_invalid")
        self._state = State(stateDir, name)
        self._eventlogger = EventLogger(logDir + '/' + name +'.events')
        self._resetCounts()

    def isCurrentDay(self, date):
        return date.split('T')[0] == self._state.getTime().split()[0]

    def startRepository(self):
        self._resetCounts()
        self._state.markStarted()

    def _resetCounts(self):
        self._harvestedCount = 0
        self._uploadedCount = 0
        self._deletedCount = 0

    def totalIds(self):
        return len(self._ids)

    def totalInvalidIds(self):
        return len(self._invalidIds)

    def eventLogger(self):
        # Should be removed, but is still used in Harvester.
        return self._eventlogger

    def markDeleted(self):
        self._ids.clear()
        self._state.markDeleted()
        self._eventlogger.logSuccess('Harvested/Uploaded/Deleted/Total: 0/0/0/0, Done: Deleted all ids.', id=self._name)

    def endRepository(self, token, responseDate):
        self._state.markHarvested(self.countsSummary(), token, responseDate)
        self._eventlogger.logSuccess('Harvested/Uploaded/Deleted/Total: %s, ResumptionToken: %s' % (self.countsSummary(), token), id=self._name)

    def endWithException(self, exType, exValue, exTb):
        self._state.markException(exType, exValue, self.countsSummary())
        error = '|'.join(str.strip(s) for s in traceback.format_exception(exType, exValue, exTb))
        self._eventlogger.logError(error, id=self._name)

    def countsSummary(self):
        return '%d/%d/%d/%d' % (self._harvestedCount, self._uploadedCount, self._deletedCount, self.totalIds())

    def close(self):
        self._eventlogger.close()
        self._ids.close()
        self._invalidIds.close()
        self._state.close()

    def notifyHarvestedRecord(self, uploadid):
        self._removeFromInvalidData(uploadid)
        self._harvestedCount += 1

    def uploadIdentifier(self, uploadid):
        self._ids.add(uploadid)
        self._uploadedCount += 1

    def deleteIdentifier(self, uploadid):
        self._ids.remove(uploadid)
        self._deletedCount += 1

    def logInvalidData(self, uploadid, message):
        self._invalidIds.add(uploadid)
        filePath = self._invalidDataMessageFilePath(uploadid)
        ensureDirectory(dirname(filePath))
        open(filePath, 'w').write(message)

    def logIgnoredIdentifierWarning(self, uploadid):
        self._eventlogger.logWarning('IGNORED', uploadid)

    def clearInvalidData(self, repositoryId):
        for id in list(self._invalidIds):
            if id.startswith("%s:" % repositoryId):
                self._invalidIds.remove(id)
        rmtree(join(self._logDir, INVALID_DATA_MESSAGES_DIR, repositoryId))

    def hasWork(self, continuousInterval=None):
        if continuousInterval is not None:
            from_ = self._state.from_
            if from_ and 'T' not in from_:
                from_ += "T00:00:00Z"
            return from_ is None or ZuluTime().epoch - ZuluTime(from_).epoch > continuousInterval
        return self._state.token or self._state.from_ is None or not self.isCurrentDay(self._state.from_)

    def state(self):
        return self._state

    def invalidIds(self):
        return list(self._invalidIds)

    def _removeFromInvalidData(self, uploadid):
        self._invalidIds.remove(uploadid)
        invalidDataMessageFilePath = self._invalidDataMessageFilePath(uploadid)
        if isfile(invalidDataMessageFilePath):
            remove(invalidDataMessageFilePath)

    def _invalidDataMessageFilePath(self, uploadid):
        repositoryId, recordId = uploadid.split(":", 1)
        return join(self._logDir, INVALID_DATA_MESSAGES_DIR, escapeFilename(repositoryId), escapeFilename(recordId))


