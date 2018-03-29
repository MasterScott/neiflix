#!/usr/bin/python
# This is a simple port-forward / proxy, written using only the default python
# library. If you want to make a suggestion or fix something you can contact-me
# at voorloop_at_gmail.com
# Distributed over IDC(I Don't Care) license
import socket
import select
import time
import sys
import re
from threading import Thread
from threading import Lock

# Changing the BUFFER_SIZE and delay, you can improve the speed and bandwidth.
# But when buffer get to high or delay go too down, you can broke things
BUFFER_SIZE = 4096
MAX_LISTEN = 10
CONNECT_PATTERN="CONNECT (.*mega(?:\.co)?\.nz):(443) HTTP/(1\.[01])"

class Forward:
    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception, e:
            print e
            return False

class MegaProxyServer(Thread):
    stop=False
    input_list = []
    channel = {}

    def synchronized(func):
    
        func.__lock__ = Lock()
            
        def synced_func(*args, **kws):
            with func.__lock__:
                return func(*args, **kws)

        return synced_func

    def __init__(self, host, port):
        Thread.__init__(self)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(MAX_LISTEN)

    @synchronized
    def stop_server(self):
        print "Stopping server..."
        self.stop=True

    @synchronized
    def isStopServer(self):
        return self.stop

    def run(self):
        self.input_list.append(self.server)

        while not self.isStopServer():
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [], 1.0)
            for self.s in inputready:
                if self.s == self.server:
                    self.on_accept()
                    break

                self.data = self.s.recv(BUFFER_SIZE)
                if len(self.data) == 0:
                    self.on_close()
                    break
                else:
                    self.on_recv()

        print "Bye bye"

    def on_accept(self):
        
        clientsock, clientaddress = self.server.accept()
        
        print clientaddress, "has connected"
        
        self.input_list.append(clientsock)

    def on_close(self):
        print self.s.getpeername(), "has disconnected"
        #remove objects from input_list
        self.input_list.remove(self.s)
        self.input_list.remove(self.channel[self.s])
        out = self.channel[self.s]
        # close the connection with client
        self.channel[out].close()  # equivalent to do self.s.close()
        # close the connection with remote server
        self.channel[self.s].close()
        # delete both objects from channel dict
        del self.channel[out]
        del self.channel[self.s]

    def on_recv(self):
        
        data = self.data

        if data.find("CONNECT") != -1:

            m = re.search(CONNECT_PATTERN, data)

            forward = Forward().start(m.group(1), int(m.group(2)))

            print(m.group(1))
            
            if forward:
                self.input_list.append(forward)
                self.channel[self.s] = forward
                self.channel[forward] = self.s
                self.s.send("HTTP/1.1 200 Connection established\r\nProxy-agent: Neiflix/0.1\r\n\r\n")
            else:
                print "Can't establish connection with remote server.",
                print "Closing connection with client side"
                self.s.close()
        else:
            self.channel[self.s].send(data)
