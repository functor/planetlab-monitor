"""
shared types, functions and constants
"""
import sys


DEFAULT_PORT = 18812

def raise_exception(typ, val, tbtext):
    """a helper for raising remote exceptions"""
    if type(typ) == str:
        raise typ
    else:
        val._remote_traceback = tbtext
        raise val

class ImmDict(object):
    """immutable dict (passes by value)"""
    def __init__(self, dict):
        self.dict = dict
    def items(self):
        return self.dict.items()

class AttrFrontend(object):
    """a wrapper that implements the attribute protocol for a dict backend"""
    def __init__(self, dict):
        self.__dict__["____dict"] = dict
    def __delattr__(self, name):
        del self.__dict__["____dict"][name]
    def __getattr__(self, name):
        return self.__dict__["____dict"][name]
    def __setattr__(self, name, value):
        self.__dict__["____dict"][name] = value
    def __repr__(self):
        return "<AttrFrontend %s>" % (self.__dict__["____dict"].keys(),)

# installs an rpyc-enabled exception hook. this happens automatically when the module
# is imported. also, make sure the current excepthook is the original one, so we dont 
# install our hook twice (and thus cause infinite recursion) in case the module is reloaded 
def rpyc_excepthook(exctype, value, traceback):
    if hasattr(value, "_remote_traceback"):
        print >> sys.stderr, "======= Remote traceback ======="
        print >> sys.stderr, value._remote_traceback
        print >> sys.stderr, "======= Local exception ======="
        orig_excepthook(exctype, value, traceback)
    else:
        orig_excepthook(exctype, value, traceback)

if sys.excepthook.__name__ != "rpyc_excepthook": 
    orig_excepthook = sys.excepthook
    sys.excepthook = rpyc_excepthook


