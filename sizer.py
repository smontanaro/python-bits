"""
Simple module size estimator

Working from the modules present in sys.modules, the Sizer class makes a
reasonable estimate of the number of global objects reachable from each
loaded module without traversing into other modules (more-or-less).

Usage is simple:

    s = Sizer()
    s.sizeall()
    for item in s.get_deltas():
        print item
"""

import sys, types

class Sizer:
    dispatch = {}
    
    def __init__(self):
        self.oldseen = {}
        self.seen = {}
        self.unknown = {}
        self.seenids = {}
        
    def sizeall(self):
        self.oldseen = self.seen
        self.seen = {}
        self.seenids = {}
        for k in sys.modules.keys():
            self.seen[k] = self.rlen(sys.modules[k])
    
    def get_sizes(self):
        result = []
        for k in self.seen.keys():
            result.append("%s: %d" % (k, self.seen[k]))
        result.sort()
        return result
    
    def get_deltas(self):
        result = []
        for k in self.seen.keys():
            delta = self.seen[k]-self.oldseen.get(k, 0)
            if delta != 0:
                result.append("%s: %d" % (k, delta))
        result.sort()
        return result
    
    def rlen(self, obj):
        try:
            return self.dispatch[type(obj)](self, obj)
        except KeyError:
            self.unknown[type(obj)] = 1
            return 1

    def rlen_module(self, mod):
        return self.rlen(mod.__dict__)
    dispatch[types.ModuleType] = rlen_module
    
    def rlen_dict(self, dict):
        total = 0
        if self.seenids.has_key(id(dict)):
            return self.seenids[id(dict)]
        self.seenids[id(dict)] = 0
        for key,val in dict.items():
            if type(key) != types.ModuleType:
                total = total + self.rlen(key)
            if type(val) != types.ModuleType:
                total = total + self.rlen(val)
        self.seenids[id(dict)] = total
        return total
    dispatch[types.DictType] = rlen_dict
    
    def rlen_seq(self, seq):
        total = 0
        if self.seenids.has_key(id(seq)):
            return self.seenids[id(seq)]
        self.seenids[id(seq)] = 0
        for i in seq:
            if type(i) != types.ModuleType:
                total = total + self.rlen(i)
        self.seenids[id(seq)] = total
        return total
    dispatch[types.ListType] = rlen_seq
    dispatch[types.TupleType] = rlen_seq

    def rlen_class(self, cls):
        return self.rlen(cls.__dict__)
    dispatch[types.ClassType] = rlen_class

    def rlen_instance(self, inst):
        return self.rlen(inst.__dict__)
    dispatch[types.InstanceType] = rlen_instance
        
if __name__ == "__main__":
    s = Sizer()
    s.sizeall()
    print "before Cache import:", s.seen.get('__main__', 0)
    import Cache
    s.sizeall()
    print "after Cache import:", s.seen.get('__main__', 0)
    c = Cache.Cache(size=1000)
    s.sizeall()
    print "after Cache instantiation:", s.seen.get('__main__', 0)
    for i in range(999):
        c[i] = i
    s.sizeall()
    print "after Cache fill:", s.seen.get('__main__', 0)
        
