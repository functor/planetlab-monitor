from NetProxy import NetProxyWrapper
from Lib import raise_exception


class InvalidAsyncResultState(Exception):
    pass


class AsyncNetProxy(NetProxyWrapper):
    """wraps an exiting synchronous netproxy to make is asynchronous 
    (remote operations return AsyncResult objects)"""
    __doc__ = NetProxyWrapper.__doc__

    def __request__(self, handler, *args):
        res = AsyncResult(self.__dict__["____conn"])
        self.__dict__["____conn"].async_request(res.callback, handler, self.__dict__["____oid"], *args)
        return res

    # must return a string... and it's not meaningful to return the repr of an async result
    def __repr__(self, *args):
        return self.__request__("handle_repr", *args).result
    def __str__(self, *args):
        return self.__request__("handle_str", *args).result      
        

class AsyncResult(object):
    """represents the result of an asynchronous operation"""
    STATE_PENDING = "pending"
    STATE_READY = "ready"
    STATE_EXCEPTION = "exception"
    STATE_UNKNOWN = "unknown"
    
    def __init__(self, conn):
        self.conn = conn
        self._state = self.STATE_PENDING
        self._result = None
        self._on_ready = None
    
    def __repr__(self):
        return "<AsyncResult (%s) at 0x%08x>" % (self._state, id(self))
    
    def callback(self, event, obj):
        if event == "result":
            self._state = self.STATE_READY
            self._result = obj
        elif event == "exception":
            self._state = self.STATE_EXCEPTION
            self._result = obj
        else:
            self._state = self.STATE_UNKNOWN
            self._result = obj
            
        if self._on_ready is not None:
            self._on_ready(self)
    
    def _get_on_ready(self):
        return self._ready_callback

    def _set_on_ready(self, obj):
        self._on_ready = obj
        if self._state != self.STATE_PENDING:
            self._on_ready(self)
    
    def _get_is_ready(self):
        if self._state == self.STATE_PENDING:
            self.conn.poll()
        return self._state != self.STATE_PENDING
    
    def _get_result(self):
        while self._state == self.STATE_PENDING:
            self.conn.serve()
        if self._state == self.STATE_READY:
            return self._result
        elif self._state == self.STATE_EXCEPTION:
            raise_exception(*self._result)
        else:
            raise InvalidAsyncResultState(self._state)
            
    is_ready = property(_get_is_ready, doc = "indicates whether or not the result is ready")
    result = property(_get_result, doc = "the value of the async result (may block)")
    on_ready = property(_get_on_ready, _set_on_ready, doc =
        "if not None, specifies a callback which is called when the result is ready")
