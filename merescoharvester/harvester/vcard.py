## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Seek You Too (CQ2) http://www.cq2.nl
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
import re

vcardLine = re.compile("^(?P<key>[A-Z]+):(?P<value>.*)$", re.M)

def fromString(aString):
    card = VCard()
    if aString != "":
        card.fromString(aString)
    return card


ESCAPED = [('\,',','), ('\;',';'), ('\:',':')]

class VCard:
    def __init__(self):
        self._valid = False
        self._fields = {}
        
    def __getattr__(self, name):
        return self.hasField(name) and self._fields[name.lower()] or ''
        
    def hasField(self, fieldName):
        return self._fields.has_key(fieldName.lower())
        
    def fromString(self, aString):
        aString = aString.replace(r'\n','\n').strip()
        if not (aString.startswith("BEGIN:VCARD") and aString.endswith("END:VCARD")):
            return
        
        lines = aString.split("\n")[1:-1]
        for line in lines:
            match = vcardLine.match(line)
            if match:
                key = match.groupdict()['key'].lower()
                value = match.groupdict()['value']
                for orig,repl in ESCAPED:
                    value = value.replace(orig, repl)
                self._fields[key] = value
        
        if len(self._fields ) > 0:
            self._valid = True

    def isValid(self):
        return self._valid
