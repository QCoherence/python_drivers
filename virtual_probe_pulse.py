from instrument import Instrument
import instruments
import numpy
import types
import logging

class virtual_probe_pulse(Instrument):
    '''
    This is the driver for the virtual instrument which can create a microwave pulse

    Usage:
    Initialize with
    <name> = qt.instruments.create('name', 'virtual_microwave_pulse', pulser='pulser_name', channel='pulser_channel_name', mwsrc='name_microwave_generator')
    '''

    def __init__(self, name, pulser, probe_src, period):
        '''
            Initialize the virtual instruments

                Input:
                    - name: Name of the virtual instruments
                    - pulser: Name of a delay generator
                    - mwsrc: Name given to the microwave_generator
                    - period: Name given to the virtual period

                Output:
                    None
        '''
        Instrument.__init__(self, name, tags=['virtual'])

        #Import instruments
        self._instruments = instruments.get_instruments()
        self._pulser      = self._instruments.get(pulser)
        self._period      = self._instruments.get(period)
        self._probe_src   = self._instruments.get(probe_src)

        #Parameters
        self.add_parameter('width',
                            flags=Instrument.FLAG_GETSET,
                            minval=2,
                            maxval=1e10,
                            units='ns',
                            type=types.FloatType)
        self.add_parameter('delay',
                            flags=Instrument.FLAG_GETSET,
                            minval=-1e10,
                            maxval=1e10,
                            units='ns',
                            type=types.FloatType)

        self.add_parameter('frequency',
                            flags=Instrument.FLAG_GETSET,
                            units='GHz',
                            minval = 1e-4,
                            maxval= 40,
                            type=types.FloatType)

        self.add_parameter('power',
                            flags=Instrument.FLAG_GETSET,
                            minval = -135.,
                            maxval= 25.,
                            units='dBm',
                            type=types.FloatType)

        self.add_parameter('status', option_list=['ON', 'OFF'], flags=Instrument.FLAG_GETSET, type=types.StringType)


        #We initialize the trigger pulse for the board
        self._pulser.set_chC_status('OFF')
        self._pulser.set_chC_polarity('POS')
        self._pulser.set_chC_status('ON')

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
        self.get_delay()

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
                None'virtual_probe_pulse'

            Output:
                None
        '''

        return self._pulser.get_chC_width()



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
        periodA = self._pulser.get_chA_delay() + self._pulser.get_chA_width()  + cooling_time
        periodC = self._pulser.get_chC_delay() + val + cooling_time
        periodD = self._pulser.get_chD_delay() + self._pulser.get_chD_width() + cooling_time
        newPeriod = max(periodA, periodC, periodD)

        #If the new period is shorter than the old
        #we change first the pulse length and after we change the period
        if newPeriod < oldPeriod :
            self._pulser.set_chC_width(val)
            self._period.set_period(newPeriod)
        #Otherwise we change first the period and then, the pulse duration
        else:
            self._period.set_period(newPeriod)
            self._pulser.set_chC_width(val)




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
                None
        '''

        return self._pulser.get_chC_delay() - self._pulser.get_chA_delay()


    def do_set_delay(self, delay = 0.):
        '''
            Set the value of the pulse delay

            Input:
                delay (float): Time of the pulse delay [ns]

            Output:
                None
        '''

        # if self._period.get_origin() < self.get_width() + delay:

            # raise ValueError("Your origin is too small to contain your probe pulse.")
        # else:

        if self._period.get_origin() + delay >= 0:
            self._pulser.set_chC_delay(self._period.get_origin() + delay)
        else:
            raise ValueError("Your origin is too small.")

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
                power (float): power of the microwave [dBm]
        '''

        return self._probe_src.get_power()


    def do_set_power(self, power):
        '''
            Set the value of the power

            Input:
                power (float): power of the microwave [dBm]

            Output:
                None
        '''

        self._probe_src.set_power(power)


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

        return 1e-9*self._probe_src.get_frequency()


    def do_set_frequency(self,frequency):
        '''
            Set the value of the frequency

            Input:
                frequency (float): frequency of the pulse [GHz]

            Output:
                None
        '''

        self._probe_src.set_frequency(frequency*1e9)



#########################################################################
#
#
#                           Statut
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

        if status.upper() in ['ON','OFF']:
            # self._probe_src.set_RF_status('%s'%status)
            self._probe_src.set_status('%s'%status)
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

        # return self._probe_src.get_RF_status()
        return self._probe_src.get_status()

# Remy has changed RF_status into status so that it works with the SMB 100A as the probe_src.
# we have to change back when changing the source back to Agilent 40GHz 
