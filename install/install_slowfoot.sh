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

slowfoot_version=6.4.2

basedir=$(cd $(dirname $0); pwd)
source $basedir/functions.sh

isroot

if [ -z "$1" ]; then 
	echo "No cq2 dependency dir given."
	exit 1
fi
cq2_dep_dir=$1
slowfootdir=$cq2_dep_dir/slowfoot

if [ ! -d $slowfootdir ]; then
	slowfootpack=$basedir/../dist/slowfoot_$slowfoot_version.tar.gz
	mkdir -p $cq2_dep_dir
	tar --directory $cq2_dep_dir -xzf $slowfootpack
	mv $cq2_dep_dir/slowfoot_$slowfoot_version/slowfoot $cq2_dep_dir/slowfoot
	rm -rf $cq2_dep_dir/slowfoot_$slowfoot_version
fi
	

message 'Installing Slowfoot dependencies'
message "Installing required packages."

if isSuSE ; then
	which python2.4 || $PM_INSTALL python
	test -d /usr/lib/python2.4/xml || $PM_INSTALL python-xml
	test -e /usr/include/python2.4/Python.h || $PM_INSTALL python-devel
	which apache2ctl && apache2ctl -l | grep worker || $PM_INSTALL apache2-worker
	test -d /usr/include/apache2 || $PM_INSTALL apache2-devel
	which make || $PM_INSTALL make
	which gcc || $PM_INSTALL gcc
	
	mv /usr/lib/python2.4/distutils/distutils.cfg /tmp
	$basedir/install_4suite.sh
	mv /tmp/distutils.cfg /usr/lib/python2.4/distutils/distutils.cfg

	$basedir/install_amara_1.1.7.sh
elif isDebian ; then 	
	$PM_INSTALL python2.4 python2.4-dev python-xml apache2-dev flex  make gcc apache2-mpm-worker bzip2 tar
	# The link to python should be done in the following way.
	# Else python-central can't find the correct default_version.
	(cd /usr/bin; ln -sf python2.4 python)
	aptitude_install http://ftp.nl.debian.org/debian/ testing non-free python-profiler
	$basedir/install_4suite.sh
	$basedir/install_amara_1.1.7.sh

elif isFedora ; then
	$PM_INSTALL python python-devel httpd httpd-devel mod_ssl flex make gcc python-4Suite-XML python-amara
	mv /usr/sbin/httpd /usr/sbin/httpd.prefork
	ln -s /usr/sbin/httpd.worker /usr/sbin/httpd
fi


# compile the suidwrappers slowfoot uses for account creation
(
  cd $slowfootdir/suidwrapper
  make
  ./fixperms.sh
)


sh $basedir/install_mod_python_3.2.10.sh
