from threading import RLock
import struct


class Channel(object):
    """a channel transfers packages over a stream. a package is any blob of data,
    up to 4GB in size. channels are gauranteed to be thread-safe"""
    HEADER_FORMAT = ">L" # byte order must be the same at both sides!
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, stream):
        self.lock = RLock()
        self.stream = stream

    def __repr__(self):
        return "<%s(%r)>" % (self.__class__.__name__, self.stream)

    def send(self, data):
        """sends a package"""
        try:
            self.lock.acquire()
            header = struct.pack(self.HEADER_FORMAT, len(data))
            self.stream.write(header + data)
        finally:
            self.lock.release()
        
    def recv(self):
        """receives a package (blocking)"""
        try:
            self.lock.acquire()
            length, = struct.unpack(self.HEADER_FORMAT, self.stream.read(self.HEADER_SIZE))
            return self.stream.read(length)
        finally:
            self.lock.release()
    
    def close(self):
        return self.stream.close()

    def fileno(self):
        return self.stream.fileno()

    def is_available(self):
        return self.stream.is_available()

    def wait(self):
        return self.stream.wait()


