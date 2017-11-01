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
# Copyright (C) 2009, 2011 Tilburg University http://www.uvt.nl
# Copyright (C) 2011, 2015 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from re import compile
from datetime import datetime
from os.path import dirname, isdir
from os import makedirs, rename

LOGLINE_RE=compile(r'^\[([^\]]*)\]\t([\w ]+)\t\[([^\]]*)\]\t(.*)$')

class BasicEventLogger(object):
    def __init__(self, logfile, maxLogLines=20000):
        self._numberOfLogLines = 0
        self._maxLogLines = maxLogLines
        self._logfilePath = logfile
        self._logfile = self._openlogfile(self._logfilePath)

    def close(self):
        if self._logfile:
            self._logfile.close()
            self._logfile = None

    def logLine(self, event, comments, id=''):
        self._time()
        self._space()
        self._event(event)
        self._space()
        self._id(id)
        self._space()
        self._comments(comments)
        self._flush()
        self._clearExcessLogLines()

    def _time(self):
        now = datetime.utcnow()
        ms = ('%03i'%now.microsecond)[:3]
        self._logfile.write('[' + now.strftime('%Y-%m-%d %H:%M:%S.') + ms + ']')

    def _id(self, id):
        self._logfile.write('[')
        self._writeStripped(id)
        self._logfile.write(']')

    def _event(self,event):
        self._writeStripped(event)

    def _comments(self, comments):
        self._writeStripped(comments)
        self._logfile.write('\n')

    def _space(self):
        self._logfile.write('\t')

    def _writeStripped(self, aString):
        self._logfile.write(' '.join(str(aString).split()))

    def _flush(self):
        self._logfile.flush()

    def getEventLogger(self):
        return self

class EventLogger(BasicEventLogger):
    def __init__(self, logfile, maxLogLines=20000):
        super(EventLogger, self).__init__(logfile, maxLogLines=maxLogLines)

    def _openlogfile(self, logfile):
        self._numberOfLogLines = 0
        isdir(dirname(logfile)) or makedirs(dirname(logfile))
        f = open(logfile, 'a+')
        for line in f:
            self._numberOfLogLines += 1
        return f

    def _clearExcessLogLines(self):
        if self._numberOfLogLines >= self._maxLogLines:
            self._logfile.seek(0)
            tmpFile = open(self._logfilePath + ".tmp", 'w')
            for i, line in enumerate(self._logfile):
                if i >= self._maxLogLines / 2:
                    tmpFile.write(line)
            tmpFile.close()
            self.close()
            rename(self._logfilePath + ".tmp", self._logfilePath)
            self._logfile = self._openlogfile(self._logfilePath)

    def logLine(self, *args, **kwargs):
        self._numberOfLogLines += 1
        BasicEventLogger.logLine(self, *args, **kwargs)

    def logSuccess(self,comments='', id=''):
        self.logLine('SUCCES', comments=comments, id=id)

    def logFailure(self,comments='', id=''):
        self.logLine('FAILURE', comments=comments, id=id)
    #fail = failure

    def logError(self,comments='', id=''):
        self.logLine('ERROR', comments=comments, id=id)

    def logInfo(self, comments='', id=''):
        self.logLine('INFO', comments=comments, id=id)

    def logWarning(self, comments='', id=''):
        self.logLine('WARNING', comments=comments, id=id)

class StreamEventLogger(EventLogger):
    def __init__(self, stream):
        self._stream = stream
        EventLogger.__init__(self, None)

    def _openlogfile(self, logfile):
        return self._stream

    def _clearExcessLogLines(self):
        pass

class CompositeLogger(EventLogger):
    def __init__(self, loggers):
        EventLogger.__init__(self, None)
        self._loggers = loggers

    def _openlogfile(self, logfile):
        return None

    def _clearExcessLogLines(self):
        pass

    def logLine(self, event, comments, id=''):
        for events, logger in self._loggers:
            if events == ['*'] or event in events:
                logger.logLine(event, comments, id)

class NilEventLogger(EventLogger):
        def __init__(self):
            EventLogger.__init__(self, None)

        def _openlogfile(self, logfile):
            pass

        def _clearExcessLogLines(self):
            pass

        def logLine(self, event, comments, id=''):
            pass

        def close(self):
            pass
