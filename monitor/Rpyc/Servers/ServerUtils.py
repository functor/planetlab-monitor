import os
import socket
import sys
import gc
from threading import Thread
from Rpyc.Connection import Connection
from Rpyc.Stream import SocketStream, PipeStream
from Rpyc.Channel import Channel
from Rpyc.Lib import DEFAULT_PORT


class Logger(object):
    def __init__(self, logfile = None, active = True):
        self.logfile = logfile
        self.active = active
    def __call__(self, *args):
        if not self.logfile:
            return
        if not self.active:
            return
        text = " ".join([str(a) for a in args])
        self.logfile.write("[%d] %s\n" % (os.getpid(), text))
        self.logfile.flush()
        
log = Logger(sys.stdout)

def _serve(chan):
    conn = Connection(chan)
    try:
        try:
            while True:
                conn.serve()
        except EOFError:
            pass
    finally:
        conn.close()
        gc.collect()

def serve_stream(stream, authenticate = False, users = None):
    chan = Channel(stream)
    
    if authenticate:
        from Rpyc.Authentication import accept
        log("requiring authentication")
        if accept(chan, users):
            log("authenication successful")
        else:
            log("authentication failed")
            return
    
    _serve(chan)

def create_listener_socket(port):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #sock.bind(("", port))
    sock.bind(("localhost", port))
    sock.listen(4)
    log("listening on", sock.getsockname())
    return sock

def serve_socket(sock, **kw):
    sockname = sock.getpeername()
    log("welcome", sockname)
    try:
        try:
            serve_stream(SocketStream(sock), **kw)
        except socket.error:
            pass
    finally:
        log("goodbye", sockname)

def serve_pipes(incoming, outgoing, **kw):
    serve_stream(PipeStream(incoming, outgoing), **kw)

def threaded_server(port = DEFAULT_PORT, **kwargs):
    sock = create_listener_socket(port)
    while True:
        newsock, name = sock.accept()
        t = Thread(target = serve_socket, args = (newsock,), kwargs = kwargs)
        t.setDaemon(True)
        t.start()

def start_threaded_server(*args, **kwargs):
    """starts the threaded_server on a separate thread. this turns the 
    threaded_server into a mix-in you can place anywhere in your code"""
    t = Thread(target = threaded_server, args = args, kwargs = kwargs)
    t.setDaemon(True)
    t.start()

