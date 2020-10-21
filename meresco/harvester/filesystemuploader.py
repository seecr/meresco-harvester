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
# Copyright (C) 2011, 2015 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2013, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

#
from .virtualuploader import VirtualUploader, UploaderException
import os
from xml.sax.saxutils import escape as xmlEscape
from io import StringIO
from lxml.etree import parse, tostring, XML, XMLParser
from time import gmtime, strftime, time
from escaping import escapeFilename
from meresco.components import lxmltostring

OAI_ENVELOPE = """<?xml version="1.0"?>
<OAI-PMH
    xmlns="http://www.openarchives.org/OAI/2.0/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"
>
    <responseDate>%(responseDate)s</responseDate>
    <request
        verb="GetRecord"
        metadataPrefix="%(metadataPrefix)s"
        identifier="%(identifier)s"
    >%(baseurl)s</request>
    <GetRecord>%(recordData)s</GetRecord>
</OAI-PMH>"""

class FileSystemUploader(VirtualUploader):

    def __init__(self, aTarget, aLogger, aCollection):
        VirtualUploader.__init__(self, aLogger)
        self._target = aTarget
        if not os.path.isdir(self._target.path):
            os.makedirs(self._target.path)

    def tznow(self):
        return strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())

    def send(self, anUpload):
        """
        Writes the original header and metadata to a file.
        """
        try:
            filename = self._filenameFor(anUpload)
            dirname = os.path.dirname(filename)
            if not os.path.isdir(dirname):
                os.makedirs(os.path.dirname(filename))
            with open(filename, "wb") as f:
                f.write(tostring(self._createOutput(anUpload), xml_declaration=True))
        except Exception as e:
            raise UploaderException(uploadId=anUpload.id, message=str(e))

    def _createOutput(self, anUpload):
        if not self._target.oaiEnvelope:
            return anUpload.record
        envelopedata = {
            'identifier': xmlEscape(anUpload.recordIdentifier),
            'metadataPrefix': xmlEscape(str(anUpload.repository.metadataPrefix)),
            'baseurl': xmlEscape(str(anUpload.repository.baseurl)),
            'responseDate': self.tznow(),
            'recordData': lxmltostring(anUpload.record)
        }
        return parse(StringIO(OAI_ENVELOPE % envelopedata), XMLParser(ns_clean=True)).getroot()

    def _properFilename(self, anId):
        if anId in ['.', '..'] or chr(0) in anId or len(anId) > 255 or \
            len(anId) == 0:
            anId = "_malformed_id." + str(time())
        return str(anId).replace(os.path.sep, '_SLASH_') + ".record"

    def _filenameFor(self, anUpload):
        filename = self._properFilename(anUpload.id)
        return os.path.join(self._target.path, anUpload.repository.repositoryGroupId, anUpload.repository.id, filename)

    def delete(self, anUpload):
        filename = self._filenameFor(anUpload)
        if not self._target.oaiEnvelope:
            os.path.isfile(filename) and os.remove(filename)
            with open(os.path.join(self._target.path, 'deleted_records'),'a') as f:
                f.write('%s\n' % escapeFilename(anUpload.id))
        else:
            xmlResult = self._createOutput(anUpload)
            with open(filename, 'w') as fd:
                fd.write(lxmltostring(xmlResult))
        self._logDelete(anUpload.id)

    def info(self):
        return 'Writing records to path:%s' % (self._target.path)
