from slowfoot import binderytools
from os.path import join
from urllib import urlencode

from merescoharvester.harvester.oairequest import OaiRequest

class MockOaiRequest(OaiRequest):
    def __init__(self, url):
        OaiRequest.__init__(self,url)
        self._createMapping()
        
    def _request(self, argslist):
        filename = self.findFile(argslist)
        return binderytools.bind_file(filename)

    def findFile(self, argslist):
        argslist.sort()
        return self._mapping[urlencode(argslist)]
        
    def _createMapping(self):
        f = open(join(self._url, 'mapping.txt'), 'r')
        self._mapping = {}
        while 1:
            request = f.readline().strip()
            responsefile = f.readline().strip()
            if not request or not responsefile:
                break
            self._mapping[request] = join(self._url, responsefile)
        
