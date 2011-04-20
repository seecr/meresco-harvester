## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2011 Stichting Kennisnet Ict http://www.kennisnet.nl 
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
from harvesterlog import idfilename
from string import strip
from slowfoot import binderytools
from slowfoot import wrappers
import sys, os
from sets import Set
from mapping import Upload
from traceback import format_exception

from meresco.core import Observable

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


class DeleteIds(Observable):
    def __init__(self, repository, stateDir):
        Observable.__init__(self)
        self._stateDir = stateDir
        self._repository = repository
        self._filename = idfilename(self._stateDir, self._repository.id)
        self._markLogger = True
                    
    def ids(self):
        return readIds(self._filename)
        
    def delete(self):
        self.do.start()
        try:
            self._delete()
        finally:
            self.do.stop()
    
    def deleteFile(self, filename):
        self._filename = filename
        self._markLogger = False
        self.delete()
        
    def _delete(self):
        ids = self.ids()
        done = Set()
        try:
            for id in ids:
                try:
                    anUpload = Upload(repository=self._repository)
                    anUpload.id = id
                    self.do.delete(anUpload)
                    done.add(id)
                except:
                    xtype,xval,xtb = sys.exc_info()
                    errorMessage = '|'.join(map(str.strip,format_exception(xtype,xval,xtb)))
                    self.do.logError(errorMessage, id=id)
                    raise
            return ids - done
        finally:
            self._finish(ids - done)
            
    def _finish(self, remainingIDs):
        writeIds(self._filename, remainingIDs)
        if self._markLogger and not remainingIDs:
            try:
                self.do.markDeleted()
            finally:
                self.do.close()
