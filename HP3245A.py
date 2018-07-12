# HP3245A.py driver for Hewlett Packard 3245A SourceMeter
# Etienne Dumur 2013
# Modified by Nico Roch 2014
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
import numpy

import qt

class HP3245A(Instrument):
    '''
    This is the driver for the Hewlett Packard 3245A universal source

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'HP3245A',
        address='<VISA address>',
        reset=<bool>,

        change_display=<bool>,
        change_autozero=<bool>)
    '''


    def __init__(self, name, address, reset=False):
        '''
        Initializes the HP3245A, and communicates with the wrapper.

        Input:
            name (string)           : name of the instrument
            address (string)        : GPIB address
            reset (bool)            : resets to default values
        Output:
            None
        '''
        # Initialize wrapper functions
        logging.info('Initializing instrument HP3245A')
        Instrument.__init__(self, name, tags=['physical'])
        rm = visa.ResourceManager()

        # Add some global constants
        self._address = address
        try:
            self._visainstrument = rm.open_resource(self._address)
        except:
            raise SystemExit

        
        self._visainstrument.write_termination = '\r\n'
        self._visainstrument.read_termination = '\r\n'
        # self._visainstrument.term_chars = '\r\n'
        #self._visainstrument.term_chars = 'None'


        self.add_parameter('voltage', flags=Instrument.FLAG_GETSET, units='V', minval=-10, maxval=10, type=types.FloatType, maxstep=100e-3, stepdelay= 200)
        self.add_parameter('current', flags=Instrument.FLAG_GETSET, units='A', minval=-0.1, maxval=0.1, type=types.FloatType, maxstep=1e-3, stepdelay= 200)
        self.add_parameter('resolution', flags=Instrument.FLAG_GETSET, option_list=['low', 'high'], type=types.StringType)
        self.add_parameter('range', flags=Instrument.FLAG_GETSET, units='VorA', type=types.FloatType, maxstep=1e-1, stepdelay= 200)
        self.add_parameter('channel', flags=Instrument.FLAG_GETSET,  option_list=['A', 'B'], type=types.StringType)
        self.add_parameter('mode', flags=Instrument.FLAG_GETSET, option_list=['dci','dcv'], type=types.StringType)
        self.add_parameter('autorange', flags=Instrument.FLAG_GETSET, option_list=['on','off'], type=types.StringType)
        self.add_parameter('output_terminal', flags=Instrument.FLAG_GETSET, option_list=['front','rear'], type=types.StringType)

        self.add_function('reset')
        self.add_function('clear_mem')
        self.add_function('on')
        self.add_function('off')


        if reset:

            self.reset()

        self.get_all()


##################################################
#
#
#                   Methods
#
#
##################################################
    def set_defaults(self):
        '''
			Set the instrument to default values

			Input:
				None
			Output:
				None
        '''

        self.clear_mem()
        self.set_channel('A')
        self.set_mode('dci')
        self.set_resolution('high')
        self.set_autorange('on')
        self.set_current(0)

    def reset(self):
        '''
        Reset the instrument

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Reset the instrument')
        self._visainstrument.write('RST')

    def clear_mem(self):
        '''
        Clear HP3245A memory

        Input:
            None
        Output:
            None
        '''
        logging.info(__name__+ ': Clear the instrument memory')
        self._visainstrument.write('SCRATCH')

    def get_all(self):
        '''
        Get all parameters of the instrument

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : get all')
        self.get_mode()
        self.get_channel()
        self.get_resolution()
        self.get_range()
        self.get_autorange()
        if   self.get_mode() == 'dci':
            self.get_current()
        else:
            self.get_voltage()




    def do_set_mode(self, modeName):
        '''
        Change mode to DCI or DCV and apply 0 Ampere/Volt (or: do nothing if the active channel is in the correct mode)

        Input:
            modeName: string

        Output:
            None
        '''

        oldModeName = (self._visainstrument.query('APPLY?')).lower()
        modeName = modeName.lower()
        if oldModeName != modeName:
            if modeName == 'dci' or modeName == 'dcv':
                logging.info(__name__ + ' : change the active channel output mode to '+str(modeName))
                self._visainstrument.write('APPLY ' +str(modeName.upper())+'0')
            else:
                raise ValueError('The input parameter should be "dci" or "dcv"')


    def do_get_mode(self):
        '''
		    gets the active mode ('dci' or 'dcv')
            Input:
                None
            Output:
                String
        '''
        logging.info(__name__+ ' : get the active mode ("dci" or "dcv")')
        return self._visainstrument.query('APPLY?').lower()


    def do_set_channel(self, channelName):
        '''
            sets the active channel (A or B). All subsequent set and get commands are applied to this channel until it is changed again.

            Input:
                channelName: String

            Output:
                None
        '''
        if channelName.lower() == 'a':
            logging.info(__name__ + ' : set the active channel to A')
            self._visainstrument.write('USE CHANA ')
            self._visainstrument.write('MON STATE CHANA ')
        elif channelName.lower() == 'b':
            logging.info(__name__ + ' : set the active channel to B')
            self._visainstrument.write('USE CHANB ')
            self._visainstrument.write('MON STATE CHANB ')
        else:
            raise ValueError('The input parameter should be "A" or "B"')

    def do_get_channel(self):
        '''
            gets active channel

            Input:
                None

            Output:
                String
        '''
        logging.debug(__name__ + ' : get the active channel')
        channelInt = int(self._visainstrument.query('USE?'))
        if channelInt == 0:
            return 'A'
        elif channelInt == 100:
            return 'B'

    def do_set_output_terminal(self, outputTerminal):
        '''
            sets the output terminal: front or rear.

            Input:
                outputTerminal(String): FRONT or REAR

            Output:
                None
        '''
        if str(outputTerminal).lower() == 'front':
            logging.info(__name__ + ' : set the output terminal to FRONT')
            self._visainstrument.write('TERM FRONT ')
        elif str(outputTerminal).lower() == 'rear':
            logging.info(__name__ + ' : set the output terminal to REAR')
            self._visainstrument.write('TERM REAR ')
        else:
            raise ValueError('The input parameter should be "FRONT" or "REAR".')

    def do_get_output_terminal(self):
        '''
            gets the output terminal, either FRONT or REAR
        '''
        return 'Method not implemented due to error (Javier)'


    def do_set_current(self, currentValue):
        '''
            Set the output current of the active channel.

            Input:
                - currentValue (float): Current in amps

            Output:
                - None
        '''
        logging.info(__name__ + ' : set the current to '+str(currentValue))
        self._visainstrument.write('APPLY DCI '+str(currentValue))

    def do_get_current(self):
        '''
            Get the output current of the active channel.

            Input:
                - None
        '''
        logging.debug(__name__ + ' : Get the current')
        if (self._visainstrument.query('APPLY? '))!='DCI':
            raise ValueError('Active channel is not in current mode')
        else:
            return float(self._visainstrument.query('OUTPUT? '))

    def do_set_voltage(self, voltageValue):
        '''
            Set the output voltage of the active channel.

            Input:
                - voltageValue (float): voltage in Volt

            Output:
                - None
        '''
        logging.info(__name__ + ' : set the voltage to '+str(voltageValue))
        self._visainstrument.write('APPLY DCV '+str(voltageValue))

    def do_get_voltage(self):
        '''
            Get the output voltage of the active channel.

            Input:
                - None

            Output:
                - float
        '''

        logging.debug(__name__ + ' : Get the voltage')
        if (self._visainstrument.query('APPLY? '))!='DCV':
            raise ValueError('Active channel is not in voltage mode')
        else:
            return float(self._visainstrument.query('OUTPUT? '))

    def do_set_range(self, rangeValue):
        '''
            Set the current/voltage range. The range is selected accordingly out of the following lists:
                In current mode:
                    "low resolution":   Imax = 0.1 mA, dI = 50 nA
                                        Imax = 1 mA,   dI = 500 nA
                                        Imax = 10 mA,  dI = 5 uA
                                        Imax = 100 mA, dI = 50 uA
                    "high resolution":  Imax = 0.1 mA, dI = 0.1 nA
                                        Imax = 1 mA,   dI = 1 nA
                                        Imax = 10 mA,  dI = 10 nA
                                        Imax = 100 mA,  dI = 100 nA
                In voltage mode:
                    "low resolution":   Vmax = 0.15625 V, dV = 79 uV
                                        Vmax = 0.3125 V, dV = 157 uV
                                        Vmax = 0.625 V, dV = 313 uV
                                        Vmax = 1.25 V, dV = 625 uV
                                        Vmax = 2.5 V, dV = 1.25 mV
                                        Vmax = 5 V, dV = 2.5 mV
                                        Vmax = 10 V, dV = 5.0 mV
                    "high resolution":  Vmax = 1 V, dV = 1 uV
                                        Vmax = 10 V, dV = 10 uV

            Input:
                - rangeValue (float or string): Maximum expected current or voltage in Ampere or Volt, or alternatively "AUTO" for autorange.
            Output:
                - None
        '''

        logging.info(__name__ + ' : set the range to '+str(rangeValue))
        self._visainstrument.write('RANGE '+str(rangeValue))

    def do_get_range(self):
        '''
            Get the range of the device

            Input:
                - None
            Output:
                - String
        '''

        logging.info(__name__ + ' : get the range')
        return self._visainstrument.query('RANGE?')

    def do_set_autorange(self,ARStatus):
        '''
            Enables or disables autorange

			Input:
                -ARStatus "ON" or "OFF"
            Output:
				-None
		'''

        if ARStatus.lower()=='on' or ARStatus.lower()=='off':
            logging.info(__name__+ 'set autorange to' +str(ARStatus))
            self._visainstrument.write('arange '+str(ARStatus.upper()))
        else:
            raise ValueError('Autorange can be only "on" or "off"')

    def do_get_autorange(self):
		'''
			Get the status of the autorange functions

			Input:
				-None
			Output:
				-None
		'''

		logging.info(__name__+ 'get the status of the autorange function')
		return self._visainstrument.query('ARANGE?')

    def do_set_resolution(self, resolution):
        '''
            Set the resolution to the device.

            Input:
                - resolution (string): ['low', 'high']

            Output:
                - None
        '''

        if resolution.lower() == 'low' or resolution.lower() == 'high':
            logging.info(__name__ + ' : set the resolution to '+str(resolution))
            self._visainstrument.write('DCRES '+str(resolution.upper()))
        else:
            raise ValueError('The input parameter should be "low" or "high"')

    def do_get_resolution(self):
        '''
            Get the resolution of the device

            Input:
                - None
            Output:
                - String
        '''

        logging.info(__name__ + ' : get the resolution')
        return self._visainstrument.query('DCRES?')

# shortcuts
    def off(self):
        '''
        Function definition to get compatibility with Keithley 2400 driver
        '''

    def on(self):
        '''
        definition to get compatibility with Keithley 2400 driver
        '''
