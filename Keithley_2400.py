# Keithley_2400.py driver for Keithley 2400 SourceMeter
# Alexey Feofanov, 2012
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

def bool_to_str(val):
    '''
    Function to convert boolean to 'ON' or 'OFF'
    '''
    if val == True:
        return "ON"
    else:
        return "OFF"

class Keithley_2400(Instrument):
    '''
    This is the driver for the Keithley 2400 SourceMeter

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keithley_2400',
        address='<VISA address>',
        reset=<bool>,
        change_display=<bool>,
        change_autozero=<bool>)
    '''

    def __init__(self, name, address, reset=False,
            change_display=True, change_autozero=True):
        '''
        Initializes the Keithley_2400, and communicates with the wrapper.

        Input:
            name (string)           : name of the instrument
            address (string)        : GPIB address
            reset (bool)            : resets to default values
            change_display (bool)   : If True (default), automatically turn off
                                        display during measurements.
            change_autozero (bool)  : If True (default), automatically turn off
                                        autozero during measurements.
        Output:
            None
        '''
        # Initialize wrapper functions
        logging.info('Initializing instrument Keithley_2400')
        Instrument.__init__(self, name, tags=['physical'])
        rm = visa.ResourceManager()

        # Add some global constants
        self._address = address
        try:
            self._visainstrument = rm.open_resource(self._address)
        except:
            raise SystemExit
        self._visainstrument.write_termination = '\n'
        self._visainstrument.read_termination = '\n'

        self.add_parameter('current',flags=Instrument.FLAG_GETSET, units='A', type=types.FloatType,maxstep=1e-4, stepdelay= 200)
        self.add_parameter('voltage_complience',flags=Instrument.FLAG_SET, units='V', type=types.FloatType)
        self.add_parameter('current_range',flags=Instrument.FLAG_SET, units='A', type=types.FloatType)

        self.add_function('reset')
        self.add_function('set_status')
#        self.add_function('test_get_current')
        if reset:
            self.reset()

        try:
            self.set_defaults()
        except:
            raise SystemExit

    def reset(self):
        '''
        Sets the instrument to SA mode with default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Reset the instrument')
        self._visainstrument.write('*RST')

    def set_defaults(self):
#        self._visainstrument.write('REN')
        self._visainstrument.write(':SENS:FUNC "CURR";\
                                    :SENS:CURR:RANG:AUTO ON;\
                                    :SOUR:FUNC CURR;\
                                    :SOUR:CURR:MODE FIX;\
                                    :SOUR:CURR:RANG 0.1;\
                                    :DISP:CND;')
        self.off()
#        self.set_current(0)
        self.set_voltage_complience(0.4)

    ###:SENS:FUNC "RES";:SYST:RSEN ON;:SENS:RES:MODE MAN;\
    def do_set_current(self,val):
        self._visainstrument.write(':SOUR:CURR '+str(val))

    def do_get_current(self):
        return self._visainstrument.query(':SOUR:CURR?')
#        self.on()
#        self._visainstrument.write('ARM:SOUR IMM;\
#                                    :ARM:TIM 0.01;\
#                                    :TRIG:SOUR IMM;\
#                                    :TRIG:DEL 0.0;')
#        self._visainstrument.write(':TRIG:CLE;:INIT;')
#        qt.msleep(0.1)
#        self._visainstrument.write(':FETC?')
#        self._visainstrument.write('*OPC;')
#        outputString = self._visainstrument.read()
#        outputList = outputString.split(',')
#        return float(outputList[1])

    def do_set_voltage_complience(self, val):
        self._visainstrument.write(':VOLT:PROT '+str(val))

    def do_set_current_range(self,val):
        '''
        Set the current range.

        Input:
            - val (float): Maximum expected current in amps. Range is selected accordingly out of the following list.
                Imax = 1 uA, Ires = 50 pA, Inoise = 0.1*Ires
                Imax = 10 uA, Ires = 500 pA, Inoise = 0.1*Ires
                Imax = 100 uA, Ires = 5 nA, Inoise = 0.1*Ires
                Imax = 1 mA, Ires = 50 nA, Inoise = 0.1*Ires
                Imax = 10 mA, Ires = 500 nA, Inoise = 0.1*Ires
                Imax = 100 mA, Ires = 5 uA, Inoise = 0.1*Ires
                Imax = 1 A, Ires = 50 uA, Inoise = 0.1*Ires
        Output:
            - Non
        '''
        self._visainstrument.write(':SOUR:CURR:RANG '+str(val))

    def set_status(self,val):
        self._visainstrument.write(':OUTP '+str(val))


# shortcuts
    def off(self):
        '''
        Set status to 'off'

        Input:
            None

        Output:
            None
        '''
        self.set_status('off')

    def on(self):
        '''
        Set status to 'on'

        Input:
            None

        Output:
            None
        '''
        self.set_status('on')
