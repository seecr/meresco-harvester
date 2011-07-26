
from lxml.etree import parse
from os.path import join

class HarvesterData(object):

    def __init__(self, dataPath):
        self._dataPath = dataPath

    def getRepositoryGroupIds(self, domainId):
        lxml = parse(open(join(self._dataPath, '%s.domain' % domainId)))
        return lxml.xpath("/domain/repositoryGroupId/text()")

    def getRepositoryIds(self, domainId, repositoryGroupId):
        lxml = parse(open(join(self._dataPath, '%s.%s.repositoryGroup' % (domainId, repositoryGroupId))))
        return lxml.xpath("/repositoryGroup/repositoryId/text()")

    def getRepositoryGroupId(self, domainId, repositoryId):
        lxml = parse(open(join(self._dataPath, '%s.%s.repository' % (domainId, repositoryId))))
        return lxml.xpath("/repository/repositoryGroupId/text()")[0]

    
