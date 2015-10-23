#!/usr/bin/env python

from . import raw


def to_dict(e):
    r = {e[k]: k for k in e}
    r.update(e)
    return r

error_codes = to_dict(raw.fc2Error)
# bus callback
grab_modes = to_dict(raw.fc2GrabMode)
# grab timeout
# bandwith allocation
# interface type
# driver type
property_types = to_dict(raw.fc2PropertyType)
frame_rates = to_dict(raw.fc2FrameRate)
video_modes = to_dict(raw.fc2VideoMode)
modes = to_dict(raw.fc2Mode)
pixel_formats = to_dict(raw.fc2PixelFormat)
# bus speed
# pci bus speed
# color processing algorithm
bayer_tile_formats = to_dict(raw.fc2BayerTileFormat)
# image file format
# gige property type
# statistics channel
# os type
# byte order
