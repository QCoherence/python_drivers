# -*- coding: utf-8 -*-
from instrument import Instrument
import instruments
import numpy
import types
import logging
from time import time

class virtual_readout_IQ_multi(Instrument):
    '''
    This is the driver for the virtual instrument that reads out I Q using multiple pulses

    Usage:
    Initialize with
    <name> = qt.instruments.create('name', 'virtual_readout_IQ_multi', spectrum='name_spectrum', mwsrc_pulse='name_microwave_source_used_pulse', mwsrc_read_out='name_microwave_source_used_read_out')
    '''

    def __init__(self, name, spectrum, mwsrc_read_out, pulser, nums=128, segsize= 2048, amp0=500, amp1=500):
        '''
            Initialize the virtual instruments

                Input:
                    name            : Name of the virtual instruments
                    spectrum        : Name given to the Spectrum M3i4142
                    nums (int)      : number of consequtive measurements
                                        default = 128

                    segsize (int)   : Size of the memory allocated in the card [Sample]
                                        default = 2048

                    amp0 (int)      : half of the range of the channel 0 [mV]
                                        default = 500

                    amp1 (int)      : half of the range of the channel 1 [mV]
                                        default = 500

                Output:
                    None
        '''

        Instrument.__init__(self, name, tags=['virtual'])


        self.add_parameter('input_term_ch0', option_list=['50', '1 M'], units='Ω', flags=Instrument.FLAG_GETSET, type=types.StringType)
        self.add_parameter('input_term_ch1', option_list=['50', '1 M'], units='Ω', flags=Instrument.FLAG_GETSET, type=types.StringType)

        self.add_parameter('input_amp_ch0', option_list=[200, 500, 1000, 2000, 5000, 10000], units='mV', flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('input_amp_ch1', option_list=[200, 500, 1000, 2000, 5000, 10000], units='mV', flags=Instrument.FLAG_GETSET, type=types.IntType)

        self.add_parameter('filter_ch0', option_list=['FBW', '20 MHz'], units='', flags=Instrument.FLAG_GETSET, type=types.StringType)
        self.add_parameter('filter_ch1', option_list=['FBW', '20 MHz'], units='', flags=Instrument.FLAG_GETSET, type=types.StringType)

        self.add_parameter('input_coupling_ch0', option_list=['AC', 'DC'], units='', flags=Instrument.FLAG_GETSET, type=types.StringType)
        self.add_parameter('input_coupling_ch1', option_list=['AC', 'DC'], units='', flags=Instrument.FLAG_GETSET, type=types.StringType)

        #The maxvalue of the samplerate is only of 250 MS.Hz because we use the two channels of the board
        self.add_parameter('samplerate', units='MS.Hz', minval=10, maxval=250, flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('delay', units='ns', minval = 0., maxval=1e6, flags=Instrument.FLAG_GETSET, type=types.FloatType)

        self.add_parameter('segmentsize', minval=16, units='S', flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('repetitions', minval=1, flags=Instrument.FLAG_GETSET, type=types.IntType)

#        self.add_parameter('acquisitionTime', units='ms', flags=Instrument.FLAG_GET, type=types.FloatType)
#        self.add_parameter('bandWidth', units='Hz', flags=Instrument.FLAG_GET, type=types.FloatType)


        self.add_parameter('status', flags=Instrument.FLAG_GETSET, option_list=['on', 'off'], type=types.StringType)
        self.add_parameter('detuning', units='MHz', flags=Instrument.FLAG_GETSET, type=types.FloatType)
        self.add_parameter('frequency', units='GHz', minval=100e-6, maxval=12.75, flags=Instrument.FLAG_GETSET, type=types.FloatType)
        self.add_parameter('power', units='dBm', minval=-5, maxval=30, flags=Instrument.FLAG_GETSET, type=types.FloatType)
        self.add_parameter('time_delay_for_phase', units= 'ns', flags = Instrument.FLAG_GETSET, type=types.FloatType)

        # Defining some stuff
        self._instruments = instruments.get_instruments()
        self._spectrum = self._instruments.get(spectrum)
        self._pulser = self._instruments.get(pulser)

        self._microwave_generator = self._instruments.get(mwsrc_read_out)

        #Default detuning [MHz]
        self._detuning = 0

        #We initialize the card
        #Number of segments
        self._nums=nums
        #We don't want to record data before the trigger so, we put the posttrigger time equal to the segment size
        #We initialize the card on two channel multiple recording mode
        self._spectrum.init_channel01_multiple_recording(nums=self._nums, segsize=segsize, posttrigger=segsize-8, amp0=amp0, amp1=amp1)
#                       init_channel0_multiple_recording(self, nums = 4, segsize=10
# 24, posttrigger=768, amp=500, offs=0):
#        self._spectrum.init_channel0_multiple_recording(nums=self._nums, segsize=segsize, posttrigger=segsize-8,amp=amp0)

        # we put the spectrum as ext ref clock mode:
        self._spectrum.set_CM_extrefclock() # added by Remy


        #We initialize the trigger pulse for the board
        self._pulser.set_chB_status('OFF')
        self._pulser.set_chB_polarity('POS')
        self._pulser.set_chB_width(50)
        self._pulser.set_chB_delay(0.)
        self._pulser.set_chB_status('ON')
        self.time_phase_delay = 0.

        self.get_all()

    def get_all(self):
        '''
            Get all parameters of the virtual device

            Input:
                None

            Output:
                None
        '''
        self.get_input_term_ch0()
        self.get_input_term_ch1()

        self.get_input_amp_ch0()
        self.get_input_amp_ch1()

        self.get_filter_ch0()
        self.get_filter_ch1()

        self.get_input_coupling_ch0()
        self.get_input_coupling_ch1()

        self.get_samplerate()
        self.get_segmentsize()
        self.get_delay()
        self.get_repetitions()
#        self.get_acquisitionTime()
#        self.get_bandWidth()

        self.get_detuning()
        self.get_frequency()
        self.get_power()
        self.get_status()




#########################################################
#
#
#                Frequency
#
#
#########################################################




    def do_set_frequency(self, frequency=1.):
        '''
            Set the frequency of the detector

            Input:
                frequency (float): Frequency at which the instrument will be tuned [GHz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency of the detector')
        self._microwave_generator.set_frequency(frequency*1e9 + self._detuning*1e6)


    def do_get_frequency(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been tuned [GHz]
        '''

        logging.info(__name__+' : Get the frequency of the intrument')
        return float(self._microwave_generator.get_frequency())*1e-9 - self._detuning*1e-3



#########################################################################
#
#
#                           Microwave on/off
#
#
#########################################################################

    def do_set_status(self, status):
        '''
            Switch on/off the microwave generator.

            Input:
                status (String): Status of the microwave generator ['on', 'off']

            Output:
                None
        '''

        self._microwave_generator.set_status(status)

    def do_get_status(self):
        '''
            Get the status of the microwave generator.

            Input:
                None

            Output:
                status (String): Status of the microwave generator
        '''

        return self._microwave_generator.get_status()

#########################################################################
#
#
#                           Power
#
#
#########################################################################

    def do_get_power(self):
        '''
            Return the value of the power

            Input:
                None

            Output:
                None
        '''

        return self._microwave_generator.get_power()


    def do_set_power(self, power = 10.0):
        '''
            Set the value of the power

            Input:
                power (float): power of the microwave [dBm]

            Output:
                None
        '''

        self._microwave_generator.set_power(power)

#########################################################################
#
#
#                           Delay
#
#
#########################################################################

    def do_get_delay(self):
        '''
            Return the delay of the trigger pulse in ns

            Input:
                None

            Output:
                Delay of the trigger pulse in ns
        '''

        return self._pulser.get_chB_delay() - self._pulser.get_chA_delay()


    def do_set_delay(self, delay = 80.0):
        '''
            Set the value of the trigger pulse delay

            Input:
                delay (float): delay of the microwave [ns]

            Output:
                None
        '''

        aDelay = self._pulser.get_chA_delay()

        self._pulser.set_chB_delay(aDelay + delay)

#########################################################################
#
#
#                           Time_Delay for phase
#
#
#########################################################################

    def do_get_time_delay_for_phase(self):
        '''
            Return the time delay choosen by user for the phase in ns

            Input:
                None

            Output:
                Delay for the phase in ns
        '''

        return self.time_phase_delay


    def do_set_time_delay_for_phase(self, t_phi_delay = 0.0):
        '''
            Set the value of the time delay choosen by user for the phase

            Input:
                t_phi_delay (float): delay for phase [ns]

            Output:
                None
        '''
        self.time_phase_delay = t_phi_delay



#########################################################################
#
#
#                           Detuning
#
#
#########################################################################

    def do_get_detuning(self):
        '''
            Get the detuning between the microwave generator used for the read out and the microwave generator used for the microwave pulse
            detuning = mwsrc_pulse - mwsrc_read_out

            Input:
                None

            Output:
                detuning (float): detuning between the two microwave generators [MHz]
        '''

        return self._detuning


    def do_set_detuning(self, detuning=0.):
        '''
            Set the detuning between the microwave generator used for the microwave pulse and the microwave generator used for the read out
            frequency difference = mwsrc_pulse - mwsrc_read_out

            Input:
                detuning (float): Detuning between the two microwave generators [MHz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the detuning between the two microwave generators')

        self._detuning = detuning
        self.set_frequency(self.get_frequency(query=False))


#########################################################################
#
#
#                           Bandwidth
#
#
#########################################################################

#    def do_get_bandWidth(self):
#        '''
#            Get the bandwidth of the measurement

#            Input:
#                None
#            Output:
#                bandWidth (int)   : The bandWidth of the measurement [Hz]
#        '''

#        return 1./float(self.get_acquisitionTime())



#########################################################################
#
#
#                           Acquisition time
#
#
#########################################################################

    def do_get_acquisitionTime(self):
        '''
            Get the time that the measure will spend

            Input:
                None
            Output:
                acquisitionTime (int)   : The time that the measure will spend [ms]
        '''

        return float(self.get_numberSample())/float(self.get_samplerate()*1e3)



#########################################################################
#
#
#                           Memory size
#
#
#########################################################################

    def do_get_repetitions(self):
        '''
            Gets the number of segments

            Input:
                None
            Output:
               repetitions (int)   : The number of segments
        '''

        return self._nums

    def do_set_repetitions(self, nums):
        '''
            Sets the number of measurement repetitions

            Input:
               repetitions (int)   : The number of measurement repetitions
            Output:
                None
        '''

        self._nums = nums
        segsize = self.get_segmentsize(query=False)
        self._spectrum.set_memsize(segsize*nums)


    def do_get_segmentsize(self):
        '''
            Gets the length of one segment

            Input:
                None
            Output:
               segsize (int)   : The segment size set on the board [Sample]
        '''

        return self._spectrum.get_segmentsize()



    def do_set_segmentsize(self, segsize):
        '''
            Sets the number of sample that are going to be recorded info one segment

            Input:
                segsize (int)   : The segment size set on the board [Sample]. Must be a multiple of 8.
            Output:
                None
        '''

        if segsize%8 is not 0:
            segsize = 8*(segsize/8)+8
            logging.warning(__name__ + ' : Argument rounded to the next multiple of 8')


        self._spectrum.set_segmentsize(segsize)

        #We want to keep pretrigger part as small as possible, i.e. 8 samples
        self._spectrum.set_post_trigger(segsize-8)
        self._spectrum.set_memsize(segsize*self._nums)

        #We update the acquisition time and the bandwidth
#        self.get_acquisitionTime()
#        self.get_bandWidth()


#########################################################################
#
#
#                           Sample rate
#
#
#########################################################################


    def do_set_samplerate(self, rate):
        '''
            Set the samplerate of the board

            Input:
                rate (int): The samplerate wanted for the board [MHz]
            Output:
                None
        '''
        self._spectrum.set_samplerate(rate)

        #We update the acquisition time and the bandwidth
#        self.get_acquisitionTime()
#        self.get_bandWidth()


    def do_get_samplerate(self):
        '''
            Get the samplerate of the board

            Input:
                None
            Output:
                samplerate (int)    : The samplerate tuned on the board [MHz]
        '''
        return self._spectrum.get_samplerate()

#########################################################################
#
#
#                           Impedance
#
#
#########################################################################

    def do_get_input_term_ch0(self):
        '''
            Get channel 0 impedance termination

            Input:

                None

            Output:

                Impedance (string) : Impedance in ohms
        '''

        return self._spectrum.get_input_term_ch0()

    def do_set_input_term_ch0(self, impedance):
        '''
            Set the value of the impedance of channel 0 to 50 Ω or 1 MΩ

            Input:
                impedance (int) : Value of the termination [Ω]

            Output:
                None
        '''

        self._spectrum.set_input_term_ch0(impedance)



    def do_get_input_term_ch1(self):
        '''
            Get channel 1 impedance termination

            Input:

                None

            Output:

                Impedance (string) : Impedance in ohms
        '''

        return self._spectrum.get_input_term_ch1()

    def do_set_input_term_ch1(self, impedance):
        '''
            Set the value of the impedance of channel 1 to 50 Ω or 1 MΩ

            Input:
                impedance (int) : Value of the termination [Ω]

            Output:
                None
        '''

        self._spectrum.set_input_term_ch1(impedance)

#########################################################################
#
#
#                           Filter
#
#
#########################################################################

    def do_get_filter_ch0(self):
        '''
            Get channel 0 filter

            Input:

                None

            Output:

                filter (string) : filter
        '''

        return self._spectrum.get_filter_ch0()

    def do_get_filter_ch1(self):
        '''
            Get channel 01filter

            Input:

                None

            Output:

                filter (string) : filter
        '''

        return self._spectrum.get_filter_ch1()

    def do_set_filter_ch0(self, filt):
        '''
            Set the value of the filter of channel 0 to FBM or 20 MHz

            Input:
                filt (string) : ['FBW', '20 MHz']

            Output:
                None
        '''
        self._spectrum.set_filter_ch0(filt)

    def do_set_filter_ch1(self, filt):
        '''
            Set the value of the filter of channel 1 to FBM or 20 MHz

            Input:
                filt (string) : ['FBW', '20 MHz']

            Output:
                None
        '''

        self._spectrum.set_filter_ch1(filt)

#########################################################################
#
#
#                           Coupling
#
#
#########################################################################

    def do_get_input_coupling_ch0(self):
        '''
            Get channel 0 coupling

            Input:

                None

            Output:

                filter (string) : coupling
        '''

        return self._spectrum.get_input_coupling_ch0()

    def do_get_input_coupling_ch1(self):
        '''
            Get channel 01filter

            Input:

                None

            Output:

                filter (string) : coupling
        '''

        return self._spectrum.get_input_coupling_ch1()

    def do_set_input_coupling_ch0(self, coupling):
        '''
            Set the value of the coupling of channel 0 to AC or DC

            Input:
                filt (string) : ['AC', 'DC']

            Output:
                None
        '''

        self._spectrum.set_input_coupling_ch0(coupling)

    def do_set_input_coupling_ch1(self, coupling):
        '''
            Set the value of the coupling of channel 1 to AC or DC

            Input:
                filt (string) : ['AC', 'DC']

            Output:
                None
        '''

        self._spectrum.set_input_coupling_ch1(coupling)





#########################################################################
#
#
#                           Amplitude
#
#
#########################################################################


    def do_set_input_amp_ch0(self, amp):
        '''
        Sets the amplitude of the range of channel 0
        The range defines the precision of the analog-digital conversion

        Input:
            amp (int): amplitude of the channel in millivolts

        Output:
            None
        '''

        self._spectrum.set_input_amp_ch0(amp)


    def do_get_input_amp_ch0(self):
        '''
        Gets the amplitude of the range of channel 0
        The range defines the precision of the analog-digital conversion

        Input:
            None

        Output:
            amp (int): amplitude of the channel in millivolts
        '''

        return self._spectrum.get_input_amp_ch0()



    def do_set_input_amp_ch1(self, amp):
        '''
        Sets the amplitude of the range of channel 1
        The range defines the precision of the analog-digital conversion

        Input:
            amp (int): amplitude of the channel in millivolts

        Output:
            None
        '''

        self._spectrum.set_input_amp_ch1(amp)


    def do_get_input_amp_ch1(self):
        '''
        Gets the amplitude of the range of channel 1
        The range defines the precision of the analog-digital conversion

        Input:
            None

        Output:
            amp (int): amplitude of the channel in millivolts
        '''
        return self._spectrum.get_input_amp_ch1()

#########################################################################
#
#
#                           Measurement
#
#
#########################################################################


    def measurement(self, twoChannels=True):
        '''
            Run a measurement thanks to the spectrum card_status
            We assume that :
                - I correspond to the channel 0
                - Q correspond to the channel 1

            Input:
                 None

            Output:
                data (float[channel_0], float[channel_1]) : Data coming from the measurement [mV]
        '''

        #We prepare the recording
#        print 'start measurement'
#        startTime = time()
        self._spectrum.start_with_trigger_and_waitready()
        #We record the result

        if twoChannels is True:
            data =  self._spectrum.readout_doublechannel_multimode_float()
        else:
            data =  self._spectrum.readout_singlechannel_multimode_float()
#        endTime = time()
#        print('Elapsed time: %g seconds' %(endTime-startTime))
        return data


    def singlemeasurement(self):
        '''
            Run a measurement thanks to the spectrum card_status
            We assume that :
                - I correspond to the channel 0

            Input:
                 None

            Output:
                date (float[channel_0], float[channel_1]) : Data coming from the measurement [mV]
        '''

        #We prepare the recording
        self._spectrum.start_with_trigger_and_waitready()

        #We record the result
        self.result_0 =  self._spectrum.readout_singlechannel_multimode_float()

        return self.result_0
