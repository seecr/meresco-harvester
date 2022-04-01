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
# Copyright (C) 2011, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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
from .virtualuploader import VirtualUploader, UploaderException, InvalidDataException, InvalidComponentException
from http.client import HTTPConnection, SERVICE_UNAVAILABLE, OK as HTTP_OK
from lxml.etree import parse
from io import BytesIO
from meresco.harvester.namespaces import xpath

recordUpdate = """<?xml version="1.0" encoding="UTF-8"?>
<ucp:updateRequest xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:ucp="info:lc/xmlns/update-v1">
    <srw:version>1.0</srw:version>
    <ucp:action>info:srw/action/1/%(action)s</ucp:action>
    <ucp:recordIdentifier>%(recordIdentifier)s</ucp:recordIdentifier>
    <srw:record>
        <srw:recordPacking>%(recordPacking)s</srw:recordPacking>
        <srw:recordSchema>%(recordSchema)s</srw:recordSchema>
        <srw:recordData>%(recordData)s</srw:recordData>
    </srw:record>
</ucp:updateRequest>"""

class SruUpdateUploader(VirtualUploader):
    def __init__(self, sruUpdateTarget, eventlogger, collection="ignored"):
        VirtualUploader.__init__(self, eventlogger)
        self._target = sruUpdateTarget

    def send(self, anUpload):
        anId = anUpload.id
        self._logLine('UPLOAD.SEND', 'START', id = anId)

        partsItems = list(anUpload.parts.items())
        recordData = '<document xmlns="http://meresco.org/namespace/harvester/document">%s</document>' % ''.join(
                ['<part name="%s">%s</part>' % (xmlEscape(partName), xmlEscape(partValue)) for partName, partValue in partsItems])

        action = "replace"
        recordIdentifier= xmlEscape(anId)
        recordPacking = 'xml'

        partName, _ = partsItems[-1]
        recordSchema = xmlEscape(partName)
        self._sendData(anId, recordUpdate % locals())
        self._logLine('UPLOAD.SEND', 'END', id = anId)

    def delete(self, anUpload):
        self._logDelete(anUpload.id)
        action = "delete"
        recordIdentifier = xmlEscape(anUpload.id)
        recordPacking = 'xml'
        recordSchema = 'ignored'
        recordData = '<ignored/>'
        self._sendData(anUpload.id, recordUpdate % locals())

    def info(self):
        return 'Uploader connected to: %s:%s%s'%(self._target.baseurl, self._target.port, self._target.path)

    def _sendData(self, uploadId, data):
        tries = 0
        while tries < 3:
            status, message = self._sendDataToRemote(data)
            if status != SERVICE_UNAVAILABLE:
                break
            self._logWarning("Status 503, SERVICE_UNAVAILABLE received while trying to upload")
            tries += 1
        if status != HTTP_OK:
            raise UploaderException(uploadId=uploadId, message="HTTP %s: %s" % (status, message))

        #version, operationStatus, diagnostics = self._parseMessage(parse(BytesIO(bytes(message, encoding="utf-8"))))
        version, operationStatus, diagnostics = self._parseMessage(parse(BytesIO(message)))
        message = message.decode()

        if operationStatus == 'fail':
            if diagnostics[0] == 'info:srw/diagnostic/12/1':
                raise InvalidComponentException(uploadId=uploadId, message=message)
            elif diagnostics[0] == 'info:srw/diagnostic/12/12':
                raise InvalidDataException(uploadId=uploadId, message=message)

    def _sendDataToRemote(self, data):
        data = bytes(data, encoding='utf-8')
        connection = HTTPConnection(self._target.baseurl, self._target.port)
        connection.putrequest("POST", self._target.path)
        connection.putheader("Host", self._target.baseurl)
        connection.putheader("Content-Type", "text/xml; charset=\"utf-8\"")
        connection.putheader("Content-Length", str(len(data)))
        connection.endheaders()
        connection.send(data)

        result = connection.getresponse()
        message = result.read()
        return result.status, message

    def _parseMessage(self, message):
        version = xpath(message, "/srw:updateResponse/srw:version/text()")[0]
        operationStatus = xpath(message, "/srw:updateResponse/ucp:operationStatus/text()")[0]
        diagresult = None
        diagnostics = xpath(message, "/srw:updateResponse/srw:diagnostics/diag:diagnostic")
        if len(diagnostics) > 0:
            diagnostic_uri = xpath(diagnostics[0], "diag:uri/text()")[0]
            diagnostic_details = ''.join(xpath(diagnostics[0], "diag:details/text()"))
            diagnostic_message = ''.join(xpath(diagnostics[0], "diag:message/text()"))
            diagresult = (diagnostic_uri, diagnostic_details, diagnostic_message)
        return version, operationStatus, diagresult
