# -*- coding: cp1252 -*-
# Python TCP Client A
import socket 

ON = 0
OFF = 1
class client():
    def __init__(self):
        self.host = '192.168.4.1'
        self.port = 2004
        self.BUFFER_SIZE = 1024 
        self.tcpClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpClient.settimeout(0.1)
        self.tcpClient.connect((self.host, self.port))
        self.MESSAGE=''
        self.CHUNK_SIZE = 8 * 1024
        self.flagtransfer = OFF
        
    def connection(self):
        while self.MESSAGE != 'exit':
            self.MESSAGE = input("tcpClientA: Enter message to continue/ Enter exit:")
            self.tcpClient.send(bytes(self.MESSAGE.upper(),'utf-8'))    

            if self.MESSAGE.upper() == 'TRANSFER':
                self.transferClient()

            elif self.MESSAGE.upper() == 'CLOSE ALL':
                self.tcpClient.close()
                exit()

#---------------------------------------------------------------------
        
    def transferClient(self):
        chunk = self.tcpClient.recv(self.CHUNK_SIZE)
        f = open("ReceivedZip.zip", "wb")
        while chunk:
            f.write(chunk)
            try:
                chunk = self.tcpClient.recv(self.CHUNK_SIZE)
            except socket.timeout as e:
                break
        f.close()
        print("File has been received!")
        

if __name__ == "__main__":
    t=client ()
    t.connection()

