#!/usr/bin/env python

import atexit

from . import errors
from . import raw


class Context(object):
    instances = []

    @classmethod
    def get(cls, index=0):
        if index >= len(cls.instances):
            return cls.new()
        return cls.instances[index]

    @classmethod
    def new(cls):
        c = raw.fc2Context()
        errors.check_return(raw.fc2CreateContext, c)
        cls.instances.append(c)
        return c

    @classmethod
    def dispose(cls):
        for instance in cls.instances:
            #print "disposing of context %s" % hex(id(instance))
            raw.fc2DestroyContext(instance)
        cls.instances = []


get = Context.get
new = Context.new

atexit.register(Context.dispose)
