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
from meresco.harvester.harvester import harvesterlog
from meresco.harvester.harvester.deleteids import DeleteIds, readIds
from sets import Set
from meresco.harvester.harvester.virtualuploader import UploaderException, VirtualUploader
from meresco.harvester.harvester import deleteids
from tempfile import mkdtemp
from shutil import rmtree
from os.path import join, isfile
from os import makedirs


class DeleteIdsTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)
        self.stateDir = join(self.tempdir, 'state')
        makedirs(self.stateDir)
        self.logDir = join(self.tempdir, 'log')

    def testDeleteWithFailure(self):
        repository = MockRepositoryAndUploader()
        idfile = file(harvesterlog.idfilename(self.stateDir, repository.id), 'w')
        idfile.write('mock:1\nmock:2\n\n\t\nmock:raises:server:crash\nmock:2\nmock:2\n')
        idfile.close()
        self.createStatsFile(repository)
        dt = DeleteIds(repository, self.stateDir, self.logDir)
        self.assertEquals(Set(['mock:1','mock:2','mock:raises:server:crash']),dt.ids())
        try:
            dt.delete()
            self.fail()
        except UploaderException, e:
            self.assertTrue('crashed' in str(e))
        dlogfile = join(self.logDir,'deleteids.log')
        self.assertTrue(isfile(dlogfile))
        dlog = open(dlogfile).read()
        self.assertTrue('[mock:raises:server:crash]' in dlog, dlog)
        dt = DeleteIds(repository, self.stateDir, self.logDir)
        self.assertTrue('mock:raises:server:crash' in dt.ids(), dt.ids())
        
    def testDelete(self):
        repository = MockRepositoryAndUploader()
        idfile = file(harvesterlog.idfilename(self.stateDir, repository.id), 'w')
        idfile.write('mock:5\nmock:6\nmock:7\nmock:8\nmock:9\n')
        idfile.close()
        self.createStatsFile(repository)
        dt = DeleteIds(repository, self.stateDir, self.logDir)
        self.assertEquals(5, len(dt.ids()))
        dt.delete()
        dt = DeleteIds(repository, self.stateDir, self.logDir)
        self.assertEquals(0, len(dt.ids()))
        logger = harvesterlog.HarvesterLog(self.stateDir, self.logDir, repository.id)
        self.assert_(not logger.from_)

    def testDeleteUsesUploadObjectWithRepository(self):
        """This will test a bug found in May 2008 by KennisNet
        The FileSystemUploader needs a repository object in the
        Upload object."""
        repository = MockRepositoryAndUploader()
        idfile = file(harvesterlog.idfilename(self.stateDir, repository.id), 'w')
        idfile.write('mock:5\n')
        idfile.close()
        self.createStatsFile(repository)
        dt = DeleteIds(repository, self.stateDir, self.logDir)
        self.assertEquals(0, len(repository.uploads))
        dt.delete()
        self.assertEquals(1, len(repository.uploads))
        self.assertEquals(repository, repository.uploads[0].repository)

    def testDeleteOtherFilename(self):
        repository = MockRepositoryAndUploader()
        filename = join(self.stateDir, 'delete.ids.in.this.file')
        idfile = file(filename, 'w')
        idfile.write('mock:5\nmock:6\nmock:7\nmock:8\nmock:9\n')
        idfile.close()
        self.createStatsFile(repository)
        dt = DeleteIds(repository, self.stateDir, self.logDir)
        dt.deleteFile(filename)
        self.assertEquals(0, len(readIds(filename)))
        self.assertEquals(Set(['mock:5','mock:6','mock:7','mock:8','mock:9']),repository.deleted_ids)
        
        logger = harvesterlog.HarvesterLog(self.stateDir, self.logDir, repository.id)
        
    def testDeleteWithCtrlC(self):
        repository = MockRepositoryAndUploader()
        idfile = file(harvesterlog.idfilename(self.stateDir, repository.id), 'w')
        idfile.write('mock:b\n\n\t\nmock:raises:system:exit\nmock:14\nmock:15\n')
        idfile.close()
        self.createStatsFile(repository)
        dt = DeleteIds(repository, self.stateDir, self.logDir)
        self.assertEquals(4, len(dt.ids()))
        try:
            dt.delete()
            self.fail()
        except SystemExit, e:
            pass
        dt = DeleteIds(repository, self.stateDir, self.logDir)
        self.assertEquals(3, len(dt.ids()))
        
    def createStatsFile(self,repository):
        logger = harvesterlog.HarvesterLog(self.stateDir, self.logDir, repository.id)
        logger.startRepository()
        logger.endRepository(None)
        logger.close()
        

class MockRepositoryAndUploader(VirtualUploader):
    def __init__(self):
        self.id = 'mock'
        self.deleteMock24Count = 0
        self.deleted_ids = Set()
        self.uploads = []
    
    def createUploader(self, logger):
        self.logger = logger
        return self
    
    def delete(self, anUpload):
        id = anUpload.id
        self.uploads.append(anUpload)
        self.logger.logLine('UPLOADER','START deleting',id=id)
        if id == 'mock:raises:server:crash':
            raise UploaderException(uploadId=id, message='Sorry, but the vm has crashed.')
        if id == 'mock:raises:system:exit':
            raise SystemExit()
        self.deleted_ids.add(id)
        self.logger.logLine('UPLOADER','END deleting',id=id)
