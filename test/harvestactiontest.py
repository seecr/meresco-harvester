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
from cq2utils import CallTrace, CQ2TestCase
from merescoharvester.harvester.repository import HarvestAction
from merescoharvester.harvester.harvesterlog import HarvesterLog
from merescoharvester.harvester.eventlogger import NilEventLogger
from os.path import join

class HarvestActionTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)
        self.harvester = CallTrace("Harvester")
        self._original_createHarvester = HarvestAction._createHarvester
        HarvestAction._createHarvester = lambda instance: self.harvester
        self.repository = CallTrace("Repository")
        self.repository.returnValues['shopClosed'] = False

    def tearDown(self):
        HarvestAction._createHarvester = self._original_createHarvester
        CQ2TestCase.tearDown(self)

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
        self.assertEquals(('2010-03-02', None), (h.from_, h.token))

    def testResetState_ToStateBeforeResumptionToken(self):
        self.writeLogLine(2010, 3, 2, token='')
        self.writeLogLine(2010, 3, 3, token='resumptionToken')
        self.writeLogLine(2010, 3, 4, exception='Exception')
        action = self.newHarvestAction()

        action.resetState()

        h = self.newHarvesterLog()
        self.assertEquals(('2010-03-02', None), (h.from_, h.token))

    def testTheWriteLogLineTestMethod(self):
        self.writeLogLine(2010, 3, 1, token='resumptionToken')
        self.writeLogLine(2010, 3, 2, token='')
        self.writeLogLine(2010, 3, 3, exception='Exception')

        h = self.newHarvesterLog()
        self.assertEquals(('2010-03-02', None), (h.from_, h.token))

    def newHarvestAction(self):
        return HarvestAction(self.repository, stateDir=self.tempdir, logDir=self.tempdir, generalHarvestLog=NilEventLogger())

    def newHarvesterLog(self):
        return HarvesterLog(stateDir=self.tempdir, logDir=self.tempdir, name='repository')

    def writeLogLine(self, year, month, day, token=None, exception=None):
        h = self.newHarvesterLog()
        h._localtime = lambda: (year, month, day, 12, 15, 0, 0, 0, 0)
 
        h.startRepository('The Repository')
        h.begin()
        h.updateStatsfile(4,1,3)
        if exception != None:
            try:
                raise Exception(exception)
            except:
                h.endWithException()
        else:
            h.done()
            h.endRepository(token)
        h.close()
 
