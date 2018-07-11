# Tabor_WX1284C.py class
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
_EX_DAT_M2_MASK_NICO = 0x8000
_EX_DAT_M1_MASK_NICO = 0x4000
octet = 8
number_of_bits = 16

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
    complete the driver
    write a cleaner version of 'init_channel'
    make the string formatting uniform
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Tabor_WX1284C.

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

        # Add parameters ######################################################
        self.add_parameter('func_mode', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('run_mode', type=types.StringType,
            option_list=['CONT', 'TRIG', 'GATE'],
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('trigger_source', type=types.StringType,
            option_list=['EXT', 'BUS', 'TIM', 'EVEN'],
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('trigger_mode', type=types.StringType,
            option_list=['NORM', 'OVER'],
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('trigger_timer_mode', type=types.StringType,
            option_list=['TIME', 'DEL'],
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('trigger_timer_time', type=types.FloatType,
            minval = 0.2, maxval=20e6, units='us',
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('output', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 4),channel_prefix='ch%d_')
        self.add_parameter('coupling', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 4),channel_prefix='ch%d_')
        self.add_parameter('channels_synchronised', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            option_list=['ON', 'OFF']
            )
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
            minval=0.05, maxval=4, units='Volts')
        self.add_parameter('offset', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 4), channel_prefix='ch%d_',
            minval=-1, maxval=1, units='Volts')
        self.add_parameter('trigger_level', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-5, maxval=5, units='Volts')
        self.add_parameter('marker_source', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            option_list=['WAVE', 'USER'])
        self.add_parameter('marker_status_1_2', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,2), channel_prefix='m%d_')
        self.add_parameter('marker_status_3_4', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,2), channel_prefix='m%d_')
        self.add_parameter('marker_width_1_2', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,2), channel_prefix='m%d_')
        self.add_parameter('marker_width_3_4', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,2), channel_prefix='m%d_')
        self.add_parameter('marker_delay_1_2', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,2), channel_prefix='m%d_')
        self.add_parameter('marker_delay_3_4', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,2), channel_prefix='m%d_')
        # self.add_parameter('numpoints', type=types.IntType,
            # flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            # minval=192, maxval=16e9, units='Int')
        self.add_parameter('marker_high_1_2', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2), channel_prefix='m%d_',
            minval=0.5, maxval=1.2, units='Volts')
        self.add_parameter('marker_high_3_4', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2), channel_prefix='m%d_',
            minval=0.5, maxval=1.2, units='Volts')
        self.add_parameter('marker_position_1_2', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2), channel_prefix='m%d_')
        self.add_parameter('marker_position_3_4', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2), channel_prefix='m%d_')
        self.add_parameter('trace_mode', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('type_waveform', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 4),channel_prefix='ch%d_')

        # Add functions #######################################################
        self.add_function('clean_visa_open')
        self.add_function('reset')
        self.add_function('clear_err')
        self.add_function('init_channel')
        self.add_function('get_all')
        self.add_function('set_all_amp')
        self.add_function('set_all_offset')
        self.add_function('send_waveform')
        self.add_function('delete_segments')
        self.add_function('delete_segment_i')
        self.add_function('segment_select')

        #opening the visa session #############################################
        self.clean_visa_open()

        if reset:
            self.reset()
            self.clear_err()

        self.get_all()

    # Functions ###############################################################
    def delete_segments(self):
        '''
        This command will delete ALL predefined segments and will clear the entire
        waveform memory space. This command is particularly important in case
        you want to defragment the entire waveform memory and start building
        your waveform segments from scratch.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Deleting waveform memory')
        for i in [1,2,3,4]:
            self.channel_select(i)
            self._visainstrument.write(':TRAC:DEL:ALL')

    def delete_segment_i(self, i):
        '''
        This command will delete the predefined segments i and will clear the
        waveform memory space. This command is particularly important in case
        you want to defragment the entire waveform memory and start building
        your waveform segments from scratch.

        Input:
            i (int or array of int)

        Output:
            None
        '''
        logging.info(__name__ + ' : Deleting some of the waveform memory')
        if len(i) == 1:
            for ch in Channels:
                self.channel_select(ch)
                self._visainstrument.write(':TRAC:DEL {}'.format(i))
        elif len(i) > 1:
            for ch in Channels:
                self.channel_select(ch)
                for j in i:
                    self._visainstrument.write(':TRAC:DEL {}'.format(j))

        else:
            print 'problem with len(i) '

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
        self.get_run_mode()
        self.get_trace_mode()

        self.get_ref_source()
        self.get_ref_freq()


        self.get_clock_source()
        self.get_clock_freq()

        self.get_trigger_level()
        self.get_trigger_mode()
        self.get_trigger_source()
        self.get_trigger_timer_mode()
        self.get_trigger_timer_time()
        self.get_channels_synchronised()

        self.get_marker_source()

        self.get_channels_synchronised()

        for i in Channels:
            self.get('ch%d_output' % i)
            self.get('ch%d_coupling' % i)
            self.get('ch%d_amplitude' % i)
            self.get('ch%d_offset' % i)

        for i in Mark_num:
            self.get('m%d_marker_status_1_2' % i)
            self.get('m%d_marker_status_3_4' % i)
            # self.get('m%d_marker_high_1_2' % i)
            # self.get('m%d_marker_high_3_4' % i)

    def init_channel(self,channel=1):
        '''
        Initializes a given channel to allow proper upload of waveforms and markers:

        Input:
            channel (string): Channel ID

        Output:
            None
        '''
        logging.info( __name__ +' : Initializing channel {0:d}'.format(channel))
        # Select channel
        self.channel_select(channel)
        # Set it to 'User-Mode'
        self._visainstrument.write(":FUNC:MODE USER")
        # Set markers-type to 'user-defined' (external)
        self._visainstrument.write(":SOUR:MARK:SOUR USER")

    def set_all_amp(self, amp):
        '''
        Sets the amplitude of all 4 channels at the same time.
        Input:
            amp (float): amplitude of the channels in [V]
        Output:
            None
        '''
        logging.info( __name__+ ': Setting the amplitude of the 4 channels to %s.' %(amp) )

        self._visainstrument.write('OUTP:COUP:ALL DC')

        self._visainstrument.write('VOLT:ALL %s'% amp)
        if self._visainstrument.query('VOLT ?') != amp:
            logging.info('The amplitude wasn\'t set properly')
            raise ValueError('The amplitude wasn\'t set properly')

    def set_all_offset(self, offset):
        '''
        Sets the offset of all 4 channels at the same time.
        Input:
            offset (float): offset for the channels in [V]
        Output:
            None
        '''
        logging.info( __name__+ ': Setting the offset of the 4 channels to %s.' %(offset) )

        self._visainstrument.write('VOLT:OFFS:ALL %s'% offset)
        if self._visainstrument.query('VOLT:OFFS ?') != offset:
            logging.info('The offset wasn\'t set properly')
            raise ValueError('The offset wasn\'t set properly')

    def send_waveform(self, buffer, ch_id, seg_id):
        '''
        Sets the active waveform segment seg_id at the output connector ch_id
        and then download the waveform data buffer to the WX2184C waveform memory.
        Inputs:
            buffer: the binary data buffer.
            ch_id (int): channel index. Valid values are 1, 2, 3 and 4.
            seg_id (int): segment index. Between 1 and 32 000.
        Output:
            visa-error-code
        '''
        #self._visainstrument.write('TRAC:MODE SING')
        self.channel_select(ch_id)
        self._visainstrument.write(':TRAC:SEL {}'.format(seg_id))
        self._visainstrument.write(':TRAC:DEF {},{}'.format(seg_id,len(buffer)))
        err_code = self.download_binary_data(":TRAC:DATA",  buffer, len(buffer) * buffer.itemsize)
        return err_code

    def segment_select(self,ch_id,seg_id):
        '''
        Sets the active segment seg_id at the output connector ch_id
        '''
        self.channel_select(ch_id)
        self._visainstrument.write(':TRAC:SEL {}'.format(seg_id))

    def inquir(self,command):
        return self._visainstrument.query(command)

    def Write(self,command):
        self._visainstrument.write(command)

    #Parameters ###############################################################

    def do_get_type_waveform(self,channel=1):
        '''
        Use this command to query the type of waveform that will be available at the output connector.
        This command will affect the WX2184C only when the standard waveforms output has been programmed.
        Select the standard waveforms using the func:mode fix command.

        Input:
            channel (string): Channel ID

        Output:
            "SINusoid"  The built-in sine waveform is selected.
            "TRIangle"  The built-in triangular waveform is selected.
            "SQUare"    The built-in square waveform is selected.
            "RAMP"      The built-in ramp waveform is selected.
            "SINC"      The built-in sinc waveform is selected.
            "EXPonential" The built-in exponential waveform is selected.
            "GAUSsian"     The built-in gaussian waveform is selected.
            "DC" The built-in DC waveform is selected.
            "NOISe" The built-in noise waveform is selected.
        '''
        logging.info( __name__ +' : Getting the waveform of channel {0:d}'.format(channel))
        # Select channel
        self.channel_select(channel)
        # Set it to 'User-Mode'
        return self._visainstrument.query(":FUNC:SHAP ?")

    def do_set_type_waveform(self,waveform,channel=1):
        '''
        Use this command to set the type of waveform that will be available at the output connector.
        This command will affect the WX2184C only when the standard waveforms output has been programmed.
        Select the standard waveforms using the func:mode fix command.

        Input:
            channel (string): Channel ID
            "SINusoid"  The built-in sine waveform is selected.
            "TRIangle"  The built-in triangular waveform is selected.
            "SQUare"    The built-in square waveform is selected.
            "RAMP"      The built-in ramp waveform is selected.
            "SINC"      The built-in sinc waveform is selected.
            "EXPonential" The built-in exponential waveform is selected.
            "GAUSsian"     The built-in gaussian waveform is selected.
            "DC" The built-in DC waveform is selected.
            "NOISe" The built-in noise waveform is selected.
        Output:
            NONE
        '''
        logging.info( __name__ +' : Setting the waveform of channel {0:d}'.format(channel))
        # Select channel
        self.channel_select(channel)
        # Set it to 'User-Mode'
        if waveform.upper() in ('SIN','TRI','SQU','RAMP','SINC','EXP','GAUS','DC','NOIS'):
            self._visainstrument.write('FUNC:SHAP {}'.format(waveform))
            if self._visainstrument.query('FUNC:SHAP?') != waveform:
                logging.info('Instrument did not select the output waveform correctly')
        else:
            logging.info('The invalid value {} was sent to waveform method'.format(waveform))

            raise ValueError('The invalid value {} was sent to waveform method. Valid values are \'SIN\',\'TRI\',\'SQU\',\'RAMP\',\'SINC\',\'EXP\',\'GAUS\',\'DC\',\'NOIS\'.'.format(waveform))


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

    def do_get_run_mode(self):
        '''
        Gets the run mode of the instrument

        Input:
            None

        Output:
            Trigger mode (string): 'CONT', 'TRIG', 'GATE' depending on the mode
        '''
        logging.info( '{} : Getting the run mode'.format(__name__))
        if self._visainstrument.query('INIT:CONT?') == 'ON':
            return 'CONT'
        elif self._visainstrument.query('INIT:GATE?') == 'ON':
            return 'GATE'
        else:
            return 'TRIG'

    def do_set_run_mode(self, value='TRIG'):
        '''
        Sets the run mode of the instrument

        Input:
            Trigger mode (string): 'CONT', 'TRIG', 'GATE' depending on the mode

        Output:
            None
        '''
        logging.info( '{} : Setting the run mode to {}'.format(__name__,value))
        if value.upper() == 'CONT':
            self._visainstrument.write('INIT:CONT ON')
            if self._visainstrument.query('INIT:CONT?') != 'ON':
                logging.info('Run mode wasn\'t set properly')
        elif value.upper() == 'TRIG':
            self._visainstrument.write('INIT:CONT OFF')
            # self._visainstrument.write('INIT:GATE OFF')
            if self._visainstrument.query('INIT:CONT?') != 'OFF':
                logging.info('Run mode wasn\'t set properly')
            # elif self._visainstrument.query('INIT:GATE?') != 'OFF':
            #     logging.info('Run mode wasn\'t set properly')
        elif value.upper() == 'GATE':
            # self._visainstrument.write('INIT:CONT OFF')
            self._visainstrument.write('INIT:GATE ON')
            # if self._visainstrument.query('INIT:CONT?') != 'OFF':
            #     logging.info('Run mode wasn\'t set properly')
            if self._visainstrument.query('INIT:GATE?') != 'ON':
                logging.info('Run mode wasn\'t set properly')
        else:
            logging.info('The invalid value {} was sent to set_run_mode method'.format(value))
            raise ValueError('The invalid value {} was sent to set_run_mode method. Valid values are \'CONT\', \'TRIG\', \'GATE\'.'.format(value))

    def do_get_trigger_source(self):
        '''
        Get the trigger source of the instrument

        Input:
            None

        Output:
            Trigger source (string): 'EXT', 'BUS', 'TIM', 'EVEN'.
        '''

        logging.info( '{} : Getting the trigger source')
        return self._visainstrument.query(':TRIG:SOUR:ADV?')

    def do_set_trigger_source(self, value='TIM'):
        '''
            Use this command to set or query the source of the trigger event
            that will stimulate the WX2184C to generate waveforms. The source
            advance command will affect the generator only after it has been
            programmed to operate in trigger run mode. Modify the WX2184C to
            trigger run mode using the init:cont off
            command.

        Input:
            Trigger source (string): 'EXT', 'BUS', 'TIM', 'EVEN'.

        Output:
            None
        '''

        logging.info( '{} : Setting the trigger source to {}'.format(__name__,value))
        self._visainstrument.write(':TRIG:SOUR:ADV '+str(value.upper()))

        if self._visainstrument.query(':TRIG:SOUR:ADV?') != value.upper():

            logging.info('Trigger source was not set properly')
            raise ValueError('Trigger source was not set properly')

    def do_get_trigger_mode(self):
        '''
        Get the trigger mode of the instrument

        Input:
            None

        Output:
            Trigger mode (string): 'NORM', 'OVER'.
        '''

        logging.info( '{} : Getting the trigger mode')
        return self._visainstrument.query(':TRIG:MODE?')

    def do_set_trigger_mode(self, value='NORM'):
        '''
            Use this command to define or query the trigger mode. In normal mode,
            the first trigger activates the output and consecutive triggers are
            ignored for the duration of the output waveform. In override mode,
            the first trigger activates the output and consecutive triggers
            restart the output waveform, regardless if the current waveform has
            been completed or not.

        Input:
            Trigger source (string): 'EXT', 'BUS', 'TIM', 'EVEN'.

        Output:
            None
        '''

        logging.info( '{} : Setting the trigger mode to {}'.format(__name__,value))
        self._visainstrument.write(':TRIG:MODE '+str(value.upper()))

        if self._visainstrument.query(':TRIG:MODE?') != value.upper():

            logging.info('Trigger mode was not set properly')
            raise ValueError('Trigger mode was not set properly')

    def do_get_trigger_timer_mode(self):
        '''
        Get the trigger timer mode of the instrument

        Input:
            None

        Output:
            Trigger mode (string): 'TIME', 'DEL'.
        '''

        logging.info( '{} : Getting the trigger timer mode')
        return self._visainstrument.query(':TRIG:TIM:MODE?')

    def do_set_trigger_timer_mode(self, value='TIME'):
        '''
            Use this command to set or query the mode that the internal trigger
            generator will operate. Timed defines start-to-start triggers and
            Delayed defines end-to-start triggers. The timer commands will
            affect the generator only after it has been programmed to operate
            in timer mode. Modify the WX2184C to trigger run mode using the
            init:cont off command and program the internal timer using the
            trig:tim command.

        Input:
            Trigger source (string): 'TIME', 'DEL'.

        Output:
            None
        '''

        logging.info( '{} : Setting the trigger timer mode to {}'.format(__name__,value))
        self._visainstrument.write(':TRIG:TIM:MODE '+str(value.upper()))

        if self._visainstrument.query(':TRIG:TIM:MODE?') != value.upper():

            logging.info('Trigger timer mode was not set properly')
            raise ValueError('Trigger timer mode was not set properly')

    def do_get_trigger_timer_time(self):
        '''
        Get the trigger timer time of the instrument

        Input:
            None

        Output:
            Trigger timer time (float): The period in us.
        '''

        logging.info( '{} : Getting the trigger timer time')
        return float(self._visainstrument.query(':TRIG:TIM:TIME?'))*1e6

    def do_set_trigger_timer_time(self, period):
        '''
            Use this command to set the period of the internal timed
            trigger generator. This value is associated with the internal
            trigger run mode only and has no effect on other trigger modes.
            The internal trigger generator is a free-running oscillator,
            asynchronous with the frequency of the output waveform. The timer
            intervals are measured from waveform start to waveform start.

        Input:
            Trigger timer time (float): The period in us.

        Output:
            None
        '''

        logging.info( '{} : Setting the trigger timer time to {}'.format(__name__,period))
        self._visainstrument.write(':TRIG:TIM:TIME '+str(period*1e-6))

        if round(float(self._visainstrument.query(':TRIG:TIM:TIME?'))*1e6,0) != round(period,0):
            logging.info('Trigger timer time was not set properly')
            raise ValueError('Trigger timer time was not set properly')



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

        self.channel_select(channel)
        if state in ('ON','OFF'):
            self._visainstrument.write('OUTP{}'.format(state))
            if self._visainstrument.query('OUTP?') != state:
                logging.info('ON/OFF wasn\'t set properly')
        else:
            logging.info('The invalid state {} was sent to set_output'.format(state))
            raise ValueError('The invalid state {} was sent to set_output. Valid values are \'ON\' or \'OFF\'.'.format(state))

    def do_get_output(self, channel=1):
        '''
        Get the state of a given channel

        Input:
            channel (int): Channel ID

        Output:
            state (string): 'ON' or 'OFF'
        '''

        logging.info( __name__+' : Getting the output state of channel %s'%( channel))

        self.channel_select(channel)
        return self._visainstrument.query('OUTP?')

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

        self.channel_select(channel)
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
        self.channel_select(channel)

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

    def do_set_amplitude(self, amp, channel):
        '''
        Sets the amplitude of the channel.
        Input:
            amp (float): amplitude of the channel in [V]
        Output:
            None
        '''
        logging.info( __name__+ ': Setting the amplitude of the channel %s to %s.' %( channel, amp))

        self.channel_select(channel)
        if self.do_get_coupling(channel) == 'HV':
            self._visainstrument.write('VOLT:AMPL:HV %s'% amp)
            if self._visainstrument.query('VOLT:AMPL:HV ?') != amp:
                logging.info('The amplitude wasn\'t set properly')
        else:
            self._visainstrument.write('VOLT:AMPL:DC %s'% amp)
            if self._visainstrument.query('VOLT:AMPL:DC ?') != amp:
                logging.info('The amplitude wasn\'t set properly')

    def do_get_amplitude(self, channel):
        '''
        Gets the amplitude of a channel.
        Input:
        #    channel (int): Channel ID (1, 2, 3 or 4) or 0 if you want to get the amplitude of all 4 channels
        Output:
            amplitude (float): amplitude of the channel in [V]
        '''
        logging.info( __name__+ ': Getting the amplitude of channel %s' % channel)



        self.channel_select(channel)
        if self.do_get_coupling(channel) == 'HV':
            return self._visainstrument.query('VOLT:AMPL:HV ?')
        else:
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

        self.channel_select(channel)
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

        self.channel_select(channel)
        return self._visainstrument.query('VOLT:OFFS ?')

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

        if float(self._visainstrument.query('TRIG:LEV ?')) != trig_val:
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

    def do_set_marker_source(self, source='WAVE'):
        '''
        Use this command to set or query the source of the marker data. The
        WAVE marker data is a single marker transition with a varying position
        and width, similar to a SYNC output. The USER marker data enables the
        user to program multiple marker transition, similar to a separate data
        line, for example a clock. The USER data can only be programmed via a
        remote interface. The marker width (or length) is limited to the
        relevant segment length and has a resolution of 2.

        Input:
            source (string): 'WAVE', 'USER'
        Output:
            None
        '''
        logging.info( __name__+ ': Setting the marker source to %s.' % source)
        self._visainstrument.write('MARK:SOUR %s' % source)

        if self._visainstrument.query('MARK:SOUR?') != source.upper():
            logging.info('The marker source wasn\'t set properly')
            raise ValueError('The marker source wasn\'t set properly to set_marker_source. Valid value are \'WAVE\', \'USER\'.')

    def do_get_marker_source(self):
        '''
        Gets the marker source.

        Input:
            None
        Output:
            source (string): 'WAVE', 'USER'
        '''
        logging.info( __name__+ ': Getting the marker source.' )
        return self._visainstrument.query('MARK:SOUR?')

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
            self.channel_select(1)

        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))
            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for this marker. Valid values are 1,2.')


        return self._visainstrument.query('MARK:STAT ?')

    def do_set_marker_status_1_2(self, status, channel=1):
        '''
        sets the status of the marker numbered "channel" of the channel 1 or 2.
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
            self.channel_select(1)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))
            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for this marker. Valid values are 1,2.')

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
            self.channel_select(3)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for this marker. Valid values are 1, 2.')


        return self._visainstrument.query('MARK:STAT ?')

    def do_set_marker_status_3_4(self, status, channel=1):
        '''
        sets the status of the marker numbered "channel" of the channel 3 or 4.
        Input:
            channel (int): number of the marker. Valid values are 1, 2.
            status (1 or 0): 1 means the marker output is ON, 0 means it is OFF.
        Output:
            None
        '''

        logging.info( __name__+ ': Setting the marker status of the marker %s of the channel 3 and 4 to the status %s.' % (channel, status))

        if self._visainstrument.query('INST:SEL?') not in (3, 4):
            self.channel_select(3)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))
            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for this marker. Valid values are 1, 2.')

        self._visainstrument.write('MARK:STAT %s' % status )
        print status
        print self._visainstrument.query('MARK:STAT ?')
        if self._visainstrument.query('MARK:STAT ?') != status:
            logging.info('The instrument didn\'t set properly the status %s' % status)
            raise ValueError('The instrument  didn\'t set properly the status %s by set_marker_status' % status)

    def do_get_marker_high_1_2(self, channel=1):
        '''
        Gets the status of the marker number "channel" of the channel 1 or 2.
        Input:
            channel (int): number of the marker. Valid values are 1, 2
        Output:
            high_level (float): high level of the marker output in volt.
        '''

        logging.info( __name__+ ': Getting the marker high level of the marker %s of the channel 1 or 2.' % (channel))

        if self._visainstrument.query('INST:SEL?') not in (1, 2):
            self.channel_select(1)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 1,2.')


        return self._visainstrument.query('MARK:VOLT:HIGH?')

    def do_set_marker_high_1_2(self, high_level, channel=1):
        '''

        Input:
            channel (int): number of the marker. Valid values are 1, 2.
            high_level (float): high level of the marker output in volt. Valid values are between 0.5 and 1.2.
        Output:
            None
        '''

        logging.info( __name__+ ': Setting the marker high level of the marker %s of the channel 1_2 to %s.' % (channel, high_level))



        if self._visainstrument.query('INST:SEL?') not in (1,2):
            self.channel_select(1)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 1,2.')

        self._visainstrument.write('MARK:VOLT:HIGH %s' % high_level)
        if np.float(self._visainstrument.query('MARK:VOLT:HIGH?')) != high_level:
            logging.info('The instrument didn\'t set properly the high_level %s' % high_level)
            raise ValueError('The instrument  didn\'t set properly the high_level %s by set_marker_high' % high_level)

    def do_get_marker_high_3_4(self, channel=1):
        '''
        Gets the amplitude level of the marker number "channel" of the channel 3 or 4.
        Input:
            channel (int): number of the marker. Valid values are 1, 2
        Output:
            high_level (float): high level of the marker output in volt.
        '''

        logging.info( __name__+ ': Getting the marker high level of the marker %s of the channel 3_4.' % (channel))

        if self._visainstrument.query('INST:SEL?') not in (3, 4):
            self.channel_select(3)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 3, 4.')


        return self._visainstrument.query('MARK:VOLT:HIGH?')

    def do_set_marker_high_3_4(self, high_level, channel=1):
        '''
        Sets the amplitude level of the marker number "channel" of the channel 3 or 4.
        Input:
            channel (int): number of the marker. Valid values are 1, 2.
            high_level (float): high level of the marker output in volt. Valid values are between 0.5 and 1.2.
        Output:
            None
        '''

        logging.info( __name__+ ': Setting the marker high level of the marker %s of the channel 3_4 to %s.' % (channel, high_level))


        if self._visainstrument.query('INST:SEL?') not in (3,4):
            self.channel_select(3)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 1, 2.')

        self._visainstrument.write('MARK:VOLT:HIGH %s' % high_level)
        if np.float(self._visainstrument.query('MARK:VOLT:HIGH ?')) != high_level:
            logging.info('The instrument didn\'t set properly the high_level %s' % high_level)
            raise ValueError('The instrument  didn\'t set properly the high_level %s by set_marker_high' % high_level)

    def do_get_marker_position_1_2(self, channel=1):
        '''
        Gets the position of the marker output.
        The position is defined from the waveform first point in units of waveform points (sample clock periods).
        Input:
            None.

        Output:
            The WX2184C will return the present marker position value in units of waveform points.
        '''

        logging.info( __name__+ ': Getting the marker position of the marker %s of the channel 1_2.' % (channel))


        if self._visainstrument.query('INST:SEL?') not in (1,2):
            self.channel_select(2)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 1, 2.')

        return self._visainstrument.query('MARK:POS ?')

    def do_set_marker_position_1_2(self,position, channel=1):
        '''
        Sets the position of the marker output.
        The position is defined from the waveform first point in units of waveform points (sample clock periods).
        Will set marker position relative to the waveform start point in units of waveform points. The position range is
        from 0 to the last point of the waveform, minus 4. You can program the position with increments of 2 points.
        Input:
            position (int): position of the marker in units of wave form points

        Output:
            NONE
        '''

        logging.info( __name__+ ': Setting the marker position of the marker %s of the channel 1_2.' % (channel))


        if self._visainstrument.query('INST:SEL?') not in (1,2):
            self.channel_select(1)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 1, 2.')

        self._visainstrument.write('MARK:POS %i' % position)
        if np.int_(self._visainstrument.query('MARK:POS ?')) != np.int_(position):
            logging.info('The instrument didn\'t set properly the position %s' % position)
            raise ValueError('The instrument  didn\'t set properly the position %s by set_marker_position' % position)


    def do_get_marker_position_3_4(self, channel=1):
        '''
        Gets the position of the marker output.
        The position is defined from the waveform first point in units of waveform points (sample clock periods).
        Input:
            None.

        Output:
            The WX2184C will return the present marker position value in units of waveform points.
        '''

        logging.info( __name__+ ': Getting the marker position of the marker %s of the channel 1_2.' % (channel))


        if self._visainstrument.query('INST:SEL?') not in (3,4):
            self.channel_select(3)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 3, 4.')

        return self._visainstrument.query('MARK:POS ?')

    def do_set_marker_position_3_4(self,position, channel=1):
        '''
        Sets the position of the marker output.
        The position is defined from the waveform first point in units of waveform points (sample clock periods).
        Will set marker position relative to the waveform start point in units of waveform points. The position range is
        from 0 to the last point of the waveform, minus 4. You can program the position with increments of 2 points.
        Input:
            position (int): position of the marker in units of wave form points

        Output:
            NONE
        '''

        logging.info( __name__+ ': Setting the marker position of the marker %s of the channel 3_4.' % (channel))


        if self._visainstrument.query('INST:SEL?') not in (3,4):
            self.channel_select(3)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 1, 2.')

        self._visainstrument.write('MARK:POS  %i' % position)
        if np.int_(self._visainstrument.query('MARK:POS ?')) != np.int_(position):
            logging.info('The instrument didn\'t set properly the position %s' % position)
            raise ValueError('The instrument  didn\'t set properly the position %s by set_marker_position' % position)

    def do_set_marker_width_1_2(self,width, channel=1):
        '''
        Use this command to set the width of the
        marker output. The width is defined in units of waveform points (sample clock periods).
        Will set marker width in units of waveform points. The width range is from 0 to the last
        point of the waveform less 4. You can program the width in increments of 2 points. Note
        that you can program D14 and D15 to create multiple markers along the waveform length however,
        in this case, you must remove the default marker from the waveform map by setting the width
        parameter mark:wid 0.
        Input:
            width (int): width of the marker in units of wave form points. Minium 2.
                         Default:4

        Output:
            NONE
        '''

        logging.info( __name__+ ': Setting the marker width of the marker %s of the channel 1_2.' % (channel))


        if self._visainstrument.query('INST:SEL?') not in (1,2):
            self.channel_select(1)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 1, 2.')

        self._visainstrument.write('MARK:WIDTH %i' % np.int_(width))
        if self._visainstrument.query('MARK:WIDTH ?') != width:
            logging.info('The instrument didn\'t set properly the width %s' % width)
            raise ValueError('The instrument  didn\'t set properly the width %s by set_marker_width' % width)


    def do_get_marker_width_1_2(self, channel=1):
        '''
        Use this command to query the width of the
        marker output. The width is defined in units of waveform points (sample clock periods).
        Will set marker width in units of waveform points. The width range is from 0 to the last
        point of the waveform less 4. You can program the width in increments of 2 points. Note
        that you can program D14 and D15 to create multiple markers along the waveform length however,
        in this case, you must remove the default marker from the waveform map by setting the width
        parameter mark:wid 0.
        Input:
            NONE

        Output (int): width of the marker in units of wave form points. Minium 2.
                     Default:4
            NONE
        '''

        logging.info( __name__+ ': Setting the marker width of the marker %s of the channel 1_2.' % (channel))


        if self._visainstrument.query('INST:SEL?') not in (1,2):
            self.channel_select(1)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 1, 2.')

        return self._visainstrument.query('MARK:WIDTH ?')


    def do_set_marker_width_3_4(self,width, channel=1):
        '''
        Use this command to set the width of the
        marker output. The width is defined in units of waveform points (sample clock periods).
        Will set marker width in units of waveform points. The width range is from 0 to the last
        point of the waveform less 4. You can program the width in increments of 2 points. Note
        that you can program D14 and D15 to create multiple markers along the waveform length however,
        in this case, you must remove the default marker from the waveform map by setting the width
        parameter mark:wid 0.
        Input:
            width (int): width of the marker in units of wave form points. Minium 2.
                         Default:4

        Output:
            NONE
        '''

        logging.info( __name__+ ': Setting the marker width of the marker %s of the channel 3_4.' % (channel))


        if self._visainstrument.query('INST:SEL?') not in (3,4):
            self.channel_select(3)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 1, 2.')

        self._visainstrument.write('MARK:WIDTH %i' % np.int_(width))
        if self._visainstrument.query('MARK:WIDTH ?') != width:
            logging.info('The instrument didn\'t set properly the width %s' % width)
            raise ValueError('The instrument  didn\'t set properly the width %s by set_marker_width' % width)

    def do_get_marker_width_3_4(self, channel=1):
        '''
        Use this command to query the width of the
        marker output. The width is defined in units of waveform points (sample clock periods).
        Will set marker width in units of waveform points. The width range is from 0 to the last
        point of the waveform less 4. You can program the width in increments of 2 points. Note
        that you can program D14 and D15 to create multiple markers along the waveform length however,
        in this case, you must remove the default marker from the waveform map by setting the width
        parameter mark:wid 0.
        Input:
            NONE

        Output (int): width of the marker in units of wave form points. Minium 2.
                     Default:4
            NONE
        '''

        logging.info( __name__+ ': Setting the marker width of the marker %s of the channel 3_4.' % (channel))


        if self._visainstrument.query('INST:SEL?') not in (3,4):
            self.channel_select(3)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 3, 4.')

        return self._visainstrument.query('MARK:WIDTH ?')

    def do_get_marker_delay_1_2(self, channel=1):
        '''
        Use this command to query the delay
        of the marker output of channel 1_2. The delay is measured from the sync output in units of seconds.
        Input:
            NONE

        Output (float): marker delay value in units of seconds. RAnge: 0 to 3e-9

        '''

        logging.info( __name__+ ': Setting the marker delay of the marker %s of the channel 1_2.' % (channel))


        if self._visainstrument.query('INST:SEL?') not in (1,2):
            self.channel_select(1)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 1, 2.')

        return self._visainstrument.query('MARK:DEL ?')

    def do_set_marker_delay_1_2(self, delay,channel=1):
        '''
        Use this command to set the delay
        of the marker output of channel 1_2. The delay is measured from the sync output in units of seconds.
        Input:
            NONE

        Output (float): marker delay value in units of seconds, Range: 0 to 3e-9

        '''

        logging.info( __name__+ ': Setting the marker delay of the marker %s of the channel 1_2.' % (channel))


        if self._visainstrument.query('INST:SEL?') not in (1,2):
            self.channel_select(1)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 1, 2.')

        self._visainstrument.write('MARK:DEL %s' % delay)
        if np.float(self._visainstrument.query('MARK:DEL ?')) !=np.float(delay) :
            logging.info('The instrument didn\'t set properly the delay %s' % delay)
            raise ValueError('The instrument  didn\'t set properly the high_level %s by set_marker_delay' % delay)

    def do_set_marker_delay_3_4(self, delay,channel=1):
        '''
        Use this command to set the delay
        of the marker output of channel 1_2. The delay is measured from the sync output in units of seconds.
        Input:
            NONE

        Output (float): marker delay value in units of seconds, Range: 0 to 3e-9

        '''

        logging.info( __name__+ ': Setting the marker delay of the marker %s of the channel 3_4.' % (channel))


        if self._visainstrument.query('INST:SEL?') not in (3,4):
            self.channel_select(3)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 3, 4.')

        self._visainstrument.write('MARK:DEL %s' % delay)
        if np.float(self._visainstrument.query('MARK:DEL ?')) !=np.float(delay) :
            logging.info('The instrument didn\'t set properly the delay %s' % delay)
            raise ValueError('The instrument  didn\'t set properly the delay %s by set_marker_delay' % delay)

    def do_get_marker_delay_3_4(self, channel=1):
        '''
        Use this command to query the delay
        of the marker output of channel 3_4. The delay is measured from the sync output in units of seconds.
        Input:
            NONE

        Output (float): marker delay value in units of seconds. Range: 0 to 3e-9

        '''

        logging.info( __name__+ ': Setting the marker delay of the marker %s of the channel 3_4.' % (channel))


        if self._visainstrument.query('INST:SEL?') not in (3,4):
            self.channel_select(3)
        if channel in Mark_num:
            self._visainstrument.write('MARK:SEL{0:d}'.format(channel))

            if self._visainstrument.query('MARK:SEL?') != '{0:d}'.format(channel):
                logging.info('Instrument did not select the marker correctly')
                raise ValueError('The marker {0:d} was not properly selected.'.format(channel))
        else:
            logging.info('Wrong number of the channel for the marker. Valid values are 3, 4.')

        return self._visainstrument.query('MARK:DEL ?')

    def do_get_trace_mode(self):
        '''
        Gets how the arbitrary waveform is downloaded to the unit memory.
        Input:
            None
        Output:
            mode (string): possible values are 'SINGl' 'DUPL' 'ZER'  'COMB'
        '''
        logging.info( __name__+ ': Getting how the arbitrary waveform is downloaded to the unit memory.')
        return self._visainstrument.query(':TRAC:MODE ?')

    def do_set_trace_mode(self, mode='SING'):
        '''
        Sets how the arbitrary waveform is downloaded to the unit memory.
        Input:
            mode (string): possible values are 'SING' 'DUPL' 'ZER'  'COMB'
        Output:
            none
        '''
        logging.info( __name__+ ': Setting how the arbitrary waveform is downloaded to the unit memory.')

        if mode.upper() in ('SING', 'DUPL', 'ZER', 'COMB'):
            self._visainstrument.write(':TRAC:MODE %s' %mode.upper())

            if self._visainstrument.query(':TRAC:MODE ?') != mode.upper():
                logging.info('Instrument did not set correctly the mode of the trace arbitrary waveform')
                raise ValueError('Instrument did not set correctly the mode of the trace arbitrary waveform')
        else:
            logging.info('The invalid value %s was sent to set_clock_source' % mode.upper())
            raise ValueError('The invalid value %s was sent to set_clock_source. Valid values are \'SING\' , \'DUPL\', \'ZER\' or \'COMB\'.' % mode.upper())

    def do_set_channels_synchronised(self,synchronised='ON'):
        '''
        Sets or queries the couple state of the synchronized channels. Use this command to cause all four channels
        to synchronize. Following this command, the sample clock of channel 1 will feed the other channels and
        the start phase of the channels 3 and 4 channels will lock to the start phase of channels 1 and 2 waveforms.
        Input:
            mode (string): possible values are 'ON' or 'OFF'
        Output:
            none
        '''
        logging.info( __name__+ ': Setting the couple state of the synchronized channels')

        if synchronised.upper() in ('ON', 'OFF'):
            self._visainstrument.write('INST:COUP:STAT %s' % synchronised.upper())

            if self._visainstrument.query('INST:COUP:STAT ?') != synchronised.upper():
                logging.info('Instrument did not synchronise the channels')
                raise ValueError('Instrument did not synchronise the channels')
        else:
            logging.info('The invalid value %s was sent to set_channels_synchronisation' % synchronised.upper())
            raise ValueError('The invalid value %s was sent to set_channels_synchronisation. Valid values are \'ON\' or \'OFF\'.' % synchronised.upper())

    def do_get_channels_synchronised(self):
        '''
        Gets the couple state of the synchronized channels.
        Input:
            NONE
        Output:
            (integer): returns '0' if synchronisation is OFF and '1' if synchronisation is 'ON'
        '''
        logging.info( __name__+ ': Getting the couple state of the synchronisation')
        return self._visainstrument.query('INST:COUP:STAT ?')

    def channel_select(self,ch_id):
        """
        Select the active channel method.
        Input:
            ch_id (int): index of the channel to select.
        Output:
            None
        """
        if ch_id in Channels:
            self._visainstrument.write('INST:SEL{}'.format(ch_id))
            if self._visainstrument.query('INST:SEL?') != '{}'.format(ch_id):
                print('''Instrument did not select the channel correctly''')
        else:
            print('''The invalid value {} was sent to channel_select method''').format(ch_id)
            logging.info('The invalid Channel ID {0:d} was sent to set_amplitude'.format(ch_id))
            raise ValueError('The invalid Channel ID {0:d} was sent to set_amplitude. Valid values are 1,2,3,4.'.format(ch_id))

    def download_binary_data(self, msg, bin_dat, dat_size):
        """
        Download binary data to device.
        Notes:
          1. The caller needs not add the binary-data header (#<data-length>)
          2. The preceding-message is usually a SCPI string (e.g :'TRAC:DATA')

        Inputs:
            msg: the preceding string message.
            bin_dat: the binary data buffer.
            dat_size: the data-size in bytes.
        Output:
            visa-error-code.
        """

        intf_type = self._visainstrument.get_visa_attribute(vc.VI_ATTR_INTF_TYPE)
        if intf_type == vc.VI_INTF_GPIB:
            _ = self._visainstrument.write("*OPC?")
            for _ in range(2000):
                status_byte = self._visainstrument.stb
                if (status_byte & 0x10) == 0x10:
                    break
            _ = self._visainstrument.read()
            max_chunk_size = 30000L
            orig_tmout = self._visainstrument.timeout
            if orig_tmout < dat_size / 20:
                self._visainstrument.timeout = long(dat_size / 20)
        else:
            max_chunk_size = 256000L

        dat_sz_str = "{0:d}".format(dat_size)
        dat_header = msg + " #{0:d}{1}".format(len(dat_sz_str), dat_sz_str)

        ret = 0L
        p_dat = ctypes.cast(dat_header, ctypes.POINTER(ctypes.c_byte))
        ul_sz = ctypes.c_ulong(len(dat_header))
        p_ret = ctypes.cast(ret, ctypes.POINTER(ctypes.c_ulong))
        err_code = self._visainstrument.visalib.viWrite(self._visainstrument.session, p_dat, ul_sz, p_ret)

        if err_code < 0:
            print "Failed to write binary-data header. error-code=0x{0:x}".format(err_code)
            return err_code

        ul_sz = ctypes.c_ulong(dat_size)
        if isinstance(bin_dat, np.ndarray):
            p_dat = bin_dat.ctypes.data_as(ctypes.POINTER(ctypes.c_byte))
        else:
            p_dat = ctypes.cast(bin_dat, ctypes.POINTER(ctypes.c_byte))

        if dat_size <= max_chunk_size:
            err_code = self._visainstrument.visalib.viWrite(self._visainstrument.session, p_dat, ul_sz, p_ret)
        else:
            wr_offs = 0
            while wr_offs < dat_size:
                chunk_sz = min(max_chunk_size, dat_size - wr_offs)
                ul_sz = ctypes.c_ulong(chunk_sz)
                ptr = ctypes.cast(ctypes.addressof(p_dat.contents) + wr_offs, ctypes.POINTER(ctypes.c_byte))
                err_code = self._visainstrument.visalib.viWrite(self._visainstrument.session, ptr, ul_sz, p_ret)
                if err_code < 0:
                    break
                wr_offs = wr_offs + chunk_sz

        #self._visainstrument.clear()
        if err_code < 0:
            print "Failed to write binary-data. error-code=0x{0:x}".format(err_code)

        return err_code

    def add_marker_flag(self, marker_idx, start_point, len_in_pts, buffer):
        """
        Add marker flag to given pulse at the specified time-interval.
        Inputs:
            :param marker_idx: marker index (either 0 or 1)
            :param start_time: the marker start time
            :param time_span: the marker time span
        Output:
            None
        """
        marker_idx = int(marker_idx)
        ex_dat = 0
        if marker_idx == 0:
            ex_dat = _EX_DAT_MARKER_1_MASK
        elif marker_idx == 1:
            ex_dat = _EX_DAT_MARKER_2_MASK
        else:
            raise TypeError("marker_idx should be either 0 or 1")

        if start_point % MARKER_QUANTUM != 0 or len_in_pts % MARKER_QUANTUM != 0:
            warnings.warn("the marker-interval was rounded!")
            start_point = (start_point // MARKER_QUANTUM) * MARKER_QUANTUM
            len_in_pts = (len_in_pts // MARKER_QUANTUM) * MARKER_QUANTUM

        # intervals = self._normalize_interval(start_point, len_in_pts)
        intervals= np.arange(start_point,start_point+len_in_pts, MARKER_QUANTUM)
        self._add_extra_data(ex_dat, intervals)

    def _normalize_interval(self, intrv_start, intrv_len):
        """Normalize sub-interval of the waveform interval.

        The sub-interval is relative to single-period of the waveform,
        (but may be offset, so not necessarily contained in the 1st period).

        The returnd normalized-intervals list contains zero or more
        2-tuples of the form: `(<start_point_index>,<length in points>)`
        that represent sub-intervals of the duplicated waveform.

        :param intrv_start: the sub-interval start point index.
        :param intrv_len: the sub-interval length in points.
        :returns: list of normalized-intervals in the waveform intervals.
        """
        if intrv_len >= self.period_len:
            return [(0, self.period_len * self.num_periods)]
        if intrv_len < 1:
            return []
        intrv_end = intrv_start + intrv_len

        if intrv_start >= 0 and intrv_end <= self.period_len:
            if self.is_for_run_mode:
                return [(intrv_start, intrv_len)]
            else:
                return [(intrv_start + i * self.period_len, intrv_len)
                        for i in range(self.num_periods)]

        if self.is_for_run_mode:
            intrv_start = max(intrv_start, Decimal(0))
            intrv_end = min(intrv_end, self.period_len * self.num_periods)
            if intrv_end <= intrv_start:
                return []
            return [(intrv_start, intrv_end - intrv_start)]

        idxs = [intrv_start, intrv_end]

        q = intrv_start / self.period_len
        q = q.to_integral_exact(rounding=ROUND_FLOOR)
        if not q.is_zero():
            for i in range(len(idxs)):
                idxs[i] = idxs[i] - q * self.period_len
                idxs[i] = idxs[i].to_integral()
                idxs[i] = max(idxs[i], Decimal(0))
                idxs[i] = min(idxs[i], self.period_len)

        if idxs[0] == idxs[1]:
            return []

        if idxs[0] < idxs[1]:
            return [(idxs[0] + i * self.period_len, idxs[1] - idxs[0])
                    for i in range(self.num_periods)]

        intervals = []
        for i in range(self.num_periods):
            intrv_1 = (i * self.period_len, idxs[1] + i * self.period_len)
            intrv_2 = (idxs[0] + i * self.period_len, (i + 1) * self.period_len)
            intervals.append(intrv_1)
            intervals.append(intrv_2)
        return intervals

    def _add_extra_data(self, ex_dat, intervals):
        """
        Add extra-data to at the specified intervals of the waveform.

        The 'extra-data' is a 32-bits value composed of:
          - markers-flags (2-bits)
          - digital-data mask (28-bits)
          - spare (2-bits)

        The intervals-list consists of zero or more 2-tuples
        of the form: `(<first_point_index>,<length_in_points>)`
        that represent normalized intervals in the duplicated waveform.


        :param ex_dat: the extra-data (32-bits value)
        :param intervals: list of sub-intervals in the waveform.
        """
        if len(intervals) == 0:
            return

        ex_dat = self._convert_to_long(ex_dat)

        new_sub_segs = []
        pos = Decimal(0)


        i = 0
        first_pt = intervals[i][0]
        last_pt = first_pt + intervals[i][1]


        for sub_seg in self._sub_lin_segs:
            while pos > last_pt and i + 1 < len(intervals):
                i += 1
                first_pt = intervals[i][0]
                last_pt = first_pt + intervals[i][1]

            if (pos + sub_seg.length <= first_pt or pos >= last_pt or first_pt > last_pt):
                new_sub_segs.append(sub_seg)
                pos += sub_seg.length
                continue

            p0 = pos
            p1 = max(p0, first_pt)
            p2 = min(p0 + sub_seg.length, last_pt)
            p3 = p0 + sub_seg.length

            if p1 > p0:
                new_sub_seg = LinSubSeg(
                        sub_seg.ext_len,
                        sub_seg.ext_v0,
                        sub_seg.ext_v1,
                        sub_seg.sub_offs,
                        p1 - p0,
                        sub_seg.ex_dat)
                new_sub_segs.append(new_sub_seg)

            new_sub_seg = LinSubSeg(
                    sub_seg.ext_len,
                    sub_seg.ext_v0,
                    sub_seg.ext_v1,
                    sub_seg.sub_offs + p1 - p0,
                    p2 - p1,
                    sub_seg.ex_dat | ex_dat)
            new_sub_segs.append(new_sub_seg)

            if p3 > p2:
                new_sub_seg = LinSubSeg(
                        sub_seg.ext_len,
                        sub_seg.ext_v0,
                        sub_seg.ext_v1,
                        sub_seg.sub_offs + p2 - p0,
                        p3 - p2,
                        sub_seg.ex_dat)
                new_sub_segs.append(new_sub_seg)

            pos += sub_seg.length

        self._sub_lin_segs = new_sub_segs

    def add_markers_mask(self, marker_idx, offset, length, dat_buff):
        """
        Add markers mask to given buffer of wave-data and returns the new buffer data.
        The marker resolution are two wave points. Odd number of wave points are rounded.
        Marker positions are programmed on channel 1 or 3.
        Inputs:
            marker_idx (int): index of the marker. Valid values are 1 or 2.
            offset (): offset on the position of the marker
            length (): length or width of the marker signal. Had to be superior or egual to 2.
            dat_buff : the given buffer of wave data

        Output:
            returns the modified buffer of wave data containing the marker positions
        """


        mask = 0
        # |= takes the hexidecimal value into a decimal value.
        if marker_idx == 1:
            mask |= _EX_DAT_M1_MASK_NICO
        if marker_idx == 2:
            mask |= _EX_DAT_M2_MASK_NICO

        if mask == 0 or length == 0:
            print('''Wrong value of marker_idx or length. The marker_idx has to be 1 or 2. length should be superior or egal to 2 ?''')
            # you should verify the assertion on length
            return
        # % returns the modulo of the division
        if offset %2 !=0:
            offset=offset-1
        if length %2 !=0:
            length=length-1

        marker_points=length/2 # number of marker points to be programmed as one marker point hase size of 2 wave form points

        for i in range(0, marker_points):

            k=8*(np.int(offset/16)+1)+offset/2 # encodes marker position in the last 8 words of a 16 word data block
            offset=offset+2
            dat_buff[k] = mask+dat_buff[k]

        return dat_buff

    def seq_mode(self, value='STEP'):
        """
        Sequence mode setter method.
        """

        if value in ('AUTO','ONCE','STEP'):
            self._visainstrument.write('SEQ:ADV{}'.format(value))
            if self._visainstrument.query('SEQ:ADV?') != value:
                print('''Instrument did not set correctly the sequence mode''')
        else:
            print('''The invalid value {} was sent to seq_mode method''').format(value)

    def get_seq_mode(self):
        """
        Gets Sequence mode setter method.

        Input:
            None

        Output:
            Function mode (string) : 'AUTO','ONCE' or 'STEP' depending on the mode
        """

        logging.info( __name__+' : Getting the sequence mode setter method')


        return self._visainstrument.query('SEQ:ADV?')

    def seq_jump_source(self,value='BUS'):
        """
        Sequence jump source setter method: in AUTOmatic and STEPped mode only, a jump signal is required to reach the next step of the sequence.
        This jump can be either a trig (BUS) or being input on the Event input port (EVEN).
        """
        if self._visainstrument.query('SEQ:ADV?') not in ('AUTO', 'STEP'):
            raise ValueError('The sequence mode should be in AUTOmatic or in STEPped in order to use the seq_jump_source')
        if value in ('BUS','EVEN'):
            self._visainstrument.write('SEQ:JUMP{}'.format(value))
            if self._visainstrument.query('SEQ:JUMP?') !=value:
                print('''Instrument did not set correctly the sequence jump source''')
        else:
            print('''The invalid value {} was sent to seq_jump_source method''').format(value)

    def create_wvf_steps_info_buff(self, buffer):
        """
        Create buffer of the specified waveform's steps info.

        It can be used for downloading sequence-definition as binary-data.
        Note that each wvf has individual sequence (of sequencer steps).

        Important:
        The steps consist segment-numbers that should fit
        the actual segments in the device's arbitrary-memory.
        The assumption is that the script's segments correspond to
        segments number: n, n+1, n+2, .. in the device's arbitrary-memory
        where n is the number of the first one (i.e. `n = first_seg_nb`).
        Inputs:
            buffer: 2D numpy.array of the sequence formated in the following way [[loop,segment#,jum_flag],[loop,segment#,jum_flag],...]

        Output:
            m: a `numpy.array` (of bytes) with the wvf's steps-info.
        """


        # define packed struct of: uint32, uint16, uint8 and pad byte
        # (in little-endian bytes order)
        s = struct.Struct('< L H B x')

        num_steps = len(buffer)
        s_size = s.size

        m = np.empty(s_size * num_steps, dtype='uint8')
        jump_flag = 0
        for i in range(num_steps):
            s.pack_into(m, i * s_size, buffer[i,0], buffer[i,1], buffer[i,2])
        return m

    def send_seq(self,buffer,seq_id):
        """
        This method loads a sequence with number seq_id into the AWG.
        Inputs:
            buffer: 2D numpy.array of the sequence formated in the following way
                    [[loop,segment#,jum_flag],[loop,segment#,jum_flag],...]
            seq_id (int): the number of the sequence to be loaded. Value between 1 and 1 000.
        Output:
            None
        """
        #select the relevant sequence
        self._visainstrument.write(":SEQ:SEL {0:d}".format(seq_id))
        # Create packed binary buffer with the sequence info ..
        buff=self.create_wvf_steps_info_buff(buffer)
        # and download the sequence info ..
        self.download_binary_data(":SEQ:DATA", buff, len(buff) * buff.itemsize)

    def sequence_select(self, seq_id):
        '''
        Selects the active sequence seq_id
        '''
        #select the relevant sequence
        self._visainstrument.write(":SEQ:SEL {0:d}".format(seq_id))

    def query(self, cmd):
        res= self._visainstrument.query(cmd + '?')
        print res
        return res

    def tell(self, cmd):
        self._visainstrument.write(cmd)
