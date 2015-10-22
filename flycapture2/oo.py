#!/usr/bin/env python
"""
All calls need a context
"""

import atexit
import ctypes

import numpy

from . import raw


error_codes = dict([(raw.fc2Error[k], k) for k in raw.fc2Error])


class FlyCapture2Error(Exception):
    pass


def check_return(f, *args, **kwargs):
    r = f(*args, **kwargs)
    if r != 0:
        raise FlyCapture2Error(
            "%s returned error %s[%s]" % (f.name, r, error_codes[r]))


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
        check_return(raw.fc2CreateContext, c)
        cls.instances.append(c)
        return c

    @classmethod
    def dispose(cls):
        for instance in cls.instances:
            print "disposing of context %s" % hex(id(instance))
            raw.fc2DestroyContext(instance)
        cls.instances = []

atexit.register(Context.dispose)


def get_n_cameras(context=None):
    if context is None:
        context = Context.get()
    n = ctypes.c_int(0)
    check_return(raw.fc2GetNumOfCameras, context, n)
    return n.value


def get_n_devices(context=None):
    if context is None:
        context = Context.get()
    n = ctypes.c_int(0)
    check_return(raw.fc2GetNumOfDevices, context, n)
    return n.value


def get_serial_number(index, context=None):
    if context is None:
        context = Context.get()
    sn = ctypes.c_int(0)
    check_return(raw.fc2GetCameraSerialNumberFromIndex, context, index, sn)
    return sn.value


def get_camera_handle(identifier, context=None):
    if context is None:
        context = Context.get()
    g = raw.fc2PGRGuid()
    if isinstance(identifier, (str, unicode)):
        check_return(
            raw.fc2GetCameraFromSerialNumber, context, int(identifier), g)
    else:
        check_return(
            raw.fc2GetCameraFromIndex, context, int(identifier), g)
    return g


class PointGrey(object):
    def __init__(self, identifier=0, context=None):
        if context is None:
            self._c = Context.get()
        self._g = get_camera_handle(identifier, context=self._c)
        self.connected = False
        self.capturing = False

    def config(self):
        pass

    def connect(self):
        if self.connected:
            return
        check_return(raw.fc2Connect, self._c, self._g)
        self.connected = True

    def disconnect(self):
        if not self.connected:
            return
        check_return(raw.fc2Disconnect, self._c)
        self.connected = False

    def start_capture(self):
        if self.capturing:
            return
        self.connect()
        check_return(raw.fc2StartCapture, self._c)
        self.capturing = True

    def stop_capture(self):
        if not self.capturing:
            return
        check_return(raw.fc2StopCapture, self._c)
        self.capturing = False

    def grab(self):
        self.start_capture()
        im = raw.fc2Image()
        check_return(raw.fc2CreateImage, im)
        check_return(raw.fc2RetrieveBuffer, self._c, im)
        a = numpy.ctypeslib.as_array(im.pData, (im.rows, im.cols)).copy()
        check_return(raw.fc2DestroyImage, im)
        self.stop_capture()  # FIXME?
        return a
