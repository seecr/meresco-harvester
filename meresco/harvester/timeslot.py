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
# Copyright (C) 2011, 2015, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2015, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
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

import datetime
import time
import re

class Timeslot(object):
	def __init__(self, string):
		self._begin, self._end = list(map(_parse, string.split('-')))

	beginweek = property(lambda self: str(self._begin[0]))
	beginday = property(lambda self: str(self._begin[1]))
	beginhour = property(lambda self: str(self._begin[2]))
	beginminute = property(lambda self: str(self._begin[3]))
	endweek = property(lambda self: str(self._end[0]))
	endday = property(lambda self: str(self._end[1]))
	endhour = property(lambda self: str(self._end[2]))
	endminute = property(lambda self: str(self._end[3]))

	def __str__(self):
		return format(self._begin) + '-' + format(self._end)

	def valid(self):
		return self._begin < self._end

	def areWeWithinTimeslot(self, dateTuple = time.localtime()[:5]):
		date = datetime.datetime(*dateTuple)
		date = date.isocalendar()[1:] + (date.hour, date.minute)
		return self._begin <= date <= self._end

class Wildcard(object):
    def __eq__(self, arg): return True
    def __lt__(self, arg): return True
    def __le__(self, arg): return True
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

