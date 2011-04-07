## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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
from __future__ import with_statement

from xml.sax.saxutils import escape as escapeXml

class RepositoryData(object):
    def __init__(self, identifier):
        self.id = identifier
        self.repositoryGroupId = ''
        self.baseurl = ''
        self.set = ''
        self.metadataPrefix = ''
        self.mappingId = ''
        self.targetId = ''
        self.collection = ''
        self.maximumIgnore = ''
        self.use = ''
        self.complete = ''
        self.action = ''
        self.shopclosed = []

    def save(self, filename):
        with open(filename, 'w') as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write('<repository>\n')
            f.write('<id>%s</id>\n' % escapeXml(self.id))
            f.write('<repositoryGroupId>%s</repositoryGroupId>\n' % escapeXml(self.repositoryGroupId))
            f.write('<baseurl>%s</baseurl>\n' % escapeXml(self.baseurl))
            f.write('<set>%s</set>\n' % escapeXml(self.set))
            f.write('<metadataPrefix>%s</metadataPrefix>\n' % escapeXml(self.metadataPrefix))
            f.write('<mappingId>%s</mappingId>\n' % escapeXml(self.mappingId))
            f.write('<targetId>%s</targetId>\n' % escapeXml(self.targetId))
            f.write('<collection>%s</collection>\n' % escapeXml(self.collection))
            f.write('<maximumIgnore>%s</maximumIgnore>\n' % escapeXml(self.maximumIgnore))
            f.write('<use>%s</use>\n' % escapeXml(self.use))
            f.write('<complete>%s</complete>\n' % escapeXml(self.complete))
            f.write('<action>%s</action>\n' % escapeXml(self.action))
            f.write('</repository>\n')

