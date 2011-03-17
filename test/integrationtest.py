#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
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

import os, sys
os.system('find .. -name "*.pyc" | xargs rm -f')

from glob import glob
for path in glob('../deps.d/*'):
    sys.path.insert(0, path)

sys.path.insert(0, "..")

from os import system, kill, WNOHANG, waitpid
from os.path import isdir, isfile, join
from sys import exit, exc_info
from unittest import main
from random import randint
from time import time, sleep
from glob import glob
from lxml.etree import parse, tostring
from StringIO import StringIO
from amara.binderytools import bind_file, bind_string
from signal import SIGTERM, SIGKILL
from subprocess import Popen
from urllib import urlopen, urlencode

from cq2utils import CQ2TestCase 

integrationTempdir = '/tmp/mh-integration-test'
reactor = Reactor()

class IntegrationTest(CQ2TestCase):
    pass

def createDatabase(port):
    recordPacking = 'xml'
    start = time()
    print "Creating database in", integrationTempdir
    sourceFiles = glob('harvester_output/*.updateRequest')
    for updateRequestFile in sorted(sourceFiles):
        print 'Sending:', updateRequestFile
        header, body = postRequest(reactor, port, '/update', open(updateRequestFile).read())
        if '200 Ok' not in header:
            print 'No 200 Ok response, but:'
            print header
            print body.xml()
            exit(123)
        if "srw:diagnostics" in body.xml():
            print body.xml()
            exit(1234)
    print "Finished creating database in %s seconds" % (time() - start)

def startOwlimHttpServer(owlimHttpServerPort, owlimHttpServerPath, rdfStorePath):
    processInfo = Popen(["/usr/bin/start-owlimhttpserver", str(owlimHttpServerPort), owlimHttpServerPath, "triplestore", rdfStorePath])
    print "OwlimHttpServer PID", processInfo.pid
    sleep(4)
    return processInfo


def stopProcess(processInfo):
    print "Stopping process", processInfo.pid
    kill(processInfo.pid, SIGTERM)
    sleep(1)
    kill(processInfo.pid, SIGKILL)
    sleep(1)
    waitpid(processInfo.pid, WNOHANG)

if __name__ == '__main__':
    from sys import argv
    if not '--fast' in argv:
        system('rm -rf ' + integrationTempdir)
        system('mkdir --parents '+ integrationTempdir)

    portNumber = randint(50000,60000)
    config = {
    }

    owlimHttpServerProcessInfo = startOwlimHttpServer(config['owlim.portNumber'], config['databasePath'], join(integrationTempdir, config['rdf.store.path']))
    try:
        server.once.observer_init()

        if '--fast' in argv and isdir(integrationTempdir):
            argv.remove('--fast')
            print "Reusing database in", integrationTempdir
        else:
            createDatabase()
            from merescoharvester.harvester.startharvester import StartHarvester
            StartHarvester().start()
        main()
    finally:
        stopProcess(owlimHttpServerProcessInfo)

