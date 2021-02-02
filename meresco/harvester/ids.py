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
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
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

#
import os

from os import makedirs
from os.path import isdir, join, basename
from escaping import escapeFilename, unescapeFilename

def idfilename(stateDir, name):
    isdir(stateDir) or makedirs(stateDir)
    return join(stateDir, name + '.ids')

def readIds(filename):
    uniqueIds = set()
    ids = []
    with open(filename, 'a+') as fp:
        fp.seek(0)
        for id in (unescapeFilename(id) for id in fp):
            if id[-1] == '\n':
                id = id[:-1]
            if id in uniqueIds:
                continue
            ids.append(id)
            uniqueIds.add(id)
    return ids

def writeIds(filename, ids):
    idfilenew = open(filename + '.new', 'w')
    try:
        for anId in ids:
            idfilenew.write('{}\n'.format(escapeFilename(anId)))
    finally:
        idfilenew.close()
    os.rename(filename + '.new', filename)

class Ids(object):
    def __init__(self, stateDir, name):
        self._filename = idfilename(stateDir, name)
        self._idsfile = None
        self._ids = None
        self.reopen()

    def reopen(self):
        self._idsfile and self.close()
        self._ids = readIds(self._filename)
        self.open()

    def __len__(self):
        return len(self._ids)

    def __iter__(self):
        for id in self._ids:
            yield unescapeFilename(id)

    def clear(self):
        self._ids = []

    def open(self):
        self._idsfile = open(self._filename, 'a')

    def close(self):
        self._idsfile.close()
        writeIds(self._filename, self._ids)

    def getIds(self):
        return self._ids[:] #[unescapeFilename(each) for each in self._ids[:]]

    def getDeleteIds(self):
        return readIds("{}.delete".format(self._filename))


    def add(self, uploadid):
        if uploadid in self._ids:
            return
        self._ids.append(uploadid)
        self._idsfile.write('{}\n'.format(escapeFilename(uploadid)))
        self._idsfile.flush()

    def remove(self, uploadid):
        if uploadid in self._ids:
            self._ids.remove(uploadid)
            self.close()
            self.open()


