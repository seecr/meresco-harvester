## begin license ##
# 
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for 
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl 
# 
# Copyright (C) 2010-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# 
# This file is part of "Meresco Harvester"
# 
# "Meresco Harvester" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Meresco Harvester" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Meresco Harvester"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

set -e
mydir=$(cd $(dirname $0); pwd)

fullPythonVersion=python2.6

VERSION="x.y.z"

rm -rf tmp build

${fullPythonVersion} setup.py install --root tmp

if [ -f /etc/debian_version ]; then
    LOCAL_DIR=`pwd`/tmp/usr/local
    SITE_PACKAGES_DIR=${LOCAL_DIR}/lib/${fullPythonVersion}/dist-packages
    BIN_DIR=${LOCAL_DIR}/bin
else
    LOCAL_DIR=`pwd`/tmp/usr
    SITE_PACKAGES_DIR=${LOCAL_DIR}/lib/${fullPythonVersion}/site-packages
    BIN_DIR=${LOCAL_DIR}/bin
fi

cp -r test tmp/test
find tmp -type f -exec sed -r -e \
    "/DO_NOT_DISTRIBUTE/d;
    s,^binDir.*$,binDir='$BIN_DIR',;
    s,^examplesPath.*$,examplesPath='$mydir/examples',;
    s/\\\$Version:[^\\\$]*\\\$/\\\$Version: ${VERSION}\\\$/" -i {} \;

cp meresco/__init__.py ${SITE_PACKAGES_DIR}/meresco
export PYTHONPATH=${SITE_PACKAGES_DIR}:${PYTHONPATH}

teststorun=$1
if [ -z "$teststorun" ]; then
    teststorun="alltests.sh integrationtest.sh"
else
    shift
fi

echo "Will now run the tests:"
for f in $teststorun; do
    echo "- $f"
done
echo "Press [ENTER] to continue"
read

for testtorun in $teststorun; do
    set +o errexit
    (
    cd tmp/test
    ./$testtorun "$@"
    )
    set -o errexit
    echo "Finished $testtorun, press [ENTER] to continue"
    read
done

rm -rf tmp build

