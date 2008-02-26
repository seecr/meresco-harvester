#!/usr/bin/env python
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

class SaharaObject:
    
    def __init__(self, attr, listattr = []):
        self._attr = attr
        self._listattr = listattr
        self._initAttributes()
        self._saharaget = None
    
    def _initAttributes(self):
        for attr in self._attr + self._listattr:
            setattr(self, attr, None)
            
    def fill(self, saharaget, xml):
        for attr in self._attr:
            setattr(self, attr, str(getattr(xml, attr, None)))
        for attr in self._listattr:
            setattr(self, attr, map(str, getattr(xml, attr, None)))
        self._saharaget = saharaget

