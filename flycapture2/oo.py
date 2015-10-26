#!/usr/bin/env python

import ctypes

import numpy

from . import consts
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


def convert_format(im, pixel_format=None):
    if pixel_format is None:
        return im
    if pixel_format not in consts.pixel_formats:
        pixel_format = 'FC2_PIXEL_FORMAT_%s' % pixel_format.upper()
    pixel_format = consts.pixel_formats[pixel_format]
    print pixel_format
    if im.format == pixel_format:
        print "skipping convert"
        return im
    imo = structs.FCImage.get()
    errors.check_return(raw.fc2ConvertImageTo, pixel_format, im, imo)
    print "converting: %s %s" % (im.format, imo.format)
    return imo


def image_to_array(im, pixel_format=None):
    imo = convert_format(im, pixel_format)
    meta = as_dict(imo)
    del meta['pData']
    meta['bayerFormat'] = consts.bayer_tile_formats[meta['bayerFormat']]
    meta['format'] = consts.pixel_formats[meta['format']]
    # what about rgb?
    depth = imo.dataSize / (imo.cols * imo.rows)
    if depth == 1:
        a = numpy.ctypeslib.as_array(imo.pData, (imo.rows, imo.cols)).copy()
    else:
        a = numpy.ctypeslib.as_array(
            imo.pData, (imo.rows, imo.cols, depth)).copy()
    if imo is not im:
        raw.fc2DestroyImage(imo)
    return a, meta


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
        im = structs.FCImage.get()
        errors.check_return(raw.fc2RetrieveBuffer, self._c, im)
        self.stop_capture()
        return im

    def grab(self):
        im = self.raw_grab()
        a, meta = image_to_array(im)
        # TODO if this is bayer encoded, decode it
        if im.bayerFormat != 0:
            pass
        errors.check_return(raw.fc2DestroyImage, im)
        self.stop_capture()
        return a, meta
