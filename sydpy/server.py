#!/usr/bin/env python3

"""
A simple echo server
"""
import select  # @UnresolvedImport
import socket
import pexpect
import sys
import logging
from sydpy.unit import Unit
from sydpy.component import Component, compinit

def set_keepalive_linux(sock, after_idle_sec=1, interval_sec=1, max_fails=3):
    """Set TCP keepalive on an open socket.

    It activates after 1 second (after_idle_sec) of idleness,
    then sends a keepalive ping once every 3 seconds (interval_sec),
    and closes the connection after 5 failed ping (max_fails), or 15 seconds
    """
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, after_idle_sec)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_sec)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, max_fails)

class Server(Component):
    '''Simulator kernel.'''

    @compinit
    def __init__(self, host = '', port=60000, **kwargs):
        self.client = None
        self.sock = None
        backlog = 0
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((self.host,self.port))
        except Exception as e:
            raise Exception("Server port in use.")
        
#         logging.info('Socket port opened.')
        
        try:
            self.sock.listen(backlog)
#             set_keepalive_linux(self.sock)
        except:
            self.sock.close()
    
    def connect(self):
        self.client, address = self.sock.accept()
#         logging.info('Client connected.')
#         client.send(vivhdr.encode())
#         self.client.setblocking(0)
    
    def send(self, msg):
        if not self.client:
            self.connect()
            
#         print("Sending: ", msg)
        self.client.send(msg.encode())

    def recv(self, size=1024):
        if not self.client:
            self.connect()
        
        data = None
        while not data:
            data = self.client.recv(size)
        
#         print("Receiving: ", data)
        
        return data.decode()
            
    def __del__(self):
        try:
            self.sock.close()
        except:
            pass
