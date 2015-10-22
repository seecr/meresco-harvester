## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2011-2012, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Kennisnet http://www.kennisnet.nl
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

from os import listdir, remove
from os.path import join, isfile

from re import compile as compileRe
from meresco.components.json import JsonList, JsonDict
from meresco.harvester.controlpanel.tools import checkName

XMLHEADER = compileRe(r'(?s)^(?P<header>\<\?.*\?\>\s+)?(?P<body>.*)$')

class HarvesterData(object):

    def __init__(self, dataPath):
        self._dataPath = dataPath

    #domain
    def getDomainIds(self):
        return JsonList(
                [d.split('.domain',1)[0] for d in listdir(self._dataPath) if d.endswith('.domain')]
            )

    def getDomain(self, identifier):
        domainFile = join(self._dataPath, '{0}.domain'.format(identifier))
        try:
            return JsonDict.load(open(domainFile))
        except IOError:
            raise ValueError('idDoesNotExist')

    def addDomain(self, identifier):
        if identifier == '':
            raise ValueError('No name given.')
        elif not checkName(identifier):
            raise ValueError('Name is not valid. Only use alphanumeric characters.')
        filename = "{}.domain".format(identifier)
        if self._exists(filename):
            raise ValueError('The domain already exists.')
        self._save(JsonDict(dict(identifier=identifier)), filename)

    def updateDomain(self, identifier, description):
        domain = self.getDomain(identifier)
        domain['description'] = description
        self._save(domain, "{}.domain".format(identifier))

    #repositorygroup
    def getRepositoryGroupIds(self, domainId):
        return JsonDict.load(open(join(self._dataPath, '%s.domain' % domainId))).get('repositoryGroupIds',[])

    def getRepositoryGroup(self, identifier, domainId):
        return JsonDict.load(open(join(self._dataPath, '%s.%s.repositoryGroup' % (domainId, identifier))))

    def addRepositoryGroup(self, identifier, domainId):
        domain = self.getDomain(domainId)
        filename = "{}.{}.repositoryGroup".format(domainId, identifier)
        if identifier == '':
            raise ValueError('No name given.')
        elif not checkName(identifier):
            raise ValueError('Name is not valid. Only use alphanumeric characters.')
        if self._exists(filename):
            raise ValueError('The repositoryGroup already exists.')
        self._save(JsonDict(dict(identifier=identifier)), filename)
        domain.setdefault('repositoryGroupIds', []).append(identifier)
        self._save(domain, "{}.domain".format(domainId))

    def updateRepositoryGroup(self, identifier, domainId, name):
        group = self.getRepositoryGroup(identifier, domainId=domainId)
        group.setdefault('name', {}).update(name)
        self._save(group, "{}.{}.repositoryGroup".format(domainId, identifier))

    def deleteRepositoryGroup(self, identifier, domainId):
        domain = self.getDomain(domainId)
        domain['repositoryGroupIds'].remove(identifier)
        self._delete("{}.{}.repositoryGroup".format(domainId, identifier))
        self._save(domain, "{}.domain".format(domainId))

    #repository
    def getRepositoryIds(self, domainId, repositoryGroupId=None):
        result = []
        allIds = self.getRepositoryGroupIds(domainId) if repositoryGroupId is None else [repositoryGroupId]
        for repositoryGroupId in allIds:
            jsonData = JsonDict.load(open(join(self._dataPath, '%s.%s.repositoryGroup' % (domainId, repositoryGroupId))))
            result.extend(jsonData.get('repositoryIds', []))
        return result

    def getRepositoryGroupId(self, domainId, repositoryId):
        return JsonDict.load(open(join(self._dataPath, '%s.%s.repository' % (domainId, repositoryId))))['repositoryGroupId']

    def getRepositories(self, domainId, repositoryGroupId=None):
        try:
            repositoryIds = self.getRepositoryIds(domainId=domainId, repositoryGroupId=repositoryGroupId)
        except IOError:
            raise ValueError("idDoesNotExist")
        return JsonList([
                JsonDict.load(open(join(self._dataPath, '%s.%s.repository' % (domainId, repositoryId))))
                for repositoryId in repositoryIds
            ])

    def getRepository(self, identifier, domainId):
        try:
            return JsonDict.load(open(join(self._dataPath, '%s.%s.repository' % (domainId, identifier))))
        except IOError:
            raise ValueError("idDoesNotExist")

    def getTarget(self, identifier):
        try:
            return JsonDict.load(open(join(self._dataPath, '%s.target' % identifier)))
        except IOError:
            raise ValueError("idDoesNotExist")

    def getMapping(self, identifier):
        try:
            return JsonDict.load(open(join(self._dataPath, '%s.mapping' % identifier)))
        except IOError:
            raise ValueError("idDoesNotExist")

    def _save(self, data, filename):
        with open(join(self._dataPath, filename), 'w') as f:
            data.dump(f, indent=4, sort_keys=True)

    def _delete(self, filename):
        remove(join(self._dataPath, filename))

    def _exists(self, filename):
        return isfile(join(self._dataPath, filename))

