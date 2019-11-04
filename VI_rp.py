# -*- coding: utf-8 -*-
# redpitaya.py is a driver for the Time domain measurement using Redpitaya
# written by Sébastien Léger, 2019
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

from instrument import Instrument
import instruments
import qt
import logging
import types
import numpy as np
import time


class VI_rp(Instrument):
    

    def __init__(self, name, mwsrc_cavity, ssb_cavity, redpitaya, mwsrc_qubit='None', ssb_qubit='None'):

        # -------------------------------------------------------------------------------------------------------------#
        # -----------------------------------    Importation of the device    -----------------------------------------#
        # -------------------------------------------------------------------------------------------------------------#
        
        Instrument.__init__(self, name, tags=['virtual'])
        self._instruments = instruments.get_instruments()
        self._SSB_tone1 = self._instruments.get(ssb_cavity)
        self._microwave_generator1 = self._instruments.get(mwsrc_cavity)
        # self._microwave_generator1.set_status('ON')
        # self._microwave_generator1.set_power(-30)
        
        self._redpitaya = self._instruments.get(redpitaya)

        # if we import the second microwave generator or not
        if mwsrc_qubit != 'None':
            self._microwave_generator2 = self._instruments.get(mwsrc_qubit)

        # if we import the second ssb or not
        if ssb_qubit != 'None':
            self._SSB_tone2 = self._instruments.get(ssb_qubit)


        # # -------------------------------------------------------------------------------------------------------------#
        # # ----------------------------------    Creation of the parameters    -----------------------------------------#
        # # -------------------------------------------------------------------------------------------------------------#

        self.add_parameter('cw_frequency',
                           flags=Instrument.FLAG_GETSET,
                           units='GHz',
                           minval=1e-4,
                           maxval=40,
                           type=types.FloatType,
                           channels=(1, 2),
                           channel_prefix='src%d_')
        self.add_parameter('ro_pulse_duration',
                           flags=Instrument.FLAG_GETSET,
                           units='s',
                           minval=8e-9,
                           maxval=64e-6,
                           type=types.FloatType)
        self.add_parameter('ro_pulse_amplitude',
                           flags=Instrument.FLAG_GETSET,
                           units='Volt',
                           minval=0,
                           maxval=1,
                           type=types.FloatType)
        self.add_parameter('ro_pulse_frequency',
                           flags=Instrument.FLAG_GETSET,
                           units='Hz',
                           minval=0,
                           maxval=1./8e-9,
                           type=types.FloatType)
        self.add_parameter('ro_pulse_delay',
                           flags=Instrument.FLAG_GETSET,
                           units='s',
                           minval=0,
                           maxval=64e-6,
                           type=types.FloatType)
        self.add_parameter('period',
                           flags=Instrument.FLAG_GETSET,
                           units='s',
                           minval=8e-9,
                           maxval=1,
                           type=types.FloatType)
        self.add_parameter('average',
                           flags=Instrument.FLAG_GETSET,
                           units='points',
                           minval=1,
                           type=types.IntType)
        self.add_parameter('period_min',
                           flags=Instrument.FLAG_GETSET,
                           units='s',
                           minval=8e-9,
                           maxval=1,
                           type=types.FloatType)
        self.add_parameter('frequency_start',
                           flags=Instrument.FLAG_SET,
                           units='GHz',
                           minval=1e-4,
                           maxval=40,
                           type=types.FloatType,
                           channels=(1, 2),
                           channel_prefix='src%d_')
        self.add_parameter('frequency_stop',
                           flags=Instrument.FLAG_SET,
                           units='Hz',
                           minval=1e-4,
                           maxval=40,
                           channels=(1, 2),
                           channel_prefix='src%d_',
                           type=types.FloatType)
        self.add_parameter('frequency_points',
                           flags=Instrument.FLAG_SET,
                           units='%',
                           minval=1,
                           maxval=10000000,
                           channels=(1, 2),
                           channel_prefix='src%d_',
                           type=types.FloatType)
                           
                           
        # Initializing parameters
        
        self.set_ro_pulse_duration(2*640e-9) # Hz
        self.set_ro_pulse_amplitude(0.2) # V 
        self.set_ro_pulse_frequency(31.25e6) # Hz
        self.set_ro_pulse_delay(200e-9) # s 
        self.set_period(1)
        self._period_min = 100e-6
        self._security_time = 100e-9
        self._nb_point_avg = 10000

        if mwsrc_qubit != 'None':
            self._microwave_generator1.set_freqsweep('off')
            self._microwave_generator2.set_freqsweep('on')
            self._microwave_generator2.set_sweepmode('STEP')
            self._microwave_generator2.set_spacingfreq('lin')
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            self._microwave_generator1.set_status('off')
            self._microwave_generator2.set_status('off')
            self._microwave_generator1.set_gui_update('ON')
            self._microwave_generator2.set_gui_update('ON')
        else:
            self._microwave_generator1.set_freqsweep('on')
            self._microwave_generator1.set_sweepmode('STEP')
            self._microwave_generator1.set_spacingfreq('lin')
            self._microwave_generator1.set_status('off')
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            self._microwave_generator1.set_gui_update('ON')
        self._redpitaya.reset_LUT()

    def do_set_ro_pulse_duration(self,duration): 
        '''
            Set the pulse duration of the Repditaya. 
            Input :
                duration(float): duration of the pulse in second
        '''
        self._ro_pulse_duration = duration
        
    def do_get_ro_pulse_duration(self): 
        '''
            Get the pulse duration of the Repditaya. 
            Output :
                duration(float): duration of the pulse in second
        '''
        return self._ro_pulse_duration
        
    def do_set_ro_pulse_frequency(self,frequency): 
        '''
            Set the frequency of the pulse generated by the Repditaya. 
            Input :
                frequency(float): frequency in Hz 
        '''
        self._ro_pulse_frequency = frequency
        
    def do_get_ro_pulse_frequency(self): 
        '''
            Get the frequency of the pulse generated by the Repditaya. 
            Output :
                frequency(float): frequency in Hz 
        '''
        return self._ro_pulse_frequency

    def do_set_ro_pulse_amplitude(self,amplitude): 
        '''
            Set the amplitude of the pulse generated by the Repditaya. 
            Input :
                amplitude(float): amplitude in V
        '''
        self._ro_pulse_amplitude = amplitude
        
    def do_get_ro_pulse_amplitude(self):
        '''
            Get the amplitude of the pulse generated by the Repditaya. 
            Output :
                amplitude(float): amplitude in V
        '''
        return self._ro_pulse_amplitude
        
    def do_set_ro_pulse_delay(self,delay): 
        '''
            Get the delay between the begining of the DAC signal and the IQ signal.
            Used to compensate the propagation time in the fridge 
            Input :
                delay(float): delay in second 
        '''
        self._ro_pulse_delay = delay
        
    def do_get_ro_pulse_delay(self): 
        '''
            Get the delay between the begining of the DAC signal and the IQ signal.
            Used to compensate the propagation time in the fridge 
            Output :
                delay(float): delay in second 
        '''
        return self._ro_pulse_delay
        
    def do_set_period(self,period): 
        '''
            Set the period of the signal generated by the Redpitaya
            Input :
                period(float): period in second 
        '''
        self._redpitaya.set_period(period)
        
    def do_get_period(self): 
        '''
            Get the period of the signal generated by the Redpitaya
            Output :
                period(float): period in second 
        '''
        return self._period
        
    def do_set_average(self, nb_point):
        '''
            Set the number of points taken by the Redpitaya
            Input :
                nb_point(int): number of points 
        '''
        self._nb_point_avg = nb_point

    def do_get_average(self): 
        '''
            Get the number of points taken by the Redpitaya
            Output :
                nb_point_avg (int): number of points
        '''
        return self._nb_point_avg

    def do_set_period_min(self, period_min): 
        '''
            Set the minimum period between two signal
            Input :
                period_min(float): period in second 
        '''
        self._period_min = period_min
        
    def do_get_period_min(self): 
        '''
            Get the security time between two period generated by the Redpitaya
            Output :
                time(float): security time in second 
        '''
        return self._period_min
        
    def do_set_frequency_start(self,frequency_start, channel): 
        '''
            Set the starting frequency of one microwave source tacking into account the SSB 
            and the Redpitaya frequency. 
            Input :
                frequency_start (float) : frequency in GHz
                channel (int): number corresponding to the source  
        # '''
        if channel == 1:
            
            f_ro = frequency_start - self.get_ro_pulse_frequency()*1e-9*self._SSB_tone1.get_band_type()
            if frequency_start > self._SSB_tone1.get_freq_stop() or frequency_start < self._SSB_tone1.get_freq_start():
                print 'Carefull! You are over the range of the SSB1'
            self._microwave_generator1.set_startfreq(f_ro)
            qt.msleep(0.1)

        elif channel == 2: 
            f_ex = frequency_start - self.get_ro_pulse_frequency()*1e-9*self._SSB_tone2.get_band_type()
            if frequency_start > self._SSB_tone2.get_freq_stop() or frequency_start < self._SSB_tone2.get_freq_start():
                print 'Carefull! You are over the range of the SSB2'
            self._microwave_generator2.set_startfreq(f_ex)
            
            qt.msleep(0.1)

        else: 
            raise ValueError('Channel name of the microwave source should be 1 or 2')
        channel = channel

    def do_set_frequency_stop(self,frequency_stop, channel): 
        '''
            Set the stopping frequency of one microwave source tacking into account the SSB 
            and the Redpitaya frequency. 
            Input :
                frequency_stop (float) : frequency in GHz
                channel (int): number corresponding to the source  
        '''
        if channel == 1:
            f_ro = frequency_stop - self.get_ro_pulse_frequency()*1e-9*self._SSB_tone1.get_band_type()
            if frequency_stop > self._SSB_tone1.get_freq_stop() or frequency_stop < self._SSB_tone1.get_freq_start():
                print 'Careful! You are over the range of the SSB1'
            self._microwave_generator1.set_stopfreq(f_ro)
            qt.msleep(0.1)

            
        elif channel == 2: 
            f_ex = frequency_stop - self.get_ro_pulse_frequency()*1e-9*self._SSB_tone2.get_band_type()
            if frequency_stop > self._SSB_tone2.get_freq_stop() or frequency_stop < self._SSB_tone2.get_freq_start():
                print 'Careful! You are over the range of the SSB2'
            self._microwave_generator2.set_stopfreq(f_ex)
            qt.msleep(0.1)

        else: 
            raise ValueError('Channel name of the microwave source should be 1 or 2')
            
    def do_set_frequency_points(self, frequency_points, channel): 
        '''
            Set the frequency step of one microwave source tacking into account the SSB 
            and the Redpitaya frequency. 
            Input :
                frequency_sweep (float) : frequency in GHz
                channel (int): number corresponding to the source  
        '''
        if channel == 1:
            self._microwave_generator1.set_pointsfreq(frequency_points)
            qt.msleep(0.1)

        elif channel == 2: 
            self._microwave_generator2.set_pointsfreq(frequency_points)
            qt.msleep(0.1)

        else: 
            raise ValueError('Channel name of the microwave source should be 1 or 2')
    
    def do_set_cw_frequency(self, cwf, channel):
        '''
            Set the cw frequency of one microwave source tacking into account the SSB 
            and the Redpitaya frequency. 
            Input :
                cwf (float) : frequency in GHz
                channel (int): number corresponding to the source  
        '''
        if channel == 1:
            f_ro = cwf - self._SSB_tone1.get_band_type()*self.get_ro_pulse_frequency()*1e-9
            if cwf > self._SSB_tone1.get_freq_stop() or cwf < self._SSB_tone1.get_freq_start():
                print 'Careful! You are over the range of the SSB1'
            self._microwave_generator1.set_frequency(f_ro)
            qt.msleep(0.1)

        elif channel == 2:
            f_ex = cwf - self._SSB_tone2.get_band_type()*self.get_ro_pulse_frequency()*1e-9 
            if cwf > self._SSB_tone2.get_freq_stop() or cwf < self._SSB_tone2.get_freq_start():
                print 'Careful! You are over the range of the SSB2'
            self._microwave_generator2.set_frequency(f_ex)
            qt.msleep(0.1)
            
        else:
            raise ValueError('Channel name of the microwave source should be 1 or 2')
            
    def do_get_cw_frequency(self,channel): 
        '''
            Get the cw frequency of one microwave source tacking into account the SSB 
            and the Redpitaya frequency. 
            Input :
                channel (int): number corresponding to the source
            Output : 
                frequency(float) after the SSB in GHz 
        '''
        if channel == 1: 
            return self._microwave_generator1.get_frequency() + self._SSB_tone1.get_band_type()*self.get_ro_pulse_frequency()*1e-9
        if channel == 2: 
            return self._microwave_generator2.get_frequency() + self._SSB_tone2.get_band_type()*self.get_ro_pulse_frequency()*1e-9
        else: 
            raise ValueError('Channel name of the microwave source should be 1 or 24')

    def oscilloscope(self,channel,power_mw,freq_ro,nb_measure): 
    
        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(freq_ro)
        self._microwave_generator1.set_power(power_mw)
        
        self._redpitaya.reset_LUT()
        self._redpitaya.set_start_ADC(0)
        self._redpitaya.set_stop_ADC(self._ro_pulse_duration+2*self._ro_pulse_delay_IQ)
        
        table_sin = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                self._ro_pulse_duration, self._ro_pulse_delay_trigger])

        self._redpitaya.send_DAC_LUT(table_sin, channel, trigger=channel)

        
        # data = self._redpitaya.get_data(mode='IQINT', nb_measure=len(freq_vec))
        data = self._redpitaya.get_data_adc_fix('ADC', nb_measure, int((self._ro_pulse_duration+2*self._ro_pulse_delay_IQ)/8e-9))
        
        if channel == 'CH1':
            CH1 = data
            return CH1
        elif channel == 'CH2':
            CH2 = data[1]
            return CH2
        else:
            raise ValueError('Wrong channel name in the one_tone sequence')

    def one_tone(self,freq_vec, power_mw, channel): 
    
        '''
            Do a onetone measurement using the Redpitaya and one microwave source
            Input:
                - freq_vec(float): vector of frequency to be played by the microwave source in GHz
                - power_mw(float): power of the microwave source in dB
                - channel(string): channel of the redpitaya used to generate signal and reading out.
                  It should be 'CH1' of 'CH2'.
            Output : 
            - I (float) : vector of I quadrature
            - Q (float) : vector of Q quadrature
        '''
    
        # --- preparation of the microwave source 
        self._microwave_generator1.set_gui_update('on')
        self._microwave_generator1.set_power(power_mw)
        self._microwave_generator1.set_gui_update('off')
        self._microwave_generator1.set_freqsweep('off')
        
        # --- genereation of the LUT 
        table_cos_ro = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, 1,
                                                self._ro_pulse_duration,0])
        table_sin_ro = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, 1,
                                                self._ro_pulse_duration,0])
                                                            
        table_ex = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                            self._ro_pulse_duration,0])

        # --- set the period and the ADC/DAC parameters 
        time_step = self._ro_pulse_duration
        period = max(time_step, self._period_min)
        self.set_period(period+ self._security_time)
        self._redpitaya.set_stop_DAC(time_step)
        self._redpitaya.set_start_ADC(self._ro_pulse_delay)
        self._redpitaya.set_stop_ADC(self._ro_pulse_delay + time_step)
        
        

        # --- reset and fill the LUT 
        self._redpitaya.reset_LUT()
        self._redpitaya.send_DAC_LUT(table_ex, channel)
        self._redpitaya.send_IQ_LUT(table_cos_ro, channel, quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_ro, channel, quadrature='Q')
        
        # --- take the data for the frequency vector 
        I = np.zeros(len(freq_vec))
        Q = np.zeros(len(freq_vec))

        for k in xrange(len(freq_vec)): 
            print freq_vec[k]
            self.set_src1_cw_frequency(freq_vec[k])
            data = self._redpitaya.get_data(mode='IQINT', nb_measure=self._nb_point_avg)
            if channel == 'CH1': 
                I[k] = np.mean(data[0])/(time_step/8e-9)
                Q[k] = np.mean(data[1])/(time_step/8e-9)
            
            elif channel == 'CH2': 
                I[k] = np.mean(data[2])/(time_step/8e-9)
                Q[k] = np.mean(data[3])/(time_step/8e-9)
            
            else: 
                raise ValueError('For one tone the option are CH1 or CH2')

        return I, Q
        
    def IQ_noise(self,freq_ro, nb_points, power_mw, channel): 
    
        '''
            Do a I,Q measurement using the Redpitaya and one microwave source. 
            It can be used to characterize the noise of the measurement line
            Input:
                - freq_ro(float): frequency to be played by the microwave source in GHz
                - nb_points(int): number of points to be taken 
                - power_mw(float): power of the microwave source in dB
                - channel(string): channel of the redpitaya used to generate signal and reading out.
                  It should be 'CH1' of 'CH2'.
            Output : 
            - I (float) : vector of I quadrature
            - Q (float) : vector of Q quadrature
        '''
    
        # --- preparation of the microwave source 
        self._microwave_generator1.set_gui_update('on')
        self._microwave_generator1.set_power(power_mw)
        self._microwave_generator1.set_gui_update('off')
        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(freq_ro)
        
        # --- genereation of the LUT 
        table_cos_ro = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, 1,
                                                self._ro_pulse_duration,0])
        table_sin_ro = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, 1,
                                                self._ro_pulse_duration,0])
                                                            
        table_ex = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                            self._ro_pulse_duration,0])

        # --- set the period and the ADC/DAC parameters 
        time_step = self._ro_pulse_duration
        period = max(time_step, self._period_min)
        self.set_period(period+ self._security_time)
        self._redpitaya.set_stop_DAC(time_step)
        self._redpitaya.set_start_ADC(self._ro_pulse_delay)
        self._redpitaya.set_stop_ADC(self._ro_pulse_delay + time_step)
        
        

        # --- reset and fill the LUT 
        self._redpitaya.reset_LUT()
        self._redpitaya.send_DAC_LUT(table_ex, channel)
        self._redpitaya.send_IQ_LUT(table_cos_ro, channel, quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_ro, channel, quadrature='Q')
        
        # --- take the data 
            
        data = self._redpitaya.get_data(mode='IQINT', nb_measure=nb_points)
        
        if channel == 'CH1': 
            I = data[0]/(time_step/8e-9)
            Q = data[1]/(time_step/8e-9)
        
        elif channel == 'CH2': 
            I = data[2]/(time_step/8e-9)
            Q = data[3]/(time_step/8e-9)
        
        else: 
            raise ValueError('For one tone the option are CH1 or CH2')

        return I, Q
            
    def two_tones_rabi(self,freq_vec,freq_ro, power_ro, power_ex, t_ex = 1e-6,amp_ex = 0.2, channel_ro='CH1'):
        '''
            Do a twotone measurement using the redpitaya and two microwave sources.
            Carefull this is using a rabi-like sequence, the readout and the excitation
            are not simultaneous. 
            This can be usefull combined with one_tone to measure dispersive shift.
            Input:
                - freq_vec (float)    : vector of frequency to be played by the excitation source in GHz
                - freq_ro (float)     : readout frequency to be played by the readout source in GHz
                - power_ro (float)    : power of the readout source in dB 
                - power_ex (float)    : power of the excitation source in dB
                - t_ex (float)        : duration of the excitation in second, if 0 one do not use the SSB
                  for the excitation but directly the microwave source 
                - amp_ex (float)      : amplitude of excitation played by the redpitaya in volt 
                - channel_ro (string) : channel of the redpitaya used to generate signal and reading out.
            Output : 
            - I (float) : vector of I quadrature
            - Q (float) : vector of Q quadrature
        '''

        # --- preparation of the microwave source 
        self._microwave_generator1.set_gui_update('on')
        self._microwave_generator2.set_gui_update('on')
        
        self._microwave_generator1.set_freqsweep('off')
        self._microwave_generator2.set_freqsweep('off')
        
        self.set_src1_cw_frequency(freq_ro)
        
        self._microwave_generator1.set_power(power_ro)
        self._microwave_generator2.set_power(power_ex)
        
        self._microwave_generator1.set_gui_update('off')
        self._microwave_generator2.set_gui_update('off')
        
        
        """ !!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""
        # --- generate the LUT 
        table_sin_ro = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                       self._ro_pulse_duration, t_ex])
                                                       
        table_sin_IQ = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, 1,
                                                       self._ro_pulse_duration,0])
        table_cos_IQ = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, 1,
                                                        self._ro_pulse_duration,0])
                                                        
        table_sin_ex = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, amp_ex, t_ex, 0])
        
        
        
        # --- set the period and the ADC/DAC parameters 
        time_step = t_ex + self._ro_pulse_duration 
        period = self._period_min + time_step
        self.set_period(period)
        
        self._redpitaya.set_stop_DAC(time_step)
        self._redpitaya.set_start_ADC(t_ex + self._ro_pulse_delay)
        self._redpitaya.set_stop_ADC(time_step + self._ro_pulse_delay)
        
        # --- reset and fill the LUT()
        self._redpitaya.reset_LUT()
        self._redpitaya.send_DAC_LUT(table_sin_ro, channel_ro)
        # if t_ex = 0 one do bot  use de SSB for the excitation but directly the microwave source 
        if (t_ex != 0 and channel_ro == 'CH1'): 
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH2')
        elif (t_ex != 0 and channel_ro == 'CH2'): 
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH1')
            
        self._redpitaya.send_IQ_LUT(table_cos_IQ, channel_ro, quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_IQ, channel_ro, quadrature='Q')
        

        I = np.zeros(len(freq_vec))
        Q = np.zeros(len(freq_vec))
        
        # --- take the data for the frequency vector 
        t0 = time.time()
        for k in xrange(len(freq_vec)):       
            
            print freq_vec[k] 
            if t_ex == 0:
                self.set_src2_cw_frequency(freq_vec[k] + self._SSB_tone2.get_band_type()*self.get_ro_pulse_frequency()*1e-9)
            else: 
                self.set_src2_cw_frequency(freq_vec[k])
                
            data = self._redpitaya.get_data(mode='IQINT', nb_measure=self._nb_point_avg)
            
            if channel_ro == 'CH1': 
                I[k] = np.mean(data[0])/(self._ro_pulse_duration /8e-9)
                Q[k] = np.mean(data[1])/(self._ro_pulse_duration /8e-9)
            
            elif channel_ro == 'CH2': 
                I[k] = np.mean(data[2])/(self._ro_pulse_duration /8e-9)
                Q[k] = np.mean(data[3])/(self._ro_pulse_duration /8e-9)
            
            else: 
                raise ValueError('For one tone the option are CH1 or CH2')
            t1 = time.time()
            print t1-t0
            t0 = t1 

        return I, Q
        
    def two_tones(self,freq_vec,freq_ro, power_ro, power_ex, t_ro = 60e-6, t_ex = 60e-6, amp_ex = 0.2, channel_ro = 'CH1'):
        '''
            Do a twotone measurement using the redpitaya and two microwave sources. 
            Input:
                - freq_vec (float)    : vector of frequency to be played by the excitation source in GHz
                - freq_ro (float)     : readout frequency to be played by the readout source in GHz
                - power_ro (float)    : power of the readout source in dB 
                - power_ex (float)    : power of the excitation source in dB
                  for the excitation but directly the microwave source 
                - amp_ex (float)      : amplitude of excitation played by the redpitaya in volt 
                - channel_ro (string) : channel of the redpitaya used to generate signal and reading out.
            Output : 
            - I (float) : vector of I quadrature
            - Q (float) : vector of Q quadrature
        '''
        # --- preparation of the microwave source 
        self._microwave_generator1.set_gui_update('on')
        self._microwave_generator2.set_gui_update('on')
        
        self._microwave_generator1.set_freqsweep('off')
        self._microwave_generator2.set_freqsweep('off')
        
        self.set_src1_cw_frequency(freq_ro)
        
        self._microwave_generator1.set_power(power_ro)
        self._microwave_generator2.set_power(power_ex)
        
        self._microwave_generator1.set_gui_update('off')
        self._microwave_generator2.set_gui_update('off')
        
        # --- generate the LUT 
        table_sin_ro = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                       t_ro, 0])
        """!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""
        # table_sin_ro = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, self._ro_pulse_amplitude,
        #                                                t_ro, t_ex])
        """!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""
                                                       
        table_sin_IQ = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, 1,t_ro,0])
        table_cos_IQ = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, 1,t_ro,0])
                                                        
        table_sin_ex = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, amp_ex, t_ex, 0])
        
        
        # --- set the period and the ADC/DAC parameters 
        time_step = max(t_ex, t_ro)
        """!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""
        # time_step = t_ex+t_ro
        period = self._period_min + time_step
        """!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""
        self.set_period(period)
        self._redpitaya.set_stop_DAC(time_step)
        self._redpitaya.set_start_ADC(self._ro_pulse_delay)
        self._redpitaya.set_stop_ADC(t_ro + self._ro_pulse_delay)
        """!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""
        # self._redpitaya.set_start_ADC(self._ro_pulse_delay+t_ex)
        # self._redpitaya.set_stop_ADC(time_step + self._ro_pulse_delay)
        """!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""

        
        # --- reset and fill the LUT()
        self._redpitaya.reset_LUT()
        self._redpitaya.send_DAC_LUT(table_sin_ro, channel_ro)
        
        if channel_ro == 'CH1': 
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH2')
        else:
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH1')
            
        self._redpitaya.send_IQ_LUT(table_cos_IQ, channel_ro, quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_IQ, channel_ro, quadrature='Q')
        
        
        I = np.zeros(len(freq_vec))
        Q = np.zeros(len(freq_vec))
        
        # --- take the data for the frequency vector 
        t0 = time.time()
        for k in xrange(len(freq_vec)):       
            
            print freq_vec[k] 
            self.set_src2_cw_frequency(freq_vec[k])
            data = self._redpitaya.get_data(mode='IQINT', nb_measure=self._nb_point_avg)
            
            if channel_ro == 'CH1': 
                I[k] = np.mean(data[0])/(t_ro /8e-9)
                Q[k] = np.mean(data[1])/(t_ro /8e-9)
            
            elif channel_ro == 'CH2': 
                I[k] = np.mean(data[2])/(t_ro /8e-9)
                Q[k] = np.mean(data[3])/(t_ro /8e-9)
            
            else: 
                raise ValueError('For one tone the option are CH1 or CH2')
            t1 = time.time()
            print t1-t0
            t0 = t1 

        return I, Q

    def relaxation(self, freq_ex, freq_ro, power_ex, power_ro, t_wait, t_ex, amp_ex, channel_ro='CH1'):

        '''
            Do a relaxation measurement using the redpitaya and two microwave sources. 
            Input:
                - freq_ex (float)     : excitation frequency to be played by the excitation source in GHz
                - freq_ro (float)     : readout frequency to be played by the readout source in GHz
                - power_ex (float)    : power of the excitation source in dB
                - power_ro (float)    : power of the readout source in dB 
                - t_wait (float)      : time to wait between the excitation and the readout in second
                - t_ex (float)        : duration of the excitation in second, if 0 one do not use the SSB
                  for the excitation but directly the microwave source 
                - amp_ex (float)      : amplitude of excitation played by the redpitaya in volt 
                - channel_ro (string) : channel of the redpitaya used to generate signal and reading out.
            Output : 
            - I (float) : vector of I quadrature
            - Q (float) : vector of Q quadrature
        '''

        self._microwave_generator1.set_gui_update('on')
        self._microwave_generator2.set_gui_update('on')
        
        self._microwave_generator1.set_freqsweep('off')
        self._microwave_generator2.set_freqsweep('off')
        
        self.set_src1_cw_frequency(freq_ro)
        self.set_src2_cw_frequency(freq_ex)
        
        self._microwave_generator1.set_power(power_ro)
        self._microwave_generator2.set_power(power_ex)
        
        self._microwave_generator1.set_gui_update('off')
        self._microwave_generator2.set_gui_update('off')
        
        # --- generate the LUT 
        table_sin_ro = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                       self._ro_pulse_duration, t_ex+t_wait])

                                                       
        table_sin_IQ = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, 1,self._ro_pulse_duration,0])
        table_cos_IQ = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, 1,self._ro_pulse_duration,0])
                                                        
        table_sin_ex = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, amp_ex, t_ex, 0])
        
        
        # --- set the period and the ADC/DAC parameters 
        time_step = t_ex+self._ro_pulse_duration+t_wait
        period = self._period_min + time_step

        self.set_period(period)
        self._redpitaya.set_stop_DAC(time_step)

        self._redpitaya.set_start_ADC(self._ro_pulse_delay+t_ex+t_wait)
        self._redpitaya.set_stop_ADC(time_step + self._ro_pulse_delay)


        
        # --- reset and fill the LUT()
        self._redpitaya.reset_LUT()
        self._redpitaya.send_DAC_LUT(table_sin_ro, channel_ro)
        
        if channel_ro == 'CH1': 
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH2')
        else:
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH1')
            
        self._redpitaya.send_IQ_LUT(table_cos_IQ, channel_ro, quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_IQ, channel_ro, quadrature='Q')
        
        
        data = self._redpitaya.get_data(mode='IQINT', nb_measure=self._nb_point_avg)
        
        if channel_ro == 'CH1': 
            I = np.mean(data[0])/(self._ro_pulse_duration /8e-9)
            Q = np.mean(data[1])/(self._ro_pulse_duration /8e-9)
        
        elif channel_ro == 'CH2': 
            I = np.mean(data[2])/(self._ro_pulse_duration /8e-9)
            Q = np.mean(data[3])/(self._ro_pulse_duration /8e-9)
        
        else: 
            raise ValueError('For one tone the option are CH1 or CH2')

        return np.array([I]), np.array([Q])

    def rabi(self,freq_ex,freq_ro, power_ex, power_ro, t_ex, amp_ex, channel_ro='CH1', ADC=False):
        '''
            Do a rabi measurement using the redpitaya and two microwave sources. 
            Input:
                - freq_ex (float)    : vector of frequency to be played by the excitation source in GHz
                - freq_ro (float)     : readout frequency to be played by the readout source in GHz
                - power_ex (float)    : power of the excitation source in dB
                - power_ro (float)    : power of the readout source in dB 
                - t_ex (float)        : duration of the excitation in second, if 0 one do not use the SSB
                  for the excitation but directly the microwave source 
                - amp_ex (float)      : amplitude of excitation played by the redpitaya in volt 
                - channel_ro (string) : channel of the redpitaya used to generate signal and reading out.
            Output : 
            - I (float) : vector of I quadrature
            - Q (float) : vector of Q quadrature
        '''

        # --- preparation of the microwave source 
        self._microwave_generator1.set_gui_update('on')
        self._microwave_generator2.set_gui_update('on')
        
        self._microwave_generator1.set_freqsweep('off')
        self._microwave_generator2.set_freqsweep('off')
        
        self.set_src1_cw_frequency(freq_ro)
        self.set_src2_cw_frequency(freq_ex)
        
        self._microwave_generator1.set_power(power_ro)
        self._microwave_generator2.set_power(power_ex)
        
        self._microwave_generator1.set_gui_update('off')
        self._microwave_generator2.set_gui_update('off')
        
        """ !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""
        # --- generate the LUT 
        table_sin_ro = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                       self._ro_pulse_duration, t_ex])
                                                       
        table_sin_IQ = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, 1,
                                                       self._ro_pulse_duration,0])
        table_cos_IQ = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, 1,
                                                        self._ro_pulse_duration,0])
                                                        
        table_sin_ex = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, amp_ex, t_ex, 0])
        
        
        
        # --- set the period and the ADC/DAC parameters 
        time_step = t_ex + self._ro_pulse_duration 

        period = self._period_min + time_step
        self.set_period(period)
        self._redpitaya.set_stop_DAC(time_step)

        """ !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""
        self._redpitaya.set_start_ADC(t_ex + self._ro_pulse_delay)
        self._redpitaya.set_stop_ADC(time_step + self._ro_pulse_delay)
        
        # --- reset and fill the LUT()
        self._redpitaya.reset_LUT()
        self._redpitaya.send_DAC_LUT(table_sin_ro, channel_ro)

        if channel_ro == 'CH1': 
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH2')
        elif channel_ro == 'CH2': 
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH1')
            
        self._redpitaya.send_IQ_LUT(table_cos_IQ, channel_ro, quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_IQ, channel_ro, quadrature='Q')
        
        
        # --- take the data for the frequency vector 

        if ADC: 
            data = self._redpitaya.get_data(mode='ADC', nb_measure=1)
        else: 
            data = self._redpitaya.get_data(mode='IQINT', nb_measure=self._nb_point_avg)
        
        
        if ADC: 
            CH1 = data[0]
            CH2 = data[1] 
        elif (not(ADC) and channel_ro == 'CH1'): 
            I = np.mean(data[0])/(self._ro_pulse_duration/8e-9)
            Q = np.mean(data[1])/(self._ro_pulse_duration/8e-9)
        elif (not(ADC) and channel_ro == 'CH2'): 
            I = np.mean(data[2])/(self._ro_pulse_duration/8e-9)
            Q = np.mean(data[3])/(self._ro_pulse_duration/8e-9)
        else: 
            raise ValueError('For one tone the option are CH1 or CH2')

        if ADC: 
            return CH1, CH2
        else: 
            return np.array([I]), np.array([Q])
        
    def ramsey(self,freq_ex,freq_ro, power_ex, power_ro, t_wait, t_ex, amp_ex, channel_ro='CH1'):
        '''
            Do a ramsey measurement using the redpitaya and two microwave sources. 
            Input:
                - freq_ex (float)    : vector of frequency to be played by the excitation source in GHz
                - freq_ro (float)     : readout frequency to be played by the readout source in GHz
                - power_ex (float)    : power of the excitation source in dB
                - power_ro (float)    : power of the readout source in dB
                - t_wait (float)      : time to wait between the two excitations in second
                - t_ex (float)        : duration of the excitation in second, if 0 one do not use the SSB
                  for the excitation but directly the microwave source 
                - amp_ex (float)      : amplitude of excitation played by the redpitaya in volt 
                - channel_ro (string) : channel of the redpitaya used to generate signal and reading out.
            Output : 
            - I (float) : vector of I quadrature
            - Q (float) : vector of Q quadrature
        '''

        # --- preparation of the microwave source 
        self._microwave_generator1.set_gui_update('on')
        self._microwave_generator2.set_gui_update('on')
        
        self._microwave_generator1.set_freqsweep('off')
        self._microwave_generator2.set_freqsweep('off')
        
        self.set_src1_cw_frequency(freq_ro)
        self.set_src2_cw_frequency(freq_ex)
        
        self._microwave_generator1.set_power(power_ro)
        self._microwave_generator2.set_power(power_ex)
        
        self._microwave_generator1.set_gui_update('off')
        self._microwave_generator2.set_gui_update('off')
        
        # --- generate the LUT 
        table_sin_ro = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                       self._ro_pulse_duration, 2 * t_ex + t_wait])
                                                       
        table_sin_IQ = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, 1,
                                                       self._ro_pulse_duration,0])
        table_cos_IQ = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, 1,
                                                        self._ro_pulse_duration,0])
        table_sin_ex = self._redpitaya.fill_LUT('RAMSEY', [self._ro_pulse_frequency, amp_ex, t_ex, t_wait, 0])
                                                        
        # --- set the period and the ADC/DAC parameters 
        time_step = 2*t_ex + t_wait + self._ro_pulse_duration 
        period = self._period_min + time_step
        self.set_period(period)
        self._redpitaya.set_stop_DAC(time_step)
        self._redpitaya.set_start_ADC(2*t_ex + t_wait + self._ro_pulse_delay)
        self._redpitaya.set_stop_ADC(time_step + self._ro_pulse_delay)
        
        # --- reset and fill the LUT()
        self._redpitaya.reset_LUT()
        self._redpitaya.send_DAC_LUT(table_sin_ro, channel_ro)

        if channel_ro == 'CH1': 
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH2')
        elif channel_ro == 'CH2': 
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH1')
            
        self._redpitaya.send_IQ_LUT(table_cos_IQ, channel_ro, quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_IQ, channel_ro, quadrature='Q')
        
        # --- take the data for the frequency vector 

        data = self._redpitaya.get_data(mode='IQINT', nb_measure=self._nb_point_avg)
        
        if channel_ro == 'CH1': 
            I= np.mean(data[0])/(self._ro_pulse_duration/8e-9)
            Q = np.mean(data[1])/(self._ro_pulse_duration/8e-9)
        
        elif channel_ro == 'CH2': 
            I = np.mean(data[2])/(self._ro_pulse_duration/8e-9)
            Q = np.mean(data[3])/(self._ro_pulse_duration/8e-9)
        
        else: 
            raise ValueError('For one tone the option are CH1 or CH2')

        return np.array([I]), np.array([Q])

    def echo(self, freq_ex, freq_ro, power_ex, power_ro, t_wait, t_ex, amp_ex, channel_ro='CH1'):
        '''
            Do a echo measurement using the redpitaya and two microwave sources. 
            Input:
                - freq_ex (float)    : vector of frequency to be played by the excitation source in GHz
                - freq_ro (float)     : readout frequency to be played by the readout source in GHz
                - power_ex (float)    : power of the excitation source in dB
                - power_ro (float)    : power of the readout source in dB 
                - t_wait (float)      : time to wait between the two excitations in second
                - t_ex (float)        : duration of the excitation in second, if 0 one do not use the SSB
                  for the excitation but directly the microwave source 
                - amp_ex (float)      : amplitude of excitation played by the redpitaya in volt 
                - channel_ro (string) : channel of the redpitaya used to generate signal and reading out.
            Output : 
            - I (float) : vector of I quadrature
            - Q (float) : vector of Q quadrature
        '''

        # --- preparation of the microwave source 
        self._microwave_generator1.set_gui_update('on')
        self._microwave_generator2.set_gui_update('on')
        
        self._microwave_generator1.set_freqsweep('off')
        self._microwave_generator2.set_freqsweep('off')
        
        self.set_src1_cw_frequency(freq_ro)
        self.set_src2_cw_frequency(freq_ex)
        
        self._microwave_generator1.set_power(power_ro)
        self._microwave_generator2.set_power(power_ex)
        
        self._microwave_generator1.set_gui_update('off')
        self._microwave_generator2.set_gui_update('off')

        # --- generate the LUT 
        table_sin_ro = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                       self._ro_pulse_duration, 4 * t_ex + 2 * t_wait])
        table_sin_IQ = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, 1,
                                                       self._ro_pulse_duration,0])
        table_cos_IQ = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, 1,
                                                        self._ro_pulse_duration,0])
        table_sin_ex = self._redpitaya.fill_LUT('ECHO', [self._ro_pulse_frequency, amp_ex, t_ex, t_wait, 0])

        # --- set the period and the ADC/DAC parameters 
        time_step = 4 * t_ex + 2 * t_wait + self._ro_pulse_duration 
        period = self._period_min + time_step
        self.set_period(period)
        self._redpitaya.set_stop_DAC(time_step)
        self._redpitaya.set_start_ADC(4 * t_ex + 2 * t_wait + self._ro_pulse_delay)
        self._redpitaya.set_stop_ADC(time_step + self._ro_pulse_delay)

        # --- reset and fill the LUT()
        self._redpitaya.reset_LUT()
        self._redpitaya.send_DAC_LUT(table_sin_ro, channel_ro)

        if channel_ro == 'CH1': 
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH2')
        elif channel_ro == 'CH2': 
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH1')
            
        self._redpitaya.send_IQ_LUT(table_cos_IQ, channel_ro, quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_IQ, channel_ro, quadrature='Q')
        
        # --- take the data for the frequency vector 

        data = self._redpitaya.get_data(mode='IQINT', nb_measure=self._nb_point_avg)
        
        if channel_ro == 'CH1': 
            I= np.mean(data[0])/(self._ro_pulse_duration/8e-9)
            Q = np.mean(data[1])/(self._ro_pulse_duration/8e-9)
        
        elif channel_ro == 'CH2': 
            I = np.mean(data[2])/(self._ro_pulse_duration/8e-9)
            Q = np.mean(data[3])/(self._ro_pulse_duration/8e-9)
        
        else: 
            raise ValueError('For one tone the option are CH1 or CH2')

        return np.array([I]), np.array([Q])

    def rabi_sequence(self,freq_ex,freq_ro, power_ex, power_ro, t_ex_vec,amp_ex, channel_ro = 'CH1'):

        I_vec = np.array([])
        Q_vec = np.array([])
        for k in xrange(len(t_ex_vec)):
            print str(t_ex_vec[k]*1e6)
            I,Q = self.rabi(freq_ex,freq_ro, power_ex, power_ro, t_ex_vec[k],amp_ex, channel_ro)
            # I,Q = self.two_tones(freq_ex,freq_ro, power_ex, power_ro, t_ex_vec[k],amp_ex, channel_ro)
            I_vec = np.concatenate((I_vec, I))
            Q_vec = np.concatenate((Q_vec, Q))
        return I_vec,Q_vec
        
    def relaxation_sequence(self,freq_ex,freq_ro, power_ex, power_ro, t_wait_vec, t_ex, amp_ex, channel_ro = 'CH1'):

        I_vec = np.array([])
        Q_vec = np.array([])
        for k in xrange(len(t_wait_vec)):
            print str(t_wait_vec[k]*1e6)
            I,Q = self.relaxation(freq_ex,freq_ro, power_ex, power_ro, t_wait_vec[k], t_ex,amp_ex, channel_ro)
            I_vec = np.concatenate((I_vec, I))
            Q_vec = np.concatenate((Q_vec, Q))
        return I_vec,Q_vec

    def ramsey_sequence(self,freq_ex,freq_ro, power_ex, power_ro, t_wait_vec, t_ex, amp_ex, channel_ro = 'CH1'):

        I_vec = np.array([])
        Q_vec = np.array([])
        for k in xrange(len(t_wait_vec)):
            print str(t_wait_vec[k]*1e6)
            I, Q = self.ramsey(freq_ex,freq_ro, power_ex, power_ro, t_wait_vec[k], t_ex, amp_ex, channel_ro)
            I_vec = np.concatenate((I_vec, I))
            Q_vec = np.concatenate((Q_vec, Q))
        return I_vec, Q_vec

    def echo_sequence(self, freq_ex, freq_ro, power_ex, power_ro, t_wait_vec, t_ex, amp_ex, channel_ro='CH1'):
        I_vec = np.array([])
        Q_vec = np.array([])
        for k in xrange(len(t_wait_vec)):
            print str(t_wait_vec[k]*1e6)
            I, Q = self.echo(freq_ex, freq_ro, power_ex, power_ro, t_wait_vec[k], t_ex, amp_ex, channel_ro)
            I_vec = np.concatenate((I_vec, I))
            Q_vec = np.concatenate((Q_vec, Q))
        return I_vec, Q_vec

    def average_one_tone(self, freq_vec, power_mw, channel, average):
    
        '''
            Do a averageing of onetone measurement using the Redpitaya and one microwave source
            Input:
                - freq_vec(float): vector of frequency to be played by the microwave source in GHz
                - power_mw(float): power of the microwave source in dB
                - channel(string): channel of the redpitaya used to generate signal and reading out.
                  It should be 'CH1' of 'CH2'.
                - average (int)  : number of time it repeat the sequence 
            Output : 
            - I_avg (float) : vector of I quadrature
            - Q_avg (float) : vector of Q quadrature
        '''

        I_avg = []
        Q_avg = []

        for k in xrange(average):
            data = self.one_tone(freq_vec, power_mw, channel)
            I_avg.append(data[0])
            Q_avg.append(data[1])

        I_avg = np.mean(np.array([I_avg]), axis=0)
        Q_avg = np.mean(np.array([Q_avg]), axis=0)

        return I_avg, Q_avg 
        
    def average_two_tones(self, freq_vec, freq_ro, power_ro, power_ex,t_ro = 60e-6, t_ex = 60e-6,amp_ex = 0.5, channel_ro = 'CH1',average = 100):

        I_avg = []
        Q_avg = []
        for k in xrange(average):
            print 'Average: ' + str(k) 
            data = self.two_tones(freq_vec, freq_ro, power_ro, power_ex, t_ro, t_ex, amp_ex, channel_ro)
            I_avg.append(data[0])
            Q_avg.append(data[1])
        I_avg = np.mean(I_avg, axis=0)
        Q_avg = np.mean(Q_avg, axis=0)
        
        return  I_avg, Q_avg
        
    def average_two_tones_rabi(self, freq_vec, freq_ro, power_ro, power_ex, t_ex = 1e-6,amp_ex = 0.5, channel_ro = 'CH1',average = 100):

        I_avg = []
        Q_avg = []
        for k in xrange(average):
            print 'Average: ' + str(k) 
            data = self.two_tones(freq_vec, freq_ro, power_ro, power_ex, t_ex, amp_ex, channel_ro)
            I_avg.append(data[0])
            Q_avg.append(data[1])
        I_avg = np.mean(I_avg, axis=0)
        Q_avg = np.mean(Q_avg, axis=0)
        
        return  I_avg, Q_avg

    def average_relaxation(self, freq_ex, freq_ro, power_ex, power_ro, t_wait, t_ex, amp_ex, channel_ro = 'CH1', average = 100):

        I_avg = []
        Q_avg = []
        for k in xrange(average):
            print 'Average: ' + str(k) 
            data = self.relaxation_sequence(freq_ex, freq_ro, power_ex, power_ro, t_wait, t_ex, amp_ex, channel_ro)
            I_avg.append(data[0])
            Q_avg.append(data[1])
        I_avg = np.mean(I_avg, axis=0)
        Q_avg = np.mean(Q_avg, axis=0)
        return I_avg, Q_avg

    def average_rabi(self,freq_ex,freq_ro, power_ex, power_ro, t_ex_vec, amp_ex, channel_ro = 'CH1', average = 100):

        I_avg = []
        Q_avg = []
        for k in xrange(average): 
            print 'Average: '+ str(k)
            data = self.rabi_sequence(freq_ex,freq_ro, power_ex, power_ro, t_ex_vec,amp_ex, channel_ro)
            I_avg.append(data[0])
            Q_avg.append(data[1])
        I_avg = np.mean(I_avg, axis=0)
        Q_avg = np.mean(Q_avg, axis=0)
        
        return  I_avg, Q_avg

    def average_rabi_ADC(self,freq_ex,freq_ro, power_ex, power_ro, t_ex, amp_ex, channel_ro, average):
        I_avg = []
        Q_avg = []
        for k in xrange(average): 
            print 'Average: '+ str(k)
            data = self.rabi(freq_ex,freq_ro, power_ex, power_ro, t_ex, amp_ex, channel_ro, True)
            I_avg.append(data[0])
            Q_avg.append(data[1])
        I_avg = np.mean(I_avg, axis=0)
        Q_avg = np.mean(Q_avg, axis=0)
        
        return  I_avg, Q_avg
    
    def average_ramsey(self,freq_ex,freq_ro, power_ex, power_ro, t_wait_vec, t_ex, amp_ex, channel_ro = 'CH1', average = 100):

        I_avg = []
        Q_avg = []
        for k in xrange(average):
            print 'Average: '+ str(k)
            data = self.ramsey_sequence(freq_ex,freq_ro, power_ex, power_ro, t_wait_vec, t_ex, amp_ex, channel_ro)
            I_avg.append(data[0])
            Q_avg.append(data[1])
        I_avg = np.mean(I_avg, axis=0)
        Q_avg = np.mean(Q_avg, axis=0)
        
        return I_avg, Q_avg

    def average_echo(self, freq_ex, freq_ro, power_ex, power_ro, t_wait_vec, t_ex, amp_ex, channel_ro='CH1', average=100):
        I_avg = []
        Q_avg = []
        for k in xrange(average):
            print 'Average: '+ str(k)
            data = self.echo_sequence(freq_ex, freq_ro, power_ex, power_ro, t_wait_vec, t_ex, amp_ex, channel_ro)
            I_avg.append(data[0])
            Q_avg.append(data[1])
        I_avg = np.mean(I_avg, axis=0)
        Q_avg = np.mean(Q_avg, axis=0)

        return I_avg, Q_avg