from seecr.test import SeecrTestCase, CallTrace

from os.path import join
from meresco.harvester.useractions import UserActions, User
from weightless.core import be, Observable, asString
from urllib import urlencode

class UserActionsTest(SeecrTestCase):

    def setUp(self):
        SeecrTestCase.setUp(self)
        with open(join(self.tempdir, 'users.xml'), 'w') as fp:
            fp.write("""<?xml version='1.0' encoding='utf-8'?>
<users>
    <admin>
        <name>Administrator</name>
        <organization>Seecr</organization>
        <telephone>Green</telephone>
        <email>info@seecr.nl</email>
        <domain>seecr.nl</domain>
        <notes>Some guys making awesome code</notes>
    </admin>
</users>""")

    def testListUsers(self):
        userAction = UserActions(dataDir=self.tempdir)
        users = userAction.listUsers()
        self.assertEqual(1, len(users))
        self.assertEqual("admin", users[0].username)
        self.assertEqual("Administrator", users[0].name)
        self.assertEqual("Seecr", users[0].organization)
        self.assertEqual("Green", users[0].telephone)
        self.assertEqual("info@seecr.nl", users[0].email)
        self.assertEqual("seecr.nl", users[0].domain)
        self.assertEqual("Some guys making awesome code", users[0].notes)
        self.assertEqual('<admin><name>Administrator</name><organization>Seecr</organization><telephone>Green</telephone><email>info@seecr.nl</email><domain>seecr.nl</domain><notes>Some guys making awesome code</notes></admin>', users[0].asXml())

    def testCreateUser(self):
        observer = CallTrace()
        action = UserActions(dataDir=self.tempdir)
        session = {}
        dna = be(
            (Observable(),
                (action, 
                    (observer, )
                ),
            ))

        self.assertEqual(1, len(action.listUsers()))
        response = asString(dna.call.handleRequest(
           Method="POST",
           path="/user.action/create",
           session=session,
           Body=urlencode(dict(
               redirectUri="/go_here_now",
               username="johan",
               domain="domein",
               password1="password",
               password2="password"))))
        self.assertEqual(2, len(action.listUsers()))
        self.assertTrue("Location: /go_here_now?identifier=johan" in response, response)
        self.assertEqual(1, len(observer.calledMethods))
        self.assertEqual({}, session)
    
    def testCreateUserWithErrors(self):
        observer = CallTrace()
        session = {}
        action = UserActions(dataDir=self.tempdir)
        dna = be(
            (Observable(),
                (action,
                    (observer, )
                ),
            ))

        self.assertEqual(1, len(action.listUsers()))
        response = asString(dna.call.handleRequest(
           Method="POST",
           path="/user.action/create",
           session=session,
           Body=urlencode(dict(
               redirectUri="/go_here_now",
               errorUri="/oops",
               username="johan",
               domain='domein'))))
        self.assertEqual(1, len(action.listUsers()))
        self.assertTrue("Location: /oops" in response, response)
        self.assertEqual(0, len(observer.calledMethods))
        self.assertEqual({'error_newUser': 'Both passwordfields need to be supplied.', 'saved_form_values': {'domain': 'domein', 'username': 'johan'}}, session)
        
        response = asString(dna.call.handleRequest(
           Method="POST",
           path="/user.action/create",
           session=session,
           Body=urlencode(dict(
               redirectUri="/go_here_now",
               errorUri="/oops",
               username="johan",
               domain="domein",
               password1="password1",
               password2="password2"))))
        self.assertEqual(1, len(action.listUsers()))
        self.assertTrue("Location: /oops" in response, response)
        self.assertEqual(0, len(observer.calledMethods))
        self.assertEqual({'error_newUser': 'Passwords do not match.', 'saved_form_values': {'domain': 'domein', 'username': 'johan'}}, session)


    def testDeleteUser(self):
        observer = CallTrace()
        action = UserActions(dataDir=self.tempdir)
        dna = be(
            (Observable(),
                (action, 
                    (observer, )
                ),
            ))
        
        users = action.listUsers()
        users.append(User(username="johan"))
        action.saveUsers(users)
        self.assertEqual(2, len(action.listUsers()))
        response = asString(dna.call.handleRequest(
            Method="POST",
            path="/user.action/delete",
            Body=urlencode(dict(
               redirectUri="/go_here_now",
               username="johan"))))
        self.assertEqual(1, len(action.listUsers()))
        self.assertTrue("Location: /go_here_now" in response, response)
        self.assertEqual(1, len(observer.calledMethods))

    def testUpdateUser(self):
        action = UserActions(dataDir=self.tempdir)
        dna = be(
            (Observable(),
                (action, ),
            ))
        
        users = action.listUsers()
        users.append(User(username="johan"))
        action.saveUsers(users)

        self.assertEqual(2, len(action.listUsers()))
        self.assertEqual("", action.getUser("johan").organization)
        response = asString(dna.call.handleRequest(
            Method="POST",
            path="/user.action/update",
            Body=urlencode(dict(
               redirectUri="/go_here_now",
               username="johan",
               organization="Seecr"))))
        self.assertEqual(2, len(action.listUsers()))
        self.assertEqual("Seecr", action.getUser("johan").organization)
        self.assertTrue("Location: /go_here_now?identifier=johan" in response, response)
        
        response = asString(dna.call.handleRequest(
            Method="POST",
            path="/user.action/update",
            Body=urlencode(dict(
               redirectUri="/go_here_now",
               username="johan",
               organization=""))))
        self.assertEqual("", action.getUser("johan").organization)
