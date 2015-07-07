from instrument import Instrument
import instruments
import numpy
import types
import logging

class virtual_microwave_pulse(Instrument):
    '''
    This is the driver for the virtual instrument which can create a microwave pulse

    Usage:
    Initialize with
    <name> = qt.instruments.create('name', 'virtual_microwave_pulse', pulser='pulser_name', channel='pulser_channel_name', mwsrc='name_microwave_generator')
    '''
    
    def __init__(self, name, pulser, ch, mwsrc, period):
        '''
            Initialize the virtual instruments
                
                Input:
                    - name: Name of the virtual instruments
                    - pulser: Name of a delay generator (set_ch%c_width and set_ch%c_wdelay methods are required)
                    - channel: channel name of the delay generator
                    - mwsrc: Name given to the microwave_generator
                
                Output:
                    None
        '''
        Instrument.__init__(self, name, tags=['virtual'])
        
        #Import instruments
        self._instruments = instruments.get_instruments()
        self._pulser = self._instruments.get(pulser)
        self._period = self._instruments.get(period)
        self._ch = ch
        self._microwave_generator = self._instruments.get(mwsrc)
        self._pulser.set('ch%c_polarity'%self._ch,'POS')
        self._microwave_generator.set_status('ON')
        
        #Fetching parameter bounds
        self._max_power = self._microwave_generator.get_parameter_options('power')['maxval']
        
        try:
            self._min_power = self._microwave_generator.get_parameter_options('power')['minval']
        except Exception as error:
            self._min_power = -145.0
        self._max_freq = 1e-9*self._microwave_generator.get_parameter_options('frequency')['maxval']
        self._min_freq = 1e-9*self._microwave_generator.get_parameter_options('frequency')['minval']
        self._max_width = self._pulser.get_parameter_options('ch%c_width'%self._ch)['maxval']
        self._min_width = self._pulser.get_parameter_options('ch%c_width'%self._ch)['minval']
        
        #Parameters
        self.add_parameter('width',
                            flags=Instrument.FLAG_GETSET, 
                            minval=self._min_width,
                            maxval=self._max_width,
                            units='ns', 
                            type=types.FloatType)
#        self.add_parameter('delay', 
#                            flags=Instrument.FLAG_GETSET, 
#                            minval=0,
#                            maxval=1e10,
#                            units='ns', 
#                            type=types.FloatType)
        
        self.add_parameter('frequency', 
                            flags=Instrument.FLAG_GETSET, 
                            units='GHz', 
                            minval = self._min_freq, 
                            maxval= self._max_freq, 
                            type=types.FloatType)
                            
        self.add_parameter('power', 
                            flags=Instrument.FLAG_GETSET, 
                            minval = self._min_power, 
                            maxval= self._max_power, 
                            units='dBm', 
                            type=types.FloatType)

        self.add_parameter('status', option_list=['ON', 'OFF'], flags=Instrument.FLAG_GETSET, type=types.StringType)


        #Functions
        self.get_all()


    def get_all(self):
        '''
            Get all parameters of the virtual device
            
            Input:
                None
            
            Output:
                None
        '''
        
        self.get_width()
#        self.get_delay()
        
        self.get_frequency()
        self.get_power()
        self.get_status()
        
#########################################################################
#
#
#                           Width
#
#
#########################################################################

    def do_get_width(self):
        '''
            Return the width of the pulse
            
            Input:
                None
            
            Output:
                None
        '''
        
        return self._pulser.get('ch%c_width'%self._ch) 


    def do_set_width(self, val):
        '''
            Set the value of the pulse width
            The period will be automatically updated taking into account the cooling time
            
            Input:
                val (float): Time of the pulse width [ns]
            
            Output:
                None
        '''
        #We change the period of the pulser
        
        #We get the old period
        oldPeriod  = self._period.get_period()
        
        #We calculate the new possible period
        cooling_time = self._period.get_cooling_time()
        periodA = self._pulser.get_chA_delay() + val + cooling_time
        periodC = self._pulser.get_chC_delay() + self._pulser.get_chC_width() + cooling_time
        periodD = self._pulser.get_chD_delay() + self._pulser.get_chD_width() + cooling_time
        newPeriod = max(periodA, periodC, periodD)
        
        #If the new period is shorter than the old
        #we change first the pulse length and after we change the period
        if newPeriod < oldPeriod :
            self._pulser.set('ch%c_width'%self._ch, val)
            self._period.set_period(newPeriod)
        #Otherwise we change first the period and then, the pulse duration
        else:
            self._period.set_period(newPeriod)
            self._pulser.set('ch%c_width'%self._ch, val)


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


    def do_set_power(self, power):
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
        
        return 1e-9*self._microwave_generator.get_frequency()


    def do_set_frequency(self,frequency):
        '''
            Set the value of the frequency
            
            Input:
                frequency (float): frequency of the pulse [GHz]
            
            Output:
                None
        '''
        
        self._microwave_generator.set_frequency(frequency*1e9)


    def do_set_status(self, status):
        '''
            Switch on|off the microwave pulse

            Input:
                status (String): Status of the microwave pulse ['ON', 'OFF']

            Output:
                None
        '''
        
        if status.upper() in ['ON','OFF']:
            self._pulser.set('ch%c_status'%self._ch,status)
            self._microwave_generator.set_status('%s'%status)
        else:
            pass


    def do_get_status(self):
        '''
            Get the microwave pulse status

            Input:
                None

            Output:
                status (String): Microwave pulse status
        '''
        
        return self._pulser.get('ch%c_status'%self._ch).upper()


