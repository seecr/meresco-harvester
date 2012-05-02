## begin license ##
# 
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for 
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl 
# 
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from lxml.etree import parse
from os.path import join

from re import compile as compileRe

XMLHEADER = compileRe(r'(?s)^(?P<header>\<\?.*\?\>\s+)?(?P<body>.*)$')

class HarvesterData(object):

    def __init__(self, dataPath):
        self._dataPath = dataPath

    def getRepositoryGroupIds(self, domainId):
        lxml = parse(open(join(self._dataPath, '%s.domain' % domainId)))
        return lxml.xpath("/domain/repositoryGroupId/text()")

    def getRepositoryIds(self, domainId, repositoryGroupId=None):
        result = []
        allIds = self.getRepositoryGroupIds(domainId) if repositoryGroupId is None else [repositoryGroupId]
        for repositoryGroupId in allIds:
            lxml = parse(open(join(self._dataPath, '%s.%s.repositoryGroup' % (domainId, repositoryGroupId))))
            result.extend(lxml.xpath("/repositoryGroup/repositoryId/text()"))
        return result

    def getRepositoryGroupId(self, domainId, repositoryId):
        lxml = parse(open(join(self._dataPath, '%s.%s.repository' % (domainId, repositoryId))))
        return lxml.xpath("/repository/repositoryGroupId/text()")[0]

    def getRepositoryAsXml(self, domainId, repositoryId):
        m = XMLHEADER.match(open(join(self._dataPath, '%s.%s.repository' % (domainId, repositoryId))).read())
        return m.groupdict()['body']

    def getRepositories(self, domainId, repositoryGroupId=None):
        repositoryIds = self.getRepositoryIds(domainId=domainId, repositoryGroupId=repositoryGroupId)
        yield '<GetRepositories>'
        for repositoryId in repositoryIds:
            yield self.getRepositoryAsXml(domainId=domainId, repositoryId=repositoryId)
        yield '</GetRepositories>'

    
