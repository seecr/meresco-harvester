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
# Copyright (C) 2011, 2015 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2013-2015, 2017 Seecr (Seek You Too B.V.) http://seecr.nl
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

from xml.sax.saxutils import escape as xmlEscape
from eventlogger import NilEventLogger
from urlparse import urljoin
from urllib import urlencode
from saharaobject import SaharaObject
from meresco.core import Observable
from lxml.etree import XML
from meresco.harvester.namespaces import namespaces, xpathFirst, xpath
from meresco.components import lxmltostring
from oairequest import OaiResponse


nillogger = NilEventLogger()
execcode = DEFAULT_DC_CODE = DEFAULT_CODE = """
#Map template
#
#Input
# upload.record = OAI Record lxmlNode
# upload.repository = Repository object
#
#Available Methods:
# isUrl(aString) determines if aString is a url.
# lxmltostring(lxmlNode) -> returns the string representation of lxmlNode
# xpath(lxmlNode, path) -> returns a list with the xpath result.
# xpathFirst(lxmlNode, path) -> returns the first result of the xpath or None
# logger.logLine(event, comments, [id=...]) Logs a line.
# doAssert(expression, comments) perform an assertion. The comments are optional
# urljoin(baseurl, path) Joins the base url with the path.
#     urljoin('http://example.org/a/b','/c/d') --> 'http://example.org/c/d'
#     urljoin('http://example.org/a/b','c/d') --> 'http://example.org/a/c/d'
#     urljoin('http://example.org/a/b','http://c.org/d') --> 'http://c.org/d'
#     urljoin('http://example.org/a/b/','c/d') --> 'http://example.org/a/b/c/d'
# urlencode( <dict> of <tuplelist> ) Encode a sequence of two-element tuples or dictionary
#     into a URL query string.
#     urlencode({'a':'b', 'c':'d'}) --> 'a=b&c=d'
#     urlencode([('a','b'), ('c','d')]) --> 'a=b&c=d'
# skipRecord( comments ) Skip a record for a certain reason.
#
upload.parts['record'] = lxmltostring(input.record)
"""

def read(filename):
    file = open(filename)
    try:
        return file.read()
    finally:
        file.close()

def noimport(name, globals, locals, fromlist):
    raise DataMapException('Import not allowed')

class DataMapException(Exception):
    pass

class DataMapAssertionException(Exception):
    pass

class DataMapSkip(Exception):
    pass

class TestRepository(object):
    id = 'repository.id'
    repositoryGroupId = 'repository.institute'
    baseurl = 'http://repository.example.org/oai'
    set = 'some.set'
    collection = 'testcollection'
    metadataPrefix = 'md'

def isUrl(aString):
    return aString.startswith('http:') or aString.startswith('https:') or aString.startswith('ftp:')

def doAssert(aBoolean, message="Assertion failed"):
    if not aBoolean:
        raise DataMapAssertionException(message)

def doNotAssert(aBoolean, message="This should not happen"):
    pass


class UploadDict(dict):
    def __setitem__(self, key, value):
        return dict.__setitem__(self, key, str(value))


class Upload(object):
    def __init__(self, repository, oaiResponse=None):
        self.id = ''
        self.oaiResponse = oaiResponse
        self.recordIdentifier = None
        self.record = None
        if oaiResponse is not None:
            self.record = oaiResponse.record
            self.isDeleted = xpathFirst(self.record, 'oai:header/@status') == 'deleted'
            self.recordIdentifier = xpathFirst(self.record, 'oai:header/oai:identifier/text()')
        if repository is not None and self.recordIdentifier is not None:
            self.id = repository.id + ':' + self.recordIdentifier
        self.fulltexturl = None
        self.parts = UploadDict()
        self.repository = repository
        self.skip = False

    def ensureStrings(self):
        if self.id:
            self.id = str(self.id)


class Mapping(SaharaObject, Observable):
    def __init__(self, mappingId):
        SaharaObject.__init__(self,['name', 'description', 'code'])
        Observable.__init__(self)
        self.id = mappingId

    def mappingInfo(self):
        return "Mappingname '%s'" % self.name

    def setCode(self, aString):
        self.code = aString

    def createUpload(self, repository, oaiResponse, doAsserts=False):
        upload = Upload(repository=repository, oaiResponse=oaiResponse)
        if upload.isDeleted:
            return upload

        builtinscopy = __builtins__.copy()
        builtinscopy['__import__'] = noimport

        assertionMethod = doAsserts and doAssert or doNotAssert

        try:
            exec(self.code, {
                'input': upload, # backwards compatible
                'upload': upload,
                'isUrl': isUrl,
                'urljoin': urljoin,
                'urlencode': urlencode,
                'doAssert': assertionMethod,
                'logger': self.do,
                'skipRecord': self.skipSimple,
                'xmlEscape': xmlEscape,
                'xpath': xpath,
                'xpathFirst': xpathFirst,
                'lxmltostring': lxmltostring,
                '__builtins__': builtinscopy
            })
            upload.ensureStrings()
        except DataMapAssertionException, ex:
            self.do.logError(comments='Assertion: ' + str(ex), id=upload.id)
            raise ex
        except DataMapSkip, e:
            self.do.logLine('SKIP', id=upload.id, comments=str(e))
            upload.skip = True
        return upload

    def skipSimple(self, comment):
        raise DataMapSkip(comment)

    def execcode(self):
        return self.code

    def isValid(self):
        try:
            self.validate()
            return True
        except:
            return False

    def validate(self):
        response = XML("""<OAI-PMH xmlns="%(oai)s"><responseDate>2000-01-02T03:04:05Z</responseDate><ListRecords><record><header><identifier>oai:id:12345</identifier><datestamp>1999-09-09T20:21:22Z</datestamp></header><metadata><dc><identifier>test:identifier</identifier></dc></metadata><about/></record></ListRecords></OAI-PMH>""" % namespaces)
        self.createUpload(TestRepository(), OaiResponse(response))
