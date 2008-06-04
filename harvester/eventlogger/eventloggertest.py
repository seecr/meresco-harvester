#!/usr/bin/env python
## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for 
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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
#
# (C) Copyright 2005 Seek You Too B.V. http://www.cq2.nl
#
# $Id: eventloggertest.py 4825 2007-04-16 13:36:24Z TJ $
#

import unittest,os,re
from eventlogger import StreamEventLogger, EventLogger, LOGLINE_RE

EVENTLOGFILE = '/tmp/EventLoggerTestFile'
DATELENGTH = 26

class EventLoggerTest(unittest.TestCase):
	def setUp(self):
		os.path.isfile(EVENTLOGFILE) and os.remove(EVENTLOGFILE)
		self.logger = EventLogger(EVENTLOGFILE)
		self.logfile = open(EVENTLOGFILE,'r+')

	def tearDown(self):
		self.logfile.close()
		self.logger.close()
		os.path.isfile(EVENTLOGFILE) and os.remove(EVENTLOGFILE)

	def readLogLine(self):
		line = self.logfile.readline().strip()
		#[2005-08-24 14:08:14] SUCCES   [] Comments
		match = LOGLINE_RE.match(line)
		return match.groups()

	def testLogLine(self):
		self.logger.logLine('SUCCES','Some logline')
		date,event,id,logtext = self.readLogLine()
		#Something like [2005-08-24 14:08:14]
		self.assert_(re.match(r'^\d{4}\-\d{2}\-\d{2} \d{2}\:\d{2}\:\d{2}.\d{3}$',date))
		self.logger.logLine('1234567890', 'comment')
		self.logger.logLine('1', 'Even more comments')
		self.logger.logLine('1 3 5 7', 'Even\r \nmore\n\r\n comments')
		self.logger.logLine('2', 'aab', id='123')
		self.logger.logLine('3', 'bbbccc', id='uu_1234')
		self.logger.logLine('error\terr', 'bbb\tddd', id='uu_234')
		self.assertEquals('1234567890\t[]\tcomment', self.logfile.readline().strip()[DATELENGTH:])
		self.assertEquals('1\t[]\tEven more comments', self.logfile.readline().strip()[DATELENGTH:])
		self.assertEquals('1 3 5 7\t[]\tEven more comments', self.logfile.readline().strip()[DATELENGTH:])
		self.assertEquals('2\t[123]\taab', self.logfile.readline().strip()[DATELENGTH:])
		self.assertEquals('3\t[uu_1234]\tbbbccc', self.logfile.readline().strip()[DATELENGTH:])
		self.assertEquals('error err\t[uu_234]\tbbb ddd', self.logfile.readline().strip()[DATELENGTH:])
		
	def testSucces(self):
		self.logger.succes('really succesful')
		self.logger.succes('really succesful','aa')
		date,event,id,logtext = self.readLogLine()
		self.assertEquals('', id)
		self.assertEquals('SUCCES', event)
		self.assertEquals('really succesful',logtext)
		self.assertEquals('SUCCES\t[aa]\treally succesful', self.logfile.readline().strip()[DATELENGTH:])
		
	def testFail(self):
		self.logger.fail()
		self.logger.fail('uh oh','11')
		self.logger.failure('comm','id')
		self.assertEquals('FAILURE\t[]\t', self.logfile.readline()[DATELENGTH:-1])
		self.assertEquals('FAILURE\t[11]\tuh oh', self.logfile.readline().strip()[DATELENGTH:])
		self.assertEquals('FAILURE\t[id]\tcomm', self.logfile.readline().strip()[DATELENGTH:])
		
	def testError(self):
		self.logger.error()
		self.logger.error('uh oh','11')
		self.logger.error('comm','id')
		self.assertEquals('ERROR\t[]\t', self.logfile.readline()[DATELENGTH:-1])
		self.assertEquals('ERROR\t[11]\tuh oh', self.logfile.readline().strip()[DATELENGTH:])
		self.assertEquals('ERROR\t[id]\tcomm', self.logfile.readline().strip()[DATELENGTH:])
		
	def testTestStreamLog(self):
		logger = StreamEventLogger()
		logger.logLine('BLA','something')
		logger.error('this should not happen.')
		lines = []
		for line in logger:
			lines.append(line.strip()[DATELENGTH:])
		self.assertEquals(['BLA\t[]\tsomething','ERROR\t[]\tthis should not happen.'],lines)
		
	def testLogNone(self):
		logger = StreamEventLogger()
		logger.error(None)
		logger.logLine(None, None)
		lines = []
		for line in logger:
			lines.append(line[DATELENGTH:])
		self.assertEquals(['ERROR\t[]\tNone\n', 'None\t[]\tNone\n'],lines)		
		
if __name__ == '__main__':
	unittest.main()
