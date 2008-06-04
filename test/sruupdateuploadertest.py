## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for 
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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
from cq2utils import CQ2TestCase, CallTrace
from amara.binderytools import bind_string

from merescoharvester.harvester.sruupdateuploader import SruUpdateUploader

class SruUpdateUploaderTest(CQ2TestCase):
    def testOne(self):
        target = CallTrace('SruUpdateTarget', verbose=True)
        uploader = SruUpdateUploader(target, CallTrace('eventlogger'))
        sentData = []
        def sendData(data):
            sentData.append(data)
        uploader._sendData = sendData

        upload = CallTrace('Upload')
        upload.id = 'some:id'
        upload.parts={
            'meta': '<meta>....</meta>',
            'otherdata': '<stupidXML>abcdefgh'
        }
        uploader.send(upload)
        self.assertEquals(1, len(sentData))

        updateRequest = bind_string(sentData[0]).updateRequest
        self.assertEquals('some:id', str(updateRequest.recordIdentifier))
        self.assertEquals('info:srw/action/1/replace', str(updateRequest.action))
        document = updateRequest.record.recordData.document
        self.assertEquals(2, len(document.part))

        uploader.delete(upload)
        updateRequest = bind_string(sentData[1]).updateRequest
        self.assertEquals('some:id', str(updateRequest.recordIdentifier))
        self.assertEquals('info:srw/action/1/delete', str(updateRequest.action))
