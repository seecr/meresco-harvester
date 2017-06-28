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
# Copyright (C) 2011, 2015 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
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

from eventlogger import CompositeLogger, StreamEventLogger
from time import sleep
from timedprocess import TimedProcess
from urllib import urlopen
from os.path import join
from select import select, error
from sys import stderr, stdout, exit, argv
from optparse import OptionParser, SUPPRESS_HELP
from os import read
from signal import SIGTERM
from errno import EINTR, EAGAIN
from meresco.components.json import JsonDict
from meresco.harvester.internalserverproxy import InternalServerProxy

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

        config = JsonDict.load(urlopen(self.serverUrl + '/info/config'))
        if self._logDir is None:
            self._logDir = config['logPath']
        if self._stateDir is None:
            self._stateDir = config['statePath']

        self.proxy = InternalServerProxy(self.serverUrl, self.setActionDone)
        self.repository = self.repositoryId and self.proxy.getRepositoryObject(identifier=self.repositoryId, domainId=self.domainId)

    def parse_args(self):
        self.parser.add_option("-d", "--domain",
            dest="domainId",
            help="Mandatory argument denoting the domain.",
            metavar="DOMAIN")
        self.parser.add_option("-u", "--url",
            dest="serverUrl",
            help="The url of the Meresco Harvester Server",
            default="http://localhost:8888")
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
        self.parser.add_option("--child", "",
            action="store_true",
            dest="child",
            default=False,
            help=SUPPRESS_HELP)
        self.parser.add_option("--sleepTime", "",
            dest="sleepTime",
            type='int',
            default=1,
            help=SUPPRESS_HELP)

        (options, args) = self.parser.parse_args()
        for opt in ['serverUrl']:
            if not getattr(options, opt, None):
                raise ValueError('Missing option: %s' % repr(opt))
        return options

    def start(self):
        if self.child:
            self._startRepository()
        else:
            self._startChildProcesses()

    def _startChildProcesses(self):
        running = set()
        if self.repository:
            waiting = [self.repositoryId]
        else:
            waiting = self.proxy.getRepositoryIds(self.domainId)
        processes = {}
        try:
            while running or waiting:
                while waiting and (len(running) < self._concurrency):
                    repositoryId = waiting.pop(0)
                    self._createProcess(processes, repositoryId)
                    running.add(repositoryId)
                try:
                    readers, _, _ = select(processes.keys(), [], [])
                except error, (errno, description):
                    if errno == EINTR:
                        pass
                    else:
                        raise
                for reader in readers:
                    if reader not in processes:
                        continue

                    t, process, repositoryId = processes[reader]
                    try:
                        pipeContent = read(reader, 4096)
                    except OSError, e:
                        if e.errno == EAGAIN:
                            continue
                        raise
                    if reader == process.stdout.fileno():
                        stdout.write(pipeContent)
                        stdout.flush()
                    else:
                        stderr.write(pipeContent)
                        stderr.flush()

                    if process.poll() is not None:
                        exitstatus = t.stopScript(process)
                        running.remove(repositoryId)
                        del processes[process.stdout.fileno()]
                        del processes[process.stderr.fileno()]
                        if exitstatus == AGAIN_EXITCODE:
                            waiting.insert(0, repositoryId)
                        else:
                            if exitstatus != 0:
                                stderr.write("Process (for repository %s) exited with exitstatus %s.\n" % (repositoryId, exitstatus))
                                stderr.flush()
                            if not self.runOnce:
                                waiting.append(repositoryId)
                        self._updateWaiting(waiting, running)

        except:
            for t in set([t for t,process,repositoryId in processes.values()]):
                t.terminate()
            raise

    def _createProcess(self, processes, repositoryId):
        t = TimedProcess(signal=SIGTERM)
        process = t.executeScript(self._createArgs(repositoryId), self.processTimeout)
        processes[process.stdout.fileno()] = t, process, repositoryId
        processes[process.stderr.fileno()] = t, process, repositoryId

    def _createArgs(self, repositoryId):
        args = argv + ["--child"]
        extraArg = '--repository=%s' % repositoryId
        if not extraArg in argv:
            args += [extraArg]
        return args

    def _updateWaiting(self, waiting, running):
        if self.runOnce or self.repository:
            return
        repositoryIds = self.proxy.getRepositoryIds(self.domainId)
        for repoId in waiting[:]:
            if not repoId in repositoryIds:
                waiting.remove(repoId)
        for repoId in repositoryIds:
            if not repoId in waiting and not repoId in running:
                waiting.append(repoId)

    def _startRepository(self):
        if self.forceTarget:
            self.repository.targetId = self.forceTarget
        if self.forceMapping:
            self.repository.mappingId = self.forceMapping

        self._generalHarvestLog = CompositeLogger([
            (['*'], StreamEventLogger(stdout)),
            (['ERROR', 'WARN'], StreamEventLogger(stderr)),
        ])

        messageIgnored, again = self.repository.do(
            stateDir=join(self._stateDir, self.domainId),
            logDir=join(self._logDir, self.domainId),
            generalHarvestLog=self._generalHarvestLog)
        sleep(self.sleepTime)
        if again:
            exit(AGAIN_EXITCODE)

