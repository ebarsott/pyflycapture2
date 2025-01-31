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
    if isinstance(identifier, str):
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
    if isinstance(pixel_format, str):
        pixel_format = consts.pixel_formats[pixel_format]
    if im.format == pixel_format:
        return im
    imo = structs.FCImage.get()
    errors.check_return(raw.fc2ConvertImageTo, pixel_format, im, imo)
    return imo


def resolve_property_name(name):
    if name not in consts.property_types:
        name = 'FC2_%s' % name.upper()
    if isinstance(name, str):
        name = consts.property_types[name]
    return name


def resolve_video_mode(self, mode):
    if mode not in consts.video_modes:
        mode = 'FC2_VIDEOMODE_%s' % mode
    if isinstance(mode, str):
        mode = consts.video_modes[mode]
    return mode


def resolve_frame_rate(self, frame_rate):
    if frame_rate not in consts.frame_rates:
        frame_rate = 'FC2_FRAMERATE_%s' % frame_rate
    if isinstance(frame_rate, str):
        frame_rate = consts.frame_rates[frame_rate]
    return frame_rate


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
        structs.FCImage.destroy(imo)
        raw.fc2DestroyImage(imo)
    return a, meta


class PointGrey(object):
    n_instances = 0

    def __init__(self, identifier=0, context=None):
        if context is None:
            if PointGrey.n_instances == 0:
                self._c = ctx.get()
            else:
                self._c = ctx.new()
            PointGrey.n_instances += 1
        else:
            self._c = context
        self._g = get_camera_handle(identifier, context=self._c)
        self.connected = False
        self.capturing = False

    def get_config(self, as_dictionary=True):
        self.connect()
        c = raw.fc2Config()
        errors.check_return(raw.fc2GetConfiguration, self._c, c)
        if not as_dictionary:
            return c
        return as_dict(c)

    def set_config(self, **kwargs):
        pass

    def get_camera_info(self, as_dictionary=True):
        self.connect()
        ci = raw.fc2CameraInfo()
        errors.check_return(raw.fc2GetCameraInfo, self._c, ci)
        if not as_dictionary:
            return ci
        return as_dict(ci)

    def get_property(self, name, as_dictionary=True):
        self.connect()
        name = resolve_property_name(name)
        p = raw.fc2Property()
        p.type = name
        errors.check_return(raw.fc2GetProperty, self._c, p)
        if not as_dictionary:
            return p
        return as_dict(p)

    def set_property(self, name, **kwargs):
        if len(kwargs) == 0:
            return
        self.connect()
        name = resolve_property_name(name)
        p = self.get_property(name, as_dictionary=False)
        for k in kwargs:
            setattr(p, k, kwargs[k])
        errors.check_return(raw.fc2SetProperty, self._c, p)

    def get_property_info(self, name, as_dictionary=True):
        self.connect()
        name = resolve_property_name(name)
        i = raw.fc2PropertyInfo()
        i.type = name
        errors.check_return(raw.fc2GetPropertyInfo, self._c, i)
        if not as_dictionary:
            return i
        return as_dict(i)

    def get_video_mode(self):
        self.connect()
        mode = ctypes.c_uint(0)
        frame_rate = ctypes.c_uint(0)
        errors.check_return(
            raw.fc2GetVideoModeAndFrameRate, self._c,
            mode, frame_rate)
        return (
            consts.video_modes[mode.value],
            consts.frame_rates[frame_rate.value])

    def set_video_mode(self, mode, frame_rate):
        self.connect()
        mode = resolve_video_mode(mode)
        frame_rate = resolve_frame_rate(frame_rate)
        if not self.validate_video_mode(mode, frame_rate):
            raise errors.FlyCapture2ConfigError(
                "Invalid video mode: %s, %s" % (mode, frame_rate))
        errors.check_return(
            raw.fc2GetVideoModeAndFrameRateInfo, self._c,
            mode, frame_rate)

    def validate_video_mode(self, mode, frame_rate):
        self.connect()
        mode = resolve_video_mode(mode)
        frame_rate = resolve_frame_rate(frame_rate)
        supported = ctypes.c_int(0)
        errors.check_return(
            raw.fc2GetVideoModeAndFrameRateInfo, self._c,
            mode, frame_rate, supported)
        return supported.value

    def get_format7_info(self, as_dictionary=True):
        self.connect()
        fi = raw.fc2Format7Info()
        supported = ctypes.c_int(0)
        errors.check_return(raw.fc2GetFormat7Info, self._c, fi, supported)
        if not as_dictionary:
            return fi, supported.value
        return as_dict(fi), supported.value

    def get_format7_settings(self):
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

    def validate_format7_settings(self, settings):
        self.connect()
        if isinstance(settings, structs.Format7Settings):
            settings = settings.unwrap()
        packet_info = raw.fc2Format7PacketInfo()
        valid = ctypes.c_int(0)
        errors.check_return(
            raw.fc2ValidateFormat7Settings, self._c, settings,
            valid, packet_info)
        return bool(valid.value)

    def set_format7_settings(self, settings, percent=100.):
        self.connect()
        if isinstance(settings, structs.Format7Settings):
            settings = settings.unwrap()
        if not self.validate_format7_settings(settings):
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

    def allocate_buffers(self, s=3932160, n=10):
        # I'm not sure what this is for or even if it's necessary
        return
        #im = self.raw_grab(stop=False)
        #im = structs.FCImage.get()
        #errors.check_return(raw.fc2RetrieveBuffer, self._c, im)
        #size = int(im.dataSize)
        #errors.check_return(raw.fc2DestroyImage, im)
        size = int(s)
        #buffers = (ctypes.c_ubyte * (size * n))()
        self._buffers = numpy.empty(size * (n + 1), dtype='uint8')
        buffers = self._buffers.ctypes.data_as(
            ctypes.POINTER(ctypes.c_ubyte))
        #buffers = ctypes.create_string_buffer(0, size * n)
        # config has number of buffers?
        # unsigned char * buffers
        # int size
        # int n_buffers
        errors.check_return(
            raw.fc2SetUserBuffers, self._c, buffers, size, n)

    def start_capture(self):
        if self.capturing:
            return
        self.connect()
        # TODO setup user buffers
        #self.allocate_buffers()
        errors.check_return(raw.fc2StartCapture, self._c)
        self.capturing = True

    def stop_capture(self):
        if not self.capturing:
            return
        errors.check_return(raw.fc2StopCapture, self._c)
        self.capturing = False

    def raw_grab(self, stop=True):
        self.start_capture()
        im = structs.FCImage.get()
        errors.check_return(raw.fc2RetrieveBuffer, self._c, im)
        if stop:
            self.stop_capture()
        return im

    def grab(self, pixel_format=None, stop=True):
        im = self.raw_grab(stop=False)
        if im.receivedDataSize == 0:
            # this is an empty frame, regrab
            # to avoid these, don't start/stop grab so often
            return self.grab(pixel_format=pixel_format, stop=stop)
        a, meta = image_to_array(im, pixel_format)
        structs.FCImage.destroy(im)
        if stop:
            self.stop_capture()
        return a, meta
