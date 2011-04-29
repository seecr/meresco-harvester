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
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
# 
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

from meresco.harvester.state import State, getHarvestedUploadedRecords, getResumptionToken, getStartDate
from cq2utils import CQ2TestCase
from os.path import join

class StateTest(CQ2TestCase):
    def testReadStartDateFromLogLine(self):
        logline = ' Started: 2005-01-02 16:12:56, Harvested/Uploaded: 199/ 200, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45230'
        self.assertEquals('2005-01-02', getStartDate(logline))
        logline = 'Started: 2005-03-23 16:12:56, Harvested/Uploaded: 199/ 200, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45230'
        self.assertEquals('2005-03-23', getStartDate(logline))
        logline='Started: 1999-12-01 16:37:41, Harvested/Uploaded: 113/  113, Done: 2004-12-31 16:39:15, ResumptionToken: ga+hier+verder\n'
        self.assertEquals('1999-12-01', getStartDate(logline))

    def testReadHarvestedRecordsFromLogLine(self):
        logline = ' Started: 2005-01-02 16:12:56, Harvested/Uploaded/Total: 199/ 200/  678, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45230'
        self.assertEquals(('199', '200', '0', '678'), getHarvestedUploadedRecords(logline))

    def testReadDeletedRecordsFromLogLine(self):
        logline = ' Started: 2005-01-02 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45230'
        self.assertEquals(('1', '2', '3', '4'), getHarvestedUploadedRecords(logline))

    def testReadResumptionToken(self):
        logline = ' Started: 2005-01-02 16:12:56, Harvested/Uploaded: 199/ 200, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45230'
        self.assertEquals('^^^oai_dc^45230', getResumptionToken(logline))
        logline='Started: 1999-12-01 16:37:41, Harvested/Uploaded:   113/  113, Error: XXX\n'
        self.assertEqual(None, getResumptionToken(logline))
        logline = ' Started: 2005-01-02 16:12:56, Harvested/Uploaded: 199/ 200, Done: 2005-01-02 16:13:45, ResumptionToken: None'
        self.assertEqual(None, getResumptionToken(logline))
        logline = ' Started: 2005-01-02 16:12:56, Harvested/Uploaded: 199/ 200, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45230\n'
        self.assertEquals('^^^oai_dc^45230', getResumptionToken(logline))
        logline = ' Started: 2005-01-02 16:12:56, Harvested/Uploaded: 199/ 200, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^452 30\n'
        self.assertEquals('^^^oai_dc^452 30', getResumptionToken(logline))

    def testParseInfo(self):
        line = "Started: 2005-04-22 11:48:05, Harvested/Uploaded/Total: 200/201/6600, Done: 2005-04-22 11:48:30, ResumptionToken: slice^33|metadataPrefix^oai_dc|from^1970-01-01"
        harvested, uploaded, deleted, total = getHarvestedUploadedRecords(line)
        self.assertEquals('200', harvested)
        self.assertEquals('201', uploaded)
        self.assertEquals('0', deleted)
        self.assertEquals('6600', total)

    def testLogWithDeletedCount(self):
        line = "Started: 2005-04-22 11:48:05, Harvested/Uploaded/Deleted/Total: 200/195/5/449, Done: 2005-04-22 11:48:30, ResumptionToken: slice^33|metadataPrefix^oai_dc|from^1970-01-01"
        harvested, uploaded, deleted, total = getHarvestedUploadedRecords(line)
        self.assertEquals('200', harvested)
        self.assertEquals('195', uploaded)
        self.assertEquals('5', deleted)
        self.assertEquals('449', total)

    def testFindLastCleanState(self):
        f = open(join(self.tempdir, 'repository.stats'), 'w')
        f.write('''Started: 2005-01-02 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45231
Started: 2005-01-03 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-02 16:13:45, ResumptionToken:
Started: 2005-01-04 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45232
Started: 2005-01-05 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Error: ERROR
Started: 2005-01-06 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45233
Started: 2005-01-07 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45235''')
        f.close()
        s = State(self.tempdir, 'repository')
        l = s._getLastCleanState()
        self.assertEquals('Started: 2005-01-03 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-02 16:13:45, ResumptionToken:\n', l)

    def testFindLastCleanState_whichDoesNotExist(self):
        f = open(join(self.tempdir, 'repository.stats'), 'w')
        f.write('''Started: 2005-01-02 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45231
Started: 2005-01-04 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45232
Started: 2005-01-05 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Error: ERROR
Started: 2005-01-06 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45233
Started: 2005-01-07 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45235''')
        f.close()
        s = State(self.tempdir, 'repository')
        l = s._getLastCleanState()
        self.assertEquals(None, l)

