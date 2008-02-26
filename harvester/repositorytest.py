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
# (c) 2005 Seek You Too B.V.
#
# $Id: repositorytest.py 4825 2007-04-16 13:36:24Z TJ $
from saharaget import SaharaGet, SaharaGetException
from eventlogger import NilEventLogger
from harvesterlog import HarvesterLog
from repository import *
from cq2utils.wrappers import wrapp
from cq2utils.timeslot import Timeslot
from cq2utils.calltrace import CallTrace
import tempfile, os, shutil
import unittest

class RepositoryTest(unittest.TestCase):
	def setUp(self):
		self.repo = Repository('domainId','rep')
		self.repo._saharaget = self
		self.logpath = os.path.join(tempfile.gettempdir(),'repositorytest')
		self._read = self.mock_read
		self.mock_read_args = []
		self.logpath = os.path.join(tempfile.gettempdir(), 'repositorytest')
		os.path.isdir(self.logpath) or os.mkdir(self.logpath)


	def tearDown(self):
		shutil.rmtree(self.logpath)

	def testNoTimeslots(self):
		slots = self.repo.shopclosed
		self.assertEquals(None, slots)
		self.assertFalse(self.repo.shopClosed())

	def testInitHarvestExclusionInterval(self):
		self.repo.fill(self, wrapp(binderytools.bind_string(GETREPOSITORY).repository))
		slots = self.repo.shopclosed
		self.assertEquals(2, len(slots))
		self.assertEquals('*:*:10:30-*:*:11:45', slots[0])
		self.assertEquals('*:5:5:59-*:5:23:00', slots[1])

	def testShopClosed(self):
		self.repo.fill(self, wrapp(binderytools.bind_string(GETREPOSITORY).repository))
		timeslots = self.repo.closedSlots()
		self.assertEquals(False, self.repo.shopClosed(dateTuple = (2006,1,1,11,50)))

	def testTimeslotInitialization(self):
		from cq2utils.timeslot import Wildcard
		self.repo.fill(self, wrapp(binderytools.bind_string(GETREPOSITORY).repository))
		timeslots = self.repo.closedSlots()
		self.assertEquals(2, len(timeslots))
		self.assertFalse(self.repo.shopClosed(dateTuple = (2006,1,1,11,50)))
		timeslots[1]._end = (Wildcard(), Wildcard(), Wildcard(), Wildcard())
		
		self.assertTrue(self.repo.shopClosed(dateTuple = (2006,1,1,11,50)))

	def testShopNotClosedAndThenClosed(self):
		from cq2utils.timeslot import Wildcard
		self.repo.fill(self, wrapp(binderytools.bind_string(GETREPOSITORY).repository))
		timeslots = self.repo.closedSlots()
		self.assertFalse(self.repo.shopClosed(dateTuple = (2006,1,1,11,50)))
		
		timeslots[0]._end = (Wildcard(), Wildcard(), Wildcard(), Wildcard())
		self.assertTrue(self.repo.shopClosed(dateTuple = (2006,1,1,11,50)))

	def testDoNothing(self):
		self.repo.use = ''
		self.repo.action = ''
		action = MockAction()
		self.repo._createAction=lambda a: action
		result = self.repo.do(self.logpath)
		self.assertEquals('', result)
		self.assert_(action.called)
		self.assertEquals('', self.repo.use)
		self.assertEquals('', self.repo.action)

	def testDoHarvest(self):
		self.repo.use = 'true'
		self.repo.action = ''
		action = MockAction(DONE)
		self.repo._createAction=lambda a: action
		result = self.repo.do(self.logpath)
		self.assertEquals(DONE, result)
		self.assert_(action.called)
		self.assertEquals('true', self.repo.use)
		self.assertEquals('', self.repo.action)

	def testDoSomeAction(self):
		self.repo._saharaget = self
		self.repo.action = 'someaction'
		action = MockAction(DONE)
		self.repo._createAction=lambda a: action
		result = self.repo.do(self.logpath)
		self.assertEquals(DONE, result)
		self.assert_(action.called)
		self.assertEquals('', self.repo.action)
		self.assertEquals('domainId', self.mock_repositoryActionDone_domainId)
		self.assertEquals('rep', self.mock_repositoryActionDone_repositoryId)

	def testDoSomeActionThatMustBeRepeated(self):
		self.repo.use = 'true'
		self.repo.action = 'someaction'
		action = MockAction('Not yet done!', False)
		self.repo._createAction=lambda a: action
		result = self.repo.do(self.logpath)
		self.assertEquals('Not yet done!', result)
		self.assert_(action.called)
		self.assertEquals('true', self.repo.use)
		self.assertEquals('someaction', self.repo.action)

	def _testAction(self, use, action, expectedType):
		factory = ActionFactory()
		self.repo.use = use
		self.repo.action = action
		self.assert_(isinstance(self.repo._createAction(self.logpath), expectedType))

	def testActionFactory(self):
		self._testAction('', '', NoneAction)
		self._testAction('true', '', HarvestAction)
		self._testAction('', 'clear', DeleteIdsAction)
		self._testAction('true', 'clear', DeleteIdsAction)
		self._testAction('', 'refresh', SmoothAction)
		self._testAction('true', 'refresh', SmoothAction)
		try:
			self._testAction('true', 'nonexisting', None)
			self.fail()
		except ActionFactoryException, afe:
			self.assertEquals("Action 'nonexisting' not supported.", str(afe))

	def testDoWithoutLogpath(self):
		try:
			self.repo.do('')
			self.fail()
		except RepositoryException, e:
			pass

	def testHarvestAction(self):
		repository = CallTrace("Repository")
		logpath = CallTrace("LogPath")
		harvester = CallTrace("Harvester")
		
		repository.returnValues['shopClosed'] = False
		action = HarvestAction(repository, logpath)
		action._createHarvester = lambda: harvester
		action.do()
		self.assertEquals(['harvest()'], harvester.__calltrace__())
		
		repository.returnValues['shopClosed'] = True
		harvester = CallTrace("Harvester")
		action._createHarvester = lambda: harvester
		action.do()
		self.assertEquals([], harvester.__calltrace__())

	# mock saharaget
	def repositoryActionDone(self, domainId, repositoryId):
		self.mock_repositoryActionDone_domainId = domainId
		self.mock_repositoryActionDone_repositoryId = repositoryId

	def mock_read(self, **kwargs):
		self.mock_read_args.append(kwargs)
		verb = kwargs['verb']
		if verb == 'GetRepository':
			return wrapp(binderytools.bind_string(GETREPOSITORY))


class MockAction(Action):
	def __init__(self, message = '', done = True):
		self.message = message
		self.done = done
		self.called = False

	def do(self):
		self.called = True
		return self.done, self.message

GETREPOSITORY = """<?xml version="1.0" encoding="UTF-8"?>
<repository>
	<use>true</use>
	<action>refresh</action>
	<id>cq2Repository2_1</id>
	<baseurl>http://baseurl.example.org</baseurl>
	<set>set</set>
	<collection>collection</collection>
	<metadataPrefix>oai_dc</metadataPrefix>
	<targetId>aTargetId</targetId>
	<mappingId>aMappingId</mappingId>
	<repositoryGroupId>cq2Group2</repositoryGroupId>
	<shopclosed>*:*:10:30-*:*:11:45</shopclosed>
	<shopclosed>*:5:5:59-*:5:23:00</shopclosed>
</repository>
"""


if __name__ == '__main__':
	unittest.main()