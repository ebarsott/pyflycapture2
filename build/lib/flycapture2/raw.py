#!/usr/bin/env python
import ctypes
import itertools


class Enum(dict):
    def __init__(self, name, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.reverse = dict([(self[n], n) for n in self])
        self.name = name

    def name_to_value(self, name):
        return dict.__getitem__(self, name)

    def value_to_name(self, value):
        return self.reverse[value]

    def __getitem__(self, k):
        if isinstance(k, str):
            return self.name_to_value(k)
        elif isinstance(k, int):
            return self.value_to_name(k)
        else:
            raise ValueError(
                "Invalid enum key {}, must be str, unicode or int: {}".format(
                    k, type(k)))


def arg_type_convert(v, atype=None, byref=None):
    """
    This needs to know the un-pointered type when arg by value
    """
    if byref:
        if type(v) == atype:
            return v
        # this should be a simple ctype that will be pointed to
        if type(v).__module__ == 'ctypes':  # this is a valid ctypes object
            return ctypes.byref(v)
        if type(type(v)).__module__ == '_ctypes':  # defined struct, etc
            return ctypes.byref(v)
        # this is a non-ctypes object, so making it into a ctypes object
        # would 'shadow' the arg, causing any change to the generated
        # ctype object to be lost. so throw an exception
        raise Exception(
            "Arguments passed by reference must "
            "be ctypes object: {}, {}".format(v, type(v)))
    if type(v) != atype:
        return atype(v)
    return v


class Function(object):
    def __init__(self, name, restype, *args):
        self.name = name
        self.restype = restype
        self.args = args
        self.func = None
        self.lib = None
        self.converter = None

    def as_ctype(self):
        return ctypes.CFUNCTYPE(self.restype, *[a[1] for a in self.args])

    def generate_spec(self, lib):
        # TODO do I need the namespace here... probably for typedefs
        self.converter = []
        # TODO generate converter for __call__, maybe even a *gasp* doc string
        for n, vt in self.args:
            argtype = type(vt).__name__  # this is a type of a type
            if argtype == 'PyCSimpleType':  # pass by value
                self.converter.append(
                    lambda v, a=vt, b=False:
                    arg_type_convert(v, a, b)
                )
            elif argtype == 'PyCPointerType':  # pass by ref
                self.converter.append(
                    lambda v, a=vt, b=True:
                    arg_type_convert(v, a, b)
                )
            elif argtype == 'PyCStructType':
                self.converter.append(
                    lambda v, a=vt, b=False:
                    arg_type_convert(v, a, b)
                )
            else:
                raise Exception(
                    "Unknown arg type {} for {} {}".format(argtype, n, vt))
        self.assign_lib(lib)
        self.__doc__ = 'args: {}'.format(self.args)

    def assign_lib(self, lib):
        self.lib = lib
        self.func = getattr(self.lib, self.name)
        self.func.restype = self.restype
        self.func.argtypes = [v for _, v in self.args]

    def __call__(self, *args):
        if self.func is None:
            raise Exception(
                "Function has not been bound to a library: see assign_lib")
        if self.converter is None:
            raise Exception(
                "Function spec has not been generated: see generate_spec")
        if len(self.converter) != len(args):
            raise Exception(
                "Invalid number of args {} != {}".format(
                    len(args), len(self.converter)))
        return self.func(*[
            c(a) for (c, a) in zip(self.converter, args)])

    def __dump__(self):
        """
        # set restype and argtypes of lib function
        def function_name(arg1, arg2, arg3, ...):
            # do arg conversion
            lib.function_name(arg1, arg2, arg3)
        """
        raise Exception
        pass

_lib = ctypes.cdll.LoadLibrary('/usr/lib/libflycapture-c.so')


BOOL = ctypes.c_int
fc2Context = ctypes.c_void_p
fc2GuiContext = ctypes.c_void_p
fc2ImageImpl = ctypes.c_void_p
fc2ImageStatisticsContext = ctypes.c_void_p
fc2TopologyNodeContext = ctypes.c_void_p
class fc2PGRGuid(ctypes.Structure):
    _fields_ = [
        ('value', ctypes.c_uint * 4),
    ]


fc2Error = Enum('fc2Error', [
    ('FC2_ERROR_READ_REGISTER_FAILED', 28),
    ('FC2_ERROR_UNDEFINED', -1),
    ('FC2_ERROR_INVALID_PACKET_SIZE', 14),
    ('FC2_ERROR_REGISTER_FAILED', 27),
    ('FC2_ERROR_TRIGGER_FAILED', 24),
    ('FC2_ERROR_INIT_FAILED', 5),
    ('FC2_ERROR_IMAGE_CONVERSION_FAILED', 38),
    ('FC2_ERROR_NOT_IN_FORMAT7', 16),
    ('FC2_ERROR_NOT_SUPPORTED', 17),
    ('FC2_ERROR_INVALID_BUS_MANAGER', 9),
    ('FC2_ERROR_TIMEOUT', 18),
    ('FC2_ERROR_ISOCH_SYNC_FAILED', 36),
    ('FC2_ERROR_FAILED_GUID', 13),
    ('FC2_ERROR_ISOCH_START_FAILED', 33),
    ('FC2_ERROR_PROPERTY_NOT_PRESENT', 26),
    ('FC2_ERROR_INVALID_GENERATION', 20),
    ('FC2_ERROR_IIDC_FAILED', 22),
    ('FC2_ERROR_INVALID_SETTINGS', 8),
    ('FC2_ERROR_STROBE_FAILED', 23),
    ('FC2_ERROR_ISOCH_RETRIEVE_BUFFER_FAILED', 34),
    ('FC2_ERROR_IMAGE_CONSISTENCY_ERROR', 41),
    ('FC2_ERROR_BUS_MASTER_FAILED', 19),
    ('FC2_ERROR_FAILED', 1),
    ('FC2_ERROR_NOT_CONNECTED', 4),
    ('FC2_ERROR_IMAGE_LIBRARY_FAILURE', 39),
    ('FC2_ERROR_WRITE_REGISTER_FAILED', 29),
    ('FC2_ERROR_ISOCH_NOT_STARTED', 32),
    ('FC2_ERROR_ISOCH_STOP_FAILED', 35),
    ('FC2_ERROR_FORCE_32BITS', 2147483647),
    ('FC2_ERROR_NOT_INTITIALIZED', 6),
    ('FC2_ERROR_NOT_FOUND', 12),
    ('FC2_ERROR_FAILED_BUS_MASTER_CONNECTION', 3),
    ('FC2_ERROR_LOW_LEVEL_FAILURE', 11),
    ('FC2_ERROR_ISOCH_ALREADY_STARTED', 31),
    ('FC2_ERROR_INVALID_MODE', 15),
    ('FC2_ERROR_INVALID_PARAMETER', 7),
    ('FC2_ERROR_LUT_FAILED', 21),
    ('FC2_ERROR_BUFFER_TOO_SMALL', 40),
    ('FC2_ERROR_PROPERTY_FAILED', 25),
    ('FC2_ERROR_ISOCH_FAILED', 30),
    ('FC2_ERROR_INCOMPATIBLE_DRIVER', 42),
    ('FC2_ERROR_ISOCH_BANDWIDTH_EXCEEDED', 37),
    ('FC2_ERROR_NOT_IMPLEMENTED', 2),
    ('FC2_ERROR_OK', 0),
    ('FC2_ERROR_MEMORY_ALLOCATION_FAILED', 10),
])


fc2BusCallbackType = Enum('fc2BusCallbackType', [
    ('FC2_ARRIVAL', 1),
    ('FC2_CALLBACK_TYPE_FORCE_32BITS', 2147483647),
    ('FC2_REMOVAL', 2),
    ('FC2_BUS_RESET', 0),
])


fc2GrabMode = Enum('fc2GrabMode', [
    ('FC2_BUFFER_FRAMES', 1),
    ('FC2_UNSPECIFIED_GRAB_MODE', 2),
    ('FC2_GRAB_MODE_FORCE_32BITS', 2147483647),
    ('FC2_DROP_FRAMES', 0),
])


fc2GrabTimeout = Enum('fc2GrabTimeout', [
    ('FC2_TIMEOUT_UNSPECIFIED', -2),
    ('FC2_TIMEOUT_INFINITE', -1),
    ('FC2_TIMEOUT_NONE', 0),
    ('FC2_GRAB_TIMEOUT_FORCE_32BITS', 2147483647),
])


fc2BandwidthAllocation = Enum('fc2BandwidthAllocation', [
    ('FC2_BANDWIDTH_ALLOCATION_UNSUPPORTED', 2),
    ('FC2_BANDWIDTH_ALLOCATION_UNSPECIFIED', 3),
    ('FC2_BANDWIDTH_ALLOCATION_FORCE_32BITS', 2147483647),
    ('FC2_BANDWIDTH_ALLOCATION_OFF', 0),
    ('FC2_BANDWIDTH_ALLOCATION_ON', 1),
])


fc2InterfaceType = Enum('fc2InterfaceType', [
    ('FC2_INTERFACE_TYPE_FORCE_32BITS', 2147483647),
    ('FC2_INTERFACE_GIGE', 3),
    ('FC2_INTERFACE_USB_2', 1),
    ('FC2_INTERFACE_USB_3', 2),
    ('FC2_INTERFACE_UNKNOWN', 4),
    ('FC2_INTERFACE_IEEE1394', 0),
])


fc2PropertyType = Enum('fc2PropertyType', [
    ('FC2_HUE', 4),
    ('FC2_SHARPNESS', 2),
    ('FC2_ZOOM', 9),
    ('FC2_TRIGGER_MODE', 14),
    ('FC2_TRIGGER_DELAY', 15),
    ('FC2_IRIS', 7),
    ('FC2_WHITE_BALANCE', 3),
    ('FC2_PROPERTY_TYPE_FORCE_32BITS', 2147483647),
    ('FC2_SATURATION', 5),
    ('FC2_GAMMA', 6),
    ('FC2_UNSPECIFIED_PROPERTY_TYPE', 18),
    ('FC2_SHUTTER', 12),
    ('FC2_TEMPERATURE', 17),
    ('FC2_AUTO_EXPOSURE', 1),
    ('FC2_FRAME_RATE', 16),
    ('FC2_PAN', 10),
    ('FC2_BRIGHTNESS', 0),
    ('FC2_TILT', 11),
    ('FC2_FOCUS', 8),
    ('FC2_GAIN', 13),
])


fc2FrameRate = Enum('fc2FrameRate', [
    ('FC2_FRAMERATE_7_5', 2),
    ('FC2_FRAMERATE_60', 5),
    ('FC2_FRAMERATE_15', 3),
    ('FC2_FRAMERATE_1_875', 0),
    ('FC2_NUM_FRAMERATES', 9),
    ('FC2_FRAMERATE_240', 7),
    ('FC2_FRAMERATE_30', 4),
    ('FC2_FRAMERATE_120', 6),
    ('FC2_FRAMERATE_3_75', 1),
    ('FC2_FRAMERATE_FORCE_32BITS', 2147483647),
    ('FC2_FRAMERATE_FORMAT7', 8),
])


fc2VideoMode = Enum('fc2VideoMode', [
    ('FC2_VIDEOMODE_1280x960YUV422', 15),
    ('FC2_VIDEOMODE_800x600RGB', 8),
    ('FC2_NUM_VIDEOMODES', 24),
    ('FC2_VIDEOMODE_320x240YUV422', 1),
    ('FC2_VIDEOMODE_800x600YUV422', 7),
    ('FC2_VIDEOMODE_FORCE_32BITS', 2147483647),
    ('FC2_VIDEOMODE_FORMAT7', 23),
    ('FC2_VIDEOMODE_1600x1200Y8', 21),
    ('FC2_VIDEOMODE_1600x1200RGB', 20),
    ('FC2_VIDEOMODE_1280x960RGB', 16),
    ('FC2_VIDEOMODE_1600x1200YUV422', 19),
    ('FC2_VIDEOMODE_800x600Y16', 10),
    ('FC2_VIDEOMODE_640x480Y16', 6),
    ('FC2_VIDEOMODE_640x480YUV411', 2),
    ('FC2_VIDEOMODE_1024x768RGB', 12),
    ('FC2_VIDEOMODE_1280x960Y8', 17),
    ('FC2_VIDEOMODE_1024x768Y8', 13),
    ('FC2_VIDEOMODE_800x600Y8', 9),
    ('FC2_VIDEOMODE_1024x768YUV422', 11),
    ('FC2_VIDEOMODE_160x120YUV444', 0),
    ('FC2_VIDEOMODE_640x480RGB', 4),
    ('FC2_VIDEOMODE_1280x960Y16', 18),
    ('FC2_VIDEOMODE_640x480Y8', 5),
    ('FC2_VIDEOMODE_640x480YUV422', 3),
    ('FC2_VIDEOMODE_1024x768Y16', 14),
    ('FC2_VIDEOMODE_1600x1200Y16', 22),
])


fc2Mode = Enum('fc2Mode', [
    ('FC2_MODE_25', 25),
    ('FC2_MODE_24', 24),
    ('FC2_MODE_27', 27),
    ('FC2_MODE_26', 26),
    ('FC2_MODE_21', 21),
    ('FC2_MODE_20', 20),
    ('FC2_MODE_23', 23),
    ('FC2_MODE_22', 22),
    ('FC2_MODE_29', 29),
    ('FC2_MODE_28', 28),
    ('FC2_NUM_MODES', 32),
    ('FC2_MODE_30', 30),
    ('FC2_MODE_31', 31),
    ('FC2_MODE_10', 10),
    ('FC2_MODE_11', 11),
    ('FC2_MODE_12', 12),
    ('FC2_MODE_13', 13),
    ('FC2_MODE_14', 14),
    ('FC2_MODE_15', 15),
    ('FC2_MODE_16', 16),
    ('FC2_MODE_17', 17),
    ('FC2_MODE_18', 18),
    ('FC2_MODE_19', 19),
    ('FC2_MODE_FORCE_32BITS', 2147483647),
    ('FC2_MODE_2', 2),
    ('FC2_MODE_3', 3),
    ('FC2_MODE_0', 0),
    ('FC2_MODE_1', 1),
    ('FC2_MODE_6', 6),
    ('FC2_MODE_7', 7),
    ('FC2_MODE_4', 4),
    ('FC2_MODE_5', 5),
    ('FC2_MODE_8', 8),
    ('FC2_MODE_9', 9),
])


fc2PixelFormat = Enum('fc2PixelFormat', [
    ('FC2_PIXEL_FORMAT_S_RGB16', 8388608),
    ('FC2_PIXEL_FORMAT_422YUV8_JPEG', 1073741825),
    ('FC2_PIXEL_FORMAT_RGBU', 1073741826),
    ('FC2_PIXEL_FORMAT_BGR16', 33554433),
    ('FC2_PIXEL_FORMAT_444YUV8', 268435456),
    ('FC2_PIXEL_FORMAT_411YUV8', 1073741824),
    ('FC2_PIXEL_FORMAT_BGRU16', 33554434),
    ('FC2_PIXEL_FORMAT_MONO12', 1048576),
    ('FC2_PIXEL_FORMAT_MONO16', 67108864),
    ('FC2_PIXEL_FORMAT_422YUV8', 536870912),
    ('FC2_PIXEL_FORMAT_BGRU', 1073741832),
    ('FC2_PIXEL_FORMAT_RAW8', 4194304),
    ('FC2_PIXEL_FORMAT_RGB16', 33554432),
    ('FC2_PIXEL_FORMAT_RAW12', 524288),
    ('FC2_PIXEL_FORMAT_RAW16', 2097152),
    ('FC2_NUM_PIXEL_FORMATS', 20),
    ('FC2_UNSPECIFIED_PIXEL_FORMAT', 0),
    ('FC2_PIXEL_FORMAT_S_MONO16', 16777216),
    ('FC2_PIXEL_FORMAT_MONO8', 2147483648),
    ('FC2_PIXEL_FORMAT_BGR', 2147483656),
    ('FC2_PIXEL_FORMAT_RGB8', 134217728),
    ('FC2_PIXEL_FORMAT_RGB', 134217728),
])


fc2BusSpeed = Enum('fc2BusSpeed', [
    ('FC2_BUSSPEED_FORCE_32BITS', 2147483647),
    ('FC2_BUSSPEED_10000BASE_T', 11),
    ('FC2_BUSSPEED_S480', 3),
    ('FC2_BUSSPEED_S5000', 7),
    ('FC2_BUSSPEED_S800', 4),
    ('FC2_BUSSPEED_S1600', 5),
    ('FC2_BUSSPEED_100BASE_T', 9),
    ('FC2_BUSSPEED_S3200', 6),
    ('FC2_BUSSPEED_S200', 1),
    ('FC2_BUSSPEED_SPEED_UNKNOWN', -1),
    ('FC2_BUSSPEED_10BASE_T', 8),
    ('FC2_BUSSPEED_ANY', 13),
    ('FC2_BUSSPEED_S100', 0),
    ('FC2_BUSSPEED_S_FASTEST', 12),
    ('FC2_BUSSPEED_1000BASE_T', 10),
    ('FC2_BUSSPEED_S400', 2),
])


fc2PCIeBusSpeed = Enum('fc2PCIeBusSpeed', [
    ('FC2_PCIE_BUSSPEED_2_5', 0),
    ('FC2_PCIE_BUSSPEED_FORCE_32BITS', 2147483647),
    ('FC2_PCIE_BUSSPEED_UNKNOWN', -1),
    ('FC2_PCIE_BUSSPEED_5_0', 1),
])


fc2DriverType = Enum('fc2DriverType', [
    ('FC2_DRIVER_USB_NONE', 5),
    ('FC2_DRIVER_FORCE_32BITS', 2147483647),
    ('FC2_DRIVER_UNKNOWN', -1),
    ('FC2_DRIVER_USB_CAM', 6),
    ('FC2_DRIVER_1394_VIDEO1394', 3),
    ('FC2_DRIVER_GIGE_NONE', 8),
    ('FC2_DRIVER_GIGE_LWF', 11),
    ('FC2_DRIVER_GIGE_PRO', 10),
    ('FC2_DRIVER_1394_CAM', 0),
    ('FC2_DRIVER_1394_RAW1394', 4),
    ('FC2_DRIVER_1394_JUJU', 2),
    ('FC2_DRIVER_USB3_PRO', 7),
    ('FC2_DRIVER_GIGE_FILTER', 9),
    ('FC2_DRIVER_1394_PRO', 1),
])


fc2ColorProcessingAlgorithm = Enum('fc2ColorProcessingAlgorithm', [
    ('FC2_IPP', 6),
    ('FC2_EDGE_SENSING', 3),
    ('FC2_COLOR_PROCESSING_ALGORITHM_FORCE_32BITS', 2147483647),
    ('FC2_WEIGHTED_DIRECTIONAL', 8),
    ('FC2_RIGOROUS', 5),
    ('FC2_NO_COLOR_PROCESSING', 1),
    ('FC2_DEFAULT', 0),
    ('FC2_NEAREST_NEIGHBOR_FAST', 2),
    ('FC2_HQ_LINEAR', 4),
    ('FC2_DIRECTIONAL', 7),
])


fc2BayerTileFormat = Enum('fc2BayerTileFormat', [
    ('FC2_BT_GRBG', 2),
    ('FC2_BT_GBRG', 3),
    ('FC2_BT_FORCE_32BITS', 2147483647),
    ('FC2_BT_NONE', 0),
    ('FC2_BT_RGGB', 1),
    ('FC2_BT_BGGR', 4),
])


fc2ImageFileFormat = Enum('fc2ImageFileFormat', [
    ('FC2_FROM_FILE_EXT', -1),
    ('FC2_PNG', 6),
    ('FC2_IMAGE_FILE_FORMAT_FORCE_32BITS', 2147483647),
    ('FC2_RAW', 7),
    ('FC2_PGM', 0),
    ('FC2_JPEG2000', 4),
    ('FC2_PPM', 1),
    ('FC2_TIFF', 5),
    ('FC2_BMP', 2),
    ('FC2_JPEG', 3),
])


fc2GigEPropertyType = Enum('fc2GigEPropertyType', [
    ('FC2_HEARTBEAT', 0),
    ('PACKET_SIZE', 2),
    ('PACKET_DELAY', 3),
    ('FC2_HEARTBEAT_TIMEOUT', 1),
])


fc2StatisticsChannel = Enum('fc2StatisticsChannel', [
    ('FC2_STATISTICS_FORCE_32BITS', 2147483647),
    ('FC2_STATISTICS_RED', 1),
    ('FC2_STATISTICS_GREEN', 2),
    ('FC2_STATISTICS_BLUE', 3),
    ('FC2_STATISTICS_GREY', 0),
    ('FC2_STATISTICS_LIGHTNESS', 6),
    ('FC2_STATISTICS_HUE', 4),
    ('FC2_STATISTICS_SATURATION', 5),
])


fc2OSType = Enum('fc2OSType', [
    ('FC2_LINUX_X64', 3),
    ('FC2_UNKNOWN_OS', 5),
    ('FC2_WINDOWS_X86', 0),
    ('FC2_MAC', 4),
    ('FC2_WINDOWS_X64', 1),
    ('FC2_LINUX_X86', 2),
    ('FC2_OSTYPE_FORCE_32BITS', 2147483647),
])


fc2ByteOrder = Enum('fc2ByteOrder', [
    ('FC2_BYTE_ORDER_LITTLE_ENDIAN', 0),
    ('FC2_BYTE_ORDER_FORCE_32BITS', 2147483647),
    ('FC2_BYTE_ORDER_BIG_ENDIAN', 1),
])


fc2PortType = Enum('fc2PortType', [
    ('CONNECTED_TO_CHILD', 3),
    ('CONNECTED_TO_PARENT', 2),
    ('NOT_CONNECTED', 1),
])


fc2NodeType = Enum('fc2NodeType', [
    ('NODE', 3),
    ('BUS', 1),
    ('COMPUTER', 0),
    ('CAMERA', 2),
])


class fc2Image(ctypes.Structure):
    _fields_ = [
        ('rows', ctypes.c_uint),
        ('cols', ctypes.c_uint),
        ('stride', ctypes.c_uint),
        ('pData', ctypes.POINTER(ctypes.c_ubyte)),
        ('dataSize', ctypes.c_uint),
        ('receivedDataSize', ctypes.c_uint),
        ('format', ctypes.c_uint),
        ('bayerFormat', ctypes.c_uint),
        ('imageImpl', ctypes.c_void_p),
    ]


class fc2SystemInfo(ctypes.Structure):
    _fields_ = [
        ('osType', ctypes.c_uint),
        ('osDescription', ctypes.c_char * 512),
        ('byteOrder', ctypes.c_uint),
        ('sysMemSize', ctypes.c_ulong),
        ('cpuDescription', ctypes.c_char * 512),
        ('numCpuCores', ctypes.c_ulong),
        ('driverList', ctypes.c_char * 512),
        ('libraryList', ctypes.c_char * 512),
        ('gpuDescription', ctypes.c_char * 512),
        ('screenWidth', ctypes.c_ulong),
        ('screenHeight', ctypes.c_ulong),
        ('reserved', ctypes.c_uint * 16),
    ]


class fc2Version(ctypes.Structure):
    _fields_ = [
        ('major', ctypes.c_uint),
        ('minor', ctypes.c_uint),
        ('type', ctypes.c_uint),
        ('build', ctypes.c_uint),
    ]


class fc2IPAddress(ctypes.Structure):
    _fields_ = [
        ('octets', ctypes.c_ubyte * 4),
    ]


class fc2MACAddress(ctypes.Structure):
    _fields_ = [
        ('octets', ctypes.c_ubyte * 6),
    ]


class fc2GigEProperty(ctypes.Structure):
    _fields_ = [
        ('propType', ctypes.c_uint),
        ('isReadable', ctypes.c_int),
        ('isWritable', ctypes.c_int),
        ('min', ctypes.c_uint),
        ('max', ctypes.c_uint),
        ('value', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2GigEStreamChannel(ctypes.Structure):
    _fields_ = [
        ('networkInterfaceIndex', ctypes.c_uint),
        ('hostPort', ctypes.c_uint),
        ('doNotFragment', ctypes.c_int),
        ('packetSize', ctypes.c_uint),
        ('interPacketDelay', ctypes.c_uint),
        ('destinationIpAddress', fc2IPAddress),
        ('sourcePort', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2GigEConfig(ctypes.Structure):
    _fields_ = [
        ('enablePacketResend', ctypes.c_int),
        ('registerTimeoutRetries', ctypes.c_uint),
        ('registerTimeout', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2GigEImageSettingsInfo(ctypes.Structure):
    _fields_ = [
        ('maxWidth', ctypes.c_uint),
        ('maxHeight', ctypes.c_uint),
        ('offsetHStepSize', ctypes.c_uint),
        ('offsetVStepSize', ctypes.c_uint),
        ('imageHStepSize', ctypes.c_uint),
        ('imageVStepSize', ctypes.c_uint),
        ('pixelFormatBitField', ctypes.c_uint),
        ('vendorPixelFormatBitField', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 16),
    ]


class fc2GigEImageSettings(ctypes.Structure):
    _fields_ = [
        ('offsetX', ctypes.c_uint),
        ('offsetY', ctypes.c_uint),
        ('width', ctypes.c_uint),
        ('height', ctypes.c_uint),
        ('pixelFormat', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2Format7ImageSettings(ctypes.Structure):
    _fields_ = [
        ('mode', ctypes.c_uint),
        ('offsetX', ctypes.c_uint),
        ('offsetY', ctypes.c_uint),
        ('width', ctypes.c_uint),
        ('height', ctypes.c_uint),
        ('pixelFormat', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2Format7Info(ctypes.Structure):
    _fields_ = [
        ('mode', ctypes.c_uint),
        ('maxWidth', ctypes.c_uint),
        ('maxHeight', ctypes.c_uint),
        ('offsetHStepSize', ctypes.c_uint),
        ('offsetVStepSize', ctypes.c_uint),
        ('imageHStepSize', ctypes.c_uint),
        ('imageVStepSize', ctypes.c_uint),
        ('pixelFormatBitField', ctypes.c_uint),
        ('vendorPixelFormatBitField', ctypes.c_uint),
        ('packetSize', ctypes.c_uint),
        ('minPacketSize', ctypes.c_uint),
        ('maxPacketSize', ctypes.c_uint),
        ('percentage', ctypes.c_float),
        ('reserved', ctypes.c_uint * 16),
    ]


class fc2Format7PacketInfo(ctypes.Structure):
    _fields_ = [
        ('recommendedBytesPerPacket', ctypes.c_uint),
        ('maxBytesPerPacket', ctypes.c_uint),
        ('unitBytesPerPacket', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2Config(ctypes.Structure):
    _fields_ = [
        ('numBuffers', ctypes.c_uint),
        ('numImageNotifications', ctypes.c_uint),
        ('minNumImageNotifications', ctypes.c_uint),
        ('grabTimeout', ctypes.c_int),
        ('grabMode', ctypes.c_uint),
        ('highPerformanceRetrieveBuffer', ctypes.c_int),
        ('isochBusSpeed', ctypes.c_uint),
        ('asyncBusSpeed', ctypes.c_uint),
        ('bandwidthAllocation', ctypes.c_uint),
        ('registerTimeoutRetries', ctypes.c_uint),
        ('registerTimeout', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 16),
    ]


class fc2PropertyInfo(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_uint),
        ('present', ctypes.c_int),
        ('autoSupported', ctypes.c_int),
        ('manualSupported', ctypes.c_int),
        ('onOffSupported', ctypes.c_int),
        ('onePushSupported', ctypes.c_int),
        ('absValSupported', ctypes.c_int),
        ('readOutSupported', ctypes.c_int),
        ('min', ctypes.c_uint),
        ('max', ctypes.c_uint),
        ('absMin', ctypes.c_float),
        ('absMax', ctypes.c_float),
        ('pUnits', ctypes.c_char * 512),
        ('pUnitAbbr', ctypes.c_char * 512),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2TriggerDelayInfo(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_uint),
        ('present', ctypes.c_int),
        ('autoSupported', ctypes.c_int),
        ('manualSupported', ctypes.c_int),
        ('onOffSupported', ctypes.c_int),
        ('onePushSupported', ctypes.c_int),
        ('absValSupported', ctypes.c_int),
        ('readOutSupported', ctypes.c_int),
        ('min', ctypes.c_uint),
        ('max', ctypes.c_uint),
        ('absMin', ctypes.c_float),
        ('absMax', ctypes.c_float),
        ('pUnits', ctypes.c_char * 512),
        ('pUnitAbbr', ctypes.c_char * 512),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2Property(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_uint),
        ('present', ctypes.c_int),
        ('absControl', ctypes.c_int),
        ('onePush', ctypes.c_int),
        ('onOff', ctypes.c_int),
        ('autoManualMode', ctypes.c_int),
        ('valueA', ctypes.c_uint),
        ('valueB', ctypes.c_uint),
        ('absValue', ctypes.c_float),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2TriggerDelay(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_uint),
        ('present', ctypes.c_int),
        ('absControl', ctypes.c_int),
        ('onePush', ctypes.c_int),
        ('onOff', ctypes.c_int),
        ('autoManualMode', ctypes.c_int),
        ('valueA', ctypes.c_uint),
        ('valueB', ctypes.c_uint),
        ('absValue', ctypes.c_float),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2TriggerModeInfo(ctypes.Structure):
    _fields_ = [
        ('present', ctypes.c_int),
        ('readOutSupported', ctypes.c_int),
        ('onOffSupported', ctypes.c_int),
        ('polaritySupported', ctypes.c_int),
        ('valueReadable', ctypes.c_int),
        ('sourceMask', ctypes.c_uint),
        ('softwareTriggerSupported', ctypes.c_int),
        ('modeMask', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2TriggerMode(ctypes.Structure):
    _fields_ = [
        ('onOff', ctypes.c_int),
        ('polarity', ctypes.c_uint),
        ('source', ctypes.c_uint),
        ('mode', ctypes.c_uint),
        ('parameter', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2StrobeInfo(ctypes.Structure):
    _fields_ = [
        ('source', ctypes.c_uint),
        ('present', ctypes.c_int),
        ('readOutSupported', ctypes.c_int),
        ('onOffSupported', ctypes.c_int),
        ('polaritySupported', ctypes.c_int),
        ('minValue', ctypes.c_float),
        ('maxValue', ctypes.c_float),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2StrobeControl(ctypes.Structure):
    _fields_ = [
        ('source', ctypes.c_uint),
        ('onOff', ctypes.c_int),
        ('polarity', ctypes.c_uint),
        ('delay', ctypes.c_float),
        ('duration', ctypes.c_float),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2TimeStamp(ctypes.Structure):
    _fields_ = [
        ('seconds', ctypes.c_long),
        ('microSeconds', ctypes.c_uint),
        ('cycleSeconds', ctypes.c_uint),
        ('cycleCount', ctypes.c_uint),
        ('cycleOffset', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2ConfigROM(ctypes.Structure):
    _fields_ = [
        ('nodeVendorId', ctypes.c_uint),
        ('chipIdHi', ctypes.c_uint),
        ('chipIdLo', ctypes.c_uint),
        ('unitSpecId', ctypes.c_uint),
        ('unitSWVer', ctypes.c_uint),
        ('unitSubSWVer', ctypes.c_uint),
        ('vendorUniqueInfo_0', ctypes.c_uint),
        ('vendorUniqueInfo_1', ctypes.c_uint),
        ('vendorUniqueInfo_2', ctypes.c_uint),
        ('vendorUniqueInfo_3', ctypes.c_uint),
        ('pszKeyword', ctypes.c_char * 512),
        ('reserved', ctypes.c_uint * 16),
    ]


class fc2CameraInfo(ctypes.Structure):
    _fields_ = [
        ('serialNumber', ctypes.c_uint),
        ('interfaceType', ctypes.c_uint),
        ('driverType', ctypes.c_uint),
        ('isColorCamera', ctypes.c_int),
        ('modelName', ctypes.c_char * 512),
        ('vendorName', ctypes.c_char * 512),
        ('sensorInfo', ctypes.c_char * 512),
        ('sensorResolution', ctypes.c_char * 512),
        ('driverName', ctypes.c_char * 512),
        ('firmwareVersion', ctypes.c_char * 512),
        ('firmwareBuildTime', ctypes.c_char * 512),
        ('maximumBusSpeed', ctypes.c_uint),
        ('bayerTileFormat', ctypes.c_uint),
        ('pcieBusSpeed', ctypes.c_uint),
        ('nodeNumber', ctypes.c_ushort),
        ('busNumber', ctypes.c_ushort),
        ('iidcVer', ctypes.c_uint),
        ('configROM', fc2ConfigROM),
        ('gigEMajorVersion', ctypes.c_uint),
        ('gigEMinorVersion', ctypes.c_uint),
        ('userDefinedName', ctypes.c_char * 512),
        ('xmlURL1', ctypes.c_char * 512),
        ('xmlURL2', ctypes.c_char * 512),
        ('macAddress', fc2MACAddress),
        ('ipAddress', fc2IPAddress),
        ('subnetMask', fc2IPAddress),
        ('defaultGateway', fc2IPAddress),
        ('ccpStatus', ctypes.c_uint),
        ('applicationIPAddress', ctypes.c_uint),
        ('applicationPort', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 16),
    ]


class fc2EmbeddedImageInfoProperty(ctypes.Structure):
    _fields_ = [
        ('available', ctypes.c_int),
        ('onOff', ctypes.c_int),
    ]


class fc2EmbeddedImageInfo(ctypes.Structure):
    _fields_ = [
        ('timestamp', fc2EmbeddedImageInfoProperty),
        ('gain', fc2EmbeddedImageInfoProperty),
        ('shutter', fc2EmbeddedImageInfoProperty),
        ('brightness', fc2EmbeddedImageInfoProperty),
        ('exposure', fc2EmbeddedImageInfoProperty),
        ('whiteBalance', fc2EmbeddedImageInfoProperty),
        ('frameCounter', fc2EmbeddedImageInfoProperty),
        ('strobePattern', fc2EmbeddedImageInfoProperty),
        ('GPIOPinState', fc2EmbeddedImageInfoProperty),
        ('ROIPosition', fc2EmbeddedImageInfoProperty),
    ]


class fc2ImageMetadata(ctypes.Structure):
    _fields_ = [
        ('embeddedTimeStamp', ctypes.c_uint),
        ('embeddedGain', ctypes.c_uint),
        ('embeddedShutter', ctypes.c_uint),
        ('embeddedBrightness', ctypes.c_uint),
        ('embeddedExposure', ctypes.c_uint),
        ('embeddedWhiteBalance', ctypes.c_uint),
        ('embeddedFrameCounter', ctypes.c_uint),
        ('embeddedStrobePattern', ctypes.c_uint),
        ('embeddedGPIOPinState', ctypes.c_uint),
        ('embeddedROIPosition', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 31),
    ]


class fc2LUTData(ctypes.Structure):
    _fields_ = [
        ('supported', ctypes.c_int),
        ('enabled', ctypes.c_int),
        ('numBanks', ctypes.c_uint),
        ('numChannels', ctypes.c_uint),
        ('inputBitDepth', ctypes.c_uint),
        ('outputBitDepth', ctypes.c_uint),
        ('numEntries', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 8),
    ]


class fc2CameraStats(ctypes.Structure):
    _fields_ = [
        ('imageDropped', ctypes.c_uint),
        ('imageCorrupt', ctypes.c_uint),
        ('imageXmitFailed', ctypes.c_uint),
        ('imageDriverDropped', ctypes.c_uint),
        ('regReadFailed', ctypes.c_uint),
        ('regWriteFailed', ctypes.c_uint),
        ('portErrors', ctypes.c_uint),
        ('cameraPowerUp', ctypes.c_int),
        ('cameraVoltages', ctypes.c_float * 8),
        ('numVoltages', ctypes.c_uint),
        ('cameraCurrents', ctypes.c_float * 8),
        ('numCurrents', ctypes.c_uint),
        ('temperature', ctypes.c_uint),
        ('timeSinceInitialization', ctypes.c_uint),
        ('timeSinceBusReset', ctypes.c_uint),
        ('timeStamp', fc2TimeStamp),
        ('numResendPacketsRequested', ctypes.c_uint),
        ('numResendPacketsReceived', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 16),
    ]


class fc2PNGOption(ctypes.Structure):
    _fields_ = [
        ('interlaced', ctypes.c_int),
        ('compressionLevel', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 16),
    ]


class fc2PPMOption(ctypes.Structure):
    _fields_ = [
        ('binaryFile', ctypes.c_int),
        ('reserved', ctypes.c_uint * 16),
    ]


class fc2PGMOption(ctypes.Structure):
    _fields_ = [
        ('binaryFile', ctypes.c_int),
        ('reserved', ctypes.c_uint * 16),
    ]


fc2TIFFCompressionMethod = Enum('fc2TIFFCompressionMethod', [
    ('FC2_TIFF_PACKBITS', 2),
    ('FC2_TIFF_ADOBE_DEFLATE', 4),
    ('FC2_TIFF_CCITTFAX4', 6),
    ('FC2_TIFF_JPEG', 8),
    ('FC2_TIFF_CCITTFAX3', 5),
    ('FC2_TIFF_LZW', 7),
    ('FC2_TIFF_DEFLATE', 3),
    ('FC2_TIFF_NONE', 1),
])


class fc2TIFFOption(ctypes.Structure):
    _fields_ = [
        ('compression', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 16),
    ]


class fc2JPEGOption(ctypes.Structure):
    _fields_ = [
        ('progressive', ctypes.c_int),
        ('quality', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 16),
    ]


class fc2JPG2Option(ctypes.Structure):
    _fields_ = [
        ('quality', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 16),
    ]


class fc2BMPOption(ctypes.Structure):
    _fields_ = [
        ('indexedColor_8bit', ctypes.c_int),
        ('reserved', ctypes.c_uint * 16),
    ]


fc2CallbackHandle = ctypes.c_void_p
fc2BusEventCallback = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.c_uint,
)

fc2ImageEventCallback = ctypes.CFUNCTYPE(
    None,
    ctypes.POINTER(fc2Image),
    ctypes.c_void_p,
)

fc2AsyncCommandCallback = ctypes.CFUNCTYPE(
    None,
    ctypes.c_uint,
    ctypes.c_void_p,
)

fc2CameraEventCallback = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
)

class fc2EventOptions(ctypes.Structure):
    _fields_ = [
        ('EventCallbackFcn', ctypes.POINTER(None)),
        ('EventName', ctypes.c_char_p),
        ('EventUserData', ctypes.c_void_p),
        ('EventUserDataSize', ctypes.c_ulong),
    ]


class fc2EventCallbackData(ctypes.Structure):
    _fields_ = [
        ('EventUserData', ctypes.c_void_p),
        ('EventUserDataSize', ctypes.c_ulong),
        ('EventName', ctypes.c_char_p),
        ('EventID', ctypes.c_ulong),
        ('EventTimestamp', ctypes.c_ulong),
        ('EventData', ctypes.c_void_p),
        ('EventDataSize', ctypes.c_ulong),
    ]


fc2CreateContext = Function(
    'fc2CreateContext', ctypes.c_uint,
    ('pContext', ctypes.POINTER(fc2Context)),
)
fc2CreateContext.generate_spec(_lib)

fc2CreateGigEContext = Function(
    'fc2CreateGigEContext', ctypes.c_uint,
    ('pContext', ctypes.POINTER(fc2Context)),
)
fc2CreateGigEContext.generate_spec(_lib)

fc2DestroyContext = Function(
    'fc2DestroyContext', ctypes.c_uint,
    ('context', ctypes.c_void_p),
)
fc2DestroyContext.generate_spec(_lib)

fc2FireBusReset = Function(
    'fc2FireBusReset', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pGuid', ctypes.POINTER(fc2PGRGuid)),
)
fc2FireBusReset.generate_spec(_lib)

fc2GetNumOfCameras = Function(
    'fc2GetNumOfCameras', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pNumCameras', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetNumOfCameras.generate_spec(_lib)

fc2GetCameraFromIPAddress = Function(
    'fc2GetCameraFromIPAddress', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('ipAddress', fc2IPAddress),
    ('pGuid', ctypes.POINTER(fc2PGRGuid)),
)
fc2GetCameraFromIPAddress.generate_spec(_lib)

fc2GetCameraFromIndex = Function(
    'fc2GetCameraFromIndex', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('index', ctypes.c_uint),
    ('pGuid', ctypes.POINTER(fc2PGRGuid)),
)
fc2GetCameraFromIndex.generate_spec(_lib)

fc2GetCameraFromSerialNumber = Function(
    'fc2GetCameraFromSerialNumber', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('serialNumber', ctypes.c_uint),
    ('pGuid', ctypes.POINTER(fc2PGRGuid)),
)
fc2GetCameraFromSerialNumber.generate_spec(_lib)

fc2GetCameraSerialNumberFromIndex = Function(
    'fc2GetCameraSerialNumberFromIndex', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('index', ctypes.c_uint),
    ('pSerialNumber', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetCameraSerialNumberFromIndex.generate_spec(_lib)

fc2GetInterfaceTypeFromGuid = Function(
    'fc2GetInterfaceTypeFromGuid', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pGuid', ctypes.POINTER(fc2PGRGuid)),
    ('pInterfaceType', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetInterfaceTypeFromGuid.generate_spec(_lib)

fc2GetNumOfDevices = Function(
    'fc2GetNumOfDevices', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pNumDevices', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetNumOfDevices.generate_spec(_lib)

fc2GetDeviceFromIndex = Function(
    'fc2GetDeviceFromIndex', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('index', ctypes.c_uint),
    ('pGuid', ctypes.POINTER(fc2PGRGuid)),
)
fc2GetDeviceFromIndex.generate_spec(_lib)

fc2ReadPhyRegister = Function(
    'fc2ReadPhyRegister', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('guid', fc2PGRGuid),
    ('page', ctypes.c_uint),
    ('port', ctypes.c_uint),
    ('address', ctypes.c_uint),
    ('pValue', ctypes.POINTER(ctypes.c_uint)),
)
fc2ReadPhyRegister.generate_spec(_lib)

fc2WritePhyRegister = Function(
    'fc2WritePhyRegister', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('guid', fc2PGRGuid),
    ('page', ctypes.c_uint),
    ('port', ctypes.c_uint),
    ('address', ctypes.c_uint),
    ('value', ctypes.c_uint),
)
fc2WritePhyRegister.generate_spec(_lib)

fc2GetUsbLinkInfo = Function(
    'fc2GetUsbLinkInfo', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('guid', fc2PGRGuid),
    ('pValue', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetUsbLinkInfo.generate_spec(_lib)

fc2GetUsbPortStatus = Function(
    'fc2GetUsbPortStatus', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('guid', fc2PGRGuid),
    ('pValue', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetUsbPortStatus.generate_spec(_lib)

fc2GetTopology = Function(
    'fc2GetTopology', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pTopologyNodeContext', ctypes.POINTER(fc2Context)),
)
fc2GetTopology.generate_spec(_lib)

fc2RegisterCallback = Function(
    'fc2RegisterCallback', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('enumCallback', ctypes.POINTER(None)),
    ('callbackType', ctypes.c_uint),
    ('pParameter', ctypes.c_void_p),
    ('pCallbackHandle', ctypes.POINTER(fc2Context)),
)
fc2RegisterCallback.generate_spec(_lib)

fc2UnregisterCallback = Function(
    'fc2UnregisterCallback', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('callbackHandle', ctypes.c_void_p),
)
fc2UnregisterCallback.generate_spec(_lib)

fc2RescanBus = Function(
    'fc2RescanBus', ctypes.c_uint,
    ('context', ctypes.c_void_p),
)
fc2RescanBus.generate_spec(_lib)

fc2ForceIPAddressToCamera = Function(
    'fc2ForceIPAddressToCamera', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('macAddress', fc2MACAddress),
    ('ipAddress', fc2IPAddress),
    ('subnetMask', fc2IPAddress),
    ('defaultGateway', fc2IPAddress),
)
fc2ForceIPAddressToCamera.generate_spec(_lib)

fc2ForceAllIPAddressesAutomatically = Function(
    'fc2ForceAllIPAddressesAutomatically', ctypes.c_uint,
)
fc2ForceAllIPAddressesAutomatically.generate_spec(_lib)

fc2ForceIPAddressAutomatically = Function(
    'fc2ForceIPAddressAutomatically', ctypes.c_uint,
    ('serialNumber', ctypes.c_uint),
)
fc2ForceIPAddressAutomatically.generate_spec(_lib)

fc2DiscoverGigECameras = Function(
    'fc2DiscoverGigECameras', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('gigECameras', ctypes.POINTER(fc2CameraInfo)),
    ('arraySize', ctypes.POINTER(ctypes.c_uint)),
)
fc2DiscoverGigECameras.generate_spec(_lib)

fc2IsCameraControlable = Function(
    'fc2IsCameraControlable', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pGuid', ctypes.POINTER(fc2PGRGuid)),
    ('pControlable', ctypes.POINTER(BOOL)),
)
fc2IsCameraControlable.generate_spec(_lib)

fc2Connect = Function(
    'fc2Connect', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('guid', ctypes.POINTER(fc2PGRGuid)),
)
fc2Connect.generate_spec(_lib)

fc2Disconnect = Function(
    'fc2Disconnect', ctypes.c_uint,
    ('context', ctypes.c_void_p),
)
fc2Disconnect.generate_spec(_lib)

fc2IsConnected = Function(
    'fc2IsConnected', ctypes.c_int,
    ('context', ctypes.c_void_p),
)
fc2IsConnected.generate_spec(_lib)

fc2SetCallback = Function(
    'fc2SetCallback', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pCallbackFn', ctypes.POINTER(None)),
    ('pCallbackData', ctypes.c_void_p),
)
fc2SetCallback.generate_spec(_lib)

fc2StartCapture = Function(
    'fc2StartCapture', ctypes.c_uint,
    ('context', ctypes.c_void_p),
)
fc2StartCapture.generate_spec(_lib)

fc2StartCaptureCallback = Function(
    'fc2StartCaptureCallback', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pCallbackFn', ctypes.POINTER(None)),
    ('pCallbackData', ctypes.c_void_p),
)
fc2StartCaptureCallback.generate_spec(_lib)

fc2StartSyncCapture = Function(
    'fc2StartSyncCapture', ctypes.c_uint,
    ('numCameras', ctypes.c_uint),
    ('pContexts', ctypes.POINTER(fc2Context)),
)
fc2StartSyncCapture.generate_spec(_lib)

fc2StartSyncCaptureCallback = Function(
    'fc2StartSyncCaptureCallback', ctypes.c_uint,
    ('numCameras', ctypes.c_uint),
    ('pContexts', ctypes.POINTER(fc2Context)),
    ('pCallbackFns', ctypes.POINTER(fc2BusEventCallback)),
    ('pCallbackDataArray', ctypes.POINTER(fc2Context)),
)
fc2StartSyncCaptureCallback.generate_spec(_lib)

fc2RetrieveBuffer = Function(
    'fc2RetrieveBuffer', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pImage', ctypes.POINTER(fc2Image)),
)
fc2RetrieveBuffer.generate_spec(_lib)

fc2StopCapture = Function(
    'fc2StopCapture', ctypes.c_uint,
    ('context', ctypes.c_void_p),
)
fc2StopCapture.generate_spec(_lib)

fc2WaitForBufferEvent = Function(
    'fc2WaitForBufferEvent', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pImage', ctypes.POINTER(fc2Image)),
    ('eventNumber', ctypes.c_uint),
)
fc2WaitForBufferEvent.generate_spec(_lib)

fc2SetUserBuffers = Function(
    'fc2SetUserBuffers', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('ppMemBuffers', ctypes.POINTER(ctypes.c_ubyte)),
    ('size', ctypes.c_int),
    ('nNumBuffers', ctypes.c_int),
)
fc2SetUserBuffers.generate_spec(_lib)

fc2GetConfiguration = Function(
    'fc2GetConfiguration', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('config', ctypes.POINTER(fc2Config)),
)
fc2GetConfiguration.generate_spec(_lib)

fc2SetConfiguration = Function(
    'fc2SetConfiguration', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('config', ctypes.POINTER(fc2Config)),
)
fc2SetConfiguration.generate_spec(_lib)

fc2GetCameraInfo = Function(
    'fc2GetCameraInfo', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pCameraInfo', ctypes.POINTER(fc2CameraInfo)),
)
fc2GetCameraInfo.generate_spec(_lib)

fc2GetPropertyInfo = Function(
    'fc2GetPropertyInfo', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('propInfo', ctypes.POINTER(fc2PropertyInfo)),
)
fc2GetPropertyInfo.generate_spec(_lib)

fc2GetProperty = Function(
    'fc2GetProperty', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('prop', ctypes.POINTER(fc2Property)),
)
fc2GetProperty.generate_spec(_lib)

fc2SetProperty = Function(
    'fc2SetProperty', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('prop', ctypes.POINTER(fc2Property)),
)
fc2SetProperty.generate_spec(_lib)

fc2SetPropertyBroadcast = Function(
    'fc2SetPropertyBroadcast', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('prop', ctypes.POINTER(fc2Property)),
)
fc2SetPropertyBroadcast.generate_spec(_lib)

fc2GetGPIOPinDirection = Function(
    'fc2GetGPIOPinDirection', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pin', ctypes.c_uint),
    ('pDirection', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetGPIOPinDirection.generate_spec(_lib)

fc2SetGPIOPinDirection = Function(
    'fc2SetGPIOPinDirection', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pin', ctypes.c_uint),
    ('direction', ctypes.c_uint),
)
fc2SetGPIOPinDirection.generate_spec(_lib)

fc2SetGPIOPinDirectionBroadcast = Function(
    'fc2SetGPIOPinDirectionBroadcast', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pin', ctypes.c_uint),
    ('direction', ctypes.c_uint),
)
fc2SetGPIOPinDirectionBroadcast.generate_spec(_lib)

fc2GetTriggerModeInfo = Function(
    'fc2GetTriggerModeInfo', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('triggerModeInfo', ctypes.POINTER(fc2TriggerModeInfo)),
)
fc2GetTriggerModeInfo.generate_spec(_lib)

fc2GetTriggerMode = Function(
    'fc2GetTriggerMode', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('triggerMode', ctypes.POINTER(fc2TriggerMode)),
)
fc2GetTriggerMode.generate_spec(_lib)

fc2SetTriggerMode = Function(
    'fc2SetTriggerMode', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('triggerMode', ctypes.POINTER(fc2TriggerMode)),
)
fc2SetTriggerMode.generate_spec(_lib)

fc2SetTriggerModeBroadcast = Function(
    'fc2SetTriggerModeBroadcast', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('triggerMode', ctypes.POINTER(fc2TriggerMode)),
)
fc2SetTriggerModeBroadcast.generate_spec(_lib)

fc2FireSoftwareTrigger = Function(
    'fc2FireSoftwareTrigger', ctypes.c_uint,
    ('context', ctypes.c_void_p),
)
fc2FireSoftwareTrigger.generate_spec(_lib)

fc2FireSoftwareTriggerBroadcast = Function(
    'fc2FireSoftwareTriggerBroadcast', ctypes.c_uint,
    ('context', ctypes.c_void_p),
)
fc2FireSoftwareTriggerBroadcast.generate_spec(_lib)

fc2GetTriggerDelayInfo = Function(
    'fc2GetTriggerDelayInfo', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('triggerDelayInfo', ctypes.POINTER(fc2PropertyInfo)),
)
fc2GetTriggerDelayInfo.generate_spec(_lib)

fc2GetTriggerDelay = Function(
    'fc2GetTriggerDelay', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('triggerDelay', ctypes.POINTER(fc2Property)),
)
fc2GetTriggerDelay.generate_spec(_lib)

fc2SetTriggerDelay = Function(
    'fc2SetTriggerDelay', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('triggerDelay', ctypes.POINTER(fc2Property)),
)
fc2SetTriggerDelay.generate_spec(_lib)

fc2SetTriggerDelayBroadcast = Function(
    'fc2SetTriggerDelayBroadcast', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('triggerDelay', ctypes.POINTER(fc2Property)),
)
fc2SetTriggerDelayBroadcast.generate_spec(_lib)

fc2GetStrobeInfo = Function(
    'fc2GetStrobeInfo', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('strobeInfo', ctypes.POINTER(fc2StrobeInfo)),
)
fc2GetStrobeInfo.generate_spec(_lib)

fc2GetStrobe = Function(
    'fc2GetStrobe', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('strobeControl', ctypes.POINTER(fc2StrobeControl)),
)
fc2GetStrobe.generate_spec(_lib)

fc2SetStrobe = Function(
    'fc2SetStrobe', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('strobeControl', ctypes.POINTER(fc2StrobeControl)),
)
fc2SetStrobe.generate_spec(_lib)

fc2SetStrobeBroadcast = Function(
    'fc2SetStrobeBroadcast', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('strobeControl', ctypes.POINTER(fc2StrobeControl)),
)
fc2SetStrobeBroadcast.generate_spec(_lib)

fc2GetLUTInfo = Function(
    'fc2GetLUTInfo', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pData', ctypes.POINTER(fc2LUTData)),
)
fc2GetLUTInfo.generate_spec(_lib)

fc2GetLUTBankInfo = Function(
    'fc2GetLUTBankInfo', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('bank', ctypes.c_uint),
    ('pReadSupported', ctypes.POINTER(BOOL)),
    ('pWriteSupported', ctypes.POINTER(BOOL)),
)
fc2GetLUTBankInfo.generate_spec(_lib)

fc2GetActiveLUTBank = Function(
    'fc2GetActiveLUTBank', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pActiveBank', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetActiveLUTBank.generate_spec(_lib)

fc2SetActiveLUTBank = Function(
    'fc2SetActiveLUTBank', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('activeBank', ctypes.c_uint),
)
fc2SetActiveLUTBank.generate_spec(_lib)

fc2EnableLUT = Function(
    'fc2EnableLUT', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('on', ctypes.c_int),
)
fc2EnableLUT.generate_spec(_lib)

fc2GetLUTChannel = Function(
    'fc2GetLUTChannel', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('bank', ctypes.c_uint),
    ('channel', ctypes.c_uint),
    ('sizeEntries', ctypes.c_uint),
    ('pEntries', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetLUTChannel.generate_spec(_lib)

fc2SetLUTChannel = Function(
    'fc2SetLUTChannel', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('bank', ctypes.c_uint),
    ('channel', ctypes.c_uint),
    ('sizeEntries', ctypes.c_uint),
    ('pEntries', ctypes.POINTER(ctypes.c_uint)),
)
fc2SetLUTChannel.generate_spec(_lib)

fc2GetMemoryChannel = Function(
    'fc2GetMemoryChannel', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pCurrentChannel', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetMemoryChannel.generate_spec(_lib)

fc2SaveToMemoryChannel = Function(
    'fc2SaveToMemoryChannel', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('channel', ctypes.c_uint),
)
fc2SaveToMemoryChannel.generate_spec(_lib)

fc2RestoreFromMemoryChannel = Function(
    'fc2RestoreFromMemoryChannel', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('channel', ctypes.c_uint),
)
fc2RestoreFromMemoryChannel.generate_spec(_lib)

fc2GetMemoryChannelInfo = Function(
    'fc2GetMemoryChannelInfo', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pNumChannels', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetMemoryChannelInfo.generate_spec(_lib)

fc2GetEmbeddedImageInfo = Function(
    'fc2GetEmbeddedImageInfo', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pInfo', ctypes.POINTER(fc2EmbeddedImageInfo)),
)
fc2GetEmbeddedImageInfo.generate_spec(_lib)

fc2SetEmbeddedImageInfo = Function(
    'fc2SetEmbeddedImageInfo', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pInfo', ctypes.POINTER(fc2EmbeddedImageInfo)),
)
fc2SetEmbeddedImageInfo.generate_spec(_lib)

fc2WriteRegister = Function(
    'fc2WriteRegister', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('address', ctypes.c_uint),
    ('value', ctypes.c_uint),
)
fc2WriteRegister.generate_spec(_lib)

fc2ReadRegister = Function(
    'fc2ReadRegister', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('address', ctypes.c_uint),
    ('pValue', ctypes.POINTER(ctypes.c_uint)),
)
fc2ReadRegister.generate_spec(_lib)

fc2WriteRegisterBroadcast = Function(
    'fc2WriteRegisterBroadcast', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('address', ctypes.c_uint),
    ('value', ctypes.c_uint),
)
fc2WriteRegisterBroadcast.generate_spec(_lib)

fc2WriteRegisterBlock = Function(
    'fc2WriteRegisterBlock', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('addressHigh', ctypes.c_ushort),
    ('addressLow', ctypes.c_uint),
    ('pBuffer', ctypes.POINTER(ctypes.c_uint)),
    ('length', ctypes.c_uint),
)
fc2WriteRegisterBlock.generate_spec(_lib)

fc2ReadRegisterBlock = Function(
    'fc2ReadRegisterBlock', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('addressHigh', ctypes.c_ushort),
    ('addressLow', ctypes.c_uint),
    ('pBuffer', ctypes.POINTER(ctypes.c_uint)),
    ('length', ctypes.c_uint),
)
fc2ReadRegisterBlock.generate_spec(_lib)

fc2GetRegisterString = Function(
    'fc2GetRegisterString', ctypes.c_char_p,
    ('registerVal', ctypes.c_uint),
)
fc2GetRegisterString.generate_spec(_lib)

fc2GetCycleTime = Function(
    'fc2GetCycleTime', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pTimeStamp', ctypes.POINTER(fc2TimeStamp)),
)
fc2GetCycleTime.generate_spec(_lib)

fc2GetStats = Function(
    'fc2GetStats', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pCameraStats', ctypes.POINTER(fc2CameraStats)),
)
fc2GetStats.generate_spec(_lib)

#ResetStats = Function(
#    'ResetStats', ctypes.c_uint,
#)
#ResetStats.generate_spec(_lib)

fc2RegisterEvent = Function(
    'fc2RegisterEvent', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pOpts', ctypes.POINTER(fc2EventOptions)),
)
fc2RegisterEvent.generate_spec(_lib)

fc2DeregisterEvent = Function(
    'fc2DeregisterEvent', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pOpts', ctypes.POINTER(fc2EventOptions)),
)
fc2DeregisterEvent.generate_spec(_lib)

fc2RegisterAllEvents = Function(
    'fc2RegisterAllEvents', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pOpts', ctypes.POINTER(fc2EventOptions)),
)
fc2RegisterAllEvents.generate_spec(_lib)

fc2DeregisterAllEvents = Function(
    'fc2DeregisterAllEvents', ctypes.c_uint,
    ('context', ctypes.c_void_p),
)
fc2DeregisterAllEvents.generate_spec(_lib)

fc2GetVideoModeAndFrameRateInfo = Function(
    'fc2GetVideoModeAndFrameRateInfo', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('videoMode', ctypes.c_uint),
    ('frameRate', ctypes.c_uint),
    ('pSupported', ctypes.POINTER(BOOL)),
)
fc2GetVideoModeAndFrameRateInfo.generate_spec(_lib)

fc2GetVideoModeAndFrameRate = Function(
    'fc2GetVideoModeAndFrameRate', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('videoMode', ctypes.POINTER(ctypes.c_uint)),
    ('frameRate', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetVideoModeAndFrameRate.generate_spec(_lib)

fc2SetVideoModeAndFrameRate = Function(
    'fc2SetVideoModeAndFrameRate', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('videoMode', ctypes.c_uint),
    ('frameRate', ctypes.c_uint),
)
fc2SetVideoModeAndFrameRate.generate_spec(_lib)

fc2GetFormat7Info = Function(
    'fc2GetFormat7Info', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('info', ctypes.POINTER(fc2Format7Info)),
    ('pSupported', ctypes.POINTER(BOOL)),
)
fc2GetFormat7Info.generate_spec(_lib)

fc2ValidateFormat7Settings = Function(
    'fc2ValidateFormat7Settings', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('imageSettings', ctypes.POINTER(fc2Format7ImageSettings)),
    ('settingsAreValid', ctypes.POINTER(BOOL)),
    ('packetInfo', ctypes.POINTER(fc2Format7PacketInfo)),
)
fc2ValidateFormat7Settings.generate_spec(_lib)

fc2GetFormat7Configuration = Function(
    'fc2GetFormat7Configuration', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('imageSettings', ctypes.POINTER(fc2Format7ImageSettings)),
    ('packetSize', ctypes.POINTER(ctypes.c_uint)),
    ('percentage', ctypes.POINTER(ctypes.c_float)),
)
fc2GetFormat7Configuration.generate_spec(_lib)

fc2SetFormat7ConfigurationPacket = Function(
    'fc2SetFormat7ConfigurationPacket', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('imageSettings', ctypes.POINTER(fc2Format7ImageSettings)),
    ('packetSize', ctypes.c_uint),
)
fc2SetFormat7ConfigurationPacket.generate_spec(_lib)

fc2SetFormat7Configuration = Function(
    'fc2SetFormat7Configuration', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('imageSettings', ctypes.POINTER(fc2Format7ImageSettings)),
    ('percentSpeed', ctypes.c_float),
)
fc2SetFormat7Configuration.generate_spec(_lib)

fc2WriteGVCPRegister = Function(
    'fc2WriteGVCPRegister', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('address', ctypes.c_uint),
    ('value', ctypes.c_uint),
)
fc2WriteGVCPRegister.generate_spec(_lib)

fc2WriteGVCPRegisterBroadcast = Function(
    'fc2WriteGVCPRegisterBroadcast', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('address', ctypes.c_uint),
    ('value', ctypes.c_uint),
)
fc2WriteGVCPRegisterBroadcast.generate_spec(_lib)

fc2ReadGVCPRegister = Function(
    'fc2ReadGVCPRegister', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('address', ctypes.c_uint),
    ('pValue', ctypes.POINTER(ctypes.c_uint)),
)
fc2ReadGVCPRegister.generate_spec(_lib)

fc2WriteGVCPRegisterBlock = Function(
    'fc2WriteGVCPRegisterBlock', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('address', ctypes.c_uint),
    ('pBuffer', ctypes.POINTER(ctypes.c_uint)),
    ('length', ctypes.c_uint),
)
fc2WriteGVCPRegisterBlock.generate_spec(_lib)

fc2ReadGVCPRegisterBlock = Function(
    'fc2ReadGVCPRegisterBlock', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('address', ctypes.c_uint),
    ('pBuffer', ctypes.POINTER(ctypes.c_uint)),
    ('length', ctypes.c_uint),
)
fc2ReadGVCPRegisterBlock.generate_spec(_lib)

fc2WriteGVCPMemory = Function(
    'fc2WriteGVCPMemory', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('address', ctypes.c_uint),
    ('pBuffer', ctypes.POINTER(ctypes.c_ubyte)),
    ('length', ctypes.c_uint),
)
fc2WriteGVCPMemory.generate_spec(_lib)

fc2ReadGVCPMemory = Function(
    'fc2ReadGVCPMemory', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('address', ctypes.c_uint),
    ('pBuffer', ctypes.POINTER(ctypes.c_ubyte)),
    ('length', ctypes.c_uint),
)
fc2ReadGVCPMemory.generate_spec(_lib)

fc2GetGigEProperty = Function(
    'fc2GetGigEProperty', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pGigEProp', ctypes.POINTER(fc2GigEProperty)),
)
fc2GetGigEProperty.generate_spec(_lib)

fc2SetGigEProperty = Function(
    'fc2SetGigEProperty', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pGigEProp', ctypes.POINTER(fc2GigEProperty)),
)
fc2SetGigEProperty.generate_spec(_lib)

fc2DiscoverGigEPacketSize = Function(
    'fc2DiscoverGigEPacketSize', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('packetSize', ctypes.POINTER(ctypes.c_uint)),
)
fc2DiscoverGigEPacketSize.generate_spec(_lib)

fc2QueryGigEImagingMode = Function(
    'fc2QueryGigEImagingMode', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('mode', ctypes.c_uint),
    ('isSupported', ctypes.POINTER(BOOL)),
)
fc2QueryGigEImagingMode.generate_spec(_lib)

fc2GetGigEImagingMode = Function(
    'fc2GetGigEImagingMode', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('mode', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetGigEImagingMode.generate_spec(_lib)

fc2SetGigEImagingMode = Function(
    'fc2SetGigEImagingMode', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('mode', ctypes.c_uint),
)
fc2SetGigEImagingMode.generate_spec(_lib)

fc2GetGigEImageSettingsInfo = Function(
    'fc2GetGigEImageSettingsInfo', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pInfo', ctypes.POINTER(fc2GigEImageSettingsInfo)),
)
fc2GetGigEImageSettingsInfo.generate_spec(_lib)

fc2GetGigEImageSettings = Function(
    'fc2GetGigEImageSettings', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pImageSettings', ctypes.POINTER(fc2GigEImageSettings)),
)
fc2GetGigEImageSettings.generate_spec(_lib)

fc2SetGigEImageSettings = Function(
    'fc2SetGigEImageSettings', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pImageSettings', ctypes.POINTER(fc2GigEImageSettings)),
)
fc2SetGigEImageSettings.generate_spec(_lib)

fc2GetGigEImageBinningSettings = Function(
    'fc2GetGigEImageBinningSettings', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('horzBinnningValue', ctypes.POINTER(ctypes.c_uint)),
    ('vertBinnningValue', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetGigEImageBinningSettings.generate_spec(_lib)

fc2SetGigEImageBinningSettings = Function(
    'fc2SetGigEImageBinningSettings', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('horzBinnningValue', ctypes.c_uint),
    ('vertBinnningValue', ctypes.c_uint),
)
fc2SetGigEImageBinningSettings.generate_spec(_lib)

fc2GetNumStreamChannels = Function(
    'fc2GetNumStreamChannels', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('numChannels', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetNumStreamChannels.generate_spec(_lib)

fc2GetGigEStreamChannelInfo = Function(
    'fc2GetGigEStreamChannelInfo', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('channel', ctypes.c_uint),
    ('pChannel', ctypes.POINTER(fc2GigEStreamChannel)),
)
fc2GetGigEStreamChannelInfo.generate_spec(_lib)

fc2SetGigEStreamChannelInfo = Function(
    'fc2SetGigEStreamChannelInfo', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('channel', ctypes.c_uint),
    ('pChannel', ctypes.POINTER(fc2GigEStreamChannel)),
)
fc2SetGigEStreamChannelInfo.generate_spec(_lib)

fc2GetGigEConfig = Function(
    'fc2GetGigEConfig', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pConfig', ctypes.POINTER(fc2GigEConfig)),
)
fc2GetGigEConfig.generate_spec(_lib)

fc2SetGigEConfig = Function(
    'fc2SetGigEConfig', ctypes.c_uint,
    ('context', ctypes.c_void_p),
    ('pConfig', ctypes.POINTER(fc2GigEConfig)),
)
fc2SetGigEConfig.generate_spec(_lib)

fc2SetDefaultColorProcessing = Function(
    'fc2SetDefaultColorProcessing', ctypes.c_uint,
    ('defaultMethod', ctypes.c_uint),
)
fc2SetDefaultColorProcessing.generate_spec(_lib)

fc2GetDefaultColorProcessing = Function(
    'fc2GetDefaultColorProcessing', ctypes.c_uint,
    ('pDefaultMethod', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetDefaultColorProcessing.generate_spec(_lib)

fc2SetDefaultOutputFormat = Function(
    'fc2SetDefaultOutputFormat', ctypes.c_uint,
    ('format', ctypes.c_uint),
)
fc2SetDefaultOutputFormat.generate_spec(_lib)

fc2GetDefaultOutputFormat = Function(
    'fc2GetDefaultOutputFormat', ctypes.c_uint,
    ('pFormat', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetDefaultOutputFormat.generate_spec(_lib)

fc2DetermineBitsPerPixel = Function(
    'fc2DetermineBitsPerPixel', ctypes.c_uint,
    ('format', ctypes.c_uint),
    ('pBitsPerPixel', ctypes.POINTER(ctypes.c_uint)),
)
fc2DetermineBitsPerPixel.generate_spec(_lib)

fc2CreateImage = Function(
    'fc2CreateImage', ctypes.c_uint,
    ('pImage', ctypes.POINTER(fc2Image)),
)
fc2CreateImage.generate_spec(_lib)

fc2DestroyImage = Function(
    'fc2DestroyImage', ctypes.c_uint,
    ('image', ctypes.POINTER(fc2Image)),
)
fc2DestroyImage.generate_spec(_lib)

fc2SetImageDimensions = Function(
    'fc2SetImageDimensions', ctypes.c_uint,
    ('pImage', ctypes.POINTER(fc2Image)),
    ('rows', ctypes.c_uint),
    ('cols', ctypes.c_uint),
    ('stride', ctypes.c_uint),
    ('pixelFormat', ctypes.c_uint),
    ('bayerFormat', ctypes.c_uint),
)
fc2SetImageDimensions.generate_spec(_lib)

fc2GetImageDimensions = Function(
    'fc2GetImageDimensions', ctypes.c_uint,
    ('pImage', ctypes.POINTER(fc2Image)),
    ('pRows', ctypes.POINTER(ctypes.c_uint)),
    ('pCols', ctypes.POINTER(ctypes.c_uint)),
    ('pStride', ctypes.POINTER(ctypes.c_uint)),
    ('pPixelFormat', ctypes.POINTER(ctypes.c_uint)),
    ('pBayerFormat', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetImageDimensions.generate_spec(_lib)

fc2SetImageColorProcessing = Function(
    'fc2SetImageColorProcessing', ctypes.c_uint,
    ('pImage', ctypes.POINTER(fc2Image)),
    ('colorProc', ctypes.c_uint),
)
fc2SetImageColorProcessing.generate_spec(_lib)

fc2GetImageColorProcessing = Function(
    'fc2GetImageColorProcessing', ctypes.c_uint,
    ('pImage', ctypes.POINTER(fc2Image)),
    ('pColorProc', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetImageColorProcessing.generate_spec(_lib)

fc2SetImageData = Function(
    'fc2SetImageData', ctypes.c_uint,
    ('pImage', ctypes.POINTER(fc2Image)),
    ('pData', ctypes.POINTER(ctypes.c_ubyte)),
    ('dataSize', ctypes.c_uint),
)
fc2SetImageData.generate_spec(_lib)

fc2GetImageData = Function(
    'fc2GetImageData', ctypes.c_uint,
    ('pImage', ctypes.POINTER(fc2Image)),
    ('ppData', ctypes.POINTER(None)),
)
fc2GetImageData.generate_spec(_lib)

fc2GetImageMetadata = Function(
    'fc2GetImageMetadata', ctypes.c_uint,
    ('pImage', ctypes.POINTER(fc2Image)),
    ('pImageMetaData', ctypes.POINTER(fc2ImageMetadata)),
)
fc2GetImageMetadata.generate_spec(_lib)

fc2GetImageTimeStamp = Function(
    'fc2GetImageTimeStamp', fc2TimeStamp,
    ('pImage', ctypes.POINTER(fc2Image)),
)
fc2GetImageTimeStamp.generate_spec(_lib)

fc2SaveImage = Function(
    'fc2SaveImage', ctypes.c_uint,
    ('pImage', ctypes.POINTER(fc2Image)),
    ('pFilename', ctypes.c_char_p),
    ('format', ctypes.c_uint),
)
fc2SaveImage.generate_spec(_lib)

fc2SaveImageWithOption = Function(
    'fc2SaveImageWithOption', ctypes.c_uint,
    ('pImage', ctypes.POINTER(fc2Image)),
    ('pFilename', ctypes.c_char_p),
    ('format', ctypes.c_uint),
    ('pOption', ctypes.c_void_p),
)
fc2SaveImageWithOption.generate_spec(_lib)

fc2ConvertImage = Function(
    'fc2ConvertImage', ctypes.c_uint,
    ('pImageIn', ctypes.POINTER(fc2Image)),
    ('pImageOut', ctypes.POINTER(fc2Image)),
)
fc2ConvertImage.generate_spec(_lib)

fc2ConvertImageTo = Function(
    'fc2ConvertImageTo', ctypes.c_uint,
    ('format', ctypes.c_uint),
    ('pImageIn', ctypes.POINTER(fc2Image)),
    ('pImageOut', ctypes.POINTER(fc2Image)),
)
fc2ConvertImageTo.generate_spec(_lib)

fc2CalculateImageStatistics = Function(
    'fc2CalculateImageStatistics', ctypes.c_uint,
    ('pImage', ctypes.POINTER(fc2Image)),
    ('pImageStatisticsContext', ctypes.POINTER(fc2Context)),
)
fc2CalculateImageStatistics.generate_spec(_lib)

fc2CreateImageStatistics = Function(
    'fc2CreateImageStatistics', ctypes.c_uint,
    ('pImageStatisticsContext', ctypes.POINTER(fc2Context)),
)
fc2CreateImageStatistics.generate_spec(_lib)

fc2DestroyImageStatistics = Function(
    'fc2DestroyImageStatistics', ctypes.c_uint,
    ('imageStatisticsContext', ctypes.c_void_p),
)
fc2DestroyImageStatistics.generate_spec(_lib)

fc2ImageStatisticsEnableAll = Function(
    'fc2ImageStatisticsEnableAll', ctypes.c_uint,
    ('imageStatisticsContext', ctypes.c_void_p),
)
fc2ImageStatisticsEnableAll.generate_spec(_lib)

fc2ImageStatisticsDisableAll = Function(
    'fc2ImageStatisticsDisableAll', ctypes.c_uint,
    ('imageStatisticsContext', ctypes.c_void_p),
)
fc2ImageStatisticsDisableAll.generate_spec(_lib)

fc2ImageStatisticsEnableGreyOnly = Function(
    'fc2ImageStatisticsEnableGreyOnly', ctypes.c_uint,
    ('imageStatisticsContext', ctypes.c_void_p),
)
fc2ImageStatisticsEnableGreyOnly.generate_spec(_lib)

fc2ImageStatisticsEnableRGBOnly = Function(
    'fc2ImageStatisticsEnableRGBOnly', ctypes.c_uint,
    ('imageStatisticsContext', ctypes.c_void_p),
)
fc2ImageStatisticsEnableRGBOnly.generate_spec(_lib)

fc2ImageStatisticsEnableHSLOnly = Function(
    'fc2ImageStatisticsEnableHSLOnly', ctypes.c_uint,
    ('imageStatisticsContext', ctypes.c_void_p),
)
fc2ImageStatisticsEnableHSLOnly.generate_spec(_lib)

fc2GetChannelStatus = Function(
    'fc2GetChannelStatus', ctypes.c_uint,
    ('imageStatisticsContext', ctypes.c_void_p),
    ('channel', ctypes.c_uint),
    ('pEnabled', ctypes.POINTER(BOOL)),
)
fc2GetChannelStatus.generate_spec(_lib)

fc2SetChannelStatus = Function(
    'fc2SetChannelStatus', ctypes.c_uint,
    ('imageStatisticsContext', ctypes.c_void_p),
    ('channel', ctypes.c_uint),
    ('enabled', ctypes.c_int),
)
fc2SetChannelStatus.generate_spec(_lib)

fc2GetChannelRange = Function(
    'fc2GetChannelRange', ctypes.c_uint,
    ('imageStatisticsContext', ctypes.c_void_p),
    ('channel', ctypes.c_uint),
    ('pMin', ctypes.POINTER(ctypes.c_uint)),
    ('pMax', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetChannelRange.generate_spec(_lib)

fc2GetChannelPixelValueRange = Function(
    'fc2GetChannelPixelValueRange', ctypes.c_uint,
    ('imageStatisticsContext', ctypes.c_void_p),
    ('channel', ctypes.c_uint),
    ('pPixelValueMin', ctypes.POINTER(ctypes.c_uint)),
    ('pPixelValueMax', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetChannelPixelValueRange.generate_spec(_lib)

fc2GetChannelNumPixelValues = Function(
    'fc2GetChannelNumPixelValues', ctypes.c_uint,
    ('imageStatisticsContext', ctypes.c_void_p),
    ('channel', ctypes.c_uint),
    ('pNumPixelValues', ctypes.POINTER(ctypes.c_uint)),
)
fc2GetChannelNumPixelValues.generate_spec(_lib)

fc2GetChannelMean = Function(
    'fc2GetChannelMean', ctypes.c_uint,
    ('imageStatisticsContext', ctypes.c_void_p),
    ('channel', ctypes.c_uint),
    ('pPixelValueMean', ctypes.POINTER(ctypes.c_float)),
)
fc2GetChannelMean.generate_spec(_lib)

fc2GetChannelHistogram = Function(
    'fc2GetChannelHistogram', ctypes.c_uint,
    ('imageStatisticsContext', ctypes.c_void_p),
    ('channel', ctypes.c_uint),
    ('ppHistogram', ctypes.POINTER(None)),
)
fc2GetChannelHistogram.generate_spec(_lib)

fc2GetImageStatistics = Function(
    'fc2GetImageStatistics', ctypes.c_uint,
    ('imageStatisticsContext', ctypes.c_void_p),
    ('channel', ctypes.c_uint),
    ('pRangeMin', ctypes.POINTER(ctypes.c_uint)),
    ('pRangeMax', ctypes.POINTER(ctypes.c_uint)),
    ('pPixelValueMin', ctypes.POINTER(ctypes.c_uint)),
    ('pPixelValueMax', ctypes.POINTER(ctypes.c_uint)),
    ('pNumPixelValues', ctypes.POINTER(ctypes.c_uint)),
    ('pPixelValueMean', ctypes.POINTER(ctypes.c_float)),
    ('ppHistogram', ctypes.POINTER(None)),
)
fc2GetImageStatistics.generate_spec(_lib)

fc2CreateTopologyNode = Function(
    'fc2CreateTopologyNode', ctypes.c_uint,
    ('pTopologyNodeContext', ctypes.POINTER(fc2Context)),
)
fc2CreateTopologyNode.generate_spec(_lib)

fc2TopologyNodeGetGuid = Function(
    'fc2TopologyNodeGetGuid', ctypes.c_uint,
    ('TopologyNodeContext', ctypes.c_void_p),
    ('pGuid', ctypes.POINTER(fc2PGRGuid)),
)
fc2TopologyNodeGetGuid.generate_spec(_lib)

fc2TopologyNodeGetDeviceId = Function(
    'fc2TopologyNodeGetDeviceId', ctypes.c_uint,
    ('TopologyNodeContext', ctypes.c_void_p),
    ('pID', ctypes.POINTER(BOOL)),
)
fc2TopologyNodeGetDeviceId.generate_spec(_lib)

fc2TopologyNodeGetNodeType = Function(
    'fc2TopologyNodeGetNodeType', ctypes.c_uint,
    ('TopologyNodeContext', ctypes.c_void_p),
    ('pNodeType', ctypes.POINTER(ctypes.c_uint)),
)
fc2TopologyNodeGetNodeType.generate_spec(_lib)

fc2TopologyNodeGetInterfaceType = Function(
    'fc2TopologyNodeGetInterfaceType', ctypes.c_uint,
    ('TopologyNodeContext', ctypes.c_void_p),
    ('pInterfaceType', ctypes.POINTER(ctypes.c_uint)),
)
fc2TopologyNodeGetInterfaceType.generate_spec(_lib)

fc2TopologyNodeGetNumChildren = Function(
    'fc2TopologyNodeGetNumChildren', ctypes.c_uint,
    ('TopologyNodeContext', ctypes.c_void_p),
    ('pNumChildNodes', ctypes.POINTER(ctypes.c_uint)),
)
fc2TopologyNodeGetNumChildren.generate_spec(_lib)

fc2TopologyNodeGetChild = Function(
    'fc2TopologyNodeGetChild', ctypes.c_uint,
    ('TopologyNodeContext', ctypes.c_void_p),
    ('position', ctypes.c_uint),
    ('pChildTopologyNodeContext', ctypes.POINTER(fc2Context)),
)
fc2TopologyNodeGetChild.generate_spec(_lib)

fc2TopologyNodeAddChild = Function(
    'fc2TopologyNodeAddChild', ctypes.c_uint,
    ('TopologyNodeContext', ctypes.c_void_p),
    ('TopologyNodeChildContext', ctypes.c_void_p),
)
fc2TopologyNodeAddChild.generate_spec(_lib)

fc2TopologyNodeGetNumPorts = Function(
    'fc2TopologyNodeGetNumPorts', ctypes.c_uint,
    ('TopologyNodeContext', ctypes.c_void_p),
    ('pNumPorts', ctypes.POINTER(ctypes.c_uint)),
)
fc2TopologyNodeGetNumPorts.generate_spec(_lib)

fc2TopologyNodeGetPortType = Function(
    'fc2TopologyNodeGetPortType', ctypes.c_uint,
    ('TopologyNodeContext', ctypes.c_void_p),
    ('position', ctypes.c_uint),
    ('pPortType', ctypes.POINTER(ctypes.c_uint)),
)
fc2TopologyNodeGetPortType.generate_spec(_lib)

fc2TopologyNodeAddPortType = Function(
    'fc2TopologyNodeAddPortType', ctypes.c_uint,
    ('TopologyNodeContext', ctypes.c_void_p),
    ('portType', ctypes.c_uint),
)
fc2TopologyNodeAddPortType.generate_spec(_lib)

fc2TopologyNodeAssignGuidToNode = Function(
    'fc2TopologyNodeAssignGuidToNode', ctypes.c_int,
    ('TopologyNodeContext', ctypes.c_void_p),
    ('guid', fc2PGRGuid),
    ('deviceId', ctypes.c_int),
)
fc2TopologyNodeAssignGuidToNode.generate_spec(_lib)

fc2TopologyNodeAssignGuidToNodeEx = Function(
    'fc2TopologyNodeAssignGuidToNodeEx', ctypes.c_int,
    ('TopologyNodeContext', ctypes.c_void_p),
    ('guid', fc2PGRGuid),
    ('deviceId', ctypes.c_int),
    ('nodeType', ctypes.c_uint),
)
fc2TopologyNodeAssignGuidToNodeEx.generate_spec(_lib)

fc2DestroyTopologyNode = Function(
    'fc2DestroyTopologyNode', ctypes.c_uint,
    ('TopologyNodeContext', ctypes.c_void_p),
)
fc2DestroyTopologyNode.generate_spec(_lib)

fc2CheckDriver = Function(
    'fc2CheckDriver', ctypes.c_uint,
    ('pGuid', ctypes.POINTER(fc2PGRGuid)),
)
fc2CheckDriver.generate_spec(_lib)

fc2GetDriverDeviceName = Function(
    'fc2GetDriverDeviceName', ctypes.c_uint,
    ('pGuid', ctypes.POINTER(fc2PGRGuid)),
    ('pDeviceName', ctypes.c_char_p),
    ('deviceNameLength', ctypes.POINTER(ctypes.c_ulong)),
)
fc2GetDriverDeviceName.generate_spec(_lib)

fc2GetSystemInfo = Function(
    'fc2GetSystemInfo', ctypes.c_uint,
    ('pSystemInfo', ctypes.POINTER(fc2SystemInfo)),
)
fc2GetSystemInfo.generate_spec(_lib)

fc2GetLibraryVersion = Function(
    'fc2GetLibraryVersion', ctypes.c_uint,
    ('pVersion', ctypes.POINTER(fc2Version)),
)
fc2GetLibraryVersion.generate_spec(_lib)

fc2LaunchBrowser = Function(
    'fc2LaunchBrowser', ctypes.c_uint,
    ('pAddress', ctypes.c_char_p),
)
fc2LaunchBrowser.generate_spec(_lib)

fc2LaunchHelp = Function(
    'fc2LaunchHelp', ctypes.c_uint,
    ('pFileName', ctypes.c_char_p),
)
fc2LaunchHelp.generate_spec(_lib)

fc2LaunchCommand = Function(
    'fc2LaunchCommand', ctypes.c_uint,
    ('pCommand', ctypes.c_char_p),
)
fc2LaunchCommand.generate_spec(_lib)

fc2LaunchCommandAsync = Function(
    'fc2LaunchCommandAsync', ctypes.c_uint,
    ('pCommand', ctypes.c_char_p),
    ('pCallback', ctypes.POINTER(None)),
    ('pUserData', ctypes.c_void_p),
)
fc2LaunchCommandAsync.generate_spec(_lib)

fc2ErrorToDescription = Function(
    'fc2ErrorToDescription', ctypes.c_char_p,
    ('error', ctypes.c_uint),
)
fc2ErrorToDescription.generate_spec(_lib)

