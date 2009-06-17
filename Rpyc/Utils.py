"""
convenience utilities:
 * provides dir(), getattr(), hasattr(), help() and reload() that support netproxies
 * provides obtain() for really transfering remote objects
 * provides upload() and download() for working with files
 * provides a nice interface for remote shell operations (like os.system)
   and a openning a remote python interpreter (for debugging, etc.)

i removed lots of stuff from the __all__, keeping only the useful things, 
so that import * wouldnt mess your namespace too much
"""
import __builtin__
import sys
import os
import inspect
from NetProxy import NetProxy

__all__ = [
    "dir", "getattr", "hasattr", "help", "reload", "obtain",
    "upload", "download",
]

CHUNK_SIZE = 4096

class UtilityError(Exception): 
    pass

#
# working with netproxies
#
def dir(*obj):
    """a version of dir() that supports NetProxies"""
    if not obj:
        inspect_stack = [inspect.stack()[1][0].f_locals.keys()]
        inspect_stack.sort()
        return inspect_stack
    if not len(obj) == 1:
        raise TypeError("dir expected at most 1 arguments, got %d" % (len(obj),))
    obj = obj[0]
    if isinstance(obj, NetProxy):
        return obj.__dict__["____conn"].modules["__builtin__"].dir(obj)
    else:
        return __builtin__.dir(obj)

def getattr(obj, name, *default):
    """a version of getattr() that supports NetProxies"""
    if len(default) > 1:
        raise TypeError("getattr expected at most 3 arguments, got %d" % (2 + len(default),))
    if isinstance(obj, NetProxy):
        try:
            return obj.__getattr__(name)
        except AttributeError:
            if not default:
                raise
            return default[0]
    else:
        return __builtin__.getattr(obj, name, *default)

def hasattr(obj, name):
    """a version of hasattr() that supports NetProxies"""
    try:
        getattr(obj, name)
    except AttributeError:
        return False
    else:
        return True

class _Helper(object):
    """a version of help() that supports NetProxies"""
    def __repr__(self):
        return repr(__builtin__.help)
    def __call__(self, obj = None):
        if isinstance(obj, NetProxy):
            print "Help on NetProxy object for an instance of %r:" % (obj.__getattr__("__class__").__name__,)
            print
            print "Doc:"
            print obj.__doc__
            print
            print "Members:"
            print dir(obj)
        else:
            __builtin__.help(obj)
help = _Helper()

def reload(module):
    """a version of reload() that supports NetProxies"""
    if isinstance(module, NetProxy):
        return module.__dict__["____conn"].modules["__builtin__"].reload(module)
    else:
        return __builtin__.reload(module)

def obtain(proxy):
    """transfers a remote object to this process. this is done by pickling it, so it
    must be a picklable object, and should be immutable (otherwise the local object
    may be different from the remote one, which may cause problems). generally speaking, 
    you should not obtain remote objects, as NetProxies provide a stronger mechanism.
    but there are times when you want to get the real object in your hand, for pickling
    it locally (e.g., storing test results in a file), or if the connection is too slow."""
    import cPickle
    dumped = proxy.__dict__["____conn"].modules.cPickle.dumps(proxy)
    return cPickle.loads(dumped)

def getconn(obj):
    """returns the connection of a NetProxy"""
    if "____conn" not in obj.__dict__:
        raise TypeError("`obj` is not a NetProxy")
    return proxy.__dict__["____conn"]

#
# working with files
#
def upload(conn, localpath, remotepath, *a, **k):
    """uploads a file or a directory recursively (depending on what `localpath` is)"""
    if os.path.isdir(localpath):
        upload_dir(conn, localpath, remotepath, *a, **k)
    elif os.path.isfile(localpath):
        upload_file(conn, localpath, remotepath, *a, **k)
    else:
        raise UtilityError("can only upload files or directories")

def download(conn, remotepath, localpath, *a, **k):
    """downloads a file or a directory recursively (depending on what `remotepath` is)"""
    if conn.modules.os.path.isdir(remotepath):
        download_dir(conn, remotepath, localpath, *a, **k)
    elif conn.modules.os.path.isfile(remotepath):
        download_file(conn, remotepath, localpath, *a, **k)
    else:
        raise UtilityError("can only download files or directories")

def upload_file(conn, localpath, remotepath):
    lf = open(localpath, "rb")
    rf = conn.modules.__builtin__.open(remotepath, "wb")
    while True:
        chunk = lf.read(CHUNK_SIZE)
        if not chunk:
            break
        rf.write(chunk)
    lf.close()
    rf.close()

def download_file(conn, remotepath, localpath):
    lf = open(localpath, "wb")
    rf = conn.modules.__builtin__.open(remotepath, "rb")
    while True:
        chunk = rf.read(CHUNK_SIZE)
        if not chunk:
            break
        lf.write(chunk)
    lf.close()
    rf.close()
    
def upload_dir(conn, localpath, remotepath, extensions = [""]):
    if not conn.modules.os.path.exists(remotepath):
        conn.modules.os.makedirs(remotepath)
    for fn in os.listdir(localpath):
        lfn = os.path.join(localpath, fn)
        rfn = conn.modules.os.path.join(remotepath, fn)
        if os.path.isdir(lfn):
            upload_dir(conn, lfn, rfn, extensions)
        elif os.path.isfile(lfn):
            for ext in extensions:
                if fn.endswith(ext):
                    upload_file(conn, lfn, rfn)
                    break

def download_dir(conn, remotepath, localpath, extensions = [""]):
    if not os.path.exists(localpath):
        os.makedirs(localpath)
    for fn in conn.modules.os.listdir(remotepath):
        lfn = os.path.join(localpath, fn)
        rfn = conn.modules.os.path.join(remotepath, fn)
        if conn.modules.os.path.isdir(lfn):
            download_dir(conn, rfn, lfn, extensions)
        elif conn.modules.os.path.isfile(lfn):
            for ext in extensions:
                if fn.endswith(ext):
                    download_file(conn, rfn, lfn)
                    break

#
# distributing modules between hosts
#
def upload_package(conn, module, remotepath = None):
    """uploads the given package to the server, storing it in `remotepath`. if 
    remotepath is None, it defaults to the server's site-packages. if the package
    already exists, it is overwritten.
    usage:
        import xml
        upload_package(conn, xml)"""
    if remotepath is None:
        remotepath = conn.modules["distutils.sysconfig"].get_python_lib()
    localpath = os.path.dirname(module.__file__)
    upload_dir(conn, localpath, remotepath, [".py", ".pyd", ".dll", ".so", ".zip"])

def update_module(conn, module):
    """updates an existing module on the server. the local module is transfered to the
    server, overwriting the old one, and is reloaded. 
    usage:
        import xml.dom.minidom
        upload_module(conn, xml.dom.minidom)"""
    remote_module = conn.modules[module.__name__]
    local_file = inspect.getsourcefile(module)
    remote_file = inspect.getsourcefile(remote_module)
    upload_file(conn, local_filem, remote_file)
    reload(remote_module)

#
# remote shell and interpreter
#
def _redirect_std(conn):
    rsys = conn.modules.sys
    orig = (rsys.stdin, rsys.stdout, rsys.stderr)
    rsys.stdin = sys.stdin
    rsys.stdout = sys.stdout
    rsys.stderr = sys.stderr
    return orig

def _restore_std(conn, (stdin, stdout, stderr)):
    rsys = conn.modules.sys
    rsys.stdin = stdin
    rsys.stdout = stdout
    rsys.stderr = stderr
    
def remote_shell(conn, command = None):
    """runs the given command on the server, just like os.system, but takes care
    of redirecting the server's stdout/stdin to the client"""
    # BUG: on windows, there's a problem with redirecting the output of spawned command.
    # it runs fine and all, just the client can't see the output. again, windows sucks.
    if command is None:
        if sys.platform == "win32":
            command = "%COMSPEC%"
        else:
            command = "/bin/sh"
    try:
        orig = _redirect_std(conn)
        return conn.modules.os.system(command)
    finally:
        _restore_std(conn, orig)
    
def remote_interpreter(conn, namespace = None):
    """starts an interactive interpreter on the server"""
    if namespace is None:
        #namespace = inspect.stack()[1][0].f_globals.copy()
        #namespace.update(inspect.stack()[1][0].f_locals)
        namespace = {"conn" : conn}
    try:
        orig = _redirect_std(conn)
        return conn.modules["Rpyc.Utils"]._remote_interpreter_server_side(**namespace)
    finally:
        _restore_std(conn, orig)

def _remote_interpreter_server_side(**namespace):
    import code
    namespace.update(globals())
    code.interact(local = namespace)

def remote_post_mortem(conn):
    """a version of pdb.pm() that operates on exceptions at the remote side of the connection"""
    import pdb
    pdb.post_mortem(c.modules.sys.last_traceback)





