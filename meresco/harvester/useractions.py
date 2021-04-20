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

from meresco.html import PostActions
from meresco.xml import xpathFirst
from meresco.components.http.utils import redirectHttp

from meresco.components import atomic_write

from os.path import join, isfile
from lxml.etree import parse, XML
from xml.sax.saxutils import escape as escapeXml
from urllib.parse import urlencode, parse_qs


class User(object):
    ATTRIBUTES = ['name', 'organization', 'telephone', 'email', 'domain', 'notes']
    def __init__(self, xmlNode=None, username=None):
        self.username = username
        for attribute in self.ATTRIBUTES:
            self.setValueFor(attribute,  '')
        if xmlNode is not None:
            self.username = xmlNode.tag.split('}')[-1]
            for attribute in self.ATTRIBUTES:
                self.setValueFor(attribute, xpathFirst(xmlNode, '{}/text()'.format(attribute)) or '')

    def setValueFor(self, key, value):
        setattr(self, key, value)

    def getValue(self, key):
        if key not in self.ATTRIBUTES:
            raise KeyError("No such attribute {}".format(key))
        return getattr(self, key)

    def asXml(self):
        return """<{username}>{xml}</{username}>""".format(
            username=self.username,
            xml=''.join("<{tag}>{value}</{tag}>".format(
                tag=tag,
                value=escapeXml(getattr(self, tag, ''))) for tag in self.ATTRIBUTES))


class UserActions(PostActions):
    def __init__(self, dataDir):
        PostActions.__init__(self)
        self._filename = join(dataDir, 'users.xml')

        self.registerAction("create", self._create)
        self.registerAction("delete", self._delete)
        self.registerAction("update", self._update)

    def listUsers(self):
        xml = self._parseUsersXml()
        return sorted([User(xmlNode=node) for node in xml.xpath("/users/child::*")], key=lambda user: user.username)

    def getUser(self, username):
        xml = self._parseUsersXml()
        xmlNode = xpathFirst(xml, "/users/{}".format(username))

        return User(xmlNode=xmlNode) if xmlNode is not None else None

    def _parseUsersXml(self):
        if isfile(self._filename):
            with open(self._filename) as fp:
                return parse(fp)
        return XML("<users/>")

    def saveUsers(self, users):
        with atomic_write(self._filename) as fp:
            fp.write("<users>{}</users>".format(''.join(user.asXml() for user in users)))

    def _create(self, session, Body, **kwargs):
        arguments = _parseBody(Body, ['username', 'domain', 'redirectUri', 'errorUri', 'password1', 'password2'])
        redirectUri = arguments.get('redirectUri')
        errorUri = arguments.get('errorUri')
        username = arguments.get('username')
        domain = arguments.get('domain')
        password1 = arguments.get('password1', '')
        password2 = arguments.get('password2', '')

        session['saved_form_values'] = dict(username=username, domain=domain)
        if password1.strip() == '' or password2.strip() == '':
            session['error_newUser'] = "Both passwordfields need to be supplied."
            yield redirectHttp % errorUri
            return
        if password1 != password2:
            session['error_newUser'] = "Passwords do not match."
            yield redirectHttp % errorUri
            return

        users = self.listUsers()
        exists = len([user for user in users if user.username == username]) > 0
        if not exists:
            self.do.addUser(username=username, password=password1)
            user = User(username=username)
            user.domain = domain
            users.append(user)
            self.saveUsers(users)
        if 'saved_form_values' in session:
            del session['saved_form_values']

        yield redirectHttp % "{}?{}".format(redirectUri, urlencode(dict(identifier=username)))

    def _delete(self, Body, **kwargs):
        arguments = _parseBody(Body, ['username', 'redirectUri'])
        redirectUri = arguments.get('redirectUri')
        username = arguments.get('username')

        users = self.listUsers()
        withoutUser = [user for user in users if user.username != username]
        if len(users) - len(withoutUser) == 1:
            self.saveUsers(withoutUser)
            self.do.removeUser(username)
        yield redirectHttp % redirectUri

    def _update(self, Body, **kwargs):
        arguments = _parseBody(Body, ['username', 'redirectUri'] + User.ATTRIBUTES)
        redirectUri = arguments.get('redirectUri')
        username = arguments.get('username')

        users = self.listUsers()
        withoutUser = [user for user in users if user.username != username]
        user = [user for user in users if user.username == username]
        if len(user) == 1:
            for attribute in User.ATTRIBUTES:
                if attribute in arguments:
                    user[0].setValueFor(attribute, arguments[attribute])

            self.saveUsers(withoutUser + user)
        yield redirectHttp % "{}?{}".format(redirectUri, urlencode(dict(identifier=username)))

    # Bit of a hack, getUser is also implemented in PasswordFile and responds
    getUserInfo = getUser


def _parseBody(Body, fieldList):
    return dict((key, value[0]) for key, value in list(parse_qs(str(Body, encoding="utf-8"), keep_blank_values=1).items()) if key in fieldList)
