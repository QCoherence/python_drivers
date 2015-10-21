# Tektronix_AWG5014.py class
#
# Nicolas Roch <nicolas.roch@neel.cnrs.fr>, 2015
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
import visa
import types
import logging
import numpy as np
import struct
import pyvisa.constants as vc
import ctypes

################### Constants

MARKER_QUANTUM = 2        #: quantum of marker-length and marker-offset
_EX_DAT_MARKER_1_MASK = 0x20000000L #: the mask of marker 1 in the extra-data (32-bits) value
_EX_DAT_MARKER_2_MASK = 0x10000000L #: the mask of marker 2 in the extra-data (32-bits) value
Channels=(1,2,3,4)
Mark_num = (1,2)
###### Useful functions
def _engineer_to_scienc(value):
        '''
        Function to convert a value form engineering format to scientific format

        Input:
            value (int): value to convert

        Output:
            converted value (int)
        '''
        multipliers = {'n':1e-9,'u':1e-6,'m':1e-3,'k': 1e3, 'M': 1e6, 'G': 1e9}
        return int(float(value[:-1])*multipliers[value[-1]])

class Tabor_WX1284C(Instrument):
    '''
    This is the python driver for the Tabor WX1284C
    Arbitrary Waveform Generator

    Usage:
    Initialize with
    <name> = instruments.create('name', 'Tabor_WX1284C', address='<address>')

    think about:    clock, waveform length

    TODO:
    complete de driver
    write a cleaner version of 'init_channel'
    make the string formatting uniform
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the AWG520.

        Input:
            name (string)    : name of the instrument
            address (string) :  address
            reset (bool)     : resets to default values, default=false

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])


        self._address = address
        #self._visainstrument = visa.instrument(self._address)
        # self._values = {}
        # self._values['files'] = {}
        # self._clock = clock
        # self._numpoints = numpoints


        self.add_parameter('func_mode', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('trigger_mode', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('output', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 4),channel_prefix='ch%d_')
        # self.add_parameter('all_output', type=types.StringType,
        #     flags=Instrument.FLAG_SET | Instrument.FLAG_GET_AFTER_SET)

        self.add_parameter('coupling', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 4),channel_prefix='ch%d_')
        self.add_parameter('ref_freq', type=types.IntType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=10, maxval=100, units='MHz')
        self.add_parameter('ref_source', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('clock_freq', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=75, maxval=1250, units='MHz')
        self.add_parameter('clock_source', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)

        self.add_parameter('amplitude', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 4), channel_prefix='ch%d_',
            minval=0.05, maxval=2, units='Volts')

        self.add_parameter('all_amp', type=types.FloatType,
            flags=Instrument.FLAG_SET | Instrument.FLAG_GET_AFTER_SET,
            minval=0.05, maxval=2, units='Volts')


        self.add_parameter('offset', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 4), channel_prefix='ch%d_',
            minval=-1, maxval=1, units='Volts')

        self.add_parameter('all_offset', type=types.FloatType,
            flags=Instrument.FLAG_SET | Instrument.FLAG_GET_AFTER_SET,
            minval=-1, maxval=1, units='Volts')

        self.add_parameter('trigger_level', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-5, maxval=5, units='Volts')

        self.add_parameter('marker_status_1_2', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,2), channel_prefix='m%d_')

        self.add_parameter('marker_status_3_4', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,2), channel_prefix='m%d_')
        # self.add_parameter('numpoints', type=types.IntType,
            # flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            # minval=192, maxval=16e9, units='Int')
        # self.add_parameter('amplitude', type=types.FloatType,
            # flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            # channels=(1, 4), minval=0, maxval=2, units='Volts')
        # self.add_parameter('offset', type=types.FloatType,
            # flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            # channels=(1, 4), minval=-2, maxval=2, units='Volts')
        # self.add_parameter('marker1_low', type=types.FloatType,
            # flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            # channels=(1, 4), minval=-2, maxval=2, units='Volts')
        # self.add_parameter('marker1_high', type=types.FloatType,
            # flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            # channels=(1, 4), minval=-2, maxval=2, units='Volts')
        # self.add_parameter('marker2_low', type=types.FloatType,
            # flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            # channels=(1, 4), minval=-2, maxval=2, units='Volts')
        # self.add_parameter('marker2_high', type=types.FloatType,
            # flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            # channels=(1, 4), minval=-2, maxval=2, units='Volts')
        # self.add_parameter('status', type=types.StringType,
            # flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            # channels=(1, 4))

        # Add functions
        self.add_function('clean_visa_open')
        self.add_function('reset')
        self.add_function('clear_err')
        self.add_function('init_channel')
        self.add_function('get_all')

        #opening the visa session
        self.clean_visa_open()

        if reset:
            self.reset()
            self.clear_err()
        else:
            self.get_all()

    #Functions
    def clean_visa_open(self):
        '''
        Opens a visa session with the proper parameters

        Input:
            None

        Output:
            None
        '''
        try:
            rm = visa.ResourceManager()

            inst = rm.open_resource(self._address+'::5025::SOCKET')
            # since the 20th of october 2015, it seems that the complete adress of the TABOR is the IP adress plus the SOCKET...

            inst.timeout = 20000L

            inst.visalib.set_buffer(inst.session, vc.VI_READ_BUF, 4000)
            inst.visalib.set_buffer(inst.session, vc.VI_WRITE_BUF, 32000)

            inst.read_termination = '\n'
            inst.write_termination = '\n'

            intf_type = inst.get_visa_attribute(vc.VI_ATTR_INTF_TYPE)

            if intf_type in (vc.VI_INTF_USB, vc.VI_INTF_GPIB, vc.VI_INTF_TCPIP):
                inst.set_visa_attribute(vc.VI_ATTR_WR_BUF_OPER_MODE, vc.VI_FLUSH_ON_ACCESS)
                inst.set_visa_attribute(vc.VI_ATTR_RD_BUF_OPER_MODE, vc.VI_FLUSH_ON_ACCESS)
                if intf_type == vc.VI_INTF_TCPIP:
                    inst.set_visa_attribute(vc.VI_ATTR_TERMCHAR_EN, vc.VI_TRUE)

            inst.clear()

            self._visainstrument = inst

            logging.debug(__name__ + ' : visa session opened correctly')

        except:
            logging.debug(__name__ + ' : could not open visa session')
            raise ValueError(__name__ + ' : could not open visa session')

    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST')

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Reading all data from instrument')

        self.get_func_mode()
        self.get_trigger_mode()
        self.get_ref_source()
        self.get_ref_freq()
        self.get_clock_source()
        self.get_clock_freq()
        self.get_trigger_level()

        for i in Channels:
            self.get('ch%d_output' % i)
            self.get('ch%d_coupling' % i)
            self.get('ch%d_amplitude' % i)
            self.get('ch%d_offset' % i)

        for i in Mark_num:
            self.get('m%d_marker_status_1_2' % i)
            self.get('m%d_marker_status_3_4' % i)

    def clear_err(self):
        '''
        Clears the error queue of the instrument

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Clearing error queue of the instrument')
        self._visainstrument.write('*CLS')

    def init_channel(self,channel=1):
        '''
        Initializes a given channel to allow proper upload of waveforms and markers:

        Input:
            channel (string): Channel ID

        Output:
            None
        '''
        logging.info( '{} : Initializing channel {0:d}'.format(__name__,channel))
        # Select channel
        toto._visainstrument.write(":INST:SEL {0:d}".format(channel))
        # Set it to 'User-Mode'
        toto._visainstrument.write(":FUNC:MODE USER")
        # Set markers-type to 'user-defined' (external)
        toto._visainstrument.write(":SOUR:MARK:SOUR USER")

    #Parameters
    def do_get_func_mode(self):
        '''
        Gets the function mode of the instrument

        Input:
            None

        Output:
            Function mode (string) : 'FIX','USER','SEQ','ASEQ','MOD','PULS','PATT' depending on the mode
        '''
        logging.info( '{} : Getting the function mode'.format(__name__))
        return self._visainstrument.query('FUNC:MODE?')

    def do_set_func_mode(self,value='SEQ'):
        '''
        Sets the output function mode of the instrument

        Input:
            Function mode (string) : 'FIX','USER','SEQ','ASEQ','MOD','PULS','PATT' depending on the mode

        Output:
            None
        '''
        logging.info( '{} : Setting the output function mode to {}'.format(__name__,value))
        if value.upper() in ('FIX','USER','SEQ','ASEQ','MOD','PULS','PATT'):
            self._visainstrument.write('FUNC:MODE {}'.format(value))
            if self._visainstrument.query('FUNC:MODE?') != value:
                logging.info('Instrument did not select the output function correctly')
        else:
            logging.info('The invalid value {} was sent to func_mode method'.format(value))

            raise ValueError('The invalid value {} was sent to func_mode method. Valid values are \'FIX\',\'USER\',\'SEQ\',\'ASEQ\',\'MOD\',\'PULS\',\'PATT\'.'.format(value))

    def do_get_trigger_mode(self):
        '''
        Gets the trigger mode of the instrument

        Input:
            None

        Output:
            Trigger mode (string): 'CONT', 'TRIG', 'GATE' depending on the mode
        '''
        logging.info( '{} : Getting the trigger mode'.format(__name__))
        if self._visainstrument.query('INIT:CONT?') == 'ON':
            return 'CONT'
        elif self._visainstrument.query('INIT:GATE?') == 'ON':
            return 'GATE'
        else:
            return 'TRIG'

    def do_set_trigger_mode(self, value='TRIG'):
        '''
        Sets the trigger mode of the instrument

        Input:
            Trigger mode (string): 'CONT', 'TRIG', 'GATE' depending on the mode

        Output:
            None
        '''
        logging.info( '{} : Setting the trigger mode to {}'.format(__name__,value))
        if value.upper() == 'CONT':
            self._visainstrument.write('INIT:CONT ON')
            if self._visainstrument.query('INIT:CONT?') != 'ON':
                logging.info('Trigger mode wasn\'t set properly')
        elif value.upper() == 'TRIG':
            self._visainstrument.write('INIT:CONT OFF')
            self._visainstrument.write('INIT:GATE OFF')
            if self._visainstrument.query('INIT:CONT?') != 'OFF':
                logging.info('Trigger mode wasn\'t set properly')
            elif self._visainstrument.query('INIT:GATE?') != 'OFF':
                logging.info('Trigger mode wasn\'t set properly')
        elif value.upper() == 'GATE':
            self._visainstrument.write('INIT:CONT OFF')
            self._visainstrument.write('INIT:GATE ON')
            if self._visainstrument.query('INIT:CONT?') != 'OFF':
                logging.info('Trigger mode wasn\'t set properly')
            elif self._visainstrument.query('INIT:GATE?') != 'ON':
                logging.info('Trigger mode wasn\'t set properly')
        else:
            logging.info('The invalid value {} was sent to set_trigger_mode method'.format(value))
            raise ValueError('The invalid value {} was sent to set_trigger_mode method. Valid values are \'CONT\', \'TRIG\', \'GATE\'.'.format(value))

    def do_get_output(self, channel=1):
        '''
        Gets the state of a given channel: ON or OFF

        Input:
            channel (string): Channel ID

        Output:
            Output state (string): 'ON' or 'OFF'
        '''
        logging.info( __name__+ ': Getting the output state of channel %s' % channel)

        if channel in Channels:
            self._visainstrument.write('INST:SEL{0:d}'.format(channel))
            if self._visainstrument.query('INST:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the channel correctly')
        else:
            logging.info('The invalid Channel ID {0:d} was sent to get_output'.format(channel))
            raise ValueError('The invalid Channel ID {0:d} was sent to get_output. Valid values are 1,2,3,4.'.format(channel))

        return self._visainstrument.query('OUTP?')

    def do_set_output(self, state='ON', channel=1):
        '''
        Sets the state of a given channel to ON or OFF

        Input:
            channel (int): Channel ID
            state (string): 'ON' or 'OFF'

        Output:
            None
        '''

        logging.info( __name__+' : Setting the output state of channel %s to %s'%( channel, state))

        if channel in Channels:
            self._visainstrument.write('INST:SEL{0:d}'.format(channel))
            if self._visainstrument.query('INST:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the channel correctly')
        else:
            logging.info('The invalid Channel ID {0:d} was sent to set_output'.format(channel))
            raise ValueError('The invalid Channel ID {0:d} was sent to set_output. Valid values are 1,2,3,4.'.format(channel))

        if state in ('ON','OFF'):
            self._visainstrument.write('OUTP{}'.format(state))
            if self._visainstrument.query('OUTP?') != state:
                logging.info('ON/OFF wasn\'t set properly')
        else:
            logging.info('The invalid state {} was sent to set_output'.format(state))
            raise ValueError('The invalid state {} was sent to set_output. Valid values are \'ON\' or \'OFF\'.'.format(state))

    def do_get_coupling(self, channel=1):
        '''
        Gets the coupling mode of a given channel: 'DC' or 'HV'.
        'DC' has 700MHs BW and +/-2 V output while HV has 350MHs BW and +/-4 V output.

        Input:
            channel (string): Channel ID

        Output:
            Coupling (string): 'DC' or 'HV'
        '''
        logging.info( __name__+ ': Getting the coupling of channel %s' % channel)

        if channel in Channels:
            self._visainstrument.write('INST:SEL{0:d}'.format(channel))
            if self._visainstrument.query('INST:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the channel correctly')
        else:
            logging.info('The invalid Channel ID {0:d} was sent to get_output'.format(channel))
            raise ValueError('The invalid Channel ID {0:d} was sent to get_output. Valid values are 1,2,3,4.'.format(channel))

        return self._visainstrument.query('OUTP:COUP ?')

    def do_set_coupling(self, coupling='DC', channel=1):
        '''
        Sets the coupling mode of a given channel: 'DC' or 'HV'.
        'DC' has 700MHs BW and +/-2 V output while HV has 350MHs BW and +/-4 V output.

        Input:
            channel (int): Channel ID
            coupling (string): 'DC' or 'HV'

        Output:
            None
        '''

        logging.info( __name__+' : Setting the coupling of channel %s to %s'%( channel, coupling))

        if channel in Channels:
            self._visainstrument.write('INST:SEL{0:d}'.format(channel))
            if self._visainstrument.query('INST:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the channel correctly')
        else:
            logging.info('The invalid Channel ID {0:d} was sent to set_coupling'.format(channel))
            raise ValueError('The invalid Channel ID {0:d} was sent to set_coupling. Valid values are 1,2,3,4.'.format(channel))

        if coupling in ('DC','HV'):
            self._visainstrument.write('OUTP:COUP %s'% coupling)
            if self._visainstrument.query('OUTP:COUP ?') != coupling:
                logging.info('DC/HV wasn\'t set properly')
        else:
            logging.info('The invalid coupling {} was sent to set_coupling'.format(coupling))
            raise ValueError('The invalid coupling {} was sent to set_coupling. Valid values are \'DC\' or \'HV\'.'.format(coupling))

    def do_get_ref_source(self):
        '''
        Gets the source of the reference oscillator: 'INT' or 'EXT'

        Input:
            None

        Output:
            Source of the reference oscillator (string): 'INT' or 'EXT'
        '''
        logging.info( __name__+ ': Getting the source of the reference oscillator.')
        return self._visainstrument.query('ROSC:SOUR?')

    def do_set_ref_source(self,source):
        '''
        Sets the source of the reference oscillator: 'INT' or 'EXT'.

        Input:
            source (string): Source of the reference oscillator: 'INT' or 'EXT'.

        Output:
            None
        '''
        logging.info( __name__+ ': Setting the source of the reference oscillator to %s.' % source.upper())
        if source.upper() in ('INT','EXT'):
            self._visainstrument.write('ROSC:SOUR %s' %source.upper())
            if self._visainstrument.query('ROSC:SOUR?') != source.upper():
                logging.info('Instrument did not set correctly the oscillator reference')
                raise ValueError('Instrument did not set correctly the oscillator reference')
        else:
            logging.info('The invalid value %s was sent to set_ref_source' % source.upper())
            raise ValueError('The invalid value %s was sent to set_ref_source. Valid values are \'INT\' or \'EXT\'.' % source.upper())

    def do_get_ref_freq(self):
        '''
        Gets the frequency of the reference oscillator: 10,20, 50 or 100 MHz.

        Input:
            None

        Output:
            Frequency of the reference oscillator (int): 10,20, 50 or 100 MHz.
        '''
        logging.info( __name__+ ': Getting the frequency of the reference oscillator.')
        return _engineer_to_scienc(self._visainstrument.query('ROSC:FREQ?'))*1e-6

    def do_set_ref_freq(self,freq):
        '''
        Sets the frequency of the reference oscillator: 10,20, 50 or 100 MHz.

        Input:
            freq (int): Frequency of the reference oscillator (int): 10,20, 50 or 100 MHz.

        Output:
            None
        '''
        logging.info( __name__+ ': Setting the frequency of the reference oscillator to %s.' % freq)
        if freq in (10, 20, 50, 100):
            self._visainstrument.write('ROSC:FREQ %s' %int(freq*1e6))
            if _engineer_to_scienc(self._visainstrument.query('ROSC:FREQ?')) != freq*1e6:
                logging.info('Instrument did not set correctly the reference oscillator frequency')
                raise ValueError('Instrument did not set correctly the reference oscillator frequency')
        else:
            logging.info('The invalid value %s was sent to set_ref_source' % freq)
            raise ValueError('The invalid value %s was sent to set_ref_source. Valid values are 10,20, 50 or 100.' % freq)

    def do_get_clock_source(self):
        '''
        Gets the source of the sample clock: 'INT' or 'EXT'

        Input:
            None

        Output:
            Source of the sample clock (string): 'INT' or 'EXT'
        '''
        logging.info( __name__+ ': Getting the source of the sample clock.')
        return self._visainstrument.query(':FREQ:RAST:SOUR?')

    def do_set_clock_source(self,source):
        '''
        Sets the source of the sample clock: 'INT' or 'EXT'.

        Input:
            source (string): Source of the sample clock (string): 'INT' or 'EXT'

        Output:
            None
        '''
        logging.info( __name__+ ': Setting the source of the sample clock to %s.' % source.upper())
        if source.upper() in ('INT','EXT'):
            self._visainstrument.write(':FREQ:RAST:SOUR %s' %source.upper())
            if self._visainstrument.query(':FREQ:RAST:SOUR?') != source.upper():
                logging.info('Instrument did not set correctly the source of the sample clock')
                raise ValueError('Instrument did not set correctly the source of the sample clock')
        else:
            logging.info('The invalid value %s was sent to set_clock_source' % source.upper())
            raise ValueError('The invalid value %s was sent to set_clock_source. Valid values are \'INT\' or \'EXT\'.' % source.upper())

    def do_get_clock_freq(self):
        '''
        Gets the frequency of the sample clock: 75 to 1250 MHz.

        Input:
            None

        Output:
            Frequency of the sample clock (float): 75 to 1250 MHz.
        '''
        logging.info( __name__+ ': Getting the frequency of the sample clock.')
        return float(self._visainstrument.query(':FREQ:RAST?'))*1e-6

    def do_set_clock_freq(self,freq):
        '''
        Sets the frequency of the sample clock: 75 to 1250 MHz.

        Input:
            freq (float): Frequency of the sample clock: 75 to 1250 MHz.

        Output:
            None
        '''
        logging.info( __name__+ ': Setting the frequency of the sample clock to %s.' % freq)
        if freq >= 75 and freq <= 1250:
            self._visainstrument.write(':FREQ:RAST %s' %int(freq*1e6))
            if float(self._visainstrument.query(':FREQ:RAST?')) != freq*1e6:
                logging.info('Instrument did not set correctly the sample clock frequency')
                raise ValueError('Instrument did not set correctly the sample clock frequency')
        else:
            logging.info('The invalid value %s was sent to set_clock_freq' % freq)
            raise ValueError('The invalid value %s was sent to set_clock_freq. Valid values are from 10 to 1250 MHz with 8-digits precision.' % freq)


# # added by remy:
# pb with  set_all_output: "error" message (even if it seems to be working): "the instrument does not support getting all output"
    # def do_set_all_output(self, state):
    #     '''
    #     Sets the state of all 4 channels to ON or OFF
    #
    #     Input:
    #         state (string): 'ON' or 'OFF'
    #
    #     Output:
    #         None
    #     '''
    #
    #     logging.info( __name__+' : Setting the output state of all 4 channels to %s'%(state) )
    #
    #     if state in ('ON','OFF'):
    #         self._visainstrument.write('OUTP:ALL{}'.format(state))

    #         if self._visainstrument.query('OUTP:STAT?') != state:
    #             logging.info('ON/OFF wasn\'t set properly')
    #     else:
    #         logging.info('The invalid state {} was sent to set_output'.format(state))
    #         raise ValueError('The invalid state {} was sent to set_output. Valid values are \'ON\' or \'OFF\'.'.format(state))
    #

    def do_set_all_amp(self, amp):
        '''
        Sets the amplitude of all 4 channels at the same time.
        Input:
            amp (float): amplitude of the channel in [V]
        Output:
            None
        '''
        logging.info( __name__+ ': Setting the amplitude of the 4 channels to %s.' %(amp) )

        self._visainstrument.write('OUTP:COUP:ALL DC')

        self._visainstrument.write('VOLT:ALL %s'% amp)
        if self._visainstrument.query('VOLT ?') != amp:
            logging.info('The amplitude wasn\'t set properly')
            raise ValueError('The amplitude wasn\'t set properly')

    def do_set_all_offset(self, offset):
        '''
        Sets the offset of all 4 channels at the same time.
        Input:
            offset (float): offset in [V]
        Output:
            None
        '''
        logging.info( __name__+ ': Setting the offset of the 4 channels to %s.' %(offset) )

        # self._visainstrument.write('OUTP:COUP:ALL DC')

        self._visainstrument.write('VOLT:OFFS:ALL %s'% offset)
        if self._visainstrument.query('VOLT:OFFS ?') != offset:
            logging.info('The offset wasn\'t set properly')
            raise ValueError('The offset wasn\'t set properly')

    def do_set_amplitude(self, amp, channel=1):
        '''
        Sets the amplitude of the channel.
        Input:
            amp (float): amplitude of the channel in [V]
            channel (int): Channel ID (1, 2, 3 or 4) or 0 if you want to set the amplitude of all 4 channels
        Output:
            None
        '''
        logging.info( __name__+ ': Setting the amplitude of the channel %s to %s.' %( channel, amp))

        # if channel == 0:
        #     self._visainstrument.write('VOLT:AMPL:ALL %s'% amp)
        #     if self._visainstrument.query('VOLT:AMPL:ALL ?') != amp:
        #         logging.info('The amplitude wasn\'t set properly')
        #         raise ValueError('The amplitude wasn\'t set properly')
        # for now: it seems that asking for All amplitude gives an error likely linked to the timeout...

        # we may want to have the possibility to set or get the amplitude of the fours channels at the same time.
        # We may have a problem if there is a difference between self._visainstrument.query('VOLT:AMPL ?')
        # and self._visainstrument.query('VOLT:AMPL:ALL ?')

        if channel in Channels:
            self._visainstrument.write('INST:SEL{0:d}'.format(channel))
            if self._visainstrument.query('INST:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the channel correctly')
            self._visainstrument.write('VOLT:AMPL %s'% amp)
            if self._visainstrument.query('VOLT:AMPL ?') != amp:
                logging.info('The amplitude wasn\'t set properly')

        else:
            logging.info('The invalid Channel ID {0:d} was sent to set_amplitude'.format(channel))
            raise ValueError('The invalid Channel ID {0:d} was sent to set_amplitude. Valid values are 1,2,3,4.'.format(channel))

    def do_get_amplitude(self, channel=1):
        '''
        Gets the amplitude of a channel.
        Input:
            channel (int): Channel ID (1, 2, 3 or 4) or 0 if you want to get the amplitude of all 4 channels
        Output:
            amplitude (float): amplitude of the channel in [V]
        '''
        logging.info( __name__+ ': Getting the amplitude of channel %s' % channel)

        # if channel == 0:
        #     return self._visainstrument.query('VOLT:AMPL:ALL ?')
        # timeout pb... same as above...

        if channel in Channels:
            self._visainstrument.write('INST:SEL{0:d}'.format(channel))
            if self._visainstrument.query('INST:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the channel correctly')

            return self._visainstrument.query('VOLT:AMPL ?')
        else:
            logging.info('The invalid Channel ID {0:d} was sent to get_amplitude'.format(channel))
            raise ValueError('The invalid Channel ID {0:d} was sent to get_amplitude. Valid values are 1,2,3,4.'.format(channel))
            return self._visainstrument.query('VOLT:AMPL ?')

    def do_set_offset(self, offset, channel=1):
        '''
        Sets the offset of the channel.
        Input:
            offset (float): offset of the channel in [V]
            channel (int): Channel ID (1, 2, 3 or 4)
        Output:
            None
        '''
        logging.info( __name__+ ': Setting the offset of the channel %s to %s.' %( channel, offset))

        # if channel == 0:
        #     self._visainstrument.write('VOLT:OFFS:ALL %s'% offset)
        #     if self._visainstrument.query('VOLT:OFFS:ALL ?') != offset:
        #         logging.info('The offset wasn\'t set properly')
        #         raise ValueError('The offsset wasn\'t set properly to all channels by set_offset.')
        # we may want to have the possibility to set or get the offset of the fours channels at the same time.
        # We may have a problem if there is a difference between self._visainstrument.query('VOLT:OFFS ?')
        # and self._visainstrument.query('VOLT:OFFS:ALL ?')

        if channel in Channels:
            self._visainstrument.write('INST:SEL{0:d}'.format(channel))
            if self._visainstrument.query('INST:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the channel correctly')
            self._visainstrument.write('VOLT:OFFS %s'% offset)
        else:
            logging.info('The invalid Channel ID {0:d} was sent to set_offset'.format(channel))
            raise ValueError('The invalid Channel ID {0:d} was sent to set_offset. Valid values are 1,2,3,4.'.format(channel))
            self._visainstrument.write('VOLT:OFFS %s'% offset)

        if self._visainstrument.query('VOLT:OFFS ?') != offset:
            logging.info('The offset wasn\'t set properly')

    def do_get_offset(self, channel=1):
        '''
        Gets the amplitude of a channel.
        Input:
            channel (int): Channel ID (1, 2, 3 or 4) or 0 if you want to get the amplitude of all 4 channels
        Output:
            offset (float): offset of the channel in [V]
        '''
        logging.info( __name__+ ': Getting the amplitude of channel %s' % channel)

        #  if channel == 0:
        #      return self._visainstrument.query('VOLT:OFFS:ALL ?')
        if channel in Channels:
            self._visainstrument.write('INST:SEL{0:d}'.format(channel))
            if self._visainstrument.query('INST:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the channel correctly')
            return self._visainstrument.query('VOLT:OFFS ?')
        else:
            logging.info('The invalid Channel ID {0:d} was sent to get_offset'.format(channel))
            raise ValueError('The invalid Channel ID {0:d} was sent to get_offset. Valid values are 1,2,3,4.'.format(channel))

    def do_set_trigger_level(self, trig_val):
        '''
        Sets the trigger level to trig_val
        Input:
            trig_val (float): trigger level in V. The value should be between -5 and 5.
        Output:
            None
        '''
        logging.info( __name__+ ': Setting the trigger level to %s.' % trig_val)
        self._visainstrument.write('TRIG:LEV %s' % trig_val)

        if self._visainstrument.query('TRIG:LEV ?') != trig_val:
            logging.info('The trigger level wasn\'t set properly')
            raise ValueError('The trigger level wasn\'t set properly to set_trigger_level. Valid value are between -5 and 5.')

    def do_get_trigger_level(self):
        '''
        Gets the trigger level
        Input:
            None
        Output:
            trig_val (float): the trigger level in V
        '''
        logging.info( __name__+ ': Getting the trigger level.' )
        return self._visainstrument.query('TRIG:LEV ?')

    def do_get_marker_status_1_2(self, channel=1):
        '''
        Gets the status of the marker number "channel" of the channel 1 or 2.
        Input:
            channel (int): number of the marker. Valid values are 1, 2
        Output:
            status (1 or 0): 1 means the marker output is ON, 0 means it is OFF.
        '''

        logging.info( __name__+ ': Getting the marker status of the marker %s of the channel 1 or 2.' % (channel))

        if self._visainstrument.query('INST:SEL?') not in (1, 2):
            self._visainstrument.write('INST:SEL {0:d}'.format(1) )
            if self._visainstrument.query('INST:SEL?') != '{0:d}'.format(1):
                logging.info('Default channel 1   was not selected')
                raise ValueError('Default channel 1  was not selected.')

        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number for the marker number. Valid values are 1,2.')


        return self._visainstrument.query('MARK:STAT ?')

    def do_set_marker_status_1_2(self, status, channel=1):
        '''
        Gets the status of the marker numbered "channel" of the channel 1 or 2.
        Input:
            channel (int): number of the marker. Valid values are 1, 2.
            status (1 or 0): 1 means the marker output is ON, 0 means it is OFF.
        Output:
            None
        '''

        logging.info( __name__+ ': Setting the marker status of the marker %s of the channel 1_2 to the status %s.' % (channel, status))
        # if self._visainstrument.query('INST:SEL?') not in (1,2):
        #     logging.info('Channel 1 or 2  was not selected before hand')
        #     raise ValueError('Channel 1 or 2  was not selected before hand.')
        if self._visainstrument.query('INST:SEL?') not in (1,2):
            self._visainstrument.write('INST:SEL {0:d}'.format(1))
            if self._visainstrument.query('INST:SEL?') != '{0:d}'.format(1):
                logging.info('Default channel 1   was not selected ')
                raise ValueError('Default channel 1  was not selected.')

        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number for the marker number. Valid values are 1,2.')

        self._visainstrument.write('MARK:STAT %s' % status)
        if self._visainstrument.query('MARK:STAT ?') != status:
            logging.info('The instrument didn\'t set properly the status %s' % status)
            raise ValueError('The instrument  didn\'t set properly the status %s by set_marker_status' % status)

    def do_get_marker_status_3_4(self, channel=1):
        '''
        Gets the status of the marker number "channel" of the channel 3 or 4.
        Input:
            channel (int): number of the marker. Valid values are 1, 2
        Output:
            status (1 or 0): 1 means the marker output is ON, 0 means it is OFF.
        '''

        logging.info( __name__+ ': Getting the marker status of the marker %s of the channel 3 and 4.' % (channel))

        if self._visainstrument.query('INST:SEL?') not in (3, 4):
            self._visainstrument.write('INST:SEL {0:d}'.format(3) )
            if self._visainstrument.query('INST:SEL?') != '{0:d}'.format(3):
                logging.info('Default channel 3 was not selected')
                raise ValueError('Default channel 3  was not selected.')

        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number for the marker number. Valid values are 1,2.')


        return self._visainstrument.query('MARK:STAT ?')

    def do_set_marker_status_3_4(self, status, channel=1):
        '''
        Gets the status of the marker numbered "channel" of the channel 3 or 4.
        Input:
            channel (int): number of the marker. Valid values are 1, 2.
            status (1 or 0): 1 means the marker output is ON, 0 means it is OFF.
        Output:
            None
        '''

        logging.info( __name__+ ': Setting the marker status of the marker %s of the channel 3 and 4 to the status %s.' % (channel, status))

        if self._visainstrument.query('INST:SEL?') not in (3, 4):
            self._visainstrument.write('INST:SEL {0:d}'.format(3))
            if self._visainstrument.query('INST:SEL?') != '{0:d}'.format(3):
                logging.info('Default channel 3 was not selected ')
                raise ValueError('Default channel 3  was not selected.')

        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number for the marker number. Valid values are 1,2.')

        self._visainstrument.write('MARK:STAT %s' %status )
        if self._visainstrument.query('MARK:STAT ?') != status:
            logging.info('The instrument didn\'t set properly the status %s' % status)
            raise ValueError('The instrument  didn\'t set properly the status %s by set_marker_status' % status)
