# -*- coding: utf-8 -*-
## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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

from seecr.test import SeecrTestCase, CallTrace
from amara.binderytools import bind_string
from lxml.etree import parse
from StringIO import StringIO

from meresco.harvester.sruupdateuploader import SruUpdateUploader, UploaderException, InvalidComponentException, InvalidDataException
from httplib import SERVICE_UNAVAILABLE, OK as HTTP_OK

class SruUpdateUploaderTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.target = CallTrace('SruUpdateTarget', verbose=True)
        self.uploader = SruUpdateUploader(self.target, CallTrace('eventlogger'))
        self.sentData = []
        def sendData(anId, data):
            self.sentData.append(data)
        self.uploader._sendData = sendData

        self.upload = CallTrace('Upload')
        self.upload.id = 'some:id'
        self.upload.parts={
            'meta': '<meta>....</meta>',
            'otherdata': '<stupidXML>abcdefgh'
        }
        
    def testOne(self):
        self.uploader.send(self.upload)
        self.assertEquals(1, len(self.sentData))

        updateRequest = bind_string(self.sentData[0]).updateRequest
        self.assertEquals('some:id', str(updateRequest.recordIdentifier))
        self.assertEquals('info:srw/action/1/replace', str(updateRequest.action))
        document = updateRequest.record.recordData.document
        self.assertEquals(2, len(document.part))

        self.uploader.delete(self.upload)
        updateRequest = bind_string(self.sentData[1]).updateRequest
        self.assertEquals('some:id', str(updateRequest.recordIdentifier))
        self.assertEquals('info:srw/action/1/delete', str(updateRequest.action))

    def testException(self):
        possibleSRUError="""<?xml version="1.0" encoding="UTF-8"?>
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>fail</ucp:operationStatus>
    <srw:diagnostics>
        <diag:diagnostic xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/">
            <diag:uri>info:srw/diagnostic/12/1</diag:uri>
            <diag:details>Traceback (most recent call last): File "../meresco/components/sru/srurecordupdate.py", line 47, in handleRequest File "../meresco/framework/transaction.py", line 63, in unknown File "../meresco/framework/observable.py", line 101, in __call__ File "../meresco/framework/observable.py", line 109, in _callonce File "../meresco/framework/observable.py", line 109, in _callonce File "../meresco/framework/observable.py", line 109, in _callonce File "../meresco/framework/observable.py", line 106, in _callonce KeyError: '__id__' </diag:details>
            <diag:message>Invalid component: record rejected</diag:message>
        </diag:diagnostic>
    </srw:diagnostics>
</srw:updateResponse>"""
        eventLogger = CallTrace('eventlogger')
        uploader = SruUpdateUploader(self.target, eventLogger)
        uploader._sendDataToRemote = lambda data: (HTTP_OK, possibleSRUError)
        try:
            uploader.send(self.upload)
            self.fail()
        except InvalidComponentException, e:
            self.assertEquals(self.upload.id, e.uploadId)

    def testInvalidDataException(self):
        possibleSRUValidationError="""<?xml version="1.0" encoding="UTF-8"?>
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>fail</ucp:operationStatus>
    <srw:diagnostics>
        <diag:diagnostic xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/">
            <diag:uri>info:srw/diagnostic/12/12</diag:uri>
            <diag:details>Xsd Validation error</diag:details>
            <diag:message>Invalid data structure: record rejected</diag:message>
        </diag:diagnostic>
    </srw:diagnostics>
</srw:updateResponse>"""
        eventLogger = CallTrace('eventlogger')
        uploader = SruUpdateUploader(self.target, eventLogger)
        uploader._sendDataToRemote = lambda data: (HTTP_OK, possibleSRUValidationError)
        try:
            uploader.send(self.upload)
            self.fail("Diagnostic code 12 should raise a validation exception")
        except InvalidDataException, e:
            self.assertEquals(self.upload.id, e.uploadId)

    def testRetryOnServiceUnavailable(self):
        eventLogger = CallTrace('eventlogger')
        uploader = SruUpdateUploader(self.target, eventLogger)

        answers = [(HTTP_OK, SUCCES_RESPONSE)]
        datas = []
        def sendDataToRemote(data):
            answer = answers.pop(0)
            datas.append(data)
            return answer

        uploader._sendDataToRemote = sendDataToRemote
        uploader._sendData(1, "HOW IS EVERYTHING")

        self.assertEquals(0, len(answers))
        self.assertEquals(1, len(datas))

        answers = [(SERVICE_UNAVAILABLE, ''), (HTTP_OK, SUCCES_RESPONSE)]
        datas = []
        uploader._sendData(1, "HOW IS EVERYTHING")
        
        self.assertEquals(0, len(answers))
        self.assertEquals(2, len(datas))
        self.assertEquals(1, len(eventLogger.calledMethods))
        self.assertEquals("Status 503, SERVICE_UNAVAILABLE received while trying to upload", eventLogger.calledMethods[0].args[0])

    def testRetryOnServiceUnavailableFailsAfter3Times(self):
        eventLogger = CallTrace('eventlogger')
        uploader = SruUpdateUploader(self.target, eventLogger)
        
        answers = [(SERVICE_UNAVAILABLE, ''), (SERVICE_UNAVAILABLE, ''), (SERVICE_UNAVAILABLE, ''), (HTTP_OK, SUCCES_RESPONSE)]
        datas = []
        def sendDataToRemote(data):
            answer = answers.pop(0)
            datas.append(data)
            return answer
            
        uploader._sendDataToRemote = sendDataToRemote
        exception = None
        try:
            uploader._sendData(1, "HOW IS EVERYTHING")
            self.fail()
        except Exception, e:
            exception = e

        self.assertFalse(exception == None)
        self.assertEquals('uploadId: "1", message: "HTTP 503: "', str(e))
        self.assertEquals(1, len(answers))
        self.assertEquals(3, len(datas))
        self.assertEquals(3, len(eventLogger.calledMethods))

    def testParseMessageWithDiagnostic(self):
        SRU_MESSAGE=parse(StringIO("""<?xml version="1.0" encoding="UTF-8"?>
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>fail</ucp:operationStatus>
    <srw:diagnostics>
        <diag:diagnostic xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/">
            <diag:uri>info:srw/diagnostic/12/12</diag:uri>
            <diag:details>Xsd Validation error</diag:details>
            <diag:message>Invalid component: record rejected</diag:message>
        </diag:diagnostic>
    </srw:diagnostics>
</srw:updateResponse>"""))

        eventLogger = CallTrace('eventlogger')
        uploader = SruUpdateUploader(self.target, eventLogger)
        version, operationStatus, diagnostics = uploader._parseMessage(SRU_MESSAGE)
        self.assertEquals("1.0", version)
        self.assertEquals("fail", operationStatus)
        self.assertEquals(("info:srw/diagnostic/12/12", "Xsd Validation error", "Invalid component: record rejected"), diagnostics)

    def testParseMessage(self):
        SRU_MESSAGE=parse(StringIO(SUCCES_RESPONSE))

        eventLogger = CallTrace('eventlogger')
        uploader = SruUpdateUploader(self.target, eventLogger)
        version, operationStatus, diagnostics = uploader._parseMessage(SRU_MESSAGE)
        self.assertEquals("1.0", version)
        self.assertEquals("success", operationStatus)
        self.assertEquals(None, diagnostics)
        
SUCCES_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<srw:updateResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:operationStatus>success</ucp:operationStatus>
</srw:updateResponse>"""
