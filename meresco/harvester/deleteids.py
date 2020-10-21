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
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2013, 2017, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020 Netherlands Institute for Sound and Vision https://beeldengeluid.nl/
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

from escaping import escapeFilename, unescapeFilename

from meresco.core import Observable

from .mapping import Upload
from .harvesterlog import idfilename


class DeleteIds(Observable):
    def __init__(self, repository, stateDir, batchSize=1000):
        Observable.__init__(self)
        self._stateDir = stateDir
        self._repository = repository
        self._filename = idfilename(self._stateDir, self._repository.id)
        self._batchSize = batchSize

    def ids(self):
        return readIds(self._filename)

    def delete(self):
        self.do.start()
        try:
            self._delete()
        finally:
            self.do.stop()

    def deleteFile(self, filename):
        self._filename = filename
        self.delete()

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
                    processed += 1
                    if processed % self._batchSize == 0 and processed > 0:
                        self._writeIds(ids[processed:])
                except:
                    xtype, xval, xtb = sys.exc_info()
                    errorMessage = '|'.join(map(str.strip,format_exception(xtype, xval, xtb)))
                    self.do.logError(errorMessage, id=id)
                    raise
        finally:
            self._writeIds(ids[processed:])

    def _writeIds(self, remainingIDs):
        writeIds(self._filename, remainingIDs)

    def markDeleted(self):
        self.do.markDeleted()


def readIds(filename):
    ids = []
    uniqueIds = set()
    with open(filename) as fp:
        for id in (unescapeFilename(id) for id in fp):
            if id[-1] == '\n':
                id = id[:-1]
            if id in uniqueIds:
                continue
            ids.append(id)
            uniqueIds.add(id)
    return ids

def writeIds(filename, ids):
    f = open(filename,'w')
    try:
        for id in ids:
            f.write(escapeFilename(id))
            f.write('\n')
    finally:
        f.close()
