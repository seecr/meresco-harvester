#!/usr/bin/env python
## begin license ##
#
#    "Sahara" consists of two subsystems, namely an OAI-harvester and a web-control panel.
#    "Sahara" is developed for SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006,2007 SURFnet B.V. http://www.surfnet.nl
#
#    This file is part of "Sahara"
#
#    "Sahara" is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    "Sahara" is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with "Sahara"; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
#
# $Id: saharaget.py 4825 2007-04-16 13:36:24Z TJ $

from cq2utils.wrappers import wrapp
from repository import Repository
from cq2utils import binderytools
from urllib import urlencode
from target import Target
from mapping import Mapping

class SaharaGet:
	def __init__(self, saharaurl, doSetActionDone=True):
		self.doSetActionDone = doSetActionDone
		self.saharaurl = saharaurl
		
	def getRepository(self, domainId, repositoryId):
		response = self._get(verb = 'GetRepository',
									domainId = domainId,
									repositoryId = repositoryId)
		xml = response.saharaget.GetRepository.repository
		repository = Repository(domainId, repositoryId)
		repository.fill(self, xml)
		repository._copyOldStuff()
		return repository
	
	def getTarget(self, domainId, targetId):
		response = self._get(verb = 'GetTarget',
									domainId = domainId,
									targetId = targetId)
		xml = response.saharaget.GetTarget.target
		target = Target(targetId)
		target.fill(self, xml)
		target.domainId = domainId
		return target
	
	def getMapping(self, domainId, mappingId):
		response = self._get(verb = 'GetMapping',
									domainId = domainId,
									mappingId = mappingId)
		xml = response.saharaget.GetMapping.mapping
		mapping = Mapping(mappingId)
		mapping.fill(self, xml)
		return mapping
	
	def getRepositoryIds(self, domainId):
		response = self._get(verb = 'GetRepositories',
									domainId = domainId)
		repositories = response.saharaget.GetRepositories.repository
		result = []
		for repository in repositories:
			result.append(str(repository.id))
		return result
	
	def repositoryActionDone(self, domainId, repositoryId):
		if self.doSetActionDone:
			saharageturl = '%s/setactiondone?' % self.saharaurl + \
				urlencode({'domainId': domainId, 'repositoryId': repositoryId})
			binderytools.bind_uri(saharageturl)

	def _get(self, **kwargs):
		response = self._read(**kwargs)
		if str(response.saharaget.error.code):
			raise SaharaGetException(str(response.saharaget.error))
		return response
		
	def _read(self, **kwargs):
		saharageturl = '%s/saharaget?%s' % (self.saharaurl, urlencode(kwargs))
		return wrapp(binderytools.bind_uri(saharageturl))
		
class SaharaGetException(Exception):
	pass
