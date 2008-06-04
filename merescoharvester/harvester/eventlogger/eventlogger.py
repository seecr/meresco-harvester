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
# $Id: eventlogger.py 4825 2007-04-16 13:36:24Z TJ $
#

import time, re, datetime
from cStringIO import StringIO

LOGLINE_RE=re.compile(r'^\[([^\]]*)\]\t([\w ]+)\t\[([^\]]*)\]\t(.*)$')

class BasicEventLogger:
	def __init__(self, logfile):
		self._logfile = self.openlogfile(logfile)
		
	def close(self):
		if self._logfile:
			self._logfile.close()
			self._logfile = None
			
	def logLine(self, event, comments, id=''):
		self._time()
		self._space()
		self._event(event)
		self._space()
		self._id(id)
		self._space()
		self._comments(comments)
		self._flush()

	def _time(self):
		now = datetime.datetime.now()
		ms = ('%03i'%now.microsecond)[:3]
		self._logfile.write('[' + now.strftime('%Y-%m-%d %H:%M:%S.') + ms + ']')

	def _id(self, id):
		self._logfile.write('[')
		self._writeStripped(id)
		self._logfile.write(']')

	def _event(self,event):
		self._writeStripped(event)
		
	def _comments(self, comments):
		self._writeStripped(comments)
		self._logfile.write('\n')

	def _space(self):
		self._logfile.write('\t')
	
	def _writeStripped(self, aString):
		self._logfile.write(' '.join(str(aString).split()))

	def _flush(self):
		self._logfile.flush()
	
class EventLogger(BasicEventLogger):
	def __init__(self,logfile):
		BasicEventLogger.__init__(self, logfile)
		
	def openlogfile(self, logfile):
		return open(logfile, 'a+')
		
	def succes(self,comments='', id=''):
		self.logLine('SUCCES',comments=comments,id=id)

	def failure(self,comments='', id=''):
		self.logLine('FAILURE',comments=comments,id=id)
	fail = failure

	def error(self,comments='', id=''):
		self.logLine('ERROR',comments=comments,id=id)
		
class StreamEventLogger(EventLogger):
	def __init__(self,stream=None):
		self._stream = stream and stream or StringIO()
		EventLogger.__init__(self, None)
		
	def openlogfile(self, logfile):
		return self._stream
	
	def __iter__(self):
		return StringIO(self._stream.getvalue())
	
class NilEventLogger(EventLogger):
		def __init__(self):
			EventLogger.__init__(self, None)
			
		def openlogfile(self, logfile):
			pass
		
		def logLine(self, event, comments, id=''):
			pass
		
		def close(self):
			pass
