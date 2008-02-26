from cq2utils import CQ2TestCase, CallTrace
from amara.binderytools import bind_string

from sruupdateuploader import SruUpdateUploader

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
