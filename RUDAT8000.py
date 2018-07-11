from instrument import Instrument
import types
import logging
import numpy as np
import urllib2


class RUDAT8000(Instrument):
    '''
    This is the python driver for the RUDAT8000

    Usage:
    Initialize with
    <name> = instruments.create('name', 'RUDAT8000', address='<TCPIP address>', reset=True|False)
    '''

    def __init__(self, name, address):
        '''
        Initializes the RUDAT8000

        Input:
            name (string)    : name of the instrument
            address (string) : TCPIP/GPIB address
            reset (bool)     : Reset to default values

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        # print self._address
        self.add_parameter('attenuation',
            flags=Instrument.FLAG_GETSET,
            units='dB',
            minval=0., maxval=30.,
            type=types.FloatType)
        self.add_function('plus_att_step')
        self.add_function('minus_att_step')

        # self.set_attenuation(0.)
    def do_get_attenuation(self):
        return float( urllib2.urlopen(self._address+'/ATT?').read() )

    def do_set_attenuation(self, value):
        if (value % 0.25) != 0:
            print 'value should be a multiple of 0.25'

        urllib2.urlopen(self._address+'/:SETATT %s'%value)
        if value != self.get_attenuation():
            print 'error setting the attenuation'

    def plus_att_step(self):
        value = self.get_attenuation()

        if value < 30.:
            value += 0.25
            urllib2.urlopen(self._address+'/:SETATT %s'%value)

    def minus_att_step(self):
        value = self.get_attenuation()

        if value > 0.:
            value -= 0.25
            urllib2.urlopen(self._address+'/:SETATT %s'%value)
