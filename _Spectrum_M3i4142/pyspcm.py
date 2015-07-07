import os
from ctypes import *

# load registers for easier access
from regs import *

# load registers for easier access
from spcerr import *

SPCM_DIR_PCTOCARD = 0
SPCM_DIR_CARDTOPC = 1

SPCM_BUF_DATA      = 1000 # main data buffer for acquired or generated samples
SPCM_BUF_ABA       = 2000 # buffer for ABA data, holds the A-DATA (slow samples)
SPCM_BUF_TIMESTAMP = 3000 # buffer for timestamps


# define pointer aliases
drv_handle = c_void_p

int8  = c_byte
int16 = c_short
int32 = c_long
int64 = c_longlong

ptr8  = POINTER (int8)
ptr16 = POINTER (int16)
ptr32 = POINTER (int32)
ptr64 = POINTER (int64)

uint8  = c_ubyte
uint16 = c_ushort
uint32 = c_ulong
uint64 = c_ulonglong

uptr8  = POINTER (uint8)
uptr16 = POINTER (uint16)
uptr32 = POINTER (uint32)
uptr64 = POINTER (uint64)

# Windows
if os.name == 'nt':
    print "Windows found"

    # Load DLL into memory.
    # use windll because all driver access functions use _stdcall calling convention under windows
    spcmDll = windll.LoadLibrary ("c:\\windows\\system32\\spcm_win32.dll")
    print spcmDll

    # load spcm_hOpen
    spcm_hOpen = getattr (spcmDll, "_spcm_hOpen@4")
    spcm_hOpen.argtype = [c_char_p]
    spcm_hOpen.restype = drv_handle 
    print spcm_hOpen

    # load spcm_vClose
    spcm_vClose = getattr (spcmDll, "_spcm_vClose@4")
    spcm_vClose.argtype = [drv_handle]
    spcm_vClose.restype = None
    print spcm_vClose

    # load spcm_dwGetErrorInfo
    spcm_dwGetErrorInfo_i32 = getattr (spcmDll, "_spcm_dwGetErrorInfo_i32@16")
    spcm_dwGetErrorInfo_i32.argtype = [drv_handle, ptr32, ptr32, c_char_p]
    spcm_dwGetErrorInfo_i32.restype = uint32
    print spcm_dwGetErrorInfo_i32

    # load spcm_dwGetParam_i32
    spcm_dwGetParam_i32 = getattr (spcmDll, "_spcm_dwGetParam_i32@12")
    spcm_dwGetParam_i32.argtype = [drv_handle, int32, ptr32]
    spcm_dwGetParam_i32.restype = uint32
    print spcm_dwGetParam_i32

    # load spcm_dwGetParam_i64
    spcm_dwGetParam_i64 = getattr (spcmDll, "_spcm_dwGetParam_i64@12")
    spcm_dwGetParam_i64.argtype = [drv_handle, int32, ptr64]
    spcm_dwGetParam_i64.restype = uint32
    print spcm_dwGetParam_i64

    # load spcm_dwSetParam_i32
    spcm_dwSetParam_i32 = getattr (spcmDll, "_spcm_dwSetParam_i32@12")
    spcm_dwSetParam_i32.argtype = [drv_handle, int32, int32]
    spcm_dwSetParam_i32.restype = uint32
    print spcm_dwSetParam_i32

    # load spcm_dwSetParam_i64
    spcm_dwSetParam_i64 = getattr (spcmDll, "_spcm_dwSetParam_i64@16")
    spcm_dwSetParam_i64.argtype = [drv_handle, int32, int64]
    spcm_dwSetParam_i64.restype = uint32
    print spcm_dwSetParam_i64

    # load spcm_dwSetParam_i64m
    spcm_dwSetParam_i64m = getattr (spcmDll, "_spcm_dwSetParam_i64m@16")
    spcm_dwSetParam_i64m.argtype = [drv_handle, int32, int32, int32]
    spcm_dwSetParam_i64m.restype = uint32
    print spcm_dwSetParam_i64m

    # load spcm_dwDefTransfer_i64
    spcm_dwDefTransfer_i64 = getattr (spcmDll, "_spcm_dwDefTransfer_i64@36")
    spcm_dwDefTransfer_i64.argtype = [drv_handle, uint32, uint32, uint32, c_void_p, uint64, uint64]
    spcm_dwDefTransfer_i64.restype = uint32
    print spcm_dwDefTransfer_i64

    spcm_dwInvalidateBuf = getattr (spcmDll, "_spcm_dwInvalidateBuf@8")
    spcm_dwInvalidateBuf.argtype = [drv_handle, uint32]
    spcm_dwInvalidateBuf.restype = uint32


elif os.name == 'posix':
    print "Linux found"

    # Load DLL into memory.
    # use cdll because all driver access functions use cdecl calling convention under linux 
    spcmDll = cdll.LoadLibrary ("libspcm_linux.so")
    print spcmDll

    # load spcm_hOpen
    spcm_hOpen = getattr (spcmDll, "spcm_hOpen")
    spcm_hOpen.argtype = [c_char_p]
    spcm_hOpen.restype = drv_handle 
    print spcm_hOpen

    # load spcm_vClose
    spcm_vClose = getattr (spcmDll, "spcm_vClose")
    spcm_vClose.argtype = [drv_handle]
    spcm_vClose.restype = None
    print spcm_vClose

    # load spcm_dwGetErrorInfo
    spcm_dwGetErrorInfo_i32 = getattr (spcmDll, "spcm_dwGetErrorInfo_i32")
    spcm_dwGetErrorInfo_i32.argtype = [drv_handle, ptr32, ptr32, c_char_p]
    spcm_dwGetErrorInfo_i32.restype = uint32
    print spcm_dwGetErrorInfo_i32

    # load spcm_dwGetParam_i32
    spcm_dwGetParam_i32 = getattr (spcmDll, "spcm_dwGetParam_i32")
    spcm_dwGetParam_i32.argtype = [drv_handle, int32, ptr32]
    spcm_dwGetParam_i32.restype = uint32
    print spcm_dwGetParam_i32

    # load spcm_dwGetParam_i64
    spcm_dwGetParam_i64 = getattr (spcmDll, "spcm_dwGetParam_i64")
    spcm_dwGetParam_i64.argtype = [drv_handle, int32, ptr64]
    spcm_dwGetParam_i64.restype = uint32
    print spcm_dwGetParam_i64

    # load spcm_dwSetParam_i32
    spcm_dwSetParam_i32 = getattr (spcmDll, "spcm_dwSetParam_i32")
    spcm_dwSetParam_i32.argtype = [drv_handle, int32, int32]
    spcm_dwSetParam_i32.restype = uint32
    print spcm_dwSetParam_i32

    # load spcm_dwSetParam_i64
    spcm_dwSetParam_i64 = getattr (spcmDll, "spcm_dwSetParam_i64")
    spcm_dwSetParam_i64.argtype = [drv_handle, int32, int64]
    spcm_dwSetParam_i64.restype = uint32
    print spcm_dwSetParam_i64

    # load spcm_dwSetParam_i64m
    spcm_dwSetParam_i64m = getattr (spcmDll, "spcm_dwSetParam_i64m")
    spcm_dwSetParam_i64m.argtype = [drv_handle, int32, int32, int32]
    spcm_dwSetParam_i64m.restype = uint32
    print spcm_dwSetParam_i64m

    # load spcm_dwDefTransfer_i64
    spcm_dwDefTransfer_i64 = getattr (spcmDll, "spcm_dwDefTransfer_i64")
    spcm_dwDefTransfer_i64.argtype = [drv_handle, uint32, uint32, uint32, c_void_p, uint32long, uint32long]
    spcm_dwDefTransfer_i64.restype = uint32
    print spcm_dwDefTransfer_i64

else:
    raise Exception ('Operating system not supported by pySpcm')
