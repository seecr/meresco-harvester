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

from __future__ import with_statement

import os, sys
from os.path import dirname, abspath
os.system('find .. -name "*.pyc" | xargs rm -f')

from glob import glob
for path in glob('../deps.d/*'):
    sys.path.insert(0, path)

myDir = dirname(abspath(__file__))
sys.path.insert(0, dirname(myDir))

from os import system, kill, WNOHANG, waitpid, listdir
from os.path import isdir, isfile, join
from sys import exit, exc_info
from unittest import main
from urllib import urlopen
from random import randint
from time import time, sleep
from lxml.etree import parse, tostring
from StringIO import StringIO
from signal import SIGTERM, SIGKILL
from subprocess import Popen
from shutil import copytree

from cq2utils import CQ2TestCase 

integrationTempdir = '/tmp/mh-integration-test'
dumpDir = join(integrationTempdir, "dump")
harvesterLogDir = join(integrationTempdir, "log")
harvesterStateDir = join(integrationTempdir, "state")
binDir = join(dirname(myDir), 'bin')

class IntegrationTest(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)
        system("rm -rf %s/*" % dumpDir)
        system("rm -rf %s" % harvesterLogDir)
        system("rm -rf %s" % harvesterStateDir)
        urlopen("http://localhost:%s/starttest" % dumpPortNumber)

    def testHarvestToDump(self):
        startHarvester()
        self.assertEquals(14, len(listdir(dumpDir)))
        self.assertEquals(2, len([f for f in listdir(dumpDir) if "info:srw/action/1/delete" in open(join(dumpDir, f)).read()]))
        ids = open(join(harvesterStateDir, "adomain", "integrationtest.ids")).readlines()
        self.assertEquals(10, len(ids))
        ignoredIds = open(join(harvesterStateDir, "adomain", "integrationtest_ignored.ids")).readlines()
        self.assertEquals(0, len(ignoredIds))

    def testInvalidIgnoredUptoMaxIgnore(self):
        urlopen("http://localhost:%s/starttest?name=testInvalidIgnoredUptoMaxIgnore" % dumpPortNumber)
        startHarvester()
        self.assertEquals(2, len(listdir(dumpDir)))
        ids = open(join(harvesterStateDir, "adomain", "integrationtest.ids")).readlines()
        self.assertEquals(0, len(ids))
        ignoredIds = open(join(harvesterStateDir, "adomain", "integrationtest_ignored.ids")).readlines()
        self.assertEquals(5, len(ignoredIds), ignoredIds)
        ignoreDir = join(harvesterLogDir, "adomain", "ignored", "integrationtest")
        self.assertEquals(5, len(listdir(ignoreDir)))
        ignoreId1Error = open(join(ignoreDir, "recordID1")).read()
        self.assertTrue('uploadId: "integrationtest:recordID1"', ignoreId1Error)

def fileSubstVars(filepath, **kwargs):
    contents = open(filepath).read()
    for k, v in kwargs.items():
        contents = contents.replace("${%s}" % k, str(v))
    open(filepath, "w").write(contents)

def initData(targetDir, dumpPortNumber, oaiPortNumber):
    copytree("integration-data", targetDir)
    fileSubstVars(join(targetDir, "data", "DUMP.target"), dumpPortNumber=dumpPortNumber)
    fileSubstVars(join(targetDir, "data", "integration.test.repository"), oaiPortNumber=oaiPortNumber)

def startDumpServer(dumpPort):
    stdoutfile = join(integrationTempdir, "stdouterr-dump.log")
    stdouterrlog = open(stdoutfile, 'w')
    processInfo = Popen(
        args=[join(integrationTempdir, "dumpserver.py"), str(dumpPort), dumpDir], 
        cwd=integrationTempdir, 
        stdout=stdouterrlog,
        stderr=stdouterrlog)
    print "DumpServer PID", processInfo.pid
    return processInfo

def startHarvester():
    stdoutfile = join(integrationTempdir, "stdouterr-harvester.log")
    stdouterrlog = open(stdoutfile, 'w')
    harvesterProcessInfo = Popen(
        args=["python", join(integrationTempdir, "start-integrationtest-harvester.py"), "-d", "adomain", "--logDir=%s" % harvesterLogDir, "--stateDir=%s" % harvesterStateDir], 
        cwd=integrationTempdir,
        env={'PYTHONPATH': sys.path[0], 'LANG': 'en_US.UTF-8'},
        stdout=stdouterrlog,
        stderr=stdouterrlog)
    print "Harvester PID", harvesterProcessInfo.pid
    waitpid(harvesterProcessInfo.pid, 0)

def startOaiFileServer(portNumber):
    stdoutfile = join(integrationTempdir, "stdouterr-oaifileserver.log")
    stdouterrlog = open(stdoutfile, 'w')
    processInfo = Popen(
        args=[join(integrationTempdir, "oaifileserver.py"), str(portNumber)], 
        cwd=integrationTempdir,
        stdout=stdouterrlog,
        stderr=stdouterrlog)
    print "Oai Fileserver PID", processInfo.pid
    return processInfo

def startHarvesterServer(portNumber):
    stdoutfile = join(integrationTempdir, "stdouterr-harvesterserver.log")
    stdouterrlog = open(stdoutfile, 'w')
    configFile = join(integrationTempdir, 'harvester.config') 
    open(configFile, 'w').write("portNumber=%s" % portNumber)
    processInfo = Popen(
        args=[join(binDir, "harvester-server"), configFile], 
        stdout=stdouterrlog,
        stderr=stdouterrlog)
    print "Harvester Server PID", processInfo.pid
    return processInfo

def stopProcess(processInfo):
    print "Stopping process", processInfo.pid
    kill(processInfo.pid, SIGTERM)
    waitpid(processInfo.pid, WNOHANG)

if __name__ == '__main__':
    system('rm -rf ' + integrationTempdir)
    dumpPortNumber = randint(50000,60000)
    oaiPortNumber = dumpPortNumber + 1
    harvesterPortNumber = dumpPortNumber + 2

    initData(integrationTempdir, dumpPortNumber, oaiPortNumber)
    
    dumpServerProcessInfo = startDumpServer(dumpPortNumber)
    oaiServerProcessInfo = startOaiFileServer(oaiPortNumber)
    harvesterServerProcessInfo = startHarvesterServer(harvesterPortNumber)
    sleep(3)
    try:
        main()
    finally:
        stopProcess(dumpServerProcessInfo)
        stopProcess(oaiServerProcessInfo)
        stopProcess(harvesterServerProcessInfo)

