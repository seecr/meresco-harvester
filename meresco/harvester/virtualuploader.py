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
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
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

INVALID_COMPONENT = 1
INVALID_DATA = 2

class UploaderException(Exception):
    def __init__(self, uploadId, message):
        Exception.__init__(self, 'uploadId: "%s", message: "%s"' % (uploadId, message))
        self.uploadId = uploadId
        self.originalMessage = message

class InvalidComponentException(UploaderException):
    pass

class InvalidDataException(UploaderException):
    pass

class TooMuchInvalidDataException(UploaderException):
    def __init__(self, uploadId, maxIgnore):
        UploaderException.__init__(self, uploadId, "Exceeded maximum number (%d) of invalid data records." % maxIgnore)

class VirtualUploader(object):
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

    def uploaderInfo(self):
        return self.info()

    def _logLine(self, *args, **kwargs):
        self._logger.logLine(*args, **kwargs)

    def _logDelete(self, anId):
        self._logLine('DELETE', "Delete document", id=anId)

    def _logWarning(self, *args, **kwargs):
        self._logger.logWarning(*args, **kwargs)

class UploaderFactory(object):
    def __init__(self):
        from sruupdateuploader import SruUpdateUploader
        from compositeuploader import CompositeUploader
        from filesystemuploader import FileSystemUploader
        self.mapping = {
                    'sruUpdate': SruUpdateUploader,
                    'composite': CompositeUploader,
                    'filesystem': FileSystemUploader
                    }

    def createUploader(self, target, logger, collection):
        uploaderClass = self.mapping[target.targetType]
        return uploaderClass(target, logger, collection)

