import time
from Rpyc.Factories import Async

def threadfunc(callback):
    """this function will call the callback every second"""
    callback = Async(callback)
    try:
        while True:
            callback()
            time.sleep(1)
    except:
        print "thread exiting"

def printer(text):
    print text

def caller(func, *args):
    func(*args)
    