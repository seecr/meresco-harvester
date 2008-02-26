#!/bin/bash

if [ "$INSTALL_OPTIONS_FILE" == "" ]; then
	echo "INSTALL_OPTIONS_FILE not set"
	exit 2
fi

basedir=$(cd $(dirname $0); pwd)
source $basedir/functions.sh

#DEFAULTS
SAHARA_SERVERNAME=""
SAHARA_HTTPS_PORT=""
SAHARA_HTTP_PORT=""
OPEN_FIREWALL="N"
INSTALL_MOD_PYTHON_TOOLS="N"
ENABLE_MOD_PYTHON="N"

message 'This will install and configure SAHARA, containing all necessary
components. Some steps in this installation may require your confirmation or
new information. It is generally safe to answer Yes to Yes/No questions.

Note that it is a prerequisite for this script to have an up-to-date system.'
if isDebian ; then
	message "Debian version 4.0 (etch).
Make sure your /etc/apt/sources.list contains references to Debian version 4.0
and then use:
$ aptitude update
$ aptitude dist-upgrade"
fi

messageWithEnter 'It is safe to exit this script at any time by pressing CTRL+C.

The install script expects that the harvester will be run as the user sahara.
An admin account will be created to access Sahara.

It is also safe to run the script multiple times. Configuration information
must be re-entered.'

ask_question "What will be the home directory for SAHARA?" "$(cd $basedir/..;pwd)"
SAHARA_HOME_DIR=$USERINPUT

CQ2_DEP_DIR=$SAHARA_HOME_DIR/lib
SAHARA_SLOWFOOT_DIR=$CQ2_DEP_DIR/slowfoot
SAHARA_DIR=$SAHARA_HOME_DIR/wcp
SAHARA_DATA_DIR=$SAHARA_DIR/data

message 'SAHARA requires the following third-party software products:
 - Apache version 2.0 or higher
 - Python 2.4
 - mod_python 3.2.10 or higher

The installation will now proceed with installing these components. If they
are already installed or you wish to install them yourself answer N to the
following questions.'

message 'Slowfoot, a part of SAHARA, requires a special group. This can be done 
automatically by the installer.'
ask_question "Create group automatically?" "N" Y N
CREATE_SLOWFOOT_GROUP=$USERINPUT

ask_question "Install Python?" "N" Y N
INSTALL_PYTHON=$USERINPUT

ask_question "Install the Amara toolkit?" "N" Y N
INSTALL_AMARA=$USERINPUT
ask_question "Install the 4 Suite toolkit?" "N" Y N
INSTALL_4SUITE=$USERINPUT

ask_question "Install Apache?" "N" Y N
INSTALL_APACHE=$USERINPUT

if [ "$INSTALL_APACHE" == "Y" ]; then
	ask_question "Hostname for the SAHARA web interface (e.g. www.example.org)" $(hostname)
	SAHARA_SERVERNAME=$USERINPUT
	ask_question "HTTPS port for SAHARA" "443"
	SAHARA_HTTPS_PORT=$USERINPUT
	ask_question "HTTP port for SAHARA" "80"
	SAHARA_HTTP_PORT=$USERINPUT
	if isDebian ; then
		ask_question "Shall we open port $SAHARA_HTTP_PORT and $SAHARA_HTTPS_PORT on your firewall?" "Y" Y N
		OPEN_FIREWALL=$USERINPUT
	fi
fi

ask_question "Append setting PYHTONPATH to your .bashrc?" "N" Y N
MODIFY_BASHRC=$USERINPUT

ask_question "Install gcc and make?" "N" Y N
INSTALL_COMPILER=$USERINPUT

ask_question "Install mod_python 3.2.10?" "N" Y N
INSTALL_MOD_PYTHON=$USERINPUT

if [ "$INSTALL_MOD_PYTHON" == "Y" ]; then
	ask_question "Install additional tools needed to install mod_python?" "N" Y N
	INSTALL_MOD_PYTHON_TOOLS=$USERINPUT
	ask_question "Enable mod_python in Apache after install?" "N" Y N
	ENABLE_MOD_PYTHON=$USERINPUT

fi

cat << EOF > $INSTALL_OPTIONS_FILE
# created $(date)
export INSTALL_APACHE=$INSTALL_APACHE
export INSTALL_PYTHON=$INSTALL_PYTHON
export INSTALL_MOD_PYTHON=$INSTALL_MOD_PYTHON
export INSTALL_AMARA=$INSTALL_AMARA
export INSTALL_4SUITE=$INSTALL_4SUITE

export ENABLE_MOD_PYTHON=$ENABLE_MOD_PYTHON
export INSTALL_MOD_PYTHON_TOOLS=$INSTALL_MOD_PYTHON_TOOLS
export INSTALL_COMPILER=$INSTALL_COMPILER
export MODIFY_BASHRC=$MODIFY_BASHRC
export OPEN_FIREWALL=$OPEN_FIREWALL
export CQ2_DEP_DIR=$SAHARA_HOME_DIR/lib
export CREATE_SLOWFOOT_GROUP=$CREATE_SLOWFOOT_GROUP

export SAHARA_HOME_DIR=$SAHARA_HOME_DIR
export SAHARA_SLOWFOOT_DIR=$CQ2_DEP_DIR/slowfoot
export SAHARA_DIR=$SAHARA_HOME_DIR/wcp
export SAHARA_DATA_DIR=$SAHARA_DIR/data
export SAHARA_SERVERNAME=$SAHARA_SERVERNAME
export SAHARA_HTTPS_PORT=$SAHARA_HTTPS_PORT
export SAHARA_HTTP_PORT=$SAHARA_HTTP_PORT
EOF
