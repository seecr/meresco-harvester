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
# Copyright (C) 2011, 2015-2017 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011, 2015 Stichting Kennisnet http://www.kennisnet.nl
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

from os import kill, O_NONBLOCK
from subprocess import Popen, PIPE
from fcntl import fcntl, F_SETFL

from threading import Timer
from signal import SIGKILL


class TimedProcess(object):
    def __init__(self, signal=None):
        self._wasTimeout = False
        self._wasSuccess = False
        self._pid = -1
        self._signal = SIGKILL if signal is None else signal

    def wasSuccess(self):
        return self._wasSuccess

    def wasTimeout(self):
        return self._wasTimeout

    def setTimedOut(self):
        self._wasTimeout = True
        self._wasSuccess = False

    def terminate(self):
        if self._pid != -1:
            kill(self._pid, self._signal)
        self.timer.cancel()

    def timedOut(self):
        print 'Process %s with args "%s" timed out after %s seconds and will be terminated.' % (self._pid, self._args, self._timeout)
        import sys; sys.stdout.flush()
        self._wasTimeout = True
        self.terminate()

    def executeScript(self, args, timeout):
        self._args = args
        self._timeout = timeout
        process = Popen(args, stdout=PIPE, stderr=PIPE, bufsize=0)
        fcntl(process.stdout.fileno(), F_SETFL, O_NONBLOCK)
        fcntl(process.stderr.fileno(), F_SETFL, O_NONBLOCK)
        self._pid = process.pid
        self.timer = Timer(timeout, self.timedOut)
        self.timer.start()
        return process

    def stopScript(self, process):
        if not self._wasTimeout:
            self.timer.cancel()
            self._wasSuccess = True
            self._wasTimeout = False
        return process.returncode

