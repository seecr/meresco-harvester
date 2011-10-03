# -*- coding: utf-8 -*-
## begin license ##
# 
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for 
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl 
# 
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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

from __future__ import with_statement

from os.path import isdir, join, abspath, dirname, basename
from os import system, listdir, makedirs
from sys import stdout

from utils import postRequest, getRequest

from cq2utils import CQ2TestCase
from random import randint
from time import sleep, time 

from subprocess import Popen
from signal import SIGTERM
from os import waitpid, kill, WNOHANG
from urllib import urlopen, urlencode
from urlparse import urlparse
from cgi import parse_qs
from shutil import copytree

from meresco.components import readConfig

from traceback import print_exc

mypath = dirname(abspath(__file__))
binDir = join(dirname(dirname(mypath)), 'bin')
examplesPath = join(dirname(dirname(mypath)), 'examples')
harvesterDir = dirname(dirname(mypath))

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
        self.controlHelper(action='reset')

    def controlHelper(self, action, **kwargs):
        args = {'action':action}
        args.update(kwargs)
        urlopen("http://localhost:%s/control?%s" % (self.helperServerPortNumber, urlencode(args,doseq=True)))

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        return getattr(self.state, name)

    def startHarvester(self, repository=None, verbose=False):
        stdoutfile = join(self.integrationTempdir, "stdouterr-harvester.log")
        stdouterrlog = open(stdoutfile, 'w')
        if verbose:
            stdouterrlog = stdout
        additionalArgs = ['--repository=%s'%repository] if repository else []
        harvesterProcessInfo = Popen(
            args=[join(binDir, "meresco-harvester"), "-d", "adomain", "--logDir=%s" % self.harvesterLogDir, "--stateDir=%s" % self.harvesterStateDir, "--saharaurl=http://localhost:%s" % self.helperServerPortNumber] + additionalArgs, 
            cwd=binDir,
            env={'PYTHONPATH': harvesterDir, 'LANG': 'en_US.UTF-8'},
            stdout=stdouterrlog,
            stderr=stdouterrlog)
        waitpid(harvesterProcessInfo.pid, 0)
        stdouterrlog.flush()

class IntegrationState(object):
    def __init__(self, stateName, fastMode):
        self.stateName = stateName
        self._pids = []
        self.integrationTempdir = '/tmp/mh-integrationtest-%s' % stateName 
        system('rm -rf ' + self.integrationTempdir)

        self.helperServerPortNumber = PortNumberGenerator.next()
        self.harvesterInternalServerPortNumber = PortNumberGenerator.next()

        self.helperDir = join(self.integrationTempdir, 'helper')
        self.dumpDir = join(self.helperDir, 'dump')
        self.harvesterLogDir = join(self.integrationTempdir, "log")
        self.harvesterStateDir = join(self.integrationTempdir, "state")

        copytree("integration-data", self.integrationTempdir)
        fileSubstVars(join(self.integrationTempdir, "data", "SRUUPDATE.target"), helperServerPortNumber=self.helperServerPortNumber)
        fileSubstVars(join(self.integrationTempdir, "data", "FILESYSTEM.target"), integrationTempdir=self.integrationTempdir)
        fileSubstVars(join(self.integrationTempdir, "data", "adomain.integrationtest.repository"), helperServerPortNumber=self.helperServerPortNumber)
        config = readConfig(join(examplesPath, 'harvester.config'))
        
        # test example config has neccessary parameters
        def setConfig(config, parameter, value):
            assert config[parameter]
            config[parameter] = value
        setConfig(config, 'portNumber', self.harvesterInternalServerPortNumber)
        setConfig(config, 'saharaUrl', "http://localhost:%s" % self.helperServerPortNumber)
        setConfig(config, 'dataPath', join(self.integrationTempdir, 'data'))
        setConfig(config, 'statePath', self.harvesterStateDir)
        setConfig(config, 'logPath', self.harvesterLogDir)

        self._writeConfig(config, 'harvester')

        self.startHelperServer()
        self.startHarvesterInternalServer()

    def _writeConfig(self, config, name):
        configFile = join(self.integrationTempdir, '%s.config' % name)
        with open(configFile, 'w') as f:
            for item in config.items():
                f.write('%s = %s\n' % item)

    def startHelperServer(self):
        stdoutfile = join(self.integrationTempdir, "stdouterr-helper.log")
        stdouterrlog = open(stdoutfile, 'w')
        processInfo = Popen(
            args=["python", join(mypath, "helperserver.py"), str(self.helperServerPortNumber), self.helperDir], 
            env={'PYTHONPATH': harvesterDir, 'LANG': 'en_US.UTF-8'},
            cwd=self.integrationTempdir, 
            stdout=stdouterrlog,
            stderr=stdouterrlog)
        print "Helper Server PID", processInfo.pid
        self._pids.append(processInfo.pid)
        self._check(serverProcess=processInfo, 
                serviceName='TestHelper', 
                serviceReadyUrl='http://localhost:%s/ready' % self.helperServerPortNumber, 
                stdoutfile=stdoutfile)

    def startHarvesterInternalServer(self):
        stdoutfile = join(self.integrationTempdir, "stdouterr-harvesterinternalserver.log")
        stdouterrlog = open(stdoutfile, 'w')
        configFile = join(self.integrationTempdir, 'harvester.config') 
        processInfo = Popen(
            args=[join(binDir, "meresco-harvester-internal-server"), configFile], 
            env={'PYTHONPATH': harvesterDir, 'LANG': 'en_US.UTF-8'},
            cwd=binDir,
            stdout=stdouterrlog,
            stderr=stdouterrlog)
        print "Harvester Internal Server PID", processInfo.pid
        self._pids.append(processInfo.pid)
        self._check(serverProcess=processInfo, 
                serviceName='Harvester-Internal-Server', 
                serviceReadyUrl='http://localhost:%s/info/version' % self.harvesterInternalServerPortNumber, 
                stdoutfile=stdoutfile)

    def getLogs(self):
        header, result = getRequest(self.helperServerPortNumber, '/log', {}, parse=False)
        return list(self._getLogs(result))

    @staticmethod
    def _getLogs(result):
        for line in (l for l in result.split('\n') if l.strip()):
            p = urlparse(line)
            yield dict(path=p.path, arguments=parse_qs(p.query))


    def _check(self, serverProcess, serviceName, serviceReadyUrl, stdoutfile):
        stdoutWrite("Starting service '%s', for state '%s' : v" % (serviceName, self.stateName))
        done = False
        while not done:
            try:
                stdoutWrite('r')
                sleep(0.1)
                urlopen(serviceReadyUrl).read()
                done = True
            except IOError:
                if serverProcess.poll() != None:
                    self._pids.remove(serverProcess.pid)
                    exit('Service "%s" died, check "%s"' % (serviceName, stdoutfile))
        stdoutWrite('oom!\n')

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
