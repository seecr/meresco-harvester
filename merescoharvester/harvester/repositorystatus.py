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
#
import re, sys
NUMBERS_RE = re.compile(r'.*Harvested/Uploaded/Deleted/Total:\s*(\d+)/(\d+)/(\d+)/(\d+).*')
from itertools import imap, ifilter
from cgi import escape as escapeXml
    
class RepositoryStatus:
    def __init__(self):
        self.lastSuccesDate = ''
        self.harvested = ''
        self.deleted = ''
        self.uploaded = ''
        self.total = ''
        self.errors = []
        
    def reformatDate(self, aDate):
        return aDate[0:len('YYYY-MM-DD')] + 'T' + aDate[len('YYYY-MM-DD '):len('YYYY-MM-DD HH:MM:SS')] + 'Z'
        
    def addSucces(self, date, comments):
        self.lastSuccesDate = self.reformatDate(date)
        self.errors = []
        match = NUMBERS_RE.match(comments)
        if match:
            self.harvested, self.uploaded, self.deleted, self.total = match.groups()

    def addError(self, date, comments):
        self.errors.append((self.reformatDate(date), comments))

    def main(self, streamIn, streamOut):
        streamOut.write("""<?xml version="1.0"?>
<status>
""")
        self.innerXml(streamIn, streamOut)
        streamOut.write("""</status>""")
        streamOut.flush()
        
    def innerXml(self, streamIn, streamOut):
        split = lambda l:l.strip().split('\t')
        checkLen4 = lambda x:len(x)==4
        for date, event, id, comments in ifilter(checkLen4, imap(split, streamIn)):
            date = date[1:-1]
            if event == 'SUCCES':
                self.addSucces(date, comments)
            if event == 'ERROR':
                self.addError(date, comments)
        streamOut.write("""  <lastHarvestDate>%(lastSuccesDate)s</lastHarvestDate>
  <harvested>%(harvested)s</harvested>
  <uploaded>%(uploaded)s</uploaded>
  <deleted>%(deleted)s</deleted>
  <total>%(total)s</total>
"""%self.__dict__)
        streamOut.write("""  <totalerrors>%i</totalerrors>
"""%len(self.errors))
        if len(self.errors):
            streamOut.write("""  <recenterrors>
""")
            errors = self.errors[:]
            errors.reverse()
            for date,error in errors[:10]:
                streamOut.write("""    <error date="%s">%s</error>
"""%(date, escapeXml(error)))
            streamOut.write("""  </recenterrors>
""")
        else:
            streamOut.write("""  <recenterrors></recenterrors>
""")
        streamOut.flush()

