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
import getopt, threading
from urllib2 import urlopen
from urllib import urlencode
from slowfoot.wrappers import wrapp
from meresco.core import Observable
from virtualuploader import InvalidDataException, TooMuchInvalidDataException


NOTHING_TO_DO = 'Nothing to do!'
HARVESTED = 'Harvested.'

class Harvester(Observable):
    def __init__(self, repository):
        Observable.__init__(self)
        self._repository = repository
        self._MAXTIME= 30*60 # 30 minutes

    def getRecord(self, id):
        return self.any.getRecord(metadataPrefix=self._repository.metadataPrefix, identifier=id)

    def uploaderInfo(self):
        return self.any.info()

    def listRecords(self, from_, token, set):
        if token:
            return self.any.listRecords(resumptionToken=token)
        elif from_:
            if set:
                return self.any.listRecords(metadataPrefix=self._repository.metadataPrefix, from_ = from_, set = set)
            return self.any.listRecords(metadataPrefix=self._repository.metadataPrefix, from_ = from_)
        elif set:
            return self.any.listRecords(metadataPrefix=self._repository.metadataPrefix, set = set)
        return self.any.listRecords(metadataPrefix=self._repository.metadataPrefix)

    def fetchRecords(self, from_, token):
        records, resumptionToken = self.listRecords(from_, token, self._repository.set)
        for record in records:
            self.uploadRecord(record)
        return resumptionToken

    def uploadRecord(self, record):
        upload = self.any.createUpload(self._repository, record)
        self.do.notifyHarvestedRecord(upload.id)
        if record.header.status == "deleted":
            self.do.delete(upload)
            self.do.deleteIdentifier(upload.id)
        elif not upload.skip:
            try:
                self.do.send(upload)
                self.do.uploadIdentifier(upload.id)
            except InvalidDataException, e:
                maxIgnore = self._repository.maxIgnore()
                if self.any.totalIgnoredIds() >= maxIgnore:
                    raise TooMuchInvalidDataException(upload.id, maxIgnore)
                self.do.ignoreIdentifier(upload.id, e.originalMessage)

    def _harvestLoop(self):
        try:
            self.do.startRepository()
            state = self.any.state()
            newtoken = self.fetchRecords(state.startdate, state.token)
            self.do.endRepository(newtoken)
            return newtoken
        except:
            self.do.endWithException()
            raise

    def _harvest(self):
        try:
            self.do.logLine('STARTHARVEST', '',id=self._repository.id)
            self.do.logInfo(self.any.uploaderInfo(), id=self._repository.id)
            self.do.logInfo(self.any.mappingInfo(), id=self._repository.id)
            self.do.start()
            try:
                return self._harvestLoop()
            finally:
                self.do.stop()
        finally:
            self.do.logLine('ENDHARVEST','',id=self._repository.id)

    def harvest(self):
        try:
            if self.any.hasWork():
                resumptionToken = self._harvest()
                hasResumptionToken = bool(resumptionToken and str(resumptionToken) != 'None')
                return HARVESTED, hasResumptionToken
            else:
                return NOTHING_TO_DO, False
        finally:
            self.do.close()
