from seecr.test import SeecrTestCase

from os.path import join
from meresco.harvester.useractions import UserActions

class UserActionsTest(SeecrTestCase):
    def testListUsers(self):
        with open(join(self.tempdir, 'users.xml'), 'w') as fp:
            fp.write("""<?xml version='1.0' encoding='utf-8'?>
<users>
    <admin>
        <name>Administrator</name>
        <organization>Seecr</organization>
        <telephone>Green</telephone
        <email>info@seecr.nl</email>
        <domain>seecr.nl</domain>
        <notes>Some guys making awesome code</notes>
    </admin>
</users>""")
        userAction = UserAction(self.tempdir)
        users = userAction.listUsers()
        self.assertEqual(1, len(users))
        self.assertEqual("admin", users[0].name)
        self.assertEqual("Administrator", users[0].fullname)
        self.assertEqual("Seecr", users[0].organization)
        self.assertEqual("Green", users[0].telephone)
        self.assertEqual("info@seecr.nl", users[0].email)
        self.assertEqual("seecr.nl", users[0].domain)
        self.assertEqual("Some guys making awesome code", users[0].notes)

        self.fail()
