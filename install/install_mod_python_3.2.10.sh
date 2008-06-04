#!/bin/bash
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
# Copyright Seek You Too BV

source $(dirname $0)/functions.sh
isroot

if [ "$INSTALL_MOD_PYTHON_TOOLS" == "Y" ]; then
	message "Installing tools to build mod_python."
	TOOLS=""
	for command in make gcc flex tar gzip wget
	do
		which $command > /dev/null || TOOLS="$command $TOOLS"
	done
	if [ "$TOOLS" == "" ]; then
		message "All required tools have already been installed."
	else
		message "Installing $TOOLS"
		$PM_INSTALL $TOOLS
	fi

	message "Installing development environment for apache2"
	if isSuSE ; then
		test -d /usr/include/apache2 || $PM_INSTALL apache2-devel
	elif isDebian ; then 	
		$PM_INSTALL apache2-dev
	elif isFedora ; then
		$PM_INSTALL httpd-devel
	fi
fi

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

if [ "$ENABLE_MOD_PYTHON" == "Y" ]; then
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
fi
