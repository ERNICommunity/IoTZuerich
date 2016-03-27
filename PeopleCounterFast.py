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

import threading, datetime, Queue, sqlite3, sys, os, numpy as np, cv2, math
#TODO: Import additional libraries
from picamera.array import PiRGBArray
from picamera import PiCamera
import time

def main():
    pass

class PeopleCounterFast(threading.Thread):
    def __init__(self,resX, resY, barrier, frameRatio = 1, minAvg = 1, minSpeed = 16,maxSpeed=100,occupancy = 0,inputType = 'STREAM',input = '', display=False):
        threading.Thread.__init__(self)
        self.Running = False
        self.barrier = barrier #placement of counting barrier on y-axis
        self.frameRatio = frameRatio #consider every n-th frame
        self.occupancy = occupancy #current occupancy when thread is started
        self.inputType = inputType #either VIDEO or STREAM. Default is stream
        self.input = input #input source in case of inputType = 'VIDEO'
        self.display = display #display output or not
        self.resX = resX #x-resolution of video
        self.resY = resY #y-resolution of video
        self.minAvg = minAvg
        self.minSpeed = minSpeed #minimum amount of pixsels the centroid needs to move in order to be considered as an object (not noise)
        self.maxSpeed = maxSpeed
        #usually 0
        self.cameraPort = 0

    #calculate difference image between the last three images
    def diffImg(self, t0, t1, t2):
        d1 = cv2.absdiff(t2, t1)
        d2 = cv2.absdiff(t1, t0)
        return cv2.bitwise_and(d1, d2)

    def run(self):
        #Video goes here. New videos / camera setup need new parametrization:
        #if an input file is selected
        if self.inputType == 'FILE':
            cap = cv2.VideoCapture(self.input)
        else:
            camera = PiCamera()
            camera.resolution = (self.resX, self.resY)
            camera.framerate = 4
            rawCapture = PiRGBArray(camera, size=(self.resX, self.resY))
            # allow the camera to warmup
            time.sleep(0.5)

        #reset counter
        self.countIn = 0
        self.countOut = 0
        #Labeling font
        font = cv2.FONT_HERSHEY_SIMPLEX
        #read initial first three frames
        #greyscale-conversion
        if self.inputType == 'FILE':
            im1 = cap.read()[1]
            im2 = cap.read()[1]
            im3 = cap.read()[1]
        else:
            camera.capture(rawCapture, format="bgr")
            im1 = rawCapture.array
            rawCapture.truncate(0)
            camera.capture(rawCapture, format="bgr")
            im2 = rawCapture.array
            rawCapture.truncate(0)
            camera.capture(rawCapture, format="bgr")
            im3 = rawCapture.array
            rawCapture.truncate(0)
        
        self.framet_2 = cv2.cvtColor(im1, cv2.COLOR_RGB2GRAY)
        self.framet_1 = cv2.cvtColor(im2, cv2.COLOR_RGB2GRAY)
        self.framet_0 = cv2.cvtColor(im3, cv2.COLOR_RGB2GRAY)
        #calculate first difference image
        self.diffNow = self.diffImg(self.framet_2, self.framet_1, self.framet_0)
        #get moments and calculate initial centroid
        M = cv2.moments(self.diffNow)
        if(M['m00'] != 0):
            self.cx_old = int(M['m10']/M['m00'])
            self.cy_old = int(M['m01']/M['m00'])
        else:
            self.cx_old = 0
            self.cy_old = 0
        #calculate initial mean
        self.avg_old = cv2.mean(self.diffNow)

        #reset frame-counter
        self.frameCounter = 0

        self.Running = True
        #do until user interruption
        #while(self.Running == True):
        for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):


            #read next frame and increase counter
            if self.inputType == 'FILE':
                #stop thread if video capture is interrupted
                if (cap.isOpened() != True):
                    self.stop
                    break
                else:
                    currImg = cap.read()[1]
                    
            else:
                currImg = rawCapture.array
                
            self.frameCounter +=1
            rawCapture.truncate(0)

            #consider every n-th frame for a calculation
            if ((self.frameCounter-1) % self.frameRatio) == 0:
                #timer for debugging
                a = int(round(time.time() * 1000))
                #update historic frames and calculate current differenc
                self.framet_2 = self.framet_1
                self.framet_1 = self.framet_0
                self.framet_0 = cv2.cvtColor(currImg, cv2.COLOR_RGB2GRAY)
                self.diffNow = self.diffImg(self.framet_2, self.framet_1, self.framet_0)
                #mean color of image
                curr_avg = cv2.mean(self.diffNow)
                #no movement: all pixels are black = 0
                #movement: pixels become whiter
                #if average color is larger than zero, we consider possible movement of people
                if curr_avg[0] > self.minAvg:
                    #calculate centroid
                     M = cv2.moments(self.diffNow)
                     if(M['m00'] != 0):
                        cx = int(M['m10']/M['m00'])
                        cy = int(M['m01']/M['m00'])
                     else:
                        cx = 0
                        cy = 0
                     #check whether the centroid crossed the artificial barrier in either direction and moves
                     #faster than the minimal speed
                     if self.cy_old > self.barrier and cy < self.barrier and abs(self.cy_old -cy) > self.minSpeed and self.maxSpeed > abs(self.cy_old -cy):
                        self.countOut += 1
                        self.occupancy -= 1
                        print("Average: " + str(curr_avg[0]))
                        print("Distance: " + str(self.cy_old -cy))
                        print("Occupancy: " + str(self.occupancy))
                        print("Out: " + str(self.countOut))
                     elif self.cy_old < self.barrier and cy > self.barrier and abs(self.cy_old -cy) > self.minSpeed and self.maxSpeed > abs(self.cy_old -cy):
                        self.countIn += 1
                        self.occupancy += 1
                        print("Average: " + str(curr_avg[0]))
                        print("Distance: " + str(self.cy_old -cy))
                        print("Occupancy: " + str(self.occupancy))
                        print("Out: " + str(self.countOut))
                     #historize the centroid
                     self.cx_old=cx
                     self.cy_old=cy

                #historize the average
                self.avg_old = curr_avg

                #end of core algorithm
                b = int(round(time.time() * 1000))

                c=b-a

                #display image if setting enabled
                if(self.display==True):
                    #Draw counting line
                    cv2.line(currImg,(0,self.barrier),(self.resX,self.barrier),(0,255,0),3)
                    #Display passed objects in either direction
                    cv2.putText(currImg,"In"+str(self.countIn),(20,180), font, 1,(0,255,0),1,cv2.LINE_AA)
                    cv2.putText(currImg,"Out"+str(self.countOut),(160,180), font, 1,(0,255,0),1,cv2.LINE_AA)
                    #Finally, display the current frame with the tracked objects and counters
                    cv2.imshow('frame', currImg)
                cv2.waitKey(50)
                    


    def join(self):
        self.Running = False
                #Cleanup
        cap.release()
        if(self.display==True):
            cv2.destroyAllWindows()

    def getOccupancy(self):
        return self.occupancy
    def getIn(self):
        return self.countIn
    def getOut(self):
        return self.countOut

    def reset(self):
        self.occupancy = 0
        self.countIn = 0
        self.countOut = 0

    def stop(self):
        self.Running = False
