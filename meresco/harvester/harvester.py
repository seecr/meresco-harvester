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
# Copyright (C) 2010-2012, 2015, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2011-2015, 2017, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
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

import sys
from meresco.core import Observable

from .virtualuploader import InvalidDataException, TooMuchInvalidDataException
from meresco.harvester.namespaces import xpathFirst


NOTHING_TO_DO = 'Nothing to do!'
HARVESTED = 'Harvested.'

class Harvester(Observable):
    def __init__(self, repository):
        Observable.__init__(self)
        self._repository = repository
        self._MAXTIME= 30*60 # 30 minutes

    def getRecord(self, id):
        return self.call.getRecord(metadataPrefix=self._repository.metadataPrefix, identifier=id)

    def uploaderInfo(self):
        return self.call.info()

    def listRecords(self, from_, token, set):
        kwargs = {}
        if token:
            kwargs['resumptionToken'] = token
        else:
            kwargs['metadataPrefix'] = self._repository.metadataPrefix
            if from_:
                kwargs['from_'] = from_
            if set:
                kwargs['set'] = set
        return self.call.listRecords(**kwargs)

    def fetchRecords(self, from_, token):
        response = self.listRecords(from_, token, self._repository.set)
        for record in response.records:
            response.selectRecord(record)
            self.upload(response)
        return response

    def upload(self, oaiResponse):
        upload = self.call.createUpload(self._repository, oaiResponse)
        self.do.notifyHarvestedRecord(upload.id)
        if xpathFirst(oaiResponse.record, 'oai:header/@status') == "deleted":
            self.do.delete(upload)
            self.do.deleteIdentifier(upload.id)
        elif not upload.skip:
            try:
                self.do.send(upload)
                self.do.uploadIdentifier(upload.id)
            except InvalidDataException as e:
                self.do.logInvalidData(upload.id, e.originalMessage)
                maxIgnore = self._repository.maxIgnore()
                if self.call.totalInvalidIds() > maxIgnore:
                    raise TooMuchInvalidDataException(upload.id, maxIgnore)
                self.do.logIgnoredIdentifierWarning(upload.id)

    def _harvestLoop(self):
        try:
            self.do.startRepository()
            state = self.call.state()
            from_ = state.from_
            if from_ and not self._repository.continuous:
                from_ = from_.split('T')[0]
            response = self.fetchRecords(from_, state.token)
            self.do.endRepository(response.resumptionToken, response.responseDate)
            return response.resumptionToken
        except:
            exType, exValue, exTb = sys.exc_info()
            self.do.endWithException(exType, exValue, exTb)
            raise

    def _harvest(self):
        try:
            self.do.logLine('STARTHARVEST', '',id=self._repository.id)
            self.do.logInfo(self.call.uploaderInfo(), id=self._repository.id)
            self.do.logInfo(self.call.mappingInfo(), id=self._repository.id)
            self.do.start()
            try:
                return self._harvestLoop()
            finally:
                self.do.stop()
        finally:
            self.do.logLine('ENDHARVEST','',id=self._repository.id)

    def harvest(self):
        try:
            if self.call.hasWork(continuousInterval=self._repository.continuous):
                resumptionToken = self._harvest()
                hasResumptionToken = bool(resumptionToken and str(resumptionToken) != 'None')
                return HARVESTED, hasResumptionToken
            else:
                return NOTHING_TO_DO, False
        finally:
            self.do.close()
