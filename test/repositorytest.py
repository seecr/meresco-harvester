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
# Copyright (C) 2010-2011, 2015 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2013, 2015, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020 SURF https://surf.nl
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

from seecr.test import SeecrTestCase, CallTrace

from meresco.harvester.eventlogger import NilEventLogger
from meresco.harvester.repository import Repository
from meresco.harvester.action import Action, DONE, ActionException
from meresco.harvester.oairequest import OAIError
from meresco.harvester.timeslot import Wildcard
from os.path import join

class RepositoryTest(SeecrTestCase):
    def setUp(self):
        super(RepositoryTest, self).setUp()

        self.oaiRequestMock = None
        self.oaiRequestArgsKwargs = None
        def mockOaiRequest(*args, **kwargs):
            self.oaiRequestArgsKwargs = args, kwargs
            self.oaiRequestMock = CallTrace()
            return self.oaiRequestMock

        self.repo = Repository('domainId','rep', oaiRequestClass=mockOaiRequest)
        self.repo._proxy = self
        self.logAndStateDir = join(self.tempdir, 'repositorytest')

    def testNoTimeslots(self):
        slots = self.repo.shopclosed
        self.assertEqual(None, slots)
        self.assertFalse(self.repo.shopClosed())

    def testInitHarvestExclusionInterval(self):
        self.repo.fill(self, GETREPOSITORY)
        slots = self.repo.shopclosed
        self.assertEqual(2, len(slots))
        self.assertEqual('*:*:10:30-*:*:11:45', slots[0])
        self.assertEqual('*:5:5:59-*:5:23:00', slots[1])

    def testShopClosed(self):
        self.repo.fill(self, GETREPOSITORY)
        self.repo.closedSlots()
        self.assertEqual(False, self.repo.shopClosed(dateTuple = (2006,1,1,11,50)))

    def testTimeslotInitialization(self):
        self.repo.fill(self, GETREPOSITORY)
        timeslots = self.repo.closedSlots()
        self.assertEqual(2, len(timeslots))
        self.assertFalse(self.repo.shopClosed(dateTuple = (2006,1,1,11,50)))
        timeslots[1]._end = (Wildcard(), Wildcard(), Wildcard(), Wildcard())

        self.assertTrue(self.repo.shopClosed(dateTuple = (2006,1,1,11,50)))

    def testShopNotClosedAndThenClosed(self):
        self.repo.fill(self, GETREPOSITORY)
        timeslots = self.repo.closedSlots()
        self.assertFalse(self.repo.shopClosed(dateTuple = (2006,1,1,11,50)))

        timeslots[0]._end = (Wildcard(), Wildcard(), Wildcard(), Wildcard())
        self.assertTrue(self.repo.shopClosed(dateTuple = (2006,1,1,11,50)))

    def testDoNothing(self):
        self.repo.use = False
        self.repo.action = None
        action = MockAction()
        self.repo._createAction=lambda stateDir,logDir,generalHarvestLog: action
        result = self.repo.do(stateDir=self.logAndStateDir, logDir=self.logAndStateDir)
        self.assertEqual(('', False), result)
        self.assertTrue(action.called)
        self.assertEqual(False, self.repo.use)
        self.assertEqual(None, self.repo.action)

    def testHarvestWithBadResumptionToken(self):
        self.repo.use = True
        self.repo.action = None
        self.repo.complete = True
        action = CallTrace('Action')
        oaiError = OAIError('url', 'resumptionToken expired', 'badResumptionToken', 'lxmlResponse')
        action.exceptions['do'] = oaiError
        self.repo._createAction = lambda **kwargs: action
        message, again = self.repo.do(stateDir=self.logAndStateDir, logDir=self.logAndStateDir)
        self.assertTrue('resumptionToken expired' in message)
        self.assertEqual(['info', 'do', 'resetState'], [m.name for m in action.calledMethods])
        self.assertTrue(again)

    def testDoHarvest(self):
        self.repo.use = True
        self.repo.action = None
        action = MockAction(DONE)
        self.repo._createAction=lambda stateDir,logDir,generalHarvestLog: action
        result = self.repo.do(stateDir=self.logAndStateDir, logDir=self.logAndStateDir)
        self.assertEqual((DONE, False), result)
        self.assertTrue(action.called)
        self.assertEqual(True, self.repo.use)
        self.assertEqual(None, self.repo.action)

    def testDoHarvestWithCompleteHarvestingEnabled(self):
        self.repo.use = True
        self.repo.action = None
        self.repo.complete = True
        action = MockAction(DONE, hasResumptionToken=True)
        self.repo._createAction=lambda stateDir,logDir,generalHarvestLog: action
        result = self.repo.do(stateDir=self.logAndStateDir, logDir=self.logAndStateDir)
        self.assertEqual((DONE, True), result)

    def testDoHarvestWithCompleteHarvestingDisabled(self):
        self.repo.use = True
        self.repo.action = None
        self.repo.complete = False
        action = MockAction(DONE, hasResumptionToken=True)
        self.repo._createAction=lambda stateDir,logDir,generalHarvestLog: action
        result = self.repo.do(stateDir=self.logAndStateDir, logDir=self.logAndStateDir)
        self.assertEqual((DONE, False), result)

    def testDoSomeAction(self):
        self.repo._saharaget = self
        self.repo.action = 'someaction'
        action = MockAction(DONE)
        self.repo._createAction=lambda stateDir,logDir,generalHarvestLog: action
        result = self.repo.do(stateDir=self.logAndStateDir, logDir=self.logAndStateDir)
        self.assertEqual((DONE, False), result)
        self.assertTrue(action.called)
        self.assertEqual(None, self.repo.action)
        self.assertEqual('domainId', self.mock_repositoryActionDone_domainId)
        self.assertEqual('rep', self.mock_repositoryActionDone_repositoryId)

    def testDoSomeActionThatMustBeRepeated(self):
        self.repo.use = True
        self.repo.action = 'someaction'
        action = MockAction('Not yet done!', False)
        self.repo._createAction=lambda stateDir,logDir,generalHarvestLog: action
        result, hasResumptionToken = self.repo.do(stateDir=self.logAndStateDir, logDir=self.logAndStateDir)
        self.assertEqual('Not yet done!', result)
        self.assertTrue(action.called)
        self.assertEqual(True, self.repo.use)
        self.assertEqual('someaction', self.repo.action)

    def _testAction(self, use, action, expectedTypeName):
        self.repo.use = use
        self.repo.action = action
        createdAction = self.repo._createAction(stateDir=self.logAndStateDir, logDir=self.logAndStateDir, generalHarvestLog=NilEventLogger())
        self.assertEqual(expectedTypeName, createdAction.__class__.__name__)

    def testCreateAction(self):
        self._testAction(False, None, 'NoneAction')
        self._testAction(None, None, 'NoneAction')
        self._testAction(True, None, 'HarvestAction')
        self._testAction(False, 'clear', 'DeleteIdsAction')
        self._testAction(True, 'clear', 'DeleteIdsAction')
        self._testAction(False, 'refresh', 'SmoothAction')
        self._testAction(True, 'refresh', 'SmoothAction')
        try:
            self._testAction(True, 'nonexisting', 'ignored')
            self.fail()
        except ActionException as afe:
            self.assertEqual("Action 'nonexisting' not supported.", str(afe))

    def testDoWithoutLogpath(self):
        generalHarvestLog = CallTrace('Log')
        message, again = self.repo.do('','', generalHarvestLog=generalHarvestLog)
        self.assertFalse(again)
        self.assertTrue('RepositoryException: Missing stateDir and/or logDir' in message)
        self.assertEqual((message,), generalHarvestLog.calledMethods[-1].args)
        self.assertEqual({'id':self.repo.id}, generalHarvestLog.calledMethods[-1].kwargs)
        self.assertEqual('logError', generalHarvestLog.calledMethods[-1].name)

    # mock saharaget
    def repositoryActionDone(self, domainId, repositoryId):
        self.mock_repositoryActionDone_domainId = domainId
        self.mock_repositoryActionDone_repositoryId = repositoryId

    def testPassOnUserAgentAndAuthorizationKey(self):
        self.repo.userAgent = "This is the User agent"
        self.repo.authorizationKey = "Let Me In"
        self.repo.oairequest()
        self.assertEqual(((None,), {'userAgent': 'This is the User agent', 'authorizationKey': 'Let Me In'}), self.oaiRequestArgsKwargs)

    def testNoneUserAgentIfEmpty(self):
        self.repo.userAgent = ''
        self.repo.oairequest()
        self.assertEqual(((None,), {'userAgent': None, 'authorizationKey': None}), self.oaiRequestArgsKwargs)

class MockAction(Action):
    def __init__(self, message = '', done = True, hasResumptionToken=False):
        self.message = message
        self.done = done
        self.called = False
        self.hasResumptionToken = hasResumptionToken

    def do(self):
        self.called = True
        return self.done, self.message, self.hasResumptionToken

GETREPOSITORY = {
    "use": True,
    "action": "refresh",
    "id": "cq2Repository2_1",
    "baseurl": "http://baseurl.example.org",
    "set": "set",
    "collection": "collection",
    "metadataPrefix": "oai_dc",
    "targetId": "aTargetId",
    "mappingId": "aMappingId",
    "repositoryGroupId": "cq2Group2",
    "shopclosed": ["*:*:10:30-*:*:11:45", "*:5:5:59-*:5:23:00"]
}
