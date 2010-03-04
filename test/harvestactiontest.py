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
from merescoharvester.harvester.eventlogger import NilEventLogger

class HarvestActionTest(CQ2TestCase):
    def testHarvestAction(self):
        repository = CallTrace("Repository")
        harvester = CallTrace("Harvester")
        repository.returnValues['shopClosed'] = False
        harvester.returnValues['harvest'] = ('', False)
        action = HarvestAction(repository, stateDir=self.tempdir, logDir=self.tempdir, generalHarvestLog=NilEventLogger())
        action._createHarvester = lambda: harvester

        action.do()

        self.assertEquals(['harvest()'], harvester.__calltrace__())

    def testShopClosed(self):
        repository = CallTrace("Repository")
        harvester = CallTrace("Harvester")
        repository.returnValues['shopClosed'] = True
        harvester = CallTrace("Harvester")
        action = HarvestAction(repository, stateDir=self.tempdir, logDir=self.tempdir, generalHarvestLog=NilEventLogger())
        action._createHarvester = lambda: harvester

        action.do()

        self.assertEquals([], harvester.__calltrace__())
