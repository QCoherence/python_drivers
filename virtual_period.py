# -*- coding: utf-8 -*-
from instrument import Instrument
import instruments
import numpy
import types
import logging

class virtual_period(Instrument):
    '''
    This is the driver to handle period.
    '''



    def __init__(self, name, pulser):
        '''
            Initialize the virtual instruments

                Input:
                    name            : Name of the virtual instruments
                    pulser          : Name given to the pulser

                Output:
                    None
        '''

        Instrument.__init__(self, name, tags=['virtual'])

        self.add_parameter('period', units='ns',  flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET, type=types.FloatType)
        self.add_parameter('cooling_time', units='ns', flags=Instrument.FLAG_GETSET, type=types.FloatType)
        self.add_parameter('origin', units='ns', flags=Instrument.FLAG_GETSET, type=types.FloatType)


        # Defining some stuff
        self._instruments = instruments.get_instruments()
        self._pulser = self._instruments.get(pulser)

        self._cooling_time = 1e3 #in [ns]
        self._origin = 0. #in [ns]


        self.get_all()

    def get_all(self):
        '''
            Get all parameters of the virtual device

            Input:
                None

            Output:
                None
        '''
        self.get_period()




#########################################################
#
#
#                Period
#
#
#########################################################



    def do_set_period(self, period):
        '''
            set the period of the instrument

            Input:
                period (float): period of the pulser[ns]

            Output:
                None
        '''

        logging.info(__name__+' : set the period of the pulser')
        self._pulser.set_period(period)



    def do_get_period(self):
        '''
            Get the period of the instrument

            Input:
                None

            Output:
                period (float): period of the pulser[ns]
        '''

        logging.info(__name__+' : Get the period of the pulser')
        return float(self._pulser.get_period())




#########################################################
#
#
#                cooling time
#
#
#########################################################

    def do_set_cooling_time(self, cooling_time=1e3):
        '''
            Set the cooling_time of the pulser

            Input:
                cooling_time (float): cooling_time of the pulser [ns]

            Output:
                None
        '''

        logging.info(__name__+' : Set the cooling_time of the pulser')

        self._cooling_time = cooling_time
        period1 = self.get_period()
        period = self.get_origin() + self._pulser.get_chA_width()
        period = max(period, period1) #added by Remy
        self.set_period(period + cooling_time)


    def do_get_cooling_time(self):
        '''
            Get the cooling time

            Input:
                None

            Output:
                period (float): cooling time [ns]
        '''

        logging.info(__name__+' : Get the cooling time')
        return float(self._cooling_time)




#########################################################
#
#
#                Origin
#
#
#########################################################

    def do_set_origin(self, origin=1e3):
        '''
            Set the origin of the pulses

            Input:
                origin (float): origin of the pulses [ns]

            Output:
                None
        '''

        logging.info(__name__+' : Set the origin of the pulses')

        self._origin = origin
        oldPeriod = self.get_period()

        cooling_time = self.get_cooling_time()
        periodA = origin                       + self._pulser.get_chA_width() + cooling_time
        periodC = self._pulser.get_chC_delay() + self._pulser.get_chC_width() + cooling_time
        periodD = self._pulser.get_chD_delay() + self._pulser.get_chD_width() + cooling_time
        newPeriod = max(periodA, periodC, periodD)

        #If the new period is longer than the old,
        #We set first the period and next we change the delaies
        if newPeriod > oldPeriod:

            self.set_period(newPeriod)
            boardDelay = self._pulser.get_chB_delay() - self._pulser.get_chA_delay()
            self._pulser.set_chA_delay(origin)
            self._pulser.set_chB_delay(origin + boardDelay)
        else:

            boardDelay = self._pulser.get_chB_delay() - self._pulser.get_chA_delay()
            self._pulser.set_chA_delay(origin)
            self._pulser.set_chB_delay(origin + boardDelay)
            self.set_period(newPeriod)


    def do_get_origin(self):
        '''
            Get the origin of the pulses

            Input:
                None

            Output:
                period (float): origin of the pulses [ns]
        '''

        logging.info(__name__+' : Get the origin of the pulses')
        return float(self._origin)
