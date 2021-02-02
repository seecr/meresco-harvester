## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2019-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2019-2021 Stichting Kennisnet https://www.kennisnet.nl
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

from meresco.core import Transparent

class FilterFields(Transparent):
    def __init__(self, fieldDefinitions):
        Transparent.__init__(self)
        self._allowedRepositoryFields = [definition['name'] for definition in fieldDefinitions.get('repository_fields', []) if definition.get('export', False)]

    def getRepositories(self, *args, **kwargs):
        return list(map(self._stripRepository, self.call.getRepositories(*args, **kwargs)))

    def getRepository(self, *args, **kwargs):
        return self._stripRepository(self.call.getRepository(*args, **kwargs))

    def _stripRepository(self, repository):
        result = dict(repository)
        if self._allowedRepositoryFields:
            extra = repository.get('extra', {})
            result['extra'] = dict((k,v) for k,v in list(repository.get('extra', {}).items()) if k in self._allowedRepositoryFields)
            result['extra'] = dict((k, extra.get(k, "")) for k in self._allowedRepositoryFields)
        return result
