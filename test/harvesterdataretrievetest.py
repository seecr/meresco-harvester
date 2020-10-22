## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.components.http.utils import CRLF, okJson
from meresco.components.json import JsonDict
from meresco.harvester.harvesterdataretrieve import HarvesterDataRetrieve
from weightless.core import asString, DeclineMessage

class HarvesterDataRetrieveTest(SeecrTestCase):

    def testGetSomethingIsAllowed(self):
        dataRetrieve = HarvesterDataRetrieve()
        observer = CallTrace('observer', returnValues=dict(getSomething='get something result', listSomething=['a', 'b']))
        dataRetrieve.addObserver(observer)

        result = asString(dataRetrieve.handleRequest(arguments=dict(verb=['GetSomething'], argument=['value'])))
        header, body = result.split(CRLF*2,1)
        self.assertEqual(okJson, header+CRLF*2)
        self.assertEqual({'request': {
            'verb': 'GetSomething', 'argument': 'value',
            }, 'response': {'GetSomething': 'get something result'}}, JsonDict.loads(body))
        self.assertEqual(['getSomething'], observer.calledMethodNames())
        self.assertEqual({'argument': 'value'}, observer.calledMethods[0].kwargs)

    def testGetUnexisting(self):
        dataRetrieve = HarvesterDataRetrieve()
        observer = CallTrace('observer')
        observer.exceptions=dict(getUnexisting=DeclineMessage())
        dataRetrieve.addObserver(observer)
        result = asString(dataRetrieve.handleRequest(arguments=dict(verb=['GetUnexisting'], argument=['value'])))
        header, body = result.split(CRLF*2,1)
        self.assertEqual(okJson, header+CRLF*2)
        self.assertEqual({'request': {'verb': 'GetUnexisting', 'argument': 'value'}, 'error': {'message': 'Value of the verb argument is not a legal verb, the verb argument is missing, or the verb argument is repeated.', 'code': 'badVerb'}}, JsonDict.loads(body))
        self.assertEqual(['getUnexisting'], observer.calledMethodNames())
        self.assertEqual({'argument': 'value'}, observer.calledMethods[0].kwargs)

    def testNoVerb(self):
        dataRetrieve = HarvesterDataRetrieve()
        observer = CallTrace('observer')
        dataRetrieve.addObserver(observer)
        result = asString(dataRetrieve.handleRequest(arguments=dict(argument=['value'])))
        header, body = result.split(CRLF*2,1)
        self.assertEqual(okJson, header+CRLF*2)
        self.assertEqual({'request': {'argument': 'value'}, 'error': {'message': 'Value of the verb argument is not a legal verb, the verb argument is missing, or the verb argument is repeated.', 'code': 'badVerb'}}, JsonDict.loads(body))
        self.assertEqual([], observer.calledMethodNames())

    def testErrorInCall(self):
        dataRetrieve = HarvesterDataRetrieve()
        observer = CallTrace('observer')
        observer.exceptions = dict(getError=Exception('Bad Bad Bad'))
        dataRetrieve.addObserver(observer)
        result = asString(dataRetrieve.handleRequest(arguments=dict(verb=['GetError'])))
        header, body = result.split(CRLF*2,1)
        self.assertEqual(okJson, header+CRLF*2)
        self.assertEqual({'request': {'verb': 'GetError'}, 'error': {'message': "Exception('Bad Bad Bad')", 'code': 'unknown'}}, JsonDict.loads(body))
        self.assertEqual(['getError'], observer.calledMethodNames())

    def testKnownCodeException(self):
        dataRetrieve = HarvesterDataRetrieve()
        observer = CallTrace('observer')
        observer.exceptions = dict(getError=Exception('idDoesNotExist'))
        dataRetrieve.addObserver(observer)
        result = asString(dataRetrieve.handleRequest(arguments=dict(verb=['GetError'])))
        header, body = result.split(CRLF*2,1)
        self.assertEqual(okJson, header+CRLF*2)
        self.assertEqual({'request': {'verb': 'GetError'}, 'error': {'message': 'The value of an argument (id or key) is unknown or illegal.', 'code': 'idDoesNotExist'}}, JsonDict.loads(body))
        self.assertEqual(['getError'], observer.calledMethodNames())

    def testSomethingElseThanGetIsNotAllowed(self):
        dataRetrieve = HarvesterDataRetrieve()
        observer = CallTrace('observer')
        dataRetrieve.addObserver(observer)
        result = asString(dataRetrieve.handleRequest(arguments=dict(argument=['value'], verb=['AddObserver'])))
        header, body = result.split(CRLF*2,1)
        self.assertEqual(okJson, header+CRLF*2)
        self.assertEqual({'request': {'verb': 'AddObserver', 'argument': 'value'}, 'error': {'message': 'Value of the verb argument is not a legal verb, the verb argument is missing, or the verb argument is repeated.', 'code': 'badVerb'}}, JsonDict.loads(body))
        self.assertEqual([], observer.calledMethodNames())

