## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
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

import unittest
from slowfoot import binderytools
from slowfoot.wrappers import wrapp

class CacheRecordTest(unittest.TestCase):
    def testGetPartlyXML(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<ListRecords>
<record>
    <header>1</header>
</record>
    <record><header>2</header></record>
</ListRecords>"""
        w = wrapp(binderytools.bind_string(xml))
        records = w.ListRecords.record
        self.assertEquals('<record>\n    <header>1</header>\n</record>',records.xml())
        self.assertEquals('<record>\n    <header>1</header>\n</record>',records[0].xml())
        self.assertEquals('<record><header>2</header></record>',records[1].xml())
