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

from eventlogger import LOGLINE_RE
import re
NUMBERS_RE = re.compile(r'.*Harvested/Uploaded/Deleted/Total:\s*(\d+)/(\d+)/(\d+)/(\d+).*')
from xml.sax.saxutils import escape as xmlescape

class RepositoryEvent:
	def __init__(self,id):
		self.id = id
		self.lastSuccesDate = None
		self.previousSuccesDate = None
		self.numbers = None
		self.previousNumbers = None
		self._errors = []
	
	def getLastSuccesDate(self):
		return self.lastSuccesDate or ''

	def getPreviousSuccesDate(self):
		return self.previousSuccesDate or ''
		
	def succes(self, date, comments):
		if date >= self.lastSuccesDate:
			if self.lastSuccesDate >= self.previousSuccesDate:
				self.previousSuccesDate = self.lastSuccesDate
				self.previousNumbers = self.numbers
			self.lastSuccesDate = date
			self._errors = filter(self._after(self.previousSuccesDate), self._errors)
			m = NUMBERS_RE.match(comments)
			self.numbers = m and m.groups() or None
		
	def error(self, date, comments):
		self._errors.append((date, comments))
		
	def _after(self, afterdate):
		return lambda (date,comments):cmp(date, afterdate) >= 0
		
	def getErrors(self):
		return filter(self._after(self.lastSuccesDate),self._errors)
		
	def getPreviousErrors(self):
		all = filter(self._after(self.previousSuccesDate),self._errors)
		return filter(lambda (date,comments):cmp(date,self.lastSuccesDate) < 0, all)
		
	def nrOfErrors(self):
		return len(self.getErrors())
		
	def event(self, event, date, comments):
		if 'SUCCES' == event.strip():
			self.succes(date, comments)
		elif 'ERROR' == event.strip():
			self.error(date, comments)

class EventLogAnalyser:
	def __init__(self):
		self.repositories = {}

	def splitLine(self,line):
		m = LOGLINE_RE.match(line.strip())
		return m and m.groups() or None
	
	def add(self, date, event, id, comments):
		repevent = self.repositories.get(id,RepositoryEvent(id))
		repevent.event(event, date, comments)
		self.repositories[id] = repevent
		
	def numbers(self, id):
		repositoryevent = self.repositoryevent(id)
		return repositoryevent and repositoryevent.numbers or None
		
	def repositoryevent(self, id):
		return self.repositories.get(id,None)
		
	def analyse(self, eventlines):
		events = filter(None,map(self.splitLine, eventlines))
		for date,event,id,comments in events:
			self.add(date,event,id, comments)
		
	def results(self):
		results = map(lambda event:(event.id, event.lastSuccesDate, event.nrOfErrors()), self.repositories.values())
		results.sort()
		return results
		
	def asXml(self, stream):
		stream.write('<?xml version="1.0"?>\n<log>\n')
		repositories = self.repositories.values()
		repositories.sort(lambda a,b:cmp(a.id,b.id))
		for repository in repositories:
			stream.write('\t<repository key="%s">\n'%repository.id)
			stream.write('\t\t<lastsuccesdate>%s</lastsuccesdate>\n'%repository.getLastSuccesDate())
			repository.numbers and stream.write('\t\t<numbers harvested="%s" uploaded="%s" deleted="%s" total="%s"/>\n'%repository.numbers)
			stream.write('\t\t<errors nr="%s">\n'%repository.nrOfErrors())
			for date,comments in repository.getErrors():
				stream.write('\t\t\t<error date="%s">%s</error>\n'%(date,xmlescape(comments)))
			stream.write('\t\t</errors>\n')
			stream.write('\t\t<previoussuccesdate>%s</previoussuccesdate>\n'%repository.getPreviousSuccesDate())
			previousErrors = repository.getPreviousErrors()
			stream.write('\t\t<previouserrors nr="%s">\n'%len(previousErrors))
			for date,comments in previousErrors:
				stream.write('\t\t\t<error date="%s">%s</error>\n'%(date,xmlescape(comments)))
			stream.write('\t\t</previouserrors>\n')
			stream.write('\t</repository>\n')
		stream.write('</log>')
		stream.flush()
	
if __name__ == '__main__':
	import sys
	analyser = EventLogAnalyser()
	analyser.analyse(sys.stdin.readlines())
	analyser.asXml(sys.stdout)
	pass
