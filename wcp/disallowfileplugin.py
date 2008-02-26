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
# (c) 2005 Seek You Too B.V.
#
from string import strip
BANNED_EXTENSIONS = ['domain', 'repositoryGroup', 'repository', 'mapping', 'target'] 

class DisallowFilePlugin:
	def __init__(self, patterns = ['edit', 'save'], patternfile = None):
		self._patterns = patternfile and self._readPatterns(patternfile) or patterns

	def _readPatterns(self, filename):
		patternfile = open(filename)
		try:
			return filter(None, map(strip,patternfile.readlines()))
		finally:
			patternfile.close()
		
	def inPatterns(self, aString):
		return aString in self._patterns

	def handle(self, request, path):
		filename = path.split('/')[-1]
		if self.inPatterns(filename):
			username = request.getSession().get('username', None)
			if username == None:
				raise IOError(2,"No such file or directory: '%s'"%path)
		extension = filename.split('.')[-1]
		if extension in BANNED_EXTENSIONS and not request.remoteHost() in ['127.0.0.1', 'localhost'] and request.getSession().get('username', None) == None:
			raise IOError(2,"No such file or directory: '%s'"%path)

