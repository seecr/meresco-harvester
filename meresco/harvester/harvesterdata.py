## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2011-2012, 2015-2017, 2019-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012, 2015, 2019-2021 Stichting Kennisnet https://www.kennisnet.nl
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

from os import listdir, remove, rename, makedirs
from os.path import join, isfile, isdir
from shutil import copy

from re import compile as compileRe
from uuid import uuid4

from meresco.components.json import JsonList, JsonDict

from meresco.harvester.controlpanel.tools import checkName
from meresco.harvester.mapping import Mapping


class HarvesterData(object):
    def __init__(self, dataPath, id_fn=lambda: str(uuid4())):
        self._dataPath = dataPath
        self._dataIdPath = join(dataPath, '_')
        isdir(self._dataIdPath) or makedirs(self._dataIdPath)
        self.id_fn = id_fn

    #domain
    def getDomainIds(self):
        return JsonList(
                sorted([d.split('.domain',1)[0] for d in listdir(self._dataPath) if d.endswith('.domain')])
            )

    def getDomain(self, identifier, id=None):
        return self._readJsonWithId(fn_domain(identifier), id=id)

    def addDomain(self, identifier):
        if identifier == '':
            raise ValueError('No name given.')
        elif not checkName(identifier):
            raise ValueError('Name is not valid. Only use alphanumeric characters.')
        filename = fn_domain(identifier)
        if isfile(join(self._dataPath, filename)):
            raise ValueError('The domain already exists.')
        self._writeJsonWithId(filename, JsonDict({'identifier': identifier}))

    def updateDomain(self, identifier, description):
        domain = self.getDomain(identifier)
        domain['description'] = description
        self._writeJsonWithId(fn_domain(identifier), domain)

    #repositorygroup
    def getRepositoryGroupIds(self, domainId):
        return self.getDomain(domainId).get('repositoryGroupIds', [])


    def getRepositoryGroup(self, identifier, domainId, id=None):
        return self._readJsonWithId(fn_repositoryGroup(domainId, identifier), id)

    def getRepositoryGroups(self, domainId):
        return [self.getRepositoryGroup(repositoryGroupId, domainId) for repositoryGroupId in self.getRepositoryGroupIds(domainId)]

    def addRepositoryGroup(self, identifier, domainId):
        domain = self.getDomain(domainId)
        filename = fn_repositoryGroup(domainId, identifier)
        if identifier == '':
            raise ValueError('No name given.')
        elif not checkName(identifier):
            raise ValueError('Name is not valid. Only use alphanumeric characters.')
        if identifier.lower() in [g.lower() for g in domain.get('repositoryGroupIds', [])]:
            raise ValueError('The repositoryGroup already exists.')
        self._writeJsonWithId(filename, {'identifier': identifier})
        domain.setdefault('repositoryGroupIds', []).append(identifier)
        self._writeJsonWithId(fn_domain(domainId), domain)

    def updateRepositoryGroup(self, identifier, domainId, name):
        group = self.getRepositoryGroup(identifier, domainId=domainId)
        group.setdefault('name', {}).update(name)
        self._writeJsonWithId(fn_repositoryGroup(domainId, identifier), group)

    def deleteRepositoryGroup(self, identifier, domainId):
        domain = self.getDomain(domainId)
        domain['repositoryGroupIds'].remove(identifier)
        self._deleteWithId(fn_repositoryGroup(domainId, identifier))
        self._writeJsonWithId(fn_domain(domainId), domain)

    #repository
    def getRepositoryIds(self, domainId, repositoryGroupId=None):
        result = JsonList()
        allIds = self.getRepositoryGroupIds(domainId) if repositoryGroupId is None else [repositoryGroupId]
        for repositoryGroupId in allIds:
            jsonData = self.getRepositoryGroup(repositoryGroupId, domainId)
            result.extend(jsonData.get('repositoryIds', []))
        return result

    def getRepositoryGroupId(self, domainId, repositoryId):
        return self.getRepository(repositoryId, domainId)['repositoryGroupId']

    def getRepositories(self, domainId, repositoryGroupId=None):
        try:
            repositoryIds = self.getRepositoryIds(domainId=domainId, repositoryGroupId=repositoryGroupId)
        except IOError:
            raise ValueError("idDoesNotExist")

        return JsonList([self.getRepository(repositoryId, domainId) for repositoryId in repositoryIds])

    def getRepository(self, identifier, domainId, id=None):
        return self._readJsonWithId(fn_repository(domainId, identifier), id=id)

    def addRepository(self, identifier, domainId, repositoryGroupId):
        group = self.getRepositoryGroup(repositoryGroupId, domainId)
        filename = fn_repository(domainId, identifier)
        if identifier == '':
            raise ValueError('No name given.')
        elif not checkName(identifier):
            raise ValueError('Name is not valid. Only use alphanumeric characters.')
        if identifier.lower() in [r.lower() for r in group.get('repositoryIds', [])]:
            raise ValueError('The repository already exists.')
        if isfile(join(self._dataPath, filename)):
            raise ValueError("Repository name already in use.")

        self._writeJsonWithId(filename, JsonDict(dict(identifier=identifier, repositoryGroupId=repositoryGroupId)))
        group.setdefault('repositoryIds', []).append(identifier)
        self._writeJsonWithId(fn_repositoryGroup(domainId, repositoryGroupId), group)

    def deleteRepository(self, identifier, domainId, repositoryGroupId):
        group = self.getRepositoryGroup(repositoryGroupId, domainId)
        group['repositoryIds'].remove(identifier)
        repo = self.getRepository(identifier, domainId)
        fname = fn_repository(domainId, identifier)
        self._deleteWithId(fname)
        self._writeJsonWithId(fn_repositoryGroup(domainId, repositoryGroupId), group)

    def updateRepository(self, identifier, domainId, baseurl, set, metadataPrefix, mappingId, targetId, collection, maximumIgnore, use, continuous, complete, action, shopclosed, userAgent, authorizationKey, **kwargs):
        repository = self.getRepository(identifier, domainId)
        repository['baseurl'] = baseurl
        repository['set'] = set
        repository['metadataPrefix'] = metadataPrefix
        repository['mappingId'] = mappingId
        repository['targetId'] = targetId
        repository['collection'] = collection
        repository['maximumIgnore'] = maximumIgnore
        repository['use'] = use
        repository['complete'] = complete
        repository['continuous'] = continuous
        repository['action'] = action
        repository['userAgent'] = userAgent
        repository['authorizationKey'] = authorizationKey
        repository['shopclosed'] = shopclosed
        repository.update(**kwargs)
        self._writeJsonWithId(fn_repository(domainId, identifier), repository)

    def repositoryDone(self, identifier, domainId):
        repository = self.getRepository(identifier, domainId)
        repository['action'] = None
        self._writeJsonWithId(fn_repository(domainId, identifier), repository, newId=False)

    #target
    def getTarget(self, identifier, id=None):
        return self._readJsonWithId(fn_target(identifier), id=id)

    def addTarget(self, name, domainId, targetType):
        domain = self.getDomain(domainId)
        if not name:
            raise ValueError('No name given.')
        identifier = self.id_fn()
        target = JsonDict(
                name=name,
                identifier=identifier,
                targetType=targetType,
            )
        domain.setdefault('targetIds', []).append(identifier)
        self._writeJsonWithId(fn_target(identifier), target)
        self._writeJsonWithId(fn_domain(domainId), domain)
        return identifier

    def updateTarget(self, identifier, name, username, port, targetType, delegateIds, path, baseurl, oaiEnvelope):
        target = self.getTarget(identifier)
        target['name'] = name
        target['username'] = username
        target['port'] = port
        target['targetType'] = targetType
        target['delegateIds'] = delegateIds
        target['path'] = path
        target['baseurl'] = baseurl
        target['oaiEnvelope'] = oaiEnvelope
        self._writeJsonWithId(fn_target(identifier), target)

    def deleteTarget(self, identifier, domainId):
        domain = self.getDomain(domainId)
        domain['targetIds'].remove(identifier)
        self._deleteWithId(fn_target(identifier))
        self._writeJsonWithId(fn_domain(domainId), domain)

    #mapping
    def getMapping(self, identifier, id=None):
        return self._readJsonWithId(fn_mapping(identifier), id=id)

    def addMapping(self, name, domainId):
        domain = self.getDomain(domainId)
        if not name:
            raise ValueError('No name given.')
        identifier = self.id_fn()
        mapping = JsonDict(
                identifier=identifier,
                name=name,
                code = '''upload.parts['record'] = lxmltostring(upload.record)

upload.parts['meta'] = """<meta xmlns="http://meresco.org/namespace/harvester/meta">
  <upload><id>%(id)s</id></upload>
  <record>
    <id>%(recordId)s</id>
    <harvestdate>%(harvestDate)s</harvestdate>
  </record>
  <repository>
    <id>%(repository)s</id>
    <set>%(set)s</set>
    <baseurl>%(baseurl)s</baseurl>
    <repositoryGroupId>%(repositoryGroupId)s</repositoryGroupId>
    <metadataPrefix>%(metadataPrefix)s</metadataPrefix>
    <collection>%(collection)s</collection>
  </repository>
</meta>""" % dict([(k,xmlEscape(v) if v else '') for k,v in {
  'id': upload.id,
  'set': upload.repository.set,
  'baseurl': upload.repository.baseurl,
  'repositoryGroupId':  upload.repository.repositoryGroupId,
  'repository': upload.repository.id,
  'metadataPrefix': upload.repository.metadataPrefix,
  'collection': upload.repository.collection,
  'recordId': upload.recordIdentifier,
  'harvestDate': upload.oaiResponse.responseDate,
}.items()])
''',
                description = """This mapping is what has become the default mapping for most Meresco based projects.
""",
            )
        domain.setdefault('mappingIds', []).append(identifier)
        self._writeJsonWithId(fn_mapping(identifier), mapping)
        self._writeJsonWithId(fn_domain(domainId), domain)
        return identifier

    def updateMapping(self, identifier, name, description, code):
        mapping = self.getMapping(identifier)
        mapping['name'] = name
        mapping['description'] = description
        mapping['code'] = code
        self._writeJsonWithId(fn_mapping(identifier), mapping)
        mapping = Mapping(identifier)
        mapping.setCode(code)
        try:
            mapping.validate()
        except Exception as e:
            raise ValueError(e)

    def deleteMapping(self, identifier, domainId):
        domain = self.getDomain(domainId)
        domain['mappingIds'].remove(identifier)
        self._writeJsonWithId(fn_domain(domainId), domain)
        self._deleteWithId(fn_mapping(identifier))

    def _writeJsonWithId(self, filename, data, newId=True):
        if '@id' in data and newId:
            copy(join(self._dataPath, filename), join(self._dataIdPath, filename) + '.' + data['@id'])
            data['@base'] = data['@id']
        with open(join(self._dataPath, filename), 'w') as f:
            if newId:
                data['@id'] = self.id_fn()
            JsonDict(data).dump(f, indent=4, sort_keys=True)

    def _readJsonWithId(self, filename, id=None):
        fpath = join(self._dataPath, filename)
        if id is not None:
            fpath = join(self._dataIdPath, filename) + '.' + id
        try:
            d = JsonDict.load(fpath)
        except IOError:
            if id is not None:
                result = self._readJsonWithId(filename)
                if result['@id'] == id:
                    return result
            raise ValueError(filename)
        if id is None and '@id' not in d:
            self._writeJsonWithId(filename, d)
        return d

    def _deleteWithId(self, filename):
        fpath = join(self._dataPath, filename)
        curId = JsonDict.load(fpath)['@id']
        rename(fpath, join(self._dataIdPath, filename) + '.' + curId)


fn_domain = lambda domainId: "{}.domain".format(domainId)
fn_repositoryGroup = lambda domainId, repositoryGroupId: "{}.{}.repositoryGroup".format(domainId, repositoryGroupId)
fn_repository = lambda domainId, repositoryId: "{}.{}.repository".format(domainId, repositoryId)
fn_target = lambda targetId: "{}.target".format(targetId)
fn_mapping = lambda mappingId: "{}.mapping".format(mappingId)


XMLHEADER = compileRe(r'(?s)^(?P<header>\<\?.*\?\>\s+)?(?P<body>.*)$')
