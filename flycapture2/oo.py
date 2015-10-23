#!/usr/bin/env python
"""
All calls need a context
"""

import ctypes

import numpy

from . import ctx
from . import errors
from . import raw
from . import structs


def as_dict(obj):
    return {a: getattr(obj, a) for a in dir(obj) if a[0] != '_'}


def get_n_cameras(context=None):
    if context is None:
        context = ctx.get()
    n = ctypes.c_int(0)
    errors.check_return(raw.fc2GetNumOfCameras, context, n)
    return n.value


def get_n_devices(context=None):
    if context is None:
        context = ctx.get()
    n = ctypes.c_int(0)
    errors.check_return(raw.fc2GetNumOfDevices, context, n)
    return n.value


def get_serial_number(index, context=None):
    if context is None:
        context = ctx.get()
    sn = ctypes.c_int(0)
    errors.check_return(
        raw.fc2GetCameraSerialNumberFromIndex, context, index, sn)
    return sn.value


def get_camera_handle(identifier, context=None):
    if context is None:
        context = ctx.get()
    g = raw.fc2PGRGuid()
    if isinstance(identifier, (str, unicode)):
        errors.check_return(
            raw.fc2GetCameraFromSerialNumber, context, int(identifier), g)
    else:
        errors.check_return(
            raw.fc2GetCameraFromIndex, context, int(identifier), g)
    return g


# TODO fc2ConvertImageTo to correct bayer? or to grey?
# TODO fc2GetFormat7Info contains: maxHeight maxWidth etc...
# TODO fc2GetCameraInfo contains: sensor info
# TODO fc2GetProperty, fc2GetPropertyInfo
# TODO mode for setting non-format7 stuff:
#  fc2GetVideoModeAndFrameRate use ...Info to check if supported

class PointGrey(object):
    def __init__(self, identifier=0, context=None):
        if context is None:
            self._c = ctx.get()
        self._g = get_camera_handle(identifier, context=self._c)
        self.connected = False
        self.capturing = False

    def get_config(self):
        self.connect()
        settings = raw.fc2Format7ImageSettings()
        packet_size = ctypes.c_uint()
        percent = ctypes.c_float()
        errors.check_return(
            raw.fc2GetFormat7Configuration, self._c, settings,
            packet_size, percent)
        return (
            structs.Format7Settings(settings), packet_size.value,
            percent.value)

    def validate_config(self, settings):
        self.connect()
        if isinstance(settings, structs.Format7Settings):
            settings = settings.unwrap()
        packet_info = raw.fc2Format7PacketInfo()
        valid = ctypes.c_int(0)
        errors.check_return(
            raw.fc2ValidateFormat7Settings, self._c, settings,
            valid, packet_info)
        return bool(valid.value)

    def set_config(self, settings, percent=100.):
        self.connect()
        if isinstance(settings, structs.Format7Settings):
            settings = settings.unwrap()
        if not self.validate_config(settings):
            raise errors.FlyCapture2ConfigError(
                "Invalid settings: %s" % as_dict(settings))
        percent = ctypes.c_float(percent)
        errors.check_return(
            raw.fc2SetFormat7Configuration, self._c, settings, percent)

    def connect(self):
        if self.connected:
            return
        errors.check_return(raw.fc2Connect, self._c, self._g)
        self.connected = True

    def disconnect(self):
        if not self.connected:
            return
        errors.check_return(raw.fc2Disconnect, self._c)
        self.connected = False

    def start_capture(self):
        if self.capturing:
            return
        self.connect()
        errors.check_return(raw.fc2StartCapture, self._c)
        self.capturing = True

    def stop_capture(self):
        if not self.capturing:
            return
        errors.check_return(raw.fc2StopCapture, self._c)
        self.capturing = False

    def raw_grab(self):
        self.start_capture()
        im = raw.fc2Image()
        errors.check_return(raw.fc2CreateImage, im)
        errors.check_return(raw.fc2RetrieveBuffer, self._c, im)
        self.stop_capture()
        return im

    def grab(self):
        im = self.raw_grab()
        meta = as_dict(im)
        del meta['pData']
        a = numpy.ctypeslib.as_array(im.pData, (im.rows, im.cols)).copy()
        errors.check_return(raw.fc2DestroyImage, im)
        self.stop_capture()
        return a, meta
