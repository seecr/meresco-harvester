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
# Copyright Seek You Too BV

source $(dirname $0)/functions.sh
isroot

if ! hasPythonModule mod_python ; then
	message "Installing mod_python"
	(
	cd /tmp
	wget "http://www.eu.apache.org/dist/httpd/modpython/mod_python-3.2.10.tgz"
	tar xzvf mod_python-3.2.10.tgz
	cd mod_python-3.2.10
	# Patch to make mod_python-3.2.10 work with bash 3.1.xx
	# See https://issues.apache.org/jira/browse/MODPYTHON-122
	sed --in-place sX'^MP_VERSION=`echo $MP_VERSION | sed s/\\\\"//g`$'X'MP_VERSION=`echo $MP_VERSION | sed s/\\"//g`'X configure
	if isSuSE ; then
		./configure --with-apxs=`which apxs2-worker`
	else
		./configure
	fi
	make
	make install
	)
else
	message "mod_python found"
fi

if isSuSE ; then
	message "Enabling mod_python"
	echo "LoadModule python_module	/usr/lib/apache2-worker/mod_python.so" > /etc/apache2/conf.d/mod_python.conf
elif isFedora ; then
	message "Enabling mod_python"
	echo "LoadModule python_module  modules/mod_python.so" > /etc/httpd/conf.d/000-modules.conf
elif isDebian ; then
	if [ ! -f /etc/apache2/mods-enabled/mod_python.load ]; then
		message "Enabling mod_python"
		echo "LoadModule python_module /usr/lib/apache2/modules/mod_python.so" > /etc/apache2/mods-available/mod_python.load
		ln -sf /etc/apache2/mods-available/mod_python.load /etc/apache2/mods-enabled/mod_python.load
	fi
fi
