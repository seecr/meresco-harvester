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
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
# 
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

from string import strip
BANNED_EXTENSIONS = ['domain', 'repositoryGroup', 'repository', 'mapping', 'target']

class DisallowFilePlugin(object):
    def __init__(self, patterns = ['edit', 'save'], patternfile = None):
        self._patterns = patternfile and self._readPatterns(patternfile) or patterns

    def _readPatterns(self, filename):
        patternfile = open(filename)
        try:
            return filter(None, map(strip,patternfile.readlines()))
        finally:
            patternfile.close()

    def inPatterns(self, aString):
        return aString in self._patterns

    def handle(self, request, path):
        filename = path.split('/')[-1]
        if self.inPatterns(filename):
            username = request.getSession().get('username', None)
            if username == None:
                self.doNotAllowedAction(request, path)
        extension = filename.split('.')[-1]
        if extension in BANNED_EXTENSIONS and not request.remoteHost() in ['127.0.0.1', 'localhost'] and request.getSession().get('username', None) == None:
            self.doNotAllowedAction(request, path)

    def doNotAllowedAction(self, request, path):
        raise IOError(2,"No such file or directory: '%s'"%path)
