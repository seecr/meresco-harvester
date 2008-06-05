## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for 
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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


import os, sys, shelve, time, traceback,re
from harvesterlog import HarvesterLog
import getopt, threading
from urllib2 import urlopen
from urllib import urlencode
from cq2utils.wrappers import wrapp
from oairequest import OAIRequest
NOTHING_TO_DO = 'Nothing to do!'
HARVESTED = 'Harvested.'

def p(anObject):
    sys.stdout.write(str(anObject)+'\n')
    sys.stdout.flush()

class Harvester:
    def __init__(self, repository, stateDir, logDir, mockRequest = None, mockLogger = None):
        self._repository = repository
        self._logger = mockLogger or HarvesterLog(logpath, repository.id)
        self._eventlogger = self._logger.eventLogger()
        self._oairequest = mockRequest or OAIRequest(self._repository.url)
        self._uploader = repository.createUploader(self._eventlogger)
        self._mapper = repository.mapping()
        self._MAXTIME= 30*60 # 30 minutes

    def getRecord(self, id):
        return self._oairequest.getRecord(metadataPrefix=self._repository.metadataPrefix, identifier=id)

    def uploaderInfo(self):
        return self._uploader.info()

    def listRecords(self, server, from_, token, set):
        if token:
            return server.listRecords(resumptionToken=token)
        elif from_:
            if set:
                return server.listRecords(metadataPrefix=self._repository.metadataPrefix, from_ = from_, set = set)
            return server.listRecords(metadataPrefix=self._repository.metadataPrefix, from_ = from_)
        elif set:
            return server.listRecords(metadataPrefix=self._repository.metadataPrefix, set = set)
        return server.listRecords(metadataPrefix=self._repository.metadataPrefix)

    def fetchRecords(self, server, from_, token, total):
        harvestedRecords = 0
        uploadedRecords = 0
        deletedRecords = 0
        self._logger.begin()
        records = self.listRecords(server, from_, token, self._repository.set)
        self._logger.updateStatsfile(harvestedRecords, uploadedRecords, deletedRecords, total + uploadedRecords)
        for record in records:
            harvestedRecords += 1
            uploadcount, deletecount = self.uploadRecord(record.header, record.metadata,
            record.about)
            uploadedRecords += uploadcount
            deletedRecords += deletecount
            self._logger.updateStatsfile(harvestedRecords, uploadedRecords, deletedRecords, total + uploadedRecords)
        newtoken = getattr(records.parentNode, 'resumptionToken', None)
        self._logger.done()
        return uploadedRecords == harvestedRecords, newtoken

    def uploadRecord(self, header, metadata, about):
        upload = self._mapper.createEmptyUpload(self._repository, header, metadata, about)

        if header.status == "deleted":
            self._uploader.delete(upload)
            self._logger.logDeletedID(upload.id)
            uploadresult = (0,1)
        else:
            upload = self._mapper.createUpload(self._repository, header, metadata, about, logger=self._eventlogger)
            if upload:
                self._uploader.send(upload)
                self._logger.logID(upload.id)
                uploadresult = (1,0)
            else:
                uploadresult = (0,0)
        return uploadresult

    def _harvestLoop(self):

        try:
            self._logger.startRepository(self._oairequest.identify().repositoryName)
            result, newtoken = self.fetchRecords(self._oairequest, self._logger.from_, self._logger.token, self._logger.total)
            self._logger.endRepository(newtoken)
        except:
            self._logger.endWithException()
            raise

    def _harvest(self):
        try:
            self._logger.eventLogger().logLine('STARTHARVEST',self.uploaderInfo(),id=self._repository.id)
            self._eventlogger.logLine("INFO", "Mappingname '%s'"%self._mapper.name, id=self._repository.id)
            self._uploader.start()
            try:
                self._harvestLoop()
            finally:
                self._uploader.stop()
        finally:
            self._logger.eventLogger().logLine('ENDHARVEST','',id=self._repository.id)

    def harvest(self):
        try:
            if self._logger.hasWork():
                self._harvest()
                return HARVESTED
            else:
                return NOTHING_TO_DO
        finally:
            self._logger.close()
