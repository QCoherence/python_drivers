# Work in PROGRESS
# made by Remy Dassonneville in 2016

from instrument import Instrument
import instruments
import numpy as np
import types
import logging

# Should we put the measurement in the driver???
# from lib.math import fit # to be able to do some fit during the measurements
# import ATS9360.DataTreatment as dt
# import qt

# from lib.math.useful_functions import volt2bit, volt2bit_2, cos, pulse
# now coded in this driver
import matplotlib.pyplot as plt

CHANNEL=(1,2,3,4)

class virtual_spectro_pulse_onetone(Instrument):
    '''
    TO DO: complete it!!!
    This is the driver for the virtual instrument which can create a spectroscopic sequence pulses and measure it.

    Usage:
    Initialize with
    <name> = qt.instruments.create('name', 'virtual_spectro_pulse_onetone',
    AWG='awg_name', mwsrc='name_microwave_generator', board='board_name',
    mwsrc2= 'name_microwave_generator2--if present--', current_src='name_current_source--if present--' )
    '''

    def __init__(self, name, awg, mwsrc1, board, mwsrc2 = 'None', current_src = 'None'):
        '''
            Initialize the virtual instrument

                Input:
                    - name: Name of the virtual instruments
                    - awg: Name given to an arbitrary waveform generator
                    - mwsrc1: Name given to the first microwave_generator
                    - board: Name given to the acquisition card
                    - mwsrc2: Name given to the second microwave_generator
                    - current_src: Name given to the current source
                Output:
                    None
        '''
        Instrument.__init__(self, name, tags=['virtual'])
        #Import instruments
        self._instruments = instruments.get_instruments()

        self._arbitrary_waveform_generator = self._instruments.get(awg)

        self._microwave_generator1 = self._instruments.get(mwsrc1)
        self._microwave_generator1.set_power(5)
        self._microwave_generator1.set_status('ON')

        self._board = self._instruments.get(board)

        # if we import the second microwave generator or not
        if mwsrc2 != 'None':
            self._presence_mwsrc2 = 1
            self._microwave_generator2 = self._instruments.get(mwsrc2)
            self._microwave_generator2.set_power(5)
            self._microwave_generator2.set_status('ON')
        else:
            self._presence_mwsrc2 = 0

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
                            channel_prefix='scr%d_')

        # Attention: may have to change something after changing frequency sweep
        # parameters
        self.add_parameter('frequency_start',
                            flags=Instrument.FLAG_GETSET,
                            units='GHz',
                            minval = 1e-4,
                            maxval= 40,
                            type=types.FloatType,
                            channels=(1, 2),
                            channel_prefix='scr%d_')

        self.add_parameter('frequency_stop',
                            flags=Instrument.FLAG_GETSET,
                            units='GHz',
                            minval = 1e-4,
                            maxval= 40,
                            type=types.FloatType,
                            channels=(1, 2),
                            channel_prefix='scr%d_')

        self.add_parameter('frequency_step',
                            flags=Instrument.FLAG_GETSET,
                            units='GHz',
                            minval = 1e-4,
                            maxval= 40,
                            type=types.FloatType,
                            channels=(1, 2),
                            channel_prefix='scr%d_')

        self.add_parameter('points_freq_sweep',
                            flags=Instrument.FLAG_GETSET,
                            minval=1,
                            type=types.IntType,
                            channels=(1, 2),
                            channel_prefix='scr%d_')

        self.add_parameter('averaging',
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
        self._awg_routing['mw1_power'] = 5.
        self._awg_routing['mw2_power'] = 5.
        self._awg_routing['mw1_ssb_bandtype'] = -1
        self._awg_routing['mw2_ssb_bandtype'] = -1

        self.add_parameter('temp_length_firsttone',
                            flags=Instrument.FLAG_GETSET,
                            minval = 0.,
                            maxval= 100e-6,
                            units='s',
                            type=types.FloatType)
        self._firsttone_temp_length = 1e-6

        self.add_parameter('temp_length_secondtone',
                            flags=Instrument.FLAG_GETSET,
                            minval = 0.,
                            maxval= 100e-6,
                            units='s',
                            type=types.FloatType)
        self._secondtone_temp_length = 0.

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
        self._secondtone_temp_start = 0.
        ########################################################################
        # GET only
        self.add_parameter('SSB_conversion_loss',
                            flags=Instrument.FLAG_GET,
                            type=FloatType)
        self._SSB_conver_loss = 6.
        # it is the typical  conversion loss of a SSB

        self.add_parameter('electrical_phase_delay',
                            flags=Instrument.FLAG_GET,
                            type=FloatType)
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

        self.add_parameter('marker1_width',
                            flags=Instrument.FLAG_GET,
                            units='s',
                            type=types.FloatType)
        self._marker1_width = 80e-6

        self.add_parameter('marker2_width',
                            flags=Instrument.FLAG_GET,
                            units='s',
                            type=types.FloatType)
        self._marker2_width = 80e-6

        self.add_parameter('marker1_start',
                            flags=Instrument.FLAG_GET,
                            units='s',
                            type=types.FloatType)
        self._marker1_start = 100e-9

        self.add_parameter('marker2_start',
                            flags=Instrument.FLAG_GET,
                            units='s',
                            type=types.FloatType)
        self._marker2_start = 100e-9

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
        acq_time = self._firsttone_temp_length - 0.2e-6
        acq_time = np.int(acq_time/128)*128
        self._board.set_acquisition_time(acq_time)

        # initialize awg
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)
        self._trigger_time= 100 # set_trigger_timer_time is in us
        self._arbitrary_waveform_generator.set_trigger_timer_time(self._trigger_time)
        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')
        self._arbitrary_waveform_generator.set_channels_synchronised('ON')

        for i in CHANNEL:
            self._arbitrary_waveform_generator.set_coupling('DC', channel=i)
            self._arbitrary_waveform_generator.set_amplitude(2, channel=i)

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
        while (self._M+1)*self._arbitrary_waveform_generator.get_trigger_time() < self.get_mw_security_time():
            self._M +=1
        ########################################################################
        #                       Functions
        ########################################################################
        self.add_function('write_onetone_pulsessequence')
        self.add_function('measure_onetone')

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
            return self._microwave_generator1.get_frequency()/1e9 + self._awg_routing['mw1_ssb_bandtype']*self.get_down_converted_frequency()
        elif channel==2:
            return self._microwave_generator2.get_frequency()/1e9 + self._awg_routing['mw2_ssb_bandtype']*self.get_down_converted_frequency()
        else:
            print 'Error: channel must be in (1, 2)'

    def do_set_cw_frequency(self, cwf, channel=1):
        '''
        Sets the continuous wave frequency in GHz of the microwave generator channel
        '''

        if channel == 1:
            cwf -= self._awg_routing['mw1_ssb_bandtype']
            return self._microwave_generator1.set_frequency(cwf*1e9)*self.get_down_converted_frequency()
        elif channel == 2:
            cwf -= self._awg_routing['mw2_ssb_bandtype']
            return self._microwave_generator2.set_frequency(cwf*1e9)*self.get_down_converted_frequency()
        else:
            print 'Error: channel must be in (1, 2)'

    def do_get_frequency_start(self, channel=1):
        '''
        Get the starting frequency of the frequency sweep in GHz of the microwave generator channel
        '''
        if channel == 1:
            return self._microwave_generator1.get_startfreq() + self._awg_routing['mw1_ssb_bandtype']*self.get_down_converted_frequency()
        elif channel == 2:
            return self._microwave_generator2.get_startfreq() + self._awg_routing['mw2_ssb_bandtype']*self.get_down_converted_frequency()
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
            freq_start -= self._awg_routing['mw1_ssb_bandtype']*self.get_down_converted_frequency()
            self._microwave_generator1.set_startfreq(freq_start)

            number_sequence = self._pulsenumber_averaging*self._microwave_generator1.get_pointsfreq()
            self._board.set_nb_sequence(number_sequence)

        elif channel == 2:
            freq_start -= self._awg_routing['mw2_ssb_bandtype']*self.get_down_converted_frequency()
            self._microwave_generator2.set_startfreq(freq_start)

            number_sequence = self._pulsenumber_averaging*self._microwave_generator2.get_pointsfreq()
            self._board.set_nb_sequence(number_sequence)
        else:
            print 'Error: channel should be in (1, 2)'

    def do_get_frequency_stop(self, channel =1):
        '''
        Get the last frequency of the frequency sweep in GHz of the microwave generator channel
        '''
        if channel == 1:
            return self._microwave_generator1.get_stopfreq() + self._awg_routing['mw1_ssb_bandtype']*self.get_down_converted_frequency()
        elif channel == 2:
            return self._microwave_generator2.get_stopfreq() + self._awg_routing['mw2_ssb_bandtype']*self.get_down_converted_frequency()
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
            freq_stop -= self._awg_routing['mw1_ssb_bandtype']*self.get_down_converted_frequency()
            self._microwave_generator1.set_stopfreq(freq_stop)

            number_sequence = self._pulsenumber_averaging*self._microwave_generator1.get_pointsfreq()
            self._board.set_nb_sequence(number_sequence)
        elif channel == 2:
            freq_stop -= self._awg_routing['mw2_ssb_bandtype']*self.get_down_converted_frequency()
            self._microwave_generator2.set_stopfreq(freq_stop)

            number_sequence = self._pulsenumber_averaging*self._microwave_generator2.get_pointsfreq()
            self._board.set_nb_sequence(number_sequence)
        else:
            print 'Error: channel should be in (1, 2)'

    def do_get_frequency_step(self, channel=1):
        '''
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

            number_sequence = self._pulsenumber_averaging*self._microwave_generator1.get_pointsfreq()
            self._board.set_nb_sequence(number_sequence)
        elif channel == 2:
            self._microwave_generator2.set_stepfreq(freq_step)

            number_sequence = self._pulsenumber_averaging*self._microwave_generator2.get_pointsfreq()
            self._board.set_nb_sequence(number_sequence)
        else:
            print 'Error: channel must be in (1,2)'

    def do_get_points_freq_sweep(self, channel=1):
        '''
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

            number_sequence = self._pulsenumber_averaging*self._microwave_generator1.get_pointsfreq()
            self._board.set_nb_sequence(number_sequence)
        elif channel == 2:
            self._microwave_generator2.set_pointsfreq(points)

            number_sequence = self._pulsenumber_averaging*self._microwave_generator1.get_pointsfreq()
            self._board.set_nb_sequence(number_sequence)
        else:
            print 'Error: channel must be in (1,2)'

    def do_get_averaging(self):
        '''
        Get the total averaging. It is the board averaging multiply by the number of pulses averaging.
        '''
        return self._board.get_averaging()*self._pulsenumber_averaging

    def do_set_averaging(self, average):
        '''
        Set the total averaging. It is a multiple of the number of pulses averaging.
        '''
        if average % self._pulsenumber_averaging == 0:
            self._board.set_averaging(average/self._pulsenumber_averaging)
        else:
            print 'Error: the total averaging should be a multiple of the number of pulses averaging'

    def do_get_routing_awg(self):
        '''
        Gets the awg routing map.
        '''
        return self._awg_routing

    def do_set_routing_awg(self, firsttone_channel, secondtone_channel,
        board_marker, mw_marker, mw1_power, mw2_power, mw1_ssb_bandtype, mw2_ssb_bandtype):
        '''
        Sets the awg routing map.
        Inputs:
            firsttone_channel (int): number of the first tone awg channel
            secondtone_channel (int): number of the first tone awg channel
            board_marker (int): number of the board marker
            mw_marker (int): number of the microwave marker
            mw1_power (dBm): the power of the microwave generator 1
            mw2_power (dBm): the power of the microwave generator 2
            mw1_ssb_bandtype (-1, +1): the bandtype of the ssb associated to the microwave generator 1
            mw2_ssb_bandtype (-1, +1): the bandtype of the ssb associated to the microwave generator 2
        note: for ssb_bandtype, -1 means lower side band, +1 means upper side band.
        '''
        self._awg_routing['firsttone_channel'] = firsttone_channel
        self._awg_routing['secondtone_channel'] = secondtone_channel
        self._awg_routing['board_marker'] = board_marker
        self._awg_routing['mw_marker'] = mw_marker
        self._awg_routing['mw1_power'] = mw1_power
        self._awg_routing['mw2_power'] = mw2_power
        self._awg_routing['mw1_ssb_bandtype'] = mw1_ssb_bandtype
        self._awg_routing['mw2_ssb_bandtype'] = mw2_ssb_bandtype

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
        acq_time = np.int(acq_time/128)*128
        self._board.set_acquisition_time(acq_time)

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

    def do_set_temp_length_secondtone(self, t0):
        '''
        Sets the temporal start of the second tone pulses in s.
        '''
        self._secondtone_temp_start = t0

    ############################################################################
    # get_only
    def do_get_SSB_conversion_loss(self):
        return self._SSB_conver_loss

    def do_get_down_converted_frequency(self):
        '''
        Get the down_converted_frequency in GHz
        '''
        return self._down_converted_frequency

    def do_get_electrical_phase_delay(self):
        return self._elec_delay

    def do_get_marker1_width(self):
        return self._marker1_width

    def do_get_marker2_width(self):
        return self._marker2_width

    def do_get_marker1_start(self):
        return self._marker1_start

    def do_get_marker2_start(self):
        return self._marker2_start

    def do_get_mw_security_time(self):
        return self._mw_security_time

    ############################################################################
    #  Functions
    ############################################################################
    def write_onetone_pulsessequence(self, freq_vec, power, average, readout_channel=1, sequence_index=1):
        '''
        Putting in the awg memory the onetone pulses sequence.
        Inputs:
            frec_vec: frequency vector in GHz of the onetone sweep
            power: power at the SSB output in dBm
            average (int): number of averaging
            readout_channel: awg channel used. Value in (1, 2, 3, 4)
            sequence_index: value in 1 to 1000
        '''
        # self._pulsenumber_averaging
        self.set_frequency_start(freq_vec[0], channel=1)
        self.set_frequency_stop(freq_vec[-1], channel=1)
        self.set_points_freq_sweep(len(freq_vec), channel=1)

        self._freq_vec = freq_vec
        self.set_averaging(average)

        power += self.get_SSB_conversion_loss()
        amplitude = np.sqrt(2.*50.*10**((power-30.)/10.))

        nb_samples_smb =  round((self.get_marker2_start()+self.get_marker2_width())*self._arbitrary_waveform_generator.get_clock_freq()*1e6/16., 0)*16
        time_smb = np.arange(nb_samples_smb)/self._arbitrary_waveform_generator.get_clock_freq()*1e-6

        for i in np.arange(self._M + self._pulsenumber_averaging + 1):
            if i == self._M + self._pulsenumber_averaging:
                # changing smb frequency part of the sequence
                p = [0, 0, 0, 0]
                wave_pulse_read_out  = self.volt2bit_2(self.cos(p, time_smb))
                wave_pulse_read_out = self._arbitrary_waveform_generator.\
                        add_markers_mask(self._awg_routing['mw_marker'],
                        self.get_marker2_start(), self.get_marker2_width(),
                        wave_pulse_read_out)

                self._seq_list.append([1,i+1,0])
                self._W.append(wave_pulse_read_out)

                self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out, readout_channel, i+1)
            elif i < self._M:
                # waiting part of the sequence
                p = [0, 0, 0, 0]
                wave_pulse_read_out  = self.volt2bit_2(np.zeros(16*50)) #

                self._seq_list.append([1,i+1,0])
                self._W.append(wave_pulse_read_out)

                self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out, readout_channel, i+1)
            else:
                # reading-out part of the sequence
                p = [self.get_temp_start_firsttone(), self.get_temp_length_firsttone(), amplitude, self.get_down_converted_frequency()]

                wave_pulse_read_out  = self.volt2bit_2(self.cos(p, time))
                wave_pulse_read_out = self._arbitrary_waveform_generator.add_markers_mask(\
                                self.get_board_marker(), self.get_marker1_start(),
                                self.get_marker1_width(), wave_pulse_read_out)

                self._seq_list.append([1,i+1,0])
                self._W.append(wave_pulse_read_out)
                self._arbitrary_waveform_generator.send_waveform(wave_pulse_read_out, readout_channel, i+1)

        self._seq_list = np.array(self._seq_list)
        self._arbitrary_waveform_generator.set_ref_source('EXT')
        self._arbitrary_waveform_generator.set_ref_freq(10)
        self._arbitrary_waveform_generator.set_clock_freq(1e3)
        self._arbitrary_waveform_generator.set_channels_synchronised('ON')
        self._arbitrary_waveform_generator.channel_select(readout_channel)
        self._arbitrary_waveform_generator.send_seq(seq_list, sequence_index)
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        # self._arbitrary_waveform_generator.set_m1_marker_status_1_2('OFF')
        # self._arbitrary_waveform_generator.set_m2_marker_status_1_2('OFF')
        self._arbitrary_waveform_generator.set_m2_marker_high_1_2(1.)
        self._arbitrary_waveform_generator.set_m1_marker_high_1_2(1.)
        # smb_cavity.set_gui_update('OFF')
        self._arbitrary_waveform_generator.seq_jump_source('BUS')
        self._arbitrary_waveform_generator.seq_mode('STEP')
        self._arbitrary_waveform_generator.set_trigger_mode('NORM')
        self._arbitrary_waveform_generator.set_trigger_timer_mode('TIME')
        self._arbitrary_waveform_generator.set_run_mode('TRIG')
        self._arbitrary_waveform_generator.set_func_mode('SEQ')
        self._arbitrary_waveform_generator.set_trigger_timer_time(self._trigger_time) #in us
        self._arbitrary_waveform_generator.set_output('ON', channel=readout_channel)
        self._arbitrary_waveform_generator.set_m1_marker_status_1_2('ON')
        self._arbitrary_waveform_generator.set_m2_marker_status_1_2('ON')

    def measure_onetone(self, p0=[0,0,0,0], fitting=True):
        '''
        Do the onetone measurement. Be sure to have run the write_onetone_pulsessequence function first!
        Inputs:
            p0 = [Qi, Qext, f0, background]

        '''
        self._arbitrary_waveform_generator.set_trigger_source('EVEN')
        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator1.set_freqsweep('ON')
        self._microwave_generator1.restartsweep()
        qt.mstart()

        data_measurement = qt.Data(name='Onetone_spectroscopy')
        data_measurement.add_coordinate('Read-out frequency [GHz]', units = 'GHz')
        data_measurement.add_value('S21 ', units = 'Volt')
        data_measurement.add_value('Phase ', units = 'rad')
        data_measurement.add_value('S21dB ', units = 'dB')
        data_measurement.create_file()

        plot2d_1 = qt.Plot2D(data_measurement,
                          name      = 'S21 ',
                          coorddim  = 0,
                          valdim    = 1)

        plot2d_2 = qt.Plot2D(data_measurement,
                            name      = 'Phase ',
                            coorddim  = 0,
                            valdim    = 2)

        plot2d_3 = qt.Plot2D(data_measurement,
                          name      = 'S21dB ',
                          coorddim  = 0,
                          valdim    = 3)

        board_flag = None
        try:
            amp_phas = dt.RealImagPerSequence(self._get_acquisition_time()*1e-9, self._board_samplerate*1e6,
                              self._get_down_converted_frequency()*1e9)
            self._board.measurement_initialization(processor=amp_phas)
            qt.msleep(1)
            self._microwave_generator1.restartsweep()
            qt.msleep(1)

            board_flag = True
            self._arbitrary_waveform_generator.set_trigger_source('TIM')
            while self._board.get_completed_acquisition() != 100.:


                result = self._board.measurement()
                (real_a, imag_a), (real_b, imag_b) = result

                real_a = np.mean(np.reshape(real_a, (len(self._freq_vec),N) ), axis = 1)
                imag_a = np.mean(np.reshape(imag_a, (len(self._freq_vec),N) ), axis = 1)
                amplitude = np.sqrt(real_a**2+imag_a**2)
                complexe = (real_a + 1j*imag_a )*np.exp(1j*self._freq_vec*self.get_electrical_phase_delay()*2.*np.pi)
                phase=np.unwrap(np.arctan(np.imag(complexe)/np.real(complexe)))
                qt.msleep(0.1)
                s21dB = 20*np.log10(amplitude/cos_amplitude_read_out)
                plot2d_1.replace_inline_data(x, amplitude)
                plot2d_2.replace_inline_data(x, phase)
                plot2d_3.replace_inline_data(x, s21dB)

            self._arbitrary_waveform_generator.set_trigger_source('EVEN')
            self._board.measurement_close(transfert_info=False)
            board_flag = False


        finally:
            if board_flag:
                self._board.measurement_close(transfert_info=False)
            data_measurement.add_data_point(self._freq_vec, amplitude, phase, s21dB)
            data_measurement.close_file()

            print self._board.measurement_close(transfert_info=True)
            self._microwave_generator1.set_freqsweep('OFF')
            self._microwave_generator1.set_gui_update('ON')
            self._arbitrary_waveform_generator.set_trigger_source('EVEN')

        if fitting:
            data_fit= qt.Data(name='Onetone_spectroscopy_fit')
            data_fit.add_value('parameters ', units = 'none, none, GHz, Volt')
            data_fit.add_value('errors ', units = 'none, none, GHz, Volt')
            data_fit.create_file()

            s = fit.S21dB_pic_amplitude()
            s.set_data(self._freq_vec, amplitude)

            # fitting ##################################################################
            p = s.fit(p0)
            values_from_fit = s.func(p)
            print 'params:', s.get_fit_params()
            print 'errors:', s.get_fit_errors()

            data_fit.add_data_point(s.get_fit_params(),s.get_fit_errors())
            plot2d_1.add(self._freq_vec, values_from_fit)
            data_fit.close_file()

        plot2d_1.save_png()
        plot2d_2.save_png()
        plot2d_3.save_png()
        qt.mend()

    ############################################################################
    # useful Functions
    ############################################################################
    def volt2bit(volt):
        """
            Return the bit code corresponding to the entered voltage value in uint16
        """
        full = 4. # in volt
        resolution = 2**14. - 1.

        return  np.array(np.round((volt + full/2.)*resolution/full, 0),
                         dtype ='uint16')

    def volt2bit_2(volt):
        """
            Return the bit code corresponding to the entered voltage value in uint16
        """
        full = 2. # in volt
        resolution = 2**14. - 1.

        return  np.array(np.round((volt + full/2.)*resolution/full, 0),
                         dtype ='uint16')

    def pulse(p, x, type='DC'):
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

    def cos(p, x):
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
