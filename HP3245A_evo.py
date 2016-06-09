# HP3245A.py driver for Hewlett Packard 3245A Universal Source
# Etienne Dumur 2013
# Bruno Kueng 2014
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
    # To do:
    # - Apply WFI and Apply WFV is currently useless since no method is written to upload waveform arrays

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

        # Add some global constants
        self._address = address
        try:
            self._visainstrument = visa.instrument(self._address)
        except:
            raise SystemExit
        self._visainstrument.term_chars = '\r\n'

        self.add_parameter('amplitude', flags=Instrument.FLAG_GETSET,
            units='VorA', type=types.FloatType, maxstep=1e-4, stepdelay=200)

        self.add_parameter('channel', flags=Instrument.FLAG_GETSET,
            option_list=['A', 'B'], type=types.StringType)

        self.add_parameter('dc_offset', flags=Instrument.FLAG_GETSET, units='VorA',
            type=types.FloatType, stepdelay=200)

        self.add_parameter('duty_cycle', flags=Instrument.FLAG_GETSET,
            units='VorA', type=types.FloatType, minval=5, maxval=95)

        self.add_parameter('frequency', flags=Instrument.FLAG_GETSET,
            units='Hz', type=types.FloatType, minval=0, maxval=1e6)

        self.add_parameter('resolution', flags=Instrument.FLAG_SET,
            option_list=['low', 'high'], type=types.StringType)

        self.add_parameter('range', flags=Instrument.FLAG_SET, units='VorA',
            type=types.FloatType)

        self.add_parameter('output_mode', flags=Instrument.FLAG_GETSET,
            option_list=['DCI', 'DCV', 'DCMEMI', 'DCMEMV', 'ACI', 'ACV',
            'RPI', 'RPV', 'SQI', 'SQV', 'WFI', 'WFV'], type=types.StringType)

        self.add_parameter('trigger_mode', flags=Instrument.FLAG_GETSET,
            option_list=['OFF', 'ARMWF', 'GATED', 'DUALFR'], type=types.StringType)

        self.add_parameter('trigger_event', flags=Instrument.FLAG_GETSET,
            option_list=['TB0', 'TB1', 'EXT', 'EXTBAR', 'LOW', 'HIGH', 'HOLD',
            'SGL'], type=types.StringType)

        self.add_function('reset')

        if reset:
            self.reset()

        self.get_all()


    def get_all(self):
        '''
            Get all parameters of the device

            Input:
                None

            Output:
                None
        '''
        self.get_channel()
        self.get_mode()
        self.get_amplitude()
        self.get_dc_offset()
        self.get_frequency()
        self.get_trigger_mode()
        self.get_trigger_event()


    def set_defaults(self):
        '''
        Applies the default instrument settings. Sets both channels to DCI mode
        with 0 A on the output.

        Input:
            None

        Output:
            None
        '''
        self.set_channel('B')
        self.set_mode('dci')
        self.set_amplitude(0)
        self.set_dc_offset(0)
        self.set_channel('A')
        self.set_mode('dci')
        self.set_amplitude(0)
        self.set_dc_offset(0)
        self.set_range('high')
        self.set_trigger_mode('OFF')
        self._visainstrument.write('arange on')


    def reset(self):
        '''
        Reset the instrument

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Reset the instrument')
        self._visainstrument.write('rst')


    def do_set_output_mode(self, modeName):
        '''
        Change mode and apply 0 Ampere/Volt (or: do nothing if the
        active channel is already in the correct mode). Accepts any of the
        following:
        'DCI' direct current
        'DCV' direct voltage
        'DCMEMI' triggered direct current
        'DCMEMV' triggered direct voltage
        'ACI' alternating current (sine)
        'ACV' alternating voltage (sine)
        'RPI' alternating current (ramp)
        'RPV' alternating voltage (ramp)
        'SQI' alternating current (square wave)
        'SQV' alternating voltage (square wave)
        'WFI' arbitrary waveform current
        'WFV' arbitrary waveform voltage

        Input:
            modeName (str): name of the mode

        Output:
            None
        '''
        oldModeName = self.get_output_mode
        modeName = modeName.lower()
        modeOptions = self.get_parameter_options('output_mode')['option_list']
        modeOptions = [mo.lower() for mo in modeOptions]

        if oldModeName != modeName:
            if modeName in modeOptions:
                logging.info(__name__ + ' : change the active channel output mode to '+str(modeName))
                logging.info(__name__ + ' : set amplitude to 0')
                self._visainstrument.write('apply ' + modeName + ' 0')
            else:
                raise ValueError('Input parameter must be one of the following: ' + ', '.join(modeOptions))


    def do_get_output_mode(self):
        '''
        Get the output mode of the device.

        Input:
            None

        Output:
            modeName: string
        '''
        return (self._visainstrument.ask('apply? ')).lower()


    def do_set_trigger_mode(self, modeName):
        '''
        Change trigger mode. Accepts any of the following:
        'OFF'    not triggered
        'ARMWF'  output is triggered when trigger from the TRIGIN source occurs
        'GATED'  output is set when input trigger level is LOW (0 V)
        'DUALFR' output frequency can be varied between two values

        Input:
            modeName (str): name of the mode

        Output:
            None
        '''

        modeOptions = self.get_parameter_options('trigger_mode')['option_list']
        modeOptions = [mo.lower() for mo in modeOptions]

        if modeName in modeOptions:
            logging.info(__name__ + ' : change the active channel output mode to ' + str(modeName))
            logging.info(__name__ + ' : set amplitude to 0')
            self._visainstrument.write('trigmode ' + modeName)
        else:
            raise ValueError('Input parameter must be one of the following: ' + ', '.join(modeOptions))

    def do_get_trigger_mode(self):
        '''
        Get the trigger mode of the device.

        Input:
            None

        Output:
            modeName (str): name of the mode
        '''
        return (self._visainstrument.ask('trigmode? ')).lower()


    def do_set_trigger_event(self, eventName):
        '''
        Change trigger event type. Accepts any of the following:
        'TB0'     Signal on the TB0 trigger bus
        'TB1'     Signal on the TB1 trigger bus
        'EXT'     Signal on the front panel trigger connector
        'EXTBAR': Inverse of signal on the front panel trigger connector
        'LOW':    Used with 'HIGH' parameter to internally trigger
        'HIGH':   Used with 'LOW' parameter to internally trigger
        'HOLD':   Same as HIGH parameter
        'SGL':    Single trigger

        Input:
            eventName (str): name of the trigger event type

        Output:
            None
        '''
        eventOptions = self.get_parameter_options('trigger_event')['option_list']
        eventOptions = [mo.lower() for mo in eventOptions]

        if eventName in eventOptions:
            logging.info(__name__ + ' : change the active channel trigger event type to ' + str(eventName))
            logging.info(__name__ + ' : set amplitude to 0')
            self._visainstrument.write('trigin ' + eventName)
        else:
            raise ValueError('Input parameter must be one of the following: ' + ', '.join(eventOptions))


    def do_get_trigger_event(self):
        '''
        Get the trigger event type of the device.

        Input:
            None

        Output:
            eventName (str): name of the trigger event type
        '''
        return (self._visainstrument.ask('trigin? ')).lower()


    def do_set_channel(self, channelName, changeDisplay=True):
        '''
            Sets the active channel ("A" or "B"). All subsequent set and get
            commands are applied to this channel until it is changed again.

            Input:
                channelName (str): "A" or "B", channel name
                changeDisplay (bool): decides whether the device display is
                                      changed to show the active channel

            Output:
                None
        '''
        channelName = channelName.lower()
        if channelName in ['a', 'b']
            logging.info(__name__ + ' : set the active channel to ' + channelName)
            self._visainstrument.write('use chan' + channelName)
            if changeDisplay is True:
                self._visainstrument.write('mon state chan' + channelName)
            # get value afterwards to update
            self.get_amplitude()
        else:
            raise ValueError('The input parameter should be "A" or "B"')

    def do_get_channel(self):
        '''
            Gets the active channel

            Input:
                None

            Output:
                channelName (str): name of the active channel ("A" or "B")
        '''
        logging.debug(__name__ + ' : get the active channel')
        channelInt = int(self._visainstrument.ask('use?'))
        if channelInt == 0:
            return 'A'
        elif channelInt == 100:
            return 'B'



    def do_set_amplitude(self, value):
        '''
            Set the output amplitude of the active channel.

            Input:
                - amplitudeValue (float): Amplitude in Volt or Ampere

            Output:
                - None
        '''
        mode = self.get_mode()
        logging.info(__name__ + ' : set the amplitude to ' + str(value))
        self._visainstrument.write('apply ' + mode + ' ' + str(value))

    def do_get_amplitude(self):
        '''
            Get the output amplitude of the active channel.

            Input:
                - None
            Output:
                - amplitudeValue (float): Amplitude in Volt or Ampere
        '''
        logging.info(__name__ + ' : Get the amplitude')
        return float(self._visainstrument.ask('OUTPUT? '))


    def do_set_dc_offset(self, value):
        '''
            Set the dc offset of the active channel.

            Input:
                - value (float): DC offset in Volt or Ampere

            Output:
                - None
        '''
        logging.info(__name__ + ' : set the dc offset to '+str(value))
        self._visainstrument.write('dcoff ' + str(value))


    def do_get_dc_offset(self):
        '''
            Get the dc offset of the active channel.

            Input:
                - None
            Output:
                - value (float): DC offset in Volt or Ampere
        '''
        logging.debug(__name__ + ' : Get the dc offset')
        return float(self._visainstrument.ask('dcoff? '))


    def do_set_frequency(self, value):
        # To do: accept second frequency to get compatibility with dual frequency mode
        mode = self.get_mode()
        self._visainstrument.write('freq ' + str(value))


    def do_get_frequency(self):

        return float(self._visainstrument.ask('freq? '))


    def do_set_duty_cycle(self, value):

        mode = self.get_mode()
        self._visainstrument.write('duty ' + str(value))


    def do_get_duty_cycle(self):

        return float(self._visainstrument.ask('duty? '))


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
                - rangeValue (float or str): Maximum expected current or
                                             voltage in Ampere or Volt, or
                                             alternatively "AUTO" for autorange.
            Output:
                - None
        '''
        logging.info(__name__ + ' : set the range to '+str(rangeValue))
        self._visainstrument.write('range '+str(rangeValue))


    def do_set_resolution(self, resolution):
        '''
            Set the resolution of the device.

            Input:
                - resolution (string): ['low', 'high']

            Output:
                - None
        '''
        if resolution == 'low' or resolution == 'high':
            logging.info(__name__ + ' : set the resolution to '+str(resolution))
            self._visainstrument.write('dcres '+str(resolution))
        else:
            raise ValueError('The input parameter should be "low" or "high"')
