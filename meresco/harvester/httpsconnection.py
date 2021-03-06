## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2014-2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from httplib import HTTPSConnection
from ssl import wrap_socket, PROTOCOL_TLSv1
from socket import create_connection
from urllib2 import HTTPSHandler


class HTTPSConnectionTLS(HTTPSConnection):
    def connect(self):
        sock = create_connection((self.host, self.port), self.timeout)
        if not getattr(self, '_tunnel_host') is None:
            self.sock = sock
            self._tunnel()
        self.sock = wrap_socket(sock, self.key_file, self.cert_file, ssl_version=PROTOCOL_TLSv1)

class HTTPSHandlerTLS(HTTPSHandler):
    def https_open(self, req):
        return self.do_open(HTTPSConnectionTLS, req)
