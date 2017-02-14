# Work in PROGRESS
# made by Remy Dassonneville in 2016-2017

from instrument import Instrument
import instruments
import numpy as np
import types
import logging
import ATS9360.DataTreatment as dt

# now coded in this driver
import matplotlib.pyplot as plt

CHANNEL=(1,2,3,4)

class virtual_pulsing_instrument(Instrument):
    '''
    TO DO: complete it!!!
        - write_Ramsey_pulsessequence

    This is the driver for the virtual instrument which can create a spectroscopic
    sequence pulses and measure it.

    Note: on the file instrument.py of the qutlab, in order to have a dictionary as
    input variable of a set function, we need to add the line # This line #

    _CONVERT_MAP = {
            types.IntType: int,
            types.FloatType: float,
            types.StringType: str,
            types.BooleanType: bool,
            types.TupleType: tuple,
            types.ListType: list,
            types.DictType: dict, # This line #
            np.ndarray: lambda x: x.tolist(),
    }

    Usage:
    Initialize with:
    <name> = qt.instruments.create('name', 'virtual_pulsing_instrument',
    awg='awg_name', mwsrc1='name_microwave_generator', board='board_name', ssb1 = 'ssb1_name',
    mwsrc2= 'name_microwave_generator2--if present--', ssb2 = 'ssb2_name--if present--',
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
        # if current_src != 'None':
        #     self._presence_current_src = 1
        #     self._current_source = self._instruments.get(current_src)
        #     self._current_source.set_mode('dci')
        #     self._current_source.set_channel('A')
        #     self._current_source.set_resolution('high')
        # else:
        #     self._presence_current_src = 0


        ########################################################################
        #                    parameters
        ########################################################################
        # GET_SET
        self.add_parameter('power_first_tone',
                            flags=Instrument.FLAG_GETSET,
                            minval = -50.,
                            maxval= 4.,
                            units='dBm',
                            type=types.FloatType)

        self.add_parameter('power_second_tone',
                            flags=Instrument.FLAG_GETSET,
                            minval = -50.,
                            maxval= 4.,
                            units='dBm',
                            type=types.FloatType)
        self.set_power_first_tone(0.)
        self.set_power_second_tone(0.)


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
        # self._awg_routing['firsttone_channel'] = firsttone_channel
        # self._awg_routing['secondtone_channel'] = secondtone_channel
        # self._awg_routing['board_marker'] = board_marker
        # self._awg_routing['mw_marker'] = mw_marker
        self.set_routing_awg({'firsttone_channel':firsttone_channel,
            'secondtone_channel':secondtone_channel, 'board_marker':board_marker,
            'mw_marker':mw_marker})

        self.add_parameter('awg_segmentation',
                            flags=Instrument.FLAG_GETSET,
                            type=types.DictType)
        self._segmentation = {}
        # self._segmentation['onetone'] = 1 + np.arange(3)
        # self._segmentation['twotone'] = 4 + np.arange(3)

        self.add_parameter('number_segments_memorized',
                            flags=Instrument.FLAG_GET,
                            minval= 0,
                            maxval= 32000,
                            type=types.IntType)
        # self._nb_segmt_memorized = 0

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
                            flags=Instrument.FLAG_GETSET,
                            units='GHz',
                            minval = 1e-4,
                            maxval= 1.,
                            type=types.FloatType)
        # self._down_converted_frequency =

        self.add_parameter('mw_security_time',
                            flags=Instrument.FLAG_GET,
                            units='s',
                            minval= 0.,
                            maxval= 1.,
                            type=types.FloatType)
        self._mw_security_time = 5e-3



        # initialize the board
        self._board.set_mode('CHANNEL_A')
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
        self._trigger_time = 100. # set_trigger_timer_time is in us
        self._arbitrary_waveform_generator.set_trigger_timer_time(self._trigger_time)
        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
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

        self._sequence_dict = {'onetone':1, 'twotone':2, 'rabi1':3, 'rabi2':4,
            'relaxation1':5,'relaxation2':6, 'ramsey1':7, 'ramsey2':8, 'IQ':9}
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
                                    'marker_trigger':{1:[], 2:[], 3:[], 4:[] }},
                            'relaxation': {'binary':{1:[], 2:[], 3:[], 4:[] },
                                    'cosine':{1:[], 2:[], 3:[], 4:[] },
                                    'marker_trigger':{1:[], 2:[], 3:[], 4:[] }},
                            'ramsey': {'binary':{1:[], 2:[], 3:[], 4:[] },
                                    'cosine':{1:[], 2:[], 3:[], 4:[] },
                                    'marker_trigger':{1:[], 2:[], 3:[], 4:[] }},
                            'IQ': {'binary':{1:[], 2:[], 3:[], 4:[] },
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
        self.add_function('prep_onetone')
        self.add_function('write_twotone_pulsessequence')
        self.add_function('prep_twotone')
        self.add_function('display_pulses_sequence')
        self.add_function('prep_rabi')
        self.add_function('write_Rabi_pulsessequence')
        self.add_function('prep_relaxation')
        self.add_function('write_Relaxation_pulsessequence')
        self.add_function('prep_ramsey')
        self.add_function('write_Ramsey_pulsessequence')

        self.add_function('prep_IQ')
        self.add_function('write_IQ')
        self.add_function('prep_timing')


        self.add_function('cos')
        self.add_function('volt2bit')
        self.add_function('volt2bit_2')
        self.add_function('pulse')

        self.write_onetone_pulsessequence( delete = True)
        # # self.write_twotone_pulsessequence( 0, 0)
        # # self.write_Rabi_pulsessequence( 0, 0, 20e-6, 0.1e-6, 0)
        # # self.write_Relaxation_pulsessequence( 0, 0, 1e-6, 20e-6, 0.1e-6, 0)
        # self.write_Ramsey_pulsessequence( 0, 0, 200e-9, 20e-6, 5e-6, 0)
        # self.write_IQ( 0, 4e-6)

    ############################################################################
    # GET_SET
    def do_get_awg_segmentation(self):
        '''
        Get the segmentation used for the differents sequences.
        Input:
            None
        Output:
            dictionnary
        '''
        return self._segmentation

    def do_set_awg_segmentation(self, dictio):
        '''
        Set the segmentation used for the sequence sequence_name
        Input:
        dictio (dictionnary) : \{ sequence_name1: segment_vec1, sequence_name2: segment_vec2, ...\}
            sequence_name (str): name of the sequence
            segment_vec (array of int)
        '''
        for seq_name, seg_vec in dictio.iteritems():
            self._segmentation[seq_name] = seg_vec

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

    def do_set_routing_awg(self, dictio):
        '''
        Sets the awg routing map.
        Inputs:
            dictio
            firsttone_channel (int): number of the first tone awg channel
            secondtone_channel (int): number of the first tone awg channel
            board_marker (int): number of the board marker
            mw_marker (int): number of the microwave marker
        note: for ssb_bandtype, -1 means lower side band, +1 means upper side band.
        '''
        for name, val in dictio.iteritems():
            # print name, type(name)
            # print val, type(val)

            self._awg_routing[name] = val
        # self._awg_routing['firsttone_channel'] = firsttone_channel
        # self._awg_routing['secondtone_channel'] = secondtone_channel
        # self._awg_routing['board_marker'] = board_marker
        # self._awg_routing['mw_marker'] = mw_marker
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

    def do_get_down_converted_frequency(self):
        '''
        Get the down_converted_frequency in GHz
        '''
        if np.int(self._arbitrary_waveform_generator.get_trigger_timer_time()\
            *self._SSB_tone1.get_IF_frequency()*1e3) != self._arbitrary_waveform_generator.\
            get_trigger_timer_time()*self._SSB_tone1.get_IF_frequency()*1e3:
            print 'Problem: the awg period should be a multiple of the IF period'
            print 'awg period [us]:', self._arbitrary_waveform_generator.get_trigger_timer_time()
            print 'IF period [us]:', 1e-3/self._SSB_tone1.get_IF_frequency()
        return self._SSB_tone1.get_IF_frequency()

    def do_set_down_converted_frequency(self, dcf):
        '''
        Set the down_converted_frequency in GHz
        Input:
            dcf [GHz]
        Output:
            None
        '''
        self._SSB_tone1.set_IF_frequency(dcf)


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

    def do_get_number_segments_memorized(self):
        '''
        Get the number of segments implemented in the awg memory.
        Input:
            None
        Output:
            number of segments [int]
        '''
        values = self.get_awg_segmentation().values()
        if len(values) == 0:
            return 0
        else:
            values = [item for sublist in values for item in sublist]
            return np.max(values)

    ############################################################################
    #  Functions
    ############################################################################
    def prep_onetone(self, freq_vec, average, power):
        '''
        Preparing the instruments for a onetone pulses sequence. This function do not
        write in the awg memory.
        Inputs:
            frec_vec: frequency vector in GHz of the onetone sweep
            average (int): number of averaging
            power: power at the awg output
        '''
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

        # self._freq_vec = freq_vec

        # Setting the averaging:
        self.set_total_averaging(average)
        self._microwave_generator1.set_gui_update('OFF')

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['onetone'])

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self.set_power_first_tone(power)
        amplitude = 10**((power)/10.)
        print amplitude
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude)

        processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                          self.get_down_converted_frequency()*1e9)
        self._board.measurement_initialization(processor=processus)

    def write_onetone_pulsessequence(self, delete = False):
        '''
        Putting in the awg memory the onetone pulses sequence and preparing the awg.
        Inputs:
            frec_vec: frequency vector in GHz of the onetone sweep
            average (int): number of averaging
            readout_channel: awg channel used. Value in (1, 2, 3, 4)
            sequence_index (str): onetone, twone, rabi... yet to be implemented
            delete (True or False): the option to delete or not the awg memory

        '''
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        # Computing the amplitude of the readout_pulse
        amplitude = 0.9999 # corresponds to 16382 in uint16 with volt2bit_2

        # Setting the starts of first tone and markers
        self.set_marker1_start(100e-9)
        self.set_temp_start_firsttone(100e-9)
        self.set_marker2_start(100e-9)
        self.set_temp_length_firsttone(4e-6)
        self.set_marker1_width(self.get_temp_length_firsttone())
        self.set_marker2_width(20e-6)

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

        if delete:
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}

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
                            self._awg_routing['firsttone_channel'], self.get_number_segments_memorized() + 1)

        ########## waiting part of the sequence
        segment2_c  = np.zeros(16*50)
        segment2_m  = np.zeros(16*50)
        segment2_b  = self.volt2bit_2(segment2_c)

        # Putting the segment in the awg memory
        self._arbitrary_waveform_generator.send_waveform(segment2_b,
                            self._awg_routing['firsttone_channel'], self.get_number_segments_memorized() + 2)

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
                            self._awg_routing['firsttone_channel'], self.get_number_segments_memorized() + 3)

        for i in np.arange(self._M + self.get_pulsenumber_averaging() + 1):
            if i == self._M + self.get_pulsenumber_averaging():
                self._seq_list.append([1, self.get_number_segments_memorized() + 1, 0])
                self._awg_waves['onetone']['binary'][self._awg_routing['firsttone_channel']].append(segment1_b)
                self._awg_waves['onetone']['cosine'][self._awg_routing['firsttone_channel']].append(segment1_c)
                self._awg_waves['onetone']['marker_trigger'][self._awg_routing['firsttone_channel']].append(segment1_m)
            elif i < self._M:
                self._seq_list.append([1, self.get_number_segments_memorized() + 2, 0])
                self._awg_waves['onetone']['binary'][self._awg_routing['firsttone_channel']].append(segment2_b)
                self._awg_waves['onetone']['cosine'][self._awg_routing['firsttone_channel']].append(segment2_c)
                self._awg_waves['onetone']['marker_trigger'][self._awg_routing['firsttone_channel']].append(segment2_m)
            else:

                self._seq_list.append([1, self.get_number_segments_memorized() + 3, 0])
                self._awg_waves['onetone']['binary'][self._awg_routing['firsttone_channel']].append(segment3_b)
                self._awg_waves['onetone']['cosine'][self._awg_routing['firsttone_channel']].append(segment3_c)
                self._awg_waves['onetone']['marker_trigger'][self._awg_routing['firsttone_channel']].append(segment3_m)

        ########################################################################
        self._seq_list = np.array(self._seq_list)

        self.set_awg_segmentation({'onetone': self.get_number_segments_memorized() + 1 + np.arange(3)} )

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)
        self._arbitrary_waveform_generator.set_channels_synchronised('ON')
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, self._sequence_dict['onetone'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['onetone'])

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

    def prep_twotone(self, cwf, freq_vec, average, power_tone1, power_tone2):
        '''
        Preparing the instruments for a twotone pulses sequence. This function do not
        write in the awg memory.
        Inputs:
            cwf [GHz]: continuous wave frequency of the first tone
            frec_vec: frequency vector in GHz of the second tone sweep
            average (int): number of total averaging
        '''
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

        self._microwave_generator2.set_power(self._SSB_tone2.get_LO_power())

        self.set_total_averaging(average)

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['twotone'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['twotone'])

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)
        self.set_power_second_tone(power_tone2)
        amplitude2 = 10**((power_tone2)/10.)
        print amplitude1, amplitude2
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)

        processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                          self.get_down_converted_frequency()*1e9)
        self._board.measurement_initialization(processor=processus)

    def write_twotone_pulsessequence(self, delete = False):
        '''
        Putting in the awg memory the twotone pulses sequence and preparing the others instruments.
        Inputs:
            delete: True or False

        '''

        if delete:
            # Emptying the awg
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}

        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')

        # self.set_power_first_tone(power_tone1)
        # power_tone1 += self._SSB_tone1.get_conversion_loss()
        # self.set_power_second_tone(power_tone2)
        # power_tone2 += self._SSB_tone2.get_conversion_loss()
        # amplitude_tone1 = np.sqrt(2.*50.*10**((power_tone1-30.)/10.))
        # amplitude_tone2 = np.sqrt(2.*50.*10**((power_tone2-30.)/10.))
        # print amplitude_tone1, amplitude_tone2
        amplitude1 = 0.9999
        amplitude2 = 0.9999

        self.set_temp_length_secondtone(20e-6)
        self.set_temp_start_secondtone(100e-9)
        self.set_temp_start_firsttone(self.get_temp_start_secondtone()+self.get_temp_length_secondtone())
        self.set_temp_length_firsttone(4e-6)
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
                            self._awg_routing['firsttone_channel'], self.get_number_segments_memorized() + 1)
        self._arbitrary_waveform_generator.send_waveform(segment1_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 1)

        # waiting time segments ################################################
        segment2_ro  = self.volt2bit_2(np.zeros(16*50))
        segment2_ex = self.volt2bit_2(np.zeros(16*50))
        # Putting the segment in AWG memory
        self._arbitrary_waveform_generator.send_waveform(segment2_ro,
                            self._awg_routing['firsttone_channel'], self.get_number_segments_memorized() + 2)
        self._arbitrary_waveform_generator.send_waveform(segment2_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 2)

        # excitation and readout segments ######################################
        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            amplitude_tone2, self.get_down_converted_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 3)

        p = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
            amplitude_tone1, self.get_down_converted_frequency()*1e9]
        segment3_ro  = self.volt2bit_2(self.cos(p, time))
        segment3_ro = self._arbitrary_waveform_generator.add_markers_mask(\
            self._awg_routing['board_marker'],
            np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
            np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
            segment3_ro)
        self._arbitrary_waveform_generator.send_waveform(segment3_ro,
                            self._awg_routing['firsttone_channel'], self.get_number_segments_memorized() + 3)

        for i in np.arange(self._M + self.get_pulsenumber_averaging() + 1):
            if i == self._M + self.get_pulsenumber_averaging():
                # Segment triggering the change of smb frequency
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment1_ro)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment1_ex)
                self._seq_list.append([1, self.get_number_segments_memorized() + 1, 0])

            elif i < self._M:
                # waiting time segments
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment2_ro)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment2_ex)
                self._seq_list.append([1, self.get_number_segments_memorized() + 2, 0])
            else:
                # excitation and readout segments
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment3_ro)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment3_ex)

                self._seq_list.append([1, self.get_number_segments_memorized() + 3, 0])


        self._seq_list = np.array(self._seq_list)
        self.set_awg_segmentation({'twotone': self.get_number_segments_memorized() + 1 + np.arange(3)} )

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, self._sequence_dict['twotone'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, self._sequence_dict['twotone'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['twotone'])

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)
        self._arbitrary_waveform_generator.set_channels_synchronised('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self._arbitrary_waveform_generator.set_m2_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)

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

    def prep_rabi(self, cwf1, cwf2, average, nb_sequences, power_tone1, power_tone2):
        '''
        Preparing the instruments for a Rabi pulses sequence. This function do not
        write in the awg memory.
        Inputs:
            cwf1 [GHz]: continuous wave frequency of the first tone
            cwf2 [GHz]: continuous wave frequency of the second tone
            average (int): number of total averaging
        '''
        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator2.set_gui_update('OFF')

        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(cwf1)
        self._microwave_generator2.set_freqsweep('off')
        self.set_src2_cw_frequency(cwf2)

        self._microwave_generator2.set_power(self._SSB_tone2.get_LO_power())
        self._board.set_averaging(average)
        self._board.set_nb_sequence(nb_sequences)

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['rabi1'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['rabi2'])

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)
        self.set_power_second_tone(power_tone2)
        amplitude2 = 10**((power_tone2)/10.)
        print amplitude1, amplitude2
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)

        processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                          self.get_down_converted_frequency()*1e9)
        self._board.measurement_initialization(processor=processus)

    def write_Rabi_pulsessequence(self, Tr_stop, Tr_step, Tr_start=0., delete=False):
        '''
        Putting in the awg memory the Rabi pulses sequence and preparing the others instruments.
        Inputs:

        '''
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')

        if delete:
            # Emptying the awg
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')

        # self.set_power_first_tone(power_tone1)
        # power_tone1 += self._SSB_tone1.get_conversion_loss()
        # self.set_power_second_tone(power_tone2)
        # power_tone2 += self._SSB_tone2.get_conversion_loss()
        # amplitude_tone1 = np.sqrt(2.*50.*10**((power_tone1-30.)/10.))
        # amplitude_tone2 = np.sqrt(2.*50.*10**((power_tone2-30.)/10.))
        # print amplitude_tone1, amplitude_tone2
        amplitude_tone1 = 0.9999
        amplitude_tone2 = 0.9999

        self.set_temp_start_secondtone(Tr_stop + Tr_step  - Tr_start)
        self.set_temp_length_secondtone(Tr_start )
        self.set_temp_start_firsttone(self.get_temp_start_secondtone() + self.get_temp_length_secondtone() )
        self.set_temp_length_firsttone(4e-6)
        self.set_marker1_start(self.get_temp_start_firsttone())
        self.set_marker1_width(self.get_temp_length_firsttone())

        # print self.get_marker1_start()
        # print self.get_marker1_width()

        nb_samples1 =  round(( self.get_temp_start_firsttone() + \
                np.max(self.get_temp_length_firsttone() +self.get_marker1_width()) ) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples1)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        for ch in CHANNEL:
            self._awg_waves['rabi']['binary'][ch] = []
            self._awg_waves['rabi']['cosine'][ch] = []
            self._awg_waves['rabi']['marker_trigger'][ch] = []

        self._seq_list1 = []
        self._seq_list2 = []
        N = len(np.arange(Tr_start, Tr_stop, Tr_step))

        p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                amplitude_tone1, self.get_down_converted_frequency()*1e9]

        wave_ro_cos = self.cos(p1, time1)

        wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
        wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                    self._awg_routing['board_marker'],
                    np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    wave_pulse_read_out)
        self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
            self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() + 1)

        wave_ro_marker = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1], time1)

        for i in np.arange(N):
            nb_samples2 =  round(1.1*( self.get_temp_start_secondtone() + self.get_temp_length_secondtone()  ) *\
                    self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
            time2 = np.arange(nb_samples2)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

            if i>0:
                self.set_temp_start_secondtone(self.get_temp_start_secondtone() - Tr_step)
                self.set_temp_length_secondtone(self.get_temp_length_secondtone() + Tr_step)

            p2=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

            qb_ex_cos = self.cos(p2, time2)
            qubit_excitation = self.volt2bit_2(qb_ex_cos)
            self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
                self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + i + 2)

            self._awg_waves['rabi']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
            self._awg_waves['rabi']['binary'][self._awg_routing['secondtone_channel']].append(qubit_excitation)
            self._awg_waves['rabi']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
            self._awg_waves['rabi']['cosine'][self._awg_routing['secondtone_channel']].append(qb_ex_cos)
            self._awg_waves['rabi']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + i + 2, 0])

        self._seq_list1 = np.array(self._seq_list1)
        self._seq_list2 = np.array(self._seq_list2)
        self.set_awg_segmentation({'rabi': self.get_number_segments_memorized() + 1 + 1 + np.arange(N)} )
        # self.set_awg_segmentation({'rabi2': self.get_number_segments_memorized() + 1 + np.arange(N)} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        self._arbitrary_waveform_generator.set_channels_synchronised('ON')


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list1, self._sequence_dict['rabi1'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list2, self._sequence_dict['rabi2'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['rabi2'])

        self._arbitrary_waveform_generator.set_trigger_source('EVEN')


        self._arbitrary_waveform_generator.seq_jump_source('BUS')
        self._arbitrary_waveform_generator.seq_mode('STEP')
        self._arbitrary_waveform_generator.set_trigger_mode('NORM')
        self._arbitrary_waveform_generator.set_trigger_timer_mode('TIME')
        self._arbitrary_waveform_generator.set_run_mode('TRIG')
        self._arbitrary_waveform_generator.set_func_mode('SEQ')
        self._arbitrary_waveform_generator.set_trigger_timer_time(self._trigger_time)

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')


        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')

    def prep_relaxation(self, cwf1, cwf2, average, nb_sequences, power_tone1, power_tone2):
        '''
        Preparing the instruments for a Relaxation pulses sequence. This function do not
        write in the awg memory.
        Inputs:
            cwf1 [GHz]: continuous wave frequency of the first tone
            cwf2 [GHz]: continuous wave frequency of the second tone
            average (int): number of total averaging
        '''
        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator2.set_gui_update('OFF')

        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(cwf1)
        self._microwave_generator2.set_freqsweep('off')
        self.set_src2_cw_frequency(cwf2)

        self._microwave_generator2.set_power(self._SSB_tone2.get_LO_power())
        self._board.set_averaging(average)
        self._board.set_nb_sequence(nb_sequences)

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['relaxation1'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['relaxation2'])

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)
        self.set_power_second_tone(power_tone2)
        amplitude2 = 10**((power_tone2)/10.)
        print amplitude1, amplitude2
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)

        processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                          self.get_down_converted_frequency()*1e9)
        self._board.measurement_initialization(processor=processus)

    def write_Relaxation_pulsessequence(self, t_pi, t_wait_stop, t_wait_step, t_wait_start, delete=False):
        '''
        Putting in the awg memory the Relaxation pulses sequence and preparing the others instruments.
        Inputs:
            t_pi [s]:
            t_wait_stop [s]:
            t_wait_step [s]:
            t_wait_start [s]:
        '''
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')

        if delete:
            # Emptying the awg
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')

        # self.set_power_first_tone(power_tone1)
        # power_tone1 += self._SSB_tone1.get_conversion_loss()
        # self.set_power_second_tone(power_tone2)
        # power_tone2 += self._SSB_tone2.get_conversion_loss()
        # amplitude_tone1 = np.sqrt(2.*50.*10**((power_tone1-30.)/10.))
        # amplitude_tone2 = np.sqrt(2.*50.*10**((power_tone2-30.)/10.))
        # print amplitude_tone1, amplitude_tone2
        amplitude_tone1 = 0.9999
        amplitude_tone2 = 0.9999

        self.set_temp_start_secondtone(t_wait_stop + t_wait_step - t_wait_start+t_pi)
        self.set_temp_length_secondtone(t_pi)
        self.set_temp_start_firsttone(self.get_temp_start_secondtone() + self.get_temp_length_secondtone() + t_wait_start )
        self.set_temp_length_firsttone(4e-6)
        self.set_marker1_start(self.get_temp_start_firsttone())
        self.set_marker1_width(self.get_temp_length_firsttone())

        nb_samples1 =  round((self.get_temp_start_firsttone() \
                + np.max(self.get_temp_length_firsttone() + self.get_marker1_width()) ) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples1)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        for ch in CHANNEL:
            self._awg_waves['relaxation']['binary'][ch] = []
            self._awg_waves['relaxation']['cosine'][ch] = []
            self._awg_waves['relaxation']['marker_trigger'][ch] = []

        self._seq_list1 = []
        self._seq_list2 = []
        N = len(np.arange(t_wait_start, t_wait_stop, t_wait_step))

        p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                amplitude_tone1, self.get_down_converted_frequency()*1e9]
        wave_ro_cos = self.cos(p1, time1)

        wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
        wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                    self._awg_routing['board_marker'],
                    np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    wave_pulse_read_out)
        self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
            self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() + 1)

        wave_ro_marker = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1], time1)

        for i in np.arange(N):
            p2=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

            nb_samples2 =  round(1.1*(self.get_temp_start_secondtone() \
                    + self.get_temp_length_secondtone()  ) *\
                    self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
            time2 = np.arange(nb_samples2)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6
            self.set_temp_start_secondtone(self.get_temp_start_secondtone() - t_wait_step)


            qb_ex_cos = self.cos(p2, time2)
            qubit_excitation = self.volt2bit_2(qb_ex_cos)
            self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
                self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + i + 2)

            self._awg_waves['relaxation']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
            self._awg_waves['relaxation']['binary'][self._awg_routing['secondtone_channel']].append(qubit_excitation)
            self._awg_waves['relaxation']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
            self._awg_waves['relaxation']['cosine'][self._awg_routing['secondtone_channel']].append(qb_ex_cos)
            self._awg_waves['relaxation']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)

            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + i + 2, 0])

        self._seq_list1 = np.array(self._seq_list1)
        self._seq_list2 = np.array(self._seq_list2)

        self.set_awg_segmentation({'relaxation': self.get_number_segments_memorized() + 1+1 + np.arange(N)} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        self._arbitrary_waveform_generator.set_channels_synchronised('ON')


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list1, self._sequence_dict['relaxation1'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list2, self._sequence_dict['relaxation2'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['relaxation2'])

        self._arbitrary_waveform_generator.set_trigger_source('EVEN')


        self._arbitrary_waveform_generator.seq_jump_source('BUS')
        self._arbitrary_waveform_generator.seq_mode('STEP')
        self._arbitrary_waveform_generator.set_trigger_mode('NORM')
        self._arbitrary_waveform_generator.set_trigger_timer_mode('TIME')
        self._arbitrary_waveform_generator.set_run_mode('TRIG')
        self._arbitrary_waveform_generator.set_func_mode('SEQ')
        self._arbitrary_waveform_generator.set_trigger_timer_time(self._trigger_time)

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')


        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')

    def prep_ramsey(self, cwf1, cwf2, average, nb_sequences, power_tone1, power_tone2):
        '''
        Preparing the instruments for a Ramsey pulses sequence. This function do not
        write in the awg memory.
        Inputs:
            cwf1 [GHz]: continuous wave frequency of the first tone
            cwf2 [GHz]: continuous wave frequency of the second tone
            average (int): number of total averaging
        '''
        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator2.set_gui_update('OFF')

        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(cwf1)
        self._microwave_generator2.set_freqsweep('off')
        self.set_src2_cw_frequency(cwf2)

        self._microwave_generator2.set_power(self._SSB_tone2.get_LO_power())
        self._board.set_averaging(average)
        self._board.set_nb_sequence(nb_sequences)

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['ramsey1'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['ramsey2'])

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)
        self.set_power_second_tone(power_tone2)
        amplitude2 = 10**((power_tone2)/10.)
        print amplitude1, amplitude2
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)

        processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                          self.get_down_converted_frequency()*1e9)
        self._board.measurement_initialization(processor=processus)

    def write_Ramsey_pulsessequence(self, t_pi_o2, t_wait_stop, t_wait_step, t_wait_start, delete=False):
        '''
        Putting in the awg memory the Ramsey pulses sequence and preparing the others instruments.
        Inputs:
            t_pi_o2 [s]:
            t_wait_stop [s]:
            t_wait_step [s]:
            t_wait_start [s]:
        '''
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')

        if delete:
            # Emptying the awg
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')

        # self.set_power_first_tone(power_tone1)
        # power_tone1 += self._SSB_tone1.get_conversion_loss()
        # self.set_power_second_tone(power_tone2)
        # power_tone2 += self._SSB_tone2.get_conversion_loss()
        # amplitude_tone1 = np.sqrt(2.*50.*10**((power_tone1-30.)/10.))
        # amplitude_tone2 = np.sqrt(2.*50.*10**((power_tone2-30.)/10.))
        # print amplitude_tone1, amplitude_tone2
        amplitude_tone1 = 0.9999
        amplitude_tone2 = 0.9999

        self.set_temp_start_secondtone(t_wait_stop + t_wait_step - t_wait_start)
        self.set_temp_length_secondtone(t_pi_o2)
        self.set_temp_start_firsttone(self.get_temp_start_secondtone() + 2*self.get_temp_length_secondtone() + t_wait_start )
        self.set_temp_length_firsttone(4e-6)
        self.set_marker1_start(self.get_temp_start_firsttone())
        self.set_marker1_width(self.get_temp_length_firsttone())

        nb_samples =  round((self.get_temp_start_firsttone() \
                + self.get_temp_length_firsttone() + self.get_marker1_width() ) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        for ch in CHANNEL:
            self._awg_waves['ramsey']['binary'][ch] = []
            self._awg_waves['ramsey']['cosine'][ch] = []
            self._awg_waves['ramsey']['marker_trigger'][ch] = []

        self._seq_list1 = []
        self._seq_list2 = []


        N = len(np.arange(t_wait_start, t_wait_stop, t_wait_step))
        p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                amplitude_tone1, self.get_down_converted_frequency()*1e9]
        wave_ro_cos = self.cos(p1, time)

        wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
        wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                    self._awg_routing['board_marker'],
                    np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    wave_pulse_read_out)
        self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
            self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() + 1)

        wave_ro_marker = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1], time)

        for i in np.arange(N):
            pex1=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]
            pex2=[self.get_temp_start_firsttone() - t_pi_o2, self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

            self.set_temp_start_secondtone(self.get_temp_start_secondtone() - t_wait_step)

            qb_ex_cos = self.cos(pex1, time) + self.cos(pex2, time)
            qubit_excitation = self.volt2bit_2(qb_ex_cos)
            self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
                self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + i + 1)

            self._awg_waves['ramsey']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
            self._awg_waves['ramsey']['binary'][self._awg_routing['secondtone_channel']].append(qubit_excitation)
            self._awg_waves['ramsey']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
            self._awg_waves['ramsey']['cosine'][self._awg_routing['secondtone_channel']].append(qb_ex_cos)
            self._awg_waves['ramsey']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)

            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + i + 2, 0])

        self._seq_list2 = np.array(self._seq_list2)
        self._seq_list1 = np.array(self._seq_list1)

        self.set_awg_segmentation({'ramsey': self.get_number_segments_memorized() + 1+1 + np.arange(N)} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        self._arbitrary_waveform_generator.set_channels_synchronised('ON')


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list1, self._sequence_dict['ramsey1'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list2, self._sequence_dict['ramsey2'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['ramsey2'])

        self._arbitrary_waveform_generator.set_trigger_source('EVEN')


        self._arbitrary_waveform_generator.seq_jump_source('BUS')
        self._arbitrary_waveform_generator.seq_mode('STEP')
        self._arbitrary_waveform_generator.set_trigger_mode('NORM')
        self._arbitrary_waveform_generator.set_trigger_timer_mode('TIME')
        self._arbitrary_waveform_generator.set_run_mode('TRIG')
        self._arbitrary_waveform_generator.set_func_mode('SEQ')
        self._arbitrary_waveform_generator.set_trigger_timer_time(self._trigger_time)

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')


        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')

    def prep_IQ(self, cwf1, counts, power_tone1, cwf2='None', power_tone2 = 'None'):
        '''
        Preparing the instruments for a IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        This function do not write in the awg memory.
        Inputs:
            cwf1 [GHz]: continuous wave frequency of the first tone
            cwf2 [GHz]: continuous wave frequency of the second tone if not None
            counts (int): number of repetitions to make the histograms
        '''
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(cwf1)
        self._board.set_nb_sequence(100)
        self._board.set_averaging(counts)
        print self._board.get_averaging()


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ'])
        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        if cwf2 != 'None':
            self._microwave_generator2.set_gui_update('OFF')
            self._microwave_generator2.set_freqsweep('off')
            self.set_src2_cw_frequency(cwf2)
            self._microwave_generator2.set_power(self._SSB_tone2.get_LO_power())


            self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
            self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ'])
            self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')

        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)
        self.set_power_second_tone(power_tone2)
        amplitude2 = 10**((power_tone2)/10.)
        print amplitude1, amplitude2
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)

        processus = dt.RealImag_raw(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                          self.get_down_converted_frequency()*1e9)
        self._board.measurement_initialization(processor=processus)

    def write_IQ(self, t1, t2=0., type='onetone', delete=False):
        '''
        Putting in the awg memory the IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        Inputs:
            type (str): onetone or twotone
            power_tone1: power at the SSB output in dBm for first tone
            power_tone2: power at the SSB output in dBm for second tone
            t1 [s]: time length of firsttone
            t2 [s]: time length of secondtone
        '''
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')
        if delete:
            # Emptying the awg
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')

        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        # self.set_power_first_tone(power_tone1)
        # power_tone1 += self._SSB_tone1.get_conversion_loss()
        # self.set_power_second_tone(power_tone2)
        # power_tone2 += self._SSB_tone2.get_conversion_loss()
        # amplitude_tone1 = np.sqrt(2.*50.*10**((power_tone1-30.)/10.))
        # amplitude_tone2 = np.sqrt(2.*50.*10**((power_tone2-30.)/10.))
        # print amplitude_tone1, amplitude_tone2
        amplitude_tone1 = 0.9999
        amplitude_tone2 = 0.9999

        for ch in CHANNEL:
            self._awg_waves['IQ']['binary'][ch] = []
            self._awg_waves['IQ']['cosine'][ch] = []
            self._awg_waves['IQ']['marker_trigger'][ch] = []

        self._seq_list = []

        if type == 'onetone':
            self.set_temp_start_firsttone(100e-9 )
            self.set_temp_length_firsttone(t1)
            self.set_marker1_start(self.get_temp_start_firsttone())
            self.set_marker1_width(self.get_temp_length_firsttone())

        elif type == 'twotone':
            self.set_temp_start_secondtone(100e-9)
            self.set_temp_length_secondtone(t2)
            self.set_temp_start_firsttone(self.get_temp_start_secondtone() + self.get_temp_length_secondtone())
            self.set_temp_length_firsttone(t1)
            self.set_marker1_start(self.get_temp_start_firsttone())
            self.set_marker1_width(self.get_temp_length_firsttone())

        else:
            print 'problem with type'

        nb_samples =  round(1.1*(self.get_temp_start_firsttone() \
                + self.get_temp_length_firsttone() ) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        print time[-1]
        p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                amplitude_tone1, self.get_down_converted_frequency()*1e9]
        wave_ro_cos = self.cos(p1, time)

        wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
        wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                    self._awg_routing['board_marker'],
                    np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    wave_pulse_read_out)

        self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
            self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() + 1)

        wave_ro_marker = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1], time)

        if type == 'twotone':
            pex1=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]
            qb_ex_cos = self.cos(pex1, time)
            qubit_excitation = self.volt2bit_2(qb_ex_cos)
            self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
                self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + 1)

            self._awg_waves['IQ']['binary'][self._awg_routing['secondtone_channel']].append(qubit_excitation)
            self._awg_waves['IQ']['cosine'][self._awg_routing['secondtone_channel']].append(qb_ex_cos)

        self._awg_waves['IQ']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
        self._awg_waves['IQ']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
        self._awg_waves['IQ']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)

        # for i in np.arange(1e4):
        self._seq_list.append([1, self.get_number_segments_memorized() + 1, 0])

        self._seq_list= np.array(self._seq_list)

        self.set_awg_segmentation({'IQ': self.get_number_segments_memorized() + 1 + np.arange(1)} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        self._arbitrary_waveform_generator.set_channels_synchronised('ON')


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, self._sequence_dict['IQ'])

        if type == 'twotone':
            self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
            self._arbitrary_waveform_generator.send_seq(self._seq_list, self._sequence_dict['IQ'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ'])

        self._arbitrary_waveform_generator.set_trigger_source('EVEN')
        self._arbitrary_waveform_generator.seq_jump_source('BUS')
        self._arbitrary_waveform_generator.seq_mode('STEP')
        self._arbitrary_waveform_generator.set_trigger_mode('NORM')
        self._arbitrary_waveform_generator.set_trigger_timer_mode('TIME')
        self._arbitrary_waveform_generator.set_run_mode('TRIG')
        self._arbitrary_waveform_generator.set_func_mode('SEQ')
        self._arbitrary_waveform_generator.set_trigger_timer_time(self._trigger_time)

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
        if type == 'twotone':
            self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')

        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')

    def prep_timing(self, cwf1, average, power_tone1):
        '''
        Preparing the instruments for a timing measurement.
        This function do not write in the awg memory. You need to use write_IQ with
        onetone to test.
        Inputs:
            cwf1 [GHz]: continuous wave frequency of the first tone
            average (int): number of averaging of the V(t) curve.
        '''
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(cwf1)
        self._board.set_nb_sequence(100)
        self._board.set_averaging(average)
        print self._board.get_averaging()


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ'])
        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)
        print amplitude1
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)

        processus = dt.Average()
        self._board.measurement_initialization(processor=processus)

    ############################################################################
    def display_pulses_sequence(self, sequence = 'onetone', display_type='binary'):
        '''
        Display the last pulses sequence written.
        '''
        fig, ax = plt.subplots(1,1)
        if display_type == 'binary':
            if sequence in ('onetone', 'twotone', 'rabi', 'relaxation', 'ramsey', 'IQ'):
                for i in CHANNEL:
                    ax.plot( [item for sublist in self._awg_waves[sequence]['binary'][i] for item in sublist], label='ch_'+str(i))
            else:
                print 'sequence should be in (onetone, twotone, rabi)'
        else:
            ax.set_ylim(-2.1, 2.1)
            if sequence in ('onetone', 'twotone', 'rabi', 'relaxation', 'ramsey', 'IQ'):
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
