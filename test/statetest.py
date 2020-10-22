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
# Copyright (C) 2010-2012, 2015, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012, 2015, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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
from meresco.components.json import JsonDict
from meresco.harvester.state import State, getResumptionToken, getStartDate
from seecr.test import SeecrTestCase
from seecr.zulutime import ZuluTime

from contextlib import contextmanager
@contextmanager
def _State(*args, **kwargs):
    _state = State(*args, **kwargs)
    try:
        yield _state
    finally:
        _state.close()


class StateTest(SeecrTestCase):
    def assertRepoStats(self, expected):
        with open(join(self.tempdir, 'repo.stats')) as fp:
            self.assertEqual(expected,fp.read())

    def testReadStartDateFromLogLine(self):
        logline = ' Started: 2005-01-02 16:12:56, Harvested/Uploaded: 199/ 200, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45230'
        self.assertEqual('2005-01-02', getStartDate(logline))
        logline = 'Started: 2005-03-23 16:12:56, Harvested/Uploaded: 199/ 200, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45230'
        self.assertEqual('2005-03-23', getStartDate(logline))
        logline='Started: 1999-12-01 16:37:41, Harvested/Uploaded: 113/  113, Done: 2004-12-31 16:39:15, ResumptionToken: ga+hier+verder\n'
        self.assertEqual('1999-12-01', getStartDate(logline))

    def testReadResumptionTokenFromStats(self):
        logline = ' Started: 2005-01-02 16:12:56, Harvested/Uploaded: 199/ 200, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45230'
        self.assertEqual('^^^oai_dc^45230', getResumptionToken(logline))
        logline='Started: 1999-12-01 16:37:41, Harvested/Uploaded:   113/  113, Error: XXX\n'
        self.assertEqual(None, getResumptionToken(logline))
        logline = ' Started: 2005-01-02 16:12:56, Harvested/Uploaded: 199/ 200, Done: 2005-01-02 16:13:45, ResumptionToken: None'
        self.assertEqual(None, getResumptionToken(logline))
        logline = ' Started: 2005-01-02 16:12:56, Harvested/Uploaded: 199/ 200, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^45230\n'
        self.assertEqual('^^^oai_dc^45230', getResumptionToken(logline))
        logline = ' Started: 2005-01-02 16:12:56, Harvested/Uploaded: 199/ 200, Done: 2005-01-02 16:13:45, ResumptionToken: ^^^oai_dc^452 30\n'
        self.assertEqual('^^^oai_dc^452 30', getResumptionToken(logline))

    def testNoRepeatedNewlines(self):
        with _State(self.tempdir, 'repository'):
            pass
        with open(join(self.tempdir, 'repository.stats')) as fp:
            data = fp.read()
        self.assertEqual('', data)

        with _State(self.tempdir, 'repository') as s:
            s._write('line')
        with open(join(self.tempdir, 'repository.stats')) as fp:
            data = fp.read()
        self.assertEqual('line\n', data)

        with _State(self.tempdir, 'repository'):
            pass
        with open(join(self.tempdir, 'repository.stats')) as fp:
            data = fp.read()
        self.assertEqual('line\n', data)

    def testStartDateFromLastFirstBatch(self):
        with open(join(self.tempdir, 'repository.stats'), 'w') as f:
            f.write('''Started: 2005-01-02 16:08:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-02 16:09:45, ResumptionToken: ^^^oai_dc^45230
Started: 2005-01-03 16:10:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-03 16:11:45, ResumptionToken:
Started: 2005-01-04 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-04 16:13:45, ResumptionToken: ^^^oai_dc^45231
Started: 2005-01-05 16:14:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-05 16:15:45, ResumptionToken: ^^^oai_dc^45232
Started: 2005-01-06 16:16:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-06 16:17:45, ResumptionToken:
''')
        with _State(self.tempdir, 'repository') as s:
            self.assertEqual('2005-01-04', s.from_)

    def testStartDateFromLastFirstBatchWihoutResumptionToken(self):
        with open(join(self.tempdir, 'repository.stats'), 'w') as f:
            f.write('''Started: 2005-01-02 16:08:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-02 16:09:45, ResumptionToken: ^^^oai_dc^45230
Started: 2005-01-03 16:10:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-03 16:11:45, ResumptionToken:
Started: 2005-01-04 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-04 16:13:45, ResumptionToken: ^^^oai_dc^45231
Started: 2005-01-05 16:14:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-05 16:15:45, ResumptionToken: ^^^oai_dc^45232
Started: 2005-01-06 16:16:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-06 16:17:45, ResumptionToken:
Started: 2005-01-07 16:18:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-07 16:19:45, ResumptionToken:
''')
        with _State(self.tempdir, 'repository') as s:
            self.assertEqual('2005-01-07', s.from_)

    def testStartDateFromNewFromFile(self):
        with open(join(self.tempdir, 'repository.stats'), 'w') as f:
            f.write('''Started: 2005-01-03 16:10:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-03 16:11:45, ResumptionToken:
Started: 2005-01-04 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-04 16:13:45, ResumptionToken: ^^^oai_dc^45231
Started: 2005-01-06 16:16:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-06 16:17:45, ResumptionToken:
''')

        with open(join(self.tempdir, 'repository.next'), 'w') as f:
            f.write('{"from": "2012-01-01T09:00:00Z"}')

        with _State(self.tempdir, 'repository') as s:
            self.assertEqual('2012-01-01T09:00:00Z', s.from_)

    def testLastSuccessfulHarvestTime(self):
        with open(join(self.tempdir, 'repository.next'), 'w') as f:
            f.write('{"from": "2020-12-21T01:42:24.403578+01:00"}')
        s = State(self.tempdir, 'repository')
        self.assertEqual(ZuluTime('2020-12-21T00:42:24Z').zulu(), s.getLastSuccessfulHarvestTime().zulu())

    def testNoStartDateIfLastLogLineIsDeletedIds(self):
        with open(join(self.tempdir, 'repository.stats'), 'w') as f:
            f.write('''Started: 2005-01-03 16:10:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-03 16:11:45, ResumptionToken:
Started: 2005-01-04 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-04 16:13:45, ResumptionToken: ^^^oai_dc^45231
Started: 2005-01-06 16:16:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-06 16:17:45, ResumptionToken:
Started: 2005-01-07 16:18:56, Harvested/Uploaded/Deleted/Total: 0/0/0/0, Done: Deleted all ids
''')

        with _State(self.tempdir, 'repository') as s:
            self.assertEqual(None, s.from_)
            self.assertEqual(None, s.token)

        # and now with 'ids' misspelled as used to be the case
        with open(join(self.tempdir, 'repository.stats'), 'w') as f:
            f.write('''Started: 2005-01-03 16:10:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-03 16:11:45, ResumptionToken:
Started: 2005-01-04 16:12:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-04 16:13:45, ResumptionToken: ^^^oai_dc^45231
Started: 2005-01-06 16:16:56, Harvested/Uploaded/Deleted/Total: 1/2/3/4, Done: 2005-01-06 16:17:45, ResumptionToken:
Started: 2005-01-07 16:18:56, Harvested/Uploaded/Deleted/Total: 0/0/0/0, Done: Deleted all id's
''')

        with _State(self.tempdir, 'repository') as s:
            self.assertEqual(None, s.from_)
            self.assertEqual(None, s.token)

    def testMarkHarvested(self):
        with _State(self.tempdir, 'repo') as state:
            state.getZTime = lambda: ZuluTime('2012-08-13T12:15:00Z')
            state.markStarted()
            state.markHarvested("9999/9999/9999/9999", "resumptionToken", "2012-08-13T12:14:00")

        self.assertRepoStats('Started: 2012-08-13 12:15:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-13 12:15:00, ResumptionToken: resumptionToken\n')
        self.assertEqual({"from": "2012-08-13T12:14:00", "resumptionToken": "resumptionToken", 'lastSuccessfulHarvest':'2012-08-13T12:15:00Z'}, JsonDict.load(join(self.tempdir, 'repo.next')))
        self.assertEqual({"changedate": "2012-08-13 12:15:00", "status": "Ok", "message": ""}, JsonDict.load(join(self.tempdir, 'repo.running')))

        with _State(self.tempdir, 'repo') as state:
            self.assertEqual('2012-08-13T12:14:00', state.from_)
            self.assertEqual('resumptionToken', state.token)

            state.getZTime = lambda: ZuluTime('2012-08-13T12:17:00Z')
            state.markStarted()
            state.markHarvested("9999/9999/9999/9999", "newToken", "2012-08-13T12:16:00Z")

        self.assertRepoStats("""Started: 2012-08-13 12:15:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-13 12:15:00, ResumptionToken: resumptionToken
Started: 2012-08-13 12:17:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-13 12:17:00, ResumptionToken: newToken
""")
        self.assertEqual({"from": "2012-08-13T12:14:00", "resumptionToken": "newToken", 'lastSuccessfulHarvest':'2012-08-13T12:17:00Z'}, JsonDict.load(join(self.tempdir, 'repo.next')))
        self.assertEqual(
            {"changedate": "2012-08-13 12:15:00", "status": "Ok", "message": ""},
            JsonDict.load(join(self.tempdir, 'repo.running')))

        with _State(self.tempdir, 'repo') as state:
            self.assertEqual('2012-08-13T12:14:00', state.from_)
            self.assertEqual('newToken', state.token)
            state.getZTime = lambda: ZuluTime('2012-08-13T12:20:00Z')
            state.verbose = True
            state.markStarted()
            state.markHarvested("9999/9999/9999/9999", token=None, responseDate="2012-08-13T12:19:00Z")

        self.assertEqual({"from": "2012-08-13T12:14:00", "resumptionToken": "", 'lastSuccessfulHarvest':'2012-08-13T12:20:00Z'}, JsonDict.load(join(self.tempdir, 'repo.next')))
        self.assertEqual({"changedate": "2012-08-13 12:15:00", "status": "Ok", "message": ""}, JsonDict.load(join(self.tempdir, 'repo.running')))

    def testMarkDeleted(self):
        with _State(self.tempdir, 'repo') as state:
            state.getZTime = lambda: ZuluTime('2012-08-13T12:15:00Z')
            state.markStarted()
            state.markHarvested("9999/9999/9999/9999", "resumptionToken", "2012-08-13T12:14:00")

        self.assertRepoStats('Started: 2012-08-13 12:15:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-13 12:15:00, ResumptionToken: resumptionToken\n')
        self.assertEqual(
            {"from": "2012-08-13T12:14:00", "resumptionToken": "resumptionToken", 'lastSuccessfulHarvest':'2012-08-13T12:15:00Z'},
            JsonDict.load(join(self.tempdir, 'repo.next')))

        self.assertEqual({"changedate": "2012-08-13 12:15:00", "status": "Ok", "message": ""}, JsonDict.load(join(self.tempdir, 'repo.running')))

        with _State(self.tempdir, 'repo') as state:
            state.getZTime = lambda: ZuluTime('2012-08-13T12:17:00Z')
            state.markDeleted()

        self.assertRepoStats("""Started: 2012-08-13 12:15:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-13 12:15:00, ResumptionToken: resumptionToken
Started: 2012-08-13 12:17:00, Harvested/Uploaded/Deleted/Total: 0/0/0/0, Done: Deleted all ids.
""")
        self.assertEqual({"from": "", "resumptionToken": "", 'lastSuccessfulHarvest':None}, JsonDict.load(join(self.tempdir, 'repo.next')))
        self.assertEqual({"changedate": "2012-08-13 12:15:00", "status": "Ok", "message": ""}, JsonDict.load(join(self.tempdir, 'repo.running')))

    def testSetToLastCleanState(self):
        with _State(self.tempdir, 'repo') as state:
            state.getZTime = lambda: ZuluTime('2012-08-13T12:15:00Z')
            state.markStarted()
            state.markHarvested("9999/9999/9999/9999", "", "2012-08-13T12:14:00")
        with _State(self.tempdir, 'repo') as state:
            state.getZTime = lambda: ZuluTime('2012-08-14T12:17:00Z')
            state.markStarted()
            state.markHarvested("9999/9999/9999/9999", "resumptionToken", "2012-08-14T12:16:00")
        with _State(self.tempdir, 'repo') as state:
            state.getZTime = lambda: ZuluTime('2012-08-15T12:19:00Z')
            state.setToLastCleanState()
        self.assertRepoStats("""Started: 2012-08-13 12:15:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-13 12:15:00, ResumptionToken: \nStarted: 2012-08-14 12:17:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-14 12:17:00, ResumptionToken: resumptionToken
Started: 2012-08-15 12:19:00, Done: Reset to last clean state. ResumptionToken: \n""")
        self.assertEqual(
            {"from": "2012-08-14T12:16:00", "resumptionToken": "", 'lastSuccessfulHarvest':'2012-08-15T12:19:00Z'},
            JsonDict.load(join(self.tempdir, 'repo.next')))

    def testMarkException(self):
        with _State(self.tempdir, 'repo') as state:
            state.getZTime = lambda: ZuluTime('2012-08-13T12:15:00Z')
            state.markStarted()
            state.markHarvested("9999/9999/9999/9999", "resumptionToken", "2012-08-13T12:14:00")

        self.assertRepoStats('Started: 2012-08-13 12:15:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-13 12:15:00, ResumptionToken: resumptionToken\n')
        self.assertEqual({"from": "2012-08-13T12:14:00", "resumptionToken": "resumptionToken", 'lastSuccessfulHarvest':'2012-08-13T12:15:00Z'}, JsonDict.load(join(self.tempdir, 'repo.next')))
        self.assertEqual(
            {"changedate": "2012-08-13 12:15:00", "status": "Ok", "message": ""},
            JsonDict.load(join(self.tempdir, 'repo.running')))

        with _State(self.tempdir, 'repo') as state:
            state.getZTime = lambda: ZuluTime('2012-08-13T12:17:00Z')
            state.markStarted()
            try:
                raise ValueError("whatever")
            except:
                exType, exValue, exTraceback = exc_info()
                state.markException(exType, exValue, "9999/9999/9999/9999")
        self.assertRepoStats("""Started: 2012-08-13 12:15:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Done: 2012-08-13 12:15:00, ResumptionToken: resumptionToken
Started: 2012-08-13 12:17:00, Harvested/Uploaded/Deleted/Total: 9999/9999/9999/9999, Error: <class 'ValueError'>: whatever
""")
        self.assertEqual(
            {"changedate": "2012-08-13 12:17:00", "status": "Error", "message": "whatever"},
            JsonDict.load(join(self.tempdir, 'repo.running')))

    def testMarkHarvesterAfterExceptionChange(self):
        with _State(self.tempdir, 'repo') as state:
            state.getZTime = lambda: ZuluTime('2012-08-13T12:15:00Z')
            state.markStarted()
            try:
                raise ValueError("whatever")
            except:
                exType, exValue, exTraceback = exc_info()
                state.markException(exType, exValue, "9999/9999/9999/9999")
        self.assertEqual(
            {"changedate": "2012-08-13 12:15:00", "status": "Error", "message": "whatever"},
            JsonDict.load(join(self.tempdir, 'repo.running')))

        with _State(self.tempdir, 'repo') as state:
            state.getZTime = lambda: ZuluTime('2012-08-13T12:17:00Z')
            state.markStarted()
            state.markHarvested("9999/9999/9999/9999", "resumptionToken", "2012-08-13T12:14:00")
        self.assertEqual(
            {"changedate": "2012-08-13 12:17:00", "status": "Ok", "message": ""},
            JsonDict.load(join(self.tempdir, 'repo.running')))

    def testMarkDeletedAfterExceptionChange(self):
        with _State(self.tempdir, 'repo') as state:
            state.getZTime = lambda: ZuluTime('2012-08-13T12:15:00Z')
            state.markStarted()
            try:
                raise ValueError("whatever")
            except:
                exType, exValue, exTraceback = exc_info()
                state.markException(exType, exValue, "9999/9999/9999/9999")
        self.assertEqual(
            {"changedate": "2012-08-13 12:15:00", "status": "Error", "message": "whatever"},
            JsonDict.load(join(self.tempdir, 'repo.running')))

        with _State(self.tempdir, 'repo') as state:
            state.getZTime = lambda: ZuluTime('2012-08-13T12:17:00Z')
            state.markStarted()
            state.markDeleted()
        self.assertEqual(
            {"changedate": "2012-08-13 12:17:00", "status": "Ok", "message": ""},
            JsonDict.load(join(self.tempdir, 'repo.running')))

    def testMarkExceptionChange(self):
        with _State(self.tempdir, 'repo') as state:
            state.getZTime = lambda: ZuluTime('2012-08-13T12:15:00Z')
            state.markStarted()
            try:
                raise ValueError("the same exception")
            except:
                exType, exValue, exTraceback = exc_info()
                state.markException(exType, exValue, "9999/9999/9999/9999")
        self.assertEqual(
            {"changedate": "2012-08-13 12:15:00", "status": "Error", "message": "the same exception"},
            JsonDict.load(join(self.tempdir, 'repo.running')))

        with _State(self.tempdir, 'repo') as state:
            state.getZTime = lambda: ZuluTime('2012-08-13T12:17:00Z')
            state.markStarted()
            try:
                raise ValueError("the same exception")
            except:
                exType, exValue, exTraceback = exc_info()
                state.markException(exType, exValue, "9999/9999/9999/9999")
        self.assertEqual(
            {"changedate": "2012-08-13 12:15:00", "status": "Error", "message": "the same exception"},
            JsonDict.load(join(self.tempdir, 'repo.running')))

        with _State(self.tempdir, 'repo') as state:
            state.getZTime = lambda: ZuluTime('2012-08-13T12:19:00Z')
            state.markStarted()
            try:
                raise ValueError("the other exception")
            except:
                exType, exValue, exTraceback = exc_info()
                state.markException(exType, exValue, "9999/9999/9999/9999")
        self.assertEqual(
            {"changedate": "2012-08-13 12:19:00", "status": "Error", "message": "the other exception"},
            JsonDict.load(join(self.tempdir, 'repo.running')))

    def testGetLastSuccessfulHarvestTime(self):
        with _State(self.tempdir, 'repo') as state:
            self.assertEqual(None, state.from_)
            self.assertEqual(None, state.lastSuccessfulHarvest)

            self.assertEqual(None, state.getLastSuccessfulHarvestTime())

            state.from_ = "2019-01-01"
            self.assertEqual(ZuluTime("2019-01-01T00:00:00Z"), state.getLastSuccessfulHarvestTime())


