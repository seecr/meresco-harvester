from time import gmtime, strftime
from slowfoot.wrappers import wrapp
from slowfoot.binderytools import bind_string, bind_file

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

class MockSaharaGet(object):

    def handleRequest(self, arguments, **kwargs):
        yield '\r\n'.join(['HTTP/1.0 200 Ok', 'Content-Type: text/xml, charset=utf-8\r\n', ''])

        verb = arguments.get('verb', [None])[0]
        domainId = arguments.get('domainId', [None])[0]
        repositoryId = arguments.get('repositoryId', [None])[0]
        targetId = arguments.get('targetId', [None])[0]
        mappingId = arguments.get('mappingId', [None])[0]
        yield read(**locals()).xml()


