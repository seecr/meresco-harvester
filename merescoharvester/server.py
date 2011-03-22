#!/usr/bin/env python2.5

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
