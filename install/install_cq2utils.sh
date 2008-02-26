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

set -o errexit

cq2utils_version=2.4.3

basedir=$(cd $(dirname $0); pwd)
source $basedir/functions.sh

isroot

if [ -z "$1" ]; then 
	echo "No cq2 dependency dir given."
	exit 1
fi
cq2_dep_dir=$1
cq2utilsdir=$cq2_dep_dir/cq2utils


if [ ! -d $cq2utilsdir ]; then
	cq2utilspack=$basedir/../dist/cq2utils_$cq2utils_version.tar.gz
	mkdir -p $cq2_dep_dir
	tar --directory $cq2_dep_dir -xzf $cq2utilspack
	mv $cq2_dep_dir/cq2utils_$cq2utils_version/cq2utils $cq2_dep_dir/cq2utils
	rm -rf $cq2_dep_dir/cq2utils_$cq2utils_version
fi
	
