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

amara_version=1.1.7
python -c "import amara, sys; amara.__version__ != '$amara_version' and sys.exit(1)" > /dev/null 2>&1
if [ $? -ne 0 ] ; then
	source $(dirname $0)/functions.sh
	isroot

	echo "*
* Installing Amara"
	(
	cd /tmp
	wget "ftp://ftp.4suite.org/pub/Amara/Amara-$amara_version.tar.bz2"
	tar xjf Amara-$amara_version.tar.bz2
	cd Amara-$amara_version
	ln -s lib amara # workaround for bug in setup of 1.1.7
	python setup.py install
	)
else
	echo "*
* Amara found"
fi
