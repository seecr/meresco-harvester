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
from cq2utils_old import binderytools
from cq2utils_old.wrappers import wrapp
from merescoharvester.harvester import classification

LOM = "<lom>%s</lom>"

CLASSIFICATION = """<classification>
    <purpose>
        <source>
            <langstring xml:lang="x-none">TPv1.0.2_anders</langstring>
        </source>
        <value>
            <langstring xml:lang="nl">%s</langstring>
        </value>
    </purpose>
    %s
</classification>"""

TAXONPATH = """<taxonpath>%s</taxonpath>"""

TAXON = """<taxon>
    <id>%s</id>
    <entry>
    <langstring xml:lang="nl">%s</langstring>
    </entry>
</taxon>"""

class ClassificationTest(unittest.TestCase):
    def node(self, xmlString):
        return binderytools.bind_string(xmlString).classification
    
    def nodes(self, xmlString):
        return binderytools.bind_string(xmlString).lom.classification
    
    def testClassificationSinglePathSingleTAXON(self):
        node = self.node(CLASSIFICATION % ("discipline", TAXONPATH % TAXON % ("382", "Bouw") ))
        classificationResult = classification.fromNode(node)
        self.assertEquals("discipline:/Bouw", classificationResult.flattenEntry())
        self.assertEquals("discipline:/382", classificationResult.flattenId())
        
    def testClassificationSinglePathMultipleTAXONs(self):
        TAXON382 = TAXON % ("382", "Bouw")
        TAXON383 = TAXON % ("383", "Dakbedekking")
        singlePathMultipleTAXONs = CLASSIFICATION % ("discipline", TAXONPATH % (TAXON382 + TAXON383))

        node = self.node(singlePathMultipleTAXONs)
        classificationResult = classification.fromNode(node)
        
        self.assertEquals("discipline:/Bouw/Dakbedekking; discipline:/Bouw", classificationResult.flattenEntry())
        
        self.assertEquals("discipline:/382/383; discipline:/382", classificationResult.flattenId())
    
    def testClassificationMultiplePaths(self):
        path1 = TAXONPATH % TAXON % ("704", "Installatietechniek")
        path2 = TAXONPATH % TAXON % ("3172", "Tabs en spaties        ")
        path3 = TAXONPATH % TAXON % ("2479", "Branche")
        multiplePaths = CLASSIFICATION % ("discipline", path1 + path2 + path3)
        
        node = self.node(multiplePaths)
        classificationResult = classification.fromNode(node)
        
        self.assertEquals("discipline:/Installatietechniek; discipline:/Tabs en spaties; discipline:/Branche", classificationResult.flattenEntry())
        
    def testClassificationMultipleClassifications(self):
        classification1 = CLASSIFICATION % ("education level", TAXONPATH % TAXON % ("xxx", "xxxxxx"))
        classification2 = CLASSIFICATION % ("discipline", TAXONPATH % TAXON % ("704", "Installatietechniek"))
        classification3 = CLASSIFICATION % ("discipline", TAXONPATH % TAXON % ("3172", "Tabs en spaties        "))
        
        classifications = self.nodes(LOM % (classification1 + classification2 + classification3))
        classificationResult = classification.aggregate(classifications)
        
        self.assertEquals("discipline:/Installatietechniek; discipline:/Tabs en spaties", classificationResult.flattenEntry("discipline"))
        self.assertEquals(["discipline", "education level"], classificationResult.getPurposes())
        self.assertEquals("", classificationResult.flattenEntry("not existing"))
    
