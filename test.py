#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      richard
#
# Created:     14.01.2016
# Copyright:   (c) richard 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from PeopleCounterFast import *
from PeriodicTimer import *
from PostOccupancy import *
import requests, json, math, random, time

def main():
    global myThread
    global myPoster
    myThread = PeopleCounterFast(240,360,150,1,1,15,70,0,'STREAM','newvid.h264',True)
    myPoster = PostOccupancy()
    myTimer = PeriodicTimer(30, printOccupancy)
    myThread.start()
    myTimer.start()
    
    try:
        while 1:
            pass
    except KeyboardInterrupt:
            myTimer.cancel()
            myThread.stop()
            GPIO.cleanup()

def printOccupancy():
    if time.strftime("%H:%M") == '00:10':
        myThread.reset()
    myPoster.postOccupancy(myThread.getOccupancy(), myThread.getIn(), myThread.getOut())
##    print("Postig current occupancy")
##    print(str(myThread.getOccupancy()))
##    print("Postig total leaving")
##    print(str(myThread.getOut()))
##    print("Postig total coming in")
##    print(str(myThread.getIn()))
    #print("Last post: " + str(myPoster.readLastPost()))
    return True

if __name__ == '__main__':
    main()
