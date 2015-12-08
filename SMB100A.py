#SMB100A.py class
# Etienne Dumur <etienne.dumur@gmail.com>, 2012
# Modified by Nico Roch, 2014
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
import logging
import types
from numpy import pi

class SMB100A(Instrument):
    '''
    This is the python driver for the SMB100A

    Usage:
    Initialize with
    <name> = instruments.create('name', 'SMB100A', address='<GPIB address>', reset=True|False)
    '''

    def __init__(self, name, address, reset = False):
        '''
        Initializes the SMB100A

        Input:
            name (string)    : name of the instrument
            address (string) : TCPIP/GPIB address
            reset (bool)     : Reset to default values

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])
        rm = visa.ResourceManager()

        self._address = address
        try:
            self._visainstrument = rm.open_resource(self._address)
        except:
            raise SystemExit


        self.add_parameter('frequency', flags=Instrument.FLAG_GETSET, units='Hz', minval=100e3, maxval=20e9, type=types.FloatType)
        self.add_parameter('power', flags=Instrument.FLAG_GETSET, units='dBm', minval=-145, maxval=30.0, type=types.FloatType)
        self.add_parameter('phase', flags=Instrument.FLAG_GETSET, units='rad', minval=-pi, maxval=pi, type=types.FloatType)
        self.add_parameter('status', flags=Instrument.FLAG_GETSET, option_list=['on', 'off'], type=types.StringType)
        self.add_parameter('freqsweep', flags=Instrument.FLAG_GETSET, option_list=['on', 'off'], type=types.StringType)
        self.add_parameter('powsweep', flags=Instrument.FLAG_GETSET, option_list=['on', 'off'], type=types.StringType)


        self.add_function ('get_all')
        self.add_function('reset')

        if reset :

            self.reset()

        self.get_all()

############################################################################
#
#            Methods
#
############################################################################

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
        Get all parameters of the intrument

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
        self.get_freqsweep()
        self.get_powsweep()

#########################################################
#
#
#                Frequency
#
#
#########################################################

    def do_set_frequency(self, frequency=1.):
        '''
            Set the frequency of the instrument

            Input:
                frequency (float): Frequency at which the instrument will be tuned [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency of the intrument')
        self._visainstrument.write('frequency '+str(frequency))


    def do_get_frequency(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been tuned [Hz]
        '''

        logging.info(__name__+' : Get the frequency of the intrument')
        return self._visainstrument.query('frequency?')

#########################################################
#
#
#                Power
#
#
#########################################################

    def do_set_power(self, power=0):
        '''
            Set the power of the instrument


            Input:
                power (float): power at which the instrument will be tuned [dBm]

            Output:
                None
        '''

        logging.info(__name__+' : Set the power of the intrument')
        self._visainstrument.write('power '+str(power))


    def do_get_power(self):
        '''
            Get the power of the instrument

            Input:
                None

            Output:

                power (float): power at which the instrument has been tuned [dBm]
        '''

        logging.info(__name__+' : Get the power of the intrument')
        return self._visainstrument.query('power?')

#########################################################
#
#
#                Phase
#
#
#########################################################

    def do_set_phase(self, phase=0):
        '''
            Set the phase of the instrument


            Input:
                phase (float): phase at which the instrument will be tuned [rad]

            Output:
                None
        '''

        logging.info(__name__+' : Set the phase of the intrument')
        self._visainstrument.write('phase '+str(float(phase)*360.0/pi))


    def do_get_phase(self):
        '''
            Get the phase of the instrument

            Input:
                None

            Output:

                phase (float): phase at which the instrument has been tuned [rad]
        '''

        logging.info(__name__+' : Get the phase of the intrument')
        return self._visainstrument.query('phase?')


#########################################################
#
#
#                Status
#
#
#########################################################

    def do_get_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (string) : 'on' or 'off'
        '''
        logging.debug(__name__ + ' : get status')

        # Output can be '0', '1' or '0\n', '1\n' which are different strings.
        # By using int() we can only get 1 or 0 independently of the OS.
        stat = int(self._visainstrument.query('output?'))

        if stat == 1:
          return 'on'
        elif stat == 0:
          return 'off'
        else:
          raise ValueError('Output status not specified : %s' % stat)
        return

    def do_set_status(self, status='off'):
        '''
        Set the output status of the instrument

        Input:
            status (string) : 'on' or 'off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        if status.upper() in ('ON', 'OFF'):
            status = status.upper()
        else:
            raise ValueError('set_status(): can only set on or off')
        self._visainstrument.write('output %s' % status)

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
        stat = int(self._visainstrument.query('SWE:RUNN?'))

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
            self._visainstrument.write('TRIG:FSW:SOUR AUTO')
        elif sweepmode.upper() in ('SINGLE'):
            self._visainstrument.write('SWE:MODE AUTO')
            self._visainstrument.write('TRIG:FSW:SOUR SING')
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
        self._visainstrument.write('SOUR:SWE:FREQ:EXEC')

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
        self._visainstrument.write('SWE:STEP '+str(float(stepfreq))+'GHz')




    def set_pointsfreq(self,pointsfreq):
        '''
        Define the number of points of the frequency sweep in linear spacing mode.
        The step is changed accordingly in order to keep the start frequency and the stop frequency constant

        Input:
            pointsfreq (integer): number of points of the sweep
        Output:
            None
        '''
        logging.debug(__name__ + ' : Number of points for the frequency sweep is set to %s' % pointsfreq)
        self._visainstrument.write('SWE:POIN '+str(int(pointsfreq)))

#########################################################
#
#
#                Power sweeps
#
#
#########################################################

    def do_set_powsweep(self, powsweep='off'):
        '''
    	Set the power sweep mode

        Input:
            status (string): 'on' or 'off'
        Output:
            None
        '''
        logging.debug(__name__ + ' : set power sweep mode to %s' % powsweep)

        if powsweep.upper() in ('ON'):
            self._visainstrument.write('POWer:MODE SWEep')
        elif powsweep.upper() in ('OFF'):
            self._visainstrument.write('POWer:MODE CW')
        else:
            raise ValueError('set_powsweep(): can only set on or off')


    def do_get_powsweep(self):
        '''
        Get the status of the power sweep mode from the instrument

        Input:
            None
        Output:
            status (string) : 'on' or 'off'
        '''
        logging.debug(__name__ + ' : get power sweep mode status')
        # Output can be '0', '1' or '0\n', '1\n' which are different strings.
        # By using int() we can only get 1 or 0 independently of the OS.
        stat = int(self._visainstrument.query('SWEep:POWer:RUNNing?'))

        if stat == 1:
          return 'on'
        elif stat == 0:
          return 'off'
          return 'off'
        else:
          raise ValueError('Output status not specified : %s' % stat)
        return

	###################### Methods for the power sweep mode ########################

    def set_powdwelltime(self, dwelltime=100):
        '''
    	Set the dwell time of the power sweep mode

        Input:
            dwelltime (float): time in ms between two power steps
        Output:
            None
        '''
        logging.debug(__name__ + ' : set the dwell time of the power sweep mode to %s' % dwelltime)
        self._visainstrument.write('SWEep:POWer:DWELl '+str(float(dwelltime))+ 'ms')

    def set_powsweepmode(self, sweepmode='single'):
        '''
    	Set the power sweep mode

        Input:
            sweepmode (string): AUTO or SINGLE
        Output:
            None
        '''
        logging.debug(__name__ + ' : set the power sweep mode to %s' % sweepmode)
        if sweepmode.upper() in ('AUTO'):
            self._visainstrument.write('SWEep:POWer:MODE AUTO')
            self._visainstrument.write('TRIGger:PSWeep:SOURce  AUTO')
        elif sweepmode.upper() in ('SINGLE'):
            self._visainstrument.write('SWEep:POWer:MODE AUTO')
            self._visainstrument.write('TRIGger:PSWeep:SOURce  SING')
        else:
            raise ValueError('set_powsweepmode(): can only set AUTO or SINGLE')

    def powstartsweep(self):
        '''
    	Start the power sweep. Valid in the 'SINGLE' sweep mode.

        Input:
            None
        Output:
            None
        '''
        logging.debug(__name__ + ' : start the power sweep')
        self._visainstrument.write('SWEep:POWer:EXECute')

    def powrestartsweep(self):
        '''
    	Restart the power sweep.

        Input:
            None
        Output:
            None
        '''
        logging.debug(__name__ + ' : restart the power sweep')
        self._visainstrument.write('SWEep:RESet')

    def set_startpow(self,startpow):
        '''
    	Define the start power of the sweep.

        Input:
            startpow (float): first power value of the sweep in dBm
        Output:
            None
        '''
        logging.debug(__name__ + ' : Start power is set to %s' % startpow)
        self._visainstrument.write('POWer:STARt '+str(float(startpow))+'dBm')

    def set_stoppow(self,stoppow):
        '''
    	Define the stop frequency of the sweep.

        Input:
            stoppow (float): last power value of the sweep in dBm
        Output:
            None
        '''
        logging.debug(__name__ + ' : Stop power is set to %s' % stoppow)
        self._visainstrument.write('POWer:STOP '+str(float(stoppow))+'dBm')

    def set_steppow(self,steppow):
        '''
    	Define the power step of the sweep in dBm.

        Input:
            steppow (float): step power of the sweep in dBm
        Output:
            None
        '''
        logging.debug(__name__ + ' : Step power is set to %s' % steppow)
        self._visainstrument.write('SWEep:POWer:STEP '+str(float(steppow))+'dB')
