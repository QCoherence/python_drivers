from instrument import Instrument
import telnetlib as telnet
import logging
import types


class T560DDG(Instrument):
    '''
    This is the python driver for the T560DDG

    Usage:
    Initialize with
    <name> = instruments.create('name', 'T560DDG', address='<GPIB address>', reset=True|False)
    '''

    def __init__(self, name, address, port, reset = False):
        '''
        Initializes the T560DDG

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
        self._port    = port
        
        #Instance the object telnet
        self.T560 = telnet.Telnet()

        #Open the connection
        self.T560.open(self._address, port=self._port)
        
        
#        self.add_parameter('frequency', flags=Instrument.FLAG_GETSET, units='Hz', minval=100e3, maxval=12.75e9, type=types.FloatType)
#        self.add_parameter('power', flags=Instrument.FLAG_GETSET, units='dBm', maxval=30.0, type=types.FloatType)
#        self.add_parameter('phase', flags=Instrument.FLAG_GETSET, units='rad', minval=-pi, maxval=pi, type=types.FloatType)
#        self.add_parameter('status', flags=Instrument.FLAG_GETSET, option_list=['on', 'off'], type=types.StringType)

        
        self.add_function ('get_all')
        self.add_function('reset')
        
        if reset :
            
            self.reset()
        
        self.get_all()
        
