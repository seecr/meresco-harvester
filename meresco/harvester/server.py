## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2011-2012, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2012, 2015 Stichting Kennisnet http://www.kennisnet.nl
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

from os.path import join, abspath, dirname
from sys import stdout
import time
from xml.sax.saxutils import escape as escapeXml
from lxml.etree import XML

from weightless.io import Reactor
from weightless.core import compose, be

from meresco.components.json import JsonDict
from meresco.core import Observable

from meresco.html import DynamicHtml
from seecr.weblib import seecrWebLibPath

from meresco.components import readConfig
from meresco.components.http import ApacheLogger, PathFilter, ObservableHttpServer, StringServer, FileServer, PathRename
from meresco.components.http.utils import ContentTypePlainText

from __version__ import VERSION_STRING
from repositorystatus import RepositoryStatus
from harvesterdata import HarvesterData
from harvesterdataactions import HarvesterDataActions
from harvesterdataretrieve import HarvesterDataRetrieve
from meresco.components.http.utils import ContentTypeJson

myPath = dirname(abspath(__file__))
dynamicHtmlPath = join(myPath, 'controlpanel', 'html', 'dynamic')

def dna(reactor, port, dataPath, logPath, statePath, harvesterStatusUrl, **ignored):
    harvesterData = HarvesterData(dataPath)
    repositoryStatus = be((RepositoryStatus(logPath, statePath),
            (harvesterData,)
        ))
    configDict = JsonDict(
            logPath=logPath,
            statePath=statePath,
            harvesterStatusUrl=harvesterStatusUrl,
            dataPath=dataPath,
        )

    return \
        (Observable(),
            (ObservableHttpServer(reactor, port),
                (ApacheLogger(stdout),
                    (PathFilter("/info/version"),
                        (StringServer(VERSION_STRING, ContentTypePlainText), )
                    ),
                    (PathFilter("/info/config"),
                        (StringServer(configDict.dumps(), ContentTypeJson), )
                    ),
                    (PathFilter("/static"),
                        (PathRename(lambda name: name[len('/static/'):]),
                            (FileServer(seecrWebLibPath),)
                        )
                    ),
                    (PathFilter('/', excluding=['/info/version', '/static', '/action', '/get']),
                        (DynamicHtml(
                            [dynamicHtmlPath],
                            reactor=reactor,
                            additionalGlobals = {
                                'time': time,
                                'harvesterStatusUrl': harvesterStatusUrl,
                                'escapeXml': escapeXml,
                                'compose': compose,
                                'XML': XML,
                            },
                            indexPage="/index.html",
                            ),
                            (harvesterData,),
                            (repositoryStatus,),
                        )
                    ),
                    (PathFilter('/action'),
                        (HarvesterDataActions(),
                            (harvesterData,)
                        ),
                    ),
                    (PathFilter('/get'),
                        (HarvesterDataRetrieve(),
                            (harvesterData,),
                            (repositoryStatus,),
                        )
                    )
                )
            )
        )

def startServer(configFile):
    config = readConfig(configFile)

    portNumber = int(config['portNumber'])

    reactor = Reactor()

    server = be(dna(reactor,
            port=portNumber,
            dataPath=config['dataPath'],
            logPath=config['logPath'],
            statePath=config['statePath'],
            harvesterStatusUrl=config['harvesterStatusUrl'],
        ))
    list(compose(server.once.observer_init()))

    print "Ready to rumble at", portNumber
    stdout.flush()
    reactor.loop()

