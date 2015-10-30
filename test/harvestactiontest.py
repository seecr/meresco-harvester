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
# Copyright (C) 2012, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from actiontestcase import ActionTestCase
from seecr.test import CallTrace
from meresco.harvester.action import HarvestAction
from meresco.harvester.eventlogger import NilEventLogger

class HarvestActionTest(ActionTestCase):
    def setUp(self):
        ActionTestCase.setUp(self)
        self.harvester = CallTrace("Harvester")
        self._original_createHarvester = HarvestAction._createHarvester
        HarvestAction._createHarvester = lambda instance: self.harvester

    def tearDown(self):
        HarvestAction._createHarvester = self._original_createHarvester
        ActionTestCase.tearDown(self)

    def testHarvestAction(self):
        self.harvester.returnValues['harvest'] = ('', False)
        action = HarvestAction(self.repository, stateDir=self.tempdir, logDir=self.tempdir, generalHarvestLog=NilEventLogger())

        action.do()

        self.assertEquals(['harvest'], [m.name for m in self.harvester.calledMethods])

    def testShopClosed(self):
        self.repository.returnValues['shopClosed'] = True
        action = HarvestAction(self.repository, stateDir=self.tempdir, logDir=self.tempdir, generalHarvestLog=NilEventLogger())

        action.do()

        self.assertEquals([], [m.name for m in self.harvester.calledMethods])

    def testResetState_LastStateIsAlreadyGood(self):
        self.writeLogLine(2010, 3, 1, token='resumptionToken')
        self.writeLogLine(2010, 3, 2, token='')
        self.writeLogLine(2010, 3, 3, exception='Exception')
        action = self.newHarvestAction()

        action.resetState()

        h = self.newHarvesterLog()
        self.assertEquals(('2010-03-01T12:15:00Z', None), (h._state.from_, h._state.token))

    def testResetState_ToStateBeforeResumptionToken(self):
        self.writeLogLine(2010, 3, 2, token='')
        self.writeLogLine(2010, 3, 3, token='resumptionToken')
        self.writeLogLine(2010, 3, 4, exception='Exception')
        action = self.newHarvestAction()

        action.resetState()

        h = self.newHarvesterLog()
        self.assertEquals(('2010-03-03T12:15:00Z', None), (h._state.from_, h._state.token))

    def testResetState_ToStartAllOver(self):
        self.writeLogLine(2010, 3, 3, token='resumptionToken')
        self.writeLogLine(2010, 3, 4, exception='Exception')
        action = self.newHarvestAction()

        action.resetState()

        h = self.newHarvesterLog()
        self.assertEquals(('2010-03-03T12:15:00Z', None), (h._state.from_, h._state.token))

    def newHarvestAction(self):
        return HarvestAction(self.repository, stateDir=self.tempdir, logDir=self.tempdir, generalHarvestLog=NilEventLogger())

