
from slowfoot.slowfoothandler import Request, handlepsp, util, _psp_login, retrieveSession, apache
from disallowfileplugin import DisallowFilePlugin

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


def handler(req):
    req = Request(req, handlepsp, util, _psp_login, retrieveSession)
    
    req.addPlugin('PREOPEN', dfp)
    req.go()
    return apache.OK