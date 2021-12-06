#!/usr/bin/env python3
## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009, 2011 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011, 2015, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2013, 2015, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from seecrdeps import includeParentAndDeps       #DO_NOT_DISTRIBUTE
includeParentAndDeps(__file__, scanForDeps=True) #DO_NOT_DISTRIBUTE

try:
    from seecr_initvm import initvm; initvm('meresco_oai', 'meresco_sequentialstore')
except ImportError:
    from lucene import initVM; initVM()
    from meresco_oai import initVM; initVM()
    from meresco_sequentialstore import initVM; initVM()

from glob import glob
from sys import path
from os.path import abspath, dirname, join, isfile
from lxml.etree import XML

mydir = dirname(abspath(__file__))

baseDir = dirname(dirname(mydir))                   #DO_NOT_DISTRIBUTE
for p in glob(join(baseDir, 'deps.d') + '/*'):      #DO_NOT_DISTRIBUTE
    path.insert(0, p)                               #DO_NOT_DISTRIBUTE
path.insert(0, baseDir)                             #DO_NOT_DISTRIBUTE

from sys import stdout
from os.path import isdir, basename
from os import makedirs, remove
from re import compile
from traceback import format_exc
from xml.sax.saxutils import escape as escapeXml
from argparse import ArgumentParser

from weightless.io import Reactor
from weightless.core import compose, be

from meresco.components import lxmltostring
from meresco.components.http import ObservableHttpServer, PathFilter, StringServer
from meresco.components.http.utils import ContentTypePlainText, okPlainText
from meresco.components.sru.srurecordupdate import RESPONSE_XML, DIAGNOSTIC_XML
from meresco.oai import OaiPmh, OaiJazz
from meresco.core import Observable
from meresco.harvester.namespaces import xpathFirst
from meresco.sequentialstore import MultiSequentialStorage

mydir = dirname(abspath(__file__))
testdataDir = join(dirname(mydir), 'data', 'helper')

notWordCharRE = compile(r'\W+')

class InvalidDataException(Exception):
    pass

class Dump(object):
    def __init__(self, dumpdir):
        self._dumpdir = dumpdir
        self._number = self._findLastNumber()
        self._allInvalid = False
        self._raiseExceptionOnIds = set()

    def handleRequest(self, Body=b'', **kwargs):
        contentLength = kwargs['Headers'].get('Content-Length')
        if contentLength:
            Body = Body[:int(contentLength)]

        yield '\r\n'.join(['HTTP/1.0 200 Ok', 'Content-Type: text/xml; charset=utf-8\r\n', ''])
        try:
            updateRequest = XML(Body)
            recordId = xpathFirst(updateRequest, 'ucp:recordIdentifier/text()')
            action = xpathFirst(updateRequest, 'ucp:action/text()')
            if self._allInvalid and action == "info:srw/action/1/replace":
                if 'oai:record:02' in recordId:
                    raise InvalidDataException()
                raise InvalidDataException('Invalid data')
            if recordId in self._raiseExceptionOnIds:
                raise Exception("ERROR")
            self._number +=1
            filename = '%05d_%s.updateRequest' %(self._number, action.rsplit('/')[-1])
            with open(join(self._dumpdir, filename), 'w') as f:
                stdout.flush()
                f.write(lxmltostring(updateRequest, pretty_print=True))
            answer = RESPONSE_XML % {
                "operationStatus": "success",
                "diagnostics": ""}
        except InvalidDataException as e:
            answer = RESPONSE_XML % {
                "operationStatus": "fail",
                "diagnostics": DIAGNOSTIC_XML % {
                    'uri': 'info:srw/diagnostic/12/12',
                    'details': escapeXml(str(e)),
                    'message': 'Invalid data:  record rejected'}}
        except Exception as e:
            answer = RESPONSE_XML % {
                "operationStatus": "fail",
                "diagnostics": DIAGNOSTIC_XML % {
                    'uri': 'info:srw/diagnostic/12/1',
                    'details': escapeXml(format_exc()),
                    'message': 'Invalid component:  record rejected'}}
        import sys
        sys.stdout.flush()
        yield answer

    def _findLastNumber(self):
        return max([int(basename(f)[:5]) for f in glob(join(self._dumpdir, '*.updateRequest'))]+[0])

    def reset(self):
        self._allInvalid = False
        for f in glob(join(self._dumpdir, '*.updateRequest')):
            remove(f)
        self._number = 0
        self._raiseExceptionOnIds = set()

    def allInvalid(self):
        self._allInvalid = True

    def noneInvalid(self):
        self._allInvalid = False

    def raiseExceptionOnIds(self, ids):
        self._raiseExceptionOnIds = set(ids)

class BadOai(object):
    def handleRequest(self, path, arguments, **kwargs):
        fileargs = dict(case=path.split('/')[-1])
        for k in ['verb', 'resumptionToken', 'metadataPrefix', 'set', 'from']:
            fileargs[k] = arguments[k][0] if k in arguments else ''
        if fileargs['resumptionToken']:
            filename = '{case}-{verb}-{resumptionToken}.xml'.format(**fileargs)
        else:
            filename = '{case}-{verb}-{metadataPrefix}-{set}-{from}.xml'.format(**fileargs)
        filepath = join(testdataDir, filename)
        if isfile(filepath):
            yield 'HTTP/1.0 200 Ok\r\nContent-Type: text/xml; charset=utf-8\r\n\r\n'
            with open(filepath) as fp:
                yield fp.read()
        else:
            yield 'HTTP/1.0 400 Bad Request\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n'
            l = 'Error: file {} not found.'.format(repr(filepath))
            print(l)
            yield l


class Control(Observable):
    def handleRequest(self, arguments, **kwargs):
        action = arguments.get('action', [None])[0]
        yield okPlainText
        if action == "reset":
            self.do.reset()
        if action == "raiseExceptionOnIds":
            self.do.raiseExceptionOnIds(arguments.get('id',[]))
        if action == "noneInvalid":
            self.do.noneInvalid()
        if action == "allInvalid":
            self.do.allInvalid()
        yield "DONE"

logLines = []
class Log(Observable):
    def handleRequest(self, RequestURI, **kwargs):
        print("LOG HandleRequest", RequestURI)
        logLines.append(RequestURI)
        yield self.all.handleRequest(RequestURI=RequestURI, **kwargs)

    def reset(self):
        del logLines[:]

    def logs(self):
        return logLines

class RetrieveLog(Observable):
    def handleRequest(self, **kwargs):
        yield okPlainText
        yield '\n'.join(self.call.logs())


def main(reactor, port, directory):
    dumpdir = join(directory, 'dump')
    isdir(dumpdir) or makedirs(dumpdir)
    dump = Dump(dumpdir)
    oaiStorage = MultiSequentialStorage(join(directory, 'storage'))
    oaiJazz = OaiJazz(join(directory, 'oai'))
    server = be(
        (Observable(),
            (ObservableHttpServer(reactor, port),
                (PathFilter("/dump"),
                    (dump,)
                ),
                (PathFilter("/control"),
                    (Control(),
                        (dump,),
                        (Log(),),
                    )
                ),
                (PathFilter('/oai'),
                    (Log(),
                        (OaiPmh(repositoryName="Oai Test Server", adminEmail="admin@example.org", batchSize=10),
                            (oaiStorage,),
                            (oaiJazz,),
                        )
                    )
                ),
                (PathFilter('/badoai'),
                    (Log(),
                        (BadOai(), )
                    )
                ),
                (PathFilter("/log"),
                    (RetrieveLog(),
                        (Log(),)
                    )
                ),
                (PathFilter("/ready"),
                    (StringServer('yes', ContentTypePlainText),)
                )
            )
        )
    )
    list(compose(server.once.observer_init()))
    oaiJazz.updateMetadataFormat(prefix="oai_dc", schema="http://www.openarchives.org/OAI/2.0/oai_dc.xsd", namespace="http://www.openarchives.org/OAI/2.0/oai_dc/")
    for i in range(1,16):
        if i == 2:
            identifier = 'oai:record:02/&gkn'
        else:
            identifier = 'oai:record:%02d' % i
        oaiStorage.addData(identifier=identifier, name='oai_dc', data=bytes('''<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:dc="http://purl.org/dc/elements/1.1/" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"><dc:identifier>%s</dc:identifier><dc:title>Title is √</dc:title></oai_dc:dc>''' % escapeXml(identifier), encoding='utf-8'))
        oaiJazz.addOaiRecord(identifier=identifier, metadataPrefixes=['oai_dc'])
        if i in [3,6]:
            list(compose(oaiJazz.delete(identifier=identifier)))

if __name__== '__main__':
    parser = ArgumentParser()
    parser.add_argument('--port', required=True, type=int)
    parser.add_argument('--directory', required=True)
    args = parser.parse_args()

    reactor = Reactor()
    main(reactor, **vars(args))
    print('Ready to rumble the dumpserver at', args.port)
    print('  - dumps are written to', join(args.directory, 'dump'))
    stdout.flush()
    reactor.loop()
