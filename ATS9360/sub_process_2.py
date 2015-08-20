from __future__ import division
import numpy as np
import os
import signal
import sys
import time
import atsapi as ats


# def set_clock(board, parameters):
#     '''Set the clock of the board.
#         The method uses all clock attribut to set the clock.
#         Different verification are performed to check the validity of the
#         different clock parameters.'''
#
#     # For sake of clarity we introduce variables use in the function
#     clock_source = parameters['clock_source']
#     clock_edge   = parameters['clock_edge']
#     # the samplerate must stays in MS/s in case of internal clock
#     samplerate   = parameters['samplerate']
#
#     allow_samplerates   = parameters['allow_samplerates']
#     allow_clock_edges   = parameters['allow_clock_edges']
#     allow_clock_sources = parameters['allow_clock_sources']
#
#     # If the board uses its internal clock, the samplerate must be a string
#     # allowed by the board, see allow_samplerates attributes.
#     # The decimation is then put by default to 0 which correspond to
#     # disable decimation.
#
#     # If the board uses an external clock, the samplerate must be a float
#     # or an int.
#     # The decimation is then 0, only decimation allowed in this mode of the
#     # clock.
#
#     if clock_source == 'internal':
#
#         decimation = 0
#         samplerate = allow_samplerates[samplerate]
#     elif clock_source == 'external':
#
#         decimation = 1
#         samplerate = samplerate*1e6 # To get it in S/s
#     else:
#
#         raise ValueError('The clock source must be "internal" or\
#                          "external"')
#
#     board.setCaptureClock(allow_clock_sources[clock_source],
#                           samplerate,
#                           allow_clock_edges[clock_edge],
#                           decimation)
#
#
#
# def set_input_control(board):
#     """
#         Set the two input (channel A and B) of the board.
#         The input range is fixed two +-400mV, the impedance to 50 ohm
#         (cannot be changed) and, the coupling of the inputs to DC.
#     """
#
#
#     board.inputControl(ats.CHANNEL_A,
#                        ats.DC_COUPLING,
#                        ats.INPUT_RANGE_PM_400_MV,
#                        ats.IMPEDANCE_50_OHM)
#
#
#     board.inputControl(ats.CHANNEL_B,
#                        ats.DC_COUPLING,
#                        ats.INPUT_RANGE_PM_400_MV,
#                        ats.IMPEDANCE_50_OHM)
#
#
#
# def set_trigger(board, parameters):
#     '''
#         Set the trigger.
#         Here the trigger is supposed to be external.
#     '''
#
#
#     trigger_slope = parameters['trigger_slope']
#     trigger_range = parameters['trigger_range']
#     trigger_level = parameters['trigger_level']
#     trigger_delay = parameters['trigger_delay']*1e9 # To get it in second
#
#     samplerate    = parameters['samplerate']*1e6 # To get it in S/s
#
#     allow_trigger_slopes = parameters['allow_trigger_slopes']
#     allow_trigger_ranges = parameters['allow_trigger_ranges']
#
#
#     # The digitizer board has a flexible triggering system with two separate
#     # trigger engines that can be used independently, or combined together to
#     # generate trigger events. Since we use an external trigger, we only use
#     # one trigger engine, the J one.
#     # The three first parameters set the J engine and the choice of an
#     # external trigger.
#     # Since we don't use the second trigger engine, the four last parameters
#     # are useless.
#
#     # We calculate the trigger level for the board
#     trigger_level_code = int(round(128.\
#                                    + 127.*trigger_level/trigger_range))
#
#     board.setTriggerOperation(ats.TRIG_ENGINE_OP_J,
#                               ats.TRIG_ENGINE_J,
#                               ats.TRIG_EXTERNAL,
#                               allow_trigger_slopes[trigger_slope],
#                               trigger_level_code,
#                               ats.TRIG_ENGINE_K,
#                               ats.TRIG_DISABLE,
#                               ats.TRIGGER_SLOPE_POSITIVE,
#                               128)
#
#
#     # Set the external trigger.
#     # This has to be done after the setTriggerOperation !
#     # The coupling is DC (no choice) and the input range is given by the user.
#     board.setExternalTrigger(ats.DC_COUPLING,
#                              allow_trigger_ranges[trigger_range])
#
#     # The the trigger delay
#     # We calculate the trigger delay for the board
#     trigger_delay_code = int(trigger_delay * samplerate + 0.5)
#     board.setTriggerDelay(trigger_delay_code)
#
#     # The board has an option to fake a software trigger event in case of no
#     # hardware trigger is detected.
#     # We don't need this option and so disable it.
#     board.setTriggerTimeOut(0)
#
#     # We don't use the AUX I/O connector so don't offer the choice to tune it.
#     board.configureAuxIO(ats.AUX_OUT_TRIGGER,
#                          0)
#
#
#
# def prepare_acquisition(board, parameters):
#
#     samplesPerSec         = parameters['samplerate']*1e6
#
#     # No pre-trigger samples in NPT mode
#     preTriggerSamples     = 0
#     postTriggerSamples    = parameters['acquired_samples']
#
#     # Select the number of records per DMA buffer.
#     recordsPerBuffer      = parameters['records_per_buffer']
#
#     # Select the number of buffers per acquisition.
#     buffersPerAcquisition = parameters['buffers_per_acquisition']
#
#     # We assume two active channels
#     channels              = ats.CHANNEL_A | ats.CHANNEL_B
#     channelCount          = 2
#
#
#     # Compute the number of bytes per record and per buffer
#     memorySize_samples, bitsPerSample = board.getChannelInfo()
#     bytesPerSample   = (bitsPerSample.value + 7) // 8
#     samplesPerRecord = preTriggerSamples + postTriggerSamples
#     bytesPerRecord   = bytesPerSample * samplesPerRecord
#     bytesPerBuffer   = bytesPerRecord * recordsPerBuffer * channelCount
#
#     # Select number of DMA buffers to allocate
#     bufferCount = parameters['nb_buffer_allocated']
#
#     # Create and set the buffers
#     buffers = []
#     for i in range(bufferCount):
#         buffers.append(ats.DMABuffer(bytesPerSample, bytesPerBuffer))
#
#     board.setRecordSize(preTriggerSamples, postTriggerSamples)
#
#     # Prepate the board to work in the asynchroneous mode of acquisition
#     recordsPerAcquisition = recordsPerBuffer * buffersPerAcquisition
#
#     board.beforeAsyncRead(channels,
#                           -preTriggerSamples,
#                           samplesPerRecord,
#                           recordsPerBuffer,
#                           recordsPerAcquisition,
#                           ats.ADMA_EXTERNAL_STARTCAPTURE \
#                           | ats.ADMA_NPT | ats.ADMA_FIFO_ONLY_STREAMING)
#
#
#     # Put the buffers previously created in the list of available buffers
#     for buff in buffers:
#         board.postAsyncBuffer(buff.addr, buff.size_bytes)
#
#     return buffers
#
#
#
# def data_acquisition(board, queue_data, parameters, buffers):
#
#     # Get buffers
#     buffers               = buffers
#     buffersPerAcquisition = parameters['buffers_per_acquisition']
#     recordsPerBuffer      = parameters['records_per_buffer']
#     preTriggerSamples     = 0
#     postTriggerSamples    = parameters['acquired_samples']
#     samplesPerRecord      = preTriggerSamples + postTriggerSamples
#
#     start = time.clock() # Keep track of when acquisition started
#     board.startCapture() # Start the acquisition
#     print("Capturing %d buffers. Press any key to abort" % buffersPerAcquisition)
#     buffersCompleted = 0
#     bytesTransferred = 0
#
#     while buffersCompleted < buffersPerAcquisition:
#
#         buff = buffers[buffersCompleted % len(buffers)]
#         board.waitAsyncBufferComplete(buff.addr, timeout_ms=5000)
#
#
#         buffersCompleted += 1
#         bytesTransferred += buff.size_bytes
#
#         queue_data.put(buff.buffer)
#
#         # Update progress bar
#         #waitBar.setProgress(buffersCompleted / buffersPerAcquisition)
#
#         # Add the buffer to the end of the list of available buffers.
#         board.postAsyncBuffer(buff.addr, buff.size_bytes)
#
#     # Compute the total transfer time, and display performance information.
#     transferTime_sec = time.clock() - start
#     print("Capture completed in %f sec" % transferTime_sec)
#     buffersPerSec      = 0
#     bytesPerSec        = 0
#     recordsPerSec      = 0
#     samplesTransferred = samplesPerRecord*recordsPerBuffer*buffersPerAcquisition
#     if transferTime_sec > 0:
#         buffersPerSec = buffersCompleted / transferTime_sec
#         bytesPerSec   = bytesTransferred / transferTime_sec
#         recordsPerSec = recordsPerBuffer * buffersCompleted / transferTime_sec
#         samplePerSec  = samplesTransferred / transferTime_sec
#
#     print("Captured %d buffers (%f buffers per sec)" % (buffersCompleted, buffersPerSec))
#     print("Captured %d records (%f records per sec)" % (recordsPerBuffer * buffersCompleted, recordsPerSec))
#     print("Transferred %d bytes (%f Gbytes per sec)" % (bytesTransferred, bytesPerSec/1024**3.))
#     print("Transferred %d samples (%f GS per sec)" % (samplesTransferred, samplePerSec/1e9))


def get_data(queue_data, parameters):

    # We instance a board object
    # All the parameters of the measurement will be set on this instance
    board = ats.Board(systemId = 1, boardId = 1)
    samplesPerSec = 1800.e6
    # board.setCaptureClock(ats.INTERNAL_CLOCK,
    #                       ats.SAMPLE_RATE_1800MSPS,
    #                       ats.CLOCK_EDGE_RISING,
    #                       0)

    board.setCaptureClock(ats.EXTERNAL_CLOCK_10MHz_REF,
                          samplesPerSec,
                          ats.CLOCK_EDGE_RISING,
                          1)

    # TODO: Select channel A input parameters as required.
    board.inputControl(ats.CHANNEL_A,
                       ats.DC_COUPLING,
                       ats.INPUT_RANGE_PM_400_MV,
                       ats.IMPEDANCE_50_OHM)


    # TODO: Select channel B input parameters as required.
    board.inputControl(ats.CHANNEL_B,
                       ats.DC_COUPLING,
                       ats.INPUT_RANGE_PM_400_MV,
                       ats.IMPEDANCE_50_OHM)

    # TODO: Select trigger inputs and levels as required.
    board.setTriggerOperation(ats.TRIG_ENGINE_OP_J,
                              ats.TRIG_ENGINE_J,
                              ats.TRIG_EXTERNAL,
                              ats.TRIGGER_SLOPE_POSITIVE,
                              150,
                              ats.TRIG_ENGINE_K,
                              ats.TRIG_DISABLE,
                              ats.TRIGGER_SLOPE_POSITIVE,
                              128)

    # TODO: Select external trigger parameters as required.
    board.setExternalTrigger(ats.DC_COUPLING,
                             ats.ETR_5V)
                            #  ats.ETR_TTL)

    # TODO: Set trigger delay as required.
    triggerDelay_sec = 0
    triggerDelay_samples = int(triggerDelay_sec * samplesPerSec + 0.5)
    board.setTriggerDelay(triggerDelay_samples)

    # TODO: Set trigger timeout as required.
    #
    # NOTE: The board will wait for a for this amount of time for a
    # trigger event.  If a trigger event does not arrive, then the
    # board will automatically trigger. Set the trigger timeout value
    # to 0 to force the board to wait forever for a trigger event.
    #
    # IMPORTANT: The trigger timeout value should be set to zero after
    # appropriate trigger parameters have been determined, otherwise
    # the board may trigger if the timeout interval expires before a
    # hardware trigger event arrives.
    triggerTimeout_sec = 0
    triggerTimeout_clocks = int(triggerTimeout_sec / 10e-6 + 0.5)
    board.setTriggerTimeOut(triggerTimeout_clocks)

    # Configure AUX I/O connector as required
    board.configureAuxIO(ats.AUX_OUT_TRIGGER,
                         0)
    # No pre-trigger samples in NPT mode
    preTriggerSamples = 0

    # TODO: Select the number of sam<ples per record.
    postTriggerSamples = 10240
    postTriggerSamples = 128*80

    # TODO: Select the number of records per DMA buffer.
    recordsPerBuffer = 20



    # TODO: Select the active channels.
    channels = ats.CHANNEL_A | ats.CHANNEL_B
    channelCount = 0
    for c in ats.channels:
        channelCount += (c & channels == c)

    # TODO: Should data be saved to file?
    saveData = False
    dataFile = None
    if saveData:
        dataFile = open(os.path.join(os.path.dirname(__file__), "data.bin"), 'w')

    # Compute the number of bytes per record and per buffer
    memorySize_samples, bitsPerSample = board.getChannelInfo()
    # print memorySize_samples.value, bitsPerSample.value
    bytesPerSample = (bitsPerSample.value + 7) // 8
    samplesPerRecord = preTriggerSamples + postTriggerSamples
    bytesPerRecord = bytesPerSample * samplesPerRecord
    bytesPerBuffer = bytesPerRecord * recordsPerBuffer * channelCount

    # print channelCount

    # TODO: Select number of DMA buffers to allocate
    bufferCount = 10
    # TODO: Select the number of buffers per acquisition.
    # buffersPerAcquisition = bufferCount
    buffersPerAcquisition = 10
    # Allocate DMA buffers
    buffers = []
    for i in range(bufferCount):
        buffers.append(ats.DMABuffer(bytesPerSample, bytesPerBuffer))

    # Set the record size
    board.setRecordSize(preTriggerSamples, postTriggerSamples)

    recordsPerAcquisition = recordsPerBuffer * buffersPerAcquisition

    # Configure the board to make an NPT AutoDMA acquisition
    board.beforeAsyncRead(channels,
                          -preTriggerSamples,
                          samplesPerRecord,
                          recordsPerBuffer,
                          recordsPerAcquisition,
                          ats.ADMA_EXTERNAL_STARTCAPTURE | ats.ADMA_NPT | ats.ADMA_FIFO_ONLY_STREAMING)



    # Post DMA buffers to board
    for buffer in buffers:
        board.postAsyncBuffer(buffer.addr, buffer.size_bytes)

    start = time.clock() # Keep track of when acquisition started
    board.startCapture() # Start the acquisition
    print("Capturing %d buffers. Press any key to abort" % buffersPerAcquisition)
    buffersCompleted = 0
    bytesTransferred = 0
    while buffersCompleted < buffersPerAcquisition:
    # for buffer in buffers:
        # Wait for the buffer at the head of the list of available
        # buffers to be filled by the board.
        buffer = buffers[buffersCompleted % len(buffers)]

        board.waitAsyncBufferComplete(buffer.addr, timeout_ms=5000)
        buffersCompleted += 1
        bytesTransferred += buffer.size_bytes

        queue_data.put(buffer.buffer)

        # TODO: Process sample data in this buffer. Data is available
        # as a NumPy array at buffer.buffer

        # NOTE:
        #
        # While you are processing this buffer, the board is already
        # filling the next available buffer(s).
        #
        # You MUST finish processing this buffer and post it back to the
        # board before the board fills all of its available DMA buffers
        # and on-board memory.
        #
        # Samples are arranged in the buffer as follows: S0A, S0B, ..., S1A, S1B, ...
        # with SXY the sample number X of channel Y.
        #
        # A 12-bit sample code is stored in the most significant bits of
        # in each 16-bit sample value.
        #
        # Sample codes are unsigned by default. As a result:
        # - a sample code of 0x0000 represents a negative full scale input signal.
        # - a sample code of 0x8000 represents a ~0V signal.
        # - a sample code of 0xFFFF represents a positive full scale input signal.
        # Optionaly save data to file
        if dataFile:
            buffer.buffer.tofile(dataFile)

        # Update progress bar
        #waitBar.setProgress(buffersCompleted / buffersPerAcquisition)

        # Add the buffer to the end of the list of available buffers.
        board.postAsyncBuffer(buffer.addr, buffer.size_bytes)
    # Compute the total transfer time, and display performance information.
    transferTime_sec = time.clock() - start
    print("Capture completed in %f sec" % transferTime_sec)
    buffersPerSec = 0
    bytesPerSec = 0
    recordsPerSec = 0
    samplesTransferred = samplesPerRecord*recordsPerBuffer*buffersPerAcquisition
    if transferTime_sec > 0:
        buffersPerSec = buffersCompleted / transferTime_sec
        bytesPerSec = bytesTransferred / transferTime_sec
        recordsPerSec = recordsPerBuffer * buffersCompleted / transferTime_sec
        samplePerSec  = samplesTransferred / transferTime_sec
    print("Captured %d buffers (%f buffers per sec)" % (buffersCompleted, buffersPerSec))
    print("Captured %d records (%f records per sec)" % (recordsPerBuffer * buffersCompleted, recordsPerSec))
    print("Transferred %d bytes (%f Gbytes per sec)" % (bytesTransferred, bytesPerSec/1024**3.))
    print("Transferred %d samples (%f GS per sec)" % (samplesTransferred, samplePerSec/1e9))

    # Abort transfer.
    board.abortAsyncRead()
