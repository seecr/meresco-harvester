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
#
# Copyright (C) 2005 Seek You Too B.V. http://www.cq2.nl
#
# $Id: virtualuploader.py 146 2006-03-27 12:50:57Z svn $
#
from virtualuploader import VirtualUploader
from xml.sax.saxutils import escape as xmlEscape
from cq2utils.networking import sshclient, growlclient
import time

STANDARD_FIELD_LINE = """<field name="%s">%s</field>"""
NO_TOKENIZE_FIELD_LINE = """<field name="%s" tokenize="false">%s</field>"""

class TeddyUploader(VirtualUploader):
    
    def __init__(self, aTarget, aLogger, aCollection):
        VirtualUploader.__init__(self, aLogger)
        self._collection = aCollection
        self._target = aTarget
        self._growlClient = None
    
    def start(self):
        self._sshlayer = sshclient.open(self._target.hostname, self._target.port, self._target.username, self._target.privateKey, self._target.command)
        
        self._growlClient = growlclient.GrowlClient(self._sshlayer)
        self._growlClient.start()
    
    def stop(self):
        self._growlClient.stop()
        EOF = '\4'
        self._sshlayer.write(EOF)
        self._growlClient.waitForServerStop()
        self._sshlayer.close()
        #TODO future improvement:
        #os.kill(self.pipe.pid, signal.SIGTERM) where self.pipe is a ref. to the original ssh-process. This demands some refactoring.
        
    def send(self, anUpload):
        anId = anUpload.id
        self.logLine('UPLOAD.SEND', 'START', id = anId)
        self._growlClient.startDocument(anId)
        
        fields = self._prepareFieldList(anUpload)
        stream = self._growlClient.startPart("fields", "text/xml")
        self._writeFields(stream, fields, anUpload.getProperty('sortfields'))
        self._growlClient.stopPart()
        for partname, partvalue in anUpload.parts.items():
            stream = self._growlClient.startPart(partname, "text/plain")
            stream.write(xmlEscape(partvalue))
            self._growlClient.stopPart()
        self._growlClient.stopDocument()
        self.logLine('UPLOAD.SEND', 'END', id = anId)
    
    def delete(self, anUpload):
        self.logDelete(anUpload.id)
        self._growlClient.delete(anUpload.id)
    
    def info(self):
        return 'Uploader connected to: %s:%s (%s), collection: %s'%(self._target.baseurl, self._target.port, self._target.username, self._collection)
    
    def _prepareFieldList(self, anUpload):
        fields = []
        for k,v in anUpload.fields.items():
            value = v
            if not isinstance(v, list):
                value = [v]
                
            for item in value:
                fields.append((xmlEscape(k), xmlEscape(item)))
        fields.append(('collection', xmlEscape(self._collection)))
        return fields

    def _writeFields(self, aStream, fields, sortfields):
        aStream.write('<fields>')
        for (k,v) in fields:
            line = k in sortfields and NO_TOKENIZE_FIELD_LINE or STANDARD_FIELD_LINE
            aStream.write(line % (k, v))
        aStream.write("</fields>")
