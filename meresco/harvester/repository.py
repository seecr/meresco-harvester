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
#    Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
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

from oairequest import OAIError
from saharaobject import SaharaObject
from eventlogger import NilEventLogger
from virtualuploader import UploaderFactory
from timeslot import Timeslot
from sys import exc_info
from traceback import format_exception
from time import localtime
from action import Action

nillogger = NilEventLogger()

class RepositoryException(Exception):
    pass

class Repository(SaharaObject):
    def __init__(self, domainId, repositoryId):
        SaharaObject.__init__(self, [
            'repositoryGroupId', 'baseurl', 'set',
            'collection', 'metadataPrefix', 'use',  
            'targetId', 'mappingId', 'action', 
            'complete', 'maximumIgnore'], ['shopclosed'])
        self.domainId = domainId
        self.id = repositoryId
        self.mockUploader = None
        self.uploadfulltext = True

    def closedSlots(self):
        if not hasattr(self, '_closedslots'):
            if self.shopclosed:
                self._closedslots = map(lambda txt: Timeslot(txt), self.shopclosed)
            else:
                self._closedslots = []
        return self._closedslots

    def shopClosed(self, dateTuple = localtime()[:5]):
        return reduce(lambda lhs, rhs: lhs or rhs, map(lambda x:x.areWeWithinTimeslot( dateTuple), self.closedSlots()), False)

    def target(self):
        return self._saharaget.getTarget(self.domainId, self.targetId)

    def mapping(self):
        return self._saharaget.getMapping(self.domainId, self.mappingId)

    def maxIgnore(self):
        return int(self.maximumIgnore) if self.maximumIgnore else 0

    def createUploader(self, logger):
        if self.mockUploader:
            return self.mockUploader
        return UploaderFactory().createUploader(self.target(), logger, self.collection)
    
    def oairequest(self):
        return OaiRequest(self.baseurl)

    def _createAction(self, stateDir, logDir, generalHarvestLog):
        return Action.create(self, stateDir=stateDir, logDir=logDir, generalHarvestLog=generalHarvestLog)

    def do(self, stateDir, logDir, generalHarvestLog=nillogger):
        try:
            if not (stateDir or logDir):
                raise RepositoryException('Missing stateDir and/or logDir')
            action = self._createAction(stateDir=stateDir, logDir=logDir, generalHarvestLog=generalHarvestLog)
            if action.info():
                generalHarvestLog.logLine('START',action.info(), id=self.id)
            actionIsDone, message, hasResumptionToken = action.do()
            if  actionIsDone:
                self.action = ''
                self._saharaget.repositoryActionDone(self.domainId, self.id)
            if message:
                generalHarvestLog.logLine('END', message, id = self.id)
            completeHarvest = hasResumptionToken and self.complete == 'true'
            if completeHarvest:
                generalHarvestLog.logInfo('Repository will be completed in one attempt', id=self.id)
            return message, completeHarvest
        except OAIError, e:
            errorMessage = _errorMessage()
            generalHarvestLog.logError(errorMessage, id=self.id)
            if e.errorCode() == 'badResumptionToken':
                action.resetState()
                return errorMessage, self.complete == 'true'
            return errorMessage, False
        except:
            errorMessage = _errorMessage()
            generalHarvestLog.logError(errorMessage, id=self.id)
            return errorMessage, False

def _errorMessage():
    xtype,xval,xtb = exc_info()
    return '|'.join(line.strip() for line in format_exception(xtype,xval,xtb))
