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

from xml.sax.saxutils import escape as xmlEscape
from eventlogger import NilEventLogger
from cq2utils import binderytools
from cq2utils import wrappers
from urlparse import urljoin
from urllib import urlencode
from saharaobject import SaharaObject

import vcard, classification

nillogger = NilEventLogger()
execcode = DEFAULT_DC_CODE = """
#Map template
#
#Fields: 
# input.metadata = Metadata object
# input.header = Header object
# input.repository = Repository object
# upload.fields = a map, to filled with data that can be uploaded to
#   the search engine.
#
#Available Methods:
# isUrl(aString) determines if aString is a url.
# join(collection) joins items in a collection seperated by '; '
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
upload.fields['url'] = join(input.metadata.dc.identifier)
upload.fields['generic1'] = input.repository.id
upload.fields['generic2'] = input.header.identifier
upload.fields['generic3'] = input.repository.repositoryGroupId
dcdate = input.metadata.dc.date
if dcdate:
    upload.fields['generic4'] = dcdate[0]

upload.fields['meta_dc.contributor'] = join(input.metadata.dc.contributor)
upload.fields['meta_dc.coverage'] = join(input.metadata.dc.coverage)
upload.fields['meta_dc.creator'] = join(input.metadata.dc.creator)
upload.fields['meta_dc.date'] = join(input.metadata.dc.date)
upload.fields['meta_dc.dateint'] = join(input.metadata.dc.dateint)
upload.fields['meta_dc.description'] = join(input.metadata.dc.description)
upload.fields['meta_dc.format'] = join(input.metadata.dc.format)
upload.fields['meta_dc.identifier'] = join(input.metadata.dc.identifier)
upload.fields['meta_dc.language'] = join(input.metadata.dc.language)
upload.fields['meta_dc.publisher'] = join(input.metadata.dc.publisher)
upload.fields['meta_dc.relation'] = join(input.metadata.dc.relation)
upload.fields['meta_dc.rights'] = join(input.metadata.dc.rights)
upload.fields['meta_dc.source'] = join(input.metadata.dc.source)
upload.fields['meta_dc.subject'] = join(input.metadata.dc.subject)
upload.fields['meta_dc.title'] = join(input.metadata.dc.title)
upload.fields['meta_dc.type'] = join(input.metadata.dc.type)

data = upload.fields.get('meta_dc.title', '')
data += upload.fields.get('meta_dc.description', '')
data += upload.fields.get('meta_dc.subject', '')
upload.fields['charset']=u'utf-8'
upload.fields['data'] = data
upload.fields['title'] = upload.fields.get('meta_dc.title','')
"""

def parse_xml(aString):
	return wrappers.wrapp(binderytools.bind_string(aString))

def read(filename):
	file = open(filename)
	try:
		return file.read()
	finally:
		file.close()

def assertObligatoryFields(uploadfields):
	keys = uploadfields.keys()
	return 'title' in keys and 'data' in keys and 'charset' in keys
	
def noimport(name, globals, locals, fromlist):
	raise DataMapException('Import not allowed')
	
class DataMapException(Exception):
	pass

class DataMapAssertionException(Exception):
	pass

class DataMapSkip(Exception):
	pass

class TestRepository:
	id = 'repository.id'
	repositoryGroupId = 'repository.institute'
	baseurl = 'http://repository.example.org/oai'
	set = 'some.set'
	collection = 'testcollection'
	metadataPrefix = 'md'
	
def isUrl(aString):
	return aString.startswith('http:') or aString.startswith('https:') or aString.startswith('ftp:')
	
def join(collection):
	result = []
	for item in collection:
		result.append(str(item))
	return '; '.join(result)

def doAssert(aBoolean, message="Assertion failed"):
	if not aBoolean:
		raise DataMapAssertionException(message)

def doNotAssert(aBoolean, message="This should not happen"):
	pass
	
class Input:
	def __init__(self, header=None, metadata=None, repository=None, log=None):
		self.header = header
		self.metadata = metadata
		self.repository = repository
		self.log = log
	
class UploadDict(dict):
	def __setitem__(self, key, value):
		return dict.__setitem__(self, key, str(value))
		

class Upload:
	def __init__(self):
		self.fulltexturl = None
		self._properties = {}
		self.fields = UploadDict()
		self.parts = UploadDict()
		self.id = ''
		
	def init(self, repository, header, metadata):
		self.id = repository.id + ':' + header.identifier
		self.header = header
		self.repository = repository
		self.metadata = metadata

	def _monkeyProofKey(self, aString):
		return filter(lambda x:not x.isspace(), aString).lower()

	def setProperty(self, key, value):
		self._properties[self._monkeyProofKey(key)] = value

	def getProperty(self, key):
		value = ''
		try:
			value = self._properties[self._monkeyProofKey(key)]
		except KeyError:
			pass
		return value

	def ensureStrings(self):
		if self.id:
			self.id = str(self.id)
		
class Mapping(SaharaObject):
	def __init__(self, mappingId):
		SaharaObject.__init__(self,['name', 'description', 'code'])
		self.id = mappingId

	def setCode(self, aString):
		self.code = aString

	def createEmptyUpload(self, repository, header, metadata):
		# TJ/JJ this should be refactored into Upload. 30-8-2006
		upload = Upload()
		upload.init(repository, header, metadata)
		return upload
		

	def createUpload(self, repository, header, metadata, logger=nillogger, doAsserts=False):
		logger = logger
		builtinscopy = __builtins__.copy()
		builtinscopy['__import__']=noimport
		upload = self.createEmptyUpload(repository, header, metadata)

		assertionMethod = doAsserts and doAssert or doNotAssert
		
		try:
			exec(self.code, {'input':Input(header,metadata,repository),
			'upload':upload,
			'isUrl':isUrl,
			'join':join,
			'urljoin':urljoin,
			'urlencode':urlencode,
			'doAssert':assertionMethod,
			'logger': logger,
			'skipRecord': self.skipSimple,
			'vcard':vcard,
			'classification':classification,
			'xmlEscape': xmlEscape,
			'__builtins__':builtinscopy})
			upload.ensureStrings()
		except DataMapAssertionException, ex:
			logger.error(comments='Assertion: ' + str(ex), id=upload.id)
			raise ex
		except DataMapSkip, e:
			logger.logLine('SKIP', id=upload.id, comments=str(e))
			return None
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
		header = parse_xml("""<header><identifier>oai:id:12345</identifier><datestamp>1999-09-09T20:21:22Z</datestamp></header>""")
		metadata = parse_xml("""<metadata><dc><identifier>test:identifier</identifier></dc></metadata>""")
		upload = self.createUpload(TestRepository(), header,metadata)
		if not assertObligatoryFields(upload.fields):
			raise DataMapException('The keys: title, data, charset are mandatory')
		
