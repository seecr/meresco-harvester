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
# Copyright (C) 2011, 2013-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011, 2015 Stichting Kennisnet http://www.kennisnet.nl
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

from mapping import TestRepository,DataMapAssertionException
from eventlogger import StreamEventLogger
from saharaget import SaharaGet
from meresco.harvester.mapping import Mapping
from meresco.harvester.oairequest import OaiRequest
from meresco.harvester.controlpanel.internalserverproxy import InternalServerProxy

class OnlineHarvest(object):
    def __init__(self, outputstream, saharaUrl):
        self._output = outputstream
        self._saharaGet = SaharaGet(saharaUrl)
        self._proxy = InternalServerProxy(outputstream)

    def performMapping(self, domainId, mappingId, urlString):
        mappingDict = self._proxy.getMapping(mappingId)
        mapping = Mapping(mappingId)
        mapping.setCode(mappingDict.get('code', ''))
        mapping.addObserver(StreamEventLogger(self._output))
        self._output.write("Mappingname '{}'".format(mappingDict.get('name')))
        self._output.write('\n')
        response = OaiRequest(urlString).request()
        for record in response.records:
            response.selectRecord(record)
            try:
                upload = mapping.createUpload(TestRepository, response, doAsserts=True)
                self.writeUpload(upload)
            except DataMapAssertionException, ex:
                self.writeLine('AssertionError: '+str(ex))

    def _writeId(self, anUpload):
        self.writeLine('')
        self.writeLine('upload.id='+anUpload.id)

    def writeUpload(self, anUpload):
        self._writeId(anUpload)
        if anUpload.isDeleted:
            self.writeLine('DELETED')
            return
        for partname, part in anUpload.parts.items():
            self.writeLine('-v- part %s -v-' % partname)
            self.writeLine(part)
            self.writeLine('-^- part -^-')


    def writeLine(self, line):
        self._output.write(line + '\n')
        self._output.flush()

