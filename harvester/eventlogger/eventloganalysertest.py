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
#
#$Date: 2007-04-16 15:36:24 +0200 (Mon, 16 Apr 2007) $ $Revision: 4825 $

import unittest
from eventloganalyser import EventLogAnalyser
from cStringIO import StringIO

class EventLogAnalyserTest(unittest.TestCase):
	def setUp(self):
		self.analyser = EventLogAnalyser()
		
	def testSucces(self):
		self.analyser.analyse(['[2005-08-24 00:00:00]\tSUCCES\t[id]\tHarvester/Uploaded/Deleted/Total\n',
		'[2005-08-19 20:00:00.123]\tSUCCES\t[repository_key]\tHarvester/Uploaded/Deleted/Total\n',
		'[2005-08-20 20:00:00.456]\tSUCCES\t[repository_key]\tHarvester/Uploaded/Deleted/Total\n',
		'[2005-08-21 20:00:00]\tSUCCES\t[repository_key]\tHarvester/Uploaded/Deleted/Total\n'
		])
		self.assertEquals([('id', '2005-08-24 00:00:00', 0),('repository_key', '2005-08-21 20:00:00', 0)], self.analyser.results())
		self.assertEquals('2005-08-21 20:00:00', self.analyser.repositoryevent('repository_key').getLastSuccesDate())
		self.assertEquals('2005-08-20 20:00:00.456', self.analyser.repositoryevent('repository_key').getPreviousSuccesDate())
		self.assertEquals('', self.analyser.repositoryevent('id').getPreviousSuccesDate())
		
	def testSomeFailures(self):
		self.analyser.analyse(['[2005-08-24 00:00:00]\tSUCCES\t[id]\tHarvested/Uploaded/Deleted/Total: 200/199/1/1542\n',
		'[2005-08-20 20:00:00]\tERROR\t[repository_key]\tVery very wrong',
		'[2005-08-21 20:00:00]\tSUCCES\t[repository_key]\tHarvested/Uploaded/Deleted/Total: 134/134/0/334, Done, Resum\n',
		'[2005-08-22 20:00:00]\tERROR\t[repository_key]\texceptions.Exception "BLA DIE BLA"',
		'[2005-08-23 20:00:00]\tERROR\t[repository_key]\tEcht niet goed',
		'[2005-08-23 20:00:00]\tERROR\t[id]\tEcht niet goed',
		'[2005-08-24 20:00:00]\tERROR\t[repository_key]\tVery very wrong'
		])
		self.assertEquals([('id', '2005-08-24 00:00:00', 0),('repository_key', '2005-08-21 20:00:00', 3)], self.analyser.results())
		self.assertEquals(('134','134','0','334'),self.analyser.numbers('repository_key'))
		self.assertEquals(('200', '199', '1', '1542'),self.analyser.numbers('id'))
		self.assertEquals([],self.analyser.repositoryevent('id').getErrors())
		self.assertEquals([('2005-08-22 20:00:00', 'exceptions.Exception "BLA DIE BLA"'), 
			('2005-08-23 20:00:00', 'Echt niet goed'), 
			('2005-08-24 20:00:00', 'Very very wrong')],
			self.analyser.repositoryevent('repository_key').getErrors())
		self.assertEquals([('2005-08-23 20:00:00', 'Echt niet goed')],self.analyser.repositoryevent('id').getPreviousErrors())
		self.assertEquals([('2005-08-20 20:00:00', 'Very very wrong')],self.analyser.repositoryevent('repository_key').getPreviousErrors())
		
	def testSomeMoreFailures(self):
		self.analyser.analyse(['[2005-08-20 20:00:00]\tERROR\t[repository_key]\tVery very wrong',
		'[2005-08-22 20:00:00]\tERROR\t[repository_key]\texceptions.Exception "BLA DIE BLA"',
		'[2005-08-23 20:00:00]\tERROR\t[repository_key]\tEcht niet goed',
		'[2005-08-24 20:00:00]\tERROR\t[repository_key]\tVery very wrong'
		])
		self.assertEquals([('repository_key', None, 4)], self.analyser.results())
		
	def testAsXML(self):
		self.analyser.analyse([
		'[2005-08-22 00:00:00]\tSUCCES\t[id]\tHarvested/Uploaded/Deleted/Total: 8/4/3/16\n',
		'[2005-08-24 00:00:00]\tSUCCES\t[id]\tHarvested/Uploaded/Deleted/Total: 8/4/3/20\n',
		'[2005-08-20 20:00:00]\tERROR\t[repository_key]\tVery very wrong',
		'[2005-08-21 20:00:00]\tSUCCES\t[repository_key]\tHarvested/Uploaded/Deleted/Total: 4/3/2/10\n',
		'[2005-08-22 20:00:00]\tERROR\t[repository_key]\texceptions.Exception "BLA DIE BLA"',
		'[2005-08-23 20:00:00]\tERROR\t[repository_key]\tEcht niet goed',
		'[2005-08-23 20:00:00]\tERROR\t[id]\tEcht niet goed',
		'[2005-08-24 20:00:00]\tERROR\t[repository_key]\t<&Very&> "very" \'wrong\'',
		'[2005-08-23 20:00:00]\tERROR\t[repository_wrong]\tEcht niet goed',
		])
		stream = StringIO()
		self.analyser.asXml(stream)
		self.assertEquals("""<?xml version="1.0"?>
<log>
	<repository key="id">
		<lastsuccesdate>2005-08-24 00:00:00</lastsuccesdate>
		<numbers harvested="8" uploaded="4" deleted="3" total="20"/>
		<errors nr="0">
		</errors>
		<previoussuccesdate>2005-08-22 00:00:00</previoussuccesdate>
		<previouserrors nr="1">
			<error date="2005-08-23 20:00:00">Echt niet goed</error>
		</previouserrors>
	</repository>
	<repository key="repository_key">
		<lastsuccesdate>2005-08-21 20:00:00</lastsuccesdate>
		<numbers harvested="4" uploaded="3" deleted="2" total="10"/>
		<errors nr="3">
			<error date="2005-08-22 20:00:00">exceptions.Exception "BLA DIE BLA"</error>
			<error date="2005-08-23 20:00:00">Echt niet goed</error>
			<error date="2005-08-24 20:00:00">&lt;&amp;Very&amp;&gt; "very" 'wrong'</error>
		</errors>
		<previoussuccesdate></previoussuccesdate>
		<previouserrors nr="1">
			<error date="2005-08-20 20:00:00">Very very wrong</error>
		</previouserrors>
	</repository>
	<repository key="repository_wrong">
		<lastsuccesdate></lastsuccesdate>
		<errors nr="1">
			<error date="2005-08-23 20:00:00">Echt niet goed</error>
		</errors>
		<previoussuccesdate></previoussuccesdate>
		<previouserrors nr="0">
		</previouserrors>
	</repository>
</log>""", stream.getvalue())
		

if __name__ == '__main__':
	unittest.main()
