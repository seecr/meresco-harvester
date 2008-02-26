#!/usr/bin/env python
## begin license ##
#
#    "Sahara" consists of two subsystems, namely an OAI-harvester and a web-control panel.
#    "Sahara" is developed for SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006,2007 SURFnet B.V. http://www.surfnet.nl
#
#    This file is part of "Sahara"
#
#    "Sahara" is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    "Sahara" is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with "Sahara"; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
#
# (c) 2005 Seek You Too B.V.
#
# $Id: smoothactiontest.py 4825 2007-04-16 13:36:24Z TJ $

import unittest, shutil, os, tempfile
from repository import Repository, SmoothAction, DONE
from cq2utils.wrappers import wrapp
from harvester import HARVESTED, NOTHING_TO_DO
from deleteids import readIds
import repository
from sets import Set

class SmoothActionTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repository('domainId', 'rep')
        self.logpath = os.path.join(tempfile.tempdir, 'repositorytest')
        os.path.isdir(self.logpath) or os.mkdir(self.logpath)
        self.smoothaction = SmoothAction(self.repo, self.logpath)
        self.idfilename = os.path.join(self.logpath, 'rep.ids')
        self.old_idfilename = os.path.join(self.logpath, 'rep.ids.old')
        self.statsfilename = os.path.join(self.logpath,'rep.stats')

    def tearDown(self):
        shutil.rmtree(self.logpath)

    def testSmooth_Init(self):
        writefile(self.idfilename, 'rep:id:1\nrep:id:2\n')
        writefile(self.statsfilename, 'Started: 2005-12-22 16:33:39, Harvested/Uploaded/Deleted/Total: 10/10/0/2, Done: ResumptionToken:\n')
        
        self.assert_(not os.path.isfile(self.old_idfilename))
        
        done,message = self.smoothaction.do()
        
        self.assert_(os.path.isfile(self.old_idfilename))
        self.assert_(os.path.isfile(self.idfilename))
        self.assertEquals('rep:id:1\nrep:id:2\n', readfile(self.old_idfilename))
        self.assertEquals('', readfile(self.idfilename))
        self.assert_('Done: Deleted all id\'s' in  readfile(self.statsfilename))
        self.assertEquals('Smooth reharvest: initialized.', message)
        self.assert_(not done)
        
    def testSmooth_InitWithNothingHarvestedYetRepository(self):
        self.assert_(not os.path.isfile(self.idfilename))
        self.assert_(not os.path.isfile(self.old_idfilename))
        self.assert_(not os.path.isfile(self.statsfilename))
        
        done,message = self.smoothaction.do()
        
        self.assert_(os.path.isfile(self.old_idfilename))
        self.assert_(os.path.isfile(self.idfilename))
        self.assertEquals('', readfile(self.old_idfilename))
        self.assertEquals('', readfile(self.idfilename))
        self.assert_('Done: Deleted all id\'s' in  readfile(self.statsfilename))
        self.assertEquals('Smooth reharvest: initialized.', message)
        self.assert_(not done)
        
        
    def testSmooth_Harvest(self):
        writefile(self.old_idfilename, 'rep:id:1\nrep:id:2\n')
        writefile(self.idfilename, '')
        writefile(self.statsfilename, 'Started: 2005-12-22 16:33:39, Harvested/Uploaded/Deleted/Total: 10/10/0/2, Done: ResumptionToken:\n'+
        'Started: 2005-12-28 10:10:10, Harvested/Uploaded/Deleted/Total: 0/0/0/0, Done: Deleted all id\'s. \n')
        
        self.smoothaction._harvest = lambda:HARVESTED
        done,message = self.smoothaction.do()
        
        self.assertEquals('Smooth reharvest: Harvested.', message)
        self.assert_(not done)

    def testSmooth_HarvestAgain(self):
        writefile(self.old_idfilename, 'rep:id:1\nrep:id:2\n')
        writefile(self.idfilename, 'rep:id:41\nrep:id:2\n')
        writefile(self.statsfilename, 'Started: 2005-12-22 16:33:39, Harvested/Uploaded/Deleted/Total: 10/10/0/2, Done: ResumptionToken:\n'+
        'Started: 2005-12-28 10:10:10, Harvested/Uploaded/Deleted/Total: 2/2/0/2, Done: ResumptionToken:yes \n')
        
        self.smoothaction._harvest = lambda:HARVESTED
        done, message = self.smoothaction.do()
        
        self.assertEquals('Smooth reharvest: Harvested.', message)
        self.assert_(not done)
        
    def testSmooth_NothingToDo(self):
        writefile(self.old_idfilename, 'rep:id:1\nrep:id:2\n')
        writefile(self.idfilename, 'rep:id:41\nrep:id:2\n')
        writefile(self.statsfilename, 'Started: 2005-12-22 16:33:39, Harvested/Uploaded/Deleted/Total: 10/10/0/2, Done: ResumptionToken:\n'+
        'Started: 2005-12-28 10:10:10, Harvested/Uploaded/Deleted/Total: 2/2/0/2, Done: ResumptionToken:None \n')
        
        self.smoothaction._harvest = lambda:NOTHING_TO_DO
        self.smoothaction._finish = lambda:DONE
        done, message = self.smoothaction.do()
        
        self.assertEquals('Smooth reharvest: ' + DONE, message)
        self.assert_(done)
        
    def mockdelete(self, filename):
        self.mockdelete_filename = filename
        self.mockdelete_ids = readIds(filename)
        
    def testSmooth_Finish(self):
        writefile(self.old_idfilename, 'rep:id:1\nrep:id:2\n')
        writefile(self.idfilename, 'rep:id:41\nrep:id:2\n')
    
        self.smoothaction._delete=self.mockdelete
        result = self.smoothaction._finish()
    
        self.assert_(not os.path.isfile(self.old_idfilename))
        self.assertEquals(DONE, result)
        self.assertEquals(self.idfilename+'.delete', self.mockdelete_filename)
        self.assertEquals(Set(['rep:id:1']), self.mockdelete_ids)
    
    def testSmooth_Delete(self):
        class MockDelete:
            usedrep, usedlogpath,filename = None, None, None
            def __init__(self, rep, logpath):
                MockDelete.usedrep = rep
                MockDelete.usedlogpath = logpath
            def deleteFile(self, filename):
                MockDelete.filename = filename
        repository.DeleteIds = MockDelete
        self.smoothaction._delete(self.idfilename+'.delete') 
        self.assertEquals(self.idfilename + '.delete', MockDelete.filename)
        self.assertEquals(self.repo, MockDelete.usedrep)
        self.assertEquals(self.logpath, MockDelete.usedlogpath)
        
    
    def testHarvest(self):
        class MockHarvester:
            usedrep, usedlogpath = None, 'some path'
            def __init__(self, rep, logpath):
                MockHarvester.usedrep = rep
                MockHarvester.usedlogpath = logpath
            def harvest(self):
                return 'mockharvest'
        repository.Harvester = MockHarvester
        self.assertEquals('mockharvest', self.smoothaction._harvest())
        self.assertEquals(self.repo, MockHarvester.usedrep)
        self.assertEquals(self.logpath, MockHarvester.usedlogpath)
    
    # harvest klaar, dan deleten. en een .ids.old file. (smoothfinish/ eerst smoothinit, dan harvesten)
    # xml aanpassen.
    # xml aanpassen op de server + edit template XSLT
    # harvest gooit exception.

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

