import sys
from Boxing import Box, dump_exception, load_exception
from ModuleNetProxy import RootImporter
from Lib import raise_exception, AttrFrontend


class Connection(object):
    """
    the rpyc connection layer (protocol and APIs). generally speaking, the only 
    things you'll need to access directly from this object are:
     * modules - represents the remote python interprerer's modules namespace
     * execute - executes the given code on the other side of the connection
     * namespace - the namespace in which the code you `execute` resides

    the rest of the attributes should be of no intresent to you, except maybe for 
    `remote_conn`, which represents the other side of the connection. it is unlikely,
    however, you'll need to use it (it is used interally).
    
    when you are done using a connection, and wish to release the resources it
    uses, you should call close(). you don't have to, but if you don't, the gc
    can't release the memory because of cyclic references.
    """
    
    def __init__(self, channel):
        self._closed = False
        self._local_namespace = {}
        self.channel = channel
        self.box = Box(self)
        self.async_replies = {}
        self.sync_replies = {}
        self.request_seq = 0
        self.module_cache = {}
        # user APIs:
        self.modules = RootImporter(self)
        self.remote_conn = self.sync_request("handle_getconn")
        self.namespace = AttrFrontend(self.remote_conn._local_namespace)
    
    def __repr__(self):
        if self._closed:
            return "<%s - closed>" % (self.__class__.__name__,)
        else:
            return "<%s(%r)>" % (self.__class__.__name__, self.channel)

    # 
    # file api layer
    #
    def close(self):
        if self._closed:
            return
        self._closed = True
        self.box.close()
        self.channel.close()
        # untangle circular references
        del self._local_namespace
        del self.channel
        del self.box
        del self.async_replies
        del self.sync_replies
        del self.request_seq
        del self.module_cache
        del self.modules
        del self.remote_conn
        del self.namespace
    
    def fileno(self):
        return self.channel.fileno()

    #
    # protocol layer
    #
    def _recv(self):
        return self.box.unpack(self.channel.recv())

    def _send(self, *args):
        return self.channel.send(self.box.pack(args))
    
    def send_request(self, handlername, *args):
        try:
            self.channel.lock.acquire()
            # this must be atomic {
            self.request_seq += 1 
            self._send(handlername, self.request_seq, args)
            return self.request_seq
            # }
        finally:
            self.channel.lock.release()

    def send_exception(self, seq, exc_info):
        self._send("exception", seq, dump_exception(*exc_info))

    def send_result(self, seq, obj):
        self._send("result", seq, obj)

    def dispatch_result(self, seq, obj):
        if seq in self.async_replies:
            self.async_replies.pop(seq)("result", obj)
        else:        
            self.sync_replies[seq] = obj
    
    def dispatch_exception(self, seq, obj):
        excobj = load_exception(obj)
        if seq in self.async_replies:
            self.async_replies.pop(seq)("exception", excobj)
        else:
            raise_exception(*excobj)

    def dispatch_request(self, handlername, seq, args):
        try:
            res = getattr(self, handlername)(*args)
        except SystemExit:
            raise
        except:
            self.send_exception(seq, sys.exc_info())
        else:
            self.send_result(seq, res)

    def sync_request(self, *args):
        """performs a synchronous (blocking) request"""
        seq = self.send_request(*args)
        while seq not in self.sync_replies:
            self.serve()
        return self.sync_replies.pop(seq)
    
    def async_request(self, callback, *args):
        """performs an asynchronous (non-blocking) request"""
        seq = self.send_request(*args)
        self.async_replies[seq] = callback
        
    #
    # servers api
    #
    def poll(self):
        """if available, serves a single request, otherwise returns (non-blocking serve)"""
        if self.channel.is_available():
            self.serve()
            return True
        else:
            return False
    
    def serve(self):
        """serves a single request or reply (may block)"""
        self.channel.wait()
        handler, seq, obj = self._recv()
        if handler == "result":
            self.dispatch_result(seq, obj)
        elif handler == "exception":
            self.dispatch_exception(seq, obj)
        else:
            self.dispatch_request(handler, seq, obj)            

    #
    # root requests
    #
    def rimport(self, modulename):
        """imports a module by name (as a string)"""
        if modulename not in self.module_cache:
            module = self.sync_request("handle_import", modulename)
            self.module_cache[modulename] = module
        return self.module_cache[modulename]            

    def execute(self, expr, mode = "exec"):
        """execute the given code at the remote side of the connection"""
        return self.sync_request("handle_execute", expr, mode)

    #
    # handlers layer
    #
    def handle_incref(self, oid):
        self.box.incref(oid)
    
    def handle_decref(self, oid):
        self.box.decref(oid)
            
    def handle_delattr(self, oid, name):
        delattr(self.box[oid], name)

    def handle_getattr(self, oid, name):
        return getattr(self.box[oid], name)

    def handle_setattr(self, oid, name, value):
        setattr(self.box[oid], name, value)

    def handle_delitem(self, oid, index):
        del self.box[oid][index]

    def handle_getitem(self, oid, index):
        return self.box[oid][index]

    def handle_setitem(self, oid, index, value):
        self.box[oid][index] = value

    def handle_call(self, oid, args, kwargs):
        return self.box[oid](*args, **kwargs)

    def handle_repr(self, oid):
        return repr(self.box[oid])

    def handle_str(self, oid):
        return str(self.box[oid])

    def handle_bool(self, oid):
        return bool(self.box[oid])

    def handle_import(self, modulename):
        return __import__(modulename, None, None, modulename.split(".")[-1])

    def handle_getconn(self):
        return self

    def handle_execute(self, expr, mode):
        codeobj = compile(expr, "<from %s>" % (self,), mode)
        return eval(codeobj, self._local_namespace)



