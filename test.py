#!/usr/bin/python
# -*- coding: utf8 -*-
from time import time, localtime, strftime, sleep
import datetime
    
def get_work_days():
    day = datetime.date.today().strftime("%A")
    WORK_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    if day in WORK_DAYS:
        return True
    return False

def get_work_hours():
    WORK_HOURS = range(6, 22)
    hour = int(strftime("%H", localtime()))
    print hour
    if hour in WORK_HOURS:
        return True
    return False

def waituntil(period=30):
  #mustend = time() + timeout
  while time():# < mustend:
    print get_work_days
    print get_work_hours 
    print get_work_days()
    print get_work_hours()
    if get_work_days() and get_work_hours(): 
        print 'Yes'
        return True
    sleep(period)
  return False

if __name__ == '__main__':
    waituntil()
