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
os.system('find .. -name "*.pyc" | xargs rm -f')

from glob import glob
for path in glob('../deps.d/*'):
    sys.path.insert(0, path)

sys.path.insert(0, "..")

from os import system, kill, WNOHANG, waitpid, listdir
from os.path import isdir, isfile, join
from sys import exit, exc_info
from unittest import main
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

class IntegrationTest(CQ2TestCase):
    def testHarvestToDump(self):
        self.assertEquals(10, len(listdir(dumpDir)))

def initData(targetDir, dumpPortNumber):
    copytree("integration-data", targetDir)
    with open(join(targetDir, "data", "DUMP.target"), 'w') as f:
        f.write("""<?xml version="1.0"?>
<target>
  <id>DUMP</id>
  <name>DUMP</name>
  <username></username>
  <port>%s</port>
  <targetType>sruUpdate</targetType>
  <path>/nix/neer</path>
  <baseurl>localhost</baseurl>
</target>""" % dumpPortNumber)

def startDumpServer(dumpPort):
    stdoutfile = join(integrationTempdir, "stdouterr-dump.log")
    stdouterrlog = open(stdoutfile, 'w')
    processInfo = Popen(
        args=[join(integrationTempdir, "dumpserver.py"), str(dumpPort), dumpDir], 
        cwd=integrationTempdir, 
        stdout=stdouterrlog,
        stderr=stdouterrlog)
    print "DumpServer PID", processInfo.pid
    sleep(4)
    return processInfo

def startHarvester():
    stdoutfile = join(integrationTempdir, "stdouterr-harvester.log")
    stdouterrlog = open(stdoutfile, 'w')
    processInfo = Popen(
        args=[join(integrationTempdir, "start-integrationtest-harvester.py"), "-d", "ignored", "--logDir=%s" % join(integrationTempdir, "log"), "--stateDir=%s" % join(integrationTempdir, "state")], 
        cwd=integrationTempdir,
        stdout=stdouterrlog,
        stderr=stdouterrlog)
    print "Harvester PID", processInfo.pid
    sleep(4)
    return processInfo

def stopProcess(processInfo):
    print "Stopping process", processInfo.pid
    kill(processInfo.pid, SIGTERM)
    sleep(1)
    kill(processInfo.pid, SIGKILL)
    sleep(1)
    waitpid(processInfo.pid, WNOHANG)

if __name__ == '__main__':
    system('rm -rf ' + integrationTempdir)
    dumpPortNumber = randint(50000,60000)

    initData(integrationTempdir, dumpPortNumber)
    
    dumpServerProcessInfo = startDumpServer(dumpPortNumber)
    harvesterProcessInfo = startHarvester()
    try:
        main()
    finally:
        stopProcess(dumpServerProcessInfo)
        stopProcess(harvesterProcessInfo)

