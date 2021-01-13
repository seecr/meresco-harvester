## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2015 Stichting Kennisnet http://www.kennisnet.nl
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

from meresco.components.json import JsonDict
from meresco.harvester.mapping import Mapping
from meresco.harvester.target import Target
from meresco.harvester.repository import Repository
from urllib.parse import urlencode
from urllib.request import urlopen

class InternalServerProxy(object):
    def __init__(self, internalurl, doSetActionDone=True):
        self._internalurl = internalurl
        self._geturl = '%s/get?' % internalurl
        self._doSetActionDone = doSetActionDone

    def getRepositoryGroup(self, identifier, domainId):
        return self.urlJsonDict(verb='GetRepositoryGroup', identifier=identifier, domainId=domainId)['response']['GetRepositoryGroup']

    def getRepository(self, identifier, domainId):
        return self.urlJsonDict(verb='GetRepository', identifier=identifier, domainId=domainId)['response']['GetRepository']

    def getRepositoryObject(self, identifier, domainId):
        result = Repository(repositoryId=identifier, domainId=domainId)
        result.fill(self, self.getRepository(identifier, domainId))
        return result

    def getRepositories(self, domainId, repositoryGroupId=None):
        return self.urlJsonDict(verb='GetRepositories', domainId=domainId, repositoryGroupId=repositoryGroupId)['response']['GetRepositories']

    def getRepositoryIds(self, domainId, repositoryGroupId=None):
        return self.urlJsonDict(verb='GetRepositoryIds', domainId=domainId, repositoryGroupId=repositoryGroupId)['response']['GetRepositoryIds']

    def getTarget(self, identifier):
        return self.urlJsonDict(verb='GetTarget', identifier=identifier)['response']['GetTarget']

    def getTargetObject(self, identifier):
        result = Target(identifier)
        result.fill(self, self.getTarget(identifier=identifier))
        return result

    def getMapping(self, identifier):
        return self.urlJsonDict(verb='GetMapping', identifier=identifier)['response']['GetMapping']

    def getMappingObject(self, identifier):
        result = Mapping(identifier)
        result.fill(self, self.getMapping(identifier=identifier))
        return result

    def getDomain(self, identifier):
        return self.urlJsonDict(verb='GetDomain', identifier=identifier)['response']['GetDomain']

    def getDomainIds(self):
        return self.urlJsonDict(verb='GetDomainIds')['response']['GetDomainIds']

    def getStatus(self, **kwargs):
        return self.urlJsonDict(verb='GetStatus', **kwargs)['response']['GetStatus']

    def repositoryActionDone(self, domainId, repositoryId):
        if self._doSetActionDone:
            data = urlencode({'domainId': domainId, 'identifier': repositoryId})
            self._urlopen("{}/action/repositoryDone".format(self._internalurl), data=data.encode()).read()

    def urlJsonDict(self, **kwargs):
        arguments = dict((k ,v) for k, v in list(kwargs.items()) if v)
        result = JsonDict.load(
                self._urlopen("{}/get?{}".format(self._internalurl, urlencode(arguments)))
            )
        if 'error' in result:
            raise ValueError(result['error']['message'])
        return result

    @staticmethod
    def _urlopen(*args, **kwargs):
        return urlopen(*args, **kwargs)
