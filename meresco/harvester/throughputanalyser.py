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

#
#
import re, sys, os
from time import strptime
from datetime import datetime
NUMBERS_RE = re.compile(r'.*Harvested/Uploaded/Deleted/Total:\s*(\d+)/(\d+)/(\d+)/(\d+).*')

from xml.sax.saxutils import escape as escapeXml
from os.path import isfile

def parseToTime(dateString):
    dateList = list((strptime(dateString.split(".")[0],"%Y-%m-%d %H:%M:%S"))[:6])
    dateList.append(int(dateString.split(".")[1][:3]) * 1000)
    date = datetime(*tuple(dateList))
    return date

def diffTime(newest, oldest):
    delta = newest - oldest
    return delta.seconds + delta.microseconds/1000000.0

class ThroughputReport(object):
    def __init__(self):
        self.records = 0
        self.seconds = 0.0

    def add(self, records, seconds):
        self.records += records
        self.seconds += seconds

    def recordsPerSecond(self):
        if self.seconds == 0.0:
            return '-'
        return  "%2.2f" % (self.records / self.seconds)

    def recordsPerDay(self):
        if self.seconds == 0.0:
            return '-'
        return "%2.0f" % (self.records / self.seconds * 24 * 3600)

    def hmsString(self):
        hours = int(self.seconds) / 3600
        minutes = int(self.seconds) % 3600 / 60
        seconds = int(self.seconds) % 60
        return "%02i:%02i:%02i" % (hours, minutes, seconds)


class ThroughputAnalyser(object):
    def __init__(self, eventpath):
        self.eventpath = eventpath

    def analyse(self, repositoryNames, dateSince):
        report = ThroughputReport()
        for name in repositoryNames:
            report.add(*self._analyseRepository(name, dateSince))
        return report

    def _analyseRepository(self, repositoryName, dateSince):
        reportfile = os.path.join(self.eventpath, repositoryName + '.events')

        records, seconds = 0, 0.0
        if not isfile(reportfile):
            return records, seconds
        events = open(reportfile)
        try:
            split = lambda l:list(map(str.strip, l.split('\t')))
            begintime = None
            datefilter = lambda date_x_y_z: date_x_y_z[0][1:-1] >= dateSince
            allevents = map(split, filter(str.strip, events))
            for date, event, anIdentifier, comments in filter(datefilter, allevents):
                if event == "STARTHARVEST":
                    begintime = parseToTime(date[1:-1])
                    harvested = uploaded = deleted = total = -1
                elif event == 'ENDHARVEST':
                    if begintime and harvested > -1:
                        endtime = parseToTime(date[1:-1])
                        if endtime > begintime:
                            records += (int(uploaded) + int(deleted))
                            seconds += diffTime(endtime, begintime)
                            begintime = None
                elif event == 'SUCCES':
                    match = NUMBERS_RE.match(comments)
                    if match:
                        harvested, uploaded, deleted, total = map(int, match.groups())

        finally:
            events.close()
        return records, seconds
