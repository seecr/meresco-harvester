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
#
# (c) 2005 Seek You Too B.V.
#
# $Id: timedprocess.py 4825 2007-04-16 13:36:24Z TJ $
#

import os, sys
from threading import Timer

class TimedProcess(object):
    def __init__(self):
        self._wasTimeout = False
        self._wasSuccess = False
        self._pid = -1
        self._signal=9
            
    def wasSuccess(self):
        return self._wasSuccess

    def wasTimeout(self):
        return self._wasTimeout
    
    def setTimedOut(self):
        self._wasTimeout = True
        self._wasSuccess = False
        
    def terminate(self):
        if self._pid != -1:
            os.kill(self._pid, self._signal)
        self._wasTimeout = True
        self.timer.cancel()

    def executeScript(self, args, timeout, signal=9):
        self._signal = signal
        self._pid = os.spawnvp(os.P_NOWAIT, sys.executable,
            [sys.executable] + args)
        self.timer = Timer(timeout, self.terminate)
        self.timer.start()
        os.waitpid(self._pid, 0)

        if not self._wasTimeout:
            self.timer.cancel()
            self._wasSuccess = True
            self._wasTimeout = False
