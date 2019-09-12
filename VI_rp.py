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


class VI_rp(Instrument):
    

    def __init__(self, name, mwsrc1, ssb1, redpitaya, mwsrc2='None', ssb2='None'):

        # -------------------------------------------------------------------------------------------------------------#
        # -----------------------------------    Importation of the device    -----------------------------------------#
        # -------------------------------------------------------------------------------------------------------------#
        
        Instrument.__init__(self, name, tags=['virtual'])
        self._instruments = instruments.get_instruments()
        self._SSB_tone1 = self._instruments.get(ssb1)
        self._microwave_generator1 = self._instruments.get(mwsrc1)
        # self._microwave_generator1.set_status('ON')
        # self._microwave_generator1.set_power(-30)
        
        self._redpitaya = self._instruments.get(redpitaya)



        # if we import the second microwave generator or not
        if mwsrc2 != 'None':
            self._presence_mwsrc2 = 1
            self._microwave_generator2 = self._instruments.get(mwsrc2)
            # self._microwave_generator2.set_status('ON')
        else:
            self._presence_mwsrc2 = 0
        # if we import the second ssb or not
        if ssb2 != 'None':
            self._presence_ssb2 = 1
            self._SSB_tone2 = self._instruments.get(ssb2)
        else:
            self._presence_ssb2 = 0

        # # -------------------------------------------------------------------------------------------------------------#
        # # ----------------------------------    Creation of the parameters    -----------------------------------------#
        # # -------------------------------------------------------------------------------------------------------------#

        self.add_parameter('power_first_tone',
                           flags=Instrument.FLAG_GETSET,
                           minval=-50.,
                           maxval=4.,
                           units='dBm',
                           type=types.FloatType)
        self.add_parameter('power_second_tone',
                           flags=Instrument.FLAG_GETSET,
                           minval=-50.,
                           maxval=4.,
                           units='dBm',
                           type=types.FloatType)
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
        self.add_parameter('ro_pulse_delay_trigger',
                           flags=Instrument.FLAG_GETSET,
                           units='s',
                           minval=0,
                           maxval=64e-6,
                           type=types.FloatType)
        self.add_parameter('ro_pulse_delay_IQ',
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
        
        self.set_ro_pulse_duration(1e-6) # Hz
        self.set_ro_pulse_amplitude(0.5) # V 
        self.set_ro_pulse_frequency(31.25e6) # Hz
        self.set_ro_pulse_delay_trigger(0e-9) # s
        self.set_ro_pulse_delay_IQ(200e-9) # s 
        
        self._time_loop = 0.5 # s
        self._nb_point_int_max = 7000
        self._period_min = 64e-6 # s
        self.set_period(self._period_min)
        
        if self._presence_mwsrc2:
            self._microwave_generator1.set_freqsweep('off')
            self._microwave_generator2.set_freqsweep('on')
            self._microwave_generator2.set_sweepmode('STEP')
            self._microwave_generator2.set_spacingfreq('lin')
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            self._microwave_generator1.set_gui_update('ON')
            self._microwave_generator2.set_gui_update('ON')
        else:
            self._microwave_generator1.set_freqsweep('on')
            self._microwave_generator1.set_sweepmode('STEP')
            self._microwave_generator1.set_spacingfreq('lin')
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            self._microwave_generator1.set_gui_update('ON')
        self._redpitaya.reset_LUT()
        


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
        
    def do_set_ro_pulse_delay_trigger(self,delay): 
        '''
            Set the delay between the trigger and the begining of the signal. 
            Input :
                delay(float): delay in second 
        '''
        self._ro_pulse_delay_trigger = delay
        
    def do_get_ro_pulse_delay_trigger(self): 
        '''
            Get the delay between the trigger and the begining of the signal. 
            Output :
                delay(float): delay in second 
        '''
        return self._ro_pulse_delay_trigger
        
    def do_set_ro_pulse_delay_IQ(self,delay): 
        '''
            Get the delay between the begining of the DAC signal and the IQ signal.
            Used to compensate the propagation time in the fridge 
            Input :
                delay(float): delay in second 
        '''
        self._ro_pulse_delay_IQ = delay
        
    def do_get_ro_pulse_delay_IQ(self): 
        '''
            Get the delay between the begining of the DAC signal and the IQ signal.
            Used to compensate the propagation time in the fridge 
            Output :
                delay(float): delay in second 
        '''
        return self._ro_pulse_delay_IQ
        
    def do_set_period(self,period): 
        '''
            Set the period of the signal generated by the Redpitaya
            Input :
                period(float): period in second 
        '''
        self._period = period
        self._redpitaya.set_period(period)
        
    def do_get_period(self): 
        '''
            Get the period of the signal generated by the Redpitaya
            Input :
                period(float): period in second 
        '''
        return self._period

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
        elif channel == 2: 
            f_ex = frequency_start - self.get_ro_pulse_frequency()*1e-9*self._SSB_tone1.get_band_type()
            print f_ex 
            if frequency_start > self._SSB_tone2.get_freq_stop() or frequency_start < self._SSB_tone2.get_freq_start():
                print 'Carefull! You are over the range of the SSB2'
            self._microwave_generator2.set_startfreq(f_ex)
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
        elif channel == 2: 
            f_ex = frequency_stop - self.get_ro_pulse_frequency()*1e-9*self._SSB_tone1.get_band_type()
            print f_ex 
            if frequency_stop > self._SSB_tone2.get_freq_stop() or frequency_stop < self._SSB_tone2.get_freq_start():
                print 'Careful! You are over the range of the SSB2'
            self._microwave_generator2.set_stopfreq(f_ex)
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
        elif channel == 2: 
            self._microwave_generator2.set_pointsfreq(frequency_points)
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

        elif channel == 2:
            f_ex = cwf - self._SSB_tone2.get_band_type()*self.get_ro_pulse_frequency()*1e-9 
            if cwf > self._SSB_tone2.get_freq_stop() or cwf < self._SSB_tone2.get_freq_start():
                print 'Careful! You are over the range of the SSB2'
            self._microwave_generator2.set_frequency(f_ex)
            
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
    
        # self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(freq_ro)
        self._microwave_generator1.set_power(power_mw)
        
        self._redpitaya.reset_LUT(self._ro_pulse_duration)
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

    # def one_tone(self,freq_vec, power_mw, channel):
        # # Setting the mw1 on the sweeping mode

        # # self._microwave_generator1.set_gui_update('OFF')
        # # self._microwave_generator1.set_freqsweep('on')
        # # self._microwave_generator1.set_sweepmode('STEP')
        # # self._microwave_generator1.set_spacingfreq('lin')
        
        # # self._microwave_generator2.set_gui_update('OFF')
        # self._microwave_generator2.set_freqsweep('on')
        # self._microwave_generator2.set_sweepmode('STEP')
        # self._microwave_generator2.set_spacingfreq('lin')

        # # if self._presence_mwsrc2:
            # # self._microwave_generator2.set_freqsweep('off')
            
        # # if self._presence_mwsrc1:
            # # self._microwave_generator1.set_freqsweep('off')

        # # Setting the sweep parameters to mw1
        # # if channel == 'CH1': 
        # # self.set_src1_frequency_start(freq_vec[0])
        # # self.set_src1_frequency_stop(freq_vec[-1])
        # # self.set_src1_frequency_points(len(freq_vec))
        # # self._microwave_generator1.restartsweep()
        # # elif channel == 'CH2':
        # self.set_src2_frequency_start(freq_vec[0])
        # self.set_src2_frequency_stop(freq_vec[-1])
        # self.set_src2_frequency_points(len(freq_vec))
        # self._microwave_generator2.restartsweep()
        # # else :
            # # raise ValueError('Wrong channel name for the microwave source in one_tone')
        
        # # self._microwave_generator1.set_power(power_mw)
        # self._microwave_generator2.set_power(power_mw)

        # self._redpitaya.reset_LUT()
        
        # table_cos_ro = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                # self._ro_pulse_duration, self._ro_pulse_delay_trigger+self._ro_pulse_delay_IQ])
        # table_sin_ro = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                # self._ro_pulse_duration, self._ro_pulse_delay_trigger+self._ro_pulse_delay_IQ])
                                                            
        # table_ex = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                            # self._ro_pulse_duration, self._ro_pulse_delay_trigger])

        
        # self._redpitaya.send_DAC_LUT(table_ex, channel, trigger=channel)
        # self._redpitaya.send_IQ_LUT(table_cos_ro, channel, quadrature='I')
        # self._redpitaya.send_IQ_LUT(table_sin_ro, channel, quadrature='Q')
        # # data = self._redpitaya.get_data(mode='IQINT', nb_measure=len(freq_vec))
        # data = self._redpitaya.get_data_int_fix(mode='IQINT', nb_measure=len(freq_vec))

        # nb_points = (self._ro_pulse_duration)/8.e-9

        # if channel == 'CH1':
            # ICH1 = data[0] / (4*nb_points*8192)
            # QCH1 = data[1] / (4*nb_points*8192)
            # return np.array([ICH1, QCH1])
        # elif channel == 'CH2':
            # ICH2 = data[2::4] / 4 / nb_points / 8192.
            # QCH2 = data[3::4] / 4 / nb_points / 8192.
            # return np.array([ICH2, QCH2])
        # else:
            # raise ValueError('Wrong channel name in the one_tone sequence')
            
    def one_tone(self,freq_vec, power_mw, channel): 
    
        self._microwave_generator2.set_gui_update('off')

        self._microwave_generator2.set_freqsweep('off')
        self._microwave_generator2.set_power(power_mw)
        
        table_cos_ro = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                self._ro_pulse_duration, self._ro_pulse_delay_trigger+self._ro_pulse_delay_IQ])
        table_sin_ro = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                self._ro_pulse_duration, self._ro_pulse_delay_trigger+self._ro_pulse_delay_IQ])
                                                            
        table_ex = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                            self._ro_pulse_duration, self._ro_pulse_delay_trigger])


        time_step = self._ro_pulse_duration + self._ro_pulse_delay_trigger + self._ro_pulse_delay_IQ
        period = max(self._period_min, time_step)
        print period
        self.set_period(period)
        
        self._redpitaya.reset_LUT()
        self._redpitaya.send_DAC_LUT(table_ex, channel, trigger=channel)
        self._redpitaya.send_IQ_LUT(table_cos_ro, 'CH1', quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_ro, 'CH1', quadrature='Q')
        self._redpitaya.send_IQ_LUT(table_cos_ro, 'CH2', quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_ro, 'CH2', quadrature='Q')
        
        self._redpitaya.set_stop_DAC(self._ro_pulse_duration)
        self._redpitaya.set_start_ADC(0)
        self._redpitaya.set_stop_ADC(self._ro_pulse_duration + self._ro_pulse_delay_trigger +
                                        self._ro_pulse_delay_IQ)

        nb_measure = int(self._time_loop/self.get_period())
        I1 = np.zeros(len(freq_vec))
        Q1 = np.zeros(len(freq_vec))
        I2 = np.zeros(len(freq_vec))
        Q2 = np.zeros(len(freq_vec))
        
        for k in xrange(len(freq_vec)): 
            print k , nb_measure

            self.set_src2_cw_frequency(freq_vec[k])
            data = self._redpitaya.get_data_filter(mode='IQINT', nb_measure=8000)
            I1[k] = np.mean(data[0])/((self._ro_pulse_duration/8e-9)*8192)
            Q1[k] = np.mean(data[1])/((self._ro_pulse_duration/8e-9)*8192)
            I2[k] = np.mean(data[2])/((self._ro_pulse_duration/8e-9)*8192)
            Q2[k] = np.mean(data[3])/((self._ro_pulse_duration/8e-9)*8192)
            
        return np.array([I1, Q1, I2, Q2])

    def two_tones(self,freq_vec,cw_freq, power_cw, power_mw_ex, t_ex = 1e-6, channel_cw = 'CH1'):

        self._microwave_generator1.set_gui_update('OFF')
        # self._microwave_generator2.set_gui_update('OFF')

        self._microwave_generator2.set_freqsweep('off')
        self.set_src2_cw_frequency(cw_freq)
        self._microwave_generator2.set_power(power_cw)

        self._microwave_generator1.set_freqsweep('on')
        self._microwave_generator1.set_sweepmode('STEP')
        self._microwave_generator1.set_spacingfreq('lin')
        
        self.set_src1_frequency_start(freq_vec[0])
        self.set_src1_frequency_stop(freq_vec[-1])
        self.set_src1_frequency_points(len(freq_vec))
        self._microwave_generator1.restartsweep()
        self._microwave_generator1.set_power(power_mw_ex)

        table_sin_ro = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                       self._ro_pulse_duration, t_ex + self._ro_pulse_delay_trigger 
                                                    ])
                                                       
        table_sin_IQ = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                       self._ro_pulse_duration, t_ex + self._ro_pulse_delay_trigger 
                                                       + self._ro_pulse_delay_IQ])
        table_cos_IQ = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                        self._ro_pulse_duration, t_ex + self._ro_pulse_delay_trigger 
                                                        + self._ro_pulse_delay_IQ])
                                                        
        table_sin_ex = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                       t_ex,self._ro_pulse_delay_trigger])


        self._redpitaya.reset_LUT()
        self._redpitaya.send_DAC_LUT(table_sin_ro, channel_cw, trigger=channel_cw)
        # if channel_cw == 'CH1':
            # self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH2',trigger = 'CH2')
        # elif channel_cw == 'CH2':
            # self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH1', trigger='CH1')
        # else:
            # raise ValueError('Problem with the channel choice in twotone, it should be CH1 or CH2')

        self._redpitaya.send_IQ_LUT(table_cos_IQ, channel_cw, quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_IQ, channel_cw, quadrature='Q')

        data = self._redpitaya.get_data_int_fix(mode='IQINT', nb_measure=len(freq_vec))

        nb_points = (self._ro_pulse_duration)/8e-9

        # if channel_cw == 'CH1':
        # ICH1 = data[0] / nb_points
        # QCH1 = data[1] / nb_points 
        
        ICH1 = data[0]/(4*nb_points*8192)
        QCH1 = data[1]/(4*nb_points*8192)
        return np.array([ICH1, QCH1])
        # elif channel_cw == 'CH2':
            # ICH2 = data[2::4] / 4 / nb_points / 8192.
            # QCH2 = data[3::4] / 4 / nb_points / 8192.
            # return np.array([ICH2, QCH2])
        # else:
            # raise ValueError('Wrong channel name in the two_tone sequence')
            
    def two_tones_2(self,freq_vec,cw_freq, power_cw, power_mw_ex, t_ex = 1e-6,amp_ex = 0.5, channel_cw = 'CH1'):
    
        self._microwave_generator1.set_gui_update('on')
        self._microwave_generator2.set_gui_update('on')

        self._microwave_generator2.set_freqsweep('off')
        self.set_src2_cw_frequency(cw_freq)
        self._microwave_generator2.set_power(power_cw)
        
        self._microwave_generator1.set_power(power_mw_ex)
        self._microwave_generator1.set_freqsweep('off')
        
        table_sin_ro = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                       self._ro_pulse_duration, t_ex + self._ro_pulse_delay_trigger 
                                                    ])
                                                       
        table_sin_IQ = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                       self._ro_pulse_duration, t_ex + self._ro_pulse_delay_trigger 
                                                       + self._ro_pulse_delay_IQ])
        table_cos_IQ = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                        self._ro_pulse_duration, t_ex + self._ro_pulse_delay_trigger 
                                                        + self._ro_pulse_delay_IQ])
                                                        
        table_sin_ex = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, amp_ex,
                                                       t_ex,self._ro_pulse_delay_trigger])
        
        
        
        time_step = t_ex + self._ro_pulse_duration + self._ro_pulse_delay_trigger + self._ro_pulse_delay_IQ
        period = max(self._period_min, time_step)
        self.set_period(period)
        
        self._redpitaya.reset_LUT()
        self._redpitaya.send_DAC_LUT(table_sin_ro, channel_cw, trigger=channel_cw)
        if t_ex != 0: 
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH2',trigger = 'CH2')
            
        self._redpitaya.send_IQ_LUT(table_cos_IQ, channel_cw, quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_IQ, channel_cw, quadrature='Q')
        
        nb_measure = int(self._time_loop/self.get_period())
        I = np.zeros(len(freq_vec))
        Q = np.zeros(len(freq_vec))
        
        for k in xrange(len(freq_vec)): 
            print k 
            if t_ex == 0:
                self.set_src1_cw_frequency(freq_vec[k] + self._SSB_tone1.get_band_type()*self.get_ro_pulse_frequency()*1e-9)
            else: 
                self.set_src1_cw_frequency(freq_vec[k])
                
            data = self._redpitaya.get_data_int_fix(mode='IQINT', nb_measure= nb_measure, memory_pb = False)
            I[k] = np.mean(data[0])/(4*self._ro_pulse_duration*8192)
            Q[k] = np.mean(data[1])/(4*self._ro_pulse_duration*8192)
            
        return np.array([I, Q])


    def relaxation(self, freq_ex, freq_ro, power_ex, power_ro, t_wait, t_ex, channel_ro = 'CH1', average = 100):

        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator2.set_gui_update('OFF')

        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(freq_ro)
        self._microwave_generator1.set_power(power_ro)
        
        self._microwave_generator2.set_freqsweep('off')
        self.set_src2_cw_frequency(freq_ex)
        self._microwave_generator2.set_power(power_ex)

        """           !!!!!!!!!!!!!!!!!!!!!              TO BE CHECKED          !!!!!!!!!!!!!!!!!                   """
        # self._microwave_generator2.set_power(self._SSB_tone2.get_LO_power())

        table_sin_ro = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                        self._ro_pulse_duration, t_wait + t_ex + self._ro_pulse_delay_trigger
                                                        + self._ro_pulse_delay_IQ])
        table_cos_ro = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                        self._ro_pulse_duration, t_wait + t_ex + self._ro_pulse_delay_trigger
                                                        + self._ro_pulse_delay_IQ])
        table_sin_ex = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                        t_ex, self._ro_pulse_delay_trigger])

        self._redpitaya.reset_LUT()
        self._redpitaya.send_DAC_LUT(table_sin_ro, channel_ro, trigger=channel_ro)
        if channel_ro == 'CH1':
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH2', trigger='CH2')
        elif channel_ro == 'CH2':
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH1', trigger='CH1')
        else:
            raise ValueError('Problem with the channel choice in twotone, it should be CH1 or CH2')

        self._redpitaya.send_IQ_LUT(table_cos_ro, channel_ro, quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_ro, channel_ro, quadrature='Q')

        data = self._redpitaya.get_data(mode='IQINT', nb_measure=average)

        nb_points = (self._ro_pulse_duration) / 8e-9

        if channel_ro == 'CH1':
            ICH1 = data[::4] / 4 / nb_points / 8192.
            QCH1 = data[1::4] / 4 / nb_points / 8192.
            return np.array([np.mean(ICH1), np.mean(QCH1)])
        elif channel_ro == 'CH2':
            ICH2 = data[2::4] / 4 / nb_points / 8192.
            QCH2 = data[3::4] / 4 / nb_points / 8192.
            return np.array([np.mean(ICH2), np.mean(QCH2)])
        else:
            raise ValueError('Wrong channel name in the rabi sequence')

    def rabi(self,freq_ex,freq_ro, power_ex, power_ro, t_ex,amp_ex, channel_ro = 'CH1', average = None):

        self._microwave_generator1.set_gui_update('on')
        self._microwave_generator2.set_gui_update('on')

        self._microwave_generator2.set_freqsweep('off')
        self.set_src2_cw_frequency(freq_ro)
        self._microwave_generator2.set_power(power_ro)
        
        self._microwave_generator1.set_power(power_ex)
        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(freq_ex)
        
        self.set_ro_pulse_duration(1e-6)
        
        if self.get_ro_pulse_duration()+t_ex > 8e-6: 
            print 'The LUT is full'
        
        table_sin_ro = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                       self._ro_pulse_duration, t_ex + self._ro_pulse_delay_trigger 
                                                    ])
                                                       
        table_sin_IQ = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                       self._ro_pulse_duration, t_ex + self._ro_pulse_delay_trigger 
                                                       + self._ro_pulse_delay_IQ])
        table_cos_IQ = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                        self._ro_pulse_duration, t_ex + self._ro_pulse_delay_trigger 
                                                        + self._ro_pulse_delay_IQ])
                                                        
        table_sin_ex = self._redpitaya.fill_LUT('SIN',[self._ro_pulse_frequency, amp_ex,
                                                       t_ex,self._ro_pulse_delay_trigger])
                                                       
        
        
        time_step = t_ex + self._ro_pulse_duration + self._ro_pulse_delay_trigger + self._ro_pulse_delay_IQ
        period = max(self._period_min, time_step)
        self.set_period(period)

        self._redpitaya.reset_LUT()
        self._redpitaya.send_DAC_LUT(table_sin_ro, channel_ro, trigger=channel_ro)
        self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH2',trigger = 'CH2')
            
        self._redpitaya.send_IQ_LUT(table_cos_IQ, channel_ro, quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_IQ, channel_ro, quadrature='Q')
        
        if average == None:
            nb_measure = int(self._time_loop/self.get_period())
        else: 
            nb_measure = average
            
        data = self._redpitaya.get_data_int_fix(mode='IQINT', nb_measure= nb_measure, memory_pb = False)
        
        I = np.mean(data[0])/(4*self._ro_pulse_duration*8192)
        Q = np.mean(data[1])/(4*self._ro_pulse_duration*8192)
        return np.array([I]),np.array([Q]) 
        

    def ramsey(self,freq_ex,freq_ro, power_ex, power_ro, t_wait, t_ex = 1e-6, channel_ro = 'CH1', average = 100):

        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator2.set_gui_update('OFF')

        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(freq_ro)
        self._microwave_generator1.set_power(power_ro)
        
        self._microwave_generator2.set_freqsweep('off')
        self.set_src2_cw_frequency(freq_ex)
        self._microwave_generator2.set_power(power_ex)

        """           !!!!!!!!!!!!!!!!!!!!!              TO BE CHECKED          !!!!!!!!!!!!!!!!!                   """
        # self._microwave_generator2.set_power(self._SSB_tone2.get_LO_power())

        table_sin_ro = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                        self._ro_pulse_duration, 2*t_ex + t_wait 
                                                        + self._ro_pulse_delay_trigger+ self._ro_pulse_delay_IQ])

        table_cos_ro = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                        self._ro_pulse_duration, 2*t_ex + t_wait 
                                                        +  self._ro_pulse_delay_trigger + self._ro_pulse_delay_IQ])
                                                        
        table_sin_ex = self._redpitaya.fill_LUT('RAMSEY', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                        t_ex, self._ro_pulse_delay_trigger, t_wait])

        self._redpitaya.reset_LUT()
        self._redpitaya.send_DAC_LUT(table_sin_ro, channel_ro, trigger=channel_ro)
        if channel_ro == 'CH1':
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH2', trigger='CH2')
        elif channel_ro == 'CH2':
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH1', trigger='CH1')
        else:
            raise ValueError('Problem with the channel choice in twotone, it should be CH1 or CH2')

        self._redpitaya.send_IQ_LUT(table_cos_ro, channel_ro, quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_ro, channel_ro, quadrature='Q')

        data = self._redpitaya.get_data(mode='IQINT', nb_measure=average)

        nb_points = (self._ro_pulse_duration + self._ro_pulse_delay + 2*t_ex + t_wait) / 8e-9

        if channel_ro == 'CH1':
            ICH1 = data[::4] / 4 / nb_points / 8192.
            QCH1 = data[1::4] / 4 / nb_points / 8192.
            return np.array([np.mean(ICH1), np.mean(QCH1)])
        elif channel_ro == 'CH2':
            ICH2 = data[2::4] / 4 / nb_points / 8192.
            QCH2 = data[3::4] / 4 / nb_points / 8192.
            return np.array([ICH2, QCH2])
        else:
            raise ValueError('Wrong channel name in the ramsey sequence')

    def echo(self, freq_ex, freq_ro, power_ex, power_ro, t_wait, t_ex=1e-6, channel_ro='CH1', average=100):

        self._microwave_generator1.set_gui_update('OFF')
        self._microwave_generator2.set_gui_update('OFF')

        self._microwave_generator1.set_freqsweep('off')
        self.set_src1_cw_frequency(freq_ro)
        self._microwave_generator1.set_power(power_ro)
        
        self._microwave_generator2.set_freqsweep('off')
        self.set_src2_cw_frequency(freq_ex)
        self._microwave_generator2.set_power(power_ex)

        """           !!!!!!!!!!!!!!!!!!!!!              TO BE CHECKED          !!!!!!!!!!!!!!!!!                   """
        # self._microwave_generator2.set_power(self._SSB_tone2.get_LO_power())

        table_sin_ro = self._redpitaya.fill_LUT('SIN', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                        self._ro_pulse_duration, 4 * t_ex + 2*t_wait +
                                                        self._ro_pulse_delay_trigger + self._ro_pulse_delay_IQ])
        table_cos_ro = self._redpitaya.fill_LUT('COS', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                        self._ro_pulse_duration, 4 * t_ex + 2*t_wait +
                                                        self._ro_pulse_delay_trigger + self._ro_pulse_delay_IQ])
        table_sin_ex = self._redpitaya.fill_LUT('RAMSEY', [self._ro_pulse_frequency, self._ro_pulse_amplitude,
                                                           t_ex, self._ro_pulse_delay_trigger, t_wait])

        self._redpitaya.reset_LUT()
        self._redpitaya.send_DAC_LUT(table_sin_ro, channel_ro, trigger=channel_ro)
        if channel_ro == 'CH1':
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH2', trigger='CH2')
        elif channel_ro == 'CH2':
            self._redpitaya.send_DAC_LUT(table_sin_ex, 'CH1', trigger='CH1')
        else:
            raise ValueError('Problem with the channel choice in twotone, it should be CH1 or CH2')

        self._redpitaya.send_IQ_LUT(table_cos_ro, channel_ro, quadrature='I')
        self._redpitaya.send_IQ_LUT(table_sin_ro, channel_ro, quadrature='Q')

        data = self._redpitaya.get_data(mode='IQINT', nb_measure=average)

        nb_points = (self._ro_pulse_duration + self._ro_pulse_delay + 4*t_ex + 2*t_wait) / 8e-9

        if channel_ro == 'CH1':
            ICH1 = data[::4] / 4 / nb_points / 8192.
            QCH1 = data[1::4] / 4 / nb_points / 8192.
            return np.array([ICH1, QCH1])
        elif channel_ro == 'CH2':
            ICH2 = data[2::4] / 4 / nb_points / 8192.
            QCH2 = data[3::4] / 4 / nb_points / 8192.
            return np.array([ICH2, QCH2])
        else:
            raise ValueError('Wrong channel name in the echo sequence')

    def rabi_sequence(self,freq_ex,freq_ro, power_ex, power_ro, t_ex_vec,amp_ex, channel_ro = 'CH1', average = None):

        I_vec = np.array([])
        Q_vec = np.array([])
        for k in xrange(len(t_ex_vec)):
            I,Q = self.rabi(freq_ex,freq_ro, power_ex, power_ro, t_ex_vec[k],amp_ex, channel_ro, average)
            I_vec = np.concatenate((I_vec, I))
            Q_vec = np.concatenate((Q_vec, Q))
        return I_vec,Q_vec

    def ramsey_sequence(self,freq_ex,freq_ro, power_ex, power_ro, t_wait_vec, t_ex, channel_ro = 'CH1', average = 100):

        I_vec = np.array([])
        Q_vec = np.array([])
        for k in xrange(len(t_wait_vec)):
            I, Q = self.ramsey(self,freq_ex,freq_ro, power_ex, power_ro, t_wait_vec[k], t_ex, channel_ro, average)
            I_vec = np.concatenate((I_vec, np.mean(I)))
            Q_vec = np.concatenate((Q_vec, np.mean(Q)))
        return I_vec, Q_vec

    def echo_sequence(self, freq_ex, freq_ro, power_ex, power_ro, t_wait_vec, t_ex, channel_ro='CH1', average=100):
        I_vec = np.array([])
        Q_vec = np.array([])
        for k in xrange(len(t_wait_vec)):
            I, Q = self.echo(self, freq_ex, freq_ro, power_ex, power_ro, t_wait_vec[k], t_ex, channel_ro, average)
            I_vec = np.concatenate((I_vec, np.mean(I)))
            Q_vec = np.concatenate((Q_vec, np.mean(Q)))
        return I_vec, Q_vec

    def average_one_tone(self, freq_vec, power_mw, channel, average):
            I1_avg = []
            Q1_avg = []
            I2_avg = []
            Q2_avg = []
            for k in xrange(average):
                data = self.one_tone(freq_vec, power_mw, channel)
                I1_avg.append(data[0])
                Q1_avg.append(data[1])
                I2_avg.append(data[2])
                Q2_avg.append(data[3])
                
            I1_avg = np.mean(np.array([I1_avg]), axis=0)
            Q1_avg = np.mean(np.array([Q1_avg]), axis=0)
            I2_avg = np.mean(np.array([I1_avg]), axis=0)
            Q2_avg = np.mean(np.array([Q1_avg]), axis=0)
            return np.mean(I1_avg, axis=0), np.mean(Q1_avg, axis=0), np.mean(I2_avg, axis=0), np.mean(Q2_avg, axis=0)

    def average_two_tones(self,freq_vec,cw_freq, power_cw, power_mw_ex, t_ex = 1e-6, channel_cw = 'CH1',average = 100):

        I_avg = []
        Q_avg = []
        for k in xrange(average):
            data = self.two_tones(freq_vec,cw_freq, power_cw, power_mw_ex, t_ex, channel_cw)
            I_avg.append(data[0])
            Q_avg.append(data[1])
        I_avg = np.mean(np.array([I_avg]), axis=0)
        Q_avg = np.mean(np.array([Q_avg]), axis=0)
        return np.mean(I_avg, axis=0), np.mean(Q_avg, axis=0)
        
        
        
    def average_two_tones_2(self,freq_vec,cw_freq, power_cw, power_mw_ex, t_ex = 1e-6,amp_ex = 0.5, channel_cw = 'CH1',average = 100):

        I_avg = []
        Q_avg = []
        for k in xrange(average):
            print k 
            data = self.two_tones_2(freq_vec,cw_freq, power_cw, power_mw_ex, t_ex, amp_ex, channel_cw)
            I_avg.append(data[0])
            Q_avg.append(data[1])
        I_avg = np.mean(np.array([I_avg]), axis=0)
        Q_avg = np.mean(np.array([Q_avg]), axis=0)
        return np.mean(I_avg, axis=0), np.mean(Q_avg, axis=0)

    def average_relaxation(self, freq_ex, freq_ro, power_ex, power_ro, t_wait, t_ex, channel_ro = 'CH1', average = 100):

        I_avg = []
        Q_avg = []
        for k in xrange(average):
            data = self.relaxation(freq_ex, freq_ro, power_ex, power_ro, t_wait, t_ex, channel_ro)
            I_avg.append(data[0])
            Q_avg.append(data[1])
        I_avg = np.mean(np.array([I_avg]), axis=0)
        Q_avg = np.mean(np.array([Q_avg]), axis=0)
        return np.mean(I_avg, axis=0), np.mean(Q_avg, axis=0)

    def average_rabi(self,freq_ex,freq_ro, power_ex, power_ro, t_ex_vec,amp_ex, channel_ro = 'CH1', average_point = None, average_tot = 10):

        I_avg = []
        Q_avg = []
        for k in xrange(average_tot): 
            print k
            data = self.rabi_sequence(freq_ex,freq_ro, power_ex, power_ro, t_ex_vec,amp_ex, channel_ro, average_point)
            I_avg.append(data[0])
            Q_avg.append(data[1])
        I_avg = np.mean(np.array([I_avg]), axis=0)
        Q_avg = np.mean(np.array([Q_avg]), axis=0)
        return np.mean(I_avg, axis=0), np.mean(Q_avg, axis=0)

    def average_ramsey(self,freq_ex,freq_ro, power_ex, power_ro, t_wait_vec, t_ex, channel_ro = 'CH1', average = 100):

        I_avg = []
        Q_avg = []
        for k in xrange(average):
            data = self.ramsey_sequence(self,freq_ex,freq_ro, power_ex, power_ro, t_wait_vec, t_ex, channel_ro)
            I_avg.append(data[0])
            Q_avg.append(data[1])
        I_avg = np.mean(np.array([I_avg]), axis=0)
        Q_avg = np.mean(np.array([Q_avg]), axis=0)
        return np.mean(I_avg, axis=0), np.mean(Q_avg, axis=0)

    def average_echo(self, freq_ex, freq_ro, power_ex, power_ro, t_wait_vec, t_ex, channel_ro='CH1', average=100):

        I_avg = []
        Q_avg = []
        for k in xrange(average):
            data = self.echo_sequence(self, freq_ex, freq_ro, power_ex, power_ro, t_wait_vec, t_ex, channel_ro)
            I_avg.append(data[0])
            Q_avg.append(data[1])
        I_avg = np.mean(np.array([I_avg]), axis=0)
        Q_avg = np.mean(np.array([Q_avg]), axis=0)
        return np.mean(I_avg, axis=0), np.mean(Q_avg, axis=0)