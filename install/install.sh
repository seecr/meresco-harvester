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


basedir=$(cd $(dirname $0); pwd)

INSTALL_OPTIONS_FILE=$INSTALL_OPTIONS_FILE

source $basedir/functions.sh

isroot
chmod +x $basedir/*.sh

RESTART_APACHE=Yes
if [ "$INSTALL_OPTIONS_FILE" != "" ]; then
	source $INSTALL_OPTIONS_FILE
	RESTART_APACHE=No
else
	message 'This will install and configure SAHARA, containing all necessary
components. Some steps in this installation may require your confirmation or
new information. It is generally safe to answer Yes to Yes/No questions.

Note that it is a prerequisite for this script to have an up-to-date system.'
	if isDebian ; then
		message "DEBIAN TESTING.
Make sure your /etc/apt/sources.list contains references to debian testing
and then use:
$ aptitude update
$ aptitude dist-upgrade"
	fi

	message 'It is safe to exit this script at any time by pressing CTRL+C.

The install script expects that the harvester will be run as the user sahara.
An admin account will be created to access Sahara.

It is also safe to run the script multiple times. Configuration information
must be re-entered.
Press [ENTER] to continue'
	read
	SAHARA_HOME_DIR=$(cd $basedir/..;pwd)
	CQ2_DEP_DIR=$SAHARA_HOME_DIR/lib
	message "Sahara will be installed in the directory:
$SAHARA_HOME_DIR
Dependencies will be installed in:
$CQ2_DEP_DIR"
	SAHARA_SLOWFOOT_DIR=$CQ2_DEP_DIR/slowfoot
	SAHARA_DIR=$SAHARA_HOME_DIR/wcp
	SAHARA_DATA_DIR=$SAHARA_DIR/data
	guess=$(hostname)
	message "Specify the hostname which will be used to access the sahara web
interface (e.g. www.example.org):
[$guess]"
	read SAHARA_SERVERNAME
	if [ -z "$SAHARA_SERVERNAME" ]; then SAHARA_SERVERNAME=$guess; fi
	SAHARA_HTTPS_PORT=443
	SAHARA_HTTP_PORT=80
fi

set -o errexit

init

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
cat /etc/group | grep slowfoot || /usr/sbin/groupadd slowfoot

# Add the user under which apache runs to the slowfoot group.
isSuSE && apache_user=wwwrun 
isDebian && apache_user=www-data
isFedora && apache_user=apache

/usr/sbin/usermod -G slowfoot $apache_user

# Add user sahara to the slowfoot group.
/usr/sbin/usermod -G slowfoot sahara

message "Creating user admin, you will be asked to supply a password. Remember this
password to access Sahara over the web later."
(
  cd $SAHARA_DIR
  export PYTHONPATH=$SAHARA_HOME_DIR:$CQ2_DEP_DIR
  python saharasecurity.py
)

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
    message "WARNING: You have enabled cache modules for apache:
$(find /etc/apache2/mods-enabled/ -name "*cache*")
This will interfere with the proper functioning of Sahara.
Please disable these modules.
[Press ENTER to continue]"
    read
  fi
elif isSuSE ; then
	echo "LoadModule rewrite_module  /usr/lib/apache2-worker/mod_rewrite.so" > /etc/apache2/conf.d/mod_rewrite.conf  
	echo "LoadModule proxy_module  /usr/lib/apache2-worker/mod_proxy.so" > /etc/apache2/conf.d/mod_proxy.conf
	echo "LoadModule proxy_http_module  /usr/lib/apache2-worker/mod_proxy_http.so" > /etc/apache2/conf.d/mod_proxy_http.conf
fi

message "Creating apache configuration"

isDebian && configfile=/etc/apache2/sites-available/sahara.conf
isSuSE && configfile=/etc/apache2/vhosts.d/000-sahara.conf
isFedora && configfile=/etc/httpd/conf.d/000-sahara.conf

isDebian && apachelogdir=/var/log/apache2
isSuSE && apachelogdir=/var/log/apache2
isFedora && apachelogdir=/var/log/httpd

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

if isDebian ; then
  ln -sf /etc/apache2/sites-available/sahara.conf /etc/apache2/sites-enabled/000-sahara.conf
fi

addListenLine $SAHARA_HTTPS_PORT
addListenLine $SAHARA_HTTP_PORT

test -d $SAHARA_HOME_DIR/ssl || mkdir -p $SAHARA_HOME_DIR/ssl

if isDebian ; then
	message "Shall we open port $SAHARA_HTTP_PORT and $SAHARA_HTTPS_PORT on your firewall. [Y/n]"
	read openfirewall
case $openfirewall in
	'' | y* | Y* ) 
	echo "#!/bin/bash
IPTABLES=/sbin/iptables
\$IPTABLES --list --numeric | grep \"ACCEPT.*tcp.*dpt\:$SAHARA_HTTP_PORT \"|| \$IPTABLES -A INPUT -i eth0 -p tcp --dport $SAHARA_HTTP_PORT -j ACCEPT
\$IPTABLES --list --numeric | grep \"ACCEPT.*tcp.*dpt\:$SAHARA_HTTPS_PORT \"|| \$IPTABLES -A INPUT -i eth0 -p tcp --dport $SAHARA_HTTPS_PORT -j ACCEPT" > /etc/network/if-up.d/firewall_sahara
	chmod +x /etc/network/if-up.d/firewall_sahara
	/etc/network/if-up.d/firewall_sahara
	;;
esac
else
	message "Please open port  $SAHARA_HTTP_PORT and $SAHARA_HTTPS_PORT on your firewall."
fi

echo "localhosturl='http://localhost:$SAHARA_HTTP_PORT'" > /tmp/slowconfig.py
sudo -u sahara cp /tmp/slowconfig.py $SAHARA_DIR

isSuSE && apacheControl=apache2ctl
isDebian && apacheControl=apache2ctl
isFedora && apacheControl=apachectl


if isFedora ; then 
	chmod a+rx /home/sahara
fi

message "Installation of Sahara is finished.

However there are some things you still need to do:
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

