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
# Copyright (C) 2005 Seek You Too B.V. http://www.cq2.nl
#
# $Id: sseuploader.py 4825 2007-04-16 13:36:24Z TJ $

WAITING_BEFORE_SEND = 0

import httplib
import cgi, base64
from cStringIO import StringIO
from urllib2 import urlopen
import os, tempfile, sys, traceback, re
from eventlogger import NilEventLogger
from xml.sax.saxutils import escape as xmlEscape
from time import sleep
from virtualuploader import VirtualUploader, UploaderException

def formatException():
	xtype,xval,xtb = sys.exc_info()
	return '|'.join(map(str.strip, traceback.format_exception(xtype,xval,xtb)))



UPLOAD_HEADER="""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:apachesoap="http://xml.apache.org/xml-soap" xmlns:impl="urn:upload" xmlns:intf="urn:upload" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:tns1="http://ws.upload.ds.fast.no" xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/" xmlns:wsdlsoap="http://schemas.xmlsoap.org/wsdl/soap/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" >
<SOAP-ENV:Body>
<mns:sendDocument xmlns:mns="urn:upload" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
"""
UPLOAD_FOOTER="""</mns:sendDocument>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
"""
UPLOAD_USERPASS="""<in0 xsi:type="xsd:string">%s</in0>
<in1 xsi:type="xsd:string">%s</in1>
"""
UPLOAD_COLLECTION="""<in2 xsi:type="xsd:string">%s</in2>
"""
UPLOAD_DOC_START="""<in3 xsi:type="tns1:UploadDocument">
	<elements xsi:type="soapenc:Array" soapenc:arrayType="tns1:UploadElement[%s]">
"""
UPLOAD_DOC_END="""	</elements>
	<id xsi:type="xsd:string">%s</id>
</in3>
"""
UPLOAD_BASE64_START_ITEM="""		<Item>
			<data xsi:type="xsd:base64Binary">
"""
UPLOAD_BASE64_END_ITEM="""			</data>
			<name xsi:type="xsd:string">data</name>
			<typeboolean xsi:type="xsd:boolean">0</typeboolean>
			<typebyte xsi:type="xsd:boolean">1</typebyte>
			<typedate xsi:type="xsd:boolean">0</typedate>
			<typeint xsi:type="xsd:boolean">0</typeint>
			<typestring xsi:type="xsd:boolean">0</typestring>
		</Item>
"""
UPLOAD_ITEM="""		<Item>
			<data xsi:type="xsd:base64Binary"></data>
			<name xsi:type="xsd:string">%s</name>
			<typeboolean xsi:type="xsd:boolean">0</typeboolean>
			<typebyte xsi:type="xsd:boolean">0</typebyte>
			<typedate xsi:type="xsd:boolean">0</typedate>
			<typeint xsi:type="xsd:boolean">0</typeint>
			<typestring xsi:type="xsd:boolean">1</typestring>
			<value xsi:type="xsd:string">%s</value>
		</Item>
"""
DELETE="""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/1999/XMLSchema">
<SOAP-ENV:Body>
<deleteDocument SOAP-ENC:root="1">
<in0 xsi:type="xsd:string">%s</in0>
<in1 xsi:type="xsd:string">%s</in1>
<in2 xsi:type="xsd:string">%s</in2>
<in3 xsi:type="xsd:string">%s</in3>
</deleteDocument>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
"""
GET_LAST_ERROR="""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<SOAP-ENV:Envelope 
xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:apachesoap="http://xml.apache.org/xml-soap" xmlns:impl="urn:upload" 
xmlns:intf="urn:upload" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" 
xmlns:tns1="http://ws.upload.ds.fast.no" 
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/" 
xmlns:wsdlsoap="http://schemas.xmlsoap.org/wsdl/soap/" 
xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" >
<SOAP-ENV:Body>
<mns:getLastError xmlns:mns="urn:upload" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
</mns:getLastError>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
"""
GET_BATCH_STATE="""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<SOAP-ENV:Envelope 
xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:apachesoap="http://xml.apache.org/xml-soap" xmlns:impl="urn:upload" 
xmlns:intf="urn:upload" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" 
xmlns:tns1="http://ws.upload.ds.fast.no" 
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/" 
xmlns:wsdlsoap="http://schemas.xmlsoap.org/wsdl/soap/" 
xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" >
<SOAP-ENV:Body>
<mns:getBatchState xmlns:mns="urn:upload" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<in0 xsi:type="xsd:string">%s</in0>
</mns:getBatchState>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
"""

class NotAvailableException(UploaderException):
	pass
 
class BackoffException(UploaderException):
	pass
 
FAST_EXCEPTIONS = { 'NA':NotAvailableException, 'BACKOFF':BackoffException }
	
class LoggingUploader(VirtualUploader):
	def __init__(self, eventlogger):
		VirtualUploader.__init__(self, eventlogger)
		
	def send(self, anUpload):
		self.logLine('LoggingUploader','START send',id=anUpload.id)
		for k,v in anUpload.fields.items():
			self.logLine('upload.fields','%s=%s'%(k,v), id=anUpload.id)
		self.logLine('LoggingUploader','END send',id=anUpload.id)
	
	def delete(self, anUpload):
		self.logLine('LoggingUploader','DELETE',id=anUpload.id)
		
	def info(self):
		return 'Uploader connected to a logfile.'


class SSEUploader(VirtualUploader):
	def __init__(self, ssetarget, eventlogger, collection=None):
		VirtualUploader.__init__(self, eventlogger)
		self._mockRequestor=None
		self.debugging(False, False)
		self.collection=collection
		self._ssetarget = ssetarget
		if not collection:
			raise RuntimeError('collection expected')
		if not ssetarget:
			raise RuntimeError('ssetarget expected')
	
	def info(self):
		return 'Uploader connected to: %s:%s (%s/%s), collection: %s'%(self._ssetarget.baseurl, self._ssetarget.port, self._ssetarget.username, self._ssetarget.password, self.collection)
	
	def debugging(self, output, input):
		self.debugOut = output
		self.debugIn = input

	def _isSendableField(self, fieldName):
		return not fieldName.lower().startswith("original:")

	def _createMessage(self, anUpload):
		items = anUpload.fields
		
		start = StringIO()
		start.writelines(UPLOAD_HEADER)
		start.writelines(UPLOAD_USERPASS % (self._ssetarget.username, self._ssetarget.password))
		start.writelines(UPLOAD_COLLECTION % self.collection)

		totalitems = len(items)
		start.writelines(UPLOAD_DOC_START % len(filter(lambda x: self._isSendableField(x), items.keys())))
		for k,v in items.items():
			if self._isSendableField(k):
				start.writelines(UPLOAD_ITEM % (k,cgi.escape(v)))
		end = StringIO()
		end.writelines(UPLOAD_DOC_END % anUpload.id)
		end.writelines(UPLOAD_FOOTER)
		totalsize = start.tell() + end.tell()
		start.seek(0)
		end.seek(0)
		return ((start, end), totalsize)

	def _createRequestor(self):
		return self._mockRequestor or httplib.HTTP(self._ssetarget.baseurl, int(self._ssetarget.port))
		
	def send(self, anUpload):
		try:
			self.logLine('UPLOAD.SEND','START',id=anUpload.id)
			buffers, blen = self._createMessage(anUpload)
			if WAITING_BEFORE_SEND:
				self.logLine('UPLOAD.SEND.HACK', 'Waiting %i seconds' % WAITING_BEFORE_SEND, id=anUpload.id)
				self.sleep(WAITING_BEFORE_SEND)
				self.logLine('UPLOAD.SEND.HACK', 'Done waiting', id=anUpload.id)
			result = self.sendData(buffers, blen, anUpload.id)
			self.logLine('UPLOAD.SEND.BATCHNR',result, id=anUpload.id)
			self.logLine('UPLOAD.SEND','END',id=anUpload.id)
			return result
		except Exception, e:
			error = formatException()
			self.logLine('UPLOAD.SEND.ERROR', error,id=anUpload.id)
			raise UploaderException(e)
			
	def delete(self, anUpload):
		uploadId = anUpload.id
		try:
			self.logLine('UPLOAD.DELETE','START',id=uploadId)
			delbuf = StringIO()
			delbuf.writelines(DELETE%tuple(map(xmlEscape, (self._ssetarget.username, self._ssetarget.password, self.collection, uploadId))))
			blen = delbuf.tell()
			delbuf.seek(0)
			buffers = [delbuf]
			result = self.sendData(buffers, blen, uploadId)
			self.logLine('UPLOAD.DELETE.BATCHNR',result, id=uploadId)
			self.logLine('UPLOAD.DELETE','END',id=uploadId)
			return result
		except Exception, e:
			error = formatException()
			self.logLine('UPLOAD.DELETE.ERROR', error, id=uploadId)
			raise UploaderException(e)
			
	def getLastError(self):
		try:
			delbuf = StringIO()
			delbuf.writelines(GET_LAST_ERROR)
			blen = delbuf.tell()
			delbuf.seek(0)
			buffers = [delbuf]
			result = self.sendData(buffers, blen, None)
			return result
		except Exception, e:
			error = formatException()
			self.logLine('UPLOAD.LASTERROR.ERROR',error)
			raise UploaderException(e)
	
	def getBatchState(self, batch):
		try:
			delbuf = StringIO()
			delbuf.writelines(GET_BATCH_STATE % batch)
			blen = delbuf.tell()
			delbuf.seek(0)
			buffers = [delbuf]
			result = self.sendData(buffers, blen, None)
			return result
		except Exception, e:
			error = formatException()
			self.logLine('UPLOAD.BATCHSTATE.ERROR', error)
			raise UploaderException(e)
		
	def sleep(self, seconds):
		sleep(seconds)

	def sendData(self, buffers, blen, uploadId):
		return self._sendDataWithNotAvailable(buffers, blen, uploadId)
	
	def rewind(self, buffers):
		for buf in filter(None, buffers):
			buf.seek(0)
	
	def _sendDataWithNotAvailable(self, buffers, blen, uploadId):
		exception = None
		for waitseconds in [0, 10, 30, 60]:
			try:
				waitseconds and self.sleep(waitseconds)
				return self._sendDataWithBackoff(buffers, blen, uploadId)
			except NotAvailableException, ne:
				msg = waitseconds and ' after waiting for %i seconds.' % waitseconds or ' first time.'
				self.logLine('UPLOAD.WARNING', 'NotAvailable'+ msg, id=uploadId)
				self.rewind(buffers)
				exception = ne
		raise exception
			
	def _sendDataWithBackoff(self, buffers,blen, uploadId):
		exception = None
		for i in range(10):
			try:
				i and self.sleep(30)
				return self._sendData(buffers, blen)
			except BackoffException, be:
				msg = i and ' after waiting for %i seconds.' % (30 * i) or ' first time.'
				self.logLine('UPLOAD.WARNING', 'BACKOFF'+ msg, id=uploadId)
				self.rewind(buffers)
				exception = be
		raise exception
		
	def _sendData(self, buffers, blen):
		requestor = self._createRequestor()
		requestor.putrequest("POST", self._ssetarget.path)
		requestor.putheader("Host", self._ssetarget.baseurl)
		requestor.putheader("Content-Type", "text/xml; charset=\"utf-8\"")
		requestor.putheader("Content-Length", str(blen))
		requestor.putheader("SOAPAction", "urn:upload")
		requestor.endheaders()
		for buffer in filter(None, buffers):
			for iets in buffer:
				if self.debugOut:
					print iets,
				requestor.send(iets)
		(status_code, response, reply_headers) = requestor.getreply()
		reply_body = requestor.getfile().read()
		if self.debugIn:
			print reply_body
		succes, answer = self._openEnvelope(reply_body)
		
		exceptionClass = FAST_EXCEPTIONS.get(answer, UploaderException)
		if not succes:
			raise exceptionClass(reply_body)
		return answer
		

	def _openEnvelope(self, reply_body):
		answer = envelope_re.sub('',reply_body).strip()
		succes = reply_body.startswith('<?xml') and  \
			('true' == answer or '@' in answer)
		return succes, answer

envelope_re = re.compile(r'<[^\<]+>')
