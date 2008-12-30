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

from virtualuploader import UploaderException
from eventlogger import NilEventLogger, EventLogger
from harvesterlog import idfilename, HarvesterLog
from string import strip
from cq2utils import binderytools
from cq2utils import wrappers
import sys, os
from sets import Set
from mapping import Upload

def readIds(filename):
    ids = Set()
    f = open(filename)
    try:
        for id in filter(None, map(strip,f)):
            ids.add(id)
        return ids
    finally:
        f.close()

def writeIds(filename, ids):
    f = open(filename,'w')
    try:
        for id in ids:
            f.write(id)
            f.write('\n')
    finally:
        f.close()


class DeleteIds:
    def __init__(self, repository, stateDir, logDir):
        self._stateDir = stateDir
        self._logDir = logDir
        self.repository = repository
        self.logger = EventLogger(os.path.join(self._logDir, 'deleteids.log'))
        self.filename = idfilename(self._stateDir, self.repository.id)
        self.markLogger = True
                    
    def ids(self):
        return readIds(self.filename)
        
    def delete(self, trials = 3):
        uploader = self.repository.createUploader(self.logger)
        uploader.start()
        try:
            trials = min(10, max(1, trials))
            for i in range(trials):
                remaining = self._delete(uploader)
                if not remaining:
                    break
        finally:
            uploader.stop()
    
    def deleteFile(self, filename):
        self.filename = filename
        self.markLogger = False
        self.delete()
        
    def _delete(self, uploader):
        ids = self.ids()
        done = Set()
        exceptions = []
        try:
            for id in ids:
                try:
                    anUpload = Upload()
                    anUpload.id = id
                    anUpload.repository = self.repository
                    uploader.delete(anUpload)
                    done.add(id)
                except UploaderException, e:
                    exceptions.append((id,e))
            return ids - done
        finally:
            self._finish(ids - done)
            
    def _finish(self, remainingIDs):
        writeIds(self.filename, remainingIDs)
        if self.markLogger and not remainingIDs:
            logger = HarvesterLog(self._stateDir, self._logDir, self.repository.id)
            try:
                logger.markDeleted()
            finally:
                logger.close()
