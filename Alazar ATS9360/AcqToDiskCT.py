import ctypes as ct
from time import clock
from ALAZARERROR import alazarerror as alerr
from ALAZARCMD import alazarcmd as alcmd
from ALAZARAPI import alazarapi as alapi
from math import floor

alazardll=ct.windll.LoadLibrary("ATSApi.dll")


bh=alazardll.AlazarGetBoardBySystemID(1,1)

# Configure Board
SamplesPerSec = 100.e6;

preTriggerSamples=0
#postTriggerSamples=1024
#recordsPerBuffer=1000
samplesPerBuffer = 1024 * 1024
channelCount=1
#samplesPerRecord = preTriggerSamples + postTriggerSamples

print  alazardll.AlazarSetCaptureClock(
	bh,			# HANDLE -- board handle
	alcmd.INTERNAL_CLOCK,			# U32 -- clock source id
	alcmd.SAMPLE_RATE_100MSPS,	# U32 -- sample rate id
	alcmd.CLOCK_EDGE_RISING,		# U32 -- clock edge id
	0						# U32 -- clock decimation 
	)


maxSamplesPerChannel=ct.c_uint32()
bitsPerSample=ct.c_byte()
alazardll.AlazarGetChannelInfo(bh,ct.byref(maxSamplesPerChannel),ct.byref(bitsPerSample))	

#Globals variables
BUFFER_COUNT=4
MEM_COMMIT=0x00001000
PAGE_READWRITE=0x04

acquisitionLength_sec = 10. # time is defined in ms NOT in s

#Calculate the size of each DMA buffer in bytes
bytesPerSample = (bitsPerSample.value + 7) / 8
bytesPerBuffer = ct.c_uint32(bytesPerSample * samplesPerBuffer * channelCount)

#Calculate the number of buffers in the acquisition
samplesPerAcquisition = ct.c_uint32(int(SamplesPerSec * acquisitionLength_sec + 0.5))
buffersPerAcquisition = ct.c_uint32((samplesPerAcquisition.value + samplesPerBuffer- 1) / samplesPerBuffer)


	
BufferArray=[]

for bufferIndex in range(BUFFER_COUNT):
	BufferArray.append(ct.cast(ct.windll.kernel32.VirtualAlloc(None, bytesPerBuffer, MEM_COMMIT, PAGE_READWRITE),ct.POINTER(ct.c_uint16)))
	
	
# alazardll.AlazarSetRecordSize (bh, preTriggerSamples,postTriggerSamples)



alazardll.AlazarBeforeAsyncRead(
	bh,			# HANDLE -- board handle
	1,			# U32 -- enabled channel mask
	0,						# long -- offset from trigger in samples
	samplesPerBuffer,		# U32 -- samples per buffer
	1,						# U32 -- records per buffer (must be 1)
	buffersPerAcquisition,	# U32 -- records per acquisition 
	alapi.ADMA_EXTERNAL_STARTCAPTURE|alapi.ADMA_FIFO_ONLY_STREAMING|alapi.ADMA_TRIGGERED_STREAMING				# U32 -- AutoDMA flags
	)


# Add the buffers to a list of buffers available to be filled by the board
	
for bufferIndex in range(BUFFER_COUNT):
	pBuffer=ct.POINTER(ct.c_uint16)
	pBuffer=BufferArray[bufferIndex]
	alazardll.AlazarPostAsyncBuffer(bh, pBuffer, bytesPerBuffer)
	
#Arm the board to begin the acquisition 
	
alazardll.AlazarStartCapture(bh)

#Wait for each buffer to be filled, process the buffer, and re-post it to the board.

startTickCount = clock()
buffersCompleted = 0
bytesTransferred = 0

while (buffersCompleted < buffersPerAcquisition):
	timeout_ms = 5000
	bufferIndex = buffersCompleted % BUFFER_COUNT
	pBuffer=ct.POINTER(ct.c_uint16)
	pBuffer=BufferArray[bufferIndex]
	print alazardll.AlazarWaitAsyncBufferComplete(bh, pBuffer, timeout_ms)
	
	buffersCompleted +=1
	bytesTransferred += bytesPerBuffer.value
	
	# pRecord = pBuffer;
	# for channel in range(channelCount):
		# for record in range(recordsPerBuffer):
			# # Seek to next record in buffer
			# pRecord = ct.cast(ct.addressof(pRecord.contents)+samplesPerRecord,ct.POINTER(ct.c_uint16))
	
	#Add the buffer to the end of the list of available buffers.
	print alazardll.AlazarPostAsyncBuffer(bh, pBuffer, bytesPerBuffer)
	
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

alazardll.AlazarAbortAsyncRead(bh)


#Free Memory
MEM_RELEASE=0x8000
for bufferIndex in range(BUFFER_COUNT):
	if (BufferArray[bufferIndex] != None):
		ct.windll.kernel32.VirtualFree(BufferArray[bufferIndex], 0, MEM_RELEASE)