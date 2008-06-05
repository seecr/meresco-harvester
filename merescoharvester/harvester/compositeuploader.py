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

from virtualuploader import VirtualUploader, UploaderFactory
from target import Target

class CompositeUploader(VirtualUploader):
    
    def __init__(self, aTarget, aLogger, aCollection):
        VirtualUploader.__init__(self, aLogger)
        self._collection = aCollection
        self._target = aTarget
        self._delegates = self._getDelegates()
        
    def _getDelegates(self):
        result = []
        factory = UploaderFactory()
        for id in self._target.delegate:
            target = self._target._saharaget.getTarget(self._target.domainId, id)
            uploader = factory.createUploader(target, self._logger, self._collection)
            result.append(uploader)
        return result
    
    def start(self):
        for delegate in self._delegates:
            delegate.start()
    
    def stop(self):
        for delegate in self._delegates:
            delegate.stop()
        
    def send(self, anUpload):
        for delegate in self._delegates:
            delegate.send(anUpload)
    
    def delete(self, uploadId):
        for delegate in self._delegates:
            delegate.delete(uploadId)
    
    def info(self):
        result = []
        return "Composite Uploader: " + str(result)
