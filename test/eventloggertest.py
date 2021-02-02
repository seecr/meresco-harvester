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
# Copyright (C) 2007-2009, 2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2011, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
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

import re
from os.path import join
from meresco.harvester.eventlogger import StreamEventLogger, EventLogger, LOGLINE_RE, CompositeLogger
from io import StringIO

from seecr.test import SeecrTestCase

DATELENGTH = 26


class EventLoggerTest(SeecrTestCase):
    def setUp(self):
        super(EventLoggerTest, self).setUp()
        self._eventLogFile = join(self.tempdir, 'EventLoggerTestFile')
        self.logger = EventLogger(self._eventLogFile)
        self.logfile = open(self._eventLogFile, 'r+')

    def tearDown(self):
        super(EventLoggerTest, self).tearDown()
        self.logfile.close()
        self.logger.close()

    def readLogLine(self):
        line = self.logfile.readline().strip()
        #[2005-08-24 14:08:14] SUCCES   [] Comments
        match = LOGLINE_RE.match(line)
        return match.groups()

    def testLogLine(self):
        self.logger.logLine('SUCCES','Some logline')
        date,event,id,logtext = self.readLogLine()
        #Something like [2005-08-24 14:08:14]
        self.assertTrue(re.match(r'^\d{4}\-\d{2}\-\d{2} \d{2}\:\d{2}\:\d{2}.\d{3}$',date))
        self.logger.logLine('1234567890', 'comment')
        self.logger.logLine('1', 'Even more comments')
        self.logger.logLine('1 3 5 7', 'Even\r \nmore\n\r\n comments')
        self.logger.logLine('2', 'aab', id='123')
        self.logger.logLine('3', 'bbbccc', id='uu_1234')
        self.logger.logLine('error\terr', 'bbb\tddd', id='uu_234')
        self.assertEqual('1234567890\t[]\tcomment', self.logfile.readline().strip()[DATELENGTH:])
        self.assertEqual('1\t[]\tEven more comments', self.logfile.readline().strip()[DATELENGTH:])
        self.assertEqual('1 3 5 7\t[]\tEven more comments', self.logfile.readline().strip()[DATELENGTH:])
        self.assertEqual('2\t[123]\taab', self.logfile.readline().strip()[DATELENGTH:])
        self.assertEqual('3\t[uu_1234]\tbbbccc', self.logfile.readline().strip()[DATELENGTH:])
        self.assertEqual('error err\t[uu_234]\tbbb ddd', self.logfile.readline().strip()[DATELENGTH:])

    def testSucces(self):
        self.logger.logSuccess('really succesful')
        self.logger.logSuccess('really succesful','aa')
        date,event,id,logtext = self.readLogLine()
        self.assertEqual('', id)
        self.assertEqual('SUCCES', event)
        self.assertEqual('really succesful',logtext)
        self.assertEqual('SUCCES\t[aa]\treally succesful', self.logfile.readline().strip()[DATELENGTH:])

    def testFailure(self):
        self.logger.logFailure()
        self.logger.logFailure('uh oh','11')
        self.logger.logFailure('comm','id')
        self.assertEqual('FAILURE\t[]\t', self.logfile.readline()[DATELENGTH:-1])
        self.assertEqual('FAILURE\t[11]\tuh oh', self.logfile.readline().strip()[DATELENGTH:])
        self.assertEqual('FAILURE\t[id]\tcomm', self.logfile.readline().strip()[DATELENGTH:])

    def testError(self):
        self.logger.logError()
        self.logger.logError('uh oh','11')
        self.logger.logError('comm','id')
        self.assertEqual('ERROR\t[]\t', self.logfile.readline()[DATELENGTH:-1])
        self.assertEqual('ERROR\t[11]\tuh oh', self.logfile.readline().strip()[DATELENGTH:])
        self.assertEqual('ERROR\t[id]\tcomm', self.logfile.readline().strip()[DATELENGTH:])

    def testTestStreamLog(self):
        stream = StringIO()
        logger = StreamEventLogger(stream)
        logger.logLine('BLA','something')
        logger.logError('this should not happen.')
        lines = []
        stream.seek(0)
        for line in stream:
            lines.append(line.strip()[DATELENGTH:])
        self.assertEqual(['BLA\t[]\tsomething','ERROR\t[]\tthis should not happen.'],lines)

    def testLogNone(self):
        stream = StringIO()
        logger = StreamEventLogger(stream)
        logger.logError(None)
        logger.logLine(None, None)
        lines = []
        stream.seek(0)
        for line in stream:
            lines.append(line[DATELENGTH:])
        self.assertEqual(['ERROR\t[]\tNone\n', 'None\t[]\tNone\n'],lines)

    def compositLogger(self):
        stream1 = StringIO()
        stream2 = StringIO()
        log1 = StreamEventLogger(stream1)
        log2 = StreamEventLogger(stream2)
        comp = CompositeLogger([
                (['*'], log1),
                (['ERROR'], log2)
            ])
        return stream1, stream2, comp

    def testCompositeLogger(self):
        stream1, stream2, comp = self.compositLogger()
        comp.logInfo('info', 'id')
        self.assertEqual('', stream2.getvalue())
        self.assertEqual('INFO\t[id]\tinfo\n', stream1.getvalue()[DATELENGTH:])

    def testCompositeLogger2(self):
        stream1, stream2, comp = self.compositLogger()
        comp.logError('error', 'id')
        self.assertEqual('ERROR\t[id]\terror\n', stream1.getvalue()[DATELENGTH:])
        self.assertEqual('ERROR\t[id]\terror\n', stream2.getvalue()[DATELENGTH:])

    def testClearLogfile(self):
        self.logger.logLine('SUCCES','Some logline 1')
        self.logger.close()
        self.logger = EventLogger(self._eventLogFile, maxLogLines=4)
        self.logger.logLine('SUCCES','Some logline 2')
        self.logger.logLine('SUCCES','Some logline 3')
        self.logger.logLine('SUCCES','Some logline 4')
        with open(self._eventLogFile,'r+') as logfile:
            self.assertEqual('SUCCES\t[]\tSome logline 3', logfile.readline().strip()[DATELENGTH:])

        self.logger.logLine('SUCCES','Some logline 5')
        with open(self._eventLogFile,'r+') as logfile:
            self.assertEqual('SUCCES\t[]\tSome logline 3', logfile.readline().strip()[DATELENGTH:])

        self.logger.logLine('SUCCES','Some logline 6')
        with open(self._eventLogFile,'r+') as logfile:
            self.assertEqual('SUCCES\t[]\tSome logline 5', logfile.readline().strip()[DATELENGTH:])
