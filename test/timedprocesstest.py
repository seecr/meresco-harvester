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

import unittest, tempfile, os
from merescoharvester.harvester.timedprocess import TimedProcess

class TimedProcessTest(unittest.TestCase):

    def setUp(self):
        fd, self.filename = tempfile.mkstemp()

    def tearDown(self):
        os.remove(self.filename)

    def testSuccess(self):
        fd = open(self.filename,'w')
        try:
            fd.write('pass')
        finally:
            fd.close()

        tp = TimedProcess()
        tp.executeScript([self.filename], 10)
        self.assert_(not tp.wasTimeout())
        self.assert_(tp.wasSuccess())
    
    def testSuccessParameters(self):
        fd = open(self.filename,'w')
        try:
            fd.write("""import sys
#print len(sys.argv[1:])
""")
        finally:
            fd.close()

        tp = TimedProcess()
        tp.executeScript([self.filename, 'it','is','difficult'], 10)
        self.assert_(not tp.wasTimeout())
        self.assert_(tp.wasSuccess())

    def testTimeout(self):
        fd = open(self.filename,'w')
        try:
            fd.write("""while True:
    pass
""")
        finally:
            fd.close()

        tp = TimedProcess()
        tp.executeScript([self.filename], 1)
        self.assert_(tp.wasTimeout())
        self.assert_(not tp.wasSuccess())
        
