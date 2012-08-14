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

from os.path import join
from sys import exc_info

from meresco.harvester.state import State, getResumptionToken, getStartDate
from seecr.test import SeecrTestCase

class StateTest(SeecrTestCase):
    def testReadStartDateFromLogLine(self):
        logline = ' Started: 2005-01-02 16:12:56, Harvested/Uploaded: 199/ 200, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45230'
        self.assertEquals('2005-01-02', getStartDate(logline))
        logline = 'Started: 2005-03-23 16:12:56, Harvested/Uploaded: 199/ 200, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45230'
        self.assertEquals('2005-03-23', getStartDate(logline))
        logline='Started: 1999-12-01 16:37:41, Harvested/Uploaded: 113/  113, Done: 2004-12-31 16:39:15, ResumptionToken: ga+hier+verder\n'
        self.assertEquals('1999-12-01', getStartDate(logline))

    def testReadResumptionTokenFromStats(self):
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

    def testNoRepeatedNewlines(self):
        s = State(self.tempdir, 'repository')
        s.close()
        data = open(join(self.tempdir, 'repository.stats')).read()
        self.assertEquals('', data)
        s = State(self.tempdir, 'repository')
        s._write('line')
        s.close()
        data = open(join(self.tempdir, 'repository.stats')).read()
        self.assertEquals('line\n', data)
        s = State(self.tempdir, 'repository')
        s.close()
        data = open(join(self.tempdir, 'repository.stats')).read()
        self.assertEquals('line\n', data)

    def testStartDateFromLastFirstBatch(self):
        f = open(join(self.tempdir, 'repository.stats'), 'w')
        f.write('''Started: 2005-01-02 16:08:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-02 16:09:45, ResumptionToken: ^^^oai_dc^45230
Started: 2005-01-03 16:10:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-03 16:11:45, ResumptionToken: 
Started: 2005-01-04 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-04 16:13:45, ResumptionToken: ^^^oai_dc^45231
Started: 2005-01-05 16:14:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-05 16:15:45, ResumptionToken: ^^^oai_dc^45232
Started: 2005-01-06 16:16:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-06 16:17:45, ResumptionToken: 
''')
        f.close()
        s = State(self.tempdir, 'repository')
        self.assertEquals('2005-01-04', s.from_)

    def testStartDateFromLastFirstBatchWihoutResumptionToken(self):
        f = open(join(self.tempdir, 'repository.stats'), 'w')
        f.write('''Started: 2005-01-02 16:08:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-02 16:09:45, ResumptionToken: ^^^oai_dc^45230
Started: 2005-01-03 16:10:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-03 16:11:45, ResumptionToken: 
Started: 2005-01-04 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-04 16:13:45, ResumptionToken: ^^^oai_dc^45231
Started: 2005-01-05 16:14:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-05 16:15:45, ResumptionToken: ^^^oai_dc^45232
Started: 2005-01-06 16:16:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-06 16:17:45, ResumptionToken: 
Started: 2005-01-07 16:18:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-07 16:19:45, ResumptionToken: 
''')
        f.close()
        s = State(self.tempdir, 'repository')
        self.assertEquals('2005-01-07', s.from_)

    def testStartDateFromNewFromFile(self):
        f = open(join(self.tempdir, 'repository.stats'), 'w')
        f.write('''Started: 2005-01-03 16:10:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-03 16:11:45, ResumptionToken: 
Started: 2005-01-04 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-04 16:13:45, ResumptionToken: ^^^oai_dc^45231
Started: 2005-01-06 16:16:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-06 16:17:45, ResumptionToken: 
''')
        f.close()
        
        open(join(self.tempdir, 'repository.next'), 'w').write('{"from": "2012-01-01T09:00:00Z"}')

        s = State(self.tempdir, 'repository')
        self.assertEquals('2012-01-01', s.from_)

    def testNoStartDateIfLastLogLineIsDeletedIds(self):
        f = open(join(self.tempdir, 'repository.stats'), 'w')
        f.write('''Started: 2005-01-03 16:10:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-03 16:11:45, ResumptionToken: 
Started: 2005-01-04 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-04 16:13:45, ResumptionToken: ^^^oai_dc^45231
Started: 2005-01-06 16:16:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-06 16:17:45, ResumptionToken: 
Started: 2005-01-07 16:18:56, Harvested/Uploaded/Deleted/Total: 0/0/0/0, Done: Deleted all ids
''')
        f.close()
        
        s = State(self.tempdir, 'repository')
        self.assertEquals(None, s.from_)
        self.assertEquals(None, s.token)

        # and now with 'ids' misspelled as used to be the case
        f = open(join(self.tempdir, 'repository.stats'), 'w')
        f.write('''Started: 2005-01-03 16:10:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-03 16:11:45, ResumptionToken: 
Started: 2005-01-04 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-04 16:13:45, ResumptionToken: ^^^oai_dc^45231
Started: 2005-01-06 16:16:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-06 16:17:45, ResumptionToken: 
Started: 2005-01-07 16:18:56, Harvested/Uploaded/Deleted/Total: 0/0/0/0, Done: Deleted all id's
''')
        f.close()
        
        s = State(self.tempdir, 'repository')
        self.assertEquals(None, s.from_)
        self.assertEquals(None, s.token)

    def testMarkHarvested(self):
        state = State(self.tempdir, 'repo')
        state._gmtime = lambda: (2012, 8, 13, 12, 15, 0, 0, 0, 0)
        state.markStarted()
        state.markHarvested("9999/9999/9999/9999", "resumptionToken", "2012-08-13T12:14:00")
        state.close()

        self.assertEquals('Started: 2012-08-13 12:15:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-13 12:15:00, ResumptionToken: resumptionToken\n', open(join(self.tempdir, 'repo.stats')).read())
        self.assertEquals('{"from": "2012-08-13T12:14:00", "resumptionToken": "resumptionToken"}', open(join(self.tempdir, 'repo.next')).read())
                
        state = State(self.tempdir, 'repo')
        state._gmtime = lambda: (2012, 8, 13, 12, 17, 0, 0, 0, 0)
        state.markStarted()
        state.markHarvested("9999/9999/9999/9999", "newToken", "2012-08-13T12:16:00Z")
        state.close()

        self.assertEquals("""Started: 2012-08-13 12:15:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-13 12:15:00, ResumptionToken: resumptionToken
Started: 2012-08-13 12:17:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-13 12:17:00, ResumptionToken: newToken
""", open(join(self.tempdir, 'repo.stats')).read())
        self.assertEquals('{"from": "2012-08-13", "resumptionToken": "newToken"}', open(join(self.tempdir, 'repo.next')).read())

    def testMarkDeleted(self):
        state = State(self.tempdir, 'repo')
        state._gmtime = lambda: (2012, 8, 13, 12, 15, 0, 0, 0, 0)
        state.markStarted()
        state.markHarvested("9999/9999/9999/9999", "resumptionToken", "2012-08-13T12:14:00")
        state.close()

        self.assertEquals('Started: 2012-08-13 12:15:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-13 12:15:00, ResumptionToken: resumptionToken\n', open(join(self.tempdir, 'repo.stats')).read())
        self.assertEquals('{"from": "2012-08-13T12:14:00", "resumptionToken": "resumptionToken"}', open(join(self.tempdir, 'repo.next')).read())
                
        state = State(self.tempdir, 'repo')
        state._gmtime = lambda: (2012, 8, 13, 12, 17, 0, 0, 0, 0)
        state.markDeleted()
        state.close()

        self.assertEquals("""Started: 2012-08-13 12:15:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-13 12:15:00, ResumptionToken: resumptionToken
Started: 2012-08-13 12:17:00, Harvested/Uploaded/Deleted/Total: 0/0/0/0, Done: Deleted all ids.
""", open(join(self.tempdir, 'repo.stats')).read())
        self.assertEquals('{"from": "", "resumptionToken": ""}', open(join(self.tempdir, 'repo.next')).read())

    def testSetToLastCleanState(self):
        state = State(self.tempdir, 'repo')
        state._gmtime = lambda: (2012, 8, 13, 12, 15, 0, 0, 0, 0)
        state.markStarted()
        state.markHarvested("9999/9999/9999/9999", "", "2012-08-13T12:14:00")
        state.close()
        state = State(self.tempdir, 'repo')
        state._gmtime = lambda: (2012, 8, 14, 12, 17, 0, 0, 0, 0)
        state.markStarted()
        state.markHarvested("9999/9999/9999/9999", "resumptionToken", "2012-08-14T12:16:00")
        state.close()
        state = State(self.tempdir, 'repo')
        state._gmtime = lambda: (2012, 8, 15, 12, 19, 0, 0, 0, 0)
        state.setToLastCleanState()
        state.close()

        self.assertEquals("""Started: 2012-08-13 12:15:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-13 12:15:00, ResumptionToken: 
Started: 2012-08-14 12:17:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-14 12:17:00, ResumptionToken: resumptionToken
Started: 2012-08-15 12:19:00, Done: Reset to last clean state. ResumptionToken: 
""", open(join(self.tempdir, 'repo.stats')).read())
        self.assertEquals('{"from": "2012-08-14", "resumptionToken": ""}', open(join(self.tempdir, 'repo.next')).read())

    def testMarkException(self):
        state = State(self.tempdir, 'repo')
        state._gmtime = lambda: (2012, 8, 13, 12, 15, 0, 0, 0, 0)
        state.markStarted()
        try:
            raise ValueError("whatever")
        except:
            exType, exValue, exTraceback = exc_info()
            state.markException(exType, exValue, "9999/9999/9999/9999")
        state.close()
        self.assertEquals("""Started: 2012-08-13 12:15:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Error: <type 'exceptions.ValueError'>: whatever
""", open(join(self.tempdir, 'repo.stats')).read())



