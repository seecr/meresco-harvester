#!/usr/bin/env python
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
from mapping import Mapping, assertObligatoryFields, TestRepository, DataMapException, DataMapAssertionException, parse_xml
import os, tempfile, mapping
from cStringIO import StringIO
from eventlogger import StreamEventLogger
from cq2utils.wrappers import wrapp

class MappingTest(unittest.TestCase):
    def testCreateUploadFields(self):
        dcmap = Mapping('mappingId')
        dcmap.code = mapping.execcode
        header = parse_xml("""<header><identifier>oai:ident:321</identifier><datestamp>2005-08-29T07:08:09Z</datestamp></header>""").header
        metadata = parse_xml("""<metadata>
        <dc>
        <identifier>bla</identifier>
        <identifier>http://bla.example.org</identifier>
        <title>Title</title>
        <description>Description1</description>
        <description>Description2</description>
        <subject>sub1</subject>
        <subject>sub2</subject>
        <subject>sub3</subject>
        <creator>Jonkers, J</creator></dc></metadata>""").metadata
        about = parse_xml('<about/>').about

        uploadfields = dcmap.createUpload(TestRepository(), header, metadata, about).fields
        self.assertEquals('oai:ident:321', uploadfields['generic2'])
        self.assertEquals(str, type(uploadfields['generic2']))
        self.assertEquals('repository.id', uploadfields['generic1'])
        self.assertEquals('repository.institute', uploadfields['generic3'])
        self.assertEquals('Title', uploadfields['meta_dc.title'])
        self.assertEquals('Title', uploadfields['title'])
        self.assertEquals('Description1; Description2', uploadfields['meta_dc.description'])
        self.assertEquals('sub1; sub2; sub3', uploadfields['meta_dc.subject'])
        self.assertEquals('TitleDescription1; Description2sub1; sub2; sub3', uploadfields['data'])
        self.assertEquals('bla; http://bla.example.org', uploadfields['url'])
        self.assertEquals('bla; http://bla.example.org', uploadfields['meta_dc.identifier'])
        self.assertEquals('Jonkers, J', uploadfields['meta_dc.creator'])
        self.assertEquals('utf-8', uploadfields['charset'])

    def testAssertObligatoryFields(self):
        uploadfields = {'title':'bla', 'data':'tosti', 'charset':'utf-8'}
        self.assert_(not assertObligatoryFields({}))
        self.assert_(assertObligatoryFields(uploadfields))

    def testOtherFile(self):
        testcode="""
upload.fields['charset']=u'utf-8'
upload.fields['data'] = 'zo maar iets'
upload.fields['title'] = 'Dit is een test'"""

        dcmap = Mapping('mappingId')
        dcmap.code = testcode
        fields = dcmap.createUpload(TestRepository(),wrapp(''),None, None).fields
        self.assert_(fields)

    def testValidMapping(self):
        code = """
upload.fields['charset']=u'utf-8'
upload.fields['data'] = 'zo maar iets'
upload.fields['title'] = 'Dit is een test'
upload.fields['blah'] = input.header.identifier
upload.fields['repository'] = input.repository.id"""
        datamap = Mapping('mappingId')
        datamap.code = code
        self.assert_(datamap.isValid())
        datamap.validate()

    def testInValidMapping(self):
        datamap = Mapping('mappingId')
        datamap.code ="""upload.fields"""
        self.assert_(not datamap.isValid())
        try:
            datamap.validate()
            self.fail()
        except DataMapException, e:
            self.assertEquals('The keys: title, data, charset are mandatory', str(e))

    def testInValidWithImportMapping(self):
        datamap = Mapping('mappingId')
        datamap.code = """
upload.fields['charset']=u'utf-8'
upload.fields['data'] = 'zo maar iets'
upload.fields['title'] = 'Dit is een test'
import os
#uploadfield['tikfout']='bla'
"""
        self.assert_(not datamap.isValid())
        try:
            datamap.validate()
            self.fail()
        except DataMapException, e:
            self.assertEquals('Import not allowed', str(e))

    def testInValidCodeMapping(self):
        datamap = Mapping('mappingId')
        datamap.code = """
upload.fields['charset']=u'utf-8'
upload.fields['data'] = 'zo maar iets'
upload.fields['title'] = 'Dit is een test'
upload.fields['tikfout']='bla
"""
        self.assert_(not datamap.isValid())
        try:
            datamap.validate()
            self.fail()
        except:
            pass

    def testLogging(self):
        datamap = Mapping('mappingId')
        datamap.code = """
upload.fields['charset']=u'utf-8'
upload.fields['data'] = 'zo maar iets'
upload.fields['title'] = 'Dit is een test'
logger.error('Iets om te zeuren')
"""
        header = parse_xml("""<header><identifier>oai:ident:321</identifier><datestamp>2005-08-29T07:08:09Z</datestamp></header>""").header
        metadata = parse_xml("""<metadata></metadata>""").metadata
        about = parse_xml('<about/>').about
        stream = StringIO()
        logger = StreamEventLogger(stream)
        upload = datamap.createUpload(TestRepository(),header,metadata, about, logger)
        self.assertEquals('ERROR\t[]\tIets om te zeuren\n',stream.getvalue()[26:])

    def testNoLogging(self):
        datamap = Mapping('mappingId')
        datamap.code = """
upload.fields['charset']=u'utf-8'
upload.fields['data'] = 'zo maar iets'
upload.fields['title'] = 'Dit is een test'
logger.error('Iets om te zeuren')
"""
        header = parse_xml("""<header><identifier>oai:ident:321</identifier><datestamp>2005-08-29T07:08:09Z</datestamp></header>""").header
        metadata = parse_xml("""<metadata></metadata>""").metadata
        about = parse_xml('<about/>').about
        upload = datamap.createUpload(TestRepository(),header,metadata, about)
        self.assertEquals('Dit is een test',upload.fields['title'])

    def testJoin(self):
        metadata = parse_xml("""<metadata><dc>
        <subject>sub1</subject>
        <subject>sub2</subject>
        <creator>Groeneveld</creator>
        </dc></metadata>""").metadata
        self.assertEquals('Groeneveld', mapping.join(metadata.dc.creator))
        self.assertEquals('sub1; sub2', mapping.join(metadata.dc.subject))

    def testAssertion(self):
        datamap = Mapping('mappingId')
        datamap.code = """
doAssert(1==1)
doAssert(1==2, "1 not equal 2")
upload.fields['charset']=u'utf-8'
upload.fields['data'] = 'zo maar iets'
upload.fields['title'] = 'Dit is een test'"""

        stream = StringIO()
        logger = StreamEventLogger(stream)
        try:
            header = parse_xml("""<header><identifier>oai:ident:321</identifier></header>""").header
            datamap.createUpload(TestRepository(),header,None, None, logger, doAsserts=True)
            self.fail()
        except DataMapAssertionException, ex:
            self.assertEquals('ERROR\t[repository.id:oai:ident:321]\tAssertion: 1 not equal 2\n',stream.getvalue()[26:])
            self.assertEquals('1 not equal 2', str(ex))

        try:
            datamap.createUpload(TestRepository(),wrapp(''),None, None, doAsserts=True)
            self.fail()
        except DataMapAssertionException, ex:
            self.assertEquals('1 not equal 2', str(ex))

        stream = StringIO()
        logger = StreamEventLogger(stream)
        datamap.createUpload(TestRepository(),wrapp(''),None, None, logger, doAsserts=False)
        self.assertEquals('',stream.getvalue())

    def assertField(self, expected, fieldname, code):
        datamap = Mapping('mappingId')
        datamap.code = code
        header = parse_xml("""<header><identifier>oai:ident:321</identifier><datestamp>2005-08-29T07:08:09Z</datestamp></header>""").header
        metadata = parse_xml("""<metadata></metadata>""").metadata
        about = parse_xml('<about/>').about
        upload = datamap.createUpload(TestRepository(),header,metadata, about)
        self.assertEquals(expected,upload.fields[fieldname])

    def testUrlEncode(self):
        code = """upload.fields['url'] = 'http://some/one?'+urlencode({'id':'oai:id:3/2'})"""
        self.assertField('http://some/one?id=oai%3Aid%3A3%2F2','url', code)

    def testXmlEscape(self):
        code = """upload.fields['xml'] = '<tag>' + xmlEscape('&<>') + '</tag>'"""
        self.assertField('<tag>&amp;&lt;&gt;</tag>', 'xml', code)

    def testSkip(self):
        datamap = Mapping('mappingId')
        datamap.code = """
skipRecord("Don't like it here.")
"""
        header = parse_xml("""<header><identifier>oai:ident:321</identifier><datestamp>2005-08-29T07:08:09Z</datestamp></header>""").header
        metadata = parse_xml("""<metadata></metadata>""").metadata
        about = parse_xml('<about/>').about
        stream = StringIO()
        logger = StreamEventLogger(stream)
        upload = datamap.createUpload(TestRepository(),header,metadata, about, logger)
        self.assertEquals(None, upload)
        self.assertEquals("SKIP\t[repository.id:oai:ident:321]\tDon't like it here.\n",stream.getvalue()[26:])

    def testUploadGetSetProperty(self):
        upload = mapping.Upload()
        upload.setProperty('sortfields', ['generic4', 'generic5'])

        self.assertEquals(['generic4', 'generic5'], upload.getProperty('sortfields'))

    def testUploadPropertyKeyMonkeyProof(self):
        upload = mapping.Upload()

        upload.setProperty('CAPS', 1)
        self.assertEquals(1, upload.getProperty('caps'))

        upload.setProperty('S p A c E d ', 1)
        self.assertEquals(1, upload.getProperty('spaced'))

    def testUploadGetUnknownProperty(self):
        upload = mapping.Upload()

        self.assertEquals('', upload.getProperty('doesnotexist'))

    def testCreateUploadParts(self):
        upload = mapping.Upload()
        self.assertEquals({}, upload.parts)

        upload.parts['name'] = 'value'
        upload.parts['number'] = 1

        self.assertEquals('value', upload.parts['name'])
        self.assertEquals('1', upload.parts['number'])

if __name__ == '__main__':
    unittest.main()

