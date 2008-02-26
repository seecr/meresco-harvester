## begin license ##
#
#    "Sahara" consists of two subsystems, namely an OAI-harvester and a web-control panel.
#    "Sahara" is developed for SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006,2007 SURFnet B.V. http://www.surfnet.nl
#
#    This file is part of "Sahara"
#
#    "Sahara" is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    "Sahara" is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with "Sahara"; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
#
# Dump repository to file in XML
#
#
#
import sys
import urllib2, urllib
import re

tokenRE=re.compile(".*<resumptionToken.*>(?P<token>.*)</resumptionToken>.*")

def fetchPage(url, filename, token=None):
	args = {'verb':'ListRecords', 'metadataPrefix':'oai_dc'}
	
	if token:
		filename = filename + "." + token
		args['resumptionToken'] = token
		del(args['metadataPrefix'])
	
	filename = filename + ".xml"
	file = open(filename, 'w+')
	try:
		newToken = None
		newUrl = url + "?" + urllib.urlencode(args)
		print newUrl
		stream = urllib2.urlopen(newUrl)
		asString = stream.read()
		matchResult = tokenRE.match(asString[-10000:])
		if matchResult:
			newToken = matchResult.groupdict()['token']
		file.write(asString)
	finally:
		file.close()
	return newToken

def main(url, filename):
	done = False
	token = None
	while not done:
		token = fetchPage(url, filename, token)
		if token == None:
			break
		
if __name__ == "__main__":
	main(sys.argv[1], sys.argv[2])
