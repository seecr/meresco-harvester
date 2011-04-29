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
# Copyright (C) 2007-2009, 2011 Seek You Too (CQ2) http://www.cq2.nl
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

from slowfoot.slowfoothandler import Request, handlepsp, util, _psp_login, retrieveSession, apache
from disallowfileplugin import DisallowFilePlugin
from urllib import urlencode
from urllib2 import urlopen
from os.path import dirname, join

templatesPath = join(dirname(__file__), 'slowfoottemplates')

dfp = DisallowFilePlugin([
    'edit',
    'deletefile',
    'save',
    'domain.edit',
    'mapping.edit',
    'repository.edit',
    'repositoryGroup.edit',
    'target.edit',
    'domain.new',
    'mapping.new',
    'repository.new',
    'repositoryGroup.new',
    'target.new',
    'domain.save',
    'mapping.save',
    'repository.save',
    'repositoryGroup.save',
    'target.save',
    'domain.deleteChild',
    'repositoryGroup.deleteRepository',
    'domains',
    'user.edit',
    'user.delete',
    'user.new',
    'user.save'
    ])

internalServerStatus=[]

class StatusException(Exception):
    def __init__(self, code, message=None):
        Exception.__init__(self, message if message != None else code)
        self.code = code

def handler(req):
    if internalServerStatus != ['OK']:
        try:
            checkServerStatus(req)
            internalServerStatus.append('OK')
        except StatusException, e:
            req.uri = '/internalServerError?' + urlencode({'originalUri': req.uri, 'error': e.code, 'message': str(e)})

    req.get_options()['templatesPath'] = templatesPath
    req = Request(req, handlepsp, util, _psp_login, retrieveSession)
    
    req.addPlugin('PREOPEN', dfp)
    req.go()
    return apache.OK

def checkServerStatus(req):
    internalServer = req.get_options().get('internalServer', None)
    if internalServer == None:
        raise StatusException('internalServerNotFound')
    try:
        urlopen(internalServer + '/info/version').read()
    except:
        from traceback import format_exc
        raise StatusException('internalServerNotReachable', format_exc())
