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
# Copyright (C) 2013 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.harvester.namespaces import xpath, xpathFirst
from repository import Repository
from urllib import urlencode, urlopen
from lxml.etree import parse
from target import Target
from mapping import Mapping

class SaharaGet(object):
    def __init__(self, saharaurl, doSetActionDone=True):
        self.doSetActionDone = doSetActionDone
        self.saharaurl = saharaurl
        
    def getRepository(self, domainId, repositoryId):
        response = self._get(verb = 'GetRepository',
                                    domainId = domainId,
                                    repositoryId = repositoryId)
        repository = Repository(domainId, repositoryId)
        repository.fill(self, xpathFirst(response, '/sahara:saharaget/sahara:GetRepository/sahara:repository'))
        return repository
    
    def getTarget(self, domainId, targetId):
        response = self._get(verb = 'GetTarget',
                                    domainId = domainId,
                                    targetId = targetId)
        target = Target(targetId)
        target.fill(self, xpathFirst(response, '/sahara:saharaget/sahara:GetTarget/sahara:target'))
        target.domainId = domainId
        return target
    
    def getMapping(self, domainId, mappingId):
        response = self._get(verb = 'GetMapping',
                                    domainId = domainId,
                                    mappingId = mappingId)
        mapping = Mapping(mappingId)
        mapping.fill(self, xpathFirst(response, '/sahara:saharaget/sahara:GetMapping/sahara:mapping'))
        return mapping
    
    def getRepositoryIds(self, domainId):
        response = self._get(verb = 'GetRepositories',
                                    domainId = domainId)
        return xpath(response, '/sahara:saharaget/sahara:GetRepositories/sahara:repository/sahara:id/text()')
    
    def repositoryActionDone(self, domainId, repositoryId):
        if self.doSetActionDone:
            saharageturl = '%s/setactiondone?' % self.saharaurl + \
                urlencode({'domainId': domainId, 'repositoryId': repositoryId})
            binderytools.bind_uri(saharageturl)

    def _get(self, **kwargs):
        response = self._read(**kwargs)
        error = xpathFirst(response, '/sahara:saharaget/sahara:error/text()')
        if error is None:
            return response
        raise SaharaGetException(error)
        
    def _read(self, **kwargs):
        saharageturl = '%s/saharaget?%s' % (self.saharaurl, urlencode(kwargs))
        return parse(urlopen(saharageturl))
        
class SaharaGetException(Exception):
    pass
