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
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
# 
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
import shutil, os
from os.path import join
from tempfile import mkdtemp
from meresco.harvester.repository import Repository
from meresco.harvester.action import SmoothAction, DONE
from slowfoot.wrappers import wrapp
from meresco.harvester.harvester import HARVESTED, NOTHING_TO_DO
from meresco.harvester.deleteids import readIds
from meresco.harvester import action
from sets import Set
from meresco.harvester.eventlogger import NilEventLogger
from cq2utils import CallTrace

class SmoothActionTest(ActionTestCase):
    def setUp(self):
        ActionTestCase.setUp(self)
        self.repo = Repository('domainId', 'rep')
        self.uploader = CallTrace('Uploader')
        self.repo.createUploader = lambda logger: self.uploader
        self.stateDir = self.tempdir
        self.logDir = self.tempdir
        self.smoothaction = SmoothAction(self.repo, self.stateDir, self.logDir, NilEventLogger())
        self.idfilename = join(self.stateDir, 'rep.ids')
        self.ignoreidfilename = join(self.stateDir, 'rep_ignored.ids')
        self.old_idfilename = join(self.stateDir, 'rep.ids.old')
        self.statsfilename = join(self.stateDir,'rep.stats')

    def testSmooth_Init(self):
        writefile(self.idfilename, 'rep:id:1\nrep:id:2\n')
        writefile(self.ignoreidfilename, 'rep:id:3\n')
        writefile(self.statsfilename, 'Started: 2005-12-22 16:33:39, Harvested/Uploaded/Deleted/Total: 10/10/0/2, Done: ResumptionToken:\n')

        self.assertFalse(os.path.isfile(self.old_idfilename))

        done,message, hasResumptionToken = self.smoothaction.do()

        self.assertTrue(os.path.isfile(self.old_idfilename))
        self.assertTrue(os.path.isfile(self.idfilename))
        self.assertEquals('rep:id:1\nrep:id:2\nrep:id:3\n', readfile(self.old_idfilename))
        self.assertEquals('', readfile(self.idfilename))
        self.assertTrue('Done: Deleted all id\'s' in  readfile(self.statsfilename))
        self.assertEquals('Smooth reharvest: initialized.', message)
        self.assertFalse(done)

    def testSmooth_InitWithNothingHarvestedYetRepository(self):
        self.assertFalse(os.path.isfile(self.idfilename))
        self.assertFalse(os.path.isfile(self.ignoreidfilename))
        self.assertFalse(os.path.isfile(self.old_idfilename))
        self.assertFalse(os.path.isfile(self.statsfilename))

        done,message, hasResumptionToken = self.smoothaction.do()

        self.assertTrue(os.path.isfile(self.old_idfilename))
        self.assertTrue(os.path.isfile(self.idfilename))
        self.assertTrue(os.path.isfile(self.ignoreidfilename))
        self.assertEquals('', readfile(self.old_idfilename))
        self.assertEquals('', readfile(self.idfilename))
        self.assertEquals('', readfile(self.ignoreidfilename))
        self.assertTrue('Done: Deleted all id\'s' in  readfile(self.statsfilename))
        self.assertEquals('Smooth reharvest: initialized.', message)
        self.assertFalse(done)


    def testSmooth_Harvest(self):
        writefile(self.old_idfilename, 'rep:id:1\nrep:id:2\n')
        writefile(self.idfilename, '')
        writefile(self.statsfilename, 'Started: 2005-12-22 16:33:39, Harvested/Uploaded/Deleted/Total: 10/10/0/2, Done: ResumptionToken:\n'+
        'Started: 2005-12-28 10:10:10, Harvested/Uploaded/Deleted/Total: 0/0/0/0, Done: Deleted all id\'s. \n')

        self.smoothaction._harvest = lambda:(HARVESTED, False)
        done,message,hasResumptionToken = self.smoothaction.do()

        self.assertEquals('Smooth reharvest: Harvested.', message)
        self.assertFalse(done)

    def testSmooth_HarvestAgain(self):
        writefile(self.old_idfilename, 'rep:id:1\nrep:id:2\n')
        writefile(self.idfilename, 'rep:id:41\nrep:id:2\n')
        writefile(self.statsfilename, 'Started: 2005-12-22 16:33:39, Harvested/Uploaded/Deleted/Total: 10/10/0/2, Done: ResumptionToken:\n'+
        'Started: 2005-12-28 10:10:10, Harvested/Uploaded/Deleted/Total: 2/2/0/2, Done: ResumptionToken:yes \n')

        self.smoothaction._harvest = lambda:(HARVESTED, False)
        done, message, hasResumptionToken = self.smoothaction.do()

        self.assertEquals('Smooth reharvest: Harvested.', message)
        self.assertFalse(done)

    def testSmooth_NothingToDo(self):
        writefile(self.old_idfilename, 'rep:id:1\nrep:id:2\n')
        writefile(self.idfilename, 'rep:id:41\nrep:id:2\n')
        writefile(self.statsfilename, 'Started: 2005-12-22 16:33:39, Harvested/Uploaded/Deleted/Total: 10/10/0/2, Done: ResumptionToken:\n'+
        'Started: 2005-12-28 10:10:10, Harvested/Uploaded/Deleted/Total: 2/2/0/2, Done: ResumptionToken:None \n')

        self.smoothaction._harvest = lambda:(NOTHING_TO_DO, False)
        self.smoothaction._finish = lambda:DONE
        done, message, hasResumptionToken = self.smoothaction.do()

        self.assertEquals('Smooth reharvest: ' + DONE, message)
        self.assertTrue(done)

    def mockdelete(self, filename):
        self.mockdelete_filename = filename
        self.mockdelete_ids = readIds(filename)

    def testHarvest(self):
        harvester = CallTrace('harvester')
        self.smoothaction._createHarvester = lambda: harvester
        harvester.returnValues['harvest'] = ('result', True)

        result = self.smoothaction._harvest()
        self.assertEquals(['harvest'], [m.name for m in harvester.calledMethods]) 
        self.assertEquals(('result', True), result)

    def testResetState_WithoutPreviousCleanState(self):
        self.writeLogLine(2010, 3, 1, token='resumptionToken')
        self.writeLogLine(2010, 3, 2, token='resumptionToken')
        self.writeLogLine(2010, 3, 3, exception='Exception')
        action = self.newSmoothAction()

        action.resetState()

        h = self.newHarvesterLog()
        self.assertEquals((None, None), (h.from_, h.token))

    def testResetState_ToPreviousCleanState(self):
        self.writeLogLine(2010, 3, 2, token='')
        self.writeMarkDeleted(2010, 3, 3)
        self.writeLogLine(2010, 3, 4, token='resumptionToken')
        self.writeLogLine(2010, 3, 5, token='resumptionToken')
        self.writeLogLine(2010, 3, 6, exception='Exception')
        action = self.newSmoothAction()

        action.resetState()

        h = self.newHarvesterLog()
        self.assertEquals((None, None), (h.from_, h.token))

    def testResetState_ToStartAllOver(self):
        self.writeLogLine(2010, 3, 3, token='resumptionToken')
        self.writeLogLine(2010, 3, 4, exception='Exception')
        action = self.newSmoothAction()

        action.resetState()

        h = self.newHarvesterLog()
        self.assertEquals((None, None), (h.from_, h.token))
    
    def newSmoothAction(self):
        action = SmoothAction(self.repository, stateDir=self.tempdir, logDir=self.tempdir, generalHarvestLog=NilEventLogger())
        action._harvest = lambda:None
        return action

def writefile(filename, contents):
    f = open(filename,'w')
    try:
        f.write(contents)
    finally:
        f.close()

def readfile(filename):
    f = open(filename)
    try:
        return f.read()
    finally:
        f.close()

