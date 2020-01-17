import time
import threading

class threadloopstartstop(threading.Thread):
    def __init__ (self, interval, default, function, args=[], kwargs={}):
        threading.Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.finished = threading.Event()
        self.flagstop = default
        
    def shutdown(self):
        self.finished.set()
        self.join()
        
    def stop(self):
        self.flagstop = True
    def restart(self):
        self.flagstop = False
        print ('reloded')
    def isstopped(self):
        return self.flagstop
        
    def run(self):
        while not self.finished.isSet():
            self.finished.wait(self.interval)
            if not self.flagstop:
                self.function(*self.args, **self.kwargs)

if __name__ == "__main__":

    def my_function (a, b, c):
        print("Here I am:", a, b, c)

    print("Calling my_function() in a thread every 1/10th of second for two seconds.")
    t = threadloopstartstop(0.5, False, my_function, (1,0,-1))
    t.start()
    print('start at:',time.asctime())
    time.sleep(2)
    print('stop at:',time.asctime())
    t.stop()
    print('restart at:',time.asctime())
    t.restart()
    time.sleep(2)
    print('stop at:',time.asctime())
    t.stop()
    print('shutdown at:',time.asctime())
    t.shutdown()
    print("Done!")

