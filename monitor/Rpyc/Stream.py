import select
import socket


class Stream(object):
    """
    a stream is a file-like object that is used to expose a consistent and uniform interface
    to the 'physical' file-like objects (like sockets and pipes), which have many quirks (sockets
    may recv() less than `count`, pipes are simplex and don't flush, etc.).
    a stream is always in blocking mode.
    """
    
    def close(self):
        raise NotImplementedError()

    def fileno(self):
        raise NotImplementedError()

    def is_available(self):
        rlist, wlist, xlist = select.select([self], [], [], 0)
        return bool(rlist)

    def wait(self):
        select.select([self], [], [])

    def read(self, count):
        raise NotImplementedError()

    def write(self, data):
        raise NotImplementedError()
        
        
class SocketStream(Stream):
    """
    a stream that operates over a socket. note: 
        * the socket is expected to be reliable (i.e., TCP)
        * the socket is expected to be in blocking mode
    """
    def __init__(self, sock):
        self.sock = sock
    
    def __repr__(self):
        host, port = self.sock.getpeername()
        return "<%s(%s:%d)>" % (self.__class__.__name__, host, port)

    def from_new_socket(cls, host, port, **kw):
        sock = socket.socket(**kw)
        sock.connect((host, port))
        return cls(sock)
    from_new_socket = classmethod( from_new_socket )

    def fileno(self):
        return self.sock.fileno()
        
    def close(self):
        self.sock.close()
        
    def read(self, count):
        data = []
        while count > 0:
            buf = self.sock.recv(count)
            if not buf:
                raise EOFError()
            count -= len(buf)
            data.append(buf)
        return "".join(data)
            
    def write(self, data):
        while data:
            count = self.sock.send(data)
            data = data[count:]


class PipeStream(Stream):
    """
    a stream that operates over two simplex pipes. 
    note: the pipes are expected to be in blocking mode
    """
    
    def __init__(self, incoming, outgoing):
        self.incoming = incoming
        self.outgoing = outgoing

    def fileno(self):
        return self.incoming.fileno()
        
    def close(self):
        self.incoming.close()
        self.outgoing.close()
        
    def read(self, count):
        data = []
        while count > 0:
            buf = self.incoming.read(count)
            if not buf:
                raise EOFError()
            count -= len(buf)
            data.append(buf)
        return "".join(data)
            
    def write(self, data):
        self.outgoing.write(data)
        self.outgoing.flush()

    # win32: stubs
    import sys
    if sys.platform == "win32":
        def is_available(self):
            return True

        def wait(self):
            pass





