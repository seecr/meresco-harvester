## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
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
from eventlogger import CompositeLogger, NilEventLogger
import getopt, threading
from urllib2 import urlopen
from urllib import urlencode
from slowfoot.wrappers import wrapp
from oairequest import OAIRequest
NOTHING_TO_DO = 'Nothing to do!'
HARVESTED = 'Harvested.'

class Harvester(object):
    def __init__(self, repository, stateDir, logDir, mockRequest = None, mockLogger = None, generalHarvestLog=NilEventLogger()):
        self._repository = repository
        self._logger = mockLogger or HarvesterLog(stateDir, logDir, repository.id)
        self._eventlogger = CompositeLogger([
            (['*'], self._logger.eventLogger()),
            (['ERROR', 'INFO', 'WARN'], generalHarvestLog)
        ])
        self._oairequest = mockRequest or OAIRequest(self._repository.url)
        self._uploader = repository.createUploader(self._eventlogger)
        self._mapper = repository.mapping()
        self._MAXTIME= 30*60 # 30 minutes

    def getRecord(self, id):
        return self._oairequest.getRecord(metadataPrefix=self._repository.metadataPrefix, identifier=id)

    def uploaderInfo(self):
        return self._uploader.info()

    def listRecords(self, from_, token, set):
        if token:
            return self._oairequest.listRecords(resumptionToken=token)
        elif from_:
            if set:
                return self._oairequest.listRecords(metadataPrefix=self._repository.metadataPrefix, from_ = from_, set = set)
            return self._oairequest.listRecords(metadataPrefix=self._repository.metadataPrefix, from_ = from_)
        elif set:
            return self._oairequest.listRecords(metadataPrefix=self._repository.metadataPrefix, set = set)
        return self._oairequest.listRecords(metadataPrefix=self._repository.metadataPrefix)

    def fetchRecords(self, from_, token, total):
        harvestedRecords = 0
        uploadedRecords = 0
        deletedRecords = 0
        records = self.listRecords(from_, token, self._repository.set)
        self._logger.updateStatsfile(harvestedRecords, uploadedRecords, deletedRecords, total + uploadedRecords)
        for record in records:
            harvestedRecords += 1
            uploadcount, deletecount = self.uploadRecord(record)
            uploadedRecords += uploadcount
            deletedRecords += deletecount
            self._logger.updateStatsfile(harvestedRecords, uploadedRecords, deletedRecords, total + uploadedRecords)
        newtoken = getattr(records.parentNode, 'resumptionToken', None)
        return uploadedRecords == harvestedRecords, newtoken

    def uploadRecord(self, record):
        upload = self._mapper.createEmptyUpload(self._repository, record)

        if record.header.status == "deleted":
            self._uploader.delete(upload)
            self._logger.logDeletedID(upload.id)
            uploadresult = (0,1)
        else:
            upload = self._mapper.createUpload(self._repository, record, logger=self._eventlogger)
            if upload:
                self._uploader.send(upload)
                self._logger.logID(upload.id)
                uploadresult = (1,0)
            else:
                uploadresult = (0,0)
        return uploadresult

    def _harvestLoop(self):
        try:
            self._logger.startRepository()
            result, newtoken = self.fetchRecords(self._logger.from_, self._logger.token, self._logger.total)
            self._logger.endRepository(newtoken)
            return newtoken
        except:
            self._logger.endWithException()
            raise

    def _harvest(self):
        try:
            self._eventlogger.logLine('STARTHARVEST', '',id=self._repository.id)
            self._eventlogger.info(self.uploaderInfo(), id=self._repository.id)
            self._eventlogger.info("Mappingname '%s'"%self._mapper.name, id=self._repository.id)
            self._uploader.start()
            try:
                return self._harvestLoop()
            finally:
                self._uploader.stop()
        finally:
            self._eventlogger.logLine('ENDHARVEST','',id=self._repository.id)

    def harvest(self):
        try:
            if self._logger.hasWork():
                resumptionToken = self._harvest()
                hasResumptionToken = bool(resumptionToken and str(resumptionToken) != 'None')
                return HARVESTED, hasResumptionToken
            else:
                return NOTHING_TO_DO, False
        finally:
            self._logger.close()
