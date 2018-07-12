# Agilent_E8257D.py class, to perform the communication between the Wrapper and the device
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
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

class Agilent_E8257D_40GHz(Instrument):
    '''
    This is the driver for the Agilent E8257D Signal Generator

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Agilent_E8257D', address='<GBIP address>, reset=<bool>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Agilent_E8257D, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Agilent_E8257D')
        Instrument.__init__(self, name, tags=['physical'])
        rm = visa.ResourceManager()

        # Add some global constants
        self._address = address
        try:
            self._visainstrument = rm.open_resource(self._address)
        except:
            raise SystemExit

        self.add_parameter('power', flags=Instrument.FLAG_GETSET, units='dBm', minval=-135, maxval=25, type=types.FloatType)
        self.add_parameter('phase', flags=Instrument.FLAG_GETSET, units='rad', minval=-numpy.pi, maxval=numpy.pi, type=types.FloatType)
        self.add_parameter('frequency', flags=Instrument.FLAG_GETSET, units='Hz', minval=1e5, maxval=40e9, type=types.FloatType)
        self.add_parameter('status', flags=Instrument.FLAG_GETSET, option_list=['on', 'off'], type=types.StringType)
        self.add_parameter('pulse_status', flags=Instrument.FLAG_GETSET, option_list=['on', 'off'], type=types.StringType)
        self.add_parameter('pulse_type', flags=Instrument.FLAG_GETSET, option_list=['square', 'frun', 'trigered', 'doublet', 'gated'], type=types.StringType)
        self.add_parameter('pulse_period', flags=Instrument.FLAG_GETSET, units='s', type=types.FloatType)
        self.add_parameter('pulse_width', flags=Instrument.FLAG_GETSET, units='s', type=types.FloatType)
        self.add_parameter('freqsweep', flags=Instrument.FLAG_GETSET, option_list=['on', 'off'], type=types.StringType)


        self.add_function('reset')
        self.add_function ('get_all')


        if (reset):

            self.reset()

        self.get_all()

    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : resetting instrument')
        self._visainstrument.write('*RST')
        self.get_all()

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : get all')
        self.get_power()
        self.get_phase()
        self.get_frequency()
        self.get_status()
        self.get_pulse_status()
        self.get_pulse_period()
        self.get_pulse_width()

    def do_get_power(self):
        '''
        Reads the power of the signal from the instrument

        Input:
            None

        Output:
            ampl (?) : power in ?
        '''
        logging.debug(__name__ + ' : get power')
        return float(self._visainstrument.query('POW:AMPL?'))

    def do_set_power(self, amp):
        '''
        Set the power of the signal

        Input:
            amp (float) : power in ??

        Output:
            None
        '''
        logging.debug(__name__ + ' : set power to %f' % amp)
        self._visainstrument.write('POW:AMPL %s' % amp)

    def do_get_phase(self):
        '''
        Reads the phase of the signal from the instrument

        Input:
            None

        Output:
            phase (float) : Phase in radians
        '''
        logging.debug(__name__ + ' : get phase')
        return float(self._visainstrument.query('PHASE?'))

    def do_set_phase(self, phase):
        '''
        Set the phase of the signal

        Input:
            phase (float) : Phase in radians

        Output:
            None
        '''
        logging.debug(__name__ + ' : set phase to %f' % phase)
        self._visainstrument.write('PHASE %s' % phase)

    def do_get_frequency(self):
        '''
        Reads the frequency of the signal from the instrument

        Input:
            None

        Output:
            freq (float) : Frequency in Hz
        '''
        logging.debug(__name__ + ' : get frequency')
        return float(self._visainstrument.query('FREQ:CW?'))

    def do_set_frequency(self, freq):
        '''
        Set the frequency of the instrument

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : set frequency to %f' % freq)
        self._visainstrument.write('FREQ:CW %s' % freq)

    def do_get_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (string) : 'On' or 'Off'
        '''
        logging.debug(__name__ + ' : get status')

        # Output can be '0', '1' or '0\n', '1\n' which are different strings.
        # By using int() we can only get 1 or 0 independently of the OS.
        stat = int(self._visainstrument.query('OUTP?'))

        if stat == 1:
          return 'on'
        elif stat == 0:
          return 'off'
        else:
          raise ValueError('Output status not specified : %s' % stat)
        return

    def do_set_status(self, status):
        '''
        Set the output status of the instrument

        Input:
            status (string) : 'On' or 'Off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        if status.upper() in ('ON', 'OFF'):
            status = status.upper()
        else:
            raise ValueError('set_status(): can only set on or off')
        self._visainstrument.write('OUTP %s' % status)

    def do_get_pulse_status(self):
        '''
        Reads the output pulse status from the instrument

        Input:
            None

        Output:
            status (string) : 'On' or 'Off'
        '''
        logging.debug(__name__ + ' : get status')
        # Output can be '0', '1' or '0\n', '1\n' which are different strings.
        # By using int() we can only get 1 or 0 independently of the OS.
        stat = int(self._visainstrument.query(':pulm:stat?'))

        if stat == 1:
          return 'on'
        elif stat == 0:
          return 'off'
        else:
          raise ValueError('Output status not specified : %s' % stat)
        return

    def do_set_pulse_status(self, status):
        '''
        Set the output pulse status of the instrument

        Input:
            status (string) : 'On' or 'Off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        if status.upper() in ('ON', 'OFF'):
            status = status.upper()
        else:
            raise ValueError('set_status(): can only set on or off')
        self._visainstrument.write(':pulm:stat %s' % status)

    def do_get_pulse_type(self):
        '''
        Reads the output pulse type from the instrument

        Input:
            None

        Output:
            type (string) :'square', 'frun', 'trigered', 'doublet', 'gated'
        '''
        logging.debug(__name__ + ' : get pulse type')
        stat = self._visainstrument.query(':pulm:source:internal?')

        return stat

    def do_set_pulse_type(self, kind):
        '''
        Set the output pulse type of the instrument

        Input:
            status (string) : 'square', 'frun', 'trigered', 'doublet', 'gated', 'external'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set pulse type to %s' % kind)
        if kind.lower() in ('square', 'frun', 'trigered', 'doublet', 'gated', 'external'):
            kind = kind.upper()
            self._visainstrument.write(':pulm:source:internal %s' % kind)
        if kind.lower() in ('external'):
            kind = kind.upper()
            self._visainstrument.write(':pulm:source:external')
        else:
            raise ValueError("set_pulse_type(): can only set on'square', 'frun', 'trigered', 'doublet', 'gated', 'external'")


    def do_get_pulse_period(self):
        '''
        Reads the output pulse period from the instrument

        Input:
            None

        Output:
            period (float) : repetition period in second
        '''
        logging.debug(__name__ + ' : get pulse period')
        stat = self._visainstrument.query(':pulm:internal:period?')

        return stat

    def do_set_pulse_period(self, period):
        '''
        Set the output pulse type of the instrument

        Input:
            period (float) : repetition period in second

        Output:
            None
        '''
        logging.debug(__name__ + ' : set pulse period to %s' % period)
        self._visainstrument.write(':pulm:internal:period %s' % period)

    def do_get_pulse_width(self):
        '''
        Reads the output pulse width from the instrument

        Input:
            None

        Output:
            width (float) : width in second
        '''
        logging.debug(__name__ + ' : get pulse width')
        stat = self._visainstrument.query(':pulm:internal:pwidth?')

        return stat

    def do_set_pulse_width(self, width):
        '''
        Set the output pulse width of the instrument

        Input:
            period (float) : width in second

        Output:
            None
        '''
        logging.debug(__name__ + ' : set pulse width to %s' % width)
        self._visainstrument.write(':pulm:internal:pwidth %s' % width)

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

#########################################################
#
#
#                Frequency sweeps
#
#
#########################################################

    def do_set_freqsweep(self, freqsweep='off'):
        '''
    	Set the frequency sweep mode to 'on' or 'off'

        Input:
            status (string): 'on' or 'off'
        Output:
            None
        '''
        logging.debug(__name__ + ' : set frequency sweep mode to %s' % freqsweep)

        if freqsweep.upper() in ('ON'):
            self._visainstrument.write('SOURce:FREQuency:MODE SWEep')
        elif freqsweep.upper() in ('OFF'):
            self._visainstrument.write('SOURce:FREQuency:MODE CW')
        else:
            raise ValueError('set_freqsweep(): can only set on or off')


    def do_get_freqsweep(self):
        '''
        Get the status of the frequency sweep mode from the instrument

        Input:
            None
        Output:
            status (string) : 'on' or 'off'
        '''
        logging.debug(__name__ + ' : get frequency sweep mode status')
        # Output can be '0', '1' or '0\n', '1\n' which are different strings.
        # By using int() we can only get 1 or 0 independently of the OS.
        stat = self._visainstrument.query('SWE:RUNN?')

        if stat == 1:
          return 'on'
        elif stat == 0:
          return 'off'
        else:
          raise ValueError('Output status not specified : %s' % stat)
        return

	###################### Methods for the frequency sweep mode ########################

    def set_dwelltime(self, dwelltime=100):
        '''
    	Set the dwell time of the frequency sweep mode

        Input:
            dwelltime (float): time between two frequency steps
        Output:
            None
        '''
        logging.debug(__name__ + ' : set the dwell time of the frequency sweep mode to %s' % dwelltime)
        self._visainstrument.write('SWE:DWEL '+str(float(dwelltime))+ 'ms')

    def set_sweepmode(self, sweepmode='single'):
        '''
    	Set the frequency sweep mode

        Input:
            sweepmode (string): AUTO or SINGLE
        Output:
            None
        '''
        logging.debug(__name__ + ' : set the frequency sweep mode to %s' % sweepmode)
        if sweepmode.upper() in ('AUTO'):
            self._visainstrument.write('SWE:MODE AUTO')
            self._visainstrument.write('SWEep:GENeration STEPped')
            self._visainstrument.write('TRIGger:SOURce IMMediate')
            self._visainstrument.write('INITiate:CONTinuous ON')

        elif sweepmode.upper() in ('SINGLE'):
            self._visainstrument.write('SWE:MODE AUTO')
            self._visainstrument.write('SWEep:GENeration STEPped')
            self._visainstrument.write('TRIGger:SOURce IMMediate')
            self._visainstrument.write('INITiate:CONTinuous ON')
        else:
            raise ValueError('set_sweepmode(): can only set AUTO or SINGLE')

    def set_spacingfreq(self, spacingfreq='linear'):
        '''
    	Define the type of frequency spacing for the sweep: linear or log

        Input:
            spacingfreq (string): linear or log
        Output:
            None
        '''
        logging.debug(__name__ + ' : Spacing frequency is set to %s' % spacingfreq)
        if spacingfreq.upper() in ('LINEAR'):
            self._visainstrument.write('SWE:SPAC LIN')
        elif spacingfreq.upper() in ('LOG'):
            self._visainstrument.write('SWE:SPAC LOG')
        else:
            raise ValueError('set_spacingfreq(): can only set LINEAR or LOG')

    def startsweep(self):
        '''
    	Start the frequency sweep. Valid in the 'SINGLE' sweep mode.

        Input:
            None
        Output:
            None
        '''
        logging.debug(__name__ + ' : start the frequency sweep')
        self._visainstrument.write('FREQ:MODE SWE')


    def restartsweep(self):
        '''
    	Restart the frequency sweep.

        Input:
            None
        Output:
            None
        '''
        logging.debug(__name__ + ' : restart the frequency sweep')
        self._visainstrument.write('SOUR:SWE:RES')

    def set_startfreq(self,startfreq):
        '''
    	Define the start frequency of the sweep.

        Input:
            startfreq (float): first frequency of the sweep
        Output:
            None
        '''
        logging.debug(__name__ + ' : Start frequency is set to %s' % startfreq)
        self._visainstrument.write('FREQ:START '+str(float(startfreq))+'GHz')

    def set_stopfreq(self,stopfreq):
        '''
    	Define the stop frequency of the sweep.

        Input:
            stopfreq (float): last frequency of the sweep
        Output:
            None
        '''
        logging.debug(__name__ + ' : Stop frequency is set to %s' % stopfreq)
        self._visainstrument.write('FREQ:STOP '+str(float(stopfreq))+'GHz')

    def set_stepfreq(self,stepfreq):
        '''
    	Define the step frequency of the sweep in linear spacing mode.

        Input:
            stepfreq (float): step frequency of the sweep in GHz
        Output:
            None
        '''
        logging.debug(__name__ + ' : Step frequency is set to %s' % stepfreq)
        self._visainstrument.write('FREQ:STEP '+str(float(stepfreq))+'GHz')

    def set_points(self,points):
        '''
    	Define the number of points of the sweep in linear spacing mode.

        Input:
            points (int): number of points
        Output:
            None
        '''
        logging.debug(__name__ + ' : Sweep number of points is set to %s' % points)
        self._visainstrument.write('SWEep:POINts '+str(int(points)))
