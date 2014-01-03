# -*- coding: utf-8 -*-
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
# Copyright (C) 2013-2014 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.harvester.filesystemuploader import FileSystemUploader
from meresco.harvester.virtualuploader import UploaderException
from seecr.test import CallTrace, SeecrTestCase
import os, shutil
from tempfile import mkdtemp
from meresco.harvester.mapping import Upload

from os.path import isfile, join
from lxml.etree import XML, parse
from meresco.harvester.namespaces import namespaces, xpathFirst, xpath
from oairequesttest import oaiResponse
from meresco.components import lxmltostring

class FileSystemUploaderTest(SeecrTestCase):

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

            upload = Upload(repository=repository)
            upload.id = anId
            return self.uploader._filenameFor(upload)

        self.assertEquals(self.tempdir + '/groupId/repositoryId/aa:bb_SLASH_cc.dd.record', getFilename('aa:bb/cc.dd'))
        self.assertTrue(getFilename('.').startswith(self.tempdir + '/groupId/repositoryId/_malformed_id.'))
        self.assertTrue(getFilename('..').startswith(self.tempdir + '/groupId/repositoryId/_malformed_id.'))
        self.assertTrue(getFilename('').startswith(self.tempdir + '/groupId/repositoryId/_malformed_id.'))
        self.assertTrue(getFilename('a'*256).startswith(self.tempdir + '/groupId/repositoryId/_malformed_id.'))

    def testDeleteWithoutOaiEnvelope(self):
        recordFile = join(self.tempdir, 'id.record')
        os.system('touch ' + recordFile)
        self.assertTrue(isfile(recordFile))
        self.uploader._filenameFor = lambda *args: recordFile
        self.target.oaiEnvelope = 'false'

        repository = CallTrace('Repository')
        repository.repositoryGroupId = 'groupId'
        repository.id = 'repositoryId'


        upload = Upload(repository=repository)
        upload.id = 'id'

        self.uploader.delete(upload)

        DELETED_RECORDS = join(self.tempdir, 'deleted_records')

        self.assertTrue(isfile(DELETED_RECORDS))
        self.assertEquals(['id\n'], open(DELETED_RECORDS).readlines())
        self.assertFalse(isfile(recordFile))

        upload.id = 'second:id'
        self.uploader.delete(upload)
        self.assertEquals(['id\n', 'second:id\n'], open(DELETED_RECORDS).readlines())

    def testDeleteWithOaiEnvelope(self):
        RECORD_FILENAME = join(self.tempdir, 'id.record')
        self.uploader._filenameFor = lambda *args: RECORD_FILENAME
        self.uploader.tznow = lambda: "VANDAAG_EN_NU"
        self.target.oaiEnvelope = 'true'

        repository = CallTrace('Repository')
        repository.repositoryGroupId = 'groupId'
        repository.metadataPrefix = 'oai_dc'
        repository.baseurl = "http://repository"
        repository.id = 'repositoryId'

        upload = Upload(repository=repository, oaiResponse=oaiResponse(identifier='id.record', deleted=True))

        self.assertFalse(isfile(RECORD_FILENAME))
        self.uploader.delete(upload)
        self.assertTrue(isfile(RECORD_FILENAME))

        self.assertEqualsWS("""<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>VANDAAG_EN_NU</responseDate>
    <request verb="GetRecord" metadataPrefix="oai_dc" identifier="id.record">http://repository</request>
    <GetRecord>
        <record>
            <header status="deleted">
                <identifier>id.record</identifier>
                <datestamp>2005-08-29T07:08:09Z</datestamp>
            </header>
        </record>
    </GetRecord>
</OAI-PMH>""", open(RECORD_FILENAME).read())


    def testSend(self):
        recordFile = self.tempdir + '/group/repo/id.record'
        self.uploader._filenameFor = lambda *args: recordFile

        upload = createUpload()
        self.uploader.send(upload)

        self.assertTrue(isfile(recordFile))
        self.assertEqualsLxml(oaiResponse().record, parse(open(recordFile)))

    def testSendWithAbout(self):
        ABOUT = '<about xmlns="%(oai)s">abouttext</about>' % namespaces
        recordFile = self.tempdir + '/group/repo/id.record'
        self.uploader._filenameFor = lambda *args: recordFile

        upload = createUpload(about=ABOUT)
        self.uploader.send(upload)

        self.assertTrue(isfile(recordFile))
        self.assertEquals(ABOUT, lxmltostring(xpathFirst(parse(open(recordFile)), '//oai:about')))

    def testSendWithMultipleAbout(self):
        ABOUT = '<about xmlns="%(oai)s">about_1</about><about xmlns="%(oai)s">about_2</about>' % namespaces

        recordFile = self.tempdir + '/group/repo/id.record'
        self.uploader._filenameFor = lambda *args: recordFile

        upload = createUpload(about=ABOUT)
        self.uploader.send(upload)

        self.assertTrue(isfile(recordFile))
        self.assertEquals(ABOUT, ''.join(lxmltostring(x) for x in xpath(parse(open(recordFile)), '//oai:about')))


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

        self.assertTrue(isfile(recordFile))
        xmlGetRecord = parse(open(recordFile))
        self.assertEquals('oai:ident:321', xpathFirst(xmlGetRecord, '/oai:OAI-PMH/oai:GetRecord/oai:record/oai:header/oai:identifier/text()'))
        self.assertEquals('http://www.example.com', xpathFirst(xmlGetRecord, '/oai:OAI-PMH/oai:request/text()'))
        self.assertEquals('weird&strange', xpathFirst(xmlGetRecord, '/oai:OAI-PMH/oai:request/@metadataPrefix'))

    def testSendTwice(self):
        self.testSend()
        self.testSend()

def createUpload(about=None):
    repository = CallTrace('repository')
    repository.id = 'repoId'

    upload = Upload(repository=repository, oaiResponse=oaiResponse(about=about))
    upload.id = 'id'
    return upload

RECORD_WITH_ABOUT = """<record xmlns="http://www.openarchives.org/OAI/2.0/"><header><identifier>oai:id:0</identifier></header><metadata>text</metadata>%s</record>"""
