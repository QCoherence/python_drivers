# AcqToDisk.py :
#
# This program demonstrates how to configure an ATS9360-FIFO to make a
# No-PreTrigger (NPT) AutoDMA acquisition.
#
# Adapted by Nico ROCH from AcqToDisk.cpp
#			September 2014

import ctypes as ct
from time import clock
from ALAZARERROR import alazarerror as alerr
from ALAZARCMD import alazarcmd as alcmd
from ALAZARAPI import alazarapi as alapi
import msvcrt # built-in module to allow detecting keyboard hit
import numpy as np
import matplotlib.pyplot as plt

alazardll=ct.windll.LoadLibrary("ATSApi.dll")

#Global variables
BUFFER_COUNT=4
MEM_COMMIT=0x00001000
PAGE_READWRITE=0x04
ApiSuccess=512

#TODO: Select a board

systemId = 1
boardId = 1


try:
	bh=alazardll.AlazarGetBoardBySystemID(systemId,boardId)
	print bh	
	if (bh==None):
		raise ValueError ("Error: Unable to open board system Id %d board Id %d\n" % (systemId, boardId))
except ValueError:
	print "Error: Unable to open board system Id %d board Id %d\n" % (systemId, boardId)

#####################
# Useful functions #
#####################

def ErrorToText(retCode):
	try:
		return ct.cast(alazardll.AlazarErrorToText(ct.c_int(retCode)),ct.c_char_p).value # AlazarErrorToText returns a ct.POINTER to ct.c_char, we need to cast it to a const char pointer to read the whole message.
	except:
		print "I can't convert this error code value"

###################
# Configure Board #
###################

#TODO: Specify the sample rate (see sample rate id below)

samplesPerSec = 1800.e6

#TODO: Select clock parameters as required to generate this sample rate.

#For example: if samplesPerSec is 100.e6 (100 MS/s), then:
# - select clock source INTERNAL_CLOCK and sample rate SAMPLE_RATE_100MSPS
# - select clock source FAST_EXTERNAL_CLOCK, sample rate SAMPLE_RATE_USER_DEF,
#   and connect a 100 MHz signalto the EXT CLK BNC connector.
try:
	retCode = alazardll.AlazarSetCaptureClock(
		bh,			# HANDLE -- board handle
		alcmd.EXTERNAL_CLOCK_10MHz_REF,			# U32 -- clock source id
		alcmd.SAMPLE_RATE_1800MSPS,	# U32 -- sample rate id
		alcmd.CLOCK_EDGE_RISING,		# U32 -- clock edge id
		ct.c_uint32(1)						# U32 -- clock decimation
		)
	if (retCode != ApiSuccess):
		raise ValueError("Error: AlazarSetCaptureClock failed -- %s\n", ErrorToText(retCode))
except ValueError:
	print "Error: AlazarSetCaptureClock failed -- %s\n", ErrorToText(retCode)

# TODO: Select CHA input parameters as required

try:
	retCode = alazardll.AlazarInputControl(
		bh,			# HANDLE -- board handle
		alcmd.CHANNEL_A,				# U8 -- input channel
		alcmd.DC_COUPLING,			# U32 -- input coupling id
		alcmd.INPUT_RANGE_PM_400_MV,	# U32 -- input range id
		alcmd.IMPEDANCE_50_OHM		# U32 -- input impedance id
		)
	if (retCode != ApiSuccess):
		raise ValueError("Error: AlazarInputControl failed -- %s\n", ErrorToText(retCode))
except ValueError:
	print "Error: AlazarInputControl failed -- %s\n", ErrorToText(retCode)

# TODO: Select CHB input parameters as required

try:
	retCode = alazardll.AlazarInputControl(
		bh,			# HANDLE -- board handle
		alcmd.CHANNEL_B,				# U8 -- channel identifier
		alcmd.DC_COUPLING,			#U32 -- input coupling id
		alcmd.INPUT_RANGE_PM_400_MV,	# U32 -- input range id
		alcmd.IMPEDANCE_50_OHM		# U32 -- input impedance id
		)
	if (retCode != ApiSuccess):
		raise ValueError("Error: AlazarInputControl failed -- %s\n", ErrorToText(retCode))
except ValueError:
	print "Error: AlazarInputControl failed -- %s\n", ErrorToText(retCode)

# TODO: Select trigger inputs and levels as required
try:
	retCode = alazardll.AlazarSetTriggerOperation(
			bh,			# HANDLE -- board handle
			alcmd.TRIG_ENGINE_OP_J,		# U32 -- trigger operation
			alcmd.TRIG_ENGINE_J,			# U32 -- trigger engine id
			alcmd.TRIG_EXTERNAL,			# U32 -- trigger source id
			alcmd.TRIGGER_SLOPE_POSITIVE,	# U32 -- trigger slope id
			150,					# U32 -- trigger level from 0 (-range) to 255 (+range)
			alcmd.TRIG_ENGINE_K,			# U32 -- trigger engine id
			alcmd.TRIG_DISABLE,			# U32 -- trigger source id for engine K
			alcmd.TRIGGER_SLOPE_POSITIVE,	# U32 -- trigger slope id
			128						# U32 -- trigger level from 0 (-range) to 255 (+range)
			)
	if (retCode != ApiSuccess):
		raise ValueError("Error: AlazarSetTriggerOperation failed -- %s\n", ErrorToText(retCode))
except ValueError:
	print "Error: AlazarSetTriggerOperation failed -- %s\n", ErrorToText(retCode)

#TODO: Select external trigger parameters as required
try:
	retCode = alazardll.AlazarSetExternalTrigger(
			bh,			# HANDLE -- board handle
			alcmd.DC_COUPLING,			#U32 -- external trigger coupling id
			alcmd.ETR_2V5				#U32 -- external trigger range id
			)
	if (retCode != ApiSuccess):
		raise ValueError("Error: AlazarSetExternalTrigger failed -- %s\n", ErrorToText(retCode))
except ValueError:
	print "Error: AlazarSetExternalTrigger failed -- %s\n", ErrorToText(retCode)

#TODO: Set trigger delay as required.

triggerDelay_sec = 0.;
triggerDelay_samples = int(triggerDelay_sec * samplesPerSec + 0.5)
try:
	retCode = alazardll.AlazarSetTriggerDelay(bh, triggerDelay_samples)
	if (retCode != ApiSuccess):
		raise ValueError("Error: AlazarSetTriggerDelay failed -- %s\n", ErrorToText(retCode))
except ValueError:
	print "Error: AlazarSetTriggerDelay failed -- %s\n", ErrorToText(retCode)

#TODO: Set trigger timeout as required.

	# NOTE:
	# The board will wait for a for this amount of time for a trigger event.
	# If a trigger event does not arrive, then the board will automatically
	# trigger. Set the trigger timeout value to 0 to force the board to wait
	# forever for a trigger event.
	#
	# IMPORTANT:
	# The trigger timeout value should be set to zero after appropriate
	# trigger parameters have been determined, otherwise the
	# board may trigger if the timeout interval expires before a
	# hardware trigger event arrives.

triggerTimeout_sec = 0.
triggerTimeout_clocks = int(triggerTimeout_sec / 10.e-6 + 0.5)
try:
	retCode = alazardll.AlazarSetTriggerTimeOut(
			bh,			# HANDLE -- board handle
			triggerTimeout_clocks	# U32 -- timeout_sec / 10.e-6 (0 means wait forever)
			)
	if (retCode != ApiSuccess):
		raise ValueError("Error: AlazarSetTriggerTimeOut failed -- %s\n", ErrorToText(retCode))
except ValueError:
	print "Error: AlazarSetTriggerTimeOut failed -- %s\n", ErrorToText(retCode)

	# // TODO: Configure AUX I/O connector as required

	# retCode =
		# AlazarConfigureAuxIO(
			# boardHandle,			// HANDLE -- board handle
			# AUX_OUT_TRIGGER,		// U32 -- mode
			# 0						// U32 -- parameter
			# );
	# if (retCode != ApiSuccess)
	# {
		# printf("Error: AlazarConfigureAuxIO failed -- %s\n", AlazarErrorToText(retCode));
		# return FALSE;
	# }



#####################
# Start Acquisition #
#####################


#There are no pre-trigger samples in NPT mode

preTriggerSamples = 0

#TODO: Select the number of post-trigger samples per record

postTriggerSamples = 1024

#TODO: Specify the number of records per DMA buffer

recordsPerBuffer = 10000

#TODO: Specify the acquisition time in seconds.

acquistionTime_sec = 2.

#TODO: Select which channels to capture (A, B, or both)

channelMask = alcmd.CHANNEL_A | alcmd.CHANNEL_B

#TODO: Select if you wish to save the sample data to a file

saveData = False

#Calculate the number of enabled channels from the channel mask

channelCount = 1

	# switch (channelMask)
	# {
	# case CHANNEL_A:
	# case CHANNEL_B:
		# channelCount = 1;
		# break;
	# case CHANNEL_A | CHANNEL_B:
		# channelCount = 2;
		# break;
	# default:
		# printf("Error: Invalid channel mask %08X\n", channelMask);
		# return FALSE;
	# }

#Get the sample size in bits, and the on-board memory size in samples per channel


samplesPerChannel=ct.c_uint32()
bitsPerSample=ct.c_byte()
try:
	retCode=alazardll.AlazarGetChannelInfo(bh,ct.byref(samplesPerChannel),ct.byref(bitsPerSample))
	if (retCode != ApiSuccess):
		raise ValueError("Error: AlazarGetChannelInfo failed -- %s\n" %ErrorToText(retCode))
except ValueError:
	print "Error: AlazarGetChannelInfo failed -- %s\n" %ErrorToText(retCode)

#Calculate the size of each DMA buffer in bytes
bytesPerSample = (bitsPerSample.value + 7) / 8
samplesPerRecord = preTriggerSamples + postTriggerSamples
bytesPerRecord = bytesPerSample * samplesPerRecord
bytesPerBuffer = bytesPerRecord * recordsPerBuffer * channelCount
#bytesPerBuffer = ct.c_uint32(bytesPerRecord * recordsPerBuffer * channelCount)



#Create a data file if required

if (saveData):
	try:
		filetowrite=open("fichier.txt", "w+")
	except:
		print "Error: Unable to create data file"


#Allocate memory for DMA buffers


BufferArray=[]
intPerBuffer=bytesPerBuffer/2
try:
	for bufferIndex in range(BUFFER_COUNT):
		pBuffer=ct.cast(ct.c_void_p(ct.windll.kernel32.VirtualAlloc(None, ct.c_uint32(bytesPerBuffer), MEM_COMMIT, PAGE_READWRITE)), ct.POINTER(ct.c_byte*bytesPerBuffer))
		BufferArray.append(pBuffer)
		if (BufferArray[bufferIndex] == None):
			raise ValueError("Error: Alloc %d bytes failed\n", bytesPerBuffer)
except ValueError:
	print "Error: Alloc %d bytes failed\n", bytesPerBuffer




#Configure the record size
try:
	retCode=alazardll.AlazarSetRecordSize (bh, preTriggerSamples,postTriggerSamples)
	if (retCode != ApiSuccess):
		raise ValueError("Error: AlazarSetRecordSize failed -- %s\n" % ErrorToText(retCode))
except ValueError:
	print "Error: AlazarSetRecordSize failed -- %s\n" % ErrorToText(retCode)

#Configure the board to make an NPT AutoDMA acquisition
recordsPerAcquisition = 0x7fffffff			# Acquire until aborted
admaFlags = alapi.ADMA_EXTERNAL_STARTCAPTURE|alapi.ADMA_NPT|alapi.ADMA_FIFO_ONLY_STREAMING	# Start acquisition when AlazarStartCapture is called # Acquire multiple records with no-pretrigger samples # The ATS9360-FIFO does not have on-board memory

try:
	retCode = 	alazardll.AlazarBeforeAsyncRead(
		bh,			# HANDLE -- board handle
		1,			# U32 -- enabled channel mask
		ct.c_long(-preTriggerSamples),		# long -- offset from trigger in samples
		samplesPerRecord,		# U32 -- samples per record
		recordsPerBuffer,		# U32 -- records per buffer
		recordsPerAcquisition,	# U32 -- records per acquisition
		admaFlags				# U32 -- AutoDMA flags
		)
	if (retCode != ApiSuccess):
		raise ValueError("Error: AlazarBeforeAsyncRead failed -- %s\n" %ErrorToText(retCode))
except ValueError:
	print "Error: AlazarBeforeAsyncRead failed -- %s\n" %ErrorToText(retCode)



#Add the buffers to a list of buffers available to be filled by the board
try:
	for bufferIndex in range(BUFFER_COUNT):
		#pBuffer=ct.POINTER(ct.c_uint16)
		pBuffer=BufferArray[bufferIndex]
		retCode=alazardll.AlazarPostAsyncBuffer(bh, pBuffer, bytesPerBuffer)
		if (retCode != ApiSuccess):
			raise ValueError("Error: AlazarPostAsyncBuffer %u failed -- %s\n" % (bufferIndex,ErrorToText(retCode)))
except ValueError:
	print "Error: AlazarPostAsyncBuffer %u failed -- %s\n" % (bufferIndex,ErrorToText(retCode))

#Arm the board to begin the acquisition

try:
	retCode = alazardll.AlazarStartCapture(bh)
	if (retCode != ApiSuccess):
		raise ValueError("Error: AlazarStartCapture failed -- %s\n" % ErrorToText(retCode))
except ValueError:
	print "Error: AlazarStartCapture failed -- %s\n" % ErrorToText(retCode)

#Wait for each buffer to be filled, process the buffer, and re-post it to the board.
startTickCount = clock()
stopTickCount = startTickCount + acquistionTime_sec
buffersCompleted = 0
bytesTransferred = 0

print "Capturing for %d seconds ... press any key to abort\n" % acquistionTime_sec


while True:
	#TODO: Set a buffer timeout that is longer than the time
	#required to capture all the records in one buffer.
	timeout_ms = 5000

	# Wait for the buffer at the head of the list of available buffers
	# to be filled by the board.
	bufferIndex = buffersCompleted % BUFFER_COUNT
	#pBuffer=ct.POINTER(ct.c_uint16)
	pBuffer=BufferArray[bufferIndex]
	try:
		if(pBuffer==None):
			raise ValueError("Error: Alloc %d bytes failed\n" %bytesPerBuffer)
	except ValueError:
		print("Error: Alloc %d bytes failed\n"% bytesPerBuffer)
		break

	try:
		retCode = alazardll.AlazarWaitAsyncBufferComplete(bh, pBuffer, timeout_ms)
		if (retCode != ApiSuccess):
			raise ValueError("Error: AlazarWaitAsyncBufferComplete failed -- %s\n" % ErrorToText(retCode))
	except ValueError:
		print "Error: AlazarWaitAsyncBufferComplete failed -- %s\n" % ErrorToText(retCode)
		break


	#The buffer is full and has been removed from the list
	#of buffers available for the board
	buffersCompleted +=1
	bytesTransferred += bytesPerBuffer

	# // TODO: Process sample data in this buffer.

	# // NOTE:
	# //
	# // While you are processing this buffer, the board is already
	# // filling the next available buffer(s).
	# //
	# // You MUST finish processing this buffer and post it back to the
	# // board before the board fills all of its available DMA buffers
	# // and on-board memory.
	# //
	# // Records are arranged in the buffer as follows:
	# // R0[AB], R1[AB], R2[AB] ... Rn[AB]
	# //
	# // Samples values are arranged contiguously in each record.
	# // A 12-bit sample code is stored in the most significant
	# // bits of each 16-bit sample value.
	# //
	# // Sample codes are unsigned by default. As a result:
	# // - a sample code of 0x000 represents a negative full scale input signal.
	# // - a sample code of 0x800 represents a ~0V signal.
	# // - a sample code of 0xFFF represents a positive full scale input signal.


	for channel in range(channelCount):

		# Mapping the memory to a numpy array
		data = np.uint16(np.ctypeslib.as_array(pBuffer.contents))


		# The 12-bits samples of the card are stored as 2 bytes (16-bits) in little-endian byte order in the buffer.
		# See for example p:60 of the ATS-SDK pdf.
		# To speed up data conversion, it's better to use numpy-native array manipulation and NOT for loop.

		datarenorm=(data[:bytesPerBuffer:2]+2**8*data[1:bytesPerBuffer:2])/2**4

		#data = np.hsplit(data,bytesPerBuffer)

	# Add the buffer to the end of the list of available buffers.
	try:
		retCode = alazardll.AlazarPostAsyncBuffer(bh, pBuffer, bytesPerBuffer)
		if (retCode != ApiSuccess):
			raise ValueError("Error: AlazarPostAsyncBuffer failed -- %s\n" % ErrorToText(retCode))
	except ValueError:
		print "Error: AlazarPostAsyncBuffer failed -- %s\n" % ErrorToText(retCode)
		break

	# #If the acquisition failed, exit the acquisition loop

	# if(success != True):
		# break

	#If a key was pressed, exit the acquisition loop
	if msvcrt.kbhit():
		print "Aborted...\n"
		break

	#If the acquistion period is over, abort the acquisition

	if (clock() > stopTickCount):
		print "Acquistion complete.\n"
		break

	#Display progress
	print "Completed %d buffers\r" % buffersCompleted

## Display results

transferTime_sec = (clock() - startTickCount)
print "Capture completed in %d sec\n" % transferTime_sec

recordsTransferred = recordsPerBuffer * buffersCompleted

if (transferTime_sec > 0.):
	buffersPerSec = buffersCompleted / transferTime_sec
	bytesPerSec = bytesTransferred / transferTime_sec
	recordsPerSec = recordsTransferred / transferTime_sec
else:
	buffersPerSec = 0.
	bytesPerSec = 0.
	recordsPerSec = 0.

print "Captured %d buffers (%d buffers per sec)\n" % (buffersCompleted , buffersPerSec)
print"Captured %d records (%d records per sec)\n" % (recordsTransferred  , recordsPerSec)
print"Transferred %d bytes (%d bytes per sec)\n" % (bytesTransferred , bytesPerSec)

#Abort the acquisition

try:
	retCode = alazardll.AlazarAbortAsyncRead(bh)
	if (retCode != ApiSuccess):
		raise ValueError("Error: AlazarAbortAsyncRead failed -- %s\n" %ErrorToText(retCode))
except ValueError:
	print "Error: AlazarAbortAsyncRead failed -- %s\n" %ErrorToText(retCode)



#Free Memory
MEM_RELEASE=0x8000
for bufferIndex in range(BUFFER_COUNT):
	if (BufferArray[bufferIndex] != None):
		ct.windll.kernel32.VirtualFree(BufferArray[bufferIndex], 0, MEM_RELEASE)

# # Close the data file
# if (saveData):
	# filetowrite.write(str(data))


# if (filetowrite.closed != True):
	# filetowrite.close()

# Do some plotting
nbRecordsToPlot=100
t_ns=[i/samplesPerSec*10**9 for i in range(samplesPerRecord)]  # array of time points in ns
for j in range(nbRecordsToPlot):
	plt.plot(t_ns,datarenorm[j*samplesPerRecord:(j+1)*samplesPerRecord])
plt.show()
