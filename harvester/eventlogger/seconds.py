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

import time,sys

def seconds(aLogTime):
  timepart = aLogTime[1:20]
  mseconds = int(aLogTime[21:24])/1000.0
  return time.mktime(time.strptime(timepart, '%Y-%m-%d %H:%M:%S')) + mseconds, aLogTime

class TimeDiffer:
  def __init__(self):
    self.startid = None
    self.starttime = None
  def process(self, time, id, comment):
    if comment == 'START':
      self.startid = id
      self.starttime = time
    if comment == 'END' and id == self.startid:
      print '\t'.join([id, str(time[0] - self.starttime[0]), self.starttime[1][12:24],time[1][12:24]])

if __name__ == '__main__':
  lines = filter(None, map(str.strip, sys.stdin))
  splitted = filter(lambda a:len(a) == 4, map(lambda line:line.split('\t'), lines))
  timelines = map(lambda (time,event,id, comment):(seconds(time),event,id,comment), splitted)
  filtered = filter(lambda (time,event,id, comment): event == 'UPLOAD.SEND', timelines)
  d = TimeDiffer()
  for time, event, id, comment in filtered:
    d.process(time, id, comment)
