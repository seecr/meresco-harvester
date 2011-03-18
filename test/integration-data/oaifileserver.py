#!/usr/bin/env python2.5
## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009, 2011 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#    Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
#
#    This file is part of Meresco Components.
#
#    Meresco Components is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Components is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Components; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from glob import glob
from sys import path, argv, exit
for directory in glob('../deps.d/*'):
    path.insert(0, directory)
path.insert(0, '..')

from weightless.io import Reactor
from sys import stdout
from os.path import abspath, dirname
from meresco.components.http import ObservableHttpServer, FileServer
from meresco.core import Observable, be

mydir = dirname(abspath(__file__))

def main(reactor, portNumber):
    server = be(
        (Observable(),
            (ObservableHttpServer(reactor, portNumber),
                (FileServer(mydir),)
            )
        )
    )
    server.once.observer_init()

if __name__== '__main__':
    args = argv[1:]
    if len(args) != 1:
        print "Usage %s <portnumber>" % argv[0]
        exit(1)
    portNumber = int(args[0])
    reactor = Reactor()
    main(reactor, portNumber)
    print 'Ready to rumble the oai file-server at', portNumber
    stdout.flush()
    reactor.loop()
