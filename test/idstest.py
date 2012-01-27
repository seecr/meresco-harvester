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
# Copyright (C) 2007-2009, 2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
# 
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
from meresco.harvester.ids import Ids

class IdsTest(SeecrTestCase):
    def tearDown(self):
        ids = getattr(self, 'ids', None)
        if ids: ids.close()
        SeecrTestCase.tearDown(self)
        
    def testAddOne(self):
        self.ids = Ids(self.tempdir + '/doesnotexistyet/', 'idstest')
        self.ids.add('id:1')
        self.assertEquals(1, len(self.ids))
        
    def testAddTwice(self):
        self.ids = Ids(self.tempdir, 'idstest')
        self.ids.add('id:1')
        self.ids.add('id:1')
        self.assertEquals(1, len(self.ids))
        self.assertEquals(1, len(open(self.tempdir + '/idstest.ids').readlines()))
        
    def testInit(self):
        self.writeTestIds('one',['id:1'])
        self.ids = Ids(self.tempdir, 'one')
        self.assertEquals(1, len(self.ids))
        self.writeTestIds('three',['id:1', 'id:2', 'id:3'])
        self.ids = Ids(self.tempdir, 'three')
        self.assertEquals(3, len(self.ids))
        
    def testRemoveExistingId(self):
        self.writeTestIds('three',['id:1', 'id:2', 'id:3'])
        self.ids = Ids(self.tempdir, 'three')
        self.ids.remove('id:1')
        self.assertEquals(2, len(self.ids))
        self.assertEquals(2, len(open(self.tempdir + '/three.ids').readlines()))
        self.ids.close()
        
    def testRemoveNonExistingId(self):
        self.writeTestIds('three',['id:1', 'id:2', 'id:3'])
        self.ids = Ids(self.tempdir, 'three')
        self.ids.remove('id:4')
        self.assertEquals(3, len(self.ids))
        self.ids.close()
        self.assertEquals(3, len(open(self.tempdir + '/three.ids').readlines()))
        
        
    def writeTestIds(self, name, ids):
        w = open(self.tempdir+ '/' + name + '.ids', 'w')
        try:
            for anId in ids:
                w.write(anId + '\n')
        finally:
            w.close()
