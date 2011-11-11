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
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
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

import time, os, sys, re, string
if sys.version_info[:2] == (2,3):
    from sets import Set as set
from eventlogger import EventLogger
from ids import Ids
import traceback
from os.path import join, isdir, isfile, dirname
from os import makedirs, remove
from shutil import rmtree
from state import State
from escaping import escapeFilename


INVALID_DATA_MESSAGES_DIR = "invalid"

def idfilename(stateDir, repositorykey):
    return join(stateDir, repositorykey+'.ids')

def ensureDirectory(directoryPath):
    isdir(directoryPath) or makedirs(directoryPath)

class HarvesterLog(object):
    def __init__(self, stateDir, logDir, name):
        self._name=name
        self._logDir = logDir
        ensureDirectory(self._logDir)
        self._maybeMigrateIgnoredDir()
        ensureDirectory(stateDir)
        self._ids = Ids(stateDir, name)
        self._ignoredIds = Ids(stateDir, name + "_ignored")
        self._state = State(stateDir, name)
        self._eventlogger = EventLogger(logDir + '/' + name +'.events')
        self.from_ = self._state.startdate
        self.token = self._state.token
        self.total = self._state.total
        self._resetCounts()

    def isCurrentDay(self, yyyy_mm_dd):
        return yyyy_mm_dd == self._state.getTime()[:10]    
        
    def startRepository(self):
        self._resetCounts()
        self._state._write('Started: %s, Harvested/Uploaded/Deleted/Total: ' % self._state.getTime())

    def _resetCounts(self):
        self._harvestedCount = 0
        self._uploadedCount = 0
        self._deletedCount = 0

    def totalIds(self):
        return len(self._ids)

    def totalIgnoredIds(self):
        return len(self._ignoredIds)

    def eventLogger(self):
        # Should be removed, but is still used in Harvester.
        return self._eventlogger
            
    def markDeleted(self):
        self._ids.clear()
        self._state.markDeleted()
        self._eventlogger.logSuccess('Harvested/Uploaded/Deleted/Total: 0/0/0/0, Done: Deleted all id\'s.',id=self._name)
    
    def endRepository(self, token):
        self._state._write(self.countsSummary())
        self._state._write(', Done: %s, ResumptionToken: %s' % (self._state.getTime(), token))
        self._eventlogger.logSuccess('Harvested/Uploaded/Deleted/Total: %s, ResumptionToken: %s' % (self.countsSummary(), token), id=self._name)

    def endWithException(self):
        error = str(sys.exc_type) + ': ' + str(sys.exc_value)
        xtype,xval,xtb = sys.exc_info()
        error2 = '|'.join(map(str.strip,traceback.format_exception(xtype,xval,xtb)))
        self._eventlogger.logError(error2, id=self._name)
        self._state._write(self.countsSummary())
        self._state._write( ', Error: ' + error)

    def countsSummary(self):
        return '%d/%d/%d/%d' % (self._harvestedCount, self._uploadedCount, self._deletedCount, self.totalIds())

    def close(self):
        self._eventlogger.close()
        self._ids.close()
        self._ignoredIds.close()
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

    def ignoreIdentifier(self, uploadid):
        self._ignoredIds.add(uploadid)
        self._eventlogger.logWarning('IGNORED', uploadid)
    
    def logInvalidDataMessage(self, uploadid, message):
        filePath = self._invalidDataMessageFilePath(uploadid)
        ensureDirectory(dirname(filePath))
        open(filePath, 'w').write(message)

    def clearIgnoredAndInvalidDataMessages(self, repositoryId):
        repositoryIgnoredIds = [id for id in self._ignoredIds 
                                if id.startswith("%s:" % repositoryId)]
        for id in repositoryIgnoredIds:
            self._ignoredIds.remove(id)
        rmtree(join(self._logDir, INVALID_DATA_MESSAGES_DIR, repositoryId))

    def hasWork(self):
        return not self.isCurrentDay(self.from_) or self.token
    
    def state(self):
        return self._state

    def ignoredIds(self):
        return [id for id in self._ignoredIds]

    def _removeFromInvalidData(self, uploadid):
        self._ignoredIds.remove(uploadid)
        ignoreFile = self._invalidDataMessageFilePath(uploadid)
        if isfile(ignoreFile):
            remove(ignoreFile)

    def _invalidDataMessageFilePath(self, uploadid):
        repositoryId, recordId = uploadid.split(":", 1)
        return join(self._logDir, INVALID_DATA_MESSAGES_DIR, repositoryId, escapeFilename(recordId))

    def _maybeMigrateIgnoredDir(self):
        # Migration from Meresco Harvester 7.2.x to Meresco Harvester 7.2.5
        # 'ignored' was a misnomer, renamed to 'invalidDataMessages' because we also
        # want to log the last InvalidDataException message that was not ignored.
        ignoredPath = join(self._logDir, "ignored")
        if isdir(ignoredPath):
            from os import rename
            rename(ignoredPath, join(self._logDir, INVALID_DATA_MESSAGES_DIR))

