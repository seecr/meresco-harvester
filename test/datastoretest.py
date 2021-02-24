## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from seecr.test import SeecrTestCase

from meresco.harvester.datastore import DataStore, OldDataStore

class DataStoreTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.n = 0
        def idfn():
            self.n += 1
            return 'mock:{}'.format(self.n)
        self.store = DataStore(self.tempdir, id_fn=idfn)

    def testData(self):
        self.store.addData('mijnidentifier', 'datatype', {'mijn':'data'})
        d = self.store.getData('mijnidentifier', 'datatype')
        self.assertEqual({'mijn': 'data', '@id': 'mock:1'}, d)
        d['mijn'] = 'andere data'
        self.store.addData('mijnidentifier', 'datatype', d)
        d = self.store.getData('mijnidentifier', 'datatype')
        self.assertEqual({'mijn': 'andere data', '@id': 'mock:2', '@base': 'mock:1'}, d)
        self.store.deleteData('mijnidentifier', 'datatype')
        self.assertRaises(ValueError, lambda: self.store.getData('mijnidentifier', 'datatype'))
        self.assertEqual({'mijn': 'andere data', '@id': 'mock:2', '@base': 'mock:1'}, self.store.getData('mijnidentifier', 'datatype', 'mock:2'))

    def testListData(self):
        self.store.addData('nr:1', 'datatype', {'mijn':'data'})
        self.store.addData('nr:2', 'datatype', {'mijn':'data'})
        self.store.addData('nr:3', 'other', {'mijn':'data'})
        self.assertEqual(['nr:1', 'nr:2'], self.store.listForDatatype('datatype'))
