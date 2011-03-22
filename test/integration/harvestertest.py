#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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

from os import system, waitpid, listdir
from os.path import join, dirname, abspath
from urllib import urlopen
from time import time, sleep
from subprocess import Popen
from shutil import copytree

from cq2utils import CQ2TestCase
from utils import getRequest

from integrationtestcase import IntegrationTestCase

class HarvesterTest(IntegrationTestCase):
    def setUp(self):
        IntegrationTestCase.setUp(self)
        system("rm -rf %s/*" % self.dumpDir)
        system("rm -rf %s" % self.harvesterLogDir)
        system("rm -rf %s" % self.harvesterStateDir)

    def testHarvestToDump(self):
        self.startHarvester()
        self.assertEquals(14, len(listdir(self.dumpDir)))
        self.assertEquals(2, len([f for f in listdir(self.dumpDir) if "info:srw/action/1/delete" in open(join(self.dumpDir, f)).read()]))
        ids = open(join(self.harvesterStateDir, "adomain", "integrationtest.ids")).readlines()
        self.assertEquals(10, len(ids))
        ignoredIds = open(join(self.harvesterStateDir, "adomain", "integrationtest_ignored.ids")).readlines()
        self.assertEquals(0, len(ignoredIds))

    def testInvalidIgnoredUptoMaxIgnore(self):
        self.startHarvester()
        self.assertEquals(2, len(listdir(self.dumpDir)))
        ids = open(join(self.harvesterStateDir, "adomain", "integrationtest.ids")).readlines()
        self.assertEquals(0, len(ids))
        ignoredIds = open(join(self.harvesterStateDir, "adomain", "integrationtest_ignored.ids")).readlines()
        self.assertEquals(5, len(ignoredIds), ignoredIds)
        ignoreDir = join(self.harvesterLogDir, "adomain", "ignored", "integrationtest")
        self.assertEquals(5, len(listdir(ignoreDir)))
        ignoreId1Error = open(join(ignoreDir, "recordID1")).read()
        self.assertTrue('uploadId: "integrationtest:recordID1"', ignoreId1Error)

