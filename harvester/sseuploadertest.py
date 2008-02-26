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

import unittest
from sseuploader import SSEUploader, UploaderException
from eventlogger import StreamEventLogger, NilEventLogger
from cStringIO import StringIO
import mapping
from cq2utils.calltrace import CallTrace

class SSEUploaderTest(unittest.TestCase):
    def setUp(self):
        self.log = StringIO()
        self.loader = SSEUploader(MockSSETarget(), StreamEventLogger(self.log), collection='whocares')
        self.requestor = MockRequestor()
        self.loader._mockRequestor=self.requestor
        self.loader.sleep=self.mock_sleep
        self.mock_sleepargs = []
        
    def createUpload(self, aDictionary):
        upload = mapping.Upload()
        upload.fields = aDictionary
        upload.id = 'SOME_ID'
        return upload
        
    def testCreateMessage(self):
        (start, end),totalsize = self.loader._createMessage(self.createUpload({'title':"NICE TITLE", 'original:someMetadataFormat':"should be ignored"}))
        self.assertEqual(BIG_XML,start.getvalue()+end.getvalue())

    def testCreateLongerMessage(self):
        (start,end),totalsize = self.loader._createMessage(self.createUpload({'title':"The Guide",'data':"DON'T PANIC"}))
        total = start.getvalue()+end.getvalue()
        self.assert_('>SOME_ID</id>' in total)
        self.assert_('The Guide' in total)
        self.assert_("DON'T PANIC" in total)
        self.assert_("tns1:UploadElement[2]" in total)
        
    def testUpload(self):
        self.loader.send(self.createUpload({'title':"NICE TITLE"}))
        self.assertEqual('urn:upload', self.requestor.headers['SOAPAction'])
        self.assertEqual(BIG_XML, self.requestor.message)
        
    def testUploadFunnyCharacters(self):
        upload = mapping.Upload()
        upload.fields['title'] = 'g\xc3\xa9n\xc3\xa9ral pr\xc3\xa8s'
        upload.fields['data'] = '<data>&other stuff!!'
        
        self.loader.send(upload)
        message = self.requestor.message
        self.assert_('&lt;data&gt;&amp;other stuff!!' in message)
        self.assert_('g\xc3\xa9n\xc3\xa9ral pr\xc3\xa8s' in message)

    def testNoSSETarget(self):
        try:
            loader = SSEUploader(None, NilEventLogger(),collection='whatever')
            self.fail()
        except RuntimeError, re:
            self.assertEquals('ssetarget expected', str(re))
    
    def testNoCollection(self):
        try:
            loader = SSEUploader(MockSSETarget(), NilEventLogger(),collection=None)
            self.fail()
        except RuntimeError, re:
            self.assertEquals('collection expected', str(re))
        
    def testInfo(self):
        self.assertEquals('Uploader connected to: base-url.example.org:3128 (username/Password), collection: whocares' , self.loader.info())
        
    def doTestParseResponse(self, responsecontent):
        response = RESPONSE%responsecontent
        self.requestor.response = response
        result = self.loader.send(self.createUpload({'title':"NICE TITLE"}))
        self.assertEquals(responsecontent, result)
        batchnrs = filter(lambda (event, id, comment):'BATCHNR' in event, self.getLogging())
        self.assertEquals(['UPLOAD.SEND.BATCHNR','[SOME_ID]', responsecontent], batchnrs[0])
        
    def testParseResponse(self):
        self.doTestParseResponse('192.87.5.193--27856@base-url_27-16-1135091171807')

    def testParseResponseOtherUrl(self):
        self.doTestParseResponse('192.87.5.193--27856@other-url_27-16-1135091171807')

    def testOldResponse(self):
        self.doTestParseResponse('true')
            
    def testDeleteResponse(self):
        responsecontent='192.87.5.193--27856@base-url_27-16-1135091171807'
        response = DELETE_RESPONSE%responsecontent
        self.requestor.response = response
        upload = CallTrace('Upload')
        upload.id = 'any_id'
        result =self.loader.delete(upload)
        self.assertEquals(responsecontent, result)
        batchnrs = filter(lambda (event, id, comment):'BATCHNR' in event, self.getLogging())
        self.assertEquals(['UPLOAD.DELETE.BATCHNR','[any_id]', responsecontent], batchnrs[0])
        
    def testDeleteRequest(self):
        upload = CallTrace('Upload')
        upload.id = 'this&<id>'
        self.loader.delete(upload)
        expectedxml= DELETE_REQUEST%'this&amp;&lt;id&gt;'
        self.assertEquals(expectedxml,self.requestor.message)
        
    def doTestFailureResponse(self, responseContent):
        try:
            self.doTestParseResponse(responseContent)
            self.fail()
        except UploaderException, e:
            self.assert_(responseContent in str(e))
    
    def testOldFailureResponse(self):
        self.doTestFailureResponse('false')
    
    def testNAResponse(self):
        self.requestor = MockNARequestor()
        self.loader._mockRequestor=self.requestor
        result = self.loader.send(self.createUpload({'title':"NICE TITLE"}))
        self.assertEquals('succes@trial', result)
        self.assertEquals([10, 30, 60], self.mock_sleepargs)
        
    def testNAResponseAtMax4(self):
        self.requestor = MockNARequestor()
        self.requestor.trials = 10
        self.loader._mockRequestor=self.requestor
        try:
            self.loader.send(self.createUpload({'title':"NICE TITLE"}))
            self.fail()
        except UploaderException, ue:
            self.assert_('>NA<' in str(ue))
        self.assertEquals([10, 30, 60], self.mock_sleepargs)

    def testBACKOFFResponse(self):
        self.requestor = MockNARequestor('BACKOFF')
        self.requestor.trials = 3
        self.loader._mockRequestor=self.requestor
        result = self.loader.send(self.createUpload({'title':"NICE TITLE"}))
        self.assertEquals('succes@trial', result)
        # at first try don't sleep
        self.assertEquals([30, 30], self.mock_sleepargs)
        self.assertEquals(3, len(self.requestor.messages))
        self.assertEquals(self.requestor.messages[0], self.requestor.messages[1])
    
    def testBACKOFFResponseAtMax10(self):
        self.requestor = MockNARequestor('BACKOFF')
        self.requestor.trials = 100
        self.loader._mockRequestor=self.requestor
        try:
            self.loader.send(self.createUpload({'title':"NICE TITLE"}))
            self.fail()
        except UploaderException, ue:
            self.assert_('>BACKOFF<' in str(ue))
        # at first try don't sleep
        self.assertEquals([30] * 9, self.mock_sleepargs)

    def testJavaFailureResponse(self):
        self.doTestFailureResponse('java.lang.NullPointerException ...')
    
    def testInvalidXMLResponse(self):
        try:
            self.requestor.response = '<html>No such file. send mail to web@base-url.example.org, yours truely</html>'
            self.loader.send(self.createUpload({'data':'true'}))
            self.fail()
        except UploaderException, e:
            self.assert_('No such file.' in str(e))
        
    def mock_sleep(self, seconds):
        self.mock_sleepargs.append(seconds)
        
    def getLogging(self):
        self.log.seek(0)
        lines = map(str.strip, self.log.readlines())
        return map(lambda l:l.split('\t')[1:], lines)
    
class MockSSETarget:
    name = 'mockssetarget'
    username = 'username'
    password = 'Password'
    baseurl='base-url.example.org'
    port='3128'
    path='/axis/services/upload'

class MockRequestor:
    def __init__(self):
        self.headers={}
        self.message = ''
        self.response =RESPONSE%'true'
    def putrequest(self, type_, path):
        pass
    def putheader(self, key, value):
        self.headers[key]=value
    def endheaders(self):
        pass
    def send(self, message):
        self.message+=message
    def getreply(self):
        return (200, 'true', None)    
    def getfile(self):
        return self
    def read(self):
        return self.response
    
class MockNARequestor(MockRequestor):
    def __init__(self, result='NA'):
        MockRequestor.__init__(self)
        self._trialsDone = 0
        self.trials = 4
        self._result = result
        self.messages = []
    def read(self):
        result = self._result
        self.messages.append(self.message)
        self.message = ''
        self._trialsDone += 1
        if self._trialsDone >= self.trials:
            result = 'succes@trial'
        return RESPONSE%result

RESPONSE="""<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
         <soapenv:Body>
             <ns1:sendDocumentResponse soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="urn:upload">
                 <sendDocumentReturn xsi:type="xsd:string">%s</sendDocumentReturn>
            </ns1:sendDocumentResponse>
        </soapenv:Body>
    </soapenv:Envelope>
"""
DELETE_RESPONSE="""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/1999/XMLSchema" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance">
    <soapenv:Body>
        <deleteDocumentResponse soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
            <deleteDocumentReturn xsi:type="ns1:string" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ns1="http://www.w3.org/2001/XMLSchema">%s</deleteDocumentReturn>
        </deleteDocumentResponse>
    </soapenv:Body>
</soapenv:Envelope>
"""
DELETE_REQUEST="""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/1999/XMLSchema">
<SOAP-ENV:Body>
<deleteDocument SOAP-ENC:root="1">
<in0 xsi:type="xsd:string">username</in0>
<in1 xsi:type="xsd:string">Password</in1>
<in2 xsi:type="xsd:string">whocares</in2>
<in3 xsi:type="xsd:string">%s</in3>
</deleteDocument>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
"""
    
BIG_XML="""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:apachesoap="http://xml.apache.org/xml-soap" xmlns:impl="urn:upload" xmlns:intf="urn:upload" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:tns1="http://ws.upload.ds.fast.no" xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/" xmlns:wsdlsoap="http://schemas.xmlsoap.org/wsdl/soap/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" >
<SOAP-ENV:Body>
<mns:sendDocument xmlns:mns="urn:upload" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<in0 xsi:type="xsd:string">username</in0>
<in1 xsi:type="xsd:string">Password</in1>
<in2 xsi:type="xsd:string">whocares</in2>
<in3 xsi:type="tns1:UploadDocument">
    <elements xsi:type="soapenc:Array" soapenc:arrayType="tns1:UploadElement[1]">
        <Item>
            <data xsi:type="xsd:base64Binary"></data>
            <name xsi:type="xsd:string">title</name>
            <typeboolean xsi:type="xsd:boolean">0</typeboolean>
            <typebyte xsi:type="xsd:boolean">0</typebyte>
            <typedate xsi:type="xsd:boolean">0</typedate>
            <typeint xsi:type="xsd:boolean">0</typeint>
            <typestring xsi:type="xsd:boolean">1</typestring>
            <value xsi:type="xsd:string">NICE TITLE</value>
        </Item>
    </elements>
    <id xsi:type="xsd:string">SOME_ID</id>
</in3>
</mns:sendDocument>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
"""
    
XML="""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:apachesoap="http://xml.apache.org/xml-soap" xmlns:impl="urn:upload" xmlns:intf="urn:upload" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:tns1="http://ws.upload.ds.fast.no" xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/" xmlns:wsdlsoap="http://schemas.xmlsoap.org/wsdl/soap/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" >
<SOAP-ENV:Body>
<mns:sendDocument xmlns:mns="urn:upload" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<in0 xsi:type="xsd:string">username</in0>
<in1 xsi:type="xsd:string">Password</in1>
<in2 xsi:type="xsd:string">whocares</in2>
<in3 xsi:type="tns1:UploadDocument">
    <elements xsi:type="soapenc:Array" soapenc:arrayType="tns1:UploadElement[2]">
        <Item>
            <data xsi:type="xsd:base64Binary"></data>
            <name xsi:type="xsd:string">title</name>
            <typeboolean xsi:type="xsd:boolean">0</typeboolean>
            <typebyte xsi:type="xsd:boolean">0</typebyte>
            <typedate xsi:type="xsd:boolean">0</typedate>
            <typeint xsi:type="xsd:boolean">0</typeint>
            <typestring xsi:type="xsd:boolean">1</typestring>
            <value xsi:type="xsd:string">En nog vele jaren</value>
        </Item>
        <Item>
            <data xsi:type="xsd:base64Binary"></data>
            <name xsi:type="xsd:string">data</name>
            <typeboolean xsi:type="xsd:boolean">0</typeboolean>
            <typebyte xsi:type="xsd:boolean">0</typebyte>
            <typedate xsi:type="xsd:boolean">0</typedate>
            <typeint xsi:type="xsd:boolean">0</typeint>
            <typestring xsi:type="xsd:boolean">1</typestring>
            <value xsi:type="xsd:string">In gezondheid</value>
        </Item>
    </elements>
    <id xsi:type="xsd:string">http://www.verjaardag.nl</id>
</in3>
</mns:sendDocument>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
"""

if __name__ == '__main__':
    unittest.main()
    
