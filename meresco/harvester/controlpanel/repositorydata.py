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
from lxml.etree import parse


class RepositoryData(object):
    singularFields = ['repositoryGroupId', 'baseurl', 'set', 'metadataPrefix', 'mappingId', 'targetId', 'collection', 'maximumIgnore', 'use', 'complete', 'action']

    def __init__(self, identifier):
        self.id = identifier
        for name in self.singularFields:
            setattr(self, name, '')
        self.shopclosed = []

    def save(self, filename):
        with open(filename, 'w') as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write('<repository>\n')
            f.write('<id>%s</id>\n' % escapeXml(self.id))
            for name in self.singularFields:
                f.write('<%s>%s</%s>\n' % (name, escapeXml(getattr(self, name)), name))
            for entry in self.shopclosed:
                f.write('<shopclosed>%s</shopclosed>\n' % escapeXml(entry))
            f.write('</repository>\n')

    @classmethod
    def read(cls, filename):
        lxmlNode = parse(open(filename))
        r = cls(''.join(lxmlNode.xpath('/repository/id/text()')))
        for name in cls.singularFields:
            setattr(r, name, ''.join(lxmlNode.xpath('/repository/%s/text()' % name)))
        r.shopclosed = [str(shopclosed) for shopclosed in lxmlNode.xpath('/repository/shopclosed/text()')]
        return r

