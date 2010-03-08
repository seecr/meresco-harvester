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

from harvesterlog import HarvesterLog
from harvester import Harvester, HARVESTED, NOTHING_TO_DO
from state import State
from deleteids import DeleteIds, readIds, writeIds
from os.path import isfile, join
from os import remove, rename

DONE = 'Done.'

class Action(object):
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

    def resetState(self):
        s = State(self._stateDir, self._repository.id)
        try:
            s.setToLastCleanState()
        finally:
            s.close()

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
        self.filename = join(self._stateDir, self._repository.id + '.ids')
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

    def resetState(self):
        s = State(self._stateDir, self._repository.id)
        try:
            s.markDeleted()
        finally:
            s.close()

    def _smoothinit(self):
        if isfile(self.filename):
            rename(self.filename, self.oldfilename)
        else:
            open(self.oldfilename, 'w').close()
        open(self.filename, 'w').close()
        logger = HarvesterLog(self._stateDir, self._logDir, self._repository.id)
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

class ActionFactory(object):
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

