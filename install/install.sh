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


basedir=$(cd $(dirname $0); pwd)

source $basedir/functions.sh
isroot
chmod +x $basedir/*.sh

if [ $# -eq 1 ] ; then
	INSTALL_OPTIONS_FILE=$1
else
	export INSTALL_OPTIONS_FILE=/tmp/sahara_install.options
	# ask the person behind the keyboard some questions, save the answers
	# and source them in.
	$basedir/readoptions.sh
fi

source $INSTALL_OPTIONS_FILE

TODO_FILE=$basedir/TODO
function logToDo {
	echo $1 >> $TODO_FILE
}

message "Sahara will be installed in the directory:
$SAHARA_HOME_DIR
Dependencies will be installed in:
$CQ2_DEP_DIR"

set -o errexit
init

echo "TODO items after installation performed on $(date)" > $TODO_FILE

$basedir/install_slowfoot.sh $CQ2_DEP_DIR
$basedir/install_cq2utils.sh $CQ2_DEP_DIR

# make world writable so that the apache user can write files from 
# the edit-template
mkdir --parents $SAHARA_DATA_DIR
chmod a+rw -R $SAHARA_DATA_DIR

# The standard encoding needs to be utf-8. This is accomplished by setting
# the default system encoding for python using the sitecustomize.py file.
cp $SAHARA_SLOWFOOT_DIR/sitecustomize.py /usr/lib/python2.4/site-packages

# Create a slowfoot usergroup. This group is used to group users of slowfoot 
# together and provide file access.
if [ "$CREATE_SLOWFOOT_GROUP" == "Y" ] ; then
	# Add user sahara to the slowfoot group.
	/usr/sbin/usermod -G slowfoot sahara
else
	logToDo "- create a group called slowfoot and add the sahara user to it"
fi

todoMessage="- Add the user under which apache runs to the group called slowfoot"
if [ "$INSTALL_APACHE" == "Y" ]
then
	if [ "$CREATE_SLOWFOOT_GROUP" == "Y" ] ; then
		# Add the user under which apache runs to the slowfoot group.
		isSuSE && apache_user=wwwrun 
		isDebian && apache_user=www-data
		isFedora && apache_user=apache
		
		/usr/sbin/usermod -G slowfoot $apache_user
	else
		logToDo "$todoMessage"
	fi
else
	logToDo "$todoMessage"
fi

message "Creating user admin, you will be asked to supply a password. Remember this
password to access Sahara over the web later."
(
  cd $SAHARA_DIR
  export PYTHONPATH=$SAHARA_HOME_DIR:$CQ2_DEP_DIR
  python saharasecurity.py
)

if [ "$INSTALL_APACHE" == "Y" ]
then
	# MODULES
	if isDebian ; then
		for i in 'mod_python.load' 'rewrite.load' 'ssl.load' 'ssl.conf' 'proxy.load' 'cgid.conf' 'cgid.load'; do
			if [ ! -e /etc/apache2/mods-available/$i ]; then
				message "WARNING: module $i not found in /etc/apache2/mods-available - press ENTER to continue"
				read
			else
				ln -sf /etc/apache2/mods-available/$i /etc/apache2/mods-enabled/$i
			fi
		done
		# Disable all cache modules
		if [ $(find /etc/apache2/mods-enabled/ -name "*cache*" |  wc -l) -gt 0 ]; then
			messageWithEnter "WARNING: You have enabled cache modules for apache:
$(find /etc/apache2/mods-enabled/ -name "*cache*")
This will interfere with the proper functioning of Sahara.
Please disable these modules."
		fi
	elif isSuSE ; then
		echo "LoadModule rewrite_module  /usr/lib/apache2-worker/mod_rewrite.so" > /etc/apache2/conf.d/mod_rewrite.conf  
		echo "LoadModule proxy_module  /usr/lib/apache2-worker/mod_proxy.so" > /etc/apache2/conf.d/mod_proxy.conf
		echo "LoadModule proxy_http_module  /usr/lib/apache2-worker/mod_proxy_http.so" > /etc/apache2/conf.d/mod_proxy_http.conf
	fi
else
		logToDo "- Enable apache modules: mod_python, rewrite, ssl, proxy and cgid"
		logToDo "- Make sure apache's cache modules are disabled"
fi

if [ "$INSTALL_APACHE" == "Y" ] ; then	
	isDebian && configfile=/etc/apache2/sites-available/sahara.conf
	isSuSE && configfile=/etc/apache2/vhosts.d/000-sahara.conf
	isFedora && configfile=/etc/httpd/conf.d/000-sahara.conf
	
	isDebian && apachelogdir=/var/log/apache2
	isSuSE && apachelogdir=/var/log/apache2
	isFedora && apachelogdir=/var/log/httpd
else
	test -d $SAHARA_HOME_DIR/config || mkdir -p $SAHARA_HOME_DIR/config
	sudo chown sahara $SAHARA_HOME_DIR/config
	configfile=$SAHARA_HOME_DIR/config/sahara.conf
	apachelogdir="<APACHE LOGDIRECTORY>"
	export SAHARA_SERVERNAME="<SERVER NAME>"
	export SAHARA_HTTPS_PORT="443"
  export SAHARA_HTTP_PORT="80"
	logToDo "- Complete and enable the apache configuration stored in $configfile"
fi
message "Creating apache configuration in $configfile"
	
(
	cat << EOF
<Directory $SAHARA_HOME_DIR/wcp>
	SetHandler mod_python
	PythonHandler slowfoothandler
	PythonPath "['$SAHARA_HOME_DIR/wcp', '$SAHARA_SLOWFOOT_DIR', '$SAHARA_HOME_DIR/harvester', '$CQ2_DEP_DIR']+sys.path"
	PythonAutoReload On
	PythonDebug On
	PythonOption secureurl "https://$SAHARA_SERVERNAME:$SAHARA_HTTPS_PORT"
	#PythonEnablePdb On
	Order Allow,Deny
	Allow from All
</Directory>

NameVirtualHost *:$SAHARA_HTTP_PORT
NameVirtualHost *:$SAHARA_HTTPS_PORT
NameVirtualHost 127.0.0.1:$SAHARA_HTTP_PORT

<VirtualHost 127.0.0.1:$SAHARA_HTTP_PORT>
	ServerName $SAHARA_SERVERNAME
	DocumentRoot $SAHARA_HOME_DIR/wcp
</VirtualHost>

<VirtualHost *:$SAHARA_HTTP_PORT>
	ServerName $SAHARA_SERVERNAME
	RewriteEngine On
	RewriteCond   %{SERVER_PORT}  !^$SAHARA_HTTPS_PORT\$
	RewriteRule ^/(.*)$ https://$SAHARA_SERVERNAME:$SAHARA_HTTPS_PORT/\$1 [L,R]
</VirtualHost>

<VirtualHost *:$SAHARA_HTTPS_PORT>
	SSLEngine on
	SSLCertificateFile $SAHARA_HOME_DIR/ssl/server.crt
	SSLCertificateKeyFile $SAHARA_HOME_DIR/ssl/server.pem

	ServerName $SAHARA_SERVERNAME
	DocumentRoot $SAHARA_HOME_DIR/wcp

	CustomLog $apachelogdir/access.secure.log combined
	ErrorLog $apachelogdir/error.secure.log
</VirtualHost>
EOF
	) > $configfile

# Enable apache configuration and add Listen lines to ports.conf	
if [ "$INSTALL_APACHE" == "Y" ] ; then
	if isDebian ; then
		ln -sf /etc/apache2/sites-available/sahara.conf /etc/apache2/sites-enabled/000-sahara.conf
	fi
	
	addListenLine $SAHARA_HTTPS_PORT
	addListenLine $SAHARA_HTTP_PORT
fi

# Create a directory for ssl is it does not already exist
test -d $SAHARA_HOME_DIR/ssl || mkdir -p $SAHARA_HOME_DIR/ssl

# Ports on the firewall need to be open to reach apache
if [ "$INSTALL_APACHE" == "Y" ] ; then
	if isDebian ; then
		if [ "$OPEN_FIREWALL" == "Y" ] ; then
			echo "#!/bin/bash
	IPTABLES=/sbin/iptables
	\$IPTABLES --list --numeric | grep \"ACCEPT.*tcp.*dpt\:$SAHARA_HTTP_PORT \"|| \$IPTABLES -A INPUT -i eth0 -p tcp --dport $SAHARA_HTTP_PORT -j ACCEPT
	\$IPTABLES --list --numeric | grep \"ACCEPT.*tcp.*dpt\:$SAHARA_HTTPS_PORT \"|| \$IPTABLES -A INPUT -i eth0 -p tcp --dport $SAHARA_HTTPS_PORT -j ACCEPT" > /etc/network/if-up.d/firewall_sahara
			chmod +x /etc/network/if-up.d/firewall_sahara
			/etc/network/if-up.d/firewall_sahara
		fi
	else
		logToDo "Please open port  $SAHARA_HTTP_PORT and $SAHARA_HTTPS_PORT on your firewall."
	fi
fi

if [ "$INSTALL_APACHE" == "Y" ] ; then
	slowconfigfile=$SAHARA_DIR/slowconfig.py
else
	SAHARA_HTTP_PORT="<HTTP PORTNUMBER>"
	slowconfigfile=$SAHARA_HOME_DIR/config/slowconfig.py
	logToDo "- Complete $slowconfigfile and place it in $SAHARA_DIR"
fi

echo "localhosturl='http://localhost:$SAHARA_HTTP_PORT'" > /tmp/slowconfig.py
sudo -u sahara cp /tmp/slowconfig.py $slowconfigfile

# homedirectory needs to be readable for the apache user
if isFedora ; then 
	chmod a+rx $SAHARA_HOME_DIR
fi

if [ "$MODIFY_BASHRC" == "Y" ]; then
	DIRECTORY=$(cat /etc/passwd | grep "^sahara" | cut -d: -f6)
	cat << EOF >> $DIRECTORY/.bashrc
export PYTHONPATH=$CQ2_DEP_DIR
EOF
else
	logToDo "- set the PYTHONPATH variable to contain $CQ2_DEP_DIR"
fi

message "Installation of Sahara is finished.

However there are some things you still need to do:
- Check the file $TODO_FILE for the remaining configuration tasks
- Create a SSL certificate, name the files server.<extension> and place them
  in $SAHARA_HOME_DIR/ssl
  See the SaharaManual for more information on SSL.
- Restart the webserver yourself.
- Check if apache is started at boot time.
- Check http://$SAHARA_SERVERNAME to see if the Sahara Web Control Panel works
  correctly.
- Configure a domain, repositorie, users and such in the Control Panel before
  harvesting.
- To start harvesting, you must log into shell on the server as 'sahara'
  and go to $SAHARA_HOME_DIR/harvester, and then run:
    './startharvester.sh <options>'
  For more information on harvesting see the SaharaManual.

Good luck!
"
