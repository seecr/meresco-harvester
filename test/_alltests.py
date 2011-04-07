#!/usr/bin/env python
## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#
#    This file is part of "Meresco Harvester"
#
#    "Meresco Harvester" is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    "Meresco Harvester" is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with "Meresco Harvester"; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from os import getuid
assert getuid() != 0, "Do not run tests as 'root'"

from os import system                             #DO_NOT_DISTRIBUTE
from sys import path as sysPath                   #DO_NOT_DISTRIBUTE
system('find .. -name "*.pyc" | xargs rm -f')     #DO_NOT_DISTRIBUTE
                                                  #DO_NOT_DISTRIBUTE
from glob import glob                             #DO_NOT_DISTRIBUTE
for path in glob('../deps.d/*'):                  #DO_NOT_DISTRIBUTE
    sysPath.insert(0, path)                       #DO_NOT_DISTRIBUTE
sysPath.insert(0,'..')                            #DO_NOT_DISTRIBUTE

import unittest

from amaraforharvestertest import AmaraForHarvesterTest
from cacherecordtest import CacheRecordTest
from deleteidstest import DeleteIdsTest
from disallowfileplugintest import DisallowFilePluginTest
from eventloggertest import EventLoggerTest
from filesystemuploadtest import FileSystemUploaderTest
from harvestactiontest import HarvestActionTest
from harvesterlogtest import HarvesterLogTest
from harvestertest import HarvesterTest
from idstest import IdsTest
from mappingtest import MappingTest
from oairequesttest import OaiRequestTest
from onlineharvesttest import OnlineHarvestTest
from repositorystatustest import RepositoryStatusTest
from repositorytest import RepositoryTest
from saharagettest import SaharaGetTest
from smoothactiontest import SmoothActionTest
from sruupdateuploadertest import SruUpdateUploaderTest
from statetest import StateTest
from statustest import StatusTest
from throughputanalysertest import ThroughputAnalyserTest
from timedprocesstest import TimedProcessTest
from timeslottest import TimeslotTest
from toolstest import ToolsTest

from controlpanel.repositorydatatest import RepositoryDataTest

if __name__ == '__main__':
        unittest.main()

