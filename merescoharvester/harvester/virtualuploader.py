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

import sys

class UploaderException(Exception):
    pass

class VirtualUploader:
    def __init__(self, eventlogger):
        self._logger = eventlogger

    def start(self):
        """Overwrite to initiate connections needed."""
        pass

    def stop(self):
        """Overwrite to stop initiated connections."""
        pass

    def send(self, anUpload):
        """Send data in upload object, identified by upload.id"""
        raise NotImplementedError(self.send.__doc__)

    def delete(self, anUpload):
        """Delete the record with anUpload.id"""
        raise NotImplementedError(self.delete.__doc__)

    def info(self):
        """Return information on yourself."""
        raise NotImplementedError(self.info.__doc__)

    def logLine(self, *args, **kwargs):
        self._logger.logLine(*args, **kwargs)

    def logError(self, *args, **kwargs):
        self._logger.error(*args, **kwargs)

    def logDelete(self, anId):
        self.logLine('DELETE', "Delete document", id=anId)

class UploaderFactory:

    def __init__(self):
        from sseuploader import SSEUploader
        from sruupdateuploader import SruUpdateUploader
        from teddyuploader import TeddyUploader
        from compositeuploader import CompositeUploader
        from filesystemuploader import FileSystemUploader
        self.mapping = {
                    'sruUpdate': SruUpdateUploader,
                    'sse': SSEUploader,
                    'teddy': TeddyUploader,
                    'composite': CompositeUploader,
                    'filesystem': FileSystemUploader
                    }

    def createUploader(self, target, logger, collection):
        uploaderClass = self.mapping[target.targetType]
        return uploaderClass(target, logger, collection)
