import socket 
import threading
import RPi.GPIO as GPIO
from ina219 import INA219
from ina219 import DeviceRangeError
import time
from datetime import datetime
from threadloopstartstop import threadloopstartstop
from zipfile36 import ZipFile

CHANNEL_1 = 1
CHANNEL_2 = 2
CHANNEL_12 = 3
OFF = 0
ON = 1
SHORT_TERM = 0
LONG_TERM = 1


class Datalogger(threading.Thread, socket.socket):
    def __init__(self,setup=SHORT_TERM, channel=CHANNEL_12):
        threading.Thread.__init__(self)
        socket.socket.__init__(self)
        self.finished = threading.Event()
        self.format = '.dat'

        self.channel = channel
        self.setup = setup
        self.mode = OFF

        #config GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(21,GPIO.OUT)
        GPIO.setup(20,GPIO.OUT)
        self.SHUNT_OHMS = 0.1
        
        self.samples = 1000
        
        self.ina1=INA219(self.SHUNT_OHMS,address=0x40)
        self.ina1.configure(self.ina1.RANGE_16V)
    
        self.ina2=INA219(self.SHUNT_OHMS,address=0x41)
        self.ina2.configure(self.ina2.RANGE_16V)
        
        #SOCKETS
        self.TCP_IP = '0.0.0.0'
        self.TCP_PORT = 2004
        self.CHUNK_SIZE = 8 * 1024

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcpServer.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.tcpServer.bind((self.TCP_IP, self.TCP_PORT))
        self.tcpServer.listen(5) 
        (self.conn, (ip, port)) = self.tcpServer.accept()
        
        self.thread_2 = threading.Thread(target=self.sockets)
        self.thread_2.start()
         
        
    def transfer(self):
        if self.channel == CHANNEL_1 or self.channel == CHANNEL_2: 
            with ZipFile('SAMPLES.zip', 'w') as zipf:
                zipf.write('z.voltage_ch'+str(self.channel)+self.format)
                zipf.write('z.current_ch'+str(self.channel)+self.format)
                
        if self.channel == CHANNEL_12:
            with ZipFile('SAMPLES.zip', 'w') as zipf:
                zipf.write('z.voltage_ch1'+self.format)
                zipf.write('z.current_ch1'+self.format)
                zipf.write('z.voltage_ch2'+self.format)
                zipf.write('z.current_ch2'+self.format)

        with open('SAMPLES.zip', 'rb') as f:
            data = f.read(self.CHUNK_SIZE)
            while data:
                self.conn.sendall(data)
                data = f.read(self.CHUNK_SIZE)
        print("File has been sent")


    def sockets (self):
        data =''
        print ("Multithreaded Python server : Waiting for connections from TCP clients...")
        while True :
            data = self.conn.recv(25)
            if data == b'START':
                self.stop()
                self.start()
                
            elif data == b'STOP':
                self.stop()
                
            elif data == b'TRANSFER':
                self.transfer()
                               
            elif data == b'CLOSE ALL':
                self.stop()
                self.conn.close()
                self.tcpServer.close()
                print ('SEE YOU SOON :)')
                exit()
            
            else:
                print ("Try to enter a correct command")
#---------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------
    def deletechars(self,s):
        return s.replace('-',' ').replace(':',' ')
    

    
    def start(self):
        if self.setup == SHORT_TERM:
            self.process = threadloopstartstop(0.1,False,self.short_term)
            self.process.start()
        if self.setup == LONG_TERM:
            self.process = threadloopstartstop(0.1,False,self.long_term)
            self.process.start()
        self.mode = ON
    
         
    def stop(self):
        try:
            self.mode = OFF
            self.process.stop()
            self.process.shutdown()
        except:
            pass
    def sample_conf(self, samples):
        try:
            if self.mode == ON:
                self.stop()
                self.process.stop()
                self.process.shutdown()
            self.samples = samples
            print('New samples: ',self.samples)
           
        except:
            print('Config error')
           
    def setup_conf (self, setup):
        try:
            if self.mode == ON:
                self.stop()
                self.process.stop()
                self.process.shutdown()
            self.setup = setup
            
            if self.setup == LONG_TERM:
                self.process = threadloopstartstop(0.1,False,self.long_term)
                print ('Setup changed to LONG_TERM')
            if self.setup == SHORT_TERM:
                self.process = threadloopstartstop(0.1,False,self.short_term)
                print ('Setup changed to SHORT_TERM')
            
        except:
            print ('Setup configurtion error')
            exit()

    def channel_conf (self, channel):
        try:
            if self.mode == ON:
                self.stop()
                self.process.stop()
                self.process.shutdown()
            self.channel = channel
            
            if self.setup == LONG_TERM:
                self.process = threadloopstartstop(0.1,False,self.long_term)
            if self.setup == SHORT_TERM:
                self.process = threadloopstartstop(0.1,False,self.short_term)
                
            print ('Changed to channel ', self.channel)

            
        except:
            print ('Channel configuration error')
            exit()
            
    def short_term(self):
        if self.mode == ON:
            print ('DATALOGGING...')
            
            if self.channel == CHANNEL_1 or self.channel == CHANNEL_2:
                # header for voltage
                fv=open('z.voltage_ch'+str(self.channel)+self.format,"w")
                fv.write('% Timestamp, Voltage ch'+str(self.channel)+'(V)\n')
                fv.close()
                
                # header for current
                fc=open('z.current_ch'+str(self.channel)+self.format,"w")
                fc.write('% Timestamp, Current ch'+str(self.channel)+'(mA)\n')
                fc.close()
                
            if self.channel == CHANNEL_12:
                
                # header for ch1 voltage
                fid=open('z.voltage_ch1' + self.format,"w")
                fid.write('% Timestamp, Voltage ch1 (V)\n')
                fid.close()

                # header for ch1 current
                fid=open('z.current_ch1' + self.format,"w")
                fid.write('% Timestamp, Current ch1 (mA)\n')
                fid.close()

                # header for ch2 voltage
                fid=open('z.voltage_ch2' + self.format,"w")
                fid.write('% Timestamp, Voltage ch2 (V)\n')
                fid.close()

                # header for ch2 current
                fid=open('z.current_ch2' + self.format,"w")
                fid.write('% Timestamp, Current ch2 (mA)\n')
                fid.close()
            i=0
            while i <= self.samples and self.mode == ON:
                
                if self.channel == CHANNEL_1:
                    #logging voltage to file ch1
                    fv=open('z.voltage_ch'+str(self.channel)+ self.format,'a')
                    GPIO.output(21,GPIO.HIGH)
                    voltage=self.ina1.voltage()
                    tvol=time.time()      #tvol=time.time()
                    GPIO.output(21,GPIO.LOW)
                    fv.write(str(tvol)+"; "+str(voltage)+"\n")
                    fv.close()
                    
                    #logging current to file ch1
                    fc=open('z.current_ch'+str(self.channel)+ self.format,'a')
                    GPIO.output(20,GPIO.HIGH)
                    current=self.ina1.current()
                    tcur=time.time()
                    GPIO.output(20,GPIO.LOW)
                    fc.write(str(tcur)+"; "+str(current)+"\n")
                    fc.close()
                    time.sleep(5e-3)
                    i = i + 1
        
                if self.channel == CHANNEL_2:
                    #logging voltage to file ch2
                    fv=open('z.voltage_ch'+str(self.channel)+ self.format,'a')
                    GPIO.output(21,GPIO.HIGH)
                    voltage=self.ina2.voltage()
                    tvol=time.time()
                    #tvol=time.time()
                    GPIO.output(21,GPIO.LOW)
                    fv.write(str(tvol)+"; "+str(voltage)+"\n")
                    fv.close()
                    
                    #logging current to file ch2 
                    fc=open('z.current_ch'+str(self.channel)+self.format,'a')
                    GPIO.output(20,GPIO.HIGH)
                    current=self.ina2.current()
                    tcur=time.time() 
                    GPIO.output(20,GPIO.LOW)
                    fc.write(str(tcur)+"; "+str(current)+"\n")
                    fc.close()
                    time.sleep(5e-3)
                    i = i + 1
                    
                if self.channel == CHANNEL_12:
                    # logging to variables ch1
                    voltage1=self.ina1.voltage()
                    tvol1=time.time()
                    current1=self.ina1.current()
                    tcur1=time.time()

                    # logging to variables ch2
                    voltage2=self.ina2.voltage()
                    tvol2=time.time()
                    current2=self.ina2.current()
                    tcur2=time.time()
                    time.sleep(5e-3)
                    
                    # logging voltage to files ch1 
                    fid=open('z.voltage_ch1' + self.format,"a")
                    fid.write(self.deletechars(str(tvol1))+" ;  "+str(voltage1)+"\n")
                    fid.close()

                    # logging curent to files ch1 
                    fid=open('z.current_ch1' + self.format,"a")
                    fid.write(self.deletechars(str(tcur1))+" ;  "+str(current1)+"\n")
                    fid.close()

                    # logging voltage to files ch2 
                    fid=open('z.voltage_ch2' + self.format,"a")
                    fid.write(self.deletechars(str(tvol2))+" ;  "+str(voltage2)+"\n")
                    fid.close()

                    # logging current to files ch2 
                    fid=open('z.current_ch2' + self.format,"a")
                    fid.write(self.deletechars(str(tcur2))+" ;  "+str(current2)+"\n")
                    fid.close()
                    i = i + 1
            
            self.mode=OFF
            print ('LOGGED' ,i-1, 'samples')

             
    def long_term(self):
        if self.mode == ON:
            print ('DATALOGGING...')
            if self.channel == CHANNEL_1 or self.channel == CHANNEL_2:
                # header for voltage
                fv=open('z.voltage_ch'+str(self.channel)+ self.format,"w")
                fv.write('% Timestamp, Voltage ch'+str(self.channel)+'(V)\n')
                fv.close()
                
                # header for current
                fc=open('z.current_ch'+str(self.channel)+ self.format,"w")
                fc.write('% Timestamp, Current ch'+str(self.channel)+'(mA)\n')
                fc.close()
                
            if self.channel == CHANNEL_12:
                
                # header for ch1 voltage
                fid=open('z.voltage_ch1' + self.format,"w")
                fid.write('% Timestamp, Voltage ch1 (V)\n')
                fid.close()

                # header for ch1 current
                fid=open('z.current_ch1' + self.format,"w")
                fid.write('% Timestamp, Current ch1 (mA)\n')
                fid.close()

                # header for ch2 voltage
                fid=open('z.voltage_ch2' + self.format,"w")
                fid.write('% Timestamp, Voltage ch2 (V)\n')
                fid.close()

                # header for ch2 current
                fid=open('z.current_ch2' + self.format,"w")
                fid.write('% Timestamp, Current ch2 (mA)\n')
                fid.close()
            i=0
            while True and self.mode == ON:
                
                if self.channel == CHANNEL_1:
                    #logging voltage to file ch1
                    fv=open('z.voltage_ch'+str(self.channel)+ self.format,'a')
                    GPIO.output(21,GPIO.HIGH)
                    voltage=self.ina1.voltage()
                    tvol=time.time()      #tvol=time.time()
                    GPIO.output(21,GPIO.LOW)
                    fv.write(str(tvol)+"; "+str(voltage)+"\n")
                    fv.close()
                    
                    #logging current to file ch1
                    fc=open('z.current_ch'+str(self.channel)+ self.format,'a')
                    GPIO.output(20,GPIO.HIGH)
                    current=self.ina1.current()
                    tcur=time.time()
                    GPIO.output(20,GPIO.LOW)
                    fc.write(str(tcur)+"; "+str(current)+"\n")
                    fc.close()
                    time.sleep(5e-3)
                    i = i + 1
        
                if self.channel == CHANNEL_2:
                    #logging voltage to file ch2
                    fv=open('z.voltage_ch'+str(self.channel) + self.format,'a')
                    GPIO.output(21,GPIO.HIGH)
                    voltage=self.ina2.voltage()
                    tvol=time.time()
                    #tvol=time.time()
                    GPIO.output(21,GPIO.LOW)
                    fv.write(str(tvol)+"; "+str(voltage)+"\n")
                    fv.close()
                    
                    #logging current to file ch2 
                    fc=open('z.current_ch'+str(self.channel)+ self.format,'a')
                    GPIO.output(20,GPIO.HIGH)
                    current=self.ina2.current()
                    tcur=time.time()
                    GPIO.output(20,GPIO.LOW)
                    fc.write(str(tcur)+"; "+str(current)+"\n")
                    fc.close()
                    time.sleep(5e-3)
                    i = i + 1
                    
                if self.channel == CHANNEL_12:
                    # logging to variables ch1
                    voltage1=self.ina1.voltage()
                    tvol1=time.time()
                    current1=self.ina1.current()
                    tcur1=time.time()

                    # logging to variables ch2
                    voltage2=self.ina2.voltage()
                    tvol2=time.time()
                    current2=self.ina2.current()
                    tcur2=time.time()
                    time.sleep(5e-3)
                    
                    # logging voltage to files ch1 
                    fid=open('z.voltage_ch1' + self.format,"a")
                    fid.write(self.deletechars(str(tvol1))+" ;  "+str(voltage1)+"\n")
                    fid.close()

                    # logging curent to files ch1 
                    fid=open('z.current_ch1' + self.format,"a")
                    fid.write(self.deletechars(str(tcur1))+" ;  "+str(current1)+"\n")
                    fid.close()

                    # logging voltage to files ch2 
                    fid=open('z.voltage_ch2' + self.format,"a")
                    fid.write(self.deletechars(str(tvol2))+" ;  "+str(voltage2)+"\n")
                    fid.close()

                    # logging current to files ch2 
                    fid=open('z.current_ch2' + self.format,"a")
                    fid.write(self.deletechars(str(tcur2))+" ;  "+str(current2)+"\n")
                    fid.close()
                    i = i + 1
            
            self.mode=OFF
            print ('LOGGED' ,i-1, 'samples')
            
    
if __name__ == "__main__":
    try:
        t=Datalogger(LONG_TERM, CHANNEL_12)        
        
    except KeyboardInterrupt:
        exit() 