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
# Copyright (C) 2011, 2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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

from seecr.test import SeecrTestCase
from meresco.harvester.timedprocess import TimedProcess
from os.path import join
from time import sleep

class TimedProcessTest(SeecrTestCase):

    def testSuccess(self):
        fd = open(self.tempfile,'w')
        try:
            fd.write("""import sys
sys.exit(123)""")
        finally:
            fd.close()

        tp = TimedProcess()
        process = tp.executeScript(['python', self.tempfile], 10)
        while process.poll() is None:
            sleep(0.1)
        exitstatus = tp.stopScript(process)
        self.assertFalse(tp.wasTimeout())
        self.assertTrue(tp.wasSuccess())
        self.assertEquals(123, exitstatus)

    def testSuccessParameters(self):
        fd = open(self.tempfile,'w')
        try:
            fd.write("""import sys
open('%s', 'w').write(str(len(sys.argv[1:])))
""" % join(self.tempdir, 'output.txt'))
        finally:
            fd.close()

        tp = TimedProcess()
        process = tp.executeScript(['python', self.tempfile, 'it','is','difficult'], 10)
        while process.poll() is None:
            sleep(0.1)
        exitstatus = tp.stopScript(process)
        self.assertFalse(tp.wasTimeout())
        self.assertTrue(tp.wasSuccess())
        self.assertEquals('3', open(join(self.tempdir, 'output.txt')).read())
        self.assertEquals(0, exitstatus)

    def testTimeout(self):
        fd = open(self.tempfile,'w')
        try:
            fd.write("""while True:
    pass
""")
        finally:
            fd.close()

        tp = TimedProcess()
        process = tp.executeScript(['python', self.tempfile], 1)
        while process.poll() is None:
            sleep(0.1)
        exitstatus = tp.stopScript(process)
        self.assertTrue(tp.wasTimeout())
        self.assertFalse(tp.wasSuccess())
        self.assertEquals(-9, exitstatus)

