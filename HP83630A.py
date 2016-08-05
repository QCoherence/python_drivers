#SMB100A.py class
# Etienne Dumur <etienne.dumur@gmail.com>, 2012
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

class HP83630A(Instrument):
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

        # Remove the carriage return character from all the visa answer
        self._visainstrument.read_termination = '\n'

        self.add_parameter('frequency', flags=Instrument.FLAG_GETSET, units='Hz', minval=100e3, maxval=26.5e9, type=types.FloatType)
        self.add_parameter('power', flags=Instrument.FLAG_GETSET, units='dBm', minval= -20., maxval=25, type=types.FloatType)
        # self.add_parameter('phase', flags=Instrument.FLAG_GETSET, units='rad', minval=-pi, maxval=pi, type=types.FloatType)
        self.add_parameter('status', flags=Instrument.FLAG_GETSET, option_list=['on', 'off'], type=types.StringType)


        self.add_function ('get_all')
        self.add_function('reset')

        if reset :

            self.reset()

        self.get_all()

############################################################################

#            Methods

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
        # self.get_phase()
        self.get_frequency()
        self.get_status()

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

    # def do_set_phase(self, phase=0):
        # '''
            # Set the phase of the instrument


            # Input:
                # phase (float): phase at which the instrument will be tuned [rad]

            # Output:
                # None
        # '''

        # logging.info(__name__+' : Set the phase of the intrument')
        # self._visainstrument.write('phase '+str(float(phase)*360.0/pi))


    # def do_get_phase(self):
        # '''
            # Get the phase of the instrument

            # Input:
                # None

            # Output:

                # phase (float): phase at which the instrument has been tuned [rad]
        # '''

        # logging.info(__name__+' : Get the phase of the intrument')
        # return self._visainstrument.query('phase?')


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
        stat = self._visainstrument.query('power:state?')

        if (stat=='1'):
          return 'on'
        elif (stat=='0'):
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
        if status.upper() in 'ON':
            self._visainstrument.write('power:state 1')
        elif status.upper() in 'OFF':
            self._visainstrument.write('power:state 0')
