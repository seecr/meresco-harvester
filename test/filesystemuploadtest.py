# -*- coding: utf-8 -*-
## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for 
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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
import unittest
from merescoharvester.harvester.filesystemuploader import FileSystemUploader
from merescoharvester.harvester.virtualuploader import UploaderException
from cq2utils.calltrace import CallTrace
from cq2utils.wrappers import wrapp
import os, shutil
from cq2utils import binderytools
from cq2utils.cq2testcase import CQ2TestCase
from tempfile import mkdtemp

class FileSystemUploaderTest(CQ2TestCase):

    def setUp(self):
        self.tempdir = mkdtemp()
        self.target = CallTrace("Target")
        self.target.path = self.tempdir
        logger = CallTrace("Logger")
        collection = ''
        self.uploader = FileSystemUploader(self.target, logger, collection)
        
    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)
    
    def testFilenameForId(self):
        def getFilename(anId):
            repository = CallTrace('Repository')
            repository.repositoryGroupId = 'groupId'
            repository.id = 'repositoryId'
            
            upload = CallTrace('Upload')
            upload.id = anId
            upload.repository = repository
            return self.uploader._filenameFor(upload)

        self.assertEquals(self.tempdir + '/groupId/repositoryId/aa:bb_SLASH_cc.dd.record', getFilename('aa:bb/cc.dd'))
        self.assertTrue(getFilename('.').startswith(self.tempdir + '/groupId/repositoryId/_malformed_id.'))
        self.assertTrue(getFilename('..').startswith(self.tempdir + '/groupId/repositoryId/_malformed_id.'))
        self.assertTrue(getFilename('').startswith(self.tempdir + '/groupId/repositoryId/_malformed_id.'))
        self.assertTrue(getFilename('a'*256).startswith(self.tempdir + '/groupId/repositoryId/_malformed_id.'))

    def testDelete(self):
        recordFile = self.tempdir + '/id.record'
        os.system('touch ' + recordFile)
        self.assertTrue(os.path.isfile(recordFile))
        self.uploader._filenameFor = lambda *args: recordFile
        
        repository = CallTrace('Repository')
        repository.repositoryGroupId = 'groupId'
        repository.id = 'repositoryId'
        
        upload = CallTrace('Upload')
        upload.id = 'id'
        upload.repository = repository
        
        self.uploader.delete(upload)
        
        self.assertTrue(os.path.isfile(self.tempdir + '/deleted_records'))
        self.assertEquals(['id\n'], open(self.tempdir + '/deleted_records').readlines())
        self.assertFalse(os.path.isfile(recordFile))
        
        upload.id = 'second:id'
        self.uploader.delete(upload)
        self.assertEquals(['id\n', 'second:id\n'], open(self.tempdir + '/deleted_records').readlines())

    def testSend(self):
        recordFile = self.tempdir + '/group/repo/id.record'
        self.uploader._filenameFor = lambda *args: recordFile
        
        upload = createUpload()
        self.uploader.send(upload)
        
        self.assertTrue(os.path.isfile(recordFile))
        self.assertEquals('<?xml version="1.0" encoding="UTF-8"?>\n'+RECORD, open(recordFile).read())

    def testSendWithAbout(self):
        ABOUT = "<about>abouttext</about>"
        recordFile = self.tempdir + '/group/repo/id.record'
        self.uploader._filenameFor = lambda *args: recordFile
        
        upload = createUploadWithAbout(about=ABOUT)
        self.uploader.send(upload)
        
        self.assertTrue(os.path.isfile(recordFile))
        self.assertEquals('<?xml version="1.0" encoding="UTF-8"?>\n'+RECORD_WITH_ABOUT % ABOUT, open(recordFile).read())

    def testSendWithMultipleAbout(self):
        ABOUT = "<about>about_1</about><about>about_2</about>"
        
        recordFile = self.tempdir + '/group/repo/id.record'
        self.uploader._filenameFor = lambda *args: recordFile
        
        upload = createUploadWithAbout(about=ABOUT)
        self.uploader.send(upload)
        
        self.assertTrue(os.path.isfile(recordFile))
        self.assertEquals('<?xml version="1.0" encoding="UTF-8"?>\n'+RECORD_WITH_ABOUT % ABOUT, open(recordFile).read())

    def testSendRaisesError(self):
        def raiseError(*args, **kwargs):
            raise Exception('Catch me')
        self.uploader._filenameFor = raiseError
        
        try:
            upload = createUpload()
            self.uploader.send(upload)
            self.fail()
        except UploaderException:
            pass

        
    def testSendOaiEnvelope(self):
        self.target.oaiEnvelope = 'true'
        recordFile = self.tempdir + '/group/repo/id.record'
        self.uploader._filenameFor = lambda *args: recordFile
        
        upload = createUpload()
        upload.repository = CallTrace('Repository')
        upload.repository.baseurl = 'http://www.example.com'
        upload.repository.metadataPrefix = 'weird&strange'
        
        self.uploader.send(upload)
        
        self.assertTrue(os.path.isfile(recordFile))
        xmlGetRecord = binderytools.bind_file(recordFile)
        self.assertEquals('header', str(xmlGetRecord.OAI_PMH.GetRecord.record.header))
        self.assertEquals('http://www.example.com', str(xmlGetRecord.OAI_PMH.request))
        self.assertEquals('weird&strange', str(xmlGetRecord.OAI_PMH.request.metadataPrefix))
        
    def testSendTwice(self):
        self.testSend()
        self.testSend()

def createUpload():
    upload = CallTrace("Upload")
    record = wrapp(binderytools.bind_string("""<record xmlns="http://www.openarchives.org/OAI/2.0/">
    <header>header</header>
    <metadata>text</metadata>
</record>"""))
    
    upload.header = record.record.header
    upload.metadata = record.record.metadata
    upload.about = record.record.about
    upload.id = 'id'
    return upload
    
def createUploadWithAbout(about):
    upload = CallTrace("Upload")
    record = wrapp(binderytools.bind_string("""<record xmlns="http://www.openarchives.org/OAI/2.0/">
    <header>header</header>
    <metadata>text</metadata>
    %s
</record>""" % about))
    
    upload.header = record.record.header
    upload.metadata = record.record.metadata
    upload.about = record.record.about

    upload.id = 'id'
    return upload
        
RECORD = """<record xmlns="http://www.openarchives.org/OAI/2.0/"><header>header</header><metadata>text</metadata></record>"""
RECORD_WITH_ABOUT = """<record xmlns="http://www.openarchives.org/OAI/2.0/"><header>header</header><metadata>text</metadata>%s</record>"""
