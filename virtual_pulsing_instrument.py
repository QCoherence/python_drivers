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
import time as TIME


import multiprocessing as mp

# from ATS9360 import atsapi as ats
# from ATS9360.DataAcquisition import DataAcquisition
# data_acquisition = DataAcquisition()
# import ATS9360_NPT
CHANNEL=(1,2,3,4)

class virtual_pulsing_instrument(Instrument):
    '''
    TO DO: complete it!!!
    Write a cleaner version.
    Add a parameter homodyne/heterodyne measurement

    This is the driver for the virtual instrument which can create a some
    pulses sequence and measure it.

    ############################################################################
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
    ############################################################################

    Usage:
    Initialize with:
    <name> = qt.instruments.create('name', 'virtual_pulsing_instrument',
    awg='awg_name', mwsrc1='name_microwave_generator', board='board_name', ssb1 = 'ssb1_name',
    mwsrc2= 'name_microwave_generator2--if present--', ssb2 = 'ssb2_name--if present--',
    mwsrc3= 'name_microwave_generator3--if present--',
    current_src='name_current_source--if present--' )
    '''

    def __init__(self, name, awg, mwsrc1, board, ssb1, mwsrc2 = 'None', ssb2= 'None', mwsrc3 = 'None', ssb3='None',
                    firsttone_channel=1, secondtone_channel=4,thirdtone_channel=3, board_marker= 1, mw_marker=2):
        '''
        Initialize the virtual instrument

            Input:
                - name: Name of the virtual instruments
                - awg: Name given to an arbitrary waveform generator
                - mwsrc1: Name given to the first microwave_generator
                - ssb1: Name given to the first virtual ssb
                - board: Name given to the acquisition card
                - mwsrc2: Name given to the second microwave_generator
                - ssb2: Name given to the second virtual ssb
                - mwsrc3: Name given to the third microwave_generator
                - ssb3: Name given to the third virtual ssb
                - current_src: Name given to the current source
                - firsttone_channel, secondtone_channel: channel of the awg for
                first or second tone
                - board_marker, mw_marker: number of the marker for the triggering
                of the board or the microwave
            Output:
                None
        '''
        Instrument.__init__(self, name, tags=['virtual'])

        # Import instruments
        self._instruments = instruments.get_instruments()

        self._arbitrary_waveform_generator = self._instruments.get(awg)
        self._SSB_tone1 = self._instruments.get(ssb1)

        self._microwave_generator1 = self._instruments.get(mwsrc1)
        self._microwave_generator1.set_power(18.)         # microwave generator 1 is used for readout
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

        # if we import the third microwave generator or not
        if mwsrc3 != 'None':
            self._presence_mwsrc3 = 1
            self._microwave_generator3 = self._instruments.get(mwsrc3)
            # self._microwave_generator3.set_power(5)
            self._microwave_generator3.set_status('ON')
        else:
            self._presence_mwsrc3 = 0

        # if we import the second ssb or not
        if ssb2 != 'None':
            self._presence_ssb2 = 1
            self._SSB_tone2 = self._instruments.get(ssb2)
        else:
            self._presence_ssb2 = 0

        # if we import the thrid ssb or not
        if ssb3 != 'None':
            self._presence_ssb3 = 1
            self._SSB_tone3 = self._instruments.get(ssb3)
        else:
            self._presence_ssb3 = 0

        ########################################################################
        #                    parameters
        ########################################################################
        self.add_parameter('measurement_type',
                            flags = Instrument.FLAG_GETSET,
                            type = types.StringType,
                            option_list = ['homodyne', 'heterodyne'])
        self.set_measurement_type('homodyne')

        self.add_parameter('board_averaging',
                            flags=Instrument.FLAG_GETSET,
                            minval = 1,
                            type=types.FloatType)
        self.add_parameter('board_flag',
                        type        = types.IntType,
                        option_list = (0, 1),
                        flags       = Instrument.FLAG_GETSET )
        self.set_board_flag(0)

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
        self.add_parameter('power_third_tone',
                            flags=Instrument.FLAG_GETSET,
                            minval = -50.,
                            maxval= 4.,
                            units='dBm',
                            type=types.FloatType)
        self.add_parameter('cw_frequency',
                            flags=Instrument.FLAG_GETSET,
                            units='GHz',
                            minval = 1e-4,
                            maxval= 40,
                            type=types.FloatType,
                            channels=(1, 2, 3),
                            channel_prefix='src%d_')

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

        self.add_parameter('awg_segmentation',
                            flags=Instrument.FLAG_GETSET,
                            type=types.DictType)

        self.add_parameter('number_segments_memorized',
                            flags=Instrument.FLAG_GET,
                            minval= 0,
                            maxval= 32000,
                            type=types.IntType)

        self.add_parameter('temp_length_firsttone',
                            flags=Instrument.FLAG_GETSET,
                            minval = 0.,
                            maxval= 100e-6,
                            units='s',
                            type=types.FloatType)

        self.add_parameter('temp_length_secondtone',
                            flags=Instrument.FLAG_GETSET,
                            minval = 0.,
                            maxval= 100e-6,
                            units='s',
                            type=types.FloatType)
        self.add_parameter('temp_length_thirdtone',
                            flags=Instrument.FLAG_GETSET,
                            minval = 0.,
                            maxval= 100e-6,
                            units='s',
                            type=types.FloatType)
        self.add_parameter('temp_start_firsttone',
                            flags=Instrument.FLAG_GETSET,
                            minval = 0.,
                            maxval= 100e-6,
                            units='s',
                            type=types.FloatType)
        self.add_parameter('temp_start_secondtone',
                            flags=Instrument.FLAG_GETSET,
                            minval = 0.,
                            maxval= 100e-6,
                            units='s',
                            type=types.FloatType)
        self.add_parameter('temp_start_thirdtone',
                            flags=Instrument.FLAG_GETSET,
                            minval = 0.,
                            maxval= 100e-6,
                            units='s',
                            type=types.FloatType)
        self.add_parameter('marker1_width',
                            flags=Instrument.FLAG_GETSET,
                            units='s',
                            type=types.FloatType)
        self.add_parameter('marker2_width',
                            flags=Instrument.FLAG_GETSET,
                            units='s',
                            type=types.FloatType)
        self.add_parameter('marker1_start',
                            flags=Instrument.FLAG_GETSET,
                            units='s',
                            type=types.FloatType)
        self.add_parameter('marker2_start',
                            flags=Instrument.FLAG_GETSET,
                            units='s',
                            type=types.FloatType)
        # Initializing parameters
        self.set_power_first_tone(0.)
        self.set_power_second_tone(0.)
        self.set_power_third_tone(0.)
        self._awg_routing = {}
        self.set_routing_awg({'firsttone_channel':firsttone_channel,
                        'secondtone_channel':secondtone_channel,
                        'thirdtone_channel':thirdtone_channel,
                        'board_marker':board_marker,
                        'mw_marker':mw_marker})
        self._segmentation = {}
        # self._nb_segmt_memorized = 0
        self._secondtone_temp_length = 20e-6
        self._firsttone_temp_length = 4e-6
        self.set_temp_length_thirdtone(0)
        self._firsttone_temp_start = 100e-9
        self._secondtone_temp_start = 100e-9
        self.set_temp_start_thirdtone(0.)
        self._marker1_width = 0.05e-6
        self._marker2_width = 0.1e-6
        self._marker1_start = 100e-9
        self._marker2_start = 100e-9
        ########################################################################
        # GET only
        self.add_parameter('acquisition_completed',
                            type        = types.FloatType,
                            flags       = Instrument.FLAG_GET,
                            units       = '%')

        self.add_parameter('SSB_conversion_loss',
                            flags=Instrument.FLAG_GET,
                            type=types.FloatType)
        self.add_parameter('electrical_phase_delay',
                            flags=Instrument.FLAG_GETSET,
                            type=types.FloatType)
        self.add_parameter('pulsenumber_averaging',
                            flags=Instrument.FLAG_GETSET,
                            minval = 1,
                            type=types.IntType)
        self.add_parameter('down_converted_frequency',
                            flags=Instrument.FLAG_GETSET,
                            units='GHz',
                            # minval = 0.,
                            # maxval= 1.,
                            type=types.FloatType)
        self.add_parameter('mw_security_time',
                            flags=Instrument.FLAG_GET,
                            units='s',
                            minval= 0.,
                            maxval= 1.,
                            type=types.FloatType)
        self.add_parameter('trigger_time',
                            flags=Instrument.FLAG_GETSET,
                            units='us',
                            type=types.FloatType)
        # usual values
        self._SSB_conver_loss = 6.
        # it is the typical  conversion loss of a SSB
        self._elec_delay = -31.8
        self._pulsenumber_averaging = int(50)
        self._mw_security_time = 5e-3
        self._trigger_time = 50. #100. # set_trigger_timer_time is in us
        ########################################################################

        # initialize the board
        self._board.set_mode('CHANNEL_AB')
        self._board_samplerate = 1000.
        self._board.set_samplerate(self._board_samplerate)
        self._board.set_trigger_range(1)
        self._board.set_trigger_level(0.2)
        self._board.set_trigger_delay(175.)
        acq_time = (self._firsttone_temp_length )*1e9 # - 0.2e-6)*1e9
        acq_time = np.int(acq_time/128)*128
        self._board.set_acquisition_time(acq_time)
        self._board.set_averaging(2)

        # initialize awg
        self._arbitrary_waveform_generator.set_ref_freq(10)
        # self._arbitrary_waveform_generator.set_clock_source('EXT')
        self._arbitrary_waveform_generator.set_clock_freq(1000.)
        # self._arbitrary_waveform_generator.set_clock_source('EXT')
        self._arbitrary_waveform_generator.set_trigger_timer_time(self._trigger_time)
        self._arbitrary_waveform_generator.set_ref_source('EXT')

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.set_marker_source('USER')
        self._arbitrary_waveform_generator.set_trigger_source('EXT')
        self._arbitrary_waveform_generator.set_channels_synchronised('ON')
        #
        # self._arbitrary_waveform_generator.set_clock_freq(1000.)

        # some useful dictionaries
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
            'relaxation1':5,'relaxation2':6, 'ramsey1':7, 'ramsey2':8, 'IQ':9, 'threetone':10,
            'echo1':11, 'echo2':12, 'n_photon':13, 'twotone1':14, 'twotone2':15, 'IQ1':16, 'IQ2':17,'rabi3':18 }

        # we prepare all the channels of the AWG
        for i in CHANNEL:
            self._awg_dict_coupling[i]('DC')
            self._awg_dict_amplitude[i](2)
            self._awg_dict_output[i]('OFF')

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
                                    'marker_trigger':{1:[], 2:[], 3:[], 4:[] }},
                            'threetone': {'binary':{1:[], 2:[], 3:[], 4:[] },
                                    'cosine':{1:[], 2:[], 3:[], 4:[] },
                                    'marker_trigger':{1:[], 2:[], 3:[], 4:[] }},
                            'echo': {'binary':{1:[], 2:[], 3:[], 4:[] },
                                    'cosine':{1:[], 2:[], 3:[], 4:[] },
                                    'marker_trigger':{1:[], 2:[], 3:[], 4:[] }},
                            'n_photon': {'binary':{1:[], 2:[], 3:[], 4:[] },
                                    'cosine':{1:[], 2:[], 3:[], 4:[] },
                                    'marker_trigger':{1:[], 2:[], 3:[], 4:[] }}  }

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

        # if self._presence_mwsrc3:
            # self._microwave_generator3.set_freqsweep('off')
            # self._microwave_generator3.set_gui_update('OFF')

        self._M = 0 # number of triggers to wait to be sure that frequency has changed
        while (self._M+1)*self._arbitrary_waveform_generator.get_trigger_timer_time()*1e-6 < self.get_mw_security_time():
            self._M +=1
        ########################################################################
        #                       Functions
        ########################################################################
        # writing
        self.add_function('write_onetone_pulsessequence')
        self.add_function('write_twotone_pulsessequence')
        self.add_function('write_Rabi_pulsessequence')
        self.add_function('write_Relaxation_pulsessequence')
        self.add_function('write_Ramsey_pulsessequence')
        self.add_function('write_threetone_pulsessequence')
        self.add_function('write_IQ')
        self.add_function('write_Echo_pulsessequence')
        self.add_function('write_n_photon_pulsessequence')
        self.add_function('write_twotone_starck_pulsessequence')

        # Preparing
        self.add_function('prep_onetone')
        self.add_function('prep_twotone')
        self.add_function('prep_rabi')
        # self.add_function('prep_shift')
        self.add_function('prep_IQ')
        self.add_function('prep_threetone')
        self.add_function('prep_ramsey')
        self.add_function('prep_echo')
        self.add_function('prep_relaxation')
        self.add_function('prep_timing')
        self.add_function('prep_timing_IQ')
        self.add_function('prep_timing_IQ_pi')
        self.add_function('reset_rabi_ramsey_measurement')
        # self.add_function('reset_ramsey_measurement')

        self.add_function('prep_n_photon')

        # others
        self.add_function('display_pulses_sequence')
        self.add_function('cos')
        self.add_function('volt2bit')
        self.add_function('volt2bit_2')
        self.add_function('pulse')

        ########################################################################
        # self.write_onetone_pulsessequence( delete = 'all')
        # self.write_twotone_pulsessequence(4e-6, 10.1e-6, 10e-6)
        # self.write_threetone_pulsessequence(50e-9)
        # self.write_Rabi_pulsessequence( 0.2e-6, 1e-9, 0)
        # self.write_Relaxation_pulsessequence( 67e-9, 20e-6, 0.1e-6, 0e-6)
        # self.write_Ramsey_pulsessequence(  200e-9, 20e-6, 5e-6, 0)
        # self.write_IQ( 0.5e-6, 1e-6, 0.13e-6, type='twotone')

    ############################################################################
    # GET_SET
    def do_set_measurement_type(self, meas_type):
        self._meas_type = meas_type.lower()

    def do_get_measurement_type(self):
        return self._meas_type

    def do_get_board_flag(self):
        return self._board_flag

    def do_set_board_flag(self, value):
        self._board_flag = value

    def do_get_board_averaging(self):
        return self._board.get_averaging()

    def do_set_board_averaging(self, value):
        self._board.set_averaging(value)

    def do_get_trigger_time(self):
        if self._arbitrary_waveform_generator.get_trigger_timer_time() == self._trigger_time:
            return self._trigger_time
        else:
            return self._arbitrary_waveform_generator.get_trigger_timer_time()

    def do_set_trigger_time(self, t_t):
        self._trigger_time = t_t
        self._arbitrary_waveform_generator.set_trigger_timer_time(t_t)

        self._M = 0 # number of triggers to wait to be sure that frequency has changed
        while (self._M+1)*self._arbitrary_waveform_generator.get_trigger_timer_time()*1e-6 < self.get_mw_security_time():
            self._M +=1

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

    def do_get_power_third_tone(self):
        '''
        Get the power_third_tone. It gets the estimated power of the third tone after the SSB.
        '''
        return self._power_third_tone

    def do_set_power_third_tone(self, IFP):
        '''
        Set the power_third_tone. It sets the estimated power of the third tone after the SSB.
        Input:
            IFP (float): power_third_tone in dBm
        '''
        self._power_third_tone = IFP

    def do_get_cw_frequency(self, channel=1):
        '''
        Gets the continuous wave frequency in GHz of the microwave generator channel
        '''
        if channel == 1:
            return self._microwave_generator1.get_frequency()/1e9 + self._SSB_tone1.get_band_type()*self.get_down_converted_frequency()
        elif channel==2:
            return self._microwave_generator2.get_frequency()/1e9 + self._SSB_tone2.get_band_type()*self._SSB_tone2.get_IF_frequency()
        elif channel==3:
            return self._microwave_generator3.get_frequency()/1e9 + self._SSB_tone3.get_band_type()*self._SSB_tone3.get_IF_frequency()
        else:
            print 'Error: channel must be in (1, 2, 3)'

    def do_set_cw_frequency(self, cwf, channel=1):
        '''
        Sets the continuous wave frequency in GHz of the microwave generator channel
        '''

        if channel == 1:
            cwf -= self._SSB_tone1.get_band_type()*self.get_down_converted_frequency()
            if cwf > self._SSB_tone1.get_freq_stop() or cwf < self._SSB_tone1.get_freq_start():
                print 'Careful! You are over the range of the SSB'

            self._microwave_generator1.set_frequency(cwf*1e9)
        elif channel == 2:
            cwf -= self._SSB_tone2.get_band_type()*self._SSB_tone2.get_IF_frequency()
            if cwf > self._SSB_tone2.get_freq_stop() or cwf < self._SSB_tone2.get_freq_start():
                print 'Careful! You are over the range of the SSB'
            self._microwave_generator2.set_frequency(cwf*1e9)
        elif channel == 3:
            cwf -= self._SSB_tone3.get_band_type()*self._SSB_tone3.get_IF_frequency()
            if cwf > self._SSB_tone3.get_freq_stop() or cwf < self._SSB_tone3.get_freq_start():
                print 'Careful! You are over the range of the SSB'
            self._microwave_generator3.set_frequency(cwf*1e9)
        else:
            print 'Error: channel must be in (1, 2, 3)'

    def do_get_frequency_start(self, channel=1):
        '''
        Pb: not working function on SMB
        Get the starting frequency of the frequency sweep in GHz of the microwave generator channel
        '''
        if channel == 1:
            return self._microwave_generator1.get_startfreq() + self._SSB_tone1.get_band_type()*self.get_down_converted_frequency()
        elif channel == 2:
            return self._microwave_generator2.get_startfreq() + self._SSB_tone2.get_band_type()*self._SSB_tone2.get_IF_frequency()
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
            freq_start -= self._SSB_tone2.get_band_type()*self._SSB_tone2.get_IF_frequency()
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
            return self._microwave_generator2.get_stopfreq() + self._SSB_tone2.get_band_type()*self._SSB_tone2.get_IF_frequency()
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
            freq_stop -= self._SSB_tone2.get_band_type()*self._SSB_tone2.get_IF_frequency()
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

        acq_time = self._firsttone_temp_length
        #  - 0.2e-6
        acq_time = np.int(1e9*acq_time/128)*128
        if acq_time > 256./self._board.get_samplerate()*1e3:
            self._acquisition = 1
            self._board.set_acquisition_time(acq_time) # in ns
        else:
            self._acquisition = 0
            self._board.set_acquisition_time((256.+128)/self._board.get_samplerate()*1e3)

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

    def do_get_temp_length_thirdtone(self):
        '''
        Gets the temporal length of the third tone pulses in s.
        '''
        return self._thirdtone_temp_length

    def do_set_temp_length_thirdtone(self, delta_t):
        '''
        Sets the temporal length of the third tone pulses in s.
        '''
        self._thirdtone_temp_length = delta_t

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

    def do_set_temp_start_secondtone(self, t0=1e-6):
        '''
        Sets the temporal start of the second tone pulses in s.
        '''
        self._secondtone_temp_start = t0


    def do_get_temp_start_thirdtone(self):
        '''
        Gets the temporal start of the third tone pulses in s.
        '''
        return self._thirdtone_temp_start

    def do_set_temp_start_thirdtone(self, t0):
        '''
        Sets the temporal start of the third tone pulses in s.
        '''
        self._thirdtone_temp_start = t0

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
        if np.int(self.get_trigger_time()\
            *self._SSB_tone1.get_IF_frequency()*1e3) != self.get_trigger_time()*self._SSB_tone1.get_IF_frequency()*1e3:


            print 'Problem: the awg period should be a multiple of the IF period'
            print 'awg period [us]:', self.get_trigger_time()
            print 'IF period [us]:', 1e-3/self._SSB_tone1.get_IF_frequency()
            print 'IF frequency [MHz]: ', self._SSB_tone1.get_IF_frequency()*1e3
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
        return int(self._pulsenumber_averaging)

    def do_set_pulsenumber_averaging(self, N):
        '''
        Set the pulse number averaging.
        '''
        self._pulsenumber_averaging = int(N)

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

    def do_set_electrical_phase_delay(self, e_delay):
        '''
        Set the electrical phase delay.
        Input:
            The electrical phase delay in s due to the propagation in the wires.
        '''
        self._elec_delay = e_delay

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

    ############################################################################
    #  Functions
    ############################################################################
    def prep_onetone(self, freq_vec, average, power, acq_time=500,
            pulse_time=500, delta_t=0.):
        '''
        Preparing the instruments for a onetone pulses sequence. This function do not
        write in the awg memory.
        Inputs:
            frec_vec: frequency vector in GHz of the onetone sweep
            average (int): number of averaging
            power: power at the awg output
            pulse_time in ns
            delta_t in ns
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

        # Setting the averaging:
        self.set_total_averaging(average)
        self._microwave_generator1.set_gui_update('OFF')

        # Selecting the AWG sequence
        self.AWG_select_sequence(sequence='onetone', nb_channel=1)

        # Setting AWG power/amplitude
        self.set_power_first_tone(power)
        amplitude = 10**((power)/10.)
        print amplitude
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude)

        self._board.set_acquisition_time(acq_time)
        # Setting the measurement process
        if self.do_get_measurement_type() == 'homodyne':
            processus = dt.HomodyneRealImagPerSequence(pulse_time*1e-9, self._board.get_samplerate()*1e6, delta_t*1e-9)
        elif self.do_get_measurement_type() == 'heterodyne':
            if self._acquisition:
                processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                              self.get_down_converted_frequency()*1e9)
            else:
                processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                              self.get_down_converted_frequency()*1e9, t_ro=self.get_temp_length_firsttone())

        self._board.measurement_initialization(processor=processus)

    def prep_twotone(self, cwf, freq_vec, average, power_tone1, power_tone2,
            acq_time=500, pulse_time=500, delta_t=0):
        '''
        Preparing the instruments for a twotone pulses sequence. This function do not
        write in the awg memory.
        Inputs:
            cwf [GHz]: continuous wave frequency of the first tone
            frec_vec: frequency vector in GHz of the second tone sweep
            average (int): number of total averaging
            pulse_time in ns
            delta_t in ns
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

        self.AWG_select_sequence(sequence='twotone', nb_channel=2 )

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)
        self.set_power_second_tone(power_tone2)
        amplitude2 = 10**((power_tone2)/10.)
        print amplitude1, amplitude2
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)

        self._board.set_acquisition_time(acq_time)
        # Setting the measurement process
        if self.do_get_measurement_type() == 'homodyne':
            processus = dt.HomodyneRealImagPerSequence(pulse_time*1e-9, self._board.get_samplerate()*1e6, delta_t*1e-9)
        elif self.do_get_measurement_type() == 'heterodyne':
            if self._acquisition:
                processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                              self.get_down_converted_frequency()*1e9)
            else:
                processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                              self.get_down_converted_frequency()*1e9, t_ro=self.get_temp_length_firsttone())
        self._board.measurement_initialization(processor=processus)

    def prep_conditional_transmission(self, freq_vec, average,
                power1, f_cw=5, power2=0, acq_time=500, pulse_time=500, delta_t=0, tau=None, t_start=0 , nb_channel=2):
        '''
        Preparing the instruments for a twotone pulses sequence, where
        it is the first tone frequency who is sweepped.
        This function do not write in the awg memory.
        Inputs:
            freq_vec: frequency vector in GHz of the onetone sweep
            average (int): number of averaging
            power: power at the awg output
            acq_time in ns
            pulse_time in ns
            delta_t in ns
            tau in ns
            t_start in ns
        '''
        # Setting the mw1 on the sweeping mode
        self._microwave_generator1.set_freqsweep('on')
        self._microwave_generator1.set_sweepmode('STEP')
        self._microwave_generator1.set_spacingfreq('lin')
        if  self._presence_mwsrc2:
            self._microwave_generator2.set_freqsweep('off')

        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        # Setting the sweep parameters to mw1
        self.set_src1_frequency_start(freq_vec[0])
        self.set_src1_frequency_stop(freq_vec[-1])
        self.set_src1_points_freq_sweep(len(freq_vec))



        # Setting the averaging:
        self.set_total_averaging(average)
        self._microwave_generator1.set_gui_update('OFF')

        self.AWG_select_sequence(sequence='twotone', nb_channel=nb_channel )

        self.set_power_first_tone(power1)
        self.set_power_second_tone(power2)
        amplitude1 = 10**((power1)/10.)
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)
        amplitude2 = 10**((power2)/10.)
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude1)


        self._board.set_acquisition_time(acq_time)
        # Setting the measurement process
        if self.do_get_measurement_type() == 'homodyne':
            if tau == None:
                processus = dt.HomodyneRealImagPerSequence(pulse_time*1e-9, self._board.get_samplerate()*1e6, delta_t*1e-9)
            else:
                processus = dt.HomodyneRealImagPerSequenceWeighted(self._board.get_acquisition_time()*1e-9,
                    pulse_time*1e-9, self._board.get_samplerate()*1e6, delta_t*1e-9, tau*1e-9, t_start*1e-9)
        elif self.do_get_measurement_type() == 'heterodyne':
            if self._acquisition:
                processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                              self.get_down_converted_frequency()*1e9)
            else:
                processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                              self.get_down_converted_frequency()*1e9, t_ro=self.get_temp_length_firsttone())

        self._board.measurement_initialization(processor=processus)

    def prep_rabi(self, cwf1, cwf2, average, nb_sequences, power_tone1, power_tone2,
            acq_time=500, pulse_time=500, delta_t=0., mw = 2, power_tone3=0):
        '''
        Preparing the instruments for a Rabi pulses sequence. This function do not
        write in the awg memory.
        Inputs:
            cwf1 [GHz]: continuous wave frequency of the first tone
            cwf2 [GHz]: continuous wave frequency of the second tone
            average (int): number of total averaging
        '''
        self._acq_time = acq_time
        self._pulse_time = pulse_time
        self._delta_t = delta_t
        # self._microwave_generator1.set_gui_update('OFF')
        # self._microwave_generator2.set_gui_update('OFF')
        for i in CHANNEL:
            self._awg_dict_output[i]('OFF')


        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(cwf1)
        if mw ==2:
            self._microwave_generator2.set_freqsweep('off')
            self.set_src2_cw_frequency(cwf2)
            self._microwave_generator2.set_power(self._SSB_tone2.get_LO_power())
        elif mw == 3:
            self._microwave_generator3.set_freqsweep('off')
            self.set_src3_cw_frequency(cwf2)
            self._microwave_generator3.set_power(self._SSB_tone3.get_LO_power())

        self._board.set_nb_sequence(nb_sequences)
        self._board.set_averaging(average)

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['rabi1'])
        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        if self._thirdtone == 1:
            self._arbitrary_waveform_generator.channel_select(self._awg_routing['thirdtone_channel'])
            self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['rabi3'])
            self._awg_dict_output[self._awg_routing['thirdtone_channel']]('ON')

            self.set_power_third_tone(power_tone3)
            amplitude = 10**((power_tone3)/10.)
            print amplitude
            self._awg_dict_amplitude[self._awg_routing['thirdtone_channel']](2*amplitude)


        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)
        self.set_power_second_tone(power_tone2)
        amplitude2 = 10**((power_tone2)/10.)
        print amplitude1, amplitude2
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['rabi2'])
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)


        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self._board_flag = 1

        self._board.set_acquisition_time(acq_time)
        if self.do_get_measurement_type() == 'homodyne':
            processus = dt.HomodyneRealImagPerSequence(pulse_time*1e-9, self._board.get_samplerate()*1e6, delta_t*1e-9)
        elif self.do_get_measurement_type() == 'heterodyne':
            if self._acquisition:
                processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                              self.get_down_converted_frequency()*1e9)
            else:
                processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                              self.get_down_converted_frequency()*1e9, t_ro=self.get_temp_length_firsttone())

        self._board.measurement_initialization(processor=processus)

        # processus = dt.HomodyneRealImagPerSequence(self.get_temp_length_firsttone(), self._board.get_samplerate()*1e6, delta_t)
        #
        # self._board.measurement_initialization(processor=processus)

    def prep_relaxation(self, cwf1, cwf2, average, nb_sequences, power_tone1,
            power_tone2, acq_time, pulse_time, delta_t):
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
        self._board.set_nb_sequence(nb_sequences)
        self._board.set_averaging(average)


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

        self._board.set_acquisition_time(acq_time)
        if self.do_get_measurement_type() == 'homodyne':
            processus = dt.HomodyneRealImagPerSequence(pulse_time*1e-9, self._board.get_samplerate()*1e6, delta_t*1e-9)
        elif self.do_get_measurement_type() == 'heterodyne':
            if self._acquisition:
                processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                              self.get_down_converted_frequency()*1e9)
            else:
                processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                              self.get_down_converted_frequency()*1e9, t_ro=self.get_temp_length_firsttone())

        self._board.measurement_initialization(processor=processus)

    def prep_IQ_2(self, counts, average, cwf1, power_tone1, cwf2='None',
            power_tone2 = 'None', acq_time=500, pulse_time=500, delta_t=0., tau=None, t_start=0):
        '''
        Preparing the instruments for a IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        This function do not write in the awg memory. You need to write a twotone sequence for that...
        Inputs:
            cwf1 [GHz]: continuous wave frequency of the first tone
            cwf2 [GHz]: continuous wave frequency of the second tone if not None
            counts (int): number of repetitions to make the histograms
        '''
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(cwf1)

        self._board.set_nb_sequence(counts)
        self._board.set_averaging(average)

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ1'])
        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        if cwf2 != 'None':
            self._microwave_generator2.set_gui_update('OFF')
            self._microwave_generator2.set_freqsweep('off')
            self.set_src2_cw_frequency(cwf2)
            self._microwave_generator2.set_power(self._SSB_tone2.get_LO_power())


            self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
            self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ2'])
            self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')

            self.set_power_second_tone(power_tone2)
            amplitude2 = 10**((power_tone2)/10.)
            print amplitude2
            self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)

        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)

        print amplitude1
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)

        self._board.set_acquisition_time(acq_time)
        # processus = dt.HomodyneRealImag_raw(self.get_temp_length_firsttone(), self._board.get_samplerate()*1e6, delta_t)
        if self.do_get_measurement_type() == 'homodyne':
            if tau==None or tau ==0. :
                processus = dt.HomodyneRealImag_raw(pulse_time*1e-9, self._board.get_samplerate()*1e6, delta_t*1e-9)
            else:
                processus = dt.HomodyneRealImag_rawWeighted(self._board.get_acquisition_time()*1e-9,
                    pulse_time*1e-9, self._board.get_samplerate()*1e6, delta_t*1e-9, tau*1e-9, t_start*1e-9)
        elif self.do_get_measurement_type() == 'heterodyne':
            processus = dt.RealImag_raw(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                          self.get_down_converted_frequency()*1e9)
        # self._board.measurement_initialization(processor=processus)


        self._board.measurement_initialization(processor=processus)

    def prep_several_RO(self, counts, average, cwf1, power_tone1, cwf2='None',
            power_tone2 = 'None', acq_time=500, pulse_time=500, delta_t=500, N=1):
        '''
        Preparing the instruments for a sequence. This function do not
        write in the awg memory.
        Inputs:
            frec_vec: frequency vector in GHz of the onetone sweep
            average (int): number of averaging
            power: power at the awg output
        '''

        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(cwf1)

        self._board.set_nb_sequence(counts)
        self._board.set_averaging(average)

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ1'])
        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        if cwf2 != 'None':
            self._microwave_generator2.set_gui_update('OFF')
            self._microwave_generator2.set_freqsweep('off')
            self.set_src2_cw_frequency(cwf2)
            self._microwave_generator2.set_power(self._SSB_tone2.get_LO_power())


            self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
            self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ2'])
            self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')

            self.set_power_second_tone(power_tone2)
            amplitude2 = 10**((power_tone2)/10.)
            print amplitude2
            self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)

        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)

        print amplitude1
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)

        self._board.set_acquisition_time(acq_time)
        # processus = dt.HomodyneRealImag_raw(self.get_temp_length_firsttone(), self._board.get_samplerate()*1e6, delta_t)
        if self.do_get_measurement_type() == 'homodyne':
            processus = dt.HomodyneRealImag_Nraw(pulse_time*1e-9, self._board.get_samplerate()*1e6, delta_t*1e-9, N)
        # elif self.do_get_measurement_type() == 'heterodyne':
        #     processus = dt.RealImag_raw(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
        #                   self.get_down_converted_frequency()*1e9)
        # self._board.measurement_initialization(processor=processus)


        self._board.measurement_initialization(processor=processus)

    def prep_gliding_mean(self, cwf1, cwf2, average, power_tone1, power_tone2,
        f_cutoff, r_dB, order=4, acquisition_time='None', doweaverage=False):
        '''
        Preparing the instruments for a Tcheby timing measurement.
        This function do not write in the awg memory.
        Inputs:
            cwf1 [GHz]: continuous wave frequency of the first tone
            average (int): number of averaging of the V(t) curve.
            f_cutoff [MHz]: cut off frequency of the numerical RC filter
            order (int): order of the RC filter
            acquisition_time [ns]: time of acquisition
        '''
        # self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(cwf1)

        self._microwave_generator2.set_gui_update('OFF')
        self._microwave_generator2.set_freqsweep('off')
        self.set_src2_cw_frequency(cwf2)

        self._board.set_nb_sequence(4)
        self._board.set_averaging(average)
        if acquisition_time != 'None':
            acq_time = np.int(acquisition_time/128)*128
            self._board.set_acquisition_time(acq_time)
        # print self._board.get_averaging()

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ1'])
        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ2'])
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')

        self._arbitrary_waveform_generator.set_trigger_source('EVEN')
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')


        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)
        # print amplitude1
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)

        self.set_power_second_tone(power_tone2)
        amplitude2 = 10**((power_tone2)/10.)
        # print amplitude1
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)



        processus = dt.Homodyne_Tchebytchev(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                       f_cutoff, r_dB, order, doweaverage=doweaverage)
        # processus = dt.Raw()
        self._board.measurement_initialization(processor=processus)

    def prep_IQ_2_sevRO(self, counts, average, cwf1, power_tone1, cwf2='None',
            power_tone2 = 'None', acq_time=500, pulse_time1=500, t1_start=0,
            pulse_time2=500, t2_start=0, delta_t=0., tau=None):
        '''
        Preparing the instruments for a IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        This function do not write in the awg memory. You need to write a twotone sequence for that...
        Inputs:
            cwf1 [GHz]: continuous wave frequency of the first tone
            cwf2 [GHz]: continuous wave frequency of the second tone if not None
            counts (int): number of repetitions to make the histograms
        '''
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(cwf1)

        self._board.set_nb_sequence(counts)
        self._board.set_averaging(average)

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ1'])
        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        if cwf2 != 'None':
            self._microwave_generator2.set_gui_update('OFF')
            self._microwave_generator2.set_freqsweep('off')
            self.set_src2_cw_frequency(cwf2)
            self._microwave_generator2.set_power(self._SSB_tone2.get_LO_power())


            self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
            self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ2'])
            self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')

            self.set_power_second_tone(power_tone2)
            amplitude2 = 10**((power_tone2)/10.)
            print amplitude2
            self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)

        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)

        print amplitude1
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)

        self._board.set_acquisition_time(acq_time)
        # processus = dt.HomodyneRealImag_raw(self.get_temp_length_firsttone(), self._board.get_samplerate()*1e6, delta_t)
        if self.do_get_measurement_type() == 'homodyne':
            if tau==None or tau ==0.:
                processus = dt.HomodyneRealImag_raw_sevRO(pulse_time1*1e-9,
                        t1_start*1e-9, pulse_time2*1e-9, t2_start*1e-9,
                        self._board.get_samplerate()*1e6, delta_t*1e-9)
            else:
                processus = dt.HomodyneRealImag_raw_sevROWeighted(acq_time*1e-9, pulse_time1*1e-9,
                        t1_start*1e-9, pulse_time2*1e-9, t2_start*1e-9,
                        self._board.get_samplerate()*1e6, delta_t*1e-9, tau*1e-9)

        elif self.do_get_measurement_type() == 'heterodyne':
            processus = dt.RealImag_raw(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                          self.get_down_converted_frequency()*1e9)
        # self._board.measurement_initialization(processor=processus)


        self._board.measurement_initialization(processor=processus)



    ############################################################################
    def write_onetone_pulsessequence(self, t_1=4e-6, t1_start=0.1e-9, m1_start=0.1e-9, delete = False, t_rise=None, shape='None', tau=1.):
        '''
        Putting in the awg memory the onetone pulses sequence and preparing the awg.
        Inputs:
            frec_vec: frequency vector in GHz of the onetone sweep
            average (int): number of averaging
            readout_channel: awg channel used. Value in (1, 2, 3, 4)
            sequence_index (str): onetone, twone, rabi... yet to be implemented
            delete (True or False): the option to delete or not the awg memory

        '''
        # Computing the amplitude of the readout_pulse
        amplitude = 0.9999 # corresponds to 16382 in uint16 with volt2bit_2

        # Setting the starts of first tone and markers
        self.set_marker1_start(m1_start)
        self.set_temp_start_firsttone(t1_start)
        self.set_marker2_start(100e-9)
        self.set_temp_length_firsttone(t_1)
        # self.set_marker1_width(self.get_temp_length_firsttone())
        # self.set_marker2_width(self.get_marker2_width())

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

        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['onetone']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)

        self.clock_AWG()
        # Initializing awg firsttone channel
        self.usual_setting_AWG()

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
        if t_rise == None or t_rise==0.:
            p = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                amplitude, self.get_down_converted_frequency()*1e9]
            segment3  = self.volt2bit_2(self.cos(p, time) )
        else:
            if t_rise > self.get_temp_length_firsttone()/2.:
                print 'Be Careful: rising time should be less than the length of first tone...'
            else:
                p = [self.get_temp_start_firsttone(), t_rise, self.get_temp_length_firsttone(),
                    amplitude, self.get_down_converted_frequency()*1e9]
                segment3  = self.volt2bit_2(self.cos_rise(p, time) )

        # shaping is not yet done and working ##################################
        # if shape == 'None':
        #     segment3_c = self.cos(p, time)
        # elif shape == 'exp':
        #     pp = [self.get_temp_start_firsttone()+ self.get_temp_length_firsttone()/2., tau]
        #     segment3_c = self.cos(p, time)*self.exp_envelop(pp, time)
        ########################################################################

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
                self._awg_waves['onetone']['cosine'][self._awg_routing['firsttone_channel']].append(segment3)
                self._awg_waves['onetone']['marker_trigger'][self._awg_routing['firsttone_channel']].append(segment3_m)

        ########################################################################
        self._seq_list = np.array(self._seq_list)

        self.set_awg_segmentation({'onetone': self.get_number_segments_memorized() + 1 + np.arange(3)} )


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, self._sequence_dict['onetone'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['onetone'])

        # switching ON the output of the readout channel and the markers
        self.status_AWG('ON', nb_channel=1)

    def write_twotone_pulsessequence(self, temp_1=4e-6, t1_start=20.1e-6, temp_2=20e-6 , m1_start=20.1e-6, delete = False, t_rise =None):
        '''
        Putting in the awg memory the twotone pulses sequence and preparing the others instruments.
        Inputs:
            delete:

        '''

        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['twotone']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)

        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')

        self.clock_AWG()
        self.usual_setting_AWG(nb_channel=2)

        amplitude1 = 0.9999
        amplitude2 = 0.9999

        self.set_temp_length_secondtone(temp_2)
        self.set_temp_start_secondtone(100e-9)
        self.set_temp_start_firsttone(t1_start)

        self.set_temp_length_firsttone(temp_1)
        self.set_marker1_start(m1_start)
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

        self._seq_list1 = []
        self._seq_list2 = []

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
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 2)

        # waiting time segments ################################################
        segment2_ro  = self.volt2bit_2(np.zeros(16*50))
        segment2_ex = self.volt2bit_2(np.zeros(16*50))
        # Putting the segment in AWG memory
        self._arbitrary_waveform_generator.send_waveform(segment2_ro,
                            self._awg_routing['firsttone_channel'], self.get_number_segments_memorized() + 3)
        self._arbitrary_waveform_generator.send_waveform(segment2_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 4)

        # excitation and readout segments ######################################
        if t_rise == None or t_rise ==0.:
            p = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                amplitude1, self.get_down_converted_frequency()*1e9]
            segment3_ro  = self.volt2bit_2(self.cos(p, time))
        else:
            if t_rise > self.get_temp_length_firsttone()/2.:
                print 'Be Careful: rising times should be less than the length of first tone...'
            else:
                p = [self.get_temp_start_firsttone(), t_rise, self.get_temp_length_firsttone(),
                    amplitude1, self.get_down_converted_frequency()*1e9]
                segment3_ro  = self.volt2bit_2(self.cos_rise(p, time))

        segment3_ro = self._arbitrary_waveform_generator.add_markers_mask(\
            self._awg_routing['board_marker'],
            np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
            np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
            segment3_ro)
        self._arbitrary_waveform_generator.send_waveform(segment3_ro,
                            self._awg_routing['firsttone_channel'], self.get_number_segments_memorized() + 5)

        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            amplitude2, self._SSB_tone2.get_IF_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 6)

        for i in np.arange(self._M + self.get_pulsenumber_averaging() + 1):
            if i == self._M + self.get_pulsenumber_averaging():
                # Segment triggering the change of smb frequency
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment1_ro)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment1_ex)
                self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
                self._seq_list2.append([1, self.get_number_segments_memorized() + 2, 0])

            elif i < self._M:
                # waiting time segments
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment2_ro)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment2_ex)
                self._seq_list1.append([1, self.get_number_segments_memorized() + 3, 0])
                self._seq_list2.append([1, self.get_number_segments_memorized() + 4, 0])
            else:
                # excitation and readout segments
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment3_ro)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment3_ex)

                self._seq_list1.append([1, self.get_number_segments_memorized() + 5, 0])
                self._seq_list2.append([1, self.get_number_segments_memorized() + 6, 0])


        self._seq_list1 = np.array(self._seq_list1)
        self._seq_list2 = np.array(self._seq_list2)
        self.set_awg_segmentation({'twotone': self.get_number_segments_memorized() + 1 + np.arange(6)} )

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list1, self._sequence_dict['twotone1'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list2, self._sequence_dict['twotone2'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['twotone2'])

        # switching ON the awg channels and markers
        self.status_AWG('ON', nb_channel=2)

    ############################################################################
    def write_twotone_pulsessequence_withpi(self, temp_1=4e-6, t1_start=20.1e-6,
            temp_2=20e-6 , m1_start=20.1e-6, delete = False, t_rise=None):
        '''
        Putting in the awg memory the twotone pulses sequence and preparing the others instruments.
        Inputs:
            delete: True or False

        '''

        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['twotone']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)

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

        self.set_temp_length_secondtone(temp_2)
        self.set_temp_start_secondtone(100e-9)
        self.set_temp_start_firsttone(t1_start)
        # self.set_temp_start_firsttone(self.get_temp_start_secondtone()+self.get_temp_length_secondtone())
        self.set_temp_length_firsttone(temp_1)
        self.set_marker1_start(m1_start)
        self.set_marker2_start(100e-9)
        # self.set_marker1_width(self.get_temp_length_firsttone())
        # self.set_marker2_width(self.get_marker2_width() )
        # self.set_marker2_width(np.max(self.get_temp_length_secondtone(), 10e-6))

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

        self._seq_list1 = []
        self._seq_list2 = []

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
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 2)

        # waiting time segments ################################################
        segment2_ro  = self.volt2bit_2(np.zeros(16*50))
        segment2_ex = self.volt2bit_2(np.zeros(16*50))
        # Putting the segment in AWG memory
        self._arbitrary_waveform_generator.send_waveform(segment2_ro,
                            self._awg_routing['firsttone_channel'], self.get_number_segments_memorized() + 3)
        self._arbitrary_waveform_generator.send_waveform(segment2_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 4)

        # excitation and readout segments ######################################
        if t_rise == None or t_rise ==0.:
            p = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                amplitude1, self.get_down_converted_frequency()*1e9]
            segment3_ro  = self.volt2bit_2(self.cos(p, time))
        else:
            if t_rise > self.get_temp_length_firsttone()/2.:
                print 'Be Careful: rising times should be less than the length of first tone...'
            else:
                p = [self.get_temp_start_firsttone(), t_rise, self.get_temp_length_firsttone(),
                    amplitude1, self.get_down_converted_frequency()*1e9]
                segment3_ro  = self.volt2bit_2(self.cos_rise(p, time))
        segment3_ro = self._arbitrary_waveform_generator.add_markers_mask(\
            self._awg_routing['board_marker'],
            np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
            np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
            segment3_ro)
        self._arbitrary_waveform_generator.send_waveform(segment3_ro,
                            self._awg_routing['firsttone_channel'], self.get_number_segments_memorized() + 5)

        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            amplitude2, self._SSB_tone2.get_IF_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 6)

        for i in np.arange(self._M + self.get_pulsenumber_averaging() + 1):
            if i == self._M + self.get_pulsenumber_averaging():
                # Segment triggering the change of smb frequency
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment1_ro)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment1_ex)
                self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
                self._seq_list2.append([1, self.get_number_segments_memorized() + 2, 0])

            elif i < self._M:
                # waiting time segments
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment2_ro)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment2_ex)
                self._seq_list1.append([1, self.get_number_segments_memorized() + 3, 0])
                self._seq_list2.append([1, self.get_number_segments_memorized() + 4, 0])
            elif i>= self._M and i< self._M + self.get_pulsenumber_averaging()/2 :
                # excitation and readout segments
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment3_ro)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment3_ex)

                self._seq_list1.append([1, self.get_number_segments_memorized() + 5, 0])
                self._seq_list2.append([1, self.get_number_segments_memorized() + 4, 0])
            else:
                # excitation and readout segments
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment3_ro)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment3_ex)

                self._seq_list1.append([1, self.get_number_segments_memorized() + 5, 0])
                self._seq_list2.append([1, self.get_number_segments_memorized() + 6, 0])


        self._seq_list1 = np.array(self._seq_list1)
        self._seq_list2 = np.array(self._seq_list2)
        self.set_awg_segmentation({'twotone': self.get_number_segments_memorized() + 1 + np.arange(6)} )

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list1, self._sequence_dict['twotone1'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list2, self._sequence_dict['twotone2'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['twotone2'])

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

    def write_twotone_pulsessequence_withpi_ef(self, temp_1=4e-6, t1_start=20.1e-6,
            temp_2=20e-6, t2_start=1e-6, temp_3=1e-6, delta_m1_start=0., delete = False, t_rise=None):
        '''
        Putting in the awg memory the twotone pulses sequence and preparing the others instruments.
        Inputs:
            delete: True or False

        '''

        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['twotone']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)

        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['thirdtone_channel'])
        self._awg_dict_coupling[self._awg_routing['thirdtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['thirdtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')

        amplitude = 0.9999
        self.set_temp_start_thirdtone(100e-9)
        self.set_temp_length_thirdtone(temp_3)

        self.set_temp_start_secondtone( t2_start)
        self.set_temp_length_secondtone(temp_2)

        self.set_temp_start_firsttone(t1_start)
        self.set_temp_length_firsttone(temp_1)
        self.set_marker1_start(t1_start - delta_m1_start)
        self.set_marker2_start(100e-9)
        # self.set_marker1_width(self.get_temp_length_firsttone())
        # self.set_marker2_width(self.get_marker2_width() )
        # self.set_marker2_width(np.max(self.get_temp_length_secondtone(), 10e-6))

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
        self._arbitrary_waveform_generator.send_waveform(segment1_ex,
                            self._awg_routing['thirdtone_channel'], self.get_number_segments_memorized() + 1)

        # waiting time segments ################################################
        segment2_ro  = self.volt2bit_2(np.zeros(16*50))
        segment2_ex = self.volt2bit_2(np.zeros(16*50))
        # Putting the segment in AWG memory
        self._arbitrary_waveform_generator.send_waveform(segment2_ro,
                            self._awg_routing['firsttone_channel'], self.get_number_segments_memorized() + 2)
        self._arbitrary_waveform_generator.send_waveform(segment2_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 2)
        self._arbitrary_waveform_generator.send_waveform(segment2_ex,
                            self._awg_routing['thirdtone_channel'], self.get_number_segments_memorized() + 2)

        # excitation and readout segments ######################################
        if t_rise == None or t_rise ==0.:
            p = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                amplitude, self.get_down_converted_frequency()*1e9]
            segment3_ro  = self.volt2bit_2(self.cos(p, time))
        else:
            if t_rise > self.get_temp_length_firsttone()/2.:
                print 'Be Careful: rising times should be less than the length of first tone...'
            else:
                p = [self.get_temp_start_firsttone(), t_rise, self.get_temp_length_firsttone(),
                    amplitude, self.get_down_converted_frequency()*1e9]
                segment3_ro  = self.volt2bit_2(self.cos_rise(p, time))

        segment3_ro = self._arbitrary_waveform_generator.add_markers_mask(\
            self._awg_routing['board_marker'],
            np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
            np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
            segment3_ro)

        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            amplitude, self._SSB_tone2.get_IF_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time))

        p_qb3 = [self.get_temp_start_thirdtone(), self.get_temp_length_thirdtone(),
            amplitude, self._SSB_tone3.get_IF_frequency()*1e9]

        segment3_ex3 = self.volt2bit_2(self.cos(p_qb3, time))

        self._arbitrary_waveform_generator.send_waveform(segment3_ro,
                            self._awg_routing['firsttone_channel'], self.get_number_segments_memorized() + 3)
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 3)
        self._arbitrary_waveform_generator.send_waveform(segment3_ex3,
                            self._awg_routing['thirdtone_channel'], self.get_number_segments_memorized() + 3)

        self._arbitrary_waveform_generator.send_waveform(segment3_ex3,
                            self._awg_routing['thirdtone_channel'], self.get_number_segments_memorized() + 4)
        self._arbitrary_waveform_generator.send_waveform(segment3_ro,
                            self._awg_routing['firsttone_channel'], self.get_number_segments_memorized() + 4)
        self._arbitrary_waveform_generator.send_waveform(segment2_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 4)

        self._arbitrary_waveform_generator.send_waveform(segment3_ro,
                            self._awg_routing['firsttone_channel'], self.get_number_segments_memorized() + 5)
        self._arbitrary_waveform_generator.send_waveform(segment2_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 5)
        self._arbitrary_waveform_generator.send_waveform(segment2_ex,
                            self._awg_routing['thirdtone_channel'], self.get_number_segments_memorized() + 5)



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

            elif i>= self._M and i< self._M + self.get_pulsenumber_averaging()/3 :
                #  pi ge+ pi ef excitation and readout segments
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment3_ro)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment3_ex)
                self._seq_list.append([1, self.get_number_segments_memorized() + 3, 0])

            elif i>=self._M + self.get_pulsenumber_averaging()/3 and i< self._M + 2*self.get_pulsenumber_averaging()/3 :
                # pi ge excitation and readout segments
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment3_ro)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment3_ex)
                self._seq_list.append([1, self.get_number_segments_memorized() + 4, 0])

            else:
                # 0 excitation and readout segments
                self._awg_waves['twotone']['binary'][self._awg_routing['firsttone_channel']].append(segment3_ro)
                self._awg_waves['twotone']['binary'][self._awg_routing['secondtone_channel']].append(segment3_ex)
                self._seq_list.append([1, self.get_number_segments_memorized() + 5, 0])


        self._seq_list = np.array(self._seq_list)

        self.set_awg_segmentation({'twotone': self.get_number_segments_memorized() + 1 + np.arange(6)} )

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, self._sequence_dict['twotone'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['thirdtone_channel'])
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
        self._awg_dict_output[self._awg_routing['thirdtone_channel']]('ON')
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('ON')

        ########################################################################

    def write_twotone_starck_pulsessequence(self, temp_1=4e-6, t1_start=0.1e-6,
        temp_2=3e-6, t2_start=300e-9, marker_start=300e-9, t_ph = 5e-6, t_ph_start = 0.1e-6 ,delete = False):
        '''
        Putting in the awg memory the twotone pulses sequence and preparing the others instruments.
        Inputs:
            delete: True or False

        '''

        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['twotone']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)

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

        self.set_temp_length_secondtone(temp_2)
        self.set_temp_start_secondtone(t2_start)
        self.set_temp_start_firsttone(t1_start)
        # self.set_temp_start_firsttone(self.get_temp_start_secondtone()+self.get_temp_length_secondtone())
        # self.set_temp_length_firsttone(t1_start+temp_1-marker_start)
        self.set_temp_length_firsttone(temp_1)
        self.set_marker1_start(marker_start)
        self.set_marker2_start(100e-9)
        # self.set_marker1_width(self.get_temp_length_firsttone())
        # self.set_marker2_width(self.get_marker2_width() )
        # self.set_marker2_width(np.max(self.get_temp_length_secondtone(), 10e-6))

        ########################################################################
        nb_samples_smb =  round(1.2*(self.get_marker2_start()+self.get_marker2_width())*\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time_smb = np.arange(nb_samples_smb)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        nb_samples =  round((self.get_marker1_start() + self.get_marker1_width() +\
                self.get_temp_start_firsttone() + temp_1 +\
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
            amplitude2, self._SSB_tone2.get_IF_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 3)

        p = [self.get_temp_start_firsttone(), temp_1,
            amplitude1, self.get_down_converted_frequency()*1e9]

        p_ph = [t_ph_start, t_ph,
            amplitude1, self.get_down_converted_frequency()*1e9]
        segment3_ro  = self.volt2bit_2(self.cos(p, time) + self.cos(p_ph, time))

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

    def prep_threetone(self, cwf_ex, cwf_ro, freq_vec, average, power_tone1,
            power_tone2, power_tone3, onesource=1, acq_time=500, pulse_time=500, delta_t=0):
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
        # self._microwave_generator3.set_gui_update('OFF') # only for the smb

        self._microwave_generator1.set_freqsweep('off')
        if onesource!=1:
            self._microwave_generator3.set_freqsweep('off') # hp83630 does not have freqsweep function
        self.set_src1_cw_frequency(cwf_ro)
        if onesource!=1:
            self.set_src3_cw_frequency(cwf_ex)

        self._microwave_generator2.set_freqsweep('on')
        self._microwave_generator2.set_sweepmode('STEP')
        self._microwave_generator2.set_spacingfreq('lin')

        self.set_src2_frequency_start(freq_vec[0])
        self.set_src2_frequency_stop(freq_vec[-1])
        self.set_src2_points_freq_sweep(len(freq_vec))

        self._microwave_generator2.set_power(self._SSB_tone2.get_LO_power())
        if onesource!=1:
            self._microwave_generator3.set_power(self._SSB_tone3.get_LO_power())
        # print self._microwave_generator2.get_power()

        self.set_total_averaging(average)

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['threetone'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['threetone'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['thirdtone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['threetone'])

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')
        self._awg_dict_output[self._awg_routing['thirdtone_channel']]('ON')
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)
        self.set_power_second_tone(power_tone2)
        amplitude2 = 10**((power_tone2)/10.)
        self.set_power_second_tone(power_tone3)
        amplitude3 = 10**((power_tone3)/10.)

        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)
        self._awg_dict_amplitude[self._awg_routing['thirdtone_channel']](2*amplitude3)

        if self.do_get_measurement_type() == 'homodyne':
            self._board.set_acquisition_time(acq_time)
            processus = dt.HomodyneRealImagPerSequence(pulse_time*1e-9, self._board.get_samplerate()*1e6, delta_t*1e-9)
        elif self.do_get_measurement_type() == 'heterodyne':
            if self._acquisition:
                processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                              self.get_down_converted_frequency()*1e9)
            else:
                processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                              self.get_down_converted_frequency()*1e9, t_ro=self.get_temp_length_firsttone())
        self._board.measurement_initialization(processor=processus)

    def write_threetone_pulsessequence(self, t_3, t_2=10e-6, t_1 = 4e-6,  t_2start=None, t_1start=None, delete = False):
        '''
        WORK IN PROGRESS
        Putting in the awg memory the threetone pulses sequence and preparing the others instruments.
        Inputs:
            delete: True or False
            t_3 [ns]: time for the fixed frequency excitation tone

        '''

        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['threetone']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)

        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['thirdtone_channel'])
        self._awg_dict_coupling[self._awg_routing['thirdtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['thirdtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')

        amplitude = 0.9999

        self.set_temp_length_thirdtone(t_3)
        self.set_temp_start_thirdtone(100e-9)
        self.set_temp_length_secondtone(t_2)
        if t_2start == None:
            self.set_temp_start_secondtone(self.get_temp_length_thirdtone() + self.get_temp_start_thirdtone())
        else:
            self.set_temp_start_secondtone(t_2start)
        if t_2start == None:
            self.set_temp_start_firsttone(self.get_temp_start_secondtone() + self.get_temp_length_secondtone())
        else:
            self.set_temp_start_firsttone(t_1start)

        self.set_temp_length_firsttone(t_1)
        self.set_marker1_start(self.get_temp_start_firsttone())
        self.set_marker2_start(self.get_temp_start_thirdtone())

        ########################################################################
        nb_samples_smb =  round(1.2*(self.get_marker2_start()+self.get_marker2_width())*\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time_smb = np.arange(nb_samples_smb)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        nb_samples =  round( np.max( (self.get_marker1_start() + self.get_marker1_width()+\
                self.get_temp_start_firsttone() + self.get_temp_length_firsttone()+\
                self.get_marker2_start()+self.get_marker2_width() ) )*\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16


        time = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        if np.min((time_smb[-1], time[-1])) > self._trigger_time*1e-6:
            print 'Timing problem?'

        for i in CHANNEL:
            self._awg_waves['threetone']['binary'][i] = []
            self._awg_waves['threetone']['cosine'][i] = []
            self._awg_waves['threetone']['marker_trigger'][i] = []

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
                            self._awg_routing['thirdtone_channel'], self.get_number_segments_memorized() + 1)
        self._arbitrary_waveform_generator.send_waveform(segment1_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 1)


        # waiting time segments ################################################
        segment2_ro  = self.volt2bit_2(np.zeros(16*50))
        segment2_ex = self.volt2bit_2(np.zeros(16*50))

        # Putting the segment in AWG memory
        self._arbitrary_waveform_generator.send_waveform(segment2_ro,
                            self._awg_routing['firsttone_channel'], self.get_number_segments_memorized() + 2)
        self._arbitrary_waveform_generator.send_waveform(segment2_ex,
                            self._awg_routing['thirdtone_channel'], self.get_number_segments_memorized() + 2)
        self._arbitrary_waveform_generator.send_waveform(segment2_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 2)

        # excitations and readout segments ######################################
        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            amplitude, self._SSB_tone2.get_IF_frequency()*1e9]
        segment3_ex = self.volt2bit_2(self.cos(p_qb, time))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 3)

        p_qb2 = [self.get_temp_start_thirdtone(), self.get_temp_length_thirdtone(),
            amplitude, self._SSB_tone3.get_IF_frequency()*1e9]
        segment3_ex2 = self.volt2bit_2(self.cos(p_qb2, time))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex2,
                            self._awg_routing['thirdtone_channel'], self.get_number_segments_memorized() + 3)

        p = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
            amplitude, self.get_down_converted_frequency()*1e9]
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
                self._awg_waves['threetone']['binary'][self._awg_routing['firsttone_channel']].append(segment1_ro)
                self._awg_waves['threetone']['binary'][self._awg_routing['thirdtone_channel']].append(segment1_ro)
                self._awg_waves['threetone']['binary'][self._awg_routing['secondtone_channel']].append(segment1_ex)
                self._seq_list.append([1, self.get_number_segments_memorized() + 1, 0])

            elif i < self._M:
                # waiting time segments
                self._awg_waves['threetone']['binary'][self._awg_routing['firsttone_channel']].append(segment2_ro)
                self._awg_waves['threetone']['binary'][self._awg_routing['thirdtone_channel']].append(segment2_ro)
                self._awg_waves['threetone']['binary'][self._awg_routing['secondtone_channel']].append(segment2_ex)
                self._seq_list.append([1, self.get_number_segments_memorized() + 2, 0])
            else:
                # excitation and readout segments
                self._awg_waves['threetone']['binary'][self._awg_routing['firsttone_channel']].append(segment3_ro)
                self._awg_waves['threetone']['binary'][self._awg_routing['thirdtone_channel']].append(segment3_ex2)
                self._awg_waves['threetone']['binary'][self._awg_routing['secondtone_channel']].append(segment3_ex)

                self._seq_list.append([1, self.get_number_segments_memorized() + 3, 0])


        self._seq_list = np.array(self._seq_list)
        self.set_awg_segmentation({'threetone': self.get_number_segments_memorized() + 1 + np.arange(3)} )

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, self._sequence_dict['threetone'])

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['thirdtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, self._sequence_dict['threetone'])

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, self._sequence_dict['threetone'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['threetone'])

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
        # print self._trigger_time

        # switching ON the awg channels and markers
        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')
        self._awg_dict_output[self._awg_routing['thirdtone_channel']]('ON')
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('ON')


        ########################################################################

    def write_Rabi_pulsessequence(self, Tr_stop, Tr_step, Tr_start=0., T_meas=4e-6,
                    t_wait=0, delta_m1_start=0.,phi=0.,delete=False, t_rise=None):
        '''
        Putting in the awg memory the Rabi pulses sequence and preparing the others instruments.
        Inputs:

        '''
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        self._thirdtone=0


        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['rabi1']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)
            n_seg = self.get_awg_segmentation()['rabi2']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')

        amplitude_tone1 = 0.9999
        amplitude_tone2 = 0.9999

        self.set_temp_start_secondtone(Tr_stop + Tr_step  - Tr_start)
        self.set_temp_length_secondtone(Tr_start )
        self.set_temp_start_firsttone(self.get_temp_start_secondtone() + self.get_temp_length_secondtone() +t_wait )
        self.set_temp_length_firsttone(T_meas)
        self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)
        # self.set_marker1_width(self.get_temp_length_firsttone())

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

        if t_rise==None or t_rise ==0.:
            p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                    amplitude_tone1, self.get_down_converted_frequency()*1e9, phi]
            wave_ro_cos = self.cos_phi(p1, time1)
        else:
            if t_rise > self.get_temp_length_firsttone()/2.:
                print 'Be Careful: rising times should be less than the length of first tone...'
            else:
                p1 = [self.get_temp_start_firsttone(), t_rise, self.get_temp_length_firsttone(),
                        amplitude_tone1, self.get_down_converted_frequency()*1e9]
                wave_ro_cos = self.cos_rise(p1, time1)

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

            qb_ex_cos = self.cos(p2, time1) #change 20170505
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

    def write_Relaxation_pulsessequence(self, t_pi, t_wait_stop, t_wait_step, t_wait_start,t_meas=2e-6, delta_m1_start=0, delete=False):
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

        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['relaxation1']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)
            n_seg = self.get_awg_segmentation()['relaxation2']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)

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

        self.set_temp_start_secondtone(t_wait_stop + 2*t_wait_step - t_wait_start + 2*t_pi)
        self.set_temp_length_secondtone(t_pi)
        self.set_temp_start_firsttone(self.get_temp_start_secondtone() + self.get_temp_length_secondtone() + t_wait_start )
        self.set_temp_length_firsttone(t_meas)
        self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)
        # self.set_marker1_width(self.get_temp_length_firsttone())

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

            nb_samples2 =  round(1.5*(self.get_temp_start_secondtone() \
                    + self.get_temp_length_secondtone()  ) *\
                    self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
            time2 = np.arange(nb_samples2)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6
            self.set_temp_start_secondtone(self.get_temp_start_secondtone() - t_wait_step)


            qb_ex_cos = self.cos(p2, time1) #change 20170505
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

    def write_Relaxation_pulsessequence2(self, t_pi, t_wait_vec, t_meas=2e-6,
                            delete=False, delta_m1_start=0, before=0, t_rise=None):
        '''
        Putting in the awg memory the Relaxation pulses sequence and preparing the others instruments.
        Inputs:
            t_pi [s]:
            t_wait_vec [s]: array of the waiting time
        '''
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')

        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['relaxation1']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)
            n_seg = self.get_awg_segmentation()['relaxation2']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')


        amplitude_tone1 = 0.9999
        amplitude_tone2 = 0.9999

        self.set_temp_start_secondtone(t_wait_vec[-1] - t_wait_vec[0] + 2*t_pi)
        self.set_temp_length_secondtone(t_pi)
        self.set_temp_start_firsttone(self.get_temp_start_secondtone() + self.get_temp_length_secondtone() + t_wait_vec[0] )
        self.set_temp_length_firsttone(t_meas)
        self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)
        # self.set_marker1_width(self.get_temp_length_firsttone())

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
        N = len(t_wait_vec)

        if t_rise==None or t_rise ==0.:
            p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                    amplitude_tone1, self.get_down_converted_frequency()*1e9]
            wave_ro_cos = self.cos(p1, time1)
        else:
            if t_rise > self.get_temp_length_firsttone()/2.:
                print 'Be Careful: rising times should be less than the length of first tone...'
            else:
                p1 = [self.get_temp_start_firsttone(), t_rise ,self.get_temp_length_firsttone(),
                        amplitude_tone1, self.get_down_converted_frequency()*1e9]
                wave_ro_cos = self.cos_rise(p1, time1)


        wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
        wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                    self._awg_routing['board_marker'],
                    np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    wave_pulse_read_out)
        self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
            self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() + 1)

        wave_ro_marker = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1], time1)

        if before>0:
            print 'here'
            for i in np.arange(N+before):
                if i<before:
                    p2 = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                        0, self._SSB_tone2.get_IF_frequency()*1e9]
                    qb_ex_cos = self.cos(p2, time1) #change 20170505
                    qubit_excitation = self.volt2bit_2(qb_ex_cos)
                else:
                    p2=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                        amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

                    nb_samples2 =  round(1.5*(self.get_temp_start_secondtone() \
                            + self.get_temp_length_secondtone()  ) *\
                            self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
                    time2 = np.arange(nb_samples2)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6
                    self.set_temp_start_secondtone(t_wait_vec[-1] - t_wait_vec[0] + 2*t_pi - t_wait_vec[i-before]) # To test!

                    qb_ex_cos = self.cos(p2, time1) #change 20170505
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
        else:
            for i in np.arange(N):
                p2=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                    amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

                nb_samples2 =  round(1.5*(self.get_temp_start_secondtone() \
                        + self.get_temp_length_secondtone()  ) *\
                        self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
                time2 = np.arange(nb_samples2)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6
                self.set_temp_start_secondtone(t_wait_vec[-1] - t_wait_vec[0] + 2*t_pi - t_wait_vec[i]) # To test!

                qb_ex_cos = self.cos(p2, time1) #change 20170505
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

        self.set_awg_segmentation({'relaxation': self.get_number_segments_memorized() + 1+1 + np.arange(N)+before} )

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

    def write_Relaxation_pulsessequence_with_photons(self, t_pi, t_wait_vec,
            amplitude_photon=0., amplitude_RO=1., t_meas=2e-6, delete=False, before=0):
        '''
        Putting in the awg memory the Relaxation pulses sequence and preparing the others instruments.
        Inputs:
            t_pi [s]:
            t_wait_vec [s]: array of the waiting time
        '''
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')

        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['relaxation1']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)
            n_seg = self.get_awg_segmentation()['relaxation2']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')


        amplitude_tone1 = 0.9999*amplitude_RO
        amplitude_tone1_bis = 0.9999*amplitude_photon
        amplitude_tone2 = 0.9999

        self.set_temp_start_secondtone(t_wait_vec[-1] - t_wait_vec[0] + 2*t_pi)
        self.set_temp_length_secondtone(t_pi)
        self.set_temp_start_firsttone(self.get_temp_start_secondtone() + self.get_temp_length_secondtone() + t_wait_vec[0] )
        self.set_temp_length_firsttone(t_meas)
        self.set_marker1_start(self.get_temp_start_firsttone())
        # self.set_marker1_width(self.get_temp_length_firsttone())

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
        N = len(t_wait_vec)


        if before>0:

            for i in np.arange(N+before):
                p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                        amplitude_tone1, self.get_down_converted_frequency()*1e9]



                if i<before:
                    p1_bis = [100e-9 , self.get_temp_start_firsttone()-100e-9 ,
                            amplitude_tone1_bis, self.get_down_converted_frequency()*1e9]

                    p2 = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                        0, self._SSB_tone2.get_IF_frequency()*1e9]
                else:
                    p1_bis = [self.get_temp_start_secondtone() +self.get_temp_length_secondtone() ,
                    self.get_temp_start_firsttone() - (self.get_temp_start_secondtone() +self.get_temp_length_secondtone()) ,
                            amplitude_tone1_bis, self.get_down_converted_frequency()*1e9]

                    p2=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                        amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

                    self.set_temp_start_secondtone(t_wait_vec[-1] - t_wait_vec[0] + 2*t_pi - t_wait_vec[i-before]) # To test!

                qb_ex_cos = self.cos(p2, time1) #change 20170505
                qubit_excitation = self.volt2bit_2(qb_ex_cos)

                wave_ro_cos = self.cos(p1, time1) + self.cos(p1_bis, time1)

                wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
                wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                            self._awg_routing['board_marker'],
                            np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                            np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                            wave_pulse_read_out)
                self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
                    self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized()+2*i + 1)

                wave_ro_marker = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1], time1)


                self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
                    self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + 2*i + 2)

                self._awg_waves['relaxation']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
                self._awg_waves['relaxation']['binary'][self._awg_routing['secondtone_channel']].append(qubit_excitation)
                self._awg_waves['relaxation']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
                self._awg_waves['relaxation']['cosine'][self._awg_routing['secondtone_channel']].append(qb_ex_cos)
                self._awg_waves['relaxation']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)

                self._seq_list1.append([1, self.get_number_segments_memorized() + 2*i + 1, 0])
                self._seq_list2.append([1, self.get_number_segments_memorized() + 2*i + 2, 0])
        else:
            for i in np.arange(N):
                p2=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                    amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

                nb_samples2 =  round(1.5*(self.get_temp_start_secondtone() \
                        + self.get_temp_length_secondtone()  ) *\
                        self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
                time2 = np.arange(nb_samples2)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6
                self.set_temp_start_secondtone(t_wait_vec[-1] - t_wait_vec[0] + 2*t_pi - t_wait_vec[i]) # To test!

                qb_ex_cos = self.cos(p2, time1) #change 20170505
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

        self.set_awg_segmentation({'relaxation': self.get_number_segments_memorized() + 1+1 + np.arange(N)+before} )

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

        self._board_flag = 1
        if self._acquisition:
            processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                          self.get_down_converted_frequency()*1e9)
        else:
            processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                          self.get_down_converted_frequency()*1e9, t_ro=self.get_temp_length_firsttone())
        self._board.measurement_initialization(processor=processus)

    def write_Ramsey_pulsessequence(self, t_pi_o2, t_wait_stop, t_wait_step, t_wait_start,
                t_meas=2e-6, t_wait=0, delta_m1_start=0., delete=False, t_rise=None):
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
        self._thirdtone = 0

        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['ramsey1']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)
            n_seg = self.get_awg_segmentation()['ramsey2']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)

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

        self.set_temp_start_secondtone(t_wait_stop + t_wait_step - t_wait_start + 2*t_pi_o2) # should we put the 2*t_pi_o2?
        self.set_temp_length_secondtone(t_pi_o2)
        self.set_temp_start_firsttone(self.get_temp_start_secondtone() + 2*self.get_temp_length_secondtone() + t_wait_start +t_wait )
        self.set_temp_length_firsttone(t_meas)
        self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)
        # self.set_marker1_width(self.get_temp_length_firsttone())

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
        if t_rise==None or t_rise ==0.:
            p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                    amplitude_tone1, self.get_down_converted_frequency()*1e9]
            wave_ro_cos = self.cos(p1, time)
        else:
            if t_rise > self.get_temp_length_firsttone()/2.:
                print 'Be Careful: rising times should be less than the length of first tone...'
            else:
                p1 = [self.get_temp_start_firsttone(), t_rise, self.get_temp_length_firsttone(),
                        amplitude_tone1, self.get_down_converted_frequency()*1e9]
                wave_ro_cos = self.cos_rise(p1, time)

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
            self.set_temp_start_secondtone(self.get_temp_start_secondtone() - t_wait_step)
            pex1=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]
            pex2=[self.get_temp_start_firsttone()- t_wait - t_pi_o2 , self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]



            qb_ex_cos = self.cos(pex1, time) + self.cos(pex2, time)
            qubit_excitation = self.volt2bit_2(qb_ex_cos)
            self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
                self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + i + 2)

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

    def write_Echo_pulsessequence(self, t_pi_o2, t_wait_stop, t_wait_step, t_wait_start,t_meas=2e-6, delete=False):
        '''
        Work in progress
        Putting in the awg memory the Ramsey pulses sequence and preparing the others instruments.
        Inputs:
            t_pi_o2 [s]:
            t_wait_stop [s]:
            t_wait_step [s]:
            t_wait_start [s]:
        '''
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')

        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['echo1']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)
            n_seg = self.get_awg_segmentation()['echo2']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)

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

        self.set_temp_start_secondtone(2*(t_wait_stop + t_wait_step - t_wait_start+4*t_pi_o2))
        self.set_temp_length_secondtone(t_pi_o2)
        self.set_temp_start_firsttone(self.get_temp_start_secondtone() + 4*self.get_temp_length_secondtone() + t_wait_start )
        self.set_temp_length_firsttone(t_meas)
        self.set_marker1_start(self.get_temp_start_firsttone())
        # self.set_marker1_width(self.get_temp_length_firsttone())

        nb_samples =  round((self.get_temp_start_firsttone() \
                + self.get_temp_length_firsttone() + self.get_marker1_width() ) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        for ch in CHANNEL:
            self._awg_waves['echo']['binary'][ch] = []
            self._awg_waves['echo']['cosine'][ch] = []
            self._awg_waves['echo']['marker_trigger'][ch] = []

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
            # self.set_temp_start_secondtone(self.get_temp_start_secondtone() - t_wait_step)
            pex1=[self.get_temp_start_firsttone()-t_pi_o2, self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9] # last pi/2 pulse

            pex3=[self.get_temp_start_firsttone()-(i+1)*t_wait_step - 2*t_pi_o2, 2*self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9] # middle pi pulse

            pex2=[self.get_temp_start_firsttone()-2*(i+1)*t_wait_step - 3*t_pi_o2, self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9] # first pi/2 pulse



            qb_ex_cos = self.cos(pex1, time) + self.cos(pex2, time)  + self.cos(pex3, time)
            qubit_excitation = self.volt2bit_2(qb_ex_cos)
            self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
                self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + i + 2)

            self._awg_waves['echo']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
            self._awg_waves['echo']['binary'][self._awg_routing['secondtone_channel']].append(qubit_excitation)
            self._awg_waves['echo']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
            self._awg_waves['echo']['cosine'][self._awg_routing['secondtone_channel']].append(qb_ex_cos)
            self._awg_waves['echo']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)

            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + i + 2, 0])

        self._seq_list2 = np.array(self._seq_list2)
        self._seq_list1 = np.array(self._seq_list1)

        self.set_awg_segmentation({'echo': self.get_number_segments_memorized() + 1+1 + np.arange(N)} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        self._arbitrary_waveform_generator.set_channels_synchronised('ON')


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list1, self._sequence_dict['echo1'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list2, self._sequence_dict['echo2'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['echo2'])

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

    def prep_echo(self, cwf1, cwf2, average, nb_sequences, power_tone1, power_tone2):
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
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['echo1'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['echo2'])

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

        if self._acquisition:
            processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                          self.get_down_converted_frequency()*1e9)
        else:
            processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                          self.get_down_converted_frequency()*1e9, t_ro=self.get_temp_length_firsttone())
        self._board.measurement_initialization(processor=processus)

    def prep_IQ(self,average, counts, cwf1, power_tone1, cwf2='None', power_tone2 = 'None'):
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
        # self.set_src1_cw_frequency(cwf1)
        self._board.set_nb_sequence(counts)
        self._board.set_averaging(average)
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

            self.set_power_second_tone(power_tone2)
            amplitude2 = 10**((power_tone2)/10.)
            print amplitude2
            self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)

        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        # self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)

        print amplitude1
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)
        self.set_src1_cw_frequency(cwf1)

        processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                          self.get_down_converted_frequency()*1e9)
        self._board.measurement_initialization(processor=processus)


    def write_IQ(self, t1, t1_start=0.1e-6, t2=0., delta_m1_start=0., type='onetone', delete=False):
        '''
        Putting in the awg memory the IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        Inputs:
            type (str): onetone or twotone
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
            # self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')

        self._arbitrary_waveform_generator.set_clock_freq(1e3)
        # self._arbitrary_waveform_generator.set_clock_source('EXT')


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
            self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)
            # self.set_marker1_width(self.get_temp_length_firsttone())

        elif type == 'twotone':
            self.set_temp_start_secondtone(100e-9)
            self.set_temp_length_secondtone(t2)
            # self.set_temp_start_firsttone(t1_start)
            self.set_temp_start_firsttone( self.get_temp_start_secondtone() + self.get_temp_length_secondtone())
            self.set_temp_length_firsttone(t1)
            self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)
            # self.set_marker1_width(self.get_temp_length_firsttone())

        else:
            print 'problem with type'

        nb_samples =  round(1.1*(self.get_temp_start_firsttone() \
                + self.get_temp_length_firsttone() +self.get_temp_start_secondtone()+self.get_temp_length_secondtone()) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        print time1[-1]
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

        if type == 'twotone':
            pex1=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

            qb_ex_cos = self.cos(pex1, time1)
            qubit_excitation = self.volt2bit_2(qb_ex_cos)
            self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
                self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + 1)

            self._awg_waves['IQ']['binary'][self._awg_routing['secondtone_channel']].append(qubit_excitation)
            self._awg_waves['IQ']['cosine'][self._awg_routing['secondtone_channel']].append(qb_ex_cos)

        self._awg_waves['IQ']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
        self._awg_waves['IQ']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
        self._awg_waves['IQ']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)

        for i in np.arange(4):
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

        self._arbitrary_waveform_generator.set_trigger_source('EXT') #change of 20171003
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

    def write_IQ_phi(self, t1, t1_start=0.1e-6, t2=0., phi=0, type='onetone', delete=False):
        '''
        Putting in the awg memory the IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        Inputs:
            type (str): onetone or twotone
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
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')

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
            # self.set_marker1_width(self.get_temp_length_firsttone())

        elif type == 'twotone':
            self.set_temp_start_secondtone(100e-9)
            self.set_temp_length_secondtone(t2)
            # self.set_temp_start_firsttone(t1_start)
            self.set_temp_start_firsttone( self.get_temp_start_secondtone() + self.get_temp_length_secondtone())
            self.set_temp_length_firsttone(t1)
            self.set_marker1_start(self.get_temp_start_firsttone())
            # self.set_marker1_width(self.get_temp_length_firsttone())

        else:
            print 'problem with type'

        nb_samples =  round(1.1*(self.get_temp_start_firsttone() \
                + self.get_temp_length_firsttone() +self.get_temp_start_secondtone()+self.get_temp_length_secondtone()) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        print time1[-1]
        p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                amplitude_tone1, self.get_down_converted_frequency()*1e9, phi]
        wave_ro_cos = self.cos_phi(p1, time1)

        wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
        wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                    self._awg_routing['board_marker'],
                    np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    wave_pulse_read_out)

        self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
            self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() + 1)

        wave_ro_marker = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1], time1)

        if type == 'twotone':
            pex1=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

            qb_ex_cos = self.cos(pex1, time1)
            qubit_excitation = self.volt2bit_2(qb_ex_cos)
            self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
                self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + 1)

            self._awg_waves['IQ']['binary'][self._awg_routing['secondtone_channel']].append(qubit_excitation)
            self._awg_waves['IQ']['cosine'][self._awg_routing['secondtone_channel']].append(qb_ex_cos)

        self._awg_waves['IQ']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
        self._awg_waves['IQ']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
        self._awg_waves['IQ']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)

        for i in np.arange(4):
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

    def write_IQ_phase_stability(self, t1, t1_start=0.1e-6, t2=0., n_phi=4, type='onetone', delete=False):
        '''
        Putting in the awg memory the IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        Inputs:
            type (str): onetone or twotone
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
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')

        self._arbitrary_waveform_generator.set_clock_freq(1e3)

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

        elif type == 'twotone':
            self.set_temp_start_secondtone(100e-9)
            self.set_temp_length_secondtone(t2)
            self.set_temp_start_firsttone( self.get_temp_start_secondtone() + self.get_temp_length_secondtone())
            self.set_temp_length_firsttone(t1)
            self.set_marker1_start(self.get_temp_start_firsttone())
        else:
            print 'problem with type'

        nb_samples =  round(1.1*(self.get_temp_start_firsttone() \
                + self.get_temp_length_firsttone() +self.get_temp_start_secondtone()+self.get_temp_length_secondtone()) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        print time1[-1]





        for i in np.arange(n_phi):
            p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                    amplitude_tone1, self.get_down_converted_frequency()*1e9, i*2*np.pi/n_phi]
            wave_ro_cos = self.cos_phi(p1, time1)

            wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
            wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                        self._awg_routing['board_marker'],
                        np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                        np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                        wave_pulse_read_out)



            self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
                self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() +i + 1)
            if type == 'twotone':
                pex1=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                    amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

                qb_ex_cos = self.cos(pex1, time1)
                qubit_excitation = self.volt2bit_2(qb_ex_cos)
                self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
                    self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() +i + 1)

                self._awg_waves['IQ']['binary'][self._awg_routing['secondtone_channel']].append(qubit_excitation)
                self._awg_waves['IQ']['cosine'][self._awg_routing['secondtone_channel']].append(qb_ex_cos)

            wave_ro_marker = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1], time1)
            self._seq_list.append([1, self.get_number_segments_memorized() +i + 1, 0])

            self._awg_waves['IQ']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
            self._awg_waves['IQ']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
            self._awg_waves['IQ']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)

        self._seq_list= np.array(self._seq_list)

        self.set_awg_segmentation({'IQ': self.get_number_segments_memorized() + 1 + np.arange(n_phi)} )

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

    def write_IQ_pi(self, t1, t1_start=0.13e-6, t2=30e-9, phi=0., t2_start=0.1e-6, t_rise=None, delta_m1_start=0,delete=False):
        '''
        Putting in the awg memory the IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        Inputs:
            type (str): onetone or twotone
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
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')

        self._arbitrary_waveform_generator.set_clock_freq(1e3)
        # self._arbitrary_waveform_generator.set_clock_source('EXT')

        self._arbitrary_waveform_generator.set_trigger_source('EVEN')
        self._arbitrary_waveform_generator.seq_jump_source('BUS')
        self._arbitrary_waveform_generator.seq_mode('STEP')
        self._arbitrary_waveform_generator.set_trigger_mode('NORM')
        self._arbitrary_waveform_generator.set_trigger_timer_mode('TIME')
        self._arbitrary_waveform_generator.set_run_mode('TRIG')
        self._arbitrary_waveform_generator.set_func_mode('SEQ')
        self._arbitrary_waveform_generator.set_trigger_timer_time(self._trigger_time)

        # print 'awg period [us]:', self.get_trigger_time()

        amplitude_tone1 = 0.9999
        amplitude_tone2 = 0.9999

        for ch in CHANNEL:
            self._awg_waves['IQ']['binary'][ch] = []
            self._awg_waves['IQ']['cosine'][ch] = []
            self._awg_waves['IQ']['marker_trigger'][ch] = []

        self._seq_list1 = []
        self._seq_list2 = []


        self.set_temp_start_secondtone(t2_start)
        self.set_temp_length_secondtone(t2)
        self.set_temp_start_firsttone(t1_start)
        # self.set_temp_start_firsttone( self.get_temp_start_secondtone() + self.get_temp_length_secondtone())
        self.set_temp_length_firsttone(t1)
        self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)
            # self.set_marker1_width(self.get_temp_length_firsttone())


        nb_samples =  round(1.1*(self.get_temp_start_firsttone() \
                + self.get_temp_length_firsttone() +self.get_temp_start_secondtone()+self.get_temp_length_secondtone()) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        # print time1[-1]
        # print 'awg period [us]:', self.get_trigger_time()
        if t_rise == None:
            p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                    amplitude_tone1, self.get_down_converted_frequency()*1e9, phi]
            wave_ro_cos = self.cos_phi(p1, time1)
        else:
            if t_rise > self.get_temp_length_firsttone()/2.:
                print 'Be Careful: rising time should be less than the length of first tone...'
            else:
                p1 = [self.get_temp_start_firsttone(), t_rise, self.get_temp_length_firsttone(),
                        amplitude_tone1, self.get_down_converted_frequency()*1e9]
                wave_ro_cos = self.cos_rise(p1, time1)


        wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
        wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                    self._awg_routing['board_marker'],
                    np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    wave_pulse_read_out)

        self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
            self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() + 1)

        wave_ro_marker = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1], time1)


        pex1=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

        qb_ex_cos = self.cos(pex1, time1)
        qubit_excitation = self.volt2bit_2(qb_ex_cos)
        self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
            self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + 2)

        pex2=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            0, self._SSB_tone2.get_IF_frequency()*1e9]

        qb_ex_cos = self.cos(pex2, time1)
        qubit_excitation = self.volt2bit_2(qb_ex_cos)
        self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
            self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + 3)

        self._awg_waves['IQ']['binary'][self._awg_routing['secondtone_channel']].append(qubit_excitation)
        self._awg_waves['IQ']['cosine'][self._awg_routing['secondtone_channel']].append(qb_ex_cos)

        self._awg_waves['IQ']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
        self._awg_waves['IQ']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
        self._awg_waves['IQ']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)

        for i in np.arange(1): # without pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 3, 0])
        for i in np.arange(1): # with pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 2, 0])
        for i in np.arange(1): # without pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 3, 0])
        for i in np.arange(1): # with pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 2, 0])

        self._seq_list1 = np.array(self._seq_list1)
        self._seq_list2 = np.array(self._seq_list2)

        self.set_awg_segmentation({'IQ': self.get_number_segments_memorized() + 1 + np.arange(3)} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)


        self._arbitrary_waveform_generator.set_channels_synchronised('ON')
        print 'awg period [us]:', self.get_trigger_time()


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list1, self._sequence_dict['IQ1'])


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list2, self._sequence_dict['IQ2'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ2'])



        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')

        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        print 'awg period [us]:', self.get_trigger_time()

    def write_IQ_pi_2steps(self, t1_strong, t1, t1_start=0.13e-6, t2=30e-9, phi=0., a=0.1, delta_m1_start=0,delete=False):
        '''
        Putting in the awg memory the IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        Inputs:
            type (str): onetone or twotone
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
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')

        self._arbitrary_waveform_generator.set_clock_freq(1e3)
        # self._arbitrary_waveform_generator.set_clock_source('EXT')

        self._arbitrary_waveform_generator.set_trigger_source('EVEN')
        self._arbitrary_waveform_generator.seq_jump_source('BUS')
        self._arbitrary_waveform_generator.seq_mode('STEP')
        self._arbitrary_waveform_generator.set_trigger_mode('NORM')
        self._arbitrary_waveform_generator.set_trigger_timer_mode('TIME')
        self._arbitrary_waveform_generator.set_run_mode('TRIG')
        self._arbitrary_waveform_generator.set_func_mode('SEQ')
        self._arbitrary_waveform_generator.set_trigger_timer_time(self._trigger_time)

        # print 'awg period [us]:', self.get_trigger_time()

        amplitude_tone1 = 0.9999
        amplitude_tone2 = 0.9999

        for ch in CHANNEL:
            self._awg_waves['IQ']['binary'][ch] = []
            self._awg_waves['IQ']['cosine'][ch] = []
            self._awg_waves['IQ']['marker_trigger'][ch] = []

        self._seq_list1 = []
        self._seq_list2 = []


        self.set_temp_start_secondtone(100e-9)
        self.set_temp_length_secondtone(t2)
        self.set_temp_start_firsttone(t1_start)
        # self.set_temp_start_firsttone( self.get_temp_start_secondtone() + self.get_temp_length_secondtone())
        self.set_temp_length_firsttone(t1)
        self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)
            # self.set_marker1_width(self.get_temp_length_firsttone())


        nb_samples =  round(1.1*(self.get_temp_start_firsttone() \
                + self.get_temp_length_firsttone() +self.get_temp_start_secondtone()+self.get_temp_length_secondtone()) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        # print time1[-1]
        # print 'awg period [us]:', self.get_trigger_time()
        p1 = [self.get_temp_start_firsttone()+t1_strong, self.get_temp_length_firsttone()-t1_strong,
                amplitude_tone1*a, self.get_down_converted_frequency()*1e9, phi]
        p1_strong = [self.get_temp_start_firsttone(), t1_strong,
                amplitude_tone1, self.get_down_converted_frequency()*1e9, phi]
        wave_ro_cos = self.cos_phi(p1, time1) + self.cos_phi(p1_strong, time1)

        wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
        wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                    self._awg_routing['board_marker'],
                    np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    wave_pulse_read_out)

        self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
            self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() + 1)

        wave_ro_marker = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1], time1)


        pex1=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

        qb_ex_cos = self.cos(pex1, time1)
        qubit_excitation = self.volt2bit_2(qb_ex_cos)
        self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
            self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + 2)

        pex2=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            0, self._SSB_tone2.get_IF_frequency()*1e9]

        qb_ex_cos = self.cos(pex2, time1)
        qubit_excitation = self.volt2bit_2(qb_ex_cos)
        self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
            self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + 3)

        self._awg_waves['IQ']['binary'][self._awg_routing['secondtone_channel']].append(qubit_excitation)
        self._awg_waves['IQ']['cosine'][self._awg_routing['secondtone_channel']].append(qb_ex_cos)

        self._awg_waves['IQ']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
        self._awg_waves['IQ']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
        self._awg_waves['IQ']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)

        for i in np.arange(1): # without pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 3, 0])
        for i in np.arange(1): # with pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 2, 0])
        for i in np.arange(1): # without pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 3, 0])
        for i in np.arange(1): # with pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 2, 0])

        self._seq_list1 = np.array(self._seq_list1)
        self._seq_list2 = np.array(self._seq_list2)

        self.set_awg_segmentation({'IQ': self.get_number_segments_memorized() + 1 + np.arange(3)} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)


        self._arbitrary_waveform_generator.set_channels_synchronised('ON')
        print 'awg period [us]:', self.get_trigger_time()


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list1, self._sequence_dict['IQ1'])


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list2, self._sequence_dict['IQ2'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ2'])



        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')

        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        print 'awg period [us]:', self.get_trigger_time()

    def prep_timing(self, cwf1, average, power_tone1, average_type='over_seq'):
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
        # self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)
        print amplitude1
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)

        # processus = dt.Average_time(self._board.get_acquisition_time(), self._board.get_samplerate())
        if average_type=='over_seq':
            processus = dt.Average()
        else:
            processus = dt.Average_time()
        self._board.measurement_initialization(processor=processus)

    def prep_timing_pi(self, cwf1, cwf2, average, nb_seq, power_tone1, power_tone2):
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
        self._microwave_generator2.set_gui_update('OFF')
        self._microwave_generator2.set_freqsweep('off')
        self.set_src2_cw_frequency(cwf2)

        self._board.set_nb_sequence(nb_seq)
        self._board.set_averaging(average)
        print self._board.get_averaging()


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ'])
        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ'])
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')

        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        # self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)
        # print amplitude1
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)

        self.set_power_second_tone(power_tone2)
        amplitude2 = 10**((power_tone2)/10.)
        # print amplitude1
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)

        # processus = dt.Average_time(self._board.get_acquisition_time(), self._board.get_samplerate())
        processus = dt.Average_time()
        self._board.measurement_initialization(processor=processus)

    def prep_timing_IQ(self, cwf1, average, power_tone1, f_cutoff, order, acquisition_time='None'):
        '''
        Preparing the instruments for a timing measurement.
        This function do not write in the awg memory. You need to use write_IQ with
        onetone to test.
        Inputs:
            cwf1 [GHz]: continuous wave frequency of the first tone
            average (int): number of averaging of the V(t) curve.
            f_cutoff [MHz]: cut off frequency of the numerical RC filter
        '''
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(cwf1)
        self._board.set_nb_sequence(4)
        self._board.set_averaging(average)
        # print self._board.get_averaging()
        if acquisition_time != 'None':
            acq_time = np.int(acquisition_time/128)*128
            self._board.set_acquisition_time(acq_time)


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ'])
        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)
        # print amplitude1
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)

        processus = dt.Average_IQ(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                      self.get_down_converted_frequency()*1e9, f_cutoff*1e6, order)
        self._board.measurement_initialization(processor=processus)

    def prep_timing_IQ_pi(self, cwf1, cwf2, average, power_tone1, power_tone2, f_cutoff, order, acquisition_time='None'):
        '''
        Preparing the instruments for a timing measurement.
        This function do not write in the awg memory. You need to use write_IQ with
        onetone to test.
        Inputs:
            cwf1 [GHz]: continuous wave frequency of the first tone
            average (int): number of averaging of the V(t) curve.
            f_cutoff [MHz]: cut off frequency of the numerical RC filter
            order (int): order of the RC filter
            acquisition_time [ns]: time of acquisition
        '''
        # self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(cwf1)

        self._microwave_generator2.set_gui_update('OFF')
        self._microwave_generator2.set_freqsweep('off')
        self.set_src2_cw_frequency(cwf2)

        self._board.set_nb_sequence(4)
        self._board.set_averaging(average)
        if acquisition_time != 'None':
            acq_time = np.int(acquisition_time/128)*128
            self._board.set_acquisition_time(acq_time)
        # print self._board.get_averaging()


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ1'])
        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ2'])
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')

        self._arbitrary_waveform_generator.set_trigger_source('EVEN')
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')


        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)
        # print amplitude1
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)

        self.set_power_second_tone(power_tone2)
        amplitude2 = 10**((power_tone2)/10.)
        # print amplitude1
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)



        processus = dt.Average_IQ(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                      self.get_down_converted_frequency()*1e9, f_cutoff*1e6, order)
        self._board.measurement_initialization(processor=processus)

    def write_Ramsey_Starckshift_pulsessequence(self, t_pi_o2, t_wait_stop, t_wait_step, t_wait_start,
                amplitude_photon,t_meas=2e-6, t_protect = 100e-9, delete=False):
        '''
        Work in progress...
        Putting in the awg memory the Ramsey pulses sequence and preparing the others instruments.
        Inputs:
            t_pi_o2 [s]:
            t_wait_stop [s]:
            t_wait_step [s]:
            t_wait_start [s]:
            p_photon [dB]:
        '''
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')

        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['ramsey1']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)
            n_seg = self.get_awg_segmentation()['ramsey2']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)

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

        self.set_temp_start_secondtone(t_wait_stop + t_wait_step - t_wait_start + 2*t_pi_o2)
        self.set_temp_length_secondtone(t_pi_o2)
        self.set_temp_start_firsttone(self.get_temp_start_secondtone() + 2*self.get_temp_length_secondtone() + t_wait_start )
        self.set_temp_length_firsttone(t_meas)
        self.set_marker1_start(self.get_temp_start_firsttone())
        # self.set_marker1_width(self.get_temp_length_firsttone())

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

        # amplitude_photon = 10**((p_photon)/10.)

        N = len(np.arange(t_wait_start, t_wait_stop, t_wait_step))
        for i in np.arange(N):
            p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                    amplitude_tone1, self.get_down_converted_frequency()*1e9]

            # p2 = [self.get_temp_start_secondtone()+t_pi_o2, t_wait_start+i*t_wait_step,
            #         amplitude_photon, self.get_down_converted_frequency()*1e9]

            if t_wait_start+i*t_wait_step - t_protect>0:
                p2 = [self.get_temp_start_secondtone()+t_pi_o2, t_wait_start+i*t_wait_step- t_protect,
                        amplitude_photon, self._SSB_tone2.get_IF_frequency()*1e9]
            else:
                p2 = [self.get_temp_start_secondtone()+t_pi_o2, t_wait_start+i*t_wait_step,
                        amplitude_photon, self._SSB_tone2.get_IF_frequency()*1e9]

            wave_ro_cos = self.cos(p1, time) + self.cos(p2, time)

            wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
            wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                        self._awg_routing['board_marker'],
                        np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                        np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                        wave_pulse_read_out)

            self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
                self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() + i + 1)

            wave_ro_marker = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1], time)


            pex1=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]
            pex2=[self.get_temp_start_firsttone() - t_pi_o2, self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

            self.set_temp_start_secondtone(self.get_temp_start_secondtone() - t_wait_step)

            qb_ex_cos = self.cos(pex1, time) + self.cos(pex2, time)
            qubit_excitation = self.volt2bit_2(qb_ex_cos)
            self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
                self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + N + i + 1)

            self._awg_waves['ramsey']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
            self._awg_waves['ramsey']['binary'][self._awg_routing['secondtone_channel']].append(qubit_excitation)
            self._awg_waves['ramsey']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
            self._awg_waves['ramsey']['cosine'][self._awg_routing['secondtone_channel']].append(qb_ex_cos)
            self._awg_waves['ramsey']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)

            self._seq_list1.append([1, self.get_number_segments_memorized() + i + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + N + i + 1, 0])

        self._seq_list2 = np.array(self._seq_list2)
        self._seq_list1 = np.array(self._seq_list1)

        self.set_awg_segmentation({'ramsey': self.get_number_segments_memorized() + 1 + 2*np.arange(N)} )

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

    def write_n_photon_pulsessequence(self, t_pi, t_photon, amp_stop, amp_step, amp_start=0., T_meas=4e-6, delete=False):
        '''
        Work in progress
        Putting in the awg memory the Rabi pulses sequence and preparing the others instruments.
        Inputs:

        '''
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')

        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['n_photon']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')

        amplitude_tone1 = 0.9999
        amplitude_tone2 = 0.9999

        self.set_temp_start_secondtone(100e-9)
        self.set_temp_length_secondtone(t_pi )
        self.set_temp_start_firsttone(self.get_temp_start_secondtone() + self.get_temp_length_secondtone()+t_photon )
        self.set_temp_length_firsttone(T_meas)
        self.set_marker1_start(self.get_temp_start_firsttone())
        # self.set_marker1_width(self.get_temp_length_firsttone())

        nb_samples1 =  round(( self.get_temp_start_firsttone() + \
                np.max(self.get_temp_length_firsttone() +self.get_marker1_width()) ) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples1)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        for ch in CHANNEL:
            self._awg_waves['n_photon']['binary'][ch] = []
            self._awg_waves['n_photon']['cosine'][ch] = []
            self._awg_waves['n_photon']['marker_trigger'][ch] = []

        self._seq_list1 = []
        self._seq_list2 = []
        N = len(np.arange(amp_start, amp_stop, amp_step))



        for i, amplitude in enumerate(np.arange(amp_start, amp_stop, amp_step)):
            p2=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

            qb_ex_cos = self.cos(p2, time1)
            qubit_excitation = self.volt2bit_2(qb_ex_cos)
            self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
                self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + 2*i + 2)

            p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                    amplitude_tone1, self.get_down_converted_frequency()*1e9]

            p1_bis = [self.get_temp_start_firsttone()-t_photon, t_photon,
                    amplitude, self.get_down_converted_frequency()*1e9]

            wave_ro_cos = self.cos(p1, time1) + self.cos(p1_bis, time1)

            wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
            wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                        self._awg_routing['board_marker'],
                        np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                        np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                        wave_pulse_read_out)
            self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
                self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() +2*i+ 1)

            wave_ro_marker = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1], time1)



            self._awg_waves['n_photon']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
            self._awg_waves['n_photon']['binary'][self._awg_routing['secondtone_channel']].append(qubit_excitation)
            self._awg_waves['n_photon']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
            self._awg_waves['n_photon']['cosine'][self._awg_routing['secondtone_channel']].append(qb_ex_cos)
            self._awg_waves['n_photon']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)

            self._seq_list1.append([1, self.get_number_segments_memorized() +2*i+ 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 2*i + 2, 0])

        self._seq_list1 = np.array(self._seq_list1)
        self._seq_list2 = np.array(self._seq_list2)
        self.set_awg_segmentation({'n_photon': self.get_number_segments_memorized() + 1 + 1 + np.arange(N)} )
        # self.set_awg_segmentation({'rabi2': self.get_number_segments_memorized() + 1 + np.arange(N)} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        self._arbitrary_waveform_generator.set_channels_synchronised('ON')


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list1, self._sequence_dict['n_photon'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list2, self._sequence_dict['n_photon'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['n_photon'])

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

    def prep_n_photon(self, cwf1, cwf2, average, nb_sequences, power_tone1, power_tone2, mw = 2):
        '''
        Preparing the instruments for a Rabi pulses sequence. This function do not
        write in the awg memory.
        Inputs:
            cwf1 [GHz]: continuous wave frequency of the first tone
            cwf2 [GHz]: continuous wave frequency of the second tone
            average (int): number of total averaging
        '''
        # self._microwave_generator1.set_gui_update('OFF')
        # self._microwave_generator2.set_gui_update('OFF')
        for i in CHANNEL:
            self._awg_dict_output[i]('OFF')

        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(cwf1)
        if mw ==2:
            self._microwave_generator2.set_freqsweep('off')
            self.set_src2_cw_frequency(cwf2)
            self._microwave_generator2.set_power(self._SSB_tone2.get_LO_power())
        elif mw == 3:
            self._microwave_generator3.set_freqsweep('off')
            self.set_src3_cw_frequency(cwf2)
            self._microwave_generator3.set_power(self._SSB_tone3.get_LO_power())

        self._board.set_nb_sequence(nb_sequences)
        self._board.set_averaging(average)

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['n_photon'])
        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        self.set_power_first_tone(power_tone1)
        amplitude1 = 10**((power_tone1)/10.)
        self.set_power_second_tone(power_tone2)
        amplitude2 = 10**((power_tone2)/10.)
        print amplitude1, amplitude2
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude1)

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['n_photon'])
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2*amplitude2)


        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        if self._acquisition:
            processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                          self.get_down_converted_frequency()*1e9)
        else:
            processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                          self.get_down_converted_frequency()*1e9, t_ro=self.get_temp_length_firsttone())
        self._board.measurement_initialization(processor=processus)

    def write_Starck_pi2phi_pulsessequence(self, t_pi_o2, t_wait_length, phi_start, phi_step, phi_stop,
                amplitude_photon,t_meas=2e-6, t_reset_photon = 100e-9, delete=False):
        '''
        Work in progress...
        Putting in the awg memory the Ramsey pulses sequence and preparing the others instruments.
        Inputs:
            t_pi_o2 [s]:
            p_photon [dB]:
        '''
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')

        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['ramsey1']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)
            n_seg = self.get_awg_segmentation()['ramsey2']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')

        amplitude_tone1 = 0.9999
        amplitude_tone2 = 0.9999

        self.set_temp_start_secondtone(100e-9)
        self.set_temp_length_secondtone(t_pi_o2)
        self.set_temp_start_firsttone(self.get_temp_start_secondtone()+t_wait_length + 2*self.get_temp_length_secondtone()  )
        self.set_temp_length_firsttone(t_meas)
        self.set_marker1_start(self.get_temp_start_firsttone())
        # self.set_marker1_width(self.get_temp_length_firsttone())

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

        # amplitude_photon = 10**((p_photon)/10.)
        phi_vec = np.arange(phi_start, phi_stop, phi_step)
        N = len(phi_vec)
        for i in np.arange(N):
            p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                    amplitude_tone1, self.get_down_converted_frequency()*1e9]

            p2 = [self.get_temp_start_secondtone()+t_pi_o2, t_wait_length - t_reset_photon,
                    amplitude_photon, self._SSB_tone2.get_IF_frequency()*1e9]


            wave_ro_cos = self.cos(p1, time) + self.cos(p2, time)

            wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
            wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                        self._awg_routing['board_marker'],
                        np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                        np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                        wave_pulse_read_out)

            self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
                self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() + i + 1)

            wave_ro_marker = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1], time)


            pex1=[self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9, 0.]

            pex2=[self.get_temp_start_firsttone() - t_pi_o2, self.get_temp_length_secondtone(),
                amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9, phi_vec[i]]

            qb_ex_cos = self.cos_phi(pex1, time) + self.cos_phi(pex2, time)
            qubit_excitation = self.volt2bit_2(qb_ex_cos)
            self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
                self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + N + i + 1)

            self._awg_waves['ramsey']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
            self._awg_waves['ramsey']['binary'][self._awg_routing['secondtone_channel']].append(qubit_excitation)
            self._awg_waves['ramsey']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
            self._awg_waves['ramsey']['cosine'][self._awg_routing['secondtone_channel']].append(qb_ex_cos)
            self._awg_waves['ramsey']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)

            self._seq_list1.append([1, self.get_number_segments_memorized() + i + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + N + i + 1, 0])

        self._seq_list2 = np.array(self._seq_list2)
        self._seq_list1 = np.array(self._seq_list1)

        self.set_awg_segmentation({'ramsey': self.get_number_segments_memorized() + 1 + 2*np.arange(N)} )

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

    def write_IQ_trigger_front(self, t1 , t1_start=0.1e-6, t2=0., type='onetone', delete=False):
        '''
        Putting in the awg memory the IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        Inputs:
            type (str): onetone or twotone
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
        else:
            print 'problem with type'

        nb_samples =  round(1.1*(self.get_temp_start_firsttone() \
                + self.get_temp_length_firsttone() +self.get_temp_start_secondtone()+self.get_temp_length_secondtone()) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        print time1[-1]
        p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                amplitude_tone1, self.get_down_converted_frequency()*1e9]
        wave_ro_cos = self.cos(p1, time1)

        wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)

        self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
            self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() + 1)

        wave_ro_marker = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1.], time1)
        wave_ro_marker = self.volt2bit_2(wave_ro_marker)
        self._arbitrary_waveform_generator.send_waveform(wave_ro_marker,
            2,  self.get_number_segments_memorized() + 1)



        self._awg_waves['IQ']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
        self._awg_waves['IQ']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
        self._awg_waves['IQ']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)

        for i in np.arange(4):
            self._seq_list.append([1, self.get_number_segments_memorized() + 1, 0])

        self._seq_list= np.array(self._seq_list)

        self.set_awg_segmentation({'IQ': self.get_number_segments_memorized() + 1 + np.arange(1)} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[2]('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        self._arbitrary_waveform_generator.set_channels_synchronised('ON')


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, self._sequence_dict['IQ'])
        self._arbitrary_waveform_generator.channel_select(2)
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

        self._awg_dict_output[2]('ON')

        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')

    def write_IQpi_several_RO(self, t2, t1_1, t1_2, t2_start=0.6e-6 , t1_1start=0.1e-6, t1_2start=0.7e-6, delta_m1_start=0, t_rise=None, delete=False):
        '''
        Putting in the awg memory the IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        Inputs:
            type (str): onetone or twotone

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
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')

        self.clock_AWG()
        self.usual_setting_AWG(nb_channel=2)

        amplitude_tone1 = 0.9999
        amplitude_tone2 = 0.9999

        self._seq_list1 = []
        self._seq_list2 = []

        self.set_temp_length_secondtone(t2)
        self.set_temp_start_secondtone(t2_start)

        self.set_temp_start_firsttone(t1_1start )
        self.set_temp_length_firsttone(t1_1)
        self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)

        nb_samples =  round(1.5*(self.get_temp_start_firsttone() \
                + self.get_temp_length_firsttone()+t1_2start+t1_2 ) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6


        if t_rise==None:
            p1 = [t1_1start,  t1_1,
                    amplitude_tone1, self.get_down_converted_frequency()*1e9]
            p2 = [t1_2start,  t1_2,
                    amplitude_tone1, self.get_down_converted_frequency()*1e9]

            wave_ro_cos = self.cos(p1, time1) + self.cos(p2, time1)
        else:
            if 2*t_rise > t1_1 or 2*t_rise> t1_2:
                print 'Be Careful: rising time should be less than the length of first tone...'
            else:
                p1 = [t1_1start,  t_rise, t1_1,
                        amplitude_tone1, self.get_down_converted_frequency()*1e9]
                p2 = [t1_2start,  t_rise, t1_2,
                        amplitude_tone1, self.get_down_converted_frequency()*1e9]

                wave_ro_cos = self.cos_rise(p1, time1) + self.cos_rise(p2, time1)


        wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
        wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                self._awg_routing['board_marker'],
                np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                wave_pulse_read_out)

        self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
            self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() +1 )


        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time1))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 2)

        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            0, self._SSB_tone2.get_IF_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time1))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 3)

        for i in np.arange(2):
             # without pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 3, 0])
            # with pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 2, 0])


        self._seq_list1= np.array(self._seq_list1)
        self._seq_list2= np.array(self._seq_list2)

        self.set_awg_segmentation({'IQ': self.get_number_segments_memorized() + 1 + np.arange(3)} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        self._arbitrary_waveform_generator.set_channels_synchronised('ON')


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list1, self._sequence_dict['IQ1'])


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list2, self._sequence_dict['IQ2'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ2'])



        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')

        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')

    def write_IQpi_several_RO_rise(self, t2, t_rise, t1_1, t1_2, t2_start=0.6e-6 , t1_1start=0.1e-6, t1_2start=0.7e-6, delta_m1_start=0, delete=False):
        '''
        Putting in the awg memory the IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        Inputs:
            type (str): onetone or twotone

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
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')

        self.clock_AWG()
        self.usual_setting_AWG(nb_channel=2)

        amplitude_tone1 = 0.9999
        amplitude_tone2 = 0.9999

        self._seq_list1 = []
        self._seq_list2 = []

        self.set_temp_length_secondtone(t2)
        self.set_temp_start_secondtone(t2_start)

        self.set_temp_start_firsttone(t1_1start )
        self.set_temp_length_firsttone(t1_1)
        self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)

        nb_samples =  round(1.5*(self.get_temp_start_firsttone() \
                + self.get_temp_length_firsttone()+t1_2start+t1_2 ) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6



        p1 = [t1_1start,  t_rise, t1_1,
                amplitude_tone1, self.get_down_converted_frequency()*1e9]
        p2 = [t1_2start,  t_rise, t1_2,
                amplitude_tone1, self.get_down_converted_frequency()*1e9]

        wave_ro_cos = self.cos_rise(p1, time1) + self.cos_rise(p2, time1)

        wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
        wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                self._awg_routing['board_marker'],
                np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                wave_pulse_read_out)

        self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
            self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() +1 )


        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time1))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 2)

        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            0, self._SSB_tone2.get_IF_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time1))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 3)

        for i in np.arange(2):
             # without pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 3, 0])
            # with pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 2, 0])


        self._seq_list1= np.array(self._seq_list1)
        self._seq_list2= np.array(self._seq_list2)

        self.set_awg_segmentation({'IQ': self.get_number_segments_memorized() + 1 + np.arange(3)} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        self._arbitrary_waveform_generator.set_channels_synchronised('ON')


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list1, self._sequence_dict['IQ1'])


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list2, self._sequence_dict['IQ2'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ2'])



        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')

        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')

    def write_IQ_alwayspi_several_RO(self, t2, t1_1, t1_2, t2_start=0.6e-6 , t1_1start=0.1e-6, t1_2start=0.7e-6, delta_m1_start=0, delete=False):
        '''
        Putting in the awg memory the IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        Inputs:
            type (str): onetone or twotone

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
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')

        self.clock_AWG()
        self.usual_setting_AWG(nb_channel=2)

        amplitude_tone1 = 0.9999
        amplitude_tone2 = 0.9999

        self._seq_list1 = []
        self._seq_list2 = []

        self.set_temp_length_secondtone(t2)
        self.set_temp_start_secondtone(t2_start)

        self.set_temp_start_firsttone(t1_1start )
        self.set_temp_length_firsttone(t1_1)
        self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)

        nb_samples =  round(1.5*(self.get_temp_start_firsttone() \
                + self.get_temp_length_firsttone()+t1_2start+t1_2 ) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6



        p1 = [t1_1start,  t1_1,
                amplitude_tone1, self.get_down_converted_frequency()*1e9]
        p2 = [t1_2start,  t1_2,
                amplitude_tone1, self.get_down_converted_frequency()*1e9]

        wave_ro_cos = self.cos(p1, time1) + self.cos(p2, time1)

        wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
        wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                self._awg_routing['board_marker'],
                np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                wave_pulse_read_out)

        self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
            self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() +1 )


        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time1))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 2)

        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            0, self._SSB_tone2.get_IF_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time1))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 3)

        for i in np.arange(2):
             # with pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 2, 0])
            # with pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 2, 0])


        self._seq_list1= np.array(self._seq_list1)
        self._seq_list2= np.array(self._seq_list2)

        self.set_awg_segmentation({'IQ': self.get_number_segments_memorized() + 1 + np.arange(3)} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        self._arbitrary_waveform_generator.set_channels_synchronised('ON')


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list1, self._sequence_dict['IQ1'])


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list2, self._sequence_dict['IQ2'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ2'])



        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')

        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')

    def write_IQ_alwayspi_rising_several_RO(self, t2, t1_1, t1_2, t_rise=0, t2_start=0.6e-6 , t1_1start=0.1e-6, t1_2start=0.7e-6, delta_m1_start=0, delete=False):
        '''
        Putting in the awg memory the IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        Inputs:
            type (str): onetone or twotone

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
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')

        self.clock_AWG()
        self.usual_setting_AWG(nb_channel=2)

        amplitude_tone1 = 0.9999
        amplitude_tone2 = 0.9999

        self._seq_list1 = []
        self._seq_list2 = []

        self.set_temp_length_secondtone(t2)
        self.set_temp_start_secondtone(t2_start)

        self.set_temp_start_firsttone(t1_1start )
        self.set_temp_length_firsttone(t1_1)
        self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)

        nb_samples =  round(1.5*(self.get_temp_start_firsttone() \
                + self.get_temp_length_firsttone()+t1_2start+t1_2 ) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6



        p1 = [t1_1start, t_rise, t1_1,
                amplitude_tone1, self.get_down_converted_frequency()*1e9]
        p2 = [t1_2start, t_rise,  t1_2,
                amplitude_tone1, self.get_down_converted_frequency()*1e9]

        wave_ro_cos = self.cos_rise(p1, time1) + self.cos_rise(p2, time1)

        wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
        wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                self._awg_routing['board_marker'],
                np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                wave_pulse_read_out)

        self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
            self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() +1 )


        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time1))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 2)

        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            0, self._SSB_tone2.get_IF_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time1))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 3)

        for i in np.arange(2):
             # with pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 2, 0])
            # with pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 2, 0])


        self._seq_list1= np.array(self._seq_list1)
        self._seq_list2= np.array(self._seq_list2)

        self.set_awg_segmentation({'IQ': self.get_number_segments_memorized() + 1 + np.arange(3)} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        self._arbitrary_waveform_generator.set_channels_synchronised('ON')


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list1, self._sequence_dict['IQ1'])


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list2, self._sequence_dict['IQ2'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ2'])



        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')

        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')

    def write_IQpi_several_RO_bifurcationshape(self, t2, t1_1, t1_2, duty_cycle=1., diff_PdB=0.,
        t2_start=0.6e-6 , t1_1start=0.1e-6, t1_2start=0.7e-6, delta_m1_start=0,
        t_rise=None, delete=False):
        '''
        Putting in the awg memory the IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        Inputs:
            type (str): onetone or twotone

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
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')

        self.clock_AWG()
        self.usual_setting_AWG(nb_channel=2)

        amplitude_tone1 = 0.9999
        amplitude_tone2 = 0.9999

        self._seq_list1 = []
        self._seq_list2 = []

        self.set_temp_length_secondtone(t2)
        self.set_temp_start_secondtone(t2_start)

        self.set_temp_start_firsttone(t1_1start )
        self.set_temp_length_firsttone(t1_1)
        self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)

        nb_samples =  round(1.5*(self.get_temp_start_firsttone() \
                + self.get_temp_length_firsttone()+t1_2start+t1_2 ) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6


        if t_rise==None:
            p1 = [t1_1start,  t1_1,
                    amplitude_tone1, self.get_down_converted_frequency()*1e9]
            p2 = [t1_2start,  t1_2,
                    amplitude_tone1, self.get_down_converted_frequency()*1e9]

            wave_ro_cos = self.cos(p1, time1) + self.cos(p2, time1)
        else:
            if 2*t_rise > t1_1 or 2*t_rise> t1_2:
                print 'Be Careful: rising time should be less than the length of first tone...'
            else:
                p1 = [t1_1start,  t_rise, t1_1,
                        amplitude_tone1, self.get_down_converted_frequency()*1e9,
                        duty_cycle, diff_PdB]
                p2 = [t1_2start,  t_rise, t1_2,
                        amplitude_tone1, self.get_down_converted_frequency()*1e9,
                        duty_cycle, diff_PdB]

                wave_ro_cos = self.cos_plateau(p1, time1) + self.cos_plateau(p2, time1)


        wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
        wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                self._awg_routing['board_marker'],
                np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                wave_pulse_read_out)

        self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
            self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() +1 )


        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            amplitude_tone2, self._SSB_tone2.get_IF_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time1))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 2)

        p_qb = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
            0, self._SSB_tone2.get_IF_frequency()*1e9]

        segment3_ex = self.volt2bit_2(self.cos(p_qb, time1))
        self._arbitrary_waveform_generator.send_waveform(segment3_ex,
                            self._awg_routing['secondtone_channel'], self.get_number_segments_memorized() + 3)

        for i in np.arange(2):
             # without pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 3, 0])
            # with pi
            self._seq_list1.append([1, self.get_number_segments_memorized() + 1, 0])
            self._seq_list2.append([1, self.get_number_segments_memorized() + 2, 0])


        self._seq_list1= np.array(self._seq_list1)
        self._seq_list2= np.array(self._seq_list2)

        self.set_awg_segmentation({'IQ': self.get_number_segments_memorized() + 1 + np.arange(3)} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        self._arbitrary_waveform_generator.set_channels_synchronised('ON')


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list1, self._sequence_dict['IQ1'])


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list2, self._sequence_dict['IQ2'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ2'])



        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')

        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')


    def write_several_RO(self, amplitude_vec, t1_1, t1_2, t1_1start=0.2e-9, t1_2start=0.2e-9, delta_m1_start=0, delete=False):
        '''
        Putting in the awg memory the IQ pulses sequence. The IQ pulses sequence
        can be onetone or twotone.
        Inputs:
            type (str): onetone or twotone

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
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        self._arbitrary_waveform_generator.set_marker_source('USER')

        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        amplitude_tone1 = 0.9999

        self._seq_list = []


        self.set_temp_start_firsttone(t1_2start )
        self.set_temp_length_firsttone(t1_2)
        self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)


        nb_samples =  round(1.5*(self.get_temp_start_firsttone() \
                + self.get_temp_length_firsttone() ) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6


        for i, amp in  enumerate(amplitude_vec):
            p1 = [t1_1start,  t1_1,
                    amp, self.get_down_converted_frequency()*1e9]
            p2 = [t1_2start,  t1_2,
                    amplitude_tone1, self.get_down_converted_frequency()*1e9]

            wave_ro_cos = self.cos(p1, time1) + self.cos(p2, time1)

            wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
            wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                    self._awg_routing['board_marker'],
                    np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                    wave_pulse_read_out)

            self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
                self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() +i + 1)


            self._seq_list.append([1, self.get_number_segments_memorized() + 1 +i, 0])

        self._seq_list= np.array(self._seq_list)

        self.set_awg_segmentation({'IQ': self.get_number_segments_memorized() + 1 + np.arange(len(amplitude_vec))} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        self._arbitrary_waveform_generator.set_channels_synchronised('ON')


        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, self._sequence_dict['IQ'])


        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['IQ'])

        self._arbitrary_waveform_generator.set_trigger_source('EXT') #change of 20171003
        self._arbitrary_waveform_generator.seq_jump_source('BUS')
        self._arbitrary_waveform_generator.seq_mode('STEP')
        self._arbitrary_waveform_generator.set_trigger_mode('NORM')
        self._arbitrary_waveform_generator.set_trigger_timer_mode('TIME')
        self._arbitrary_waveform_generator.set_run_mode('TRIG')
        self._arbitrary_waveform_generator.set_func_mode('SEQ')
        self._arbitrary_waveform_generator.set_trigger_timer_time(self._trigger_time)

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')

        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')

    def write_DoubleRabi_pulsessequence(self, Tr_stop, Tr_step, Tr_start=0., t_pi=0., T_meas=4e-6, t2_start=100e-9,
                    t_wait=0, delta_m1_start=0.,phi=0.,delete=False, t_rise=None):
        '''
        Putting in the awg memory the Rabi pulses sequence and preparing the others instruments.
        Inputs:

        '''
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')

        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

        self._thirdtone=1


        if delete == 'all':
            # Emptying the awg memory
            self._arbitrary_waveform_generator.delete_segments()
            self._arbitrary_waveform_generator.reset()
            self._arbitrary_waveform_generator.clear_err()
            self._arbitrary_waveform_generator.set_trace_mode('SING')
            self._arbitrary_waveform_generator.delete_segments()
            self._segmentation = {}
            self._arbitrary_waveform_generator.set_clock_freq(1e3)
            # self._arbitrary_waveform_generator.set_clock_source('EXT')
        elif delete == 'segments':
            n_seg = self.get_awg_segmentation()['rabi1']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)
            n_seg = self.get_awg_segmentation()['rabi2']
            print n_seg, type(n_seg)
            self._arbitrary_waveform_generator.delete_segment_i(n_seg)


        self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
        self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['thirdtone_channel'])
        self._awg_dict_coupling[self._awg_routing['thirdtone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['thirdtone_channel']](2)

        self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
        self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)

        self._arbitrary_waveform_generator.set_marker_source('USER')

        amplitude = 0.9999

        self.set_temp_start_thirdtone(100e-9)
        self.set_temp_length_thirdtone( t_pi)

        # self.set_temp_start_secondtone(self.get_temp_start_thirdtone()\
        #         + self.get_temp_length_thirdtone()+ t_wait )
        self.set_temp_start_secondtone( t_wait + t2_start)
        self.set_temp_length_secondtone(Tr_start )

        self.set_temp_start_firsttone( self.get_temp_start_secondtone() + self.get_temp_length_secondtone() + t_wait)
        self.set_temp_length_firsttone(T_meas)
        self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)
        # self.set_marker1_width(self.get_temp_length_firsttone())


        nb_samples1 =  round(1.2*( Tr_stop + self.get_temp_start_firsttone() + \
                np.max(self.get_temp_length_firsttone() +self.get_marker1_width()) ) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time1 = np.arange(nb_samples1)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        for ch in CHANNEL:
            self._awg_waves['rabi']['binary'][ch] = []
            self._awg_waves['rabi']['cosine'][ch] = []
            self._awg_waves['rabi']['marker_trigger'][ch] = []

        self._seq_list = []

        N = len(np.arange(Tr_start, Tr_stop+Tr_step, Tr_step))




        # here we will create the pi pulse of thirdtone:
        p_pi = [self.get_temp_start_thirdtone(), self.get_temp_length_thirdtone(),
                amplitude, self._SSB_tone3.get_IF_frequency()*1e9]
        wave_pi = self.volt2bit_2(self.cos(p_pi, time1))


        nb_samples2 =  round(1.1*( self.get_temp_start_firsttone() + self.get_temp_length_firsttone()  ) *\
                self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time2 = np.arange(nb_samples2)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        for i in np.arange(N):
            if i>0:
                # self.set_temp_start_secondtone(self.get_temp_start_secondtone() - Tr_step)
                self.set_temp_length_secondtone(self.get_temp_length_secondtone() + Tr_step)
                self.set_temp_start_firsttone( self.get_temp_start_secondtone() + self.get_temp_length_secondtone() + t_wait)
                self.set_marker1_start(self.get_temp_start_firsttone()-delta_m1_start)


            p2 = [self.get_temp_start_secondtone(), self.get_temp_length_secondtone(),
                amplitude, self._SSB_tone2.get_IF_frequency()*1e9]

            if t_rise==None or t_rise ==0.:
                p1 = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(),
                        amplitude, self.get_down_converted_frequency()*1e9, phi]
                wave_ro_cos = self.cos_phi(p1, time1)
            else:
                if t_rise > self.get_temp_length_firsttone()/2.:
                    print 'Be Careful: rising times should be less than the length of first tone...'
                else:
                    p1 = [self.get_temp_start_firsttone(), t_rise, self.get_temp_length_firsttone(),
                            amplitude, self.get_down_converted_frequency()*1e9]
                    wave_ro_cos = self.cos_rise(p1, time1)

            wave_pulse_read_out  = self.volt2bit_2(wave_ro_cos)
            wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                        self._awg_routing['board_marker'],
                        np.int(self.get_marker1_start()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                        np.int(self.get_marker1_width()*self._arbitrary_waveform_generator.get_clock_freq()*1e6),
                        wave_pulse_read_out)


            wave_ro_marker = self.pulse([self.get_marker1_start(), self.get_marker1_width(), 1], time1)

            qb_ex_cos = self.cos(p2, time1) #change 20170505
            qubit_excitation = self.volt2bit_2(qb_ex_cos)
            self._arbitrary_waveform_generator.send_waveform(qubit_excitation,
                self._awg_routing['secondtone_channel'],  self.get_number_segments_memorized() + i + 1)

            self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out,
                self._awg_routing['firsttone_channel'],  self.get_number_segments_memorized() + i + 1)

            self._arbitrary_waveform_generator.send_waveform(wave_pi,
                self._awg_routing['thirdtone_channel'],  self.get_number_segments_memorized() + i + 1)

            self._awg_waves['rabi']['binary'][self._awg_routing['firsttone_channel']].append(wave_pulse_read_out)
            self._awg_waves['rabi']['binary'][self._awg_routing['secondtone_channel']].append(qubit_excitation)
            self._awg_waves['rabi']['cosine'][self._awg_routing['firsttone_channel']].append(wave_ro_cos)
            self._awg_waves['rabi']['cosine'][self._awg_routing['secondtone_channel']].append(qb_ex_cos)
            self._awg_waves['rabi']['marker_trigger'][self._awg_routing['firsttone_channel']].append(wave_ro_marker)
            self._seq_list.append([1, self.get_number_segments_memorized() + i + 1, 0])


        self._seq_list = np.array(self._seq_list)

        self.set_awg_segmentation({'rabi': self.get_number_segments_memorized() + 1 + np.arange(N)} )
        # self.set_awg_segmentation({'rabi2': self.get_number_segments_memorized() + 1 + np.arange(N)} )

        self._awg_dict_output[self._awg_routing['firsttone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')
        self._awg_dict_output[self._awg_routing['thirdtone_channel']]('OFF')

        self._arbitrary_waveform_generator.set_channels_synchronised('ON')

        self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, self._sequence_dict['rabi3'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['rabi3'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['thirdtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, self._sequence_dict['rabi3'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['rabi3'])
        self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
        self._arbitrary_waveform_generator.send_seq(self._seq_list, self._sequence_dict['rabi3'])
        self._arbitrary_waveform_generator.sequence_select(self._sequence_dict['rabi3'])

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
        self._awg_dict_output[self._awg_routing['thirdtone_channel']]('ON')


        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')

    def prep_onetone_pump_interference(self, freq_vec, average, power, acq_time=500,
            pulse_time=500, delta_t=0.):
        '''
        Preparing the instruments for a onetone pulses sequence. This function do not
        write in the awg memory.
        Inputs:
            frec_vec: frequency vector in GHz of the onetone sweep
            average (int): number of averaging
            power: power at the awg output
            pulse_time in ns
            delta_t in ns
        '''

        # Setting the mw1 on the sweeping mode
        if self._presence_mwsrc3:
            self._microwave_generator3.set_freqsweep('on')
            self._microwave_generator3.set_sweepmode('SINGLE')
            # self._microwave_generator3.set_spacingfreq('linear')
        else:
            raise ValueError('Could not prep because no microwave generator 3')


        # Setting the sweep parameters to mw1
        print freq_vec[0], freq_vec[-1], freq_vec[1]-freq_vec[0]
        self._microwave_generator3.set_startfreq(freq_vec[0])
        self._microwave_generator3.set_stopfreq(freq_vec[-1])
        self._microwave_generator3.set_stepfreq(freq_vec[1]-freq_vec[0])

        # Setting the averaging:
        self.set_total_averaging(average)

        # Selecting the AWG sequence
        self.AWG_select_sequence(sequence='onetone', nb_channel=1)

        # Setting AWG power/amplitude
        self.set_power_first_tone(power)
        amplitude = 10**((power)/10.)
        print amplitude
        self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2*amplitude)

        self._board.set_acquisition_time(acq_time)
        # Setting the measurement process
        if self.do_get_measurement_type() == 'homodyne':
            processus = dt.HomodyneRealImagPerSequence(pulse_time*1e-9, self._board.get_samplerate()*1e6, delta_t*1e-9)
        elif self.do_get_measurement_type() == 'heterodyne':
            if self._acquisition:
                processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                              self.get_down_converted_frequency()*1e9)
            else:
                processus = dt.RealImagPerSequence(self._board.get_acquisition_time()*1e-9, self._board.get_samplerate()*1e6,
                              self.get_down_converted_frequency()*1e9, t_ro=self.get_temp_length_firsttone())

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

    def pulse_rise(self, p, x, type='DC'):
        start, t_rise, width, amplitude = p

        # from second to sample
        time_step = x[1] - x[0]
        start = int(round(start/time_step))
        rise = int(round(t_rise/time_step))
        width = int(round(width/time_step))

        after  = len(x) - width - start

        pulse = np.concatenate((np.zeros(start),
                                amplitude/rise*(1+np.arange(rise)),
                                amplitude*np.ones(width),
                                np.zeros(after)))

        return pulse

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

    def cos_rise(self, p, x):
        '''
        Return an array of a cosine pulse
        '''
        start, t_rise, duration, amplitude, frequency = p

        # from second to sample
        time_step = x[1] - x[0]
        start = int(round(start/time_step))
        rise = int(round(t_rise/time_step))
        width = int(round(duration/time_step))

        after  = len(x) - width - start

         #
        pulse = np.concatenate((np.zeros(start),
                                amplitude*np.cos(2.*np.pi*frequency*x[start:start+width]),
                                np.zeros(after)))
        pulse2 = np.concatenate((np.zeros(start), amplitude/rise*(1.+np.arange(rise)),
                                amplitude*np.ones(width-2*rise),
                                amplitude/rise*(np.arange(rise-1,-1,-1.)),
                                np.zeros(after)))


        return pulse*pulse2

    def cos_plateau(self, p, x):
        '''
        Return an array of a cosine pulse
        '''
        start, t_rise, duration, amplitude, frequency, dutycycle, diff_PdB = p

        ratio = 10**(diff_PdB/10.)
        # from second to sample
        time_step = x[1] - x[0]
        start = int(round(start/time_step))
        rise = int(round(t_rise/time_step))
        width = int(round(duration/time_step))
        width_plateau = int( round( dutycycle*(duration -2*t_rise)/time_step ) )
        width_2 = width - 3*rise - width_plateau

        after  = len(x) - width - start

        pulse = np.concatenate((np.zeros(start),
                                amplitude*np.cos(2.*np.pi*frequency*x[start:start+width]),
                                np.zeros(after)))

        pulse2 = np.concatenate((np.zeros(start), amplitude/rise*(1.+np.arange(rise)),
                                amplitude*np.ones(width_plateau),
                                ratio*amplitude + (1.-ratio)*amplitude/rise*(np.arange(rise-1,-1,-1.)),
                                ratio*amplitude*np.ones(width_2),
                                ratio*amplitude/rise*(np.arange(rise-1,-1,-1.)),
                                np.zeros(after)))


        return pulse*pulse2

    def exp_envelop(self, p, x):
        '''
        Return an array of an exponential envelope
        '''
        center, tau = p

        pulse = np.exp(-np.abs(x-center)/tau)

        return pulse

    def cos_phi(self, p, x):
        '''
        Return an array of a cosine pulse
        '''
        start, duration, amplitude, frequency, phi = p

        # from second to sample
        time_step = x[1] - x[0]
        start = int(round(start/time_step))
        width = int(round(duration/time_step))

        after  = len(x) - width - start

        pulse = np.concatenate((np.zeros(start),
                                amplitude*np.cos(2.*np.pi*frequency*x[start:-after] + phi),
                                np.zeros(after)))

        return pulse

    def clock_AWG(self):
        '''
        Setting the clock system of the AWG
        '''
        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_source('INT')
        self._arbitrary_waveform_generator.set_clock_freq(1e3)

    def usual_setting_AWG(self, nb_channel=1):
        '''
        This method is used to set the usual settings of the AWG
        '''
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')
        self.status_AWG('OFF', nb_channel)
        if nb_channel == 1:
            self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
            self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
            self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
        elif nb_channel == 2:
            self._arbitrary_waveform_generator.init_channel(self._awg_routing['firsttone_channel'])
            self._awg_dict_coupling[self._awg_routing['firsttone_channel']]('DC')
            self._awg_dict_amplitude[self._awg_routing['firsttone_channel']](2)
            self._arbitrary_waveform_generator.init_channel(self._awg_routing['secondtone_channel'])
            self._awg_dict_coupling[self._awg_routing['secondtone_channel']]('DC')
            self._awg_dict_amplitude[self._awg_routing['secondtone_channel']](2)

        self.clock_AWG()
        self._arbitrary_waveform_generator.set_channels_synchronised('ON')
        self._arbitrary_waveform_generator.set_marker_source('USER')
        self._arbitrary_waveform_generator.set_m2_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)

        self._arbitrary_waveform_generator.set_trigger_source('EVEN')
        self._arbitrary_waveform_generator.seq_mode('STEP')
        self._arbitrary_waveform_generator.seq_jump_source('BUS')
        self._arbitrary_waveform_generator.set_trigger_mode('NORM')
        self._arbitrary_waveform_generator.set_trigger_timer_mode('TIME')
        self._arbitrary_waveform_generator.set_run_mode('TRIG')
        self._arbitrary_waveform_generator.set_func_mode('SEQ')
        self._arbitrary_waveform_generator.set_trigger_timer_time(self._trigger_time)
#################################################################################

    def status_AWG(self, status, nb_channel=1):
        self._awg_dict_output[self._awg_routing['firsttone_channel']](status)
        if nb_channel == 2:
            self._awg_dict_output[self._awg_routing['secondtone_channel']](status)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2(status)
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2(status)

    def AWG_select_sequence(self, sequence='onetone', nb_channel=1 ):

        if nb_channel == 1:
            self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
            self._arbitrary_waveform_generator.sequence_select(self._sequence_dict[sequence])
            self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
            self._awg_dict_output[self._awg_routing['secondtone_channel']]('OFF')
        elif nb_channel == 2:
            self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
            self._arbitrary_waveform_generator.sequence_select(self._sequence_dict[sequence+'1'])
            self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
            self._arbitrary_waveform_generator.sequence_select(self._sequence_dict[sequence+'2'])

            self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
            self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')
        elif nb_channel ==3:
            self._arbitrary_waveform_generator.channel_select(self._awg_routing['firsttone_channel'])
            self._arbitrary_waveform_generator.sequence_select(self._sequence_dict[sequence])
            self._arbitrary_waveform_generator.channel_select(self._awg_routing['secondtone_channel'])
            self._arbitrary_waveform_generator.sequence_select(self._sequence_dict[sequence])
            self._arbitrary_waveform_generator.channel_select(self._awg_routing['thirdtone_channel'])
            self._arbitrary_waveform_generator.sequence_select(self._sequence_dict[sequence])

            self._awg_dict_output[self._awg_routing['firsttone_channel']]('ON')
            self._awg_dict_output[self._awg_routing['secondtone_channel']]('ON')
            self._awg_dict_output[self._awg_routing['thirdtone_channel']]('ON')


        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')
################################################################################
    def reset_rabi_ramsey_measurement(self):
        '''
        Function to reset the measurement of a Rabi experiment.
        '''
        print 'here'
        self.measurement_close(False)
        print self.measurement_close(True)
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')
        # we closed measurement


        # we reprepare a rabi measurement:
        if not self._board_flag:
            print 'reseting'
            self.prep_rabi(self.get_src1_cw_frequency(),
                    self.get_src2_cw_frequency(),
                    self._board.get_averaging(),
                    self._board.get_nb_sequence(),
                    self.get_power_first_tone(),
                    self.get_power_second_tone(),
                    self._acq_time,
                    self._pulse_time,
                    self._delta_t,
                    power_tone3 = self.get_power_third_tone())
            TIME.sleep(2)

            self._arbitrary_waveform_generator.set_trigger_source('TIM')

    def measurement_close(self, transfert_info=False):
        try:
            self._board.measurement_close(transfert_info)
        finally:

            self._board_flag = 0

    def do_get_acquisition_completed(self):
        return self._board.get_completed_acquisition()

    def measurement(self):
        result = self._board.measurement()
        return result


    # def do_get_acquisition_completed(self):
    #     return self._board.get_completed_acquisition()
