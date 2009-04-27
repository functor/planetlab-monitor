from NetProxy import NetProxyWrapper


class ModuleNetProxy(NetProxyWrapper):
    """a netproxy specialzied for exposing remote modules (first tries to getattr,
    if it fails tries to import)"""
    __doc__ = NetProxyWrapper.__doc__
    
    def __init__(self, proxy, base):
        NetProxyWrapper.__init__(self, proxy)
        self.__dict__["____base"] = base
        self.__dict__["____cache"] = {}

    def __request__(self, handler, *args):
        return self.__dict__["____conn"].sync_request(handler, self.__dict__["____oid"], *args)

    def __getattr__(self, name):
        if name in self.__dict__["____cache"]:
            return self.__dict__["____cache"][name]

        try:
            return self.__request__("handle_getattr", name)
        except AttributeError:
            pass
        
        try:
            fullname = self.__dict__["____base"] + "." + name
            obj = self.__dict__["____conn"].rimport(fullname)
            module = ModuleNetProxy(obj, fullname)
            self.__dict__["____cache"][name] = module
            return module
        except ImportError:
            raise AttributeError("'module' object has not attribute or submodule %r" % (name,))

class RootImporter(object):
    """the root of the interpreter's import hierarchy"""
    
    def __init__(self, conn):
        self.__dict__["____conn"] = conn
    
    def __getitem__(self, name):
        return self.__dict__["____conn"].rimport(name)

    def __getattr__(self, name):
        return ModuleNetProxy(self[name], name)

