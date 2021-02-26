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

from os import getenv
from importlib import import_module

from .harvesterdata import HarvesterData
from .harvesterdataretrieve import HarvesterDataRetrieve

class Environment(object):
    def __init__(self, dataPath):
        self._dataPath = dataPath

    def createHarvesterData(self):
        return HarvesterData(self._dataPath)

    def createHarvesterDataRetrieve(self):
        return HarvesterDataRetrieve()

def createEnvironment(dataPath):
    envModuleName = getenv('MERESCO_HARVESTER_ENVIRONMENT_MODULE', 'meresco.harvester.environment')
    envModule = import_module(envModuleName)
    envClass = getattr(envModule, 'Environment')
    return envClass(dataPath=dataPath)

