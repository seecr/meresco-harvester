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
def fromNode(aClassificationXmlNode):
    classification = Classification()
    classification.fromNode(aClassificationXmlNode)
    return classification
 
def aggregate(classificationNodes):
    result = AggregatedClassificationDictionary()
    result.fromNodes(classificationNodes)
    return result
    
TAXON_FORMAT = '%s:/%s'
TAXON_SEP = '/'
TAXON_PATHSEP = '; '

class AggregatedClassificationDictionary:
    """purpose -> [classification]"""
    
    def __init__(self):
        self._classifications = {}
    
    def fromNodes(self, classificationNodes):
        for node in classificationNodes:
            aClassification = fromNode(node)
            purpose = aClassification.getPurpose()
            aList = self._classifications.get(purpose, [])
            aList.append(aClassification)
            self._classifications[purpose] = aList
    
    def flattenEntry(self, purpose):
        aList = self._classifications.get(purpose, [])
        return TAXON_PATHSEP.join(map(lambda c:c.flattenEntry(), aList))
        
    def flattenId(self, purpose):
        aList = self._classifications.get(purpose, [])
        return TAXON_PATHSEP.join(map(lambda c:c.flattenId(), aList))
        
    def getPurposes(self):
        return self._classifications.keys()

class Classification:
    
    def __init__(self):
        self._purpose = ''
        self._taxons = []
    
    def fromNode(self, aClassificationXmlNode):
        self._purpose = str(aClassificationXmlNode.purpose.value.langstring)
        for taxonpath in aClassificationXmlNode.taxonpath:
            taxons = []
            for taxon in taxonpath.taxon:
                taxons.append((str(taxon.id).strip(), str(taxon.entry.langstring).strip()))
            self._taxons.append(taxons)
    
    def _resultWithTaxons(self, aTaxonsList):
        return TAXON_FORMAT % (self._purpose, TAXON_SEP.join(aTaxonsList))
    
    def _createTaxonsRecursive(self, aDestinationList, aTaxonsList):
        if aTaxonsList == []:
            return
        
        aDestinationList.append(self._resultWithTaxons(aTaxonsList))
        self._createTaxonsRecursive(aDestinationList, aTaxonsList[:-1])
    
    def _getResults(self, aFilterMethod):
        result = []
        for taxonList in self._taxons:
            taxons = aFilterMethod(taxonList)
            taxonResult = []
            self._createTaxonsRecursive(taxonResult, taxons)
            result.append(TAXON_PATHSEP.join(taxonResult))
        return TAXON_PATHSEP.join(result)
    
    def getPurpose(self):
        return self._purpose
    
    def flattenEntry(self):
        return self._getResults(lambda taxonList: map(lambda (id, entry): entry, taxonList))
    
    def flattenId(self):
        return self._getResults(lambda taxonList: map(lambda (id, entry): id, taxonList))
    
