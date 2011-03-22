## begin license ##
#
#    "HBO-Kennisbank" is a webportal that provides free access to student theses,
#    publications and learning objects made available by the Universities of
#    Applied Sciences in the Netherlands.
#    Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
#    Copyright (C) 2011 SURFfoundation. http://www.surf.nl
#    Copyright (C) 2010-2011 Seek You Too B.V. (CQ2) http://www.cq2.nl
#
#    This file is part of "HBO-Kennisbank"
#
#    "HBO-Kennisbank" is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    "HBO-Kennisbank" is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with "HBO-Kennisbank"; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from amara.binderytools import bind_string
from lxml.etree import parse as parse_lxml
from StringIO import StringIO
from socket import socket
from urllib import urlencode
from cq2utils.wrappers import wrapp
from sys import stdout

def _socket(port, timeOutInSeconds):
    sok = socket()
    sok.connect(('localhost', port))
    sok.settimeout(5.0 if timeOutInSeconds is None else timeOutInSeconds)
    return sok

def createReturnValue(header, body, parse):
    if parse == True:
        try:
            body = wrapp(bind_string(body))
        except:
            print body
            raise
    elif parse == 'lxml':
        body = parse_lxml(StringIO(body))
    return header, body


def postRequest(port, path, data, contentType='text/xml; charset="utf-8"', parse=True, timeOutInSeconds=None):
    sok = _socket(port, timeOutInSeconds)
    try:
        contentLength = len(data)
        sendBuffer = '\r\n'.join([
            'POST %(path)s HTTP/1.0',
            'Content-Type: %s' % contentType,
            'Content-Length: %(contentLength)s',
            '', '']) % locals()
        sendBuffer += data

        totalBytesSent = 0
        bytesSent = 0
        while totalBytesSent != len(sendBuffer):
            bytesSent = sok.send(sendBuffer[totalBytesSent:])
            totalBytesSent += bytesSent

        header, body = receiveFromSocket(sok)
        return createReturnValue(header, body, parse)
    finally:
        sok.close()

def getRequest(port, path, arguments, parse=True, timeOutInSeconds=None, host=None, additionalHeaders=None):
    sok = _socket(port, timeOutInSeconds)
    try:
        requestString = path
        if arguments:
            requestString = path + '?' + urlencode(arguments, doseq=True)

        request = 'GET %(requestString)s HTTP/1.0\r\n' % locals()
        if host != None:
            request = 'GET %(requestString)s HTTP/1.1\r\nHost: %(host)s\r\n' % locals()
        if additionalHeaders != None:
            for header in additionalHeaders.items():
                request += '%s: %s\r\n' % header
        request += '\r\n'

        sok.send(request)

        header, body = receiveFromSocket(sok)
        return createReturnValue(header, body, parse)
    finally:
        sok.close()


def receiveFromSocket(sok):
    response = ''
    part = sok.recv(1024)
    response += part
    while part != None:
        part = sok.recv(1024)
        if not part:
            break
        response += part
    return response.split('\r\n\r\n', 1)


def getRequestWithChecks(port, path, arguments, parse=True):
    header, body = getRequest(port, path, arguments, parse=False)
    if 'Traceback (most recent call last):' in body:
        print body
        raise ValueError("Exception found in webpage")
    
    if not parse:
        return header, body

    try:
        parsed = parse_lxml(StringIO(body))
    except:
        for item in enumerate(body.split('\n')):
            print '%05d %s' % item
        raise
    return header, parsed
