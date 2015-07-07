#
# **************************************************************************
#
# simple_rep_single.py                           (c) Spectrum GmbH , 11/2009
#
# **************************************************************************
#
# Example for all SpcMDrv based (M2i) analog replay cards. 
# Shows a simple standard mode example using only the few necessary commands
#  
# Feel free to use this source for own projects and modify it in any kind
#
# **************************************************************************
#


from pyspcm import *

#
# **************************************************************************
# szTypeToName: doing name translation
# **************************************************************************
#

def szTypeToName (lCardType):
    sName = ''
    lVersion = (lCardType & TYP_VERSIONMASK)
    if (lCardType & TYP_SERIESMASK) == TYP_M2ISERIES:
        sName = 'M2i.%04x'%lVersion
    elif (lCardType & TYP_SERIESMASK) == TYP_M2IEXPSERIES:
        sName = 'M2i.%04x-Exp'%lVersion
    elif (lCardType & TYP_SERIESMASK) == TYP_M3ISERIES:
        sName = 'M3i.%04x'%lVersion
    elif (lCardType & TYP_SERIESMASK) == TYP_M3IEXPSERIES:
        sName = 'M3i.%04x-Exp'%lVersion
    else:
        sName = 'unknown type'
    return sName


#
# **************************************************************************
# bDoCalculation: calculates signal for output
# **************************************************************************


#
# **************************************************************************
# main 
# **************************************************************************
#

# open card
hCard = spcm_hOpen ("/dev/spcm0");
if hCard == None:
    print 'no card found...'
    exit ()


# read type, function and sn and check for D/A card
lCardType = int32 (0)
spcm_dwGetParam_i32 (hCard, SPC_PCITYP, byref (lCardType))
lSerialNumber = int32 (0)
spcm_dwGetParam_i32 (hCard, SPC_PCISERIALNO, byref (lSerialNumber))
lFncType = int32 (0)
spcm_dwGetParam_i32 (hCard, SPC_FNCTYPE, byref (lFncType))

sCardName = szTypeToName (lCardType.value)
if lFncType.value == SPCM_TYPE_AO:
    print 'Found: %s sn %05d'% (sCardName, lSerialNumber.value)
else:
    print 'Card: %s sn %05d not supported by example'%(sCardName, lSerialNumber.value)
    exit ()


# set samplerate to 1 MHz, no clock output
spcm_dwSetParam_i32 (hCard, SPC_SAMPLERATE, MEGA(1))
spcm_dwSetParam_i32 (hCard, SPC_CLOCKOUT,   0)

# setup the mode
qwChEnable = uint64 (1)
llMemSamples = int64 (KILO_B(64))
llLoops = int64 (0) # loop continuously
spcm_dwSetParam_i32 (hCard, SPC_CARDMODE,    SPC_REP_STD_CONTINUOUS)
spcm_dwSetParam_i64 (hCard, SPC_CHENABLE,    qwChEnable)
spcm_dwSetParam_i64 (hCard, SPC_MEMSIZE,     llMemSamples)
spcm_dwSetParam_i64 (hCard, SPC_LOOPS,       llLoops)

lSetChannels = int32 (0)
spcm_dwGetParam_i32 (hCard, SPC_CHCOUNT,     byref (lSetChannels))
lBytesPerSample = int32 (0)
spcm_dwGetParam_i32 (hCard, SPC_MIINST_BYTESPERSAMPLE,  byref (lBytesPerSample))

# setup the trigger mode
# (SW trigger, no output)
spcm_dwSetParam_i32 (hCard, SPC_TRIG_ORMASK,      SPC_TMASK_SOFTWARE)
spcm_dwSetParam_i32 (hCard, SPC_TRIG_ANDMASK,     0)
spcm_dwSetParam_i32 (hCard, SPC_TRIG_CH_ORMASK0,  0)
spcm_dwSetParam_i32 (hCard, SPC_TRIG_CH_ORMASK1,  0)
spcm_dwSetParam_i32 (hCard, SPC_TRIG_CH_ANDMASK0, 0)
spcm_dwSetParam_i32 (hCard, SPC_TRIG_CH_ANDMASK1, 0)
spcm_dwSetParam_i32 (hCard, SPC_TRIGGEROUT,       0)

lChannel = int32 (0)
spcm_dwSetParam_i32 (hCard, SPC_AMP0 + lChannel.value * (SPC_AMP1 - SPC_AMP0), int32 (1000))

# setup software buffer
qwBufferSize = uint64 (llMemSamples.value * lBytesPerSample.value * lSetChannels.value)
pvBuffer = create_string_buffer (qwBufferSize.value)

# calculate the data
pnBuffer = cast  (pvBuffer, ptr16)
for i in range (0, llMemSamples.value, 1):
   pnBuffer[i] = i

# we define the buffer for transfer and start the DMA transfer
print 'Starting the DMA transfer and waiting until data is in board memory'
spcm_dwDefTransfer_i64 (hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, int32 (0), pvBuffer, uint64 (0), qwBufferSize)
spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)
print '... data has been transferred to board memory'

# We'll start and wait until the card has finished or until a timeout occurs
spcm_dwSetParam_i32 (hCard, SPC_TIMEOUT, 10000)
print ''
print 'Starting the card and waiting for ready interrupt\n(continuous and single restart will have timeout)'
dwError = spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER | M2CMD_CARD_WAITREADY)
if dwError == ERR_TIMEOUT:
    spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_CARD_STOP)

spcm_vClose (hCard);

