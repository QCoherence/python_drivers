# ZVL13.py driver for Rohde & Schwarz ZVL13 Vector Network Analyser
# Thomas Weissl
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
import qt
import visa
import logging
import types
from numpy import pi
import numpy as np

class ZVL13(Instrument):
    '''
    This is the python driver for the ZVL13

    Usage:
    Initialize with
    <name> = instruments.create('name', 'ZVL13', address='<GPIB address>', reset=True|False)
    '''

    def __init__(self, name, address, reset = False):
        '''
        Initializes the ZVL13

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


        self.add_parameter('frequencyspan', flags=Instrument.FLAG_GETSET, units='Hz', minval=9e3, maxval=13.6e9, type=types.FloatType)
        self.add_parameter('centerfrequency', flags=Instrument.FLAG_GETSET, units='Hz', minval=9e3, maxval=13.6e9, type=types.FloatType)
        self.add_parameter('startfrequency', flags=Instrument.FLAG_GETSET, units='Hz', minval=9e3, maxval=13.6e9, type=types.FloatType)
        self.add_parameter('stopfrequency', flags=Instrument.FLAG_GETSET, units='Hz', minval=9e3, maxval=13.6e9, type=types.FloatType)
        self.add_parameter('power', flags=Instrument.FLAG_GETSET, units='dBm', maxval=30.0, type=types.FloatType)
        self.add_parameter('averages', flags=Instrument.FLAG_GETSET, units='', maxval=100000, type=types.FloatType)
        self.add_parameter('averagestatus', flags=Instrument.FLAG_GETSET, option_list=['on', 'off'], type=types.StringType)
        self.add_parameter('points', flags=Instrument.FLAG_GETSET, units='', minval=1, maxval=100000, type=types.FloatType)
        self.add_parameter('sweeps', flags=Instrument.FLAG_GETSET, units='', minval=1, maxval=1000, type=types.FloatType)
        self.add_parameter('measBW', flags=Instrument.FLAG_GETSET, units='Hz', minval=10, maxval=500e3, type=types.FloatType)
        self.add_parameter('status', flags=Instrument.FLAG_GETSET, option_list=['on', 'off'], type=types.StringType)

        self.add_function('get_all')
        self.add_function('reset')
        self.add_function('create_trace')

        if reset :

            self.reset()

        self.get_all()

############################################################################

#            Methods

#########################################################

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
        Get all parameters of the instrument

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : get all')
        self.get_frequencyspan()
        self.get_centerfrequency()
        self.get_startfrequency()
        self.get_stopfrequency()
        self.get_power()
        self.get_averages()
        self.get_averagestatus()
        self.get_points()
        self.get_sweeps()
        self.get_measBW()
        self.get_status()

    def create_trace(self,trace,Sparam):
        '''
        creates a trace to measure Sparam and displays it


        Input:
            trace (string, Sparam ('S11','S21','S12','S22')

        Output:
            None

        '''
        logging.info(__name__ + ' : create trace')
        self._visainstrument.write('calc:parameter:sdef  "%s","%s"' %(trace,Sparam))
        self._visainstrument.write('calc:parameter:del  "Trc1"')
        self._visainstrument.write('disp:wind1:stat off')
        self._visainstrument.write('disp:wind1:stat on')
        self._visainstrument.write('disp:wind1:trac1:feed "%s"' % trace)
        self._visainstrument.write('syst:disp:upd on')
        self._visainstrument.write('init:cont off')

    def measure(self):
        '''
        creates a trace to measure Sparam and displays it



        Input:
            trace (string, Sparam ('S11','S21','S12','S22')

        Output:
            None

        '''
        logging.info(__name__ + ' : start to measure and wait till it is finished')
        self._visainstrument.write('init:imm')
        #self._visainstrument.write('*WAI')
        self._visainstrument.write('*OPC')

    # def measure_modified(self):
        # '''
        # creates a trace to measure Sparam and displays it



        # Input:
            # trace (string, Sparam ('S11','S21','S12','S22')

        # Output:
            # None

        # '''
        # logging.info(__name__ + ' : start to measure and wait till it is finished')

       # self._visainstrument.write('*SRE 32')
       # self._visainstrument.write('*ESE 1')
        # self._visainstrument.write('init:imm; *OPC')


    # def gettrace(self):
        # '''

        # reades a trace from zvl

        # Input:

            # trace (string)

        # Output:

            # None
        # '''
        # logging.info(__name__ + ' : start to measure and wait till it is finished')

       # counter = 0
       # while counter < 10
           # counter += 1
           # try
               # dstring=self._visainstrument.query('calculate:Data:NSweep? Sdata, 1 ')
               # real,im= np.reshape(np.array(dstring.split(','),dtype=float),(-1,2)).T
               # break
           # except VisaIOError
               # qt.msleep(10)
       # return real+im*1j


        # counter=0
        # while self._visainstrument.query('*OPC?') != u'1\n':
            # qt.msleep(10)
            # counter +=1
            # if counter > 20:
                # break
        # else:
            # dstring=self._visainstrument.query('calculate:Data:NSweep? Sdata, 1 ')
            # real,im= np.reshape(np.array(dstring.split(','),dtype=float),(-1,2)).T
            # return real+im*1j

    def gettrace(self):
        '''

        reades a trace from zvl

        Input:

            trace (string)

        Output:

            None
        '''
        logging.info(__name__ + ' : start to measure and wait till it is finished')


        while self._visainstrument.query('*ESR?') != '1\n':
            qt.msleep(1)
        else:
			dstring=self._visainstrument.query('calculate:Data:NSweep? Sdata, 1 ')
			real,im= np.reshape(np.array(dstring.split(','),dtype=float),(-1,2)).T
			return real+im*1j

    def averageclear(self):
        '''
        Starts a new average cycle


        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : clear average')
        self._visainstrument.write('AVERage:CLEar')
#########################################################
#
#
#                  Write and Read from VISA
#
#
#########################################################
    def tell(self, cmd):
        self._visainstrument.write(cmd)
    def query(self, cmd):
        res= self._visainstrument.query(cmd + '?')
        print res
        return res
#########################################################
#
#
#                Frequency
#
#
#########################################################
    def do_set_centerfrequency(self, centerfrequency=1.):
        '''
            Set the center frequency of the instrument

            Input:
                frequency (float): Center frequency at which the instrument will measure [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency of the instrument')
        self._visainstrument.write('frequency:center '+str(centerfrequency))


    def do_get_centerfrequency(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been tuned [Hz]
        '''

        logging.info(__name__+' : Get the frequency of the instrument')
        return self._visainstrument.query('frequency:center?')

    def do_set_frequencyspan(self, frequencyspan=1.):
        '''
            Set the frequency span of the instrument

            Input:
                frequency (float): Frequency span at which the instrument will measure [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency of the instrument')
        self._visainstrument.write('frequency:span '+str(stopfrequency))


    def do_get_frequencyspan(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been tuned [Hz]
        '''

        logging.info(__name__+' : Get the frequency of the instrument')
        return self._visainstrument.query('frequency:span?')


    def do_set_startfrequency(self, startfrequency=1.):
        '''
            Set the start frequency of the instrument

            Input:
                frequency (float): Frequency at which the instrument will be tuned [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency of the instrument')
        self._visainstrument.write('frequency:start '+str(startfrequency))


    def do_get_startfrequency(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been tuned [Hz]
        '''

        logging.info(__name__+' : Get the frequency of the instrument')
        return self._visainstrument.query('frequency:start?')

    def do_set_stopfrequency(self, stopfrequency=1.):
        '''
            Set the start frequency of the instrument

            Input:
                frequency (float): Frequency at which the instrument will be tuned [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency of the instrument')
        self._visainstrument.write('frequency:stop '+str(stopfrequency))


    def do_get_stopfrequency(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been tuned [Hz]
        '''

        logging.info(__name__+' : Get the frequency of the instrument')
        return self._visainstrument.query('frequency:stop?')


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

        logging.info(__name__+' : Set the power of the instrument')
        self._visainstrument.write('source:power '+str(power))


    def do_get_power(self):
        '''
            Get the power of the instrument

            Input:
                None

            Output:

                power (float): power at which the instrument has been tuned [dBm]
        '''

        logging.info(__name__+' : Get the power of the instrument')
        return self._visainstrument.query('source:power?')

#########################################################
#
#
#                Averages
#
#
#########################################################

    def do_set_averages(self, averages=1):
        '''
            Set the averages of the instrument


            Input:
                phase (float): averages at which the instrument will be tuned [rad]

            Output:
                None
        '''

        logging.info(__name__+' : Set the averages of the instrument')
        self._visainstrument.write('average:count '+str(averages))


    def do_get_averages(self):
        '''
            Get the phase of the instrument


            Input:
                None

            Output:

                phase (float): averages of the instrument
        '''

        logging.info(__name__+' : Get the averages of the instrument')
        return self._visainstrument.query('average:count?')

    def do_get_averagestatus(self):
        """
        Reads the output status from the instrument

        Input:
            None


        Output:
            status (string) : 'on' or 'off'
        """
        logging.debug(__name__ + ' : get status')
        stat = self._visainstrument.query('average?')
        if stat=='1\n':
          return 'on'
        elif stat=='0\n':
          return 'off'
        else:
		  raise ValueError('Output status not specified : %s' % stat)

    def do_set_averagestatus(self, status='off'):
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
        self._visainstrument.write('average %s' % status.upper())


#########################################################
#
#
#                BW
#
#
#########################################################

    def do_set_measBW(self, measBW=1000):
        '''
            Set the measurement bandwidth of the instrument



            Input:
                measBW (float): measurement bandwidth [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the measurement bandwidth of the instrument')
        self._visainstrument.write('sens:band '+str(measBW))


    def do_get_measBW(self):
        '''
            Get the BW of the instrument

            Input:
                None

            Output:


                BW (float): measurement bandwidth [Hz]
        '''

        logging.info(__name__+' : Get the BW of the instrument')
        return self._visainstrument.query('sens:band?')


#########################################################
#
#
#                Points
#
#
#########################################################

    def do_set_points(self, points=1001):
        '''
            Set the points of the instrument


            Input:
                power (float): power to which the instrument will be tuned [dBm]

            Output:
                None
        '''

        logging.info(__name__+' : Set the power of the instrument')
        self._visainstrument.write('sens:sweep:points '+str(points))


    def do_get_points(self):
        '''
            Get the pointsof the instrument

            Input:
                None

            Output:

                BW (float): power at which the instrument has been tuned [dBm]
        '''

        logging.info(__name__+' : Get the BW of the instrument')
        return self._visainstrument.query('sens:sweep:points?')

#########################################################
#
#
#                Sweeps
#
#
#########################################################

    def do_set_sweeps(self, sweeps=1):
        '''
            Set the points of the instrument


            Input:
                power (float): sweeps of the instrument will be tuned

            Output:
                None
        '''

        logging.info(__name__+' : Set the power of the instrument')
        self._visainstrument.write('initiate:cont Off ')
        self._visainstrument.write('sens:sweep:count '+str(sweeps))


    def do_get_sweeps(self):
        '''
            Get the points of the instrument

            Input:
                None

            Output:

                BW (float):sweeps at which the instrument
        '''

        logging.info(__name__+' : Get the sweeps of the instrument')
        return self._visainstrument.query('sens:sweep:count?')


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
        stat = self._visainstrument.query('output?')

        if (stat=='1\n'):
          return 'on'
        elif (stat=='0\n'):
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
#                Methods
#
#
#########################################################

    def set_sweeptype(self, sweeptype='LIN'):
        '''
    	Define the type of the sweep: LINear | LOGarithmic

        Input:
            sweeptype (string): LIN, LOG
        Output:
            None
        '''
        logging.debug(__name__ + ' : The type of the sweep is set to %s' % sweeptype)
        if sweeptype.upper() in ('LIN'):
            self._visainstrument.write('SWE:TYPE LIN')
        elif sweeptype.upper() in ('LOG'):
            self._visainstrument.write('SWE:TYPE LOG')
        else:
            raise ValueError('set_sweeptype(): can only set LIN, LOG')
            
            
    def set_trigger(self, trigger='IMM'):
        '''
    	Define the source of the trigger: IMMediate (free run measurement or untriggered), EXTernal
        Input:
            trigger (string): IMM, EXT 
        Output:
            None
        '''
        logging.debug(__name__ + ' : The source of the trigger is set to %s' % trigger)
        if trigger.upper() in ('IMM'):
            self._visainstrument.write('TRIG:SOUR IMM')
        elif trigger.upper() in ('EXT'):
            self._visainstrument.write('TRIG:SOUR EXT')
        else:
            raise ValueError('set_trigger(): can only set IMM, EXT')
