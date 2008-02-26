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
# (c) 2005, Seek You Too B.V.
#
# $Id: startharvestertest.py 4825 2007-04-16 13:36:24Z TJ $
#
import unittest, tempfile, os, shutil
import startharvester

class StartHarvesterTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.gettempdir()
        self.testdir = self.tempdir + '/startharvestertest'
        os.path.isdir(self.testdir) and shutil.rmtree(self.testdir)
        os.makedirs(self.testdir)
        
    def testHarvest(self):
        #startharvester.harvest('sahararep1',logpath=self.testdir)
        pass

