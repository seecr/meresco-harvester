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
from virtualuploader import VirtualUploader
import time, os
from cq2utils import binderytools

class FileSystemUploader(VirtualUploader):
	
	def __init__(self, aTarget, aLogger, aCollection):
		VirtualUploader.__init__(self, aLogger)
		self._target = aTarget
		if not os.path.isdir(self._target.path):
			os.makedirs(self._target.path)
	
	def send(self, anUpload):
		"""
		Writes the original header and metadata to a file.
		The fields are ignored.
		"""
		filename = self._filenameFor(anUpload)
		dirname = os.path.dirname(filename)
		if not os.path.isdir(dirname):
			os.makedirs(os.path.dirname(filename))
		f = open(filename, 'w')
		try:
			theXml = binderytools.bind_string('<record xmlns="http://www.openarchives.org/OAI/2.0/"/>')
			theXml.record.xml_children.append(anUpload.header)
			theXml.record.xml_children.append(anUpload.metadata)
			f.write(theXml.xml())
		finally:
			f.close()

	def _properFilename(self, anId):
		if anId in ['.', '..'] or chr(0) in anId or len(anId) > 255 or \
			len(anId) == 0:
			anId = "_malformed_id." + str(time.time())
		return str(anId).replace(os.path.sep, '_SLASH_') + ".record"

	def _filenameFor(self, anUpload):
		filename = self._properFilename(anUpload.id)
		return os.path.join(self._target.path, anUpload.repository.repositoryGroupId, anUpload.repository.id, filename)
			
	def delete(self, anUpload):
		filename = self._filenameFor(anUpload)
		os.path.isfile(filename) and os.remove(filename)
		f = open(os.path.join(self._target.path,
			'deleted_records'),'a')
		try:
			f.write('%s\n' % anUpload.id)
		finally:
			f.close()
		self.logDelete(anUpload.id)
	
	def info(self):
		return 'Writing records to path:%s' % (self._target.path)
