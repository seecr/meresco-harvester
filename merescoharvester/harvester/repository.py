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
#    Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
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

from slowfoot import binderytools
from mapping import Mapping
from harvesterlog import HarvesterLog
from harvester import Harvester, HARVESTED, NOTHING_TO_DO
from oairequest import OAIError
from deleteids import DeleteIds, readIds, writeIds
from saharaobject import SaharaObject
from shutil import move
from os.path import isfile, join
from os import remove
from eventlogger import NilEventLogger
from virtualuploader import UploaderFactory
from timeslot import Timeslot
from sys import exc_info
from traceback import format_exception
import time

nillogger = NilEventLogger()
DONE = 'Done.'

class RepositoryException(Exception):
    pass

class Action:
    def __init__(self, repository, stateDir, logDir, generalHarvestLog):
        self._repository = repository
        self._stateDir = stateDir
        self._logDir = logDir
        self._generalHarvestLog = generalHarvestLog
    def do(self):
        """
        perform action and return
        (if the action is finished/done, a Message about what happened.)
        """
        raise NotImplementedError
    def info(self):
        return  str(self.__class__.__name__)

class NoneAction(Action):
    def do(self):
        return False, '', False
    def info(self):
        return ''

class HarvestAction(Action):
    def _createHarvester(self):
        return Harvester(self._repository, self._stateDir, self._logDir, generalHarvestLog=self._generalHarvestLog)

    def do(self):
        if self._repository.shopClosed():
            return False, 'Not harvesting outside timeslots.', False

        harvester = self._createHarvester()
        message, hasResumptionToken = harvester.harvest()
        return False, message, hasResumptionToken

class DeleteIdsAction(Action):
    def do(self):
        if self._repository.shopClosed():
            return False, 'Not deleting outside timeslots.', False

        d = DeleteIds(self._repository, self._stateDir, self._logDir, generalHarvestLog=self._generalHarvestLog)
        d.delete()
        return True, 'Deleted', False

class SmoothAction(Action):
    def __init__(self, repository, stateDir, logDir, generalHarvestLog):
        Action.__init__(self, repository, stateDir, logDir, generalHarvestLog)
        self.filename = join(self._stateDir, self._repository.key + '.ids')
        self.oldfilename = self.filename + ".old"

    def do(self):
        if self._repository.shopClosed():
            return False, 'Not smoothharvesting outside timeslots.', False

        if not isfile(self.oldfilename):
            result, hasResumptionToken = self._smoothinit(), True
        else:
            result, hasResumptionToken = self._harvest()
        if result == NOTHING_TO_DO:
            result = self._finish()
            hasResumptionToken = False
        return result == DONE, 'Smooth reharvest: ' + result, hasResumptionToken

    def _smoothinit(self):
        if isfile(self.filename):
            move(self.filename, self.oldfilename)
        else:
            open(self.oldfilename, 'w').close()
        open(self.filename, 'w').close()
        logger = HarvesterLog(self._stateDir, self._logDir, self._repository.key)
        try:
            logger.markDeleted()
        finally:
            logger.close()
        return     'initialized.'

    def _finish(self):
        deletefilename = self.filename + '.delete'
        if not isfile(deletefilename):
            writeIds(deletefilename, readIds(self.oldfilename) - readIds(self.filename))
        self._delete(deletefilename)
        remove(self.oldfilename)
        remove(deletefilename)
        return DONE

    def _delete(self, filename):
        d = DeleteIds(self._repository, self._stateDir, self._logDir, generalHarvestLog=self._generalHarvestLog)
        d.deleteFile(filename)

    def _harvest(self):
        harvester = Harvester(self._repository, self._stateDir, self._logDir, generalHarvestLog=self._generalHarvestLog)
        return harvester.harvest()

class ActionFactoryException(Exception):
    pass

class ActionFactory:
    def createAction(self, repository, stateDir, logDir, generalHarvestLog):
        if repository.action == 'clear':
            return DeleteIdsAction(repository, stateDir=stateDir, logDir=logDir, generalHarvestLog=generalHarvestLog)
        if repository.action == 'refresh':
            return SmoothAction(repository, stateDir=stateDir, logDir=logDir, generalHarvestLog=generalHarvestLog)
        if repository.use == 'true' and repository.action == '':
            return HarvestAction(repository, stateDir=stateDir, logDir=logDir, generalHarvestLog=generalHarvestLog)
        if repository.use == "" and repository.action == '':
            return NoneAction(repository, stateDir=stateDir, logDir=logDir, generalHarvestLog=generalHarvestLog)
        raise ActionFactoryException("Action '%s' not supported."%repository.action)

class Repository(SaharaObject):
    def __init__(self, domainId, repositoryId):
        SaharaObject.__init__(self, ['repositoryGroupId', 'baseurl', 'set',
            'collection', 'metadataPrefix', 'use',  'targetId', 'mappingId', 'action', 'complete'], ['shopclosed'])
        self.domainId = domainId
        self.id = repositoryId
        self.mockUploader = None
        self.uploadfulltext = True
        self._copyOldStuff()

    def _copyOldStuff(self):
        self.key = self.id
        self.url = self.baseurl
        self.institutionkey = self.repositoryGroupId

    def closedSlots(self):
        if not hasattr(self, '_closedslots'):
            if self.shopclosed:
                self._closedslots = map(lambda txt: Timeslot(txt), self.shopclosed)
            else:
                self._closedslots = []
        return self._closedslots

    def shopClosed(self, dateTuple = time.localtime()[:5]):
        return reduce(lambda lhs, rhs: lhs or rhs, map(lambda x:x.areWeWithinTimeslot( dateTuple), self.closedSlots()), False)

    def target(self):
        return self._saharaget.getTarget(self.domainId, self.targetId)

    def mapping(self):
        return self._saharaget.getMapping(self.domainId, self.mappingId)

    def createUploader(self, logger):
        if self.mockUploader:
            return self.mockUploader
        return UploaderFactory().createUploader(self.target(), logger, self.collection)

    def _createAction(self, stateDir, logDir, generalHarvestLog):
        return ActionFactory().createAction(self, stateDir=stateDir, logDir=logDir, generalHarvestLog=generalHarvestLog)

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
                generalHarvestLog.info('Repository will be completed in one attempt', id=self.id)
            return message, completeHarvest
        except OAIError, e:
            errorMessage = _errorMessage()
            generalHarvestLog.error(errorMessage, id=self.id)
            if e.errorCode() == 'badResumptionToken':
                return errorMessage, self.complete == 'true'
            return errorMessage, False
        except:
            errorMessage = _errorMessage()
            generalHarvestLog.error(errorMessage, id=self.id)
            return errorMessage, False

def _errorMessage():
    xtype,xval,xtb = exc_info()
    return '|'.join(line.strip() for line in format_exception(xtype,xval,xtb))
