## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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

from harvesterlog import HarvesterLog
from eventlogger import EventLogger, NilEventLogger
from harvester import Harvester
from sseuploader import LoggingUploader
import sys, os, optparse
from saharaget import SaharaGet
from time import sleep
import traceback
from timedprocess import TimedProcess
from urllib import urlopen
from os.path import join


class StartHarvester:
    def __init__(self):
        if len(sys.argv[1:]) == 0:
                        sys.argv.append('-h')
        self.parser = optparse.OptionParser()
        args = self.parse_args()
        self.__dict__.update(args.__dict__)

        if not self.domainId:
            self.parser.error("Specify domain")

        if self._logDir == None:
            self._logDir = urlopen(self.saharaurl + '/_getoptions/logDir').read()
        if self._stateDir == None:
            self._stateDir = urlopen(self.saharaurl + '/_getoptions/stateDir').read()

        self.saharaget = SaharaGet(self.saharaurl, self.setActionDone)

        self.repository = self.repositoryId and self.saharaget.getRepository(self.domainId, self.repositoryId)

        if not self.repository:
            self.restartWithLoop(self.domainId, self.processTimeout)

        if self.forceTarget:
            self.repository.targetId = self.forceTarget
        if self.forceMapping:
            self.repository.mappingId = self.forceMapping

        self._generalHarvestLog = EventLogger(join(self._logDir, self.domainId, 'harvester.log'))

        if self.uploadLog:
            self.repository.mockUploader = LoggingUploader(EventLogger(self.uploadLog))

    def parse_args(self):
        self.parser.add_option("-d", "--domain", dest="domainId",
                        help="Mandatory argument denoting the domain.", metavar="DOMAIN")
        self.parser.add_option("-s", "--saharaurl", dest="saharaurl",
                        help="The url of the SAHARA web interface, e.g. https://username:password@sahara.example.org", default="http://localhost")
        self.parser.add_option("-r", "--repository", dest="repositoryId",
                        help="Process a single repository within the given domain. Defaults to all repositories from the domain.", metavar="REPOSITORY")
        self.parser.add_option("-t", "--set-process-timeout", dest="processTimeout",
                        type="int", default=60*60, metavar="TIMEOUT",
                        help="Subprocess will be timed out after amount of seconds.")
        self.parser.add_option("--logDir", "", dest="_logDir",
                        help="Override the logDir in the apache configuration.", metavar="DIRECTORY", default=None)
        self.parser.add_option("--stateDir", dest="_stateDir",
                        help="Override the stateDir in the apache configuration.", metavar="DIRECTORY", default=None)
        self.parser.add_option("--uploadLog", "", dest="uploadLog",
                        help="Set the mockUploadLogFile to which the fields are logged instead of uploading to a server.", metavar="FILE")
        self.parser.add_option("--force-target", "", dest="forceTarget",
                        help="Overrides the repository's target", metavar="TARGETID")
        self.parser.add_option("--force-mapping", "", dest="forceMapping",
                        help="Overrides the repository's mapping", metavar="MAPPINGID")
        self.parser.add_option("--no-action-done", "", action="store_false",
                        dest="setActionDone", default=True,
                        help="Do not set SAHARA's actions", metavar="TARGETID")

        (options, args) = self.parser.parse_args()
        return options

    def restartWithLoop(self, domainId, processTimeout=60*60):
        for key in self.saharaget.getRepositoryIds(domainId):
            args = sys.argv[:1] + ['--repository='+key] + sys.argv[1:]
            t = TimedProcess()
            try:
                SIG_INT = 2
                t.executeScript(args, processTimeout, SIG_INT)
            except KeyboardInterrupt, e:
                t.terminate()
                raise
        sys.exit()

    def start(self):
        again = True
        while again:
            messageIgnored, again = self.repository.do(
                stateDir=join(self._stateDir, self.domainId),
                logDir=join(self._logDir, self.domainId),
                generalHarvestLog=self._generalHarvestLog)
        sleep(1)

