# This Python file uses the following encoding: utf-8
# ATS9360_NPT.py driver for The aquisition board Alzar ATS9360
# Etienne Dumur <etienne.dumur@neel.cnrs.fr> 2015
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from __future__ import division
import ctypes
import numpy as np
import time
import atsapi as ats

windowType = ats.DSP_WINDOW_HAMMING


class DataAcquisition(object):
    """
        Class handling the acquisition of data from the ATS board.
        Basically, user should only use the get_data method.
    """



    def set_clock(self, board, parameters):
        '''Set the clock of the board.
            The method uses all clock attribut to set the clock.
            Different verification are performed to check the validity of the
            different clock parameters.'''

        # For sake of clarity we introduce variables use in the function
        clock_source = parameters['clock_source']
        clock_edge   = parameters['clock_edge']
        # the samplerate must stays in MS/s in case of internal clock
        samplerate   = parameters['samplerate']

        allow_samplerates   = parameters['allow_samplerates']
        allow_clock_edges   = parameters['allow_clock_edges']
        allow_clock_sources = parameters['allow_clock_sources']

        # If the board uses its internal clock, the samplerate must be a string
        # allowed by the board, see allow_samplerates attributes.
        # The decimation is then put by default to 0 which correspond to
        # disable decimation.

        # If the board uses an external clock, the samplerate must be a float
        # or an int.
        # The decimation is then 0, only decimation allowed in this mode of the
        # clock.

        if clock_source == 'internal':

            decimation = 0
            samplerate = allow_samplerates[samplerate]
        elif clock_source == 'external':

            decimation = 1
            samplerate = samplerate*1e6 # To get it in S/s
        elif clock_source == 'fast_external':

            decimation = 1
            samplerate = samplerate*1e6 # To get it in S/s
        else:

            raise ValueError('The clock source must be "internal" or\
                             "external"')

        board.setCaptureClock(allow_clock_sources[clock_source],
                              samplerate,
                              allow_clock_edges[clock_edge],
                              decimation)



    def set_input_control(self, board):
        """
            Set the two input (CHANNEL A and B) of the board.
            The input range is fixed two +-400mV, the impedance to 50 ohm
            (cannot be changed) and, the coupling of the inputs to DC.
        """


        board.inputControl(ats.CHANNEL_A,
                           ats.DC_COUPLING,
                           ats.INPUT_RANGE_PM_400_MV,
                           ats.IMPEDANCE_50_OHM)


        board.inputControl(ats.CHANNEL_B,
                           ats.DC_COUPLING,
                           ats.INPUT_RANGE_PM_400_MV,
                           ats.IMPEDANCE_50_OHM)



    def set_trigger(self, board, parameters):
        '''
            Set the trigger.
            Here the trigger is supposed to be external.
        '''


        trigger_slope = parameters['trigger_slope']
        trigger_range = parameters['trigger_range']
        trigger_level = parameters['trigger_level']
        trigger_delay = parameters['trigger_delay']*1e-9 # To get it in second

        samplerate    = parameters['samplerate']*1e6 # To get it in S/s

        allow_trigger_slopes = parameters['allow_trigger_slopes']
        allow_trigger_ranges = parameters['allow_trigger_ranges']


        # The digitizer board has a flexible triggering system with two separate
        # trigger engines that can be used independently, or combined together to
        # generate trigger events. Since we use an external trigger, we only use
        # one trigger engine, the J one.
        # The three first parameters set the J engine and the choice of an
        # external trigger.
        # Since we don't use the second trigger engine, the four last parameters
        # are useless.

        # We calculate the trigger level for the board
        trigger_level_code = int(round(128.\
                                       + 127.*trigger_level/trigger_range))

        board.setTriggerOperation(ats.TRIG_ENGINE_OP_J,
                                  ats.TRIG_ENGINE_J,
                                  ats.TRIG_EXTERNAL,
                                  allow_trigger_slopes[trigger_slope],
                                  trigger_level_code,
                                  ats.TRIG_ENGINE_K,
                                  ats.TRIG_DISABLE,
                                  ats.TRIGGER_SLOPE_POSITIVE,
                                  128)


        # Set the external trigger.
        # This has to be done after the setTriggerOperation !
        # The coupling is DC (no choice) and the input range is given by the user.
        board.setExternalTrigger(ats.DC_COUPLING,
                                 allow_trigger_ranges[trigger_range])

        # The the trigger delay
        # We calculate the trigger delay for the board
        trigger_delay_code = int(trigger_delay * samplerate + 0.5)
        board.setTriggerDelay(trigger_delay_code)

        # The board has an option to fake a software trigger event in case of no
        # hardware trigger is detected.
        # We don't need this option and so disable it.
        board.setTriggerTimeOut(0)

        # We don't use the AUX I/O connector so don't offer the choice to tune it.
        board.configureAuxIO(ats.AUX_OUT_TRIGGER,
                             0)



    def prepare_acquisition(self, board, parameters):
        """
            Prepare the DMA buffers for the board.
            Return a list of buffers
        """

        samplesPerSec         = parameters['samplerate']*1e6

        # No pre-trigger samples in NPT mode
        preTriggerSamples     = 0
        postTriggerSamples    = parameters['samplesPerRecord']

        # Select the number of records per DMA buffer.
        recordsPerBuffer      = parameters['records_per_buffer']

        # Select the number of buffers per acquisition.
        buffersPerAcquisition = parameters['buffers_per_acquisition']

        # get the info about the FFT module
        if parameters['mode'] == 'FFT':

            dsp_array=board.dspGetModules()

            fft_module=dsp_array[0]

            dsp_info=fft_module.dspGetInfo()

        # define the channel mask according to the working mode of the digitizer
        if parameters['mode']== 'FFT':
            # Only channel A is used when on-FPGA FFT is active
            channels              = ats.CHANNEL_A
            channelCount          = 1
        elif parameters['mode']== 'CHANNEL_AB':
            # For two active channels
            channels              = ats.CHANNEL_A | ats.CHANNEL_B
            channelCount          = 2
        elif parameters['mode']== 'CHANNEL_A':
            # If channel A only is active
            channels              = ats.CHANNEL_A
            channelCount          = 1
        elif parameters['mode']== 'CHANNEL_B':
            # If channel B only is active
            channels              = ats.CHANNEL_B
            channelCount          = 1
        else:
            raise ValueError('mode of the digitizer must be "CHANNEL_AB" or \
                            "CHANNEL_A" or "CHANNEL_B" or "FFT"')

        # Compute the number of samples per record
        samplesPerRecord = preTriggerSamples + postTriggerSamples

        #Configure the FFT module
        if parameters['mode'] == 'FFT':
            fftLength_samples = 1
            while fftLength_samples < samplesPerRecord :
                fftLength_samples *= 2

            # Sets the real part of the FFT windowing
            fft_window_real=ats.dspGenerateWindowFunction(windowType, samplesPerRecord, fftLength_samples - samplesPerRecord)

            # According to the documentation, the imaginary part of the FFT windowing should be filled with zeros
            fft_window_imag=ats.dspGenerateWindowFunction(windowType, 0, fftLength_samples - samplesPerRecord)

            # Configures the FFT window
            fft_module.fftSetWindowFunction(samplesPerRecord,ctypes.c_void_p(fft_window_real.ctypes.data),ctypes.c_void_p(fft_window_imag.ctypes.data))

            # Compute the number of bytes per record and per buffer

            # For now the output of the output of the on-FPGA FFT is set to 'FFT_OUTPUT_FORMAT_U16_AMP2',
            # thus the number of bytes per sample is 2
            bytesPerSample = 2

            # Computes the number of bytes per record according to the settings of the on-FPGA FFT
            bytesPerRecord=fft_module.fftSetup(channels, samplesPerRecord, fftLength_samples, ats.FFT_OUTPUT_FORMAT_U16_AMP2, ats.FFT_FOOTER_NONE,0)

            bytesPerBuffer   = bytesPerRecord * recordsPerBuffer

            # change made by Remy the 2018/06/21
            parameters['samplesPerRecord'] = int(bytesPerRecord/bytesPerSample)
            # before it was:
            # parameters['samplesPerRecord'] = bytesPerRecord/bytesPerSample


        else:

            # Compute the number of bytes per record and per buffer
            memorySize_samples, bitsPerSample = board.getChannelInfo()
            bytesPerSample   = (bitsPerSample.value + 7) // 8

            bytesPerRecord   = bytesPerSample * samplesPerRecord
            bytesPerBuffer   = bytesPerRecord * recordsPerBuffer * channelCount
            # change made by Remy the 2018/06/21
            parameters['samplesPerRecord'] = int(bytesPerRecord/bytesPerSample)
            # before it was:
            # parameters['samplesPerRecord'] = bytesPerRecord/bytesPerSample

        # Select number of DMA buffers to allocate
        bufferCount = parameters['nb_buffer_allocated']

        # Modified per Etienne.
        # Alazar gave bytesPerSample > 8 but this condition seemed strange to
        # me considering the previous code bytesPerSample   = (bitsPerSample.value + 7) // 8

        # Allocate DMA buffers
        sample_type = ctypes.c_uint8
        if bytesPerSample > 1:
            sample_type = ctypes.c_uint16

        buffers = []
        for i in range(bufferCount):
            buffers.append(ats.DMABuffer(sample_type, bytesPerBuffer))


        board.setRecordSize(preTriggerSamples, postTriggerSamples)

        # Prepate the board to work in the asynchroneous mode of acquisition
        recordsPerAcquisition = recordsPerBuffer * buffersPerAcquisition

        if parameters['mode'] == 'FFT':
            admaFlags = ats.ADMA_EXTERNAL_STARTCAPTURE| ats.ADMA_NPT | ats.ADMA_DSP
            board.beforeAsyncRead(channels,
                                0,
                                bytesPerRecord,
                                recordsPerBuffer,
                                0x7FFFFFFF,
                                admaFlags)
        elif parameters['mode'] == 'CHANNEL_AB':
            board.beforeAsyncRead(channels,
                                -preTriggerSamples,
                                samplesPerRecord,
                                recordsPerBuffer,
                                recordsPerAcquisition,
                                ats.ADMA_EXTERNAL_STARTCAPTURE \
                                | ats.ADMA_NPT | ats.ADMA_FIFO_ONLY_STREAMING)
        elif parameters['mode'] == 'CHANNEL_A':
             board.beforeAsyncRead(channels,
                                -preTriggerSamples,
                                samplesPerRecord,
                                recordsPerBuffer,
                                recordsPerAcquisition,
                                ats.ADMA_EXTERNAL_STARTCAPTURE \
                                | ats.ADMA_NPT | ats.ADMA_FIFO_ONLY_STREAMING)
        elif parameters['mode'] == 'CHANNEL_B':
             board.beforeAsyncRead(channels,
                                -preTriggerSamples,
                                samplesPerRecord,
                                recordsPerBuffer,
                                recordsPerAcquisition,
                                ats.ADMA_EXTERNAL_STARTCAPTURE \
                                | ats.ADMA_NPT | ats.ADMA_FIFO_ONLY_STREAMING)


        # Put the buffers previously created in the list of available buffers
        for buff in buffers:
            board.postAsyncBuffer(buff.addr, buff.size_bytes)

        return buffers



    def data_acquisition(self, board, queue_data, parameters, buffers):
        """
            Acquire data and put them in the FIFO queue_data buffer memory.

            Output buffersCompleted (int): Number of emptied buffer.
        """

        buffersPerAcquisition = parameters['buffers_per_acquisition']
        recordsPerBuffer      = parameters['records_per_buffer']
        preTriggerSamples     = 0 # NPT mode
        postTriggerSamples    = parameters['samplesPerRecord']
        samplesPerRecord      = preTriggerSamples + postTriggerSamples

        start = time.clock() # Keep track of when acquisition started
        board.startCapture() # Start the acquisition

        message = 'Attempt to capture %d buffers\n' % buffersPerAcquisition
        buffersCompleted = 0
        bytesTransferred = 0

        # We measure up to have empty all the buffers set by the user or
        # if the user stop the measurement
        while buffersCompleted < buffersPerAcquisition and parameters['measuring']:

            buff = buffers[buffersCompleted % len(buffers)]
            if parameters['mode'] == 'FFT':
                board.dspGetBuffer(buff.addr, timeout_ms=5000)
            else:
                board.waitAsyncBufferComplete(buff.addr, timeout_ms=5000)

            buffersCompleted += 1
            bytesTransferred += buff.size_bytes

            if parameters['mode'] == 'FFT':
                queue_data.put(np.copy(buff.buffer))
            elif parameters['mode'] == 'CHANNEL_AB':
                queue_data[0].put(np.copy(buff.buffer[0::2]))
                queue_data[1].put(np.copy(buff.buffer[1::2]))
            elif parameters['mode'] == 'CHANNEL_A':
                queue_data.put(np.copy(buff.buffer))
            elif parameters['mode'] == 'CHANNEL_B':
                queue_data.put(np.copy(buff.buffer))

            # Add the buffer to the end of the list of available buffers.
            board.postAsyncBuffer(buff.addr, buff.size_bytes)

        # Compute the total transfer time, and display performance information.
        transferTime_sec = time.clock() - start
        message += 'Capture completed in %f sec\n' % transferTime_sec
        buffersPerSec      = 0
        bytesPerSec        = 0
        recordsPerSec      = 0
        samplesTransferred = samplesPerRecord*recordsPerBuffer*buffersCompleted*2
        if transferTime_sec > 0:
            buffersPerSec = buffersCompleted / transferTime_sec
            bytesPerSec   = bytesTransferred / transferTime_sec
            recordsPerSec = recordsPerBuffer * buffersCompleted / transferTime_sec
            samplePerSec  = samplesTransferred / transferTime_sec

        message += 'Captured %d buffers (%f buffers per sec)\n' % (buffersCompleted, buffersPerSec)
        message += 'Captured %d records (%f records per sec)\n' % (recordsPerBuffer * buffersCompleted, recordsPerSec)
        message += 'Transferred %d bytes (%f Mbytes per sec)\n' % (bytesTransferred, bytesPerSec/1024**2.)
        message += 'Transferred %d samples (%f MS per sec)\n' % (samplesTransferred, samplePerSec/1e6)

        parameters['message'] = message

        return buffersCompleted



    def get_data(self, queue_data, parameters):
        """
            Method allowing the transfert of data from the board to the computer.
            The board is instanced following the parameters input and data are
            transfert to the queue_data memory buffer.

            Input:
                - queue_data_cha: FIFO memory buffer instance from the
                               multiprocess library.
                - queue_data_chb: FIFO memory buffer instance from the
                               multiprocess library.
                - parameters: Dictionnary with all board parameters instance
                              from multiprocess library
        """

        # We instance a board object
        # All the parameters of the measurement will be set on this instance
        board = ats.Board(systemId = 1, boardId = 1)

        # We set the clock
        self.set_clock(board, parameters)

        # We set the two inputs (chanel A and B)
        self.set_input_control(board)

        # We set the trigger
        self.set_trigger(board, parameters)

        # We prepare the acquisition
        buffers = self.prepare_acquisition(board, parameters)

        # We wait a little to let the time to the board to initialize itself
        time.sleep(0.5)

        # We launch the data acquisition
        parameters['measured_buffers'] = self.data_acquisition(board,
                                                               queue_data,
                                                               parameters, buffers)

        # We stop the transfer.
        if parameters['mode'] == 'FFT' :
            board.dspAbortCapture()
        else:
            board.abortAsyncRead()

        # We inform the parent process that the board is properly "closed"
        parameters['safe_acquisition'] = True

        # Once the board is "close" properly, we close the FIFO memory
        if parameters['mode'] == 'FFT' :
            queue_data.close()
        if parameters['mode'] == 'CHANNEL_AB' :
            queue_data[0].close()
            queue_data[1].close()
        if parameters['mode'] == 'CHANNEL_A' :
            queue_data.close()
        if parameters['mode'] == 'CHANNEL_B' :
            queue_data.close()
