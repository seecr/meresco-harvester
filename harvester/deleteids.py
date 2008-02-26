#!/usr/bin/env python
## begin license ##
#
#    "Sahara" consists of two subsystems, namely an OAI-harvester and a web-control panel.
#    "Sahara" is developed for SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006,2007 SURFnet B.V. http://www.surfnet.nl
#
#    This file is part of "Sahara"
#
#    "Sahara" is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    "Sahara" is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with "Sahara"; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
#
# (c) 2005 Seek You Too B.V.
#
# $Id: deleteids.py 4825 2007-04-16 13:36:24Z TJ $
#


from sseuploader import SSEUploader, UploaderException
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
    def __init__(self, repository, logpath):
        self.logpath = logpath
        self.repository = repository
        self.logger = EventLogger(os.path.join(logpath,'deleteids.log'))
        self.filename = idfilename(self.logpath,self.repository.id)
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
            logger = HarvesterLog(self.logpath,self.repository.id)
            try:
                logger.markDeleted()
            finally:
                logger.close()
