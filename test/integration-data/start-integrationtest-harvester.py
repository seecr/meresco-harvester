#!/usr/bin/env python
## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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

# This script should be run by a user with write access to the logDir and stateDir
# specified in the apache configuration

from time import gmtime, strftime
from slowfoot.wrappers import wrapp
from slowfoot.binderytools import bind_string, bind_file

from merescoharvester.harvester.startharvester import StartHarvester


from merescoharvester.harvester.saharaget import SaharaGet

def buildResponseDateXml():
    return """<responseDate>%s</responseDate>""" % strftime('%Y-%m-%dT%H:%M:%SZ', gmtime())

def GetRepositories(domainId, **kwargs):
    responseDateXml = buildResponseDateXml()
    repositoryXml = readFile("integration.test.repository").repository.xml()
    xml="""<?xml version="1.0" encoding="UTF-8"?>
<saharaget xmlns="http://sahara.cq2.org/xsd/saharaget.xsd">
 %(responseDateXml)s
 <request>
     <verb>GetRepositories</verb>
     <domainId>%(domainId)s</domainId>
 </request>
 <GetRepositories>
    %(repositoryXml)s
 </GetRepositories>
</saharaget>""" % locals()
    return wrapp(bind_string(xml))

def GetRepository(domainId, repositoryId, **kwargs):
    responseDateXml = buildResponseDateXml()
    repositoryXml = readFile("integration.test.repository").repository.xml()
    xml="""<?xml version="1.0" encoding="UTF-8"?>
<saharaget xmlns="http://sahara.cq2.org/xsd/saharaget.xsd">
 %(responseDateXml)s
 <request>
     <verb>GetRepository</verb>
     <domainId>%(domainId)s</domainId>
     <repositoryId>%(repositoryId)s</repositoryId>
 </request>
 <GetRepository>
    %(repositoryXml)s
 </GetRepository>
</saharaget>""" % locals()
    return wrapp(bind_string(xml))

def GetTarget(domainId, targetId, **kwargs):
    responseDateXml = buildResponseDateXml()
    targetXml = readFile("%s.target" % targetId).target.xml()
    xml="""<?xml version="1.0" encoding="UTF-8"?>
<saharaget xmlns="http://sahara.cq2.org/xsd/saharaget.xsd">
 %(responseDateXml)s
 <request>
     <verb>GetTarget</verb>
     <domainId>%(domainId)s</domainId>
     <targetId>%(targetId)s</targetId>
 </request>
 <GetTarget>
    %(targetXml)s
 </GetTarget>
</saharaget>""" % locals()
    return wrapp(bind_string(xml))

def GetMapping(domainId, mappingId, **kwargs):
    responseDateXml = buildResponseDateXml()
    mappingXml = readFile("%s.mapping" % mappingId).mapping.xml()
    xml="""<?xml version="1.0" encoding="UTF-8"?>
<saharaget xmlns="http://sahara.cq2.org/xsd/saharaget.xsd">
 %(responseDateXml)s
 <request>
     <verb>GetMapping</verb>
     <domainId>%(domainId)s</domainId>
     <mappingId>%(mappingId)s</mappingId>
 </request>
 <GetMapping>
    %(mappingXml)s
 </GetMapping>
</saharaget>""" % locals()
    return wrapp(bind_string(xml))

def readFile(fileName):
    return bind_file("data/" + fileName)

def read(self, verb, **kwargs):
    print verb, kwargs
    return globals()[verb](**kwargs)

SaharaGet._read = read


StartHarvester().start()


