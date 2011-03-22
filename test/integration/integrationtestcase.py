# -*- coding: utf-8 -*-
## begin license ##
#
#    "HBO-Kennisbank" is a webportal that provides free access to student theses,
#    publications and learning objects made available by the Universities of
#    Applied Sciences in the Netherlands.
#    Copyright (C) 2007-2011 SURFfoundation. http://www.surf.nl
#    Copyright (C) 2007-2011 Seek You Too B.V. (CQ2) http://www.cq2.nl
#
#    This file is part of "HBO-Kennisbank"
#
#    "HBO-Kennisbank" is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    "HBO-Kennisbank" is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with "HBO-Kennisbank"; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from __future__ import with_statement

from os.path import isdir, join, abspath, dirname, basename
from os import system, listdir, makedirs
from sys import stdout

from utils import postRequest

from cq2utils import CQ2TestCase
from random import randint
from time import sleep, time 

from subprocess import Popen
from signal import SIGTERM
from os import waitpid, kill, WNOHANG
from urllib import urlopen, urlencode
from shutil import copytree

from meresco.components import readConfig

from traceback import print_exc

mypath = dirname(abspath(__file__))
binDir = join(dirname(dirname(mypath)), 'bin')
documentationPath = join(dirname(dirname(mypath)), 'doc')

if not isdir(binDir):
    binDir = '/usr/bin'

def stdoutWrite(aString):
    stdout.write(aString)
    stdout.flush()

class PortNumberGenerator(object):
    startNumber = randint(50000, 60000)

    @classmethod
    def next(cls):
        cls.startNumber += 1
        return cls.startNumber

class IntegrationTestCase(CQ2TestCase):
    def setUp(self):
        CQ2TestCase.setUp(self)
        global state
        self.state = state

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        return getattr(self.state, name)


class IntegrationState(object):
    def __init__(self, stateName, fastMode):
        self.stateName = stateName
        self._pids = []
        self.integrationTempdir = '/tmp/mh-integrationtest-%s' % stateName 
        system('rm -rf ' + self.integrationTempdir)

        self.dumpPortNumber = PortNumberGenerator.next()
        self.oaiPortNumber = PortNumberGenerator.next()
        self.harvesterPortalPortNumber = PortNumberGenerator.next()

        self.dumpDir = join(self.integrationTempdir, 'dump')
        self.harvesterLogDir = join(self.integrationTempdir, "log")
        self.harvesterStateDir = join(self.integrationTempdir, "state")

        self.initialize()
        config = readConfig(join(documentationPath, 'harvester.config'))
        
        # test example config has neccessary parameters
        def setConfig(config, parameter, value):
            assert config[parameter]
            config[parameter] = value
        setConfig(config, 'portNumber', self.harvesterPortalPortNumber)
        setConfig(config, 'saharaUrl', "http://localhost:%s" % self.harvesterPortalPortNumber)

        self._writeConfig(config, 'harvester')

    def _writeConfig(self, config, name):
        configFile = join(self.integrationTempdir, '%s.config' % name)
        with open(configFile, 'w') as f:
            for item in config.items():
                f.write('%s = %s\n' % item)

    def initialize(self):
        copytree("integration-data", self.integrationTempdir)
        fileSubstVars(join(self.integrationTempdir, "data", "DUMP.target"), dumpPortNumber=self.dumpPortNumber)
        fileSubstVars(join(self.integrationTempdir, "data", "integration.test.repository"), oaiPortNumber=self.oaiPortNumber)

        self.startDumpServer()
        self.startOaiFileServer()

        sleep(3)

    def startDumpServer(self):
        stdoutfile = join(self.integrationTempdir, "stdouterr-dump.log")
        stdouterrlog = open(stdoutfile, 'w')
        processInfo = Popen(
            args=[join(self.integrationTempdir, "dumpserver.py"), str(self.dumpPortNumber), self.dumpDir], 
            cwd=self.integrationTempdir, 
            stdout=stdouterrlog,
            stderr=stdouterrlog)
        print "DumpServer PID", processInfo.pid
        self._pids.append(processInfo.pid)

    def startOaiFileServer(self):
        stdoutfile = join(self.integrationTempdir, "stdouterr-oaifileserver.log")
        stdouterrlog = open(stdoutfile, 'w')
        processInfo = Popen(
            args=[join(self.integrationTempdir, "oaifileserver.py"), str(self.oaiPortNumber)], 
            cwd=self.integrationTempdir,
            stdout=stdouterrlog,
            stderr=stdouterrlog)
        print "Oai Fileserver PID", processInfo.pid
        self._pids.append(processInfo.pid)

    def startHarvesterPortal(self, portNumber):
        stdoutfile = join(self.integrationTempdir, "stdouterr-harvesterportal.log")
        stdouterrlog = open(stdoutfile, 'w')
        configFile = join(self.integrationTempdir, 'harvester.config') 
        open(configFile, 'w').write("portNumber=%s\r\nsaharaUrl=http://localhost:%s" % (portNumber, harvesterPortalPortNumber))
        processInfo = Popen(
            args=[join(binDir, "harvester-portal"), configFile], 
            cwd=binDir,
            stdout=stdouterrlog,
            stderr=stdouterrlog)
        print "Harvester Portal PID", processInfo.pid
        self._pids.append(processInfo.pid)

    def tearDown(self):
        for pid in self._pids:
            kill(pid, SIGTERM)
            waitpid(pid, WNOHANG)

def globalSetUp(fast, stateName):
    global state, fastMode
    fastMode = fast
    state = IntegrationState(stateName, fastMode)

def globalTearDown():
    global state
    state.tearDown()

def fileSubstVars(filepath, **kwargs):
    contents = open(filepath).read()
    for k, v in kwargs.items():
        contents = contents.replace("${%s}" % k, str(v))
    open(filepath, "w").write(contents)
