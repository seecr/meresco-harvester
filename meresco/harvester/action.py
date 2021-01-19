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
# Copyright (C) 2010-2011, 2015 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2015, 2017 Seecr (Seek You Too B.V.) http://seecr.nl
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

from os.path import isfile, join
from os import remove

from weightless.core import be

from .deleteids import DeleteIds
from .eventlogger import CompositeLogger, EventLogger
from .harvester import Harvester, NOTHING_TO_DO
from .harvesterlog import HarvesterLog
from .state import State
from .ids import readIds, writeIds


class Action(object):
    def __init__(self, repository, stateDir, logDir, generalHarvestLog):
        self._repository = repository
        self._stateDir = stateDir
        self._logDir = logDir
        self._generalHarvestLog = generalHarvestLog
        self.invalidIdsFilename = join(self._stateDir, self._repository.id + '_invalid.ids')

    @staticmethod
    def create(repository, stateDir, logDir, generalHarvestLog):
        actionUse2Class = {
            'clear': lambda use: DeleteIdsAction,
            'refresh': lambda use: SmoothAction,
            None: lambda use: {True: HarvestAction, False: NoneAction, None: NoneAction}[use]
        }
        try:
            actionClass = actionUse2Class[repository.action](repository.use)
            return actionClass(repository, stateDir=stateDir, logDir=logDir, generalHarvestLog=generalHarvestLog)
        except KeyError:
            raise ActionException("Action '%s' not supported." % repository.action)

    def do(self):
        """
        perform action and return
            (if the action is finished/done, a Message about what happened, hasResumptionToken)
        """
        raise NotImplementedError

    def info(self):
        return  str(self.__class__.__name__)

    def _createHarvester(self):
        harvesterLog = HarvesterLog(self._stateDir, self._logDir, self._repository.id)
        eventlogger = CompositeLogger([
            (['*'], harvesterLog.eventLogger()),
            (['ERROR', 'INFO', 'WARN'], self._generalHarvestLog)
        ])
        uploader = self._repository.createUploader(eventlogger)
        mapping = self._repository.mapping()
        oairequest = self._repository.oairequest()
        helix = \
            (Harvester(self._repository),
                (oairequest,),
                (harvesterLog,),
                (eventlogger,),
                (uploader,),
                (mapping,
                    (eventlogger,)
                ),
            )
        return [harvesterLog], be(helix)

    def _createDeleteIds(self):
        harvesterLog = HarvesterLog(self._stateDir, self._logDir, self._repository.id)
        deleteIdsLog = EventLogger(join(self._logDir, 'deleteids.log'))
        eventlogger = CompositeLogger([
            (['*'], deleteIdsLog),
            (['*'], harvesterLog.eventLogger()),
            (['ERROR', 'INFO', 'WARN'], self._generalHarvestLog),
        ])
        uploader = self._repository.createUploader(eventlogger)
        helix = \
            (DeleteIds(self._repository, self._stateDir),
                (harvesterLog,),
                (eventlogger,),
                (uploader,),
            )
        return [harvesterLog, deleteIdsLog], be(helix)


class NoneAction(Action):
    def do(self):
        return False, '', False
    def info(self):
        return ''


class HarvestAction(Action):
    def do(self):
        if self._repository.shopClosed():
            return False, 'Not harvesting outside timeslots.', False

        _, harvester = self._createHarvester()
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

        self.filename = join(self._stateDir, self._repository.id + '.ids')

        loggers, d = self._createDeleteIds()
        try:
            d.deleteFile(self.filename)
            d.deleteFile(self.invalidIdsFilename)
            d.markDeleted()
        finally:
            for each in loggers:
                each.close()
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
            writeIds(self.oldfilename, sorted(set(readIds(self.filename) + readIds(self.invalidIdsFilename))))
            writeIds(self.filename, set())
        else:
            open(self.oldfilename, 'w').close()
        loggers, d = self._createDeleteIds()
        try:
            d.markDeleted()
        finally:
            for each in loggers:
                each.close()
        return 'initialized.'

    def _finish(self):
        deletefilename = self.filename + '.delete'
        if not isfile(deletefilename):
            writeIds(deletefilename, sorted(set(readIds(self.oldfilename)) - set(readIds(self.filename))))
        self._delete(deletefilename)
        remove(self.oldfilename)
        remove(deletefilename)
        return DONE

    def _delete(self, filename):
        loggers, d = self._createDeleteIds()
        try:
            d.deleteFile(filename)
        finally:
            for each in loggers:
                each.close()

    def _harvest(self):
        loggers, harvester = self._createHarvester()
        try:
            return harvester.harvest()
        finally:
            for each in loggers:
                each.close()

DONE = 'Done.'

class ActionException(Exception):
    pass

