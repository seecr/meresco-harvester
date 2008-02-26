#!/bin/bash
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

source $(dirname $0)/functions.sh
isroot

if ! hasPythonModule Ft  ; then
	echo "*
* Installing Ft"
	(
	cd /tmp
	wget "ftp://ftp.4suite.org/pub/4Suite/4Suite-XML-1.0.2.tar.bz2"
	tar jxvf 4Suite-XML-1.0.2.tar.bz2
	cd 4Suite-XML-1.0.2
	python setup.py install
	)
else
	echo "*
* Ft found"
fi
