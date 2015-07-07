# -*- coding: utf-8 -*-
from instrument import Instrument
import instruments
import numpy
import types
import logging


import pylab

class virtual_readout_IQ(Instrument):
    '''
    This is the driver for the virtual instrument which can read out I Q

    Usage:
    Initialize with
    <name> = qt.instruments.create('name', 'virtual_readout_IQ', spectrum='name_spectrum', mwsrc_pulse='name_microwave_source_used_pulse', mwsrc_read_out='name_microwave_source_used_read_out')
    '''
    
    def __init__(self, name, spectrum, mwsrc_read_out, memsize= 8008, amp0=500, amp1=500):
        '''
            Initialize the virtual instruments
                
                Input:
                    name:                       Name of the virtual instruments
                    spectrum:                   Name given to the Spectrum M3i4142

                    
                    memsize (sample):           Size of the memory allocated in the card [Sample]
                                                default = 8008
                                        
                    amp0 (int)                  : half of the range of the channel 0 [mV]
                                                default = 500
                                        
                    amp1 (int)                  : half of the range of the channel 1 [mV]
                                                default = 500
                
                Output:
                    None
        '''
        
        Instrument.__init__(self, name, tags=['virtual'])
        
        
        self.add_parameter('input_term_ch0', option_list=['50', '1 M'], units='Ω', flags=Instrument.FLAG_GETSET, type=types.StringType)
        self.add_parameter('input_term_ch1', option_list=['50', '1 M'], units='Ω', flags=Instrument.FLAG_GETSET, type=types.StringType)

        self.add_parameter('input_amp_ch0', option_list=[200, 500, 1000, 2000, 5000, 10000], units='mV', flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('input_amp_ch1', option_list=[200, 500, 1000, 2000, 5000, 10000], units='mV', flags=Instrument.FLAG_GETSET, type=types.IntType)
        
        #The maxvalue of the samplerate is only of 250 MS.Hz because we use the two channels of the board
        self.add_parameter('samplerate', units='MS.Hz', maxval=400, flags=Instrument.FLAG_GETSET, type=types.IntType)

        self.add_parameter('numberSample', minval=16, units='S', flags=Instrument.FLAG_GETSET, type=types.IntType)
        
        self.add_parameter('acquisitionTime', units='ms', flags=Instrument.FLAG_GET, type=types.FloatType)
        self.add_parameter('bandWidth', units='Hz', flags=Instrument.FLAG_GET, type=types.FloatType)


        self.add_parameter('status', flags=Instrument.FLAG_GETSET, option_list=['on', 'off'], type=types.StringType)
        self.add_parameter('detuning', units='MHz', flags=Instrument.FLAG_GETSET, type=types.FloatType)
        self.add_parameter('frequency', units='GHz', minval=100e-6, maxval=12.75, flags=Instrument.FLAG_GETSET, type=types.FloatType)
        self.add_parameter('power', units='dBm', minval=-20, maxval=30, flags=Instrument.FLAG_GETSET, type=types.FloatType)

        
        # Defining some stuff
        self._instruments = instruments.get_instruments()
        self._spectrum = self._instruments.get(spectrum)
        
        self._microwave_generator = self._instruments.get(mwsrc_read_out)
        
        #Default detuning [MHz]
        self.detuning = 0
        
        #We initialize the card
        #The memory size is in sample
        self.memsize = memsize
        
        #We don't want to record data before the trigger so, we put the posttrigger time equal to the total memory size
        self.posttrigger = self.memsize

        #We initialize the card on two channel single mode
        self._spectrum.init_channel01_single_mode(int(self._spectrum.get_memsize()), int(self._spectrum.get_post_trigger()),amp0= int(self._spectrum.get_input_amp_ch0()),amp1 = int(self._spectrum.get_input_amp_ch1()) )

        
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
        
        self.get_samplerate()
        self.get_numberSample()
        self.get_acquisitionTime()
        self.get_bandWidth()
        
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
        self._microwave_generator.set_frequency(frequency*1e9 + self.detuning*1e6)


    def do_get_frequency(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been tuned [Hz]
        '''
        
        logging.info(__name__+' : Get the frequency of the intrument')
        return float(self._microwave_generator.get_frequency())*1e-9 - self.detuning*1e-3



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


    def do_set_power(self, power = 0.0):
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
        
        return self.detuning


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
        
        self.detuning = detuning
#        self.set_frequency(self.get_frequency())


#########################################################################
#
#
#                           Bandwidth
#
#
#########################################################################

    def do_get_bandWidth(self):
        '''
            Get the bandwidth of the measurement

            Input:
                None
            Output:
                bandWidth (int)   : The bandWidth of the measurement [Hz]
        '''
        
        return 1./float(self.get_acquisitionTime())



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

    def do_get_numberSample(self):
        '''
            Get the number the memory size prepared in the board

            Input:
                None
            Output:
                memsize (int)   : The memory size setted on the board [Sample]
        '''
        
        return self._spectrum.get_memsize()



    def do_set_numberSample(self, memsize):
        '''
            Set the number of sample that are going to be record

            Input:
                memsize (int)   : The memory size setted on the board [Sample]
            Output:
                None
        '''
        
        self._spectrum.set_memsize(memsize)

        #We want to have all the memory size dedicated to the postrigger
        self._spectrum.set_post_trigger(memsize)
        
        #We update the acquisition time and the bandwidth
        self.get_acquisitionTime()
        self.get_bandWidth()


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
        self.get_acquisitionTime()
        self.get_bandWidth()


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


    def measurement(self):
        '''
            Run a measurement thanks to the spectrum card_status
            We assume that :
                - I correspond to the channel 0
                - Q correspond to the channel 1

            Input:
                 None

            Output:
                date (float[channel_0], float[channel_1]) : Data coming from the measurement [mV]
        '''
        
        #We prepare the recording
        self._spectrum.start_with_trigger_and_waitready()
        
        #We record the result
        self.result_0, self.result_1 =  self._spectrum.readout_doublechannel_singlemode_float()
        
        return self.result_0, self.result_1

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
        self.result_0 =  self._readout_singlechannel_multimode_float()
        
        return self.result_0

