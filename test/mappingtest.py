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

import unittest
from meresco.harvester.mapping import Mapping, TestRepository, DataMapException, DataMapAssertionException, parse_xml
import os, tempfile
from meresco.harvester import mapping
from StringIO import StringIO
from meresco.harvester.eventlogger import StreamEventLogger
from slowfoot.wrappers import wrapp

class MappingTest(unittest.TestCase):
    def testInValidMapping(self):
        datamap = Mapping('mappingId')
        datamap.code ="""upload.parts['unfinishpython"""
        self.assert_(not datamap.isValid())
        try:
            datamap.validate()
            self.fail()
        except Exception, e:
            self.assertTrue('EOL while scanning single-quoted string' in str(e), str(e))

    def testInValidWithImportMapping(self):
        datamap = Mapping('mappingId')
        datamap.code = """
upload.parts['record']="<somexml/>"
import os
"""
        self.assert_(not datamap.isValid())
        try:
            datamap.validate()
            self.fail()
        except DataMapException, e:
            self.assertEquals('Import not allowed', str(e))

    def testLogging(self):
        datamap = Mapping('mappingId')
        datamap.code = """
upload.parts['record']="<somexml/>"
logger.logError('Iets om te zeuren')
"""
        record = parse_xml("""<record><header><identifier>oai:ident:321</identifier><datestamp>2005-08-29T07:08:09Z</datestamp></header><metadata></metadata><about/></record>""").record
        stream = StringIO()
        logger = StreamEventLogger(stream)
        datamap.addObserver(logger)
        upload = datamap.createUpload(TestRepository(), record)
        self.assertEquals('ERROR\t[]\tIets om te zeuren\n',stream.getvalue()[26:])

    def testNoLogging(self):
        datamap = Mapping('mappingId')
        datamap.code = """
upload.parts['record']="<somexml/>"
logger.logError('Iets om te zeuren')
"""
        record = parse_xml("""<record><header><identifier>oai:ident:321</identifier><datestamp>2005-08-29T07:08:09Z</datestamp></header><metadata></metadata><about/></record>""").record
        upload = datamap.createUpload(TestRepository(), record)
        self.assertEquals('<somexml/>',upload.parts['record'])

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
upload.parts['record']="<somexml/>"
"""

        stream = StringIO()
        logger = StreamEventLogger(stream)
        datamap.addObserver(logger)
        try:
            record = parse_xml("""<record><header><identifier>oai:ident:321</identifier><datestamp>2005-08-29T07:08:09Z</datestamp></header><metadata></metadata><about/></record>""").record
            datamap.createUpload(TestRepository(), record, doAsserts=True)
            self.fail()
        except DataMapAssertionException, ex:
            self.assertEquals('ERROR\t[repository.id:oai:ident:321]\tAssertion: 1 not equal 2\n',stream.getvalue()[26:])
            self.assertEquals('1 not equal 2', str(ex))

        try:
            datamap.createUpload(TestRepository(), record=wrapp(''), doAsserts=True)
            self.fail()
        except DataMapAssertionException, ex:
            self.assertEquals('1 not equal 2', str(ex))

        stream = StringIO()
        logger = StreamEventLogger(stream)
        datamap.createUpload(TestRepository(),wrapp(''), doAsserts=False)
        self.assertEquals('',stream.getvalue())

    def assertPart(self, expected, partname, code):
        datamap = Mapping('mappingId')
        datamap.code = code
        record = parse_xml("""<record><header><identifier>oai:ident:321</identifier><datestamp>2005-08-29T07:08:09Z</datestamp></header></record>""").record
        upload = datamap.createUpload(TestRepository(), record)
        self.assertEquals(expected,upload.parts[partname])

    def testUrlEncode(self):
        code = """upload.parts['url'] = 'http://some/one?'+urlencode({'id':'oai:id:3/2'})"""
        self.assertPart('http://some/one?id=oai%3Aid%3A3%2F2','url', code)

    def testXmlEscape(self):
        code = """upload.parts['xml'] = '<tag>' + xmlEscape('&<>') + '</tag>'"""
        self.assertPart('<tag>&amp;&lt;&gt;</tag>', 'xml', code)

    def testSkip(self):
        datamap = Mapping('mappingId')
        datamap.code = """
skipRecord("Don't like it here.")
"""
        record = parse_xml("""<record><header><identifier>oai:ident:321</identifier><datestamp>2005-08-29T07:08:09Z</datestamp></header><metadata></metadata><about/></record>""").record
        stream = StringIO()
        logger = StreamEventLogger(stream)
        datamap.addObserver(logger)
        upload = datamap.createUpload(TestRepository(), record)
        self.assertTrue(upload.skip)
        self.assertEquals("SKIP\t[repository.id:oai:ident:321]\tDon't like it here.\n", stream.getvalue()[26:])

    def testCreateUploadParts(self):
        upload = mapping.Upload()
        self.assertEquals({}, upload.parts)

        upload.parts['name'] = 'value'
        upload.parts['number'] = 1

        self.assertEquals('value', upload.parts['name'])
        self.assertEquals('1', upload.parts['number'])

