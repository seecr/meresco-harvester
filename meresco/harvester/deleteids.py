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
# Copyright (C) 2011, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2013, 2017, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020 Netherlands Institute for Sound and Vision https://beeldengeluid.nl/
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
from traceback import format_exception

from meresco.core import Observable

from .mapping import Upload
from .ids import idfilename

class DeleteIds(Observable):
    def __init__(self, repository, stateDir, batchSize=1000):
        Observable.__init__(self)
        self._stateDir = stateDir
        self._repository = repository
        self._batchSize = batchSize
        self._invalid = self._deleteIds = False

    def ids(self):
        return self.call.getIds(invalid=self._invalid, deleteIds=self._deleteIds)

    def delete(self):
        self.do.start()
        try:
            self._delete()
        finally:
            self.do.stop()

    def deleteFile(self, filename):
        self._invalid = filename.endswith("_invalid.ids")
        self._deleteIds = filename.endswith(".delete")
        try:
            self.delete()
        finally:
            self._invalid = False
            self._deleteIds = False

    def _delete(self):
        ids = self.ids()
        processed = 0
        try:
            for id in ids:
                try:
                    anUpload = Upload(repository=self._repository)
                    anUpload.id = id
                    self.do.notifyHarvestedRecord(anUpload.id)
                    self.do.delete(anUpload)
                    if not self._invalid and not self._deleteIds:
                        self.do.deleteIdentifier(id)
                    processed += 1
                    if processed % self._batchSize == 0 and processed > 0:
                        self.call.flushIds(invalid=self._invalid, deleteIds=self._deleteIds)
                except:
                    xtype, xval, xtb = sys.exc_info()
                    errorMessage = '|'.join(map(str.strip,format_exception(xtype, xval, xtb)))
                    self.do.logError(errorMessage, id=id)
                    raise
        finally:
            self.call.flushIds(invalid=self._invalid, deleteIds=self._deleteIds)

    def markDeleted(self):
        self.do.markDeleted()
