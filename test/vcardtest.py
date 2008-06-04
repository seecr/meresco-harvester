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
import unittest
from merescoharvester.harvester import vcard
from cq2utils import binderytools
from cq2utils.wrappers import wrapp

validCard = """BEGIN:VCARD
FN:International Finance and Commodities Institute
N:;;International Finance and Commodities Institute
ORG:International Finance and Commodities Institute
VERSION:3.0
END:VCARD"""

cardInXml = r"""<centity>BEGIN:VCARD\nFN:Suilen\, A.\nN:Suilen\, A.\nVERSION:3.0\nEND:VCARD\n</centity>"""

cardInXmlWithEncoding = r"""<centity><vcard>BEGIN:vcard&#xD;FN:onbekend&#xD;ORG:Fontys/MBRT&#xD;END:vcard</vcard></centity>"""

class VCardTest(unittest.TestCase):
    
    def testReadEmptyVCard(self):
        card = vcard.fromString("")
        self.assertFalse(card.isValid())

    def testReadVCard(self):
        card = vcard.fromString(validCard)
        self.assertTrue(card.isValid())
        self.assertEquals("3.0", card.version)
        self.assertEquals("International Finance and Commodities Institute", card.fn)

    def testHasFieldVCard(self):
        card = vcard.fromString(validCard)
        self.assertTrue(card.isValid())
        self.assertTrue(card.hasField('version'))
        self.assertTrue(card.hasField('VERSION'))
        self.assertFalse(card.hasField('doesnotexist'))
        
    def testGetFields(self):
        card = vcard.fromString(validCard)
        self.assertTrue(card.isValid())
        self.assertEquals('3.0', card.email or card.version)
        self.assertEquals('', card.email)
        self.assertEquals('', card.fullname)
        
    def testReadFromXmlString(self):
        xmlCard = wrapp(binderytools.bind_string(cardInXml)).centity
        card = vcard.fromString(xmlCard)
        self.assertTrue(card.isValid())
        self.assertEquals('Suilen, A.', card.fn)

    def testReadFromXmlStringWithEncoding(self):
        """    
          Fontis in LOREnet does not abide by the VCARD spec. They use \r instead of \n and in the begin/end marker
          they spell 'vcard' in lowercase. This test is here to show that when those changes are made to the text
            before it is fed into the vcard-parser it will work. 
        """
        xmlCard = wrapp(binderytools.bind_string(cardInXmlWithEncoding)).centity.vcard
        card = vcard.fromString(xmlCard.replace('\r', '\n').replace('vcard', 'VCARD'))
        self.assertTrue(card.isValid())
        self.assertEquals('onbekend', card.fn)


if __name__ == '__main__':
    unittest.main()
