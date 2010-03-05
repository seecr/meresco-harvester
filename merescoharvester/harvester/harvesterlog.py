## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
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

import time, os, sys, re, string
if sys.version_info[:2] == (2,3):
    from sets import Set as set
from eventlogger import EventLogger
from ids import Ids
import traceback
from os.path import join as pathjoin, isdir
from os import makedirs
from state import State

def idfilename(stateDir, repositorykey):
    return pathjoin(stateDir, repositorykey+'.ids')

def ensureDirectory(directoryPath):
    isdir(directoryPath) or makedirs(directoryPath)

class HarvesterLog(object):
    def __init__(self, stateDir, logDir, name):
        self._name=name
        ensureDirectory(stateDir)
        self._ids = Ids(stateDir, name)
        self._state = State(stateDir, name)
        self._eventlogger = EventLogger(logDir + '/' + name +'.events')
        self.from_, self._statsfile, self.token, self.total = self._state.readFromStatsFileAndOpenForWriting()
        self._lastline = ''

    def printTime(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', self._localtime())
    
    def isCurrentDay(self, yyyy_mm_dd):
        return yyyy_mm_dd == self.printTime()[:10]    
        
    def startRepository(self, repositoryname):
        self._statsfile.write('Started: %s' % self.printTime())

    def totalids(self):
        return self._ids.total()

    def eventLogger(self):
        return self._eventlogger
            
    def markDeleted(self):
        self.startRepository(self._name)
        self._ids.clear()
        self.begin()
        self.updateStatsfile(0,0,0)
        self.done()
        self._statsfile.write(", Done: Deleted all id's.")
        self._statsfile.flush()
        self._eventlogger.succes('Harvested/Uploaded/Deleted/Total: 0/0/0/0, Done: Deleted all id\'s.',id=self._name)
    
    def endRepository(self, token):
        self._statsfile.write(', Done: %s, ResumptionToken: %s' % (self.printTime(), token))
        self._statsfile.flush()
        self._eventlogger.succes('Harvested/Uploaded/Deleted/Total: %s, ResumptionToken: %s'%(self._lastline,token),id=self._name)

    def endWithException(self):
        error = str(sys.exc_type) + ': ' + str(sys.exc_value)
        xtype,xval,xtb = sys.exc_info()
        error2 = '|'.join(map(str.strip,traceback.format_exception(xtype,xval,xtb)))
        self._eventlogger.error(error2, id=self._name)
        self._statsfile.write( ', Error: ' + error)
        self._statsfile.flush()

    def close(self):
        self._eventlogger.close()
        self._ids.close()
        self._statsfile.write('\n')
        self._statsfile.close()

    def logID(self, uploadid):
        self._ids.add(uploadid)
        
    def logDeletedID(self, uploadid):
        self._ids.remove(uploadid)
        
    def updateStatsfile(self, harvested, uploaded, deleted, totalWillBeIgnored=None):
        self._statsfile.seek(self._pos)
        self._lastline = '%d/%d/%d/%d' % (harvested, uploaded, deleted, self.totalids())
        self._statsfile.write(self._lastline)
        self._statsfile.write(' busy...')
        self._statsfile.flush()

    def begin(self):
        self._statsfile.write(', Harvested/Uploaded/Deleted/Total: ')
        self._pos = self._statsfile.tell()
        
    def done(self):
        self._statsfile.seek(-8, 2)
    
    def hasWork(self):
        return not self.isCurrentDay(self.from_) or self.token

    def _localtime(self):
        return time.localtime()
