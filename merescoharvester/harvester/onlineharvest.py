## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
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

from harvester import Harvester
from slowfoot import binderytools
from slowfoot.wrappers import wrapp
from mapping import TestRepository,DataMapAssertionException
from eventlogger import StreamEventLogger

class OnlineHarvest:
    def __init__(self, outputstream):
        self._output = outputstream
        self.eventlogger = StreamEventLogger(self._output)

    def performMapping(self, mapping, urlString):
        doAssertions=True
        xml = wrapp(binderytools.bind_uri(urlString))
        records = xml.OAI_PMH.ListRecords.record
        for record in records:
            try:
                upload = mapping.createEmptyUpload(TestRepository, record.header, record.metadata, record.about)
                if record.header.status == "deleted":
                    self.writeDelete(upload)
                else:
                    upload = mapping.createUpload(TestRepository, record.header, record.metadata, record.about, self.eventlogger, doAssertions)
                    if upload != None:
                        self.writeUpload(upload)
            except DataMapAssertionException, ex:
                self.writeLine('AssertionError: '+str(ex))

    def _writeId(self, anUpload):
        self.writeLine('')
        self.writeLine('upload.id='+anUpload.id)

    def writeDelete(self, anUpload):
        self._writeId(anUpload)
        self.writeLine('DELETED')

    def writeUpload(self, anUpload):
        self._writeId(anUpload)
        self.writeLine('-v- upload.fields -v-')
        for k,v in anUpload.fields.items():
            self.writeLine('  '+k+'='+v)
        self.writeLine('-^- upload.fields -^-')
        for partname, part in anUpload.parts.items():
            self.writeLine('-v- part %s -v-' % partname)
            self.writeLine(part)
            self.writeLine('-^- part -^-')


    def writeLine(self, line):
        self._output.write(line + '\n')
        self._output.flush()

#    def harvest(self, repositorykey, resumptionToken = None, mockRequest = None):
#        repository = getRepository(repositorykey)
#        repository.ssetarget =  self.ssetarget
#        harvester = Harvester(repository, None)
