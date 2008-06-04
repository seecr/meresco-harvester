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

set -o nounset
set -o errexit

function isSuSE {
	test -e /etc/SuSE-release
}
	
function isFedora {
	test -e /etc/fedora-release
}
		
function isDebian {
	test -e /etc/debian_version
}
			
PM_INSTALL="UNDEFINED"
isDebian && export PM_INSTALL="aptitude install"
isSuSE && export PM_INSTALL="yast --install"
isFedora && export PM_INSTALL="yum install"
			
if [ "$PM_INSTALL" == "UNDEFINED" ]; then
	echo "We are sorry, but your linux distribution is not supported!"
	exit 1
fi
					
function message {
 echo "
$1" | sed 's/^/* /'
}

function messageWithEnter {
	message "$1"
	read -p "Press [ENTER] to continue"
}

function isroot {
 if [ "`id -u`" != "0" ]
 then
   echo "Need to be root"
   exit -1
 fi
}

function init {
	isroot
	which sudo > /dev/null || $PM_INSTALL sudo
}

function create_user {
	username=$1
	if [ ! -d /home/$username ]
	then
		useradd --create-home $username
	fi
	sshdir=/home/$username/.ssh
	keyfile=$sshdir/id_rsa
	if [ ! -f $keyfile ]; then
		message  "Creating ssh-key"
		sudo -u $username mkdir --parents $sshdir
		sudo -u $username ssh-keygen -t rsa -f $keyfile -P ''
	fi

}

function aptitude_install {
	repository=$1
	distro=$2
	component=$3
	package=$4
	APTFILE=/etc/apt/sources.list.d/$distro'_'$component.list
	message "Adding temporary repository to APT ($repository $distro $component)"
	echo "deb $repository $distro $component" > $APTFILE
	aptitude update
	aptitude install $package
	message "Removing temporary repository ($repository $distro $component)"
	rm $APTFILE
	aptitude update
}

function ez_install {
	if [ -z "$(which easy_install)" ]; then
		cd /tmp
		wget http://peak.telecommunity.com/dist/ez_setup.py
		python ez_setup.py
		rm ez_setup.py
	fi
	easy_install $*
}

function install_sshkey {
	user=$1
	target_machine=$2
	target_user=$3
	(
		set +e
		ssh -i /home/$user/.ssh/id_rsa -o NumberOfPasswordPrompts=0 -o IdentitiesOnly=yes $target_user@$target_machine "echo test"

		if [ $? -ne 0 ]; then
			message "Enabling access for user $user to $target_user@$target_machine. Please provide root password."
			cat /home/$user/.ssh/id_rsa.pub | \
				ssh root@$target_machine "cat - >> /home/$target_user/.ssh/authorized_keys"
		fi
	)
}


function assert {
	assertion_cmd=$1
	message_when_fails=$2
	error=no
	trap "error=yes" HUP KILL INT ABRT STOP QUIT SEGV TERM EXIT
	$assertion_cmd
	if [ $? -ne 0  || "$error" == "yes" ]
	then
		message $message_when_fails
		exit -1
	fi
}

function hasPythonModule {
        mod_name=$1
        set +e
        python -c "import $mod_name"
        export _result=$?
        set -e
        return $_result
}

function addListenLine {
	port=$1
	if isSuSE; then
		portsconf=/etc/apache2/listen.conf
	elif isDebian; then
		portsconf=/etc/apache2/ports.conf
	elif isFedora; then
		portsconf=/etc/httpd/conf.d/000-ports.conf
	fi
	
	oldconfig=$(cat $portsconf | grep -v "^Listen\\W*$port\$")
	echo "$oldconfig" > $portsconf
	echo "Listen $port" >> $portsconf
}



USERINPUT=""

function show_question {
  USERINPUT=""

  local question="$1"
  if [ "$2" != "" ]; then  
    question="$question [$2]:"
  else
    question="$question "
  fi

  read -p "$question" USERINPUT
  if [ "$USERINPUT" == "" ]; then
    USERINPUT=$2
  fi
}

function ask_question {
  question=$1
  default=$2

  valid=""
  if [ $# -ge 3 ]; then
    shift 2
    valid=[$(echo $@ | tr ' ' ',')]
    question="$question ($(echo $@ | tr ' ' '/'))"
  fi

  question_answered="N"
  while [ $question_answered == "N" ]
  do
    show_question "$question" "$default"
    if [ "$valid" != "" ]; then
      case $USERINPUT in
        $valid) question_answered="Y";;
        *) question_answered="N";;
      esac
    else
      question_answered="Y"
    fi
  done
}



