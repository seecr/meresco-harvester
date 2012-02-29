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
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
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

from eventlogger import EventLogger, NilEventLogger, CompositeLogger, StreamEventLogger
from harvester import Harvester
from saharaget import SaharaGet
from time import sleep
import traceback
from timedprocess import TimedProcess
from urllib import urlopen
from os.path import join
from select import select, error
from sys import stderr, stdout, exit, argv
from optparse import OptionParser
from os import read
from signal import SIGINT

AGAIN_EXITCODE = 42

class StartHarvester(object):
    def __init__(self):
        if len(argv[1:]) == 0:
            argv.append('-h')
        self.parser = OptionParser()
        args = self.parse_args()
        self.__dict__.update(args.__dict__)

        if not self.domainId:
            self.parser.error("Specify domain")
        if self._concurrency < 1:
            self.parser.error("Concurrency must be at least 1.")

        if self._logDir == None:
            self._logDir = urlopen(self.saharaurl + '/_getoptions/logDir').read()
        if self._stateDir == None:
            self._stateDir = urlopen(self.saharaurl + '/_getoptions/stateDir').read()

        self.saharaget = SaharaGet(self.saharaurl, self.setActionDone)

        self.repository = self.repositoryId and self.saharaget.getRepository(self.domainId, self.repositoryId)


    def parse_args(self):
        self.parser.add_option("-d", "--domain",
            dest="domainId",
            help="Mandatory argument denoting the domain.", 
            metavar="DOMAIN")
        self.parser.add_option("-s", "--saharaurl", 
            dest="saharaurl",
            help="The url of the SAHARA web interface, e.g. https://username:password@sahara.example.org", 
            default="http://localhost")
        self.parser.add_option("-r", "--repository", 
            dest="repositoryId",
            help="Process a single repository within the given domain. Defaults to all repositories from the domain.", 
            metavar="REPOSITORY")
        self.parser.add_option("-t", "--set-process-timeout", 
            dest="processTimeout",
            type="int", 
            default=60*60, 
            metavar="TIMEOUT",
            help="Subprocess will be timed out after amount of seconds.")
        self.parser.add_option("--logDir", "", 
            dest="_logDir",
            help="Override the logDir in the apache configuration.",
            metavar="DIRECTORY", 
            default=None)
        self.parser.add_option("--stateDir", 
            dest="_stateDir",
            help="Override the stateDir in the apache configuration.", 
            metavar="DIRECTORY", 
            default=None)
        self.parser.add_option("--concurrency", 
            dest="_concurrency",
            type="int",
            default=1,
            help="Number of repositories to be concurrently harvested. Defaults to 1 (no concurrency).", 
            metavar="NUMBER")
        self.parser.add_option("--force-target", "", 
            dest="forceTarget",
            help="Overrides the repository's target", 
            metavar="TARGETID")
        self.parser.add_option("--force-mapping", "", 
            dest="forceMapping",
            help="Overrides the repository's mapping", 
            metavar="MAPPINGID")
        self.parser.add_option("--no-action-done", "", 
            action="store_false",
            dest="setActionDone", 
            default=True,
            help="Do not set SAHARA's actions", 
            metavar="TARGETID")
        self.parser.add_option("--runOnce", "", 
            dest="runOnce", 
            action="store_true",
            default=False,
            help="Prevent harvester from looping (if combined with --repository)")

        (options, args) = self.parser.parse_args()
        return options

    def start(self):
        self._childProcesses = []
        if not self.repository:
            self._restartWithLoop()
        elif not self.runOnce:
            self._startRepositoryWithChild()
        else:
            self._startRepository()

    def _restartWithLoop(self):
        for key in self.saharaget.getRepositoryIds(self.domainId):
            extraArgs = ['--repository='+key]
            extraArgs += ['--runOnce'] if self.runOnce else [] 
            self._childProcesses.append(self._createArgs(extraArgs))
        self._startChildProcesses()

    def _startRepositoryWithChild(self):
        self._childProcesses.append(self._createArgs(['--runOnce']))
        self._startChildProcesses()

    def _startChildProcesses(self):
        processes = {}
        try:
            for i in range(min(self._concurrency, len(self._childProcesses))):
                args = self._childProcesses.pop(0)
                t, process = self._createProcess(args)
                processes[process.stdout.fileno()] = t, process, args
                processes[process.stderr.fileno()] = t, process, args

            while processes:
                try:
                    readers, _, _ = select(processes.keys(), [], [])
                except error, (errno, description):
                    if errno == EBADF:
                        self._findAndRemoveBadFd()
                    elif errno == EINTR:
                        pass
                    else:
                        raise
                for reader in readers:
                    if reader not in processes:
                        continue

                    t, process, args = processes[reader]
                    pipeContent = read(reader, 4096)
                    if reader == process.stdout.fileno():
                        stdout.write(pipeContent)
                        stdout.flush()
                    else:
                        stderr.write(pipeContent)
                        stderr.flush()

                    if process.poll() is not None:
                        exitstatus = t.stopScript(process)
                        del processes[process.stdout.fileno()]
                        del processes[process.stderr.fileno()]
                        if exitstatus == AGAIN_EXITCODE:
                            self._childProcesses.insert(0, args)
                        elif not self.runOnce:
                            self._childProcesses.append(args)
                        if len(self._childProcesses) > 0:
                            t, process = self._createProcess(self._childProcesses.pop(0))
                            processes[process.stdout.fileno()] = t, process, args
                            processes[process.stderr.fileno()] = t, process, args
        except KeyboardInterrupt, e:
            for t in set([t for t,process,args in processes.values()]):
                t.terminate()
            raise

    def _createProcess(self, args):
        t = TimedProcess()
        return t, t.executeScript(args, self.processTimeout, SIGINT)

    def _createArgs(self, extraArgs):
        return argv[:1] + extraArgs + argv[1:]

    def _startRepository(self):
        if self.forceTarget:
            self.repository.targetId = self.forceTarget
        if self.forceMapping:
            self.repository.mappingId = self.forceMapping

        self._generalHarvestLog = CompositeLogger([
            (['*'], EventLogger(join(self._logDir, self.domainId, 'harvester.log'))),
            (['*'], StreamEventLogger(stdout)),
            (['ERROR', 'WARN'], StreamEventLogger(stderr)),
        ])

        messageIgnored, again = self.repository.do(
            stateDir=join(self._stateDir, self.domainId),
            logDir=join(self._logDir, self.domainId),
            generalHarvestLog=self._generalHarvestLog)
        sleep(1)
        if again:
            exit(AGAIN_EXITCODE)

