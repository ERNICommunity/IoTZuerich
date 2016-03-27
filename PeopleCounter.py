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
#from picamera.array import PiRGBArray
#from picamera import PiCamera
import time

def main():
    pass

class PeopleCounter(threading.Thread):
    def __init__(self, areaThreshold, barrier, blurRadius, frameRatio,speedLimit,occupancy,inputType = 'STREAM',input = '', display=False):
        threading.Thread.__init__(self)
        self.Running = False
        self.areaThreshold = areaThreshold
        self.barrier = barrier
        self.frameRatio = frameRatio
        self.speedLimit = speedLimit
        self.occupancy = occupancy
        self.inputType = inputType
        self.input = input
        self.blurRadius = blurRadius
        self.display = display
        #usually 0
        self.cameraPort = 0

        print(cv2.__version__)

        #Create the bakcgroundSubtractor. This is the initial step when processing the video
        self.fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows=False)

    def run(self):
        #Video goes here. New videos / camera setup need new parametrization:
        print(cv2.useOptimized())
        if self.inputType == 'FILE':
            cap = cv2.VideoCapture(self.input)
        else:
            cap = cv2.VideoCapture(0)
            cap.set(3,480)
            cap.set(4,360)
            cap.set(5,5)
            #camera = PiCamera()
            #camera.resolution = (480, 360)
            #camera.framerate = 5
            #rawCapture = PiRGBArray(camera, size=(480, 360))

            ## allow the camera to warmup
            #time.sleep(0.1)
        #Counter for all passed objects
        runningID = 0
        #Array of objects currently tracked
        trackedObjects = []
        #Objects not detected anymore in current frame
        toDelete = []
        #Labeling font
        font = cv2.FONT_HERSHEY_SIMPLEX
        #framecounter to skip n frames and improve performance
        framecount = 0
        #Counters for passed obejcts
        countIn = 2
        countOut = 0
        self.Running = True
        #do until user interruption
        while(self.Running == True):

            framecount=framecount + 1
            ret, frame = cap.read()
            #grab next frame and increase framecounter
            #change the modulo to skip frames. currently consider each frame
            if (framecount % self.frameRatio) == 0:
            #for capture in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
                #frame = capture.array
                #coose region of interest and apply foreground subtractor to it


                fgmask = self.fgbg.apply(frame)

                #Smooth the detected foreground

                blurred = cv2.medianBlur(fgmask,self.blurRadius)

                #Find countours around detected objects
                cv2.imshow('frame1', blurred)


                image, contours, hierarchy = cv2.findContours(blurred,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

                #print('\n')
                #Loop through all detected objects in current frame
                a = int(round(time.time() * 1000))
                for cnt in contours:
                    #Get the moments (information about object density or so)
                    M = cv2.moments(cnt)
                    #Make sure we can divide by zero-moment and the object has a certain size.
                    #Size threshold to be found empirically
                    if (M['m00'] > 0 and cv2.contourArea(cnt) > self.areaThreshold):
                        #Calculate centroid
                        cx = int(M['m10']/M['m00'])
                        cy = int(M['m01']/M['m00'])
                        #Store area
                        area = cv2.contourArea(cnt)
                        print('Area: ')
                        print(area)
                        #Redundant area check...first could be removed I guess
                        #Object of interest. We assume it is not tracked yet
                        tracked = False
                        #Loop through all tracked objects and calculate the distance of the centroid to the current object
                        for i in range(len(trackedObjects)):
                            #distance calculation...pythagoras
                            distance = math.sqrt((cx-trackedObjects[i][1])*(cx-trackedObjects[i][1])+(cy-trackedObjects[i][2])*(cy-trackedObjects[i][2]))
                            #print for debug
                            print('Distance; ')
                            print(distance)
                            #If the distance to a certain tracked object is smaller than a certain threshold, we
                            #assume it is the same object and distance is due to movement. More sophisticated criteria could be included here
                            #such as shape info etc.
                            if(distance < self.speedLimit):
                                #check whether the objects has passed an imaginary counting line in either direction since the last frame
                                if(cy < self.barrier and trackedObjects[i][2] > self.barrier):
                                    countIn+=1
                                    self.occupancy += 1
                                elif(cy > self.barrier and trackedObjects[i][2] < self.barrier):
                                    countOut +=1
                                    self.occupancy -=1
                                #Update information of the tracked object, since it is the same
                                trackedObjects[i][1] = cx
                                trackedObjects[i][2] = cy
                                trackedObjects[i][3] = area
                                #This is used to sort out the objects later that disappeared in the current frame
                                trackedObjects[i][4] = True
                                if(self.display==True):
                                #Draw a contour around it
                                    frame = cv2.drawContours(frame, [cnt], 0, (255,0,0), 3)
                                    cv2.putText(frame,str(trackedObjects[i][0]),(cx,cy), font, 2,(255,0,0),2,cv2.LINE_AA)
                                #Mark the object as tracked.
                                tracked = True
                                #Break loop. One object can not be tracked multiple times :)
                                break
                        #If the object is identified as new object
                        if tracked == False:
                            #assign new ID
                            runningID = runningID + 1
                            #Store its ID, centroid, area and track status in the array of tracked objects
                            trackedObjects.append([runningID,cx,cy,area,True])
                            if(self.display==True):
                                #Draw the bounding box
                                frame = cv2.drawContours(frame, [cnt], 0, (255,0,0), 3)
                                #Label it
                                cv2.putText(frame,str(runningID),(int(cx),int(cy)), font, 2,(255,0,0),2,cv2.LINE_AA)
                #Loop through all tracked objects and verify whether they still exist in the current frame
                for i in range(len(trackedObjects)):
                    if(trackedObjects[i][4]) == False:
                        toDelete.append(trackedObjects[i])
                    else:
                        trackedObjects[i][4] = False
                #Delete objects which left the frame
                for i in range(len(toDelete)):
                    trackedObjects.remove(toDelete[i])
                #Empty storage for objects to delete
                toDelete = []
                if(self.display==True):
                    #Draw counting line
                    cv2.line(frame,(0,self.barrier),(480,self.barrier),(0,255,0),3)
                    #Display passed objects in either direction
                    cv2.putText(frame,"In"+str(countIn),(20,180), font, 1,(0,255,0),1,cv2.LINE_AA)
                    cv2.putText(frame,"Out"+str(countOut),(160,180), font, 1,(0,255,0),1,cv2.LINE_AA)
                    #Finally, display the current frame with the tracked objects and counters
                    cv2.imshow('frame', frame)
                    cv2.waitKey(250)
                #rawCapture.truncate(0)
                b = int(round(time.time() * 1000))

                print("Frametime: ")
                c=b-a
                print(c)


    def join(self):
        self.Running = False
                #Cleanup
        cap.release()
        if(self.display==True):
            cv2.destroyAllWindows()

    def getOccupancy(self):
        return self.occupancy

    def stop(self):
        self.Running = False
