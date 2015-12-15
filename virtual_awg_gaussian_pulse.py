from instrument import Instrument
import instruments
import numpy as np
import types
import logging

class virtual_awg_gaussian_pulse(Instrument):
    '''
    This is the driver for the virtual instrument which can create a microwave
    Gaussian pulse
    '''

    def __init__(self, name, awg, channel, mwsrc):
        '''
            Initialize the virtual instruments

                Input:
                    - name (string): Name of the virtual instruments
                    - awg (string): Name of a awg
                    - channel (int): channel number of the awg
                    - mwsrc (string): Name of to the microwave generator

                Output:
                    None
        '''
        Instrument.__init__(self, name, tags=['virtual'])

        #Import instruments
        self._instruments = instruments.get_instruments()
        self._awg         = self._instruments.get(awg)
        self._mwsrc       = self._instruments.get(mwsrc)

        if not channel in (1, 2, 3, 4):
            raise ValueError('The channel of the awg should be between 1 and for')
        self._channel     = int(channel)

        # Default parameters
        self._duration = 50 # In ns
        self._delay    = 50 # In ns


        self._awg.set_ref_source('EXT')
        self._awg.set_ref_freq(10)

        self._awg.set_func_mode('SEQ')
        self._awg.seq_mode('STEP')
        self._awg.seq_jump_source('BUS')
        self._awg.set_trace_mode('SING')
        self._awg.set_clock_freq(1e3)

        self._awg.set_run_mode('TRIG')
        self._awg.set_trigger_mode('NORM')
        self._awg.set_trigger_source('TIM')
        self._awg.set_trigger_timer_mode('TIME')
        self._awg.set_channels_synchronised('ON')
        self._awg.set_trigger_timer_time(100)
        self._awg.init_channel(self._channel)
        self._gaussian()

        #Parameters
        self.add_parameter('duration',
                            flags  = Instrument.FLAG_GETSET,
                            minval = 0.,
                            # maxval = self._max_width,
                            units  = 'ns',
                            type   = types.FloatType)

        self.add_parameter('delay',
                           flags=Instrument.FLAG_GETSET,
                           minval=0,
                        #    maxval=1e10,
                           units='ns',
                           type=types.FloatType)

        min_freq = 1e-9*self._mwsrc.get_parameter_options('frequency')['minval']
        max_freq = 1e-9*self._mwsrc.get_parameter_options('frequency')['maxval']
        self.add_parameter('frequency',
                           flags  = Instrument.FLAG_GETSET,
                           units  = 'GHz',
                           minval = min_freq,
                           maxval = max_freq,
                           type   = types.FloatType)

        min_power = self._mwsrc.get_parameter_options('power')['minval']
        max_power = self._mwsrc.get_parameter_options('power')['maxval']
        self.add_parameter('power',
                            flags  = Instrument.FLAG_GETSET,
                            minval = min_power,
                            maxval = max_power,
                            units  = 'dBm',
                            type   = types.FloatType)

        self.add_parameter('status',
                           option_list = ['ON', 'OFF'],
                           flags       = Instrument.FLAG_GETSET,
                           type        = types.StringType)



        self.set_status('OFF')
        self._mwsrc.set_status('ON')
        #Functions
        self.get_all()


    def _volt2bit(self, volt):
        """
            Return the bit code corresponding to the entered voltage value in uint16
        """

        full = 4. # in volt
        resolution = 2**14. - 1.

        return  np.array(np.round((volt + full/2.)*resolution/full, 0),
                         dtype ='uint16')

    def _gaussian(self):

        scale = 4. # Numbers of sigma

        # Get timeline in sample
        nb_samples = self._awg.get_trigger_timer_time()*self._awg.get_clock_freq()
        time       = np.arange(nb_samples)#/self._awg.get_clock_freq()*1e-6

        # std   = self._duration/scale*1e-9 # In second
        std = int(round(self._duration/scale*self._awg.get_clock_freq()*1e-3, 0)) # In sample
        x0  = int(round(self._delay*self._awg.get_clock_freq()*1e-3 + std*scale/2., 0)) # In sample

        # We build the full gaussian
        gaussian = np.exp(-(time-x0)**2./2./std**2.)

        # we truncate the waveform and keep only 2 sigma of each side
        waveform = np.concatenate((np.zeros(x0-2*std),
                                   gaussian[x0-2*std:x0+2*std],
                                   np.zeros(nb_samples - x0 - 2*std)))

        waveform = self._volt2bit(waveform)
        self._awg.send_waveform(waveform, self._channel, 1)

    def get_all(self):
        '''
            Get all parameters of the virtual device

            Input:
                None

            Output:
                None
        '''

        self.get_duration()
        self.get_delay()

        self.get_frequency()
        self.get_power()
        self.get_status()

#########################################################################
#
#
#                           Duration
#
#
#########################################################################

    def do_get_duration(self):
        '''
            Return the duration of the pulse

            Input:
                None

            Output:
                val (float): Duration of the pulse [ns]
        '''

        return self._duration


    def do_set_duration(self, val):
        '''
            Set the duration of the pulse.

            Input:
                val (float): Duration of the pulse [ns]

            Output:
                None
        '''

        self._duration = val

        # Update the waveform
        self._gaussian()


#########################################################################
#
#
#                           Delay
#
#
#########################################################################

    def do_get_delay(self):
        '''
            Return the delay of the pulse

            Input:
                None

            Output:
                val (float): delay of the pulse [ns]
        '''

        return self._delay


    def do_set_delay(self, val):
        '''
            Set the delay of the pulse.

            Input:
                val (float): delay of the pulse [ns]

            Output:
                None
        '''

        self._delay = val

        # Update the waveform
        self._gaussian()


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

        return self._mwsrc.get_power()


    def do_set_power(self, power):
        '''
            Set the value of the power

            Input:
                power (float): power of the microwave [dBm]

            Output:
                None
        '''

        self._mwsrc.set_power(power)


#########################################################################
#
#
#                           Frequency
#
#
#########################################################################

    def do_get_frequency(self):
        '''
            Return the value of the frequency

            Input:
                None

            Output:
                Frequency (Float): Frequency of the pulse [GHz]
        '''

        return 1e-9*self._mwsrc.get_frequency()


    def do_set_frequency(self,frequency):
        '''
            Set the value of the frequency

            Input:
                frequency (float): frequency of the pulse [GHz]

            Output:
                None
        '''

        self._mwsrc.set_frequency(frequency*1e9)


#########################################################################
#
#
#                           Status
#
#
#########################################################################

    def do_set_status(self, status):
        '''
            Switch on|off the microwave pulse

            Input:
                status (String): Status of the microwave pulse ['ON', 'OFF']

            Output:
                None
        '''

        if self._channel == 1:
            return self._awg.set_ch1_output(status)
        elif self._channel == 2:
            return self._awg.set_ch2_output(status)
        elif self._channel == 3:
            return self._awg.set_ch3_output(status)
        else:
            return self._awg.set_ch4_output(status)


    def do_get_status(self):
        '''
            Get the microwave pulse status

            Input:
                None

            Output:
                status (String): Microwave pulse status
        '''

        if self._channel == 1:
            return self._awg.get_ch1_output()
        elif self._channel == 2:
            return self._awg.get_ch2_output()
        elif self._channel == 3:
            return self._awg.get_ch3_output()
        else:
            return self._awg.get_ch4_output()
