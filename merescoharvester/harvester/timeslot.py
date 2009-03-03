## begin license ##
#
#    "CQ2 Utils" (cq2utils) is a package with a wide range of valuable tools.
#    Copyright (C) 2005-2008 Seek You Too (CQ2) http://www.cq2.nl
#
#    This file is part of "CQ2 Utils".
#
#    "CQ2 Utils" is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    "CQ2 Utils" is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with "CQ2 Utils"; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
import datetime
import time
import re

class Wildcard:
    def __eq__(self, arg): return True
    def __gt__(self, arg): return True
    def __ge__(self, arg): return True
    def __str__(self): return '*'
    def __repr__(self): return '*'

def _parseField(string):
	if string == '*':
		return Wildcard()
	else:
		return int(string)

class ParseException(Exception):
	pass

_r = re.compile('(\d{1,2}|\*):(\d|\*):(\d{1,2}):(\d{1,2})')
def _parse(txt):
	match = _r.match(txt)
	if not match:
		raise ParseException('Illegal timeslot definition (should be "W[W]*|:D|*:HH:MM"), where W is weeknumber, D is day of week (monday = 0), HH is hours in 24 format, MM is minutes.  Week and weekday can be * (wildcard).')
	return tuple(map(_parseField, match.groups()))

def format(date):
	return ':'.join(map(str, date))

class Timeslot:

	def __init__(self, string):
		self._begin, self._end = map(_parse, string.split('-'))
		self.beginweek = str(self._begin[0])
		self.beginday = str(self._begin[1])
		self.beginhour = str(self._begin[2])
		self.beginminute = str(self._begin[3])
		self.endweek = str(self._end[0])
		self.endday = str(self._end[1])
		self.endhour = str(self._end[2])
		self.endminute = str(self._end[3])

	def __str__(self):
		return format(self._begin) + '-' + format(self._end)

	def valid(self):
		return self._begin < self._end

	def areWeWithinTimeslot(self, dateTuple = time.localtime()[:5]):
		date = datetime.datetime(*dateTuple)
		date = date.isocalendar()[1:] + (date.hour, date.minute)
		return self._begin <= date <= self._end
		
