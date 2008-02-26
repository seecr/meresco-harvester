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
# $Id: disallowfileplugintest.py 4825 2007-04-16 13:36:24Z TJ $
#

import unittest
from disallowfileplugin import DisallowFilePlugin
import tempfile,os

class MockRequest:
	def __init__(self):
		self._session = None

	def setUser(self, aString):
		self._user = aString

	def user(self):
		return self._user

	def getSession(self):
		if self._session == None:
			self._session = {}
		return self._session

class DisallowFilePluginTest(unittest.TestCase):

	def testHandle(self):
		# The handle call should not throw an exception.
		# If it does, then something is wrong.
		dfp = DisallowFilePlugin()
		req = MockRequest()

		dfp.handle(req, '/zomaariets')
		
		# "edit" is a special page that requires a user to be logged in.
		req.getSession()['username'] = 'karel'
		dfp.handle(req, '/edit')
		
	def testDonotHandle(self):
		dfp = DisallowFilePlugin()
		req = MockRequest()
		try:
			dfp.handle(req, '/some/path/to/datadirectory/edit')
			self.fail()
		except IOError, e:
			self.assertEquals('[Errno 2] No such file or directory',str(e)[:35])

	def testInitializePatterns(self):
		nr,filename = tempfile.mkstemp()
		try:
			pf = open(filename,'w')
			pf.write('edit\n\r\nsave\r\n\r\n\n\nmapping.edit\n\n\n')
			pf.close()
			dfp = DisallowFilePlugin(patternfile=filename)
			self.assertEquals(['edit','save','mapping.edit'],dfp._patterns)
		finally:
			os.remove(filename)
		
						

if __name__ == '__main__': unittest.main()
