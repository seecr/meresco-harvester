#!/usr/bin/env python2.5
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

from meresco.core import Observable, be
from os.path import join, abspath, dirname
from sys import stdout

import time
from weightless.io import Reactor
from dynamichtml import DynamicHtml

from meresco.components import readConfig
from meresco.components.http import ApacheLogger, PathFilter, ObservableHttpServer, StringServer, FileServer
from meresco.components.http.utils import ContentTypePlainText
from __version__ import VERSION_STRING

from saharaget import SaharaGet
from status import Status
from harvesterdata import HarvesterData

myPath = dirname(abspath(__file__))
dynamicHtmlPath = join(myPath, 'controlpanel', 'html', 'dynamic')
staticHtmlPath = join(myPath, 'controlpanel', 'html')

def dna(reactor, observableHttpServer, saharaUrl, dataPath, logPath, statePath):
    return \
        (Observable(),
            (observableHttpServer,
                (ApacheLogger(stdout),
                    (PathFilter("/info/version"),
                        (StringServer(VERSION_STRING, ContentTypePlainText), )
                    ),
                    (PathFilter("/static"),
                        (FileServer(staticHtmlPath),)
                    ),
                    (PathFilter('/', excluding=['/info/version', '/static']),
                        (DynamicHtml(
                            [dynamicHtmlPath],
                            reactor=reactor,
                            additionalGlobals = {'time': time},
                            indexPage="/index.html",
                            ),
                            (SaharaGet(saharaurl=saharaUrl),),
                            (Status(logPath, statePath),
                                (HarvesterData(dataPath),)    
                            )
                        )
                    )
                )
            )
        )

def startServer(configFile):
    config = readConfig(configFile)

    portNumber = int(config['portNumber'])
    saharaUrl = config['saharaUrl']
    dataPath = config['dataPath']
    logPath = config['logPath']
    statePath = config['statePath']

    reactor = Reactor()
    observableHttpServer = ObservableHttpServer(reactor, portNumber)

    server = be(dna(reactor, observableHttpServer, saharaUrl, dataPath, logPath, statePath))
    server.once.observer_init()

    print "Ready to rumble at", portNumber
    stdout.flush()
    reactor.loop()
