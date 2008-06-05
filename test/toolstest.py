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
import unittest
from merescoharvester.controlpanel import tools

class ToolsTest(unittest.TestCase):
	def testCheckName(self):
		assert tools.checkName('domain')
		assert not tools.checkName('doma:in')
		assert tools.checkName('doD432_main')
		assert tools.checkName('doD432-main')
		assert not tools.checkName('doma:in')
		assert not tools.checkName(' domain')
		assert not tools.checkName('do main')
		assert not tools.checkName('doma?in')
		assert not tools.checkName('doma@in')

	def testDomainId(self):
		self.assertEquals('cq2Mock', tools.getDomainId('/cq2Mock.hoi.st'))
		self.assertEquals('cq2Mock', tools.getDomainId('cq2Mock.hoi.st'))
		self.assertEquals('cq2Mock', tools.getDomainId('/asf/asdf/cq2Mock.hoi.st'))

