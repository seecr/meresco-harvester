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
from __future__ import with_statement

from test.mocksaharaget import MockSaharaGet

from glob import glob
from sys import path, argv, exit

from weightless.io import Reactor
from sys import stdout
from os.path import abspath, dirname, join, isdir, basename
from os import makedirs
from meresco.components.http import ObservableHttpServer, PathFilter, FileServer, StringServer
from meresco.components.http.utils import ContentTypePlainText, okPlainText
from meresco.components.sru.srurecordupdate import RESPONSE_XML, DIAGNOSTIC_XML, escapeXml, bind_string
from meresco.core import Observable, be
from re import compile
from traceback import format_exc

mydir = dirname(abspath(__file__))
notWordCharRE = compile('\W+')

class InvalidDataException(Exception):
    pass

class Dump(object):
    def __init__(self, dumpdir):
        self._dumpdir = dumpdir
        self._number = self._findLastNumber()

    def handleRequest(self, Body='', **kwargs):
        yield '\r\n'.join(['HTTP/1.0 200 Ok', 'Content-Type: text/xml, charset=utf-8\r\n', ''])
        try:
            updateRequest = bind_string(Body).updateRequest
            print self._ignoreAll, str(updateRequest.action)
            if self._ignoreAll and str(updateRequest.action) == "info:srw/action/1/replace":
                raise InvalidDataException('Data not valid.')
            recordId = str(updateRequest.recordIdentifier)
            normalizedRecordId = notWordCharRE.sub('_', recordId)
            self._number +=1
            filename = '%05d_%s.updateRequest' %(self._number, normalizedRecordId)
            with open(join(self._dumpdir, filename), 'w') as f:
                print recordId
                stdout.flush()
                updateRequest.xml(f)
            answer = RESPONSE_XML % {
                "operationStatus": "success",
                "diagnostics": ""}
        except InvalidDataException, e:
            answer = RESPONSE_XML % {
                "operationStatus": "fail",
                "diagnostics": DIAGNOSTIC_XML % {
                    'uri': 'info:srw/diagnostic/12/12',
                    'details': escapeXml(str(e)),
                    'message': 'Invalid data:  record rejected'}}
        except Exception, e:
            answer = RESPONSE_XML % {
                "operationStatus": "fail",
                "diagnostics": DIAGNOSTIC_XML % {
                    'uri': 'info:srw/diagnostic/12/1', 
                    'details': escapeXml(format_exc()), 
                    'message': 'Invalid component:  record rejected'}}
        print answer
        import sys
        sys.stdout.flush()
        yield answer

    def _findLastNumber(self):
        return max([int(basename(f)[:5]) for f in glob(join(self._dumpdir, '*.updateRequest'))]+[0])

    def reset(self):
        self._ignoreAll = False

    def ignoreAll(self):
        self._ignoreAll = True

ALL_TESTNAMES = [
        "integration.harvestertest.HarvesterTest.testHarvestToDump",
        "integration.harvestertest.HarvesterTest.testInvalidIgnoredUptoMaxIgnore",
        "integration.internalservertest.InternalServerTest.testGetStatus",
        "integration.internalservertest.InternalServerTest.testListAllRepositories",
        "integration.internalservertest.InternalServerTest.testViewIgnoredRecord",
]
class StartTest(Observable):
    def handleRequest(self, arguments, **kwargs):
        name = arguments.get('name', [None])[0]
        yield okPlainText
        if name not in ALL_TESTNAMES:
            yield 'ERROR: name "%s" not found' % name
            return
        self.any.reset()
        if name in [
                "integration.harvestertest.HarvesterTest.testInvalidIgnoredUptoMaxIgnore",
                "integration.internalservertest.InternalServerTest.testGetStatus",
                "integration.internalservertest.InternalServerTest.testListAllRepositories",
                "integration.internalservertest.InternalServerTest.testViewIgnoredRecord",
            ]:
            self.any.ignoreAll()
        yield "Ready to start"

def main(reactor, portNumber, dumpdir):
    isdir(dumpdir) or makedirs(dumpdir)
    dump = Dump(dumpdir)
    server = be(
        (Observable(),
            (ObservableHttpServer(reactor, portNumber),
                (PathFilter("/dump"),
                    (dump,)
                ),
                (PathFilter("/starttest"),
                    (StartTest(),
                        (dump,)
                    )
                ),
                (PathFilter("/files"),
                    (FileServer(mydir),)
                ),
                (PathFilter("/saharaget"),
                    (MockSaharaGet(),)
                ),
                (PathFilter("/ready"),
                    (StringServer('yes', ContentTypePlainText),)
                )
            )
        )
    )
    server.once.observer_init()

if __name__== '__main__':
    args = argv[1:]
    if len(args) != 2:
        print "Usage %s <portnumber> <dumpdir>" % argv[0]
        exit(1)
    portNumber = int(args[0])
    dumpdir = args[1]
    reactor = Reactor()
    main(reactor, portNumber, dumpdir)
    print 'Ready to rumble the dumpserver at', portNumber
    print '  - dumps are written to', dumpdir
    stdout.flush()
    reactor.loop()
