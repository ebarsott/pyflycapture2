#!/usr/bin/env python

from . import consts


class FlyCapture2Error(Exception):
    pass


class FlyCapture2ConfigError(FlyCapture2Error):
    pass


def check_return(f, *args, **kwargs):
    r = f(*args, **kwargs)
    if r != 0:
        raise FlyCapture2Error(
            "%s returned error %s[%s]" % (f.name, r, consts.error_codes[r]))
