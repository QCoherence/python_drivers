# Work in PROGRESS
# made by Remy Dassonneville in 2016-2017

from instrument import Instrument
import instruments
import numpy as np
import types
import logging

# from lib.math import fit # to be able to do some fit during the measurements
# import ATS9360.DataTreatment as dt
# import qt

# from lib.math.useful_functions import volt2bit, volt2bit_2, cos, pulse
# now coded in this driver
import matplotlib.pyplot as plt

CHANNEL=(1,2,3,4)

class virtual_pulsing_instrument(Instrument):
    '''
    TO DO: complete it!!!
    This is the driver for the virtual instrument which can create a spectroscopic
    sequence pulses and measure it.

    Usage:
    Initialize with:
    <name> = qt.instruments.create('name', 'virtual_pulsing_instrument',
    awg='awg_name', mwsrc1='name_microwave_generator', board='board_name',
    mwsrc2= 'name_microwave_generator2--if present--',
    current_src='name_current_source--if present--' )
    '''

    def __init__(self, name, awg, mwsrc1, board, ssb1, mwsrc2 = 'None', ssb2= 'None', current_src = 'None',
            firsttone_channel=1, secondtone_channel=4, board_marker= 1, mw_marker=2):
        '''
        Initialize the virtual instrument

            Input:
                - name: Name of the virtual instruments
                - awg: Name given to an arbitrary waveform generator
                - mwsrc1: Name given to the first microwave_generator
                - board: Name given to the acquisition card
                - mwsrc2: Name given to the second microwave_generator
                - current_src: Name given to the current source
                - firsttone_channel, secondtone_channel: channel of the awg for
                first or second tone
                - board_marker, mw_marker: number of the marker for the triggering
                of the board or the microwave
            Output:
                None
        '''
        Instrument.__init__(self, name, tags=['virtual'])
        #Import instruments
        self._instruments = instruments.get_instruments()

        self._arbitrary_waveform_generator = self._instruments.get(awg)
        self._SSB_tone1 = self._instruments.get(ssb1)
        self._microwave_generator1 = self._instruments.get(mwsrc1)

        self._microwave_generator1.set_power(21)  #microwave generator 1 is used for readout
        self._microwave_generator1.set_status('ON')
        self._microwave_generator1.set_pointsfreq(2)
        self._board = self._instruments.get(board)

        # if we import the second microwave generator or not
        if mwsrc2 != 'None':
            self._presence_mwsrc2 = 1
            self._microwave_generator2 = self._instruments.get(mwsrc2)
            self._microwave_generator2.set_power(5)
            self._microwave_generator2.set_status('ON')
        else:
            self._presence_mwsrc2 = 0

        # if we import the second ssb or not
        if ssb2 != 'None':
            self._presence_ssb2 = 1
            self._SSB_tone2 = self._instruments.get(ssb2)
        else:
            self._presence_ssb2 = 0

        # if we import the current source or not
        if current_src != 'None':
            self._presence_current_src = 1
            self._current_source = self._instruments.get(current_src)
            self._current_source.set_mode('dci')
            self._current_source.set_channel('A')
            self._current_source.set_resolution('high')
        else:
            self._presence_current_src = 0


        ########################################################################
        #                    parameters
        ########################################################################
        # GET_SET
        self.add_parameter('power_first_tone',
                            flags=Instrument.FLAG_GETSET,
                            minval = -20.,
                            maxval= 4.,
                            units='dBm',
                            type=types.FloatType)

        self.add_parameter('power_second_tone',
                            flags=Instrument.FLAG_GETSET,
                            minval = -20.,
                            maxval= 4.,
                            units='dBm',
                            type=types.FloatType)
        self._power_first_tone = 0.
        self._power_second_tone = 0.


        self.add_parameter('cw_frequency',
                            flags=Instrument.FLAG_GETSET,
                            units='GHz',
                            minval = 1e-4,
                            maxval= 40,
                            type=types.FloatType,
                            channels=(1, 2),
                            channel_prefix='src%d_')

        # Attention: may have to change something after changing frequency sweep
        # parameters
        self.add_parameter('frequency_start',
                            flags=Instrument.FLAG_GETSET,
                            units='GHz',
                            minval = 1e-4,
                            maxval= 40,
                            type=types.FloatType,
                            channels=(1, 2),
                            channel_prefix='src%d_')

        self.add_parameter('frequency_stop',
                            flags=Instrument.FLAG_GETSET,
                            units='GHz',
                            minval = 1e-4,
                            maxval= 40,
                            type=types.FloatType,
                            channels=(1, 2),
                            channel_prefix='src%d_')

        self.add_parameter('frequency_step',
                            flags=Instrument.FLAG_GETSET,
                            units='GHz',
                            minval = 1e-4,
                            maxval= 40,
                            type=types.FloatType,
                            channels=(1, 2),
                            channel_prefix='src%d_')

        self.add_parameter('points_freq_sweep',
                            flags=Instrument.FLAG_GETSET,
                            minval=1,
                            type=types.IntType,
                            channels=(1, 2),
                            channel_prefix='src%d_')

        self.add_parameter('total_averaging',
                            flags=Instrument.FLAG_GETSET,
                            minval = 1,
                            type=types.FloatType)

        self.add_parameter('routing_awg',
                            flags=Instrument.FLAG_GETSET,
                            type=types.DictType)
        self._awg_routing = {}
        self._awg_routing['firsttone_channel'] = firsttone_channel
        self._awg_routing['secondtone_channel'] = secondtone_channel
        self._awg_routing['board_marker'] = board_marker
        self._awg_routing['mw_marker'] = mw_marker
        # self._awg_routing['mw1_power'] = 21.
        # self._awg_routing['mw2_power'] = 5.
        # self._SSB_tone1.get_band_type() = -1
        # self._SSB_tone2.get_band_type() = -1

        self.add_parameter('temp_length_firsttone',
                            flags=Instrument.FLAG_GETSET,
                            minval = 0.,
                            maxval= 100e-6,
                            units='s',
                            type=types.FloatType)
        self._firsttone_temp_length = 4e-6

        self.add_parameter('temp_length_secondtone',
                            flags=Instrument.FLAG_GETSET,
                            minval = 0.,
                            maxval= 100e-6,
                            units='s',
                            type=types.FloatType)
        self._secondtone_temp_length = 20e-6

        self.add_parameter('temp_start_firsttone',
                            flags=Instrument.FLAG_GETSET,
                            minval = 0.,
                            maxval= 100e-6,
                            units='s',
                            type=types.FloatType)
        self._firsttone_temp_start = 100e-9

        self.add_parameter('temp_start_secondtone',
                            flags=Instrument.FLAG_GETSET,
                            minval = 0.,
                            maxval= 100e-6,
                            units='s',
                            type=types.FloatType)
        self._secondtone_temp_start = 100e-9

        self.add_parameter('marker1_width',
                            flags=Instrument.FLAG_GETSET,
                            units='s',
                            type=types.FloatType)
        self._marker1_width = 20e-6

        self.add_parameter('marker2_width',
                            flags=Instrument.FLAG_GETSET,
                            units='s',
                            type=types.FloatType)
        self._marker2_width = 45e-6

        self.add_parameter('marker1_start',
                            flags=Instrument.FLAG_GETSET,
                            units='s',
                            type=types.FloatType)
        self._marker1_start = 100e-9

        self.add_parameter('marker2_start',
                            flags=Instrument.FLAG_GETSET,
                            units='s',
                            type=types.FloatType)
        self._marker2_start = 100e-9
        ########################################################################
        # GET only
        self.add_parameter('SSB_conversion_loss',
                            flags=Instrument.FLAG_GET,
                            type=types.FloatType)
        self._SSB_conver_loss = 6.
        # it is the typical  conversion loss of a SSB

        self.add_parameter('electrical_phase_delay',
                            flags=Instrument.FLAG_GET,
                            type=types.FloatType)
        self._elec_delay = 29.8

        self.add_parameter('pulsenumber_averaging',
                            flags=Instrument.FLAG_GET,
                            minval = 1,
                            type=types.FloatType)
        self._pulsenumber_averaging = 50

        self.add_parameter('down_converted_frequency',
                            flags=Instrument.FLAG_GET,
                            units='GHz',
                            minval = 1e-4,
                            maxval= 1.,
                            type=types.FloatType)
        self._down_converted_frequency = 0.08

        self.add_parameter('mw_security_time',
                            flags=Instrument.FLAG_GET,
                            units='s',
                            minval= 0.,
                            maxval= 1.,
                            type=types.FloatType)
        self._mw_security_time = 5e-3

        # initialize the board
        self._board_samplerate = 400.
        self._board.set_samplerate(self._board_samplerate)
        self._board.set_trigger_range(1)
        self._board.set_trigger_level(0.2)
        self._board.set_trigger_delay(151.)
        acq_time = (self._firsttone_temp_length - 0.2e-6)*1e9
        acq_time = np.int(acq_time/128)*128
        # print acq_time
        self._board.set_acquisition_time(acq_time)
        self._board.set_averaging(2)

        # initialize awg
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)
        self._trigger_time = 100 # set_trigger_timer_time is in us
        self._arbitrary_waveform_generator.set_trigger_timer_time(self._trigger_time)
        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_marker_source('USER')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')
        self._arbitrary_waveform_generator.set_channels_synchronised('ON')
        
        self._awg_dict_coupling = {1:self._arbitrary_waveform_generator.set_ch1_coupling,
                                   2:self._arbitrary_waveform_generator.set_ch2_coupling,
                                   3:self._arbitrary_waveform_generator.set_ch3_coupling,
                                   4:self._arbitrary_waveform_generator.set_ch4_coupling }
        self._awg_dict_amplitude = {1:self._arbitrary_waveform_generator.set_ch1_amplitude,
                                   2:self._arbitrary_waveform_generator.set_ch2_amplitude,
                                   3:self._arbitrary_waveform_generator.set_ch3_amplitude,
                                   4:self._arbitrary_waveform_generator.set_ch4_amplitude }

        self._awg_dict_output = {1:self._arbitrary_waveform_generator.set_ch1_output,
                                   2:self._arbitrary_waveform_generator.set_ch2_output,
                                   3:self._arbitrary_waveform_generator.set_ch3_output,
                                   4:self._arbitrary_waveform_generator.set_ch4_output }

        # print self._arbitrary_waveform_generator.get_ch1_amplitude()
        for i in CHANNEL:
            self._awg_dict_coupling[i]('DC')
            self._awg_dict_amplitude[i](2)
            self._awg_dict_output[i]('OFF')
        # print self._arbitrary_waveform_generator.get_ch1_amplitude()

        self._awg_waves = {'onetone':{'binary':{1:[], 2:[], 3:[], 4:[] },
                                        'cosine':{1:[], 2:[], 3:[], 4:[] },
                                        'marker_trigger':{1:[], 2:[], 3:[], 4:[] }},
                            'twotone':{'binary':{1:[], 2:[], 3:[], 4:[] },
                                        'cosine':{1:[], 2:[], 3:[], 4:[] },
                                        'marker_trigger':{1:[], 2:[], 3:[], 4:[] }},
                            'rabi':{'binary':{1:[], 2:[], 3:[], 4:[] },
                                    'cosine':{1:[], 2:[], 3:[], 4:[] },
                                    'marker_trigger':{1:[], 2:[], 3:[], 4:[] }} }
        #initialize the mw generators
        if self._presence_mwsrc2:
            self._microwave_generator1.set_freqsweep('off')
            self._microwave_generator2.set_freqsweep('on')
            self._microwave_generator2.set_sweepmode('STEP')
            self._microwave_generator2.set_spacingfreq('lin')
            self._microwave_generator1.set_gui_update('OFF')
            self._microwave_generator2.set_gui_update('OFF')
        else:
            self._microwave_generator1.set_freqsweep('on')
            self._microwave_generator1.set_sweepmode('STEP')
            self._microwave_generator1.set_spacingfreq('lin')
            self._microwave_generator1.set_gui_update('OFF')


        self._M = 0 # number of triggers to wait to be sure that frequency has changed
        while (self._M+1)*self._arbitrary_waveform_generator.get_trigger_timer_time()*1e-6 < self.get_mw_security_time():
            self._M +=1
        ########################################################################
        #                       Functions
        ########################################################################
        self.add_function('write_onetone_pulsessequence')
        self.add_function('write_twotone_pulsessequence')
        self.add_function('display_pulses_sequence')
        # self.add_function('measure_onetone')

        self.add_function('cos')
        self.add_function('volt2bit')
        self.add_function('volt2bit_2')
        self.add_function('pulse')


    ############################################################################
    # GET_SET

    def do_get_power_first_tone(self):
        '''
        Get the power_first_tone. It gets the estimated power of the first tone after the SSB.
        '''
        return self._power_first_tone

    def do_set_power_first_tone(self, IFP):
        '''
        Set the power_first_tone. It sets the estimated power of the first tone after the SSB.
        Input:
            IFP (float): power_first_tone in dBm
        '''
        self._power_first_tone = IFP

    def do_get_power_second_tone(self):
        '''
        Get the power_second_tone. It gets the estimated power of the second tone after the SSB.
        '''
        return self._power_second_tone

    def do_set_power_second_tone(self, IFP):
        '''
        Set the power_second_tone. It sets the estimated power of the second tone after the SSB.
        Input:
            IFP (float): power_second_tone in dBm
        '''
        self._power_second_tone = IFP

    def do_get_cw_frequency(self, channel=1):
        '''
        Gets the continuous wave frequency in GHz of the microwave generator channel
        '''
        if channel == 1:
            return self._microwave_generator1.get_frequency()/1e9 + self._SSB_tone1.get_band_type()*self.get_down_converted_frequency()
        elif channel==2:
            return self._microwave_generator2.get_frequency()/1e9 + self._SSB_tone2.get_band_type()*self.get_down_converted_frequency()
        else:
            print 'Error: channel must be in (1, 2)'

    def do_set_cw_frequency(self, cwf, channel=1):
        '''
        Sets the continuous wave frequency in GHz of the microwave generator channel
        '''

        if channel == 1:
            cwf -= self._SSB_tone1.get_band_type()*self.get_down_converted_frequency()
            if cwf > self._SSB_tone1.get_freq_stop() or cwf < self._SSB_tone1.get_freq_start():
                print 'Careful! You are over the range of the SSB'

            return self._microwave_generator1.set_frequency(cwf*1e9)
        elif channel == 2:
            cwf -= self._SSB_tone2.get_band_type()*self.get_down_converted_frequency()
            if cwf > self._SSB_tone2.get_freq_stop() or cwf < self._SSB_tone2.get_freq_start():
                print 'Careful! You are over the range of the SSB'
            return self._microwave_generator2.set_frequency(cwf*1e9)
        else:
            print 'Error: channel must be in (1, 2)'

    def do_get_frequency_start(self, channel=1):
        '''
        Pb: not working function on SMB
        Get the starting frequency of the frequency sweep in GHz of the microwave generator channel
        '''
        if channel == 1:
            return self._microwave_generator1.get_startfreq() + self._SSB_tone1.get_band_type()*self.get_down_converted_frequency()
        elif channel == 2:
            return self._microwave_generator2.get_startfreq() + self._SSB_tone2.get_band_type()*self.get_down_converted_frequency()
        else:
            print 'Error: channel should be in (1, 2)'

    def do_set_frequency_start(self, freq_start, channel=1):
        '''
        Set the starting frequency of the frequency sweep in GHz of the microwave generator channel
        Input:
            freq_start (float): starting frequency in GHz
        Output:
            None
        '''
        if channel == 1:
            freq_start -= self._SSB_tone1.get_band_type()*self.get_down_converted_frequency()
            self._microwave_generator1.set_startfreq(freq_start)
            if  freq_start < self._SSB_tone1.get_freq_start():
                print 'Careful! You are over the range of the SSB'
            # number_sequence = self.get_pulsenumber_averaging()*self._microwave_generator1.get_pointsfreq()
            # self._board.set_nb_sequence(number_sequence)

        elif channel == 2:
            freq_start -= self._SSB_tone2.get_band_type()*self.get_down_converted_frequency()
            self._microwave_generator2.set_startfreq(freq_start)

            if freq_start < self._SSB_tone2.get_freq_start():
                print 'Careful! You are over the range of the SSB'
            # number_sequence = self.get_pulsenumber_averaging()*self._microwave_generator2.get_pointsfreq()
            # self._board.set_nb_sequence(number_sequence)
        else:
            print 'Error: channel should be in (1, 2)'

    def do_get_frequency_stop(self, channel =1):
        '''
        Pb: not working function on SMB
        Get the last frequency of the frequency sweep in GHz of the microwave generator channel
        '''
        if channel == 1:
            return self._microwave_generator1.get_stopfreq() + self._SSB_tone1.get_band_type()*self.get_down_converted_frequency()
        elif channel == 2:
            return self._microwave_generator2.get_stopfreq() + self._SSB_tone2.get_band_type()*self.get_down_converted_frequency()
        else:
            print 'Error: channel should be in (1, 2)'

    def do_set_frequency_stop(self, freq_stop, channel =1):
        '''
        Set the last frequency of the frequency sweep in GHz of the microwave generator channel
        Input:
            freq_stop (float): last frequency in GHz
        Output:
            None
        '''
        if channel == 1:
            freq_stop -= self._SSB_tone1.get_band_type()*self.get_down_converted_frequency()
            self._microwave_generator1.set_stopfreq(freq_stop)

            if freq_stop > self._SSB_tone1.get_freq_stop():
                print 'Careful! You are over the range of the SSB'
            # number_sequence = self.get_pulsenumber_averaging()*self._microwave_generator1.get_pointsfreq()
            # self._board.set_nb_sequence(number_sequence)
        elif channel == 2:
            freq_stop -= self._SSB_tone2.get_band_type()*self.get_down_converted_frequency()
            self._microwave_generator2.set_stopfreq(freq_stop)

            if freq_stop > self._SSB_tone2.get_freq_stop():
                print 'Careful! You are over the range of the SSB'
            # number_sequence = self.get_pulsenumber_averaging()*self._microwave_generator2.get_pointsfreq()
            # self._board.set_nb_sequence(number_sequence)
        else:
            print 'Error: channel should be in (1, 2)'

    def do_get_frequency_step(self, channel=1):
        '''
        Pb: not working function on SMB
        Get the step frequency of the frequency sweep in GHz of the microwave generator channel
        '''
        if channel == 1:
            return self._microwave_generator1.get_stepfreq()
        elif channel == 2:
            return self._microwave_generator2.get_stepfreq()
        else:
            print 'Error: channel should be in (1, 2)'

    def do_set_frequency_step(self, freq_step, channel=1):
        '''
        Set the step frequency of the frequency sweep in GHz of the microwave generator channel
        Input:
            freq_step (float): step frequency in GHz
        Output:
            None
        '''
        if channel == 1:
            self._microwave_generator1.set_stepfreq(freq_step)

            # number_sequence = self.get_pulsenumber_averaging()*self._microwave_generator1.get_pointsfreq()
            # self._board.set_nb_sequence(number_sequence)
        elif channel == 2:
            self._microwave_generator2.set_stepfreq(freq_step)
            #
            # number_sequence = self.get_pulsenumber_averaging()*self._microwave_generator2.get_pointsfreq()
            # self._board.set_nb_sequence(number_sequence)
        else:
            print 'Error: channel must be in (1,2)'

    def do_get_points_freq_sweep(self, channel=1):
        '''
        Pb: get_pointsfreq is a not working function on SMB
        Get the number of points in frequency of the frequency sweep in GHz of the microwave generator channel
        '''
        if channel == 1:
            return self._microwave_generator1.get_pointsfreq()
        elif channel == 2:
            return self._microwave_generator2.get_pointsfreq()
        else:
            print 'Error: channel must be in (1,2)'

    def do_set_points_freq_sweep(self, points, channel=1):
        '''
        Set the number of points in frequency of the frequency sweep in GHz of the microwave generator channel
        Input:
            points (int): number of points of the sweep
        Output:
            None
        '''
        if channel == 1:
            self._microwave_generator1.set_pointsfreq(points)
            # print self.get_pulsenumber_averaging(), type(self.get_pulsenumber_averaging())
            # print self._microwave_generator1.get_pointsfreq(), type(self._microwave_generator1.get_pointsfreq())
            number_sequence = np.int(self.get_pulsenumber_averaging()*points)
            self._board.set_nb_sequence(number_sequence)
        elif channel == 2:
            self._microwave_generator2.set_pointsfreq(points)

            number_sequence = np.int(self.get_pulsenumber_averaging()*points)
            self._board.set_nb_sequence(number_sequence)
        else:
            print 'Error: channel must be in (1,2)'

    def do_get_total_averaging(self):
        '''
        Get the total averaging. It is the board averaging multiply by the number of pulses averaging.
        '''
        return self._board.get_averaging()*self.get_pulsenumber_averaging()

    def do_set_total_averaging(self, average):
        '''
        Set the total averaging. It is a multiple of the number of pulses averaging.
        '''
        if average % self.get_pulsenumber_averaging() == 0:
            if np.int(average/self.get_pulsenumber_averaging()) %2  == 0:
                self._board.set_averaging(np.int(average/self.get_pulsenumber_averaging()))
                print 'Board averaging set to:', self._board.get_averaging()
                print 'Total averaging set to:', self.get_total_averaging()
            else:
                self._board.set_averaging(np.int(average/self.get_pulsenumber_averaging()))
                print 'Board averaging set to:',self._board.get_averaging()
                print 'Total averaging set to:', self.get_total_averaging()
        else:
            if np.int(average/self.get_pulsenumber_averaging()) %2  == 0:
                self._board.set_averaging(np.int(average/self.get_pulsenumber_averaging()))
                print 'Board averaging set to:', self._board.get_averaging()
                print 'Total averaging set to:', self.get_total_averaging()
            else:
                self._board.set_averaging(np.int(average/self.get_pulsenumber_averaging()))
                print 'Board averaging set to:',self._board.get_averaging()
                print 'Total averaging set to:', self.get_total_averaging()
            print 'Error: the total averaging should be a multiple of the number of pulses averaging'

    def do_get_routing_awg(self):
        '''
        Gets the awg routing map.
        '''
        return self._awg_routing

    def do_set_routing_awg(self, firsttone_channel, secondtone_channel,
        board_marker, mw_marker, mw1_ssb_bandtype, mw2_ssb_bandtype):
        '''
        Sets the awg routing map.
        Inputs:
            firsttone_channel (int): number of the first tone awg channel
            secondtone_channel (int): number of the first tone awg channel
            board_marker (int): number of the board marker
            mw_marker (int): number of the microwave marker
            # mw1_ssb_bandtype (-1, +1): the bandtype of the ssb associated to the microwave generator 1
            # mw2_ssb_bandtype (-1, +1): the bandtype of the ssb associated to the microwave generator 2
        note: for ssb_bandtype, -1 means lower side band, +1 means upper side band.
        '''
        self._awg_routing['firsttone_channel'] = firsttone_channel
        self._awg_routing['secondtone_channel'] = secondtone_channel
        self._awg_routing['board_marker'] = board_marker
        self._awg_routing['mw_marker'] = mw_marker
        # self._SSB_tone1.get_band_type() = mw1_ssb_bandtype
        # self._SSB_tone2.get_band_type() = mw2_ssb_bandtype

    def do_get_temp_length_firsttone(self):
        '''
        Gets the temporal length of the first tone pulses in s.
        '''
        return self._firsttone_temp_length

    def do_set_temp_length_firsttone(self, delta_t):
        '''
        Sets the temporal length of the first tone pulses in s.
        '''
        self._firsttone_temp_length = delta_t

        acq_time = self._firsttone_temp_length - 0.2e-6
        acq_time = np.int(1e9*acq_time/128)*128
        self._board.set_acquisition_time(acq_time) # in ns

    def do_get_temp_length_secondtone(self):
        '''
        Gets the temporal length of the second tone pulses in s.
        '''
        return self._secondtone_temp_length

    def do_set_temp_length_secondtone(self, delta_t):
        '''
        Sets the temporal length of the second tone pulses in s.
        '''
        self._secondtone_temp_length = delta_t

    def do_get_temp_start_firsttone(self):
        '''
        Gets the temporal start of the first tone pulses in s.
        '''
        return self._firsttone_temp_start

    def do_set_temp_start_firsttone(self, t0):
        '''
        Sets the temporal start of the first tone pulses in s.
        '''
        self._firsttone_temp_start = t0

    def do_get_temp_start_secondtone(self):
        '''
        Gets the temporal start of the second tone pulses in s.
        '''
        return self._secondtone_temp_start

    def do_set_temp_start_secondtone(self, t0):
        '''
        Sets the temporal start of the second tone pulses in s.
        '''
        self._secondtone_temp_start = t0

    def do_get_marker1_width(self):
        '''
        Get the marker1 width.
        Output:
            marker1_width in s: temporal width of marker 1
        '''
        return self._marker1_width

    def do_get_marker2_width(self):
        '''
        Get the marker2 width.
        Output:
            marker2_width in s: temporal width of marker 2
        '''
        return self._marker2_width

    def do_get_marker1_start(self):
        '''
        Get the marker1 start.
        Output:
            marker1_start in s: time at which to start the marker 1
        '''
        return self._marker1_start

    def do_get_marker2_start(self):
        '''
        Get the marker2 start.
        Output:
            marker2_start in s: time at which to start the marker 2
        '''
        return self._marker2_start

    def do_set_marker1_width(self, marker1_width):
        '''
        Set the marker1 width.
        Input:
            marker1_width in s: temporal width of marker 1
        '''
        self._marker1_width = marker1_width

    def do_set_marker2_width(self, marker2_width):
        '''
        Set the marker2 width.
        Input:
            marker2_width in s: temporal width of marker 2
        '''
        self._marker2_width = marker2_width

    def do_set_marker1_start(self, marker1_start):
        '''
        Set the marker1 start.
        Input:
            marker1_start in s: time at which to start the marker 1
        '''
        self._marker1_start = marker1_start

    def do_set_marker2_start(self, marker2_start):
        '''
        Set the marker2 start.
        Input:
            marker2_start in s: time at which to start the marker 2
        '''
        self._marker2_start = marker2_start

    ############################################################################
    # get_only
    def do_get_pulsenumber_averaging(self):
        '''
        Get the pulse number averaging.
        '''
        return self._pulsenumber_averaging

    def do_get_SSB_conversion_loss(self):
        '''
        Get the Single Side Band conversion loss in dB. It is an estimation.
        '''
        return self._SSB_conver_loss

    def do_get_down_converted_frequency(self):
        '''
        Get the down_converted_frequency in GHz
        '''
        return self._down_converted_frequency

    def do_get_electrical_phase_delay(self):
        '''
        Get the electrical phase delay.
        Output:
            The electrical phase delay in s due to the propagation in the wires.
        '''
        return self._elec_delay

    def do_get_mw_security_time(self):
        '''
        Get the security time to allow the microwave generator to change frequency.
        Input:
            None
        Output:
            security time in s.
        '''
        return self._mw_security_time

    ############################################################################
    #  Functions
    ############################################################################
    def write_onetone_pulsessequence(self, freq_vec, power, average, readout_channel=1, sequence_index=1):
        '''
        Putting in the awg memory the onetone pulses sequence and preparing the others instruments.
        Inputs:
            frec_vec: frequency vector in GHz of the onetone sweep
            power: power at the SSB output in dBm
            average (int): number of averaging
            readout_channel: awg channel used. Value in (1, 2, 3, 4)
            sequence_index: value in 1 to 1000
        '''
        self._awg_routing['firsttone_channel'] = readout_channel
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        # Setting the mw1 on the sweeping mode
        self._microwave_generator1.set_freqsweep('on')
        self._microwave_generator1.set_sweepmode('STEP')
        self._microwave_generator1.set_spacingfreq('lin')
        if  self._presence_mwsrc2:
            self._microwave_generator2.set_freqsweep('off')

        # Setting the sweep parameters to mw1
        self.set_src1_frequency_start(freq_vec[0])
        self.set_src1_frequency_stop(freq_vec[-1])
        self.set_src1_points_freq_sweep(len(freq_vec))

        self._freq_vec = freq_vec

        # Setting the averaging:
        self.set_total_averaging(average)

        # Computing the amplitude of the readout_pulse
        power += self._SSB_tone1.get_conversion_loss()
        amplitude = np.sqrt(2.*50.*10**((power-30.)/10.))
        print amplitude

        # Setting the starts of first tone and markers
        self.set_marker1_start(100e-9)
        self.set_temp_start_firsttone(100e-9)
        self.set_marker2_start(100e-9)

        # Creating a time array and sampling it for writing in the awg memory
        nb_samples_smb =  round(1.2*(self.get_marker2_start()+self.get_marker2_width())*\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time_smb = np.arange(nb_samples_smb)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        nb_samples =  round((self.get_marker1_start() + self.get_marker1_width()+\
                self.get_temp_start_firsttone() + self.get_temp_length_firsttone() )*\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6
        if np.min((time_smb[-1], time[-1])) > self._trigger_time*1e-6:
            print 'Timing problem?'

        # Emptying the awg memory
        self._arbitrary_waveform_generator.delete_segments()
        self._arbitrary_waveform_generator.reset()
        self._arbitrary_waveform_generator.clear_err()
        self._arbitrary_waveform_generator.set_trace_mode('SING')
        self._arbitrary_waveform_generator.delete_segments()

        # Initializing awg firsttone channel
        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)

        self._arbitrary_waveform_generator.set_clock_freq(1e3)
        self._arbitrary_waveform_generator.set_marker_source('USER')
        # Initializing the array for the ability to display the pulses sequence
        for i in CHANNEL:
            self._awg_waves['onetone']['binary'][i] = []
            self._awg_waves['onetone']['cosine'][i] = []
            self._awg_waves['onetone']['marker_trigger'][i] = []

        self._seq_list = []

        ############## writing the 3 segments ##################################
        ########### changing smb frequency part of the sequence
        segment1_c  = self.cos([0, 0, 0, 0], time_smb)
        segment1  = self.volt2bit_2(self.cos([0, 0, 0, 0], time_smb))
        # Adding the marker triggering the mw1
        segment1_b = self._arbitrary_waveform_generator.add_markers_mask(\
            self._awg_routing['mw_marker'],
            np.int(self.get_marker2_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
            np.int(self.get_marker2_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                segment1)
        segment1_m = self.pulse([self.get_marker2_start(), self.get_marker2_width(), 1], time_smb)

        # Putting the segment in the awg memory
        self._arbitrary_waveform_generator.send_waveform(segment1,
                            self._awg_routing['firsttone_channel'], 1)

        ########## waiting part of the sequence
        segment2_c  = np.zeros(16*50)
        segment2_m  = np.zeros(16*50)
        segment2_b  = self.volt2bit_2(segment2_c)

        # Putting the segment in the awg memory
        self._arbitrary_waveform_generator.send_waveform(segment2_b,
                            self._awg_routing['firsttone_channel'], 2)

        ########## reading-out part of the sequence
        p = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
            amplitude, self.get_down_converted_frequency()*1e9]
        segment3  = self.volt2bit_2(self.cos(p, time) )
        segment3_c = self.cos(p, time)

        segment3_b = self._arbitrary_waveform_generator.add_markers_mask(\
            self._awg_routing['board_marker'],
            np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
            np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
            segment3)
        segment3_m = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1], time)
        # Putting the segment in the awg memory
        self._arbitrary_waveform_generator.send_waveform(segment3,
                            self._awg_routing['firsttone_channel'], 3)

        for i in np.arange(self._M + self.get_pulsenumber_averaging() + 1):
            if i == self._M + self.get_pulsenumber_averaging():
                self._seq_list.append([1, 1, 0])
                self._awg_waves['onetone']['binary'][self._awg_routing['firsttone_channel']].append(segment1_b)
                self._awg_waves['onetone']['cosine'][self._awg_routing['firsttone_channel']].append(segment1_c)
                self._awg_waves['onetone']['marker_trigger'][self._awg_routing['firsttone_channel']].append(segment1_m)
            elif i < self._M:
                self._seq_list.append([1, 2, 0])
                self._awg_waves['onetone']['binary'][self._awg_routing['firsttone_channel']].append(segment2_b)
                self._awg_waves['onetone']['cosine'][self._awg_routing['firsttone_channel']].append(segment2_c)
                self._awg_waves['onetone']['marker_trigger'][self._awg_routing['firsttone_channel']].append(segment2_m)
            else:

                self._seq_list.append([1, 3, 0])
                self._awg_waves['onetone']['binary'][self._awg_routing['firsttone_channel']].append(segment3_b)
                self._awg_waves['onetone']['cosine'][self._awg_routing['firsttone_channel']].append(segment3_c)
                self._awg_waves['onetone']['marker_trigger'][self._awg_routing['firsttone_channel']].append(segment3_m)

        ########################################################################
        self._seq_list = np.array(self._seq_list)


        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)
        self._arbitrary_waveform_generator.set_channels_synchronised('ON')
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')
        # self._arbitrary_waveform_generator.set_m2_marker_high_1_2(1.)
        # self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, sequence_index)
        self._arbitrary_waveform_generator.sequence_select(sequence_index)

        self._arbitrary_waveform_generator.set_trigger_source('EVEN')
        self._arbitrary_waveform_generator.seq_mode('STEP')
        self._arbitrary_waveform_generator.seq_jump_source('BUS')

        self._arbitrary_waveform_generator.set_trigger_mode('NORM')
        self._arbitrary_waveform_generator.set_trigger_timer_mode('TIME')
        self._arbitrary_waveform_generator.set_run_mode('TRIG')
        self._arbitrary_waveform_generator.set_func_mode('SEQ')
        self._arbitrary_waveform_generator.set_trigger_timer_time(self._trigger_time) #in us

        # switching ON the output of the readout channel and the markers
        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('ON')

        self._microwave_generator1.set_gui_update('OFF')

    def write_twotone_pulsessequence(self, cwf, freq_vec, power_tone1, power_tone2, average,
                SSBrange='0550', readout_channel=1, excitation_channel=4, sequence_index=1):
        '''
        Putting in the awg memory the twotone pulses sequence and preparing the others instruments.
        Inputs:
            cwf [GHz]: continuous wave frequency of the first tone
            frec_vec: frequency vector in GHz of the second tone sweep
            power_tone1: power at the SSB output in dBm for first tone
            power_tone2: power at the SSB output in dBm for second tone
            average (int): number of total averaging
            readout_channel: awg channel used. Value in (1, 2, 3, 4)
            excitation_channel: awg channel used. Value in (1, 2, 3, 4)
            sequence_index: value in 1 to 1000
        '''
        self._awg_routing['firsttone_channel'] = readout_channel
        self._awg_routing['secondtone_channel'] = excitation_channel

        # Emptying the awg
        self._arbitrary_waveform_generator.reset()
        self._arbitrary_waveform_generator.clear_err()
        self._arbitrary_waveform_generator.set_trace_mode('SING')
        self._arbitrary_waveform_generator.delete_segments()

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.delete_segments()
        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.delete_segments()

        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._awg_dict_coupling[excitation_channel]('DC')
        self._awg_dict_amplitude[excitation_channel](2)

        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator2.set_gui_update('OFF')

        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(cwf)

        self._microwave_generator2.set_freqsweep('on')
        self._microwave_generator2.set_sweepmode('STEP')
        self._microwave_generator2.set_spacingfreq('lin')

        self.set_src2_frequency_start(freq_vec[0])
        self.set_src2_frequency_stop(freq_vec[-1])
        self.set_src2_points_freq_sweep(len(freq_vec))

        if SSBrange == '0550':
            self._microwave_generator2.set_power(5.)
        elif SSBrange == '4080' or SSBrange == '8012':
            self._microwave_generator2.set_power(15.)
        else:
            print 'Error: SSBrange should be 0550, 4080 or 8012'

        self._freq_vec = freq_vec
        self.set_total_averaging(average)

        power_tone1 += self._SSB_tone1.get_conversion_loss()
        power_tone2 += self._SSB_tone2.get_conversion_loss()
        amplitude_tone1 = np.sqrt(2.*50.*10**((power_tone1-30.)/10.))
        amplitude_tone2 = np.sqrt(2.*50.*10**((power_tone2-30.)/10.))
        print amplitude_tone1, amplitude_tone2

        self.set_temp_length_secondtone(20e-6)
        self.set_temp_start_firsttone(self.get_temp_start_secondtone()+self.get_temp_length_secondtone())
        self.set_marker1_start(self.get_temp_start_firsttone())
        self.set_marker2_start(100e-9)

        ########################################################################
        nb_samples_smb =  round(1.2*(self.get_marker2_start()+self.get_marker2_width())*\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time_smb = np.arange(nb_samples_smb)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        nb_samples =  round((self.get_marker1_start() + self.get_marker1_width() +\
                self.get_temp_start_firsttone() + self.get_temp_length_firsttone() +\
                self.get_temp_start_secondtone() + self.get_temp_length_secondtone()) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        if np.min((time_smb[-1], time[-1])) > self._trigger_time*1e-6:
            print 'Timing problem?'

        for i in CHANNEL:
            self._awg_waves['twotone']['binary'][i] = []
            self._awg_waves['twotone']['cosine'][i] = []
            self._awg_waves['twotone']['marker_trigger'][i] = []

        self._seq_list = []

        # Segment triggering the change of smb frequency #######################
        segment1_ro  = self.volt2bit_2(self.cos([0, 0, 0, 0], time_smb))
        segment1_ro = self._arbitrary_waveform_generator.add_markers_mask(\
            self._awg_routing['mw_marker'],
            np.int(self.get_marker2_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
            np.int(self.get_marker2_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                segment1_ro)
        segment1_ex = self.volt2bit_2(self.cos([0, 0, 0, 0], time_smb))

        # Putting the segment in AWG memory
        self._arbitrary_waveform_generator.send_waveform(segment1_ro,
                            self._awg_routing['firsttone_channel'], 1)
        self._arbitrary_waveform_generator.send_waveform(segment1_ex,
                            self._awg_routing['secondtone_channel'], 1)

        # waiting time segments ################################################
        segment2_ro  = self.volt2bit_2(np.zeros(16*50))
        segment2_ex = self.volt2bit_2(np.zeros(16*50))
        # Putting the segment in AWG memory
        self._arbitrary_waveform_generator.send_waveform(segment2_ro,
                            self._awg_routing['firsttone_channel'], 2)
        self._arbitrary_waveform_generator.send_waveform(segment2_ex,
                            self._awg_routing['secondtone_channel'], 2)

        # excitation and readout segments ######################################
        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            amplitude_tone2, self.get_down_converted_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], 3)

        p = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
            amplitude_tone1, self.get_down_converted_frequency()*1e9]
        segment3_ro  = self.volt2bit_2(self.cos(p, time))
        segment3_ro = self._arbitrary_waveform_generator.add_markers_mask(\
            self._awg_routing['board_marker'],
            np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
            np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
            segment3_ro)
        self._arbitrary_waveform_generator.send_waveform(segment3_ro,
                            self._awg_routing['firsttone_channel'], 3)

        for i in np.arange(self._M + self.get_pulsenumber_averaging() + 1):
            if i == self._M + self.get_pulsenumber_averaging():
                # Segment triggering the change of smb frequency
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment1)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment1_ex)
                self._seq_list.append([1, 1, 0])

            elif i < self._M:
                # waiting time segments
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment2_ro)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment2_ex)
                self._seq_list.append([1,2,0])
            else:
                # excitation and readout segments
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment3_ro)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment3_ex)

                self._seq_list.append([1,3,0])


        self._seq_list = np.array(self._seq_list)

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, sequence_index)
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, sequence_index)
        self._arbitrary_waveform_generator.sequence_select(sequence_index)

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)
        self._arbitrary_waveform_generator.set_channels_synchronised('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        # self._arbitrary_waveform_generator.set_m2_marker_high_1_2(1.)
        # self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)

        self._arbitrary_waveform_generator.seq_jump_source('BUS')
        self._arbitrary_waveform_generator.seq_mode('STEP')
        self._arbitrary_waveform_generator.set_trigger_mode('NORM')
        self._arbitrary_waveform_generator.set_trigger_timer_mode('TIME')
        self._arbitrary_waveform_generator.set_run_mode('TRIG')
        self._arbitrary_waveform_generator.set_func_mode('SEQ')
        self._arbitrary_waveform_generator.set_trigger_timer_time(self._trigger_time) #in us

        # switching ON the awg channels and markers
        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('ON')


        ########################################################################

    def write_Rabi_pulsessequence(self, cwf1, cwf2, power_tone1, power_tone2, average, Tr_stop,
            Tr_step, Tr_start=0., SSBrange='0550', readout_channel=1, excitation_channel=4, sequence_index=1):
        '''
        Putting in the awg memory the Rabi pulses sequence and preparing the others instruments.
        Inputs:
            cwf1 [GHz]: continuous wave frequency of the first tone
            cwf2 [GHz]: continuous wave frequency of the second tone
            power_tone1: power at the SSB output in dBm for first tone
            power_tone2: power at the SSB output in dBm for second tone
            average (int): number of total averaging
            readout_channel: awg channel used. Value in (1, 2, 3, 4)
            excitation_channel: awg channel used. Value in (1, 2, 3, 4)
            sequence_index: value in 1 to 1000
        '''

    def display_pulses_sequence(self, sequence = 'onetone', display_type='binary'):
        '''
        Display the last pulses sequence written.
        '''
        fig, ax = plt.subplots(1,1)
        if display_type == 'binary':
            if sequence in ('onetone', 'twotone', 'rabi'):
                for i in CHANNEL:
                    ax.plot( [item for sublist in self._awg_waves[sequence]['binary'][i] for item in sublist], label='ch_'+str(i))
            else:
                print 'sequence should be in (onetone, twotone, rabi)'
        else:
            if sequence in ('onetone', 'twotone', 'rabi'):
                for i in CHANNEL:
                    ax.plot( [item for sublist in self._awg_waves[sequence]['cosine'][i] for item in sublist], label='ch_'+str(i))
                    ax.plot( [item for sublist in self._awg_waves[sequence]['marker_trigger'][i] for item in sublist], label='ch_'+str(i))
            else:
                print 'sequence should be in (onetone, twotone, rabi)'
        ax.grid()
        ax.legend(loc='best')
        plt.show()

    ############################################################################
    # useful Functions
    ############################################################################
    def volt2bit(self, volt):
        """
            Return the bit code corresponding to the entered voltage value in uint16
        """
        full = 4. # in volt
        resolution = 2**14. - 1.

        return  np.array(np.round((volt + full/2.)*resolution/full, 0),
                         dtype ='uint16')

    def volt2bit_2(self, volt):
        """
            Return the bit code corresponding to the entered voltage value in uint16
        """
        full = 2. # in volt
        resolution = 2**14. - 1.

        return  np.array(np.round((volt + full/2.)*resolution/full, 0),
                         dtype ='uint16')

    def pulse(self, p, x, type='DC'):
        start, width, amplitude = p

        # from second to sample
        time_step = x[1] - x[0]
        start = int(round(start/time_step))
        width = int(round(width/time_step))

        after  = len(x) - width - start

        pulse = np.concatenate((np.zeros(start),
                                np.ones(width),
                                np.zeros(after)))

        return amplitude*pulse

    def cos(self, p, x):
        '''
        Return an array of a cosine pulse
        '''
        start, duration, amplitude, frequency = p

        # from second to sample
        time_step = x[1] - x[0]
        start = int(round(start/time_step))
        width = int(round(duration/time_step))

        after  = len(x) - width - start

        pulse = np.concatenate((np.zeros(start),
                                amplitude*np.cos(2.*np.pi*frequency*x[start:-after]),
                                np.zeros(after)))

        return pulse
