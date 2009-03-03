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
#
import sys, os
if sys.version_info[:2] == (2,3):
    from sets import Set as set

from os import makedirs
from os.path import isdir

def idfilename(stateDir, name):
    isdir(stateDir) or makedirs(stateDir)
    return os.path.join(stateDir, name + '.ids')

class Ids:
    def __init__(self, stateDir, name):
        self._filename = idfilename(stateDir, name)
        self._ids = set(map(lambda f:f.strip(), open(self._filename, 'a+').readlines()))
        self._idsfile = open(self._filename, 'a')
        
    def total(self):
        return len(self._ids)
    
    def clear(self):
        self._ids = []
        
    def close(self):
        self._idsfile.close()
        idfilenew = open(self._filename + '.new', 'w')
        try:
            for anId in self._ids:
                idfilenew.write( anId + '\n')
        finally:
            idfilenew.close()
        os.rename(self._filename + '.new', self._filename)

    def add(self, uploadid):
        self._ids.add(uploadid)
        self._idsfile.write( uploadid + '\n')
        self._idsfile.flush()

    def remove(self, uploadid):
        uploadid in self._ids and self._ids.remove(uploadid)
        
