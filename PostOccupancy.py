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

import requests, json, math, random, os

def main():
    pass

class PostOccupancy():

    def __init__(self):
        self.writeKey = 'H5Z56N26SFHWB6M8'
        self.readKey = 'GJFZUAHNKGDUUW53'
        self.postUrl = 'https://api.thingspeak.com/update.json'
        self.getUrl = 'https://api.thingspeak.com/channels/61942/feeds.json'

    def postOccupancy(self, occupancy, cin, cout):
        weather = 'Winter'
        temperature = self.getCPUtemperature()
        noise = 40 + random.random()*60
        payload = {'api_key' : self.writeKey, 'field1' : occupancy, 'field2' : cin, 'field3' : cout, 'field4' : temperature}
        r = requests.post(self.postUrl, params=payload)

    def readLastPost(self):
        payload = {'apy_key' : self.readKey, 'results' : 1}
        r = requests.get(self.getUrl, params = payload)
        print(r.status_code)
        channelData = r.json()
        feedsDict = channelData['feeds']
        for record in feedsDict:
            return record['field1']

    def getCPUtemperature(self):
        res = os.popen('vcgencmd measure_temp').readline()
        return(res.replace("temp=","").replace("'C\n",""))
