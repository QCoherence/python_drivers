from instrument import Instrument
import instruments
import numpy
import types
import logging

class virtual_afg_burst_pulse(Instrument):
    '''
    This is the driver for the virtual instrument which can create a microwave pulse

    Usage:
    Initialize with
    <name> = qt.instruments.create('name', 'virtual_afg_burst_pulse', afg='name_afg', mwsrc='name_microwave_generator')
    '''
    
    def __init__(self, name, afg, mwsrc, live_update=True):
        '''
            Initialize the virtual instruments
                
                Input:
                    - name: Name of the virtual instruments
                    - afg: Name of the tektronix AFG3252
                    - mwsrc: Name given to the microwave_generator
                    - live_update (bool): The microwave pulse will be update at each setting or not
                    
                
                Output:
                    None
        '''
        
        Instrument.__init__(self, name, tags=['virtual'])
        
        #Parameters
        self.add_parameter('rise_time', flags=Instrument.FLAG_GETSET, units='ns', type=types.FloatType)
        self.add_parameter('plateau_time', flags=Instrument.FLAG_GETSET, units='ns', type=types.FloatType)
        self.add_parameter('fall_time', flags=Instrument.FLAG_GETSET, units='ns', type=types.FloatType)
        
        self.add_parameter('plateau_voltage', flags=Instrument.FLAG_GETSET, units='V', minval=0.05, maxval=5.0, type=types.FloatType)
        self.add_parameter('amplitude', flags=Instrument.FLAG_GET, units='mV', type=types.FloatType)
        
        # self.add_parameter('frequency', flags=Instrument.FLAG_GETSET, units='GHz', minval=100e-6, maxval=12.75, type=types.FloatType)
        # self.add_parameter('power', flags=Instrument.FLAG_GETSET, units='dBm', type=types.FloatType)
        
        self.add_parameter('interval', minval=1e-3, maxval= 500, units='s', flags=Instrument.FLAG_GETSET, type=types.FloatType)

        
        # self.add_parameter('status', option_list=['on', 'off'], flags=Instrument.FLAG_GETSET, type=types.StringType)
        self.add_parameter('live_update', option_list=[True, False], flags=Instrument.FLAG_GETSET, type=types.BooleanType)


        #Functions

        
        #Import instruments
        self._instruments = instruments.get_instruments()
        self._afg = self._instruments.get(afg)
        self._microwave_generator = self._instruments.get(mwsrc)
        self.live_update = live_update
        
        
        #Define default values
        self.rise_time = 10.0 #ns
        self.plateau_time = 20.0 #ns
        self.fall_time = 10.0 #ns
        
        self.plateau_voltage = 3.5 #V
        
        self.get_all()


    def get_all(self):
        '''
            Get all parameters of the virtual device
            
            Input:
                None
            
            Output:
                None
        '''
        
        self.get_rise_time()
        self.get_plateau_time()
        self.get_fall_time()
        
        self.get_plateau_voltage()
        
        # self.get_frequency()
        # self.get_power()
        self.get_amplitude()

        # self.get_status()
        
        self.get_interval()

#########################################################
#
#
#                       Live update
#
#
#########################################################


    def do_get_live_update(self):
        '''
        Get the option live update

        Input:
            None

        Output:
            live_update (bool) : the boolean option 
        '''
        return self.live_update


    def do_set_live_update(self, boolean):
        '''
        Set the live update function

        Input:
            live_update (bool) : the live update option

        Output:
            None
        '''
        
        self.live_update = boolean


        
#########################################################
#
#
#                       Amplitude
#
#
#########################################################


    def do_get_amplitude(self):
        '''
        Get the amplitude of the microwave pulse

        Input:
            None

        Output:
            amplitude (float) : Amplitude of the microwave pulse [mV]
        '''
        logging.debug(__name__ + ' : Get the amplitude of the microwave pulse')
        
        #To calculate the amplitude in voltage we assume that there is a match at 50 Ohms
        P = 1e-3*10.**(float(self._microwave_generator.get_power())/10.)
        
        return numpy.sqrt(P*50.)*1000.


#########################################################
#
#
#                       Interval between each pulse of the burst mode
#
#
#########################################################


    def do_get_interval(self):
        '''
        Get the interval between each cycle

        Input:
            None

        Output:
            interval (float) : The interval between each cycle
        '''
        logging.debug(__name__ + ' : Get the interval between each cycle')
        return self._afg.get_interval()



    def do_set_interval(self, interval=1.):
        '''
        Set the interval between each cycle

        Input:
            interval (float) : interval between each cycle [s]

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set the interval between each cycle to %.6f' % (interval))
        self._afg.set_interval(interval)


#########################################################################
#
#
#                           Rise time
#
#
#########################################################################

    def do_get_rise_time(self):
        '''
            Return the value of the rise time of the pulse
            
            Input:
                None
            
            Output:
                None
        '''
        
        return self.rise_time


    def do_set_rise_time(self, time = 0.0):
        '''
            Set the value of the rise time of the pulse
            
            Input:
                time (float): Time of the rise [ns]
            
            Output:
                None
        '''
        
        
        self.rise_time = time
        
        #We update the display of the tektro
        if self.live_update:
            self.set_pulse()


#########################################################################
#
#
#                           Plateau time
#
#
#########################################################################

    def do_get_plateau_time(self):
        '''
            Return the value of the plateau time of the pulse
            
            Input:
                None
            
            Output:
                None
        '''
        
        return self.plateau_time


    def do_set_plateau_time(self, time = 0.0):
        '''
            Set the value of the plateau time of the pulse
            
            Input:
                time (float): Time of the plateau [ns]
            
            Output:
                None
        '''
        
        
        self.plateau_time = time
        
        #We update the display of the tektro
        if self.live_update:
            self.set_pulse()


#########################################################################
#
#
#                           Fall time
#
#
#########################################################################

    def do_get_fall_time(self):
        '''
            Return the value of the fall time of the pulse
            
            Input:
                None
            
            Output:
                None
        '''
        
        return self.fall_time


    def do_set_fall_time(self, time = 0.0):
        '''
            Set the value of the fall time of the pulse
            
            Input:
                time (float): Time of the fall [ns]
            
            Output:
                None
        '''
        
        
        self.fall_time = time
        
        #We update the display of the tektro
        if self.live_update:
            self.set_pulse()


#########################################################################
#
#
#                           Plateau voltage
#
#
#########################################################################

    def do_get_plateau_voltage(self):
        '''
            Return the value in Volt of the plateau
            
            Input:
                None
            
            Output:
                None
        '''
        
        return self.plateau_voltage


    def do_set_plateau_voltage(self, voltage = 0.0):
        '''
            Set the value in Volt of the plateau
            
            Input:
                voltage (float): Voltage of the plateau [V]
            
            Output:
                None
        '''
        
        
        self.plateau_voltage = voltage
        
        #We update the display of the tektro
        if self.live_update:
            self.set_pulse()


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
        
        #We update the amplitude
        self.get_amplitude()


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
        
        return float(self._microwave_generator.get_frequency())*1e-9


    def do_set_frequency(self, frequency = 1.0):
        '''
            Set the value of the frequency
            
            Input:
                frequency (float): frequency of the pulse [GHz]
            
            Output:
                None
        '''
        
        self._microwave_generator.set_frequency(frequency*1e9)


#########################################################################
#
#
#                           Pulse
#
#
#########################################################################


    def set_pulse(self):
        '''
            Create a pulse depending parameters saved in set.
            
            Input:
                None
            
            Output:
                None
        '''
        
        
        #First we set the SMB
#        self._microwave_generator.set_status('on')
        
        self.total_point     = self._afg.get_maxpoint()
        
#        self.rise_time       = float(rise_time)
#        self.plateau_time    = float(plateau_time)Pul
#        self.fall_time       = float(fall_time)
        
        #We check if the time of the pulse is not too short or too long
        if self.get_rise_time() + self.get_plateau_time() + self.get_fall_time() < 16.67 or self.get_rise_time() + self.get_plateau_time() + self.get_fall_time() > 1e12 :
            
            self.logging.debug(__name__ + ' : Error, the pulse time is too short or too long')
            return 'Error: The pulse time is too short or too long'
        
        #We calculate the number of point of the waveform
        self.number_point = ( self.get_rise_time() + self.get_plateau_time() + self.get_fall_time() )*1e-9 * self._afg.get_maxrate()
        
        if self.number_point > self.total_point :
            
            self.number_point = self.total_point
        
        
#        self._afg.reset()
        self._afg.set_run_mode_burst_ch1()
        self._afg.set_burst_mode_triger_ch1()
        self._afg.set_ncycles_ch1(1)
#        self._afg.set_triger_source_internal()
        
        #The precision of the tektro is of 1 Hz, we calculate the frequency from different time
        self._frequency = 1.0/((self.get_rise_time() + self.get_plateau_time() + self.get_fall_time())*1e-9)
        self._afg.set_frequency_ch1(self._frequency)
#        
#        self._afg.set_period_ch1(rise_time + plateau_time + fall_time)
        
        #We set the amplitude of the AFG
        self._afg.set_amplitude_ch1(self.get_plateau_voltage())
        
        #We calculate the number of second we will have per points
        second_per_point = (self.get_rise_time() + self.get_plateau_time() + self.get_fall_time())*1e-9/self.number_point
        
        #We calculate the number of point dedicated for each parts of the pulse
        number_point_rise    = int(round(self.get_rise_time()*1e-9 / second_per_point, 0))
        number_point_plateau = int(round(self.get_plateau_time()*1e-9/second_per_point, 0))
        number_point_fall    = int(round(self.get_fall_time()*1e-9/second_per_point, 0))
        
        #We check if the number total of point calculated doesn't overflow the number total of point accepted by the tektro
        while number_point_rise + number_point_plateau + number_point_fall > self.total_point :
            
            number_point_plateau -= 1
        
        #We calculate the linear coeficient of the rise and of the fall
        coeficient_rise = self.plateau_voltage/number_point_rise
        coeficient_fall = self.plateau_voltage/number_point_fall
        
        #We create the list wich will contain all points of the waveform
        wave = []
        #First the rise
        for i in range(number_point_rise + 1):
            
            wave.append(i*coeficient_rise)
        
        #The plateau
        for i in range(number_point_plateau - 2):
            
            wave.append(self.plateau_voltage)
        
        #The fall
        for i in range(number_point_fall + 1):
            
            wave.append(self.plateau_voltage -i*coeficient_fall)
        
        #We send the pulse to the tektro
        self._afg.set_waveform_ch1(wave)
        #We save this pulse inside the memory of the tektro
        self._afg.set_transfert_ememory_user1()
        #We tune the tektro to use the waveform that we have just saved
        self._afg.set_function_user1_ch1()




    def do_set_status(self, status):
        '''
            Switch on|off the microwave pulse

            Input:
                status (String): Status of the microwave pulse ['on', 'off']

            Output:
                None
        '''
        
        if status.upper() == 'ON':
        
            #We set the pulse
            self.set_pulse()
           
            #We switch on|off the channel 1 of the tecktro
            self._afg.set_status_ch1(status)

            #We switch on|off the microwave generator
            self._microwave_generator.set_status(status)
        else :

            #We switch on|off the channel 1 of the tecktro
            self._afg.set_status_ch1(status)

            #We switch on|off the microwave generator
            self._microwave_generator.set_status(status)



    def do_get_status(self):
        '''
            Get the microwave pulse status

            Input:
                None

            Output:
                status (String): Microwave pulse status
        '''
        
        #We get status of the channel 1 of the tecktro
        status_1 = self._afg.get_status_ch1()
        
        #We get the status of the microwave generator
        status_2 = self._microwave_generator.get_status()
        
        #If at least one devices is switch off we consider the microwave pulse switched off
        if status_1.upper() == 'OFF' or status_2.upper() == 'OFF' :

            return 'off'
        else:

            return 'on'


