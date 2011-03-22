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

from weightless.io import Reactor
from dynamichtml import DynamicHtml

from meresco.components import readConfig
from meresco.components.http import ApacheLogger, PathFilter, ObservableHttpServer

from harvester.harvesterlog import HarvesterLog
from harvester.saharaget import SaharaGet

myPath = dirname(abspath(__file__))
dynamicHtmlPath = join(myPath, 'controlpanel', 'html')

def dna(reactor, observableHttpServer, config, saharaUrl):
    return \
        (Observable(),
            (observableHttpServer,
                (ApacheLogger(stdout),
                    (PathFilter('/'),
                        (DynamicHtml(
                            [dynamicHtmlPath],
                            reactor=reactor,
                            additionalGlobals = {},
                            indexPage="/index.html",
                            ),
                            (SaharaGet(saharaurl=saharaUrl),)
                        )
                    )
                )
            )
        )

def startServer(configFile):
    config = readConfig(configFile)

    portNumber = int(config['portNumber'])
    saharaUrl = config['saharaUrl']

    reactor = Reactor()
    observableHttpServer = ObservableHttpServer(reactor, portNumber)

    server = be(dna(reactor, observableHttpServer, config, saharaUrl))
    server.once.observer_init()

    print "Ready to rumble at", portNumber
    stdout.flush()
    reactor.loop()
