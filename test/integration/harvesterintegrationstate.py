# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2011, 2013, 2015, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011, 2015, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from os.path import join, abspath, dirname, isfile
from os import listdir

from seecr.test.utils import getRequest
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.parse import urlparse, parse_qs
from shutil import copytree

from seecr.test.integrationtestcase import IntegrationState
from seecr.test.portnumbergenerator import PortNumberGenerator
from seecr.test.udplistenandlog import UdpListenAndLog

mydir = dirname(abspath(__file__))
projectDir = dirname(dirname(mydir))
examplesPath = join(dirname(dirname(mydir)), 'examples')

class HarvesterIntegrationState(IntegrationState):
    def __init__(self, stateName, tests=None, fastMode=False):
        IntegrationState.__init__(self, "harvester-"+stateName, tests=tests, fastMode=fastMode)
        self.helperServerPortNumber = PortNumberGenerator.next()
        self.harvesterInternalServerPortNumber = PortNumberGenerator.next()
        self.gustosPort = PortNumberGenerator.next()

        self.helperDir = join(self.integrationTempdir, 'helper')
        self.dumpDir = join(self.helperDir, 'dump')
        self.harvesterLogDir = join(self.integrationTempdir, "log")
        self.harvesterStateDir = join(self.integrationTempdir, "state")

        copytree(join("integration-data", "data"), join(self.integrationTempdir, 'data'))
        for f in listdir(join(self.integrationTempdir, "data")):
            filepath = join(self.integrationTempdir, "data", f)
            if isfile(filepath):
                fileSubstVars(filepath, helperServerPortNumber=self.helperServerPortNumber, integrationTempdir=self.integrationTempdir)

    def binDir(self):
        return join(projectDir, 'bin')

    def setUp(self):
        self.startGustosUdpListener()
        self.startHelperServer()
        self.startHarvesterInternalServer()

    def controlHelper(self, action, **kwargs):
        args = {'action':action}
        args.update(kwargs)
        urlopen("http://localhost:%s/control?%s" % (self.helperServerPortNumber, urlencode(args,doseq=True)))

    def startHarvester(self, repository=None, concurrency=None, runOnce=True, sleepTime=0, verbose=False, timeoutInSeconds=6, **kwargs):
        arguments = dict(domain='adomain', logDir=self.harvesterLogDir, stateDir=self.harvesterStateDir, url="http://localhost:{}".format(self.harvesterInternalServerPortNumber), sleepTime=sleepTime, gustosId="harvester", gustosHost="localhost", gustosPort=self.gustosPort)
        arguments.update(kwargs)
        if repository is not None:
            arguments['repository'] = repository
        if concurrency is not None:
            arguments['concurrency'] = concurrency
        return self._runExecutable(
                self.binPath('meresco-harvester'),
                processName='harvester',
                flagOptions=['runOnce'] if runOnce else [],
                timeoutInSeconds=timeoutInSeconds,
                **arguments
            )

    def startHelperServer(self):
        self._startServer(
            serviceName='TestHelper',
            executable=join(mydir, 'helperserver.py'),
            serviceReadyUrl='http://localhost:%s/ready' % self.helperServerPortNumber,
            port=self.helperServerPortNumber,
            directory=self.helperDir
        )

    def startGustosUdpListener(self):
        self.gustosUdpListener = UdpListenAndLog(self.gustosPort)

    def startHarvesterInternalServer(self):
        self._startServer(
            serviceName='Harvester-Internal-Server',
            executable=self.binPath('meresco-harvester-server'),
            serviceReadyUrl='http://localhost:%s/info/version' % self.harvesterInternalServerPortNumber,
            port=self.harvesterInternalServerPortNumber,
            dataPath=join(self.integrationTempdir, 'data'),
            logPath=self.harvesterLogDir,
            statePath=self.harvesterStateDir,
            externalUrl="http://localhost:9999"
        )

    def getLogs(self):
        header, result = getRequest(self.helperServerPortNumber, '/log', {}, parse=False)
        return list(self._getLogs(str(result, encoding='utf-8')))

    @staticmethod
    def _getLogs(result):
        for line in (l for l in result.split('\n') if l.strip()):
            p = urlparse(line)
            yield dict(path=p.path, arguments=parse_qs(p.query))

def fileSubstVars(filepath, **kwargs):
    contents = open(filepath).read()
    for k, v in list(kwargs.items()):
        contents = contents.replace("${%s}" % k, str(v))
    open(filepath, "w").write(contents)
