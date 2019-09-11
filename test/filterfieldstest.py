## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2019 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2019 Stichting Kennisnet https://www.kennisnet.nl
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

from unittest import TestCase
from seecr.test import CallTrace
from weightless.core import be
from meresco.core import Observable
from meresco.harvester.filterfields import FilterFields

class FilterFieldsTest(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.observer = CallTrace()
        definition = {
            'repository_fields': [
                {"name": "name", "export": True},
                {"name": "hidden", "export": False},
            ]
        }
        self.top = be((Observable(),
            (FilterFields(definition),
                (self.observer,)
            )
        ))

    def testFilterGetRepositories(self):
        self.observer.returnValues['getRepositories'] = [
                {'identifier':'identA', 'extra':{'name':'Repo name A', 'hidden': 'Hidden 1'}},
                {'identifier':'identB', 'extra':{'name':'Repo name B', 'hidden': 'Hidden 2'}},
                {'identifier':'identC', }
            ]
        result = self.top.call.getRepositories(arg1=1, arg2=2)
        self.assertEqual([
                {'identifier':'identA', 'extra':{'name':'Repo name A'}},
                {'identifier':'identB', 'extra':{'name':'Repo name B'}},
                {'identifier':'identC'}
            ], result)
        self.assertEqual({'arg1':1, 'arg2':2}, self.observer.calledMethods[0].kwargs)

    def testFilterGetRepository(self):
        self.observer.returnValues['getRepository'] = {'identifier':'identA', 'extra':{'name':'Repo name A', 'hidden': 'Hidden 1'}}
        result = self.top.call.getRepository(arg1=1, arg2=2)
        self.assertEqual({'identifier':'identA', 'extra':{'name':'Repo name A'}}, result)
        self.assertEqual({'arg1':1, 'arg2':2}, self.observer.calledMethods[0].kwargs)

    def testOthers(self):
        self.observer.returnValues['getTarget'] = {'some':'data'}
        result = self.top.call.getTarget(arg1=1, arg2=2)
        self.assertEqual({'some':'data'}, result)
        self.assertEqual({'arg1':1, 'arg2':2}, self.observer.calledMethods[0].kwargs)

