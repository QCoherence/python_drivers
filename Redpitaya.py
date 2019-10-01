# -*- coding: utf-8 -*-
# redpitaya.py is a driver for the Redpitaya card SCPI IQ server 
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

import visa
from instrument import Instrument
import qt
import logging
import types
import numpy as np
import time 

'''
TO DO : - add more function is fill_LO_table
        - add the pulse parameters in the set file
'''

class Redpitaya(Instrument): 

    def __init__(self, name, address):
    
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])
        rm = visa.ResourceManager()
        
        self._address = address
        try : 
            self._visainstrument = rm.open_resource(self._address, read_termination = '\r\n')
        except: 
            raise SystemExit
            
        self.add_parameter('freq_filter',
                            flags   = Instrument.FLAG_SET,
                            units   = 'Hz',
                            minval  = 10e3,
                            maxval  = 62.5e6,
                            type    = types.FloatType)
                            
        self.add_parameter('decimation_filter',
                            flags   = Instrument.FLAG_SET,
                            minval  = 0,
                            maxval  = 65535,
                            type    = types.IntType)
                            
        self.add_parameter('start_ADC',
                            flags   = Instrument.FLAG_SET,
                            minval  = 0,
                            maxval  = 8192*8e-9,
                            type    = types.FloatType)
                            
        self.add_parameter('stop_ADC',
                            flags   = Instrument.FLAG_SET,
                            minval  = 0,
                            maxval  = 8192*8e-9,
                            type    = types.FloatType)
                            
        self.add_parameter('stop_DAC',
                            flags   = Instrument.FLAG_SET,
                            minval  = 0,
                            maxval  = 8192*8e-9,
                            type    = types.FloatType)
                            
        self.add_parameter('period',
                    flags   = Instrument.FLAG_SET,
                    minval  = 0,
                    maxval  = 125000000*8e-9,
                    type    = types.FloatType)
                                                                                                        
        self.add_parameter('mode_output',
                            flags   = Instrument.FLAG_SET,
                            option_list = ['ADC', 'IQCH1', 'IQCH2', 'IQLP1', 'IQINT'],
                            type    = types.StringType)
        
        self.add_parameter('format_output', 
                            flags = Instrument.FLAG_SET, 
                            option_list = ['ACSII','BIN'], 
                            type = types.StringType)
        
        
        
        self.add_function('start')
        self.add_function('stop')
        self.add_function('data_size')
        self.add_function('data_output')
        
    # ----------------------------------------------------- Methods -------------------------------------------------- #
        

    def start(self): 
        logging.info(__name__ + ' Play the LO table \n')
        self._visainstrument.write('START')
        
    def stop(self): 
        logging.info(__name__ + ' Stop the LO table \n')
        self._visainstrument.write('STOP')
    
    def data_size(self): 
        logging.info(__name__ + ' Ask for the data size \n')
        self._visainstrument.query('OUTPUT:DATASIZE?')
    
    def data_output(self):
        data = np.array([], dtype = 'int32')   
        logging.info(__name__ + ' Ask for the output data \n')
        data = self._visainstrument.query('OUTPUT:DATA?')
        # self._visainstrument.write('OUTPUT:DATA?')
        # print(self._visainstrument.read_bytes(1))
        
        # data = self._visainstrument.query_binary_values('OUTPUT:DATA?' )
        # data = self._visainstrument.query_ascii_values('OUTPUT:DATA?' )
        return data
        
    def do_set_freq_filter(self,freq_filter_value): 
        logging.info(__name__+ ' Set the frequency of the filter at %s Hertz \n' %freq_filter_value)
        self._visainstrument.write('FILTER:FREQ ' + str(freq_filter_value))
        
    def do_set_decimation_filter(self,decimation_filter_value):
        logging.info(__name__+ ' Set the decimation filter at %s second \n' %decimation_filter_value)
        self._visainstrument.write('FILTER:DEC ' + str(decimation_filter_value))
        
    def do_set_start_ADC(self,start_ADC_value): 
        logging.info(__name__+ ' Set the starting point of the aquisition %s second \n' %start_ADC_value)
        self._visainstrument.write('ADC:STARTPOS ' + str(int(start_ADC_value/8e-9)))
        
    def do_set_stop_ADC(self,stop_ADC_value): 
        logging.info(__name__+ ' Set the stopping point of the aquisition at %s second \n' %stop_ADC_value)
        self._visainstrument.write('ADC:STOPPOS ' + str(int(stop_ADC_value/8e-9)))
        
    def do_set_stop_DAC(self,stop_DAC_value): 
        logging.info(__name__+ ' Set the stopping point of the LO table at %s second \n' %stop_DAC_value)
        self._visainstrument.write('DAC:STOPPOS ' + str(int(stop_DAC_value/8e-9)))

                
    def do_set_period(self,period_value): 
        logging.info(__name__+ ' Set the period at %s second \n' %period_value)
        self._visainstrument.write('PERIOD ' + str(int(period_value/8e-9)))
        
    def do_set_mode_output(self,mode): 
        logging.info(__name__+ ' Select the Output mode %s \n' %mode)
        self._visainstrument.write('OUTPUT:SELECT ' + mode)
        
    def do_set_format_output(self, format): 
        logging.info(__name__ + ' Set the output format %s \n' %format)
        self._visainstrument.write('OUTPUT:FORMAT ' + format)
    
    def fill_LUT(self, function, parameters): 
        # logging.debug(__name__ + 'Fill the LUT with : frequency = %f, pulse duration = %f, amplitude = %f' %(parameters[0], parameters[1], parameters[2]))
        
        if function == 'SIN': 
            freq, Amplitude, pulse_duration, delay = parameters
            if freq > 1./8e-9 or Amplitude > 1 or pulse_duration + delay >  8e-9*8192: 
                raise ValueError('One of the parameters is not correct in the sin LUT')
            else: 
                N_point = int(pulse_duration/8e-9)
                n_oscillation = int(freq*pulse_duration)
                Amp_bit = Amplitude*8192
                t = np.linspace(0,2*np.pi,N_point)
                return Amp_bit*np.concatenate((np.zeros(int(delay/8e-9)), np.sin(n_oscillation*t)))
                
        elif function == 'COS': 
            freq, Amplitude, pulse_duration, delay = parameters
            if freq > 1./8e-9 or Amplitude > 1 or pulse_duration + delay > 8e-9*8192: 
                raise ValueError('One of the parameters is not correct in the cos LUT')
            else: 
                N_point = int(pulse_duration/8e-9)
                n_oscillation = int(freq*pulse_duration)
                Amp_bit = Amplitude*8192
                t = np.linspace(0,2*np.pi,N_point)
                return Amp_bit*np.concatenate((np.zeros(int(delay/8e-9)), np.cos(n_oscillation*t)))

        elif function == 'RAMSEY':

            freq, Amplitude, pulse_duration, delay, t_wait = parameters
            if freq > 1. / 8e-9 or Amplitude > 1 or 2*pulse_duration + delay + t_wait > 8e-9 * 8192:
                raise ValueError('One of the parameters is not correct is the Ramsey LUT')
            else :
                N_point = int(pulse_duration/8e-9)
                n_oscillation = int(freq * pulse_duration)
                Amp_bit = Amplitude * 8192
                t = np.linspace(0, 2 * np.pi, N_point)
                wait_vec = np.zeros(int(t_wait/8e-9))
                delay_vec = np.zeros(int(delay/8e-9))
                excitation_vec = np.sin(n_oscillation*t)
                return Amp_bit*np.concatenate((delay_vec,excitation_vec,wait_vec,excitation_vec))


        elif function == 'ECHO':
            freq, Amplitude, pulse_pi_2, delay, t_wait = parameters
            if freq > 1. / 8e-9 or Amplitude > 1 or 4*pulse_pi_2 + delay + 2*t_wait > 8e-9 * 8192:
                raise ValueError('One of the parameters is not correct is the Echo LUT')
            else:
                N_point_pi_2 = int(pulse_pi_2/8e-9)
                N_point_pi = int(2*pulse_pi_2 / 8e-9)

                n_oscillation_pi_2 = int(freq * pulse_pi_2)
                n_oscillation_pi = 2*n_oscillation_pi_2

                t_pi_2 = np.linspace(0, 2 * np.pi, N_point_pi_2)
                t_pi = np.linspace(0, 2 * np.pi, N_point_pi)


                Amp_bit = Amplitude * 8192

                wait_vec = np.zeros(int(t_wait/8e-9))
                delay_vec = np.zeros(int(delay/8e-9))


                pi_2_vec = np.sin(n_oscillation_pi_2*t_pi_2)
                pi_vec = np.sin(n_oscillation_pi * t_pi)

                return Amp_bit*np.concatenate((delay_vec, pi_2_vec, wait_vec, pi_vec, wait_vec, pi_2_vec))
                
        elif function == 'STEP': 
            Amplitude, pulse_duration,t_slope,delay = parameters
            if Amplitude > 1 or pulse_duration + delay + 2*t_slope > 8e-9 * 8192: 
                raise ValueError('One of the parameters is not correct is the STEP LUT')
            
            Amp_bit = Amplitude*8192
            N_point = int(pulse_duration/8e-9)
            N_slope = int(t_slope/8e-9)
            N_delay = int(delay/8e-9)
            

            delay_vec = np.zeros(N_delay)
            slope_vec = np.linspace(0,1,N_slope)
            pulse_vec = np.ones(N_point)
            
            return Amp_bit*np.concatenate((delay_vec,slope_vec,pulse_vec,slope_vec[::-1]))
            
            
        
        
        else: 
            raise ValueError('This function is undefined')

        
    def reset_LUT(self,time = 8e-6): 
        logging.info(__name__+' Reset the DAC LUT \n')
        parameters = [0, 0, time,0]
        empty_table = self.fill_LUT('SIN',parameters)
        self.set_stop_DAC(time)
        self.send_DAC_LUT(empty_table,'CH1')
        self.send_DAC_LUT(empty_table,'CH2')
        self.send_IQ_LUT(empty_table,'CH1','I')
        self.send_IQ_LUT(empty_table,'CH1','Q')
        self.send_IQ_LUT(empty_table,'CH2','I')
        self.send_IQ_LUT(empty_table,'CH2','Q')

    def send_DAC_LUT(self, table,channel, trigger = 'NONE'): 
        logging.info(__name__+ ' Send the DAC LUT \n')
        if trigger == 'NONE': 
            table_bit = table.astype(int) * 4  
        elif trigger == 'CH1': 
            table_bit = table.astype(int) * 4 + 1
        elif trigger == 'CH2': 
            table_bit = table.astype(int) * 4 + 2
        elif trigger == 'BOTH': 
            table_bit = table.astype(int) * 4 + 3
        else: 
            raise ValueError('Wrong trigger value')     

        table_bit = table_bit.astype(str)
        separator = ', '
        table_bit = separator.join(table_bit)
        print table_bit
        if channel in ['CH1', 'CH2']: 
            self._visainstrument.write('DAC:' + channel + ' ' + table_bit)
        else: 
            raise ValueError('Wrong channel value')
                
    def send_IQ_LUT(self, table, channel, quadrature): 
        logging.info(__name__+ ' Send the IQ LOT \n')
        table_bit = table.astype(int) * 4 
        table_bit = table_bit.astype(str)
        separator = ', '
        table_bit = separator.join(table_bit)
        print table_bit.count(', ')
        if quadrature in ['I', 'Q'] and channel in ['CH1', 'CH2']:
            self._visainstrument.write(quadrature + ':' + channel + ' ' + table_bit)
        else: 
            raise ValueError('Wrong quadrature or channel')

    def get_data(self, mode, nb_measure):
        
        t = 0 
        self.set_mode_output(mode)
        self.start()
        signal = np.array([], dtype ='int32')
        while t < nb_measure:
            try:
                qt.msleep(0.1)
                rep = self.data_output()
                if rep[1] != '0' or len(rep)<=2:
                    print 'Memory problem %s' %rep[1]
                    self.stop()
                    self.start()
                else: 
                    # signal.append( rep[3:-1] + ',')
                    rep = eval( '[' + rep[3:-1] + ']' )
                    signal = np.concatenate((signal,rep))
                    tick = np.bitwise_and(rep,3) # extraction du debut de l'aquisition: LSB = 3
                    t += len(np.where(tick[1:] - tick[:-1])[0])+1 # idex of the tick   
                    
            except: 
                t=t
        self.stop()
        if t > nb_measure: 
            jump_tick = np.where(tick[1:] - tick[:-1])[0]
            len_data_block = jump_tick[1] - jump_tick[0]
            signal = signal[:nb_measure*len_data_block]
            
        if mode == ('ADC' or 'IQCH1' or 'IQCH2'):
            data_1 = signal[::2]/(4*8192.)
            data_2 = signal[1::2]/(4*8192.)
            return data_1, data_2
        else: 
            ICH1 = signal[::4]/(4*8192.)
            QCH1 = signal[1::4]/(4*8192.)
            ICH2 = signal[2::4]/(4*8192.)
            QCH2 = signal[3::4]/(4*8192.)
            return ICH1, QCH1, ICH2, QCH2
            
