import ctypes as ct

alazardll=ct.windll.LoadLibrary("ATSApi.dll")


bh=alazardll.AlazarGetBoardBySystemID(1,1)


samplesPerChannel=ct.c_uint32()
bitsPerSample=ct.c_byte()
alazardll.AlazarGetChannelInfo(bh,ct.byref(samplesPerChannel),ct.byref(bitsPerSample))

latestCalDate=ct.c_uint32()
alazardll.AlazarQueryCapability(bh, 0x1000002E, 0, ct.byref(latestCalDate))