## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from os.path import join, isdir, isfile
from os import makedirs, rename, listdir, remove
from uuid import uuid4
from meresco.components.json import JsonDict
from shutil import copy

class OldDataStore(object):
    def __init__(self, dataPath, id_fn=lambda: str(uuid4())):
        self._dataPath = dataPath
        isdir(self._dataPath) or makedirs(self._dataPath)
        self.id_fn = id_fn

    def addData(self, identifier, datatype, data, newId=True):
        filename = '{}.{}'.format(identifier, datatype)
        with open(join(self._dataPath, filename), 'w') as f:
            JsonDict(data).dump(f, indent=4, sort_keys=True)

    def getData(self, identifier, datatype, guid=None):
        filename = '{}.{}'.format(identifier, datatype)
        fpath = join(self._dataPath, filename)
        if guid is not None:
            raise NotImplementedError()
        try:
            d = JsonDict.load(fpath)
        except IOError:
            raise ValueError(filename)
        return d

    def listForDatatype(self, datatype):
        ext = '.{}'.format(datatype)
        return sorted([d.split(ext,1)[0] for d in listdir(self._dataPath) if d.endswith(ext)])

    def exists(self, identifier, datatype):
        return isfile(join(self._dataPath, '{}.{}'.format(identifier, datatype)))

    def deleteData(self, identifier, datatype):
        filename = '{}.{}'.format(identifier, datatype)
        fpath = join(self._dataPath, filename)
        remove(fpath)

    def getGuid(self, guid):
        raise NotImplementedError()


class DataStore(object):
    def __init__(self, dataPath, id_fn=lambda: str(uuid4())):
        self._dataPath = dataPath
        self._dataIdPath = join(dataPath, '_')
        isdir(self._dataIdPath) or makedirs(self._dataIdPath)
        self.id_fn = id_fn

    def addData(self, identifier, datatype, data, newId=True):
        filename = '{}.{}'.format(identifier, datatype)
        if '@id' in data and newId:
            copy(join(self._dataPath, filename), join(self._dataIdPath, filename) + '.' + data['@id'])
            data['@base'] = data['@id']
        with open(join(self._dataPath, filename), 'w') as f:
            if newId:
                data['@id'] = self.id_fn()
            JsonDict(data).dump(f, indent=4, sort_keys=True)

    def getData(self, identifier, datatype, guid=None):
        filename = '{}.{}'.format(identifier, datatype)
        fpath = join(self._dataPath, filename)
        if guid is not None:
            fpath = join(self._dataIdPath, filename) + '.' + guid
        try:
            d = JsonDict.load(fpath)
        except IOError:
            if guid is not None:
                result = self.getData(identifier, datatype)
                if result['@id'] == guid:
                    return result
            raise ValueError(filename)
        if guid is None and '@id' not in d:
            self.addData(identifier, datatype, d)
        return d

    def listForDatatype(self, datatype):
        ext = '.{}'.format(datatype)
        return sorted([d.split(ext,1)[0] for d in listdir(self._dataPath) if d.endswith(ext)])

    def exists(self, identifier, datatype):
        return isfile(join(self._dataPath, '{}.{}'.format(identifier, datatype)))

    def deleteData(self, identifier, datatype):
        filename = '{}.{}'.format(identifier, datatype)
        fpath = join(self._dataPath, filename)
        curId = JsonDict.load(fpath)['@id']
        rename(fpath, join(self._dataIdPath, filename) + '.' + curId)

    def getGuid(self, guid):
        raise NotImplementedError()

