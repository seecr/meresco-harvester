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
# $Id: deleteidstest.py 4825 2007-04-16 13:36:24Z TJ $

import unittest, tempfile, os, shutil
import harvesterlog
from deleteids import DeleteIds, readIds
from sets import Set
from virtualuploader import UploaderException, VirtualUploader
import deleteids

class DeleteIdsTest(unittest.TestCase):
    def _rmtree(self):
        if os.path.isdir(self.testdir):
            shutil.rmtree(self.testdir)
        else:
            os.makedirs(self.testdir)

    def setUp(self):
        self.testdir = os.path.join(tempfile.gettempdir(), 'deleteidstest')
        self._rmtree()
        reload(deleteids)
            
    def tearDown(self):
        self._rmtree()
        
    def testDeleteWithOneFailure(self):
        repository = MockRepositoryAndUploader()
        idfile = file(harvesterlog.idfilename(self.testdir, repository.id), 'w')
        idfile.write('mock:1\nmock:2\n\n\t\nmock:3\nmock:2\nmock:2\n')
        idfile.close()
        self.createStatsFile(repository)
        dt = DeleteIds(repository, self.testdir)
        self.assertEquals(Set(['mock:1','mock:2','mock:3']),dt.ids())
        dt.delete(trials=1)
        dlogfile = os.path.join(self.testdir,'deleteids.log')
        self.assert_(os.path.isfile(dlogfile))
        dlog = open(dlogfile)
        s = Set(map(lambda l:l.split('\t')[2],dlog))
        self.assertEquals(Set(['[mock:1]','[mock:2]','[mock:3]']),s)
        dlog.close()
        dt = DeleteIds(repository, self.testdir)
        self.assertEquals(Set(['mock:3']),dt.ids())
        logger = harvesterlog.HarvesterLog(self.testdir, repository.id)
        self.assert_(logger.from_)
        
    def testDelete(self):
        repository = MockRepositoryAndUploader()
        idfile = file(harvesterlog.idfilename(self.testdir, repository.id), 'w')
        idfile.write('mock:5\nmock:6\nmock:7\nmock:8\nmock:9\n')
        idfile.close()
        self.createStatsFile(repository)
        dt = DeleteIds(repository, self.testdir)
        self.assertEquals(5, len(dt.ids()))
        dt.delete(trials=1)
        dt = DeleteIds(repository, self.testdir)
        self.assertEquals(0, len(dt.ids()))
        logger = harvesterlog.HarvesterLog(self.testdir, repository.id)
        self.assert_(not logger.from_)

    def testDeleteOtherFilename(self):
        repository = MockRepositoryAndUploader()
        filename = os.path.join(self.testdir, 'delete.ids.in.this.file')
        idfile = file(filename, 'w')
        idfile.write('mock:5\nmock:6\nmock:7\nmock:8\nmock:9\n')
        idfile.close()
        self.createStatsFile(repository)
        class MockHarvesterLog:
            def __init__(self, *args, **kwargs):
                raise AssertionError('Should not reach here')

        deleteids.HarvesterLog = MockHarvesterLog
        dt = DeleteIds(repository, self.testdir)
        dt.deleteFile(filename)
        self.assertEquals(0, len(readIds(filename)))
        self.assertEquals(Set(['mock:5','mock:6','mock:7','mock:8','mock:9']),repository.deleted_ids)
        
        logger = harvesterlog.HarvesterLog(self.testdir, repository.id)
        #self.assert_(not logger.from_)

        
    def testDeleteWithCtrlC(self):
        repository = MockRepositoryAndUploader()
        idfile = file(harvesterlog.idfilename(self.testdir, repository.id), 'w')
        idfile.write('mock:11\nmock:12\n\n\t\nmock:13\nmock:14\nmock:15\n')
        idfile.close()
        self.createStatsFile(repository)
        dt = DeleteIds(repository, self.testdir)
        self.assertEquals(5, len(dt.ids()))
        try:
            dt.delete(trials=1)
            self.fail()
        except SystemExit, e:
            pass
        dt = DeleteIds(repository, self.testdir)
        self.assertEquals(3, len(dt.ids()))
        
    def testTrials(self):
        repository = MockRepositoryAndUploader()
        idfile = file(harvesterlog.idfilename(self.testdir, repository.id), 'w')
        idfile.write('mock:21\nmock:22\nmock:23\nmock:24\nmock:25\n')
        idfile.close()
        dt = DeleteIds(repository, self.testdir)
        self.assertEquals(5, len(dt.ids()))
        dt.delete(trials=1)
        dt = DeleteIds(repository, self.testdir)
        self.assertEquals(1, len(dt.ids()))
        self.assertEquals(1, repository.deleteMock24Count)
        dt.delete()
        self.assertEquals(0, len(dt.ids()))
        self.assertEquals(3, repository.deleteMock24Count)
        

    def createStatsFile(self,repository):
        logger = harvesterlog.HarvesterLog(self.testdir, repository.id)
        logger.startRepository('A beautiful name')
        logger.begin()
        logger.updateStatsfile(0,0,0)
        logger.done()
        logger.endRepository(None)
        logger.close()
        

class MockRepositoryAndUploader(VirtualUploader):
    def __init__(self):
        self.id = 'mock'
        self.deleteMock24Count = 0
        self.deleted_ids = Set()
    
    def createUploader(self, logger):
        self.logger = logger
        return self
    
    def delete(self, anUpload):
        id = anUpload.id
        self.logger.logLine('UPLOADER','START deleting',id=id)
        if id == 'mock:3':
            raise UploaderException('Sorry, but the vm has crashed.')
        if id == 'mock:13':
            raise SystemExit()
        if id == 'mock:24':
            self.deleteMock24Count += 1
            if self.deleteMock24Count < 3:
                raise UploaderException('Sorry, but cannot delete mock24')
        self.deleted_ids.add(id)
        self.logger.logLine('UPLOADER','END deleting',id=id)

if __name__ == '__main__':
    unittest.main()
