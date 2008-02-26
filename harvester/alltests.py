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
# Generated with:
#
# $Id: alltests.py 4825 2007-04-16 13:36:24Z TJ $
#
# on Tue Aug 29 17:13:14 CEST 2006 by sahara
#

import os
os.system('rm -f *.pyc')

import unittest

from cacherecordtest import CacheRecordTest
from classificationtest import ClassificationTest
from deleteidstest import DeleteIdsTest
from filesystemuploadtest import FileSystemUploaderTest
from harvesterlogtest import HarvesterLogTest
from harvestertest import HarvesterTest
from idstest import IdsTest
from mappingtest import MappingTest
from oairequesttest import OAIRequestTest
from onlineharvesttest import OnlineHarvestTest
from repositorystatustest import RepositoryStatusTest
from repositorytest import RepositoryTest
from saharagettest import SaharaGetTest
from smoothactiontest import SmoothActionTest
from sseuploadertest import SSEUploaderTest
from startharvestertest import StartHarvesterTest
from teddyuploadertest import TeddyUploaderTest
from throughputanalysertest import ThroughputAnalyserTest
from timedprocesstest import TimedProcessTest
from vcardtest import VCardTest
from amaraforharvestertest import AmaraForHarvesterTest
from sruupdateuploadertest import SruUpdateUploaderTest

if __name__ == '__main__':
        unittest.main()

