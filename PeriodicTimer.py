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

import thread, functools, threading

def main():
    pass

class PeriodicTimer(object):
    def __init__(self, interval, callback):
        self.interval = interval

        @functools.wraps(callback)
        def wrapper(*args, **kwargs):
            result = callback(*args, **kwargs)
            if result:
                self.thread = threading.Timer(self.interval,
                                              self.callback)
                self.thread.start()

        self.callback = wrapper

    def start(self):
        self.thread = threading.Timer(self.interval, self.callback)
        self.thread.start()

    def cancel(self):
        self.thread.cancel()
