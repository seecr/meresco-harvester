## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2017, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from seecr.test import SeecrTestCase, CallTrace

from os import remove
from os.path import join
from urllib.parse import urlencode

from weightless.core import be, Observable, asString

from meresco.harvester.useractions import UserActions, User


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

    def testListUsersWhenFileMissing(self):
        remove(join(self.tempdir, 'users.xml'))
        userAction = UserActions(dataDir=self.tempdir)
        users = userAction.listUsers()
        self.assertEqual(0, len(users))

    def testGetUser(self):
        userAction = UserActions(dataDir=self.tempdir)
        user = userAction.getUser('admin')
        self.assertEqual("admin", user.username)
        self.assertEqual("Administrator", user.name)
        self.assertEqual("Seecr", user.organization)
        self.assertEqual("Green", user.telephone)
        self.assertEqual("info@seecr.nl", user.email)
        self.assertEqual("seecr.nl", user.domain)
        self.assertEqual("Some guys making awesome code", user.notes)

    def testGetUserWhenFileMissing(self):
        remove(join(self.tempdir, 'users.xml'))
        userAction = UserActions(dataDir=self.tempdir)
        user = userAction.getUser('admin')
        self.assertEqual(None, user)

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
           Body=bUrlencode(dict(
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
           Body=bUrlencode(dict(
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
           Body=bUrlencode(dict(
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
            Body=bUrlencode(dict(
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
            Body=bUrlencode(dict(
               redirectUri="/go_here_now",
               username="johan",
               organization="Seecr"))))
        self.assertEqual(2, len(action.listUsers()))
        self.assertEqual("Seecr", action.getUser("johan").organization)
        self.assertTrue("Location: /go_here_now?identifier=johan" in response, response)

        response = asString(dna.call.handleRequest(
            Method="POST",
            path="/user.action/update",
            Body=bUrlencode(dict(
               redirectUri="/go_here_now",
               username="johan",
               organization=""))))
        self.assertEqual("", action.getUser("johan").organization)

def bUrlencode(*args, **kwargs):
    return bytes(urlencode(*args, **kwargs), encoding='utf-8')

