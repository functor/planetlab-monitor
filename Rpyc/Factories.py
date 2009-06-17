"""
the factory: 
exposes a nice and easy interface to the internals of rpyc. 
this module, along with Utils, are the only modules most clients will need.
"""

from Stream import SocketStream, PipeStream
from Channel import Channel
from Connection import Connection
from AsyncNetProxy import AsyncNetProxy
from weakref import WeakValueDictionary
from Lib import DEFAULT_PORT


__all__ = ["SocketConnection", "AuthSocketConnection", "PipeConnection", "Async"]
_async_proxy_cache = WeakValueDictionary()

class LoginError(Exception):
    pass

def SocketConnection(host, port = DEFAULT_PORT, **kw):
    """shorthand for creating a conneciton over a socket to a server"""
    return Connection(Channel(SocketStream.from_new_socket(host, port, **kw)))

def _create_auth_connection(chan, username, password):
    from Authentication import login
    if not login(chan, username, password):
        raise LoginError("the server did not accept the login")
    return Connection(chan)
    
def AuthSocketConnection(host, username, password, port = DEFAULT_PORT, **kw):
    """shorthand for creating a conneciton over a socket to a server, with authentication"""
    chan = Channel(SocketStream.from_new_socket(host, port, **kw))
    return _create_auth_connection(chan, username, password)

def PipeConnection(incoming, outgoing):
    """shorthand for creating a conneciton over a pipe"""
    return Connection(Channel(PipeStream(incoming, outgoing)))

def AuthPipeConnection(incoming, outgoing, username, password):
    """shorthand for creating a conneciton over a pipe"""
    chan = Channel(PipeStream(incoming, outgoing))
    return _create_auth_connection(chan, username, password)

def Async(proxy):
    """a factory for creating asynchronous proxies for existing synchronous ones"""
    key = id(proxy)
    if key in _async_proxy_cache:
        return _async_proxy_cache[key]
    else:
        new_proxy = AsyncNetProxy(proxy)
        _async_proxy_cache[key] = new_proxy
        return new_proxy




