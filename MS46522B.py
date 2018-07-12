# -*- coding: utf-8 -*-
# MS46522B.py is a driver for Anritsu MS46522B Vector Network Analyser
# written by Remy Dassonneville, 2017
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

class MS46522B(Instrument):
    '''
    This is the python driver for the MS46522B

    Usage:
    Initialize with
    <name> = instruments.create('name', 'MS46522B', address='<TCPIP address>',
    reset = True|False)
    '''

    def __init__(self, name, address, reset = False):
        '''
        Initializes the MS46522B

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

        self._visainstrument.write_termination = '\n'
        self._visainstrument.read_termination = '\n'

        self.add_parameter('sweeptype',
                           flags       = Instrument.FLAG_GETSET,
                           option_list = ['LIN', 'LOG', 'POW' , 'FSEGM','ISEGM','CW'],
                           type        = types.StringType)

        self.add_parameter('averagestatus',
                           flags       = Instrument.FLAG_GETSET,
                           type        = types.StringType)

        self.add_parameter('power',
                           flags       = Instrument.FLAG_GETSET,
                           units       = 'dBm',
                           minval      = -30.,
                           maxval      = 20.,
                           type        = types.FloatType,
                           channels=(1, 2),
                           channel_prefix='port%d_')

        self.add_parameter('status',
                           flags       = Instrument.FLAG_GETSET,
                           type        = types.StringType)

        self.add_parameter('frequencyspan',
                           flags       = Instrument.FLAG_GETSET,
                           units       = 'Hz',
                           minval      = 100e3,
                           maxval      = 20e9,
                           type        = types.FloatType)


        self.add_parameter('startfrequency',
                           flags       = Instrument.FLAG_GETSET,
                           units       = 'Hz',
                           minval      = 100e3,
                           maxval      = 20e9,
                           type        = types.FloatType)
        self.add_parameter('stopfrequency',
                           flags       = Instrument.FLAG_GETSET,
                           units       = 'Hz',
                           minval      = 100e3,
                           maxval      = 20e9,
                           type        = types.FloatType)

        self.add_parameter('centerfrequency',
                           flags       = Instrument.FLAG_GETSET,
                           units       = 'Hz',
                           minval      = 100e3,
                           maxval      = 20e9,
                           type        = types.FloatType)

        self.add_parameter('cwfrequency',
                           flags       = Instrument.FLAG_GETSET,
                           units       = 'Hz',
                           minval      = 100e3,
                           maxval      = 20e9,
                           type        = types.FloatType)

        self.add_parameter('points',
                           flags       = Instrument.FLAG_GETSET,
                           units       = '',
                           minval      = 1,
                           maxval      = 100000,
                           type        = types.FloatType)

        self.add_parameter('averages',
                           flags       = Instrument.FLAG_GETSET,
                           units       = '',
                           minval      = 1,
                           type        = types.IntType)
        self.add_parameter('measBW',
                           flags       = Instrument.FLAG_GETSET,
                           units       = 'Hz',
                           minval      = 0.1,
                           maxval      = 500e3,
                           type        = types.FloatType)
						
        self.add_parameter('CW_sweep_points',
                            flags		= Instrument.FLAG_GETSET,
                            units		= '',
                            minval		= 1,
                            maxval		= 20001,
                            type		= types.FloatType)
							
        self.add_parameter('ext_trig_type',
                           flags		= Instrument.FLAG_GETSET,
                           option_list = ['ALL', 'POIN'],
                           type        = types.StringType)						
							
	self.add_function('reset')

        if reset :

            self.reset()


################################################################################
#
#                Methods
#
################################################################################

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
        self.get_port1_power()
        self.get_port2_power()
        self.get_averages()
        self.get_averagestatus()
        self.get_points()
        self.get_measBW()
        self.get_status()
        self.get_cwfrequency()
        self.get_CW_sweep_points()
        self.get_ext_trig_type()


################################################################################
#
#               parameters
#
################################################################################
    def do_get_averagestatus(self):
        """
        Reads the average status from the instrument
        Input:
            None


        Output:
            status (string) : 'on' or 'off'
        """
        logging.debug(__name__ + ' : get average status')

        stat = self._visainstrument.query('sens:aver?')

        if stat=='1':
          return 'on'
        elif stat=='0':
          return 'off'
        else:
          raise ValueError('Average status not specified : %s' % stat)

    def do_set_averagestatus(self, status = 'off'):
        '''
        Set the average status of the instrument
        Input:
            status (string) : 'on' or 'off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set average status to %s' % status)
        if status in ('on', 'off'):
            self._visainstrument.write('sens:aver %s' % status)
        else:
            raise ValueError('set_status(): can only set on or off')

##########################################################
    def do_get_power(self, channel=1):
        '''
        Gets the power of the port 'channel'
        '''
        return self._visainstrument.query(':sour:pow:port%s?' %channel)

    def do_set_power(self, power, channel=1):
        '''
        Sets the power in dBm to the port 'channel'
        '''

        return self._visainstrument.write(':sour:pow:port%s %s' %(channel, power))

##########################################################
    def do_get_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (string) : 'on' or 'off'
        '''
        logging.debug(__name__ + ' : get status')
        stat = self._visainstrument.query(':syst:hold:rf?')

        if (stat=='1'):
          return 'on'
        elif (stat=='0'):
          return 'off'
        else:
          raise ValueError('Output status not specified : %s' % stat)
        return

    def do_set_status(self, status = 'off'):
        '''
        Set the output status of the instrument

        Input:
            status (string) : 'on' or 'off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        if status == 'on':
            self._visainstrument.write(':syst:hold:rf 1')
            self._visainstrument.write(':sens:hold:func cont')
        elif status == 'off':
            self._visainstrument.write(':syst:hold:rf 0')
            self._visainstrument.write(':sens:hold:func hold')
        else:
            raise ValueError('set_status(): can only set on or off')

##########################################################
    def do_set_frequencyspan(self, frequencyspan = 1.):
        '''
            Set the frequency span of the instrument

            Input:
                frequency (float): Frequency span at which the instrument will
                                   measure [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency span of the instrument')
        self._visainstrument.write('sense:frequency:span '+str(frequencyspan))

    def do_get_frequencyspan(self):
        '''
            Get the frequency span of the instrument

            Input:
                None

            Output:
                frequency (float): frequency span at which the instrument has been
                                   tuned [Hz]
        '''

        logging.info(__name__+' : Get the frequency span of the instrument')
        return self._visainstrument.query('sense:frequency:span?')

##########################################################
    def do_set_startfrequency(self, startfrequency = 1.):
        '''
            Set the start frequency of the instrument

            Input:
                frequency (float): Frequency at which the instrument will be
                                   tuned [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency of the instrument')
        self._visainstrument.write('SENS:FREQ:STAR '+str(startfrequency))

    def do_get_startfrequency(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been
                                   tuned [Hz]
        '''

        logging.info(__name__+' : Get the frequency of the instrument')
        return self._visainstrument.query('SENS:FREQ:STAR?')

##########################################################
    def do_set_stopfrequency(self, stopfrequency = 1.):
        '''
            Set the start frequency of the instrument

            Input:
                frequency (float): Frequency at which the instrument will be
                                   tuned [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency of the instrument')
        self._visainstrument.write('SENS:FREQ:STOP '+str(stopfrequency))

    def do_get_stopfrequency(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been
                                   tuned [Hz]
        '''

        logging.info(__name__+' : Get the frequency of the instrument')
        return self._visainstrument.query('SENS:FREQ:STOP?')

##########################################################
    def do_set_centerfrequency(self, centerfrequency = 1.):
        '''
            Set the center frequency of the instrument

            Input:
                center frequency (float): Center frequency at which the instrument
                                   will measure [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the center frequency of the instrument')
        self._visainstrument.write('SENS:frequency:center '+str(centerfrequency))

    def do_get_centerfrequency(self):
        '''
            Get the center frequency of the instrument

            Input:
                None

            Output:
                center frequency (float): center frequency at which the instrument has been
                                   tuned [Hz]
        '''

        logging.info(__name__+' : Get the center frequency of the instrument')
        return self._visainstrument.query('SENS:frequency:center?')

##########################################################
    def do_set_cwfrequency(self, cwfrequency = 1.):
        '''
            Set the CW frequency of the instrument

            Input:
                frequency (float): Frequency at which the instrument will be
                                   tuned [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the CW frequency of the instrument')
        self._visainstrument.write('SENS:FREQ:CW '+str(cwfrequency))

    def do_get_cwfrequency(self):
        '''
            Get the CW frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been
                                   tuned [Hz]
        '''

        logging.info(__name__+' : Get the CW frequency of the instrument')
        return self._visainstrument.query('SENS:FREQ:CW?')

##########################################################
    def do_set_points(self, points = 1001):
        '''
            Set the points of the instrument


            Input:
                points (int): number of measurement points

            Output:
                None
        '''

        logging.info(__name__+' : Set the number of points of the instrument')
        if self._visainstrument.query('sens:swe:cw:state?') == '1':
            return self._visainstrument.write('sens:sweep:cw:point '+str(points))
        else:
            return self._visainstrument.write('sens:sweep:point '+str(points))

    def do_get_points(self):
        '''
            Get the number of points of the instrument

            Input:
                None

            Output:

                BW (float): power at which the instrument has been tuned [dBm]
        '''

        logging.info(__name__+' : Get the number of points of the instrument')
        if self._visainstrument.query('sens:swe:cw:state?') == '1':
            return self._visainstrument.query('sens:sweep:cw:point?')
        else:
            return self._visainstrument.query('sens:sweep:point?')

##########################################################
    def do_set_averages(self, averages = 1):
        '''
            Set the averages of the instrument


            Input:
                phase (float): averages at which the instrument will be tuned
                               [rad]

            Output:
                None
        '''

        logging.info(__name__+' : Set the averages of the instrument')
        self._visainstrument.write('initiate:cont Off')
        self._visainstrument.write('sense:average:count '+str(averages))

    def do_get_averages(self):
        '''
            Get the phase of the instrument


            Input:
                None

            Output:

                phase (float): averages of the instrument
        '''

        logging.info(__name__+' : Get the averages of the instrument')
        return self._visainstrument.query('sense:average:count?')

##########################################################
    def do_set_measBW(self, measBW = 1000.):
        '''
            Set the measurement bandwidth of the instrument



            Input:
                measBW (float): measurement bandwidth [Hz]

            Output:
                None
        '''

        logging.info(__name__+\
                     ' : Set the measurement bandwidth of the instrument')
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

##########################################################
    def do_set_sweeptype(self, sweeptype = 'LIN'):
        '''
        Define the type of the sweep:
        LINear | LOGarithmic | POWer | CW | POINt | FSEGMent

        Input:
            sweeptype (string): LIN, LOG, POW, CW, POIN or FSEG
        Output:
            None
        '''
        logging.debug(__name__ +\
                      ' : The type of the sweep is set to %s' % sweeptype)

        if sweeptype.upper() in ('LIN', 'LOG', 'POW', 'ISEGM','FSEGM'):
            self._visainstrument.write('sens:swe:cw:state 0')
            self._visainstrument.write("SENS:SWE:TYPE "+str(sweeptype.upper()))

        elif sweeptype.upper() == 'CW':
            self._visainstrument.write("SENS:SWE:TYPE LIN") # default value...
            self._visainstrument.write('sens:swe:cw:state 1')
        else:
            raise ValueError('set_sweeptype(): can only set LIN, LOG, POW, CW, ISEGM or FSEGM')

    def do_get_sweeptype(self):
        '''
        Gets the type of the sweep:
        LINear | LOGarithmic | POWer | CW | POINt | FSEGMent

        Input:
            none
        Output:
            sweeptype (string): LIN, LOG, POW, CW, POIN or FSEG
        '''

        logging.debug(__name__ +\
					   ' : Gets the type of the sweep ')



        if self._visainstrument.query('sens:swe:cw:state?') == '1':
            return 'CW'
        else:
            return self._visainstrument.query('SENS:SWE:TYPE?')
			
			
			
    def do_set_CW_sweep_points(self, Number):
        '''
         Sets the CW sweep mode number of points.
		 

        Input:
            The input parameter is a unitless number
        Output:
            None
        '''
        logging.debug(__name__ +\
                      ' : The number of points for the CW sweep ')

        if Number >=1 and Number <= 20001:
            self._visainstrument.write("SENS:SWE:CW:POIN " + str(Number) )

        else:
            raise ValueError('set_CW_sweep_points(): can only set number of points between 1 and 20 001')				

		
    def do_get_CW_sweep_points(self):
        '''
         Gets the CW sweep mode number of points.
		 Outputs the CW sweep mode number of points

         Input:
               NONE
         Output:
              Number of points of the CW sweep
         '''
        logging.debug(__name__ +\
					   ' : Gets the number of points for the CW sweep  ')


        return self._visainstrument.query('SENS:SWE:CW:POIN?')

##########################################################
    def averageclear(self):
        '''
        Starts a new average cycle


        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : clear average')
        self._visainstrument.write(':sens:aver:clear')

##########################################################
    def set_trigger(self, trigger='INT'):
        '''

        Define the source of the trigger:

        Input:
            trigger (string): INT, EXT, MAN
            trigger: IMM
        Output:
            None
        '''

        logging.debug(__name__ +\
        ' : The source of the trigger is set to %s' % trigger)

        if trigger.upper() in ('INT', 'EXT', 'MAN'):
            self._visainstrument.write("TRIG:SOUR "+str(trigger.upper()))
        elif trigger.upper() == 'IMM':

            self._visainstrument.write("TRIG:SOUR INT")
            self._visainstrument.write('sens:hold:func sing')
            self._visainstrument.write('TRIG:IMM')
        else:
            raise ValueError('set_trigger(): can only set INT, EXT, MAN, IMM'
			
    def do_set_ext_trig_type(self, ext_trigger_type='ALL'):
        '''
        The command sets the type of trigger 
		that will be associated with the external trigger.

        Input:
            trigger_type (type): ALL, POIN
        Output:
            None
        '''

        logging.debug(__name__ +\
                      ' : The mode of external trigger is ')

        if ext_trigger_type.upper() in ('ALL', 'POIN'):
            self._visainstrument.write("TRIG:EXT:TYP "+str(ext_trigger_type.upper()))

        else:
            raise ValueError('set_ext_trig_type(): must be ALL or POIN')

    def do_get_ext_trig_type(self):
        '''
        The command gets the type of trigger 
		that will be associated with the external trigger.

        Input:
            None
        Output:
            ALL or POIN
        '''

        logging.debug(__name__ +\
                      ' : Gets the mode of external trigger')

        return self._visainstrument.query("TRIG:EXT:TYP? ")

##########################################################
    def create_traces(self, traces, Sparams):
        """
            Create traces in the ZNB
            Input:
                - traces (tuple): Name of the traces from which we get data.
                                  Should be a tuple of string.
                                  ('1', '2', ...)
                                  If only one trace write ('1',) to
                                  have a tuple.
                - Sparams (tuple): S parameters we want to acquire.
                                   Should be a tuple of string.
                                   ('Sparams', 'Sparams', ...)
                                   If only one S parameter, write ('Sparam1',)
                                   to have a tuple.

            Output:
                - None
        """


        # We check if parameters are tupples
        if type(traces) is not tuple and type(Sparams) is not tuple:
            raise ValueError('Traces and Sparams must be tuple type')

        # We check if traces and Sparam have the same length
        if len(traces) != len(Sparams):
            raise ValueError('Traces and Sparams must have the same length')

        # We check the type of traces elements
        if not all([type(trace) is str for trace in traces]):
            raise ValueError('Element in traces should be string type')

        # We check the type of sparams elements
        if not all([type(Sparam) is str for Sparam in Sparams]):
            raise ValueError('Element in Sparams should be string type')

        logging.info(__name__ + ' : create trace(s)')

        # First we erase memory
        self._visainstrument.write('calc:parameter:del:all')

        # For each traces we want, we create
        for trace, Sparam in zip(traces, Sparams):
            self._visainstrument.write('calc:parameter%s:def %s' % (trace, Sparam))
            if self._visainstrument.query('calc:parameter%s:def?'%trace) != Sparam:
                print self._visainstrument.query('calc:parameter%s:def?'%trace)
                raise ValueError(" The parameter %s was not well defined on the trace %s" %(Sparam, trace))

        # We display traces on the device
        # First we put display on
        self._visainstrument.write('disp:wind1:act')

        # Second we display all traces
        for i, trace in enumerate(traces):
            self._visainstrument.write('disp:wind1:trac%s' % (i + 1) ) #<- not sure if working....

        # We set the update of the display on
        # self._visainstrument.write('syst:disp:upd on') #<- not update command

        # We set continuous measurement off
        # The measurement will be stopped after the setted number of sweep
        self._visainstrument.write('init:cont off')

##########################################################
    def initialize_one_tone_spectroscopy(self, traces, Sparams):

        # Linear sweep in frequency
        self.set_sweeptype('lin')

        # Trigger to immediate
        self.set_trigger('IMM')     # NOT DONE

        # We create traces in memory
        self.create_traces(traces, Sparams)

        # No partial measurement
        # self.set_driving_mode('chopped')  # NOT DONE


        self.set_status('on')

    def initialize_two_tone_spectroscopy(self, traces, Sparams):

        # We measure all points at the same frequency
        self.set_sweeptype('CW')

        # Trigger to external since the vna will triggered by  another device
        self.set_trigger('EXT')
        self.set_ext_trig_type('POIN')

        # We create traces in memory
        self.create_traces(traces, Sparams)

        # We clear average
        self.averageclear()

        self.set_status('on')

##########################################################
    def get_data(self, trace, data_format = 'db-phase'):
        """
            Return data given by the ZNB in the asked format.
            Input:
                - trace (string): Name of the trace from which we get data
                - data_format (string): must be:
                                        'real-imag', 'db-phase', 'amp-phase'
                                        The phase is returned in rad.

            Output:
                - Following the data_format input it returns the tupples:
                    real, imag
                    db, phase
                    amp, phase
        """

        # Selects an existing trace as the active trace of the channel
        self._visainstrument.write('calc:parameter%s:sel' % (trace))
        print self._visainstrument.query('calc:parameter:sel?')

        # self._visainstrument.write('form:Data:head 0')
        # self._visainstrument.write('calc:form REIM')
        self._visainstrument.write('form:Data real')
        # Get data as a string
        # val = self._visainstrument.query('calculate:Data:Sdata?') # to be checked
        val2 = self._visainstrument.query_binary_values('calculate:Data:Sdata?',
                    datatype='d', is_big_endian=False, container=np.array)

        # Change the shape of the array to get the real an imaginary part
        real, imag = np.transpose(np.reshape(val2, (-1, 2)))

        if data_format.lower() == 'real-imag':
            return real, imag
        elif data_format.lower() == 'db-phase':
            return 20.*np.log10(abs(real + 1j*imag)), np.angle(real + 1j*imag)
        elif data_format.lower() == 'amp-phase':
            return abs(real + 1j*imag)**2., np.angle(real + 1j*imag)
        else:
            raise ValueError("data-format must be: 'real-imag', 'db-phase', 'amp-phase'.")

    def get_traces(self, traces, data_format = 'db-phase'):# to be checked
        """
            Return data given by the ZNB in the asked format.
            Input:
                - traces (tuple): Name of the traces from which we get data.
                                  Should be a tuple of string.
                                  ('trace1', 'trace2', ...)
                                  If only one trace write ('trace1',) to
                                  have a tuple.
                - data_format (string): must be:
                                        'real-imag', 'db-phase', 'amp-phase'
                                        The phase is returned in rad.


            Output:
                - Following the data_format input it returns the tupples:
                    (a1, a2), (b1, b2), ...
                    where a1, a2 are the db-phase, by default, of the trace1
                    and b1, b2 of the trace2.
        """

        # We check if traces is tuple type
        if type(traces) is not tuple :
            raise ValueError('Traces must be tuple type')

        # We check the type of traces elements
        if not all([type(trace) is str for trace in traces]):
            raise ValueError('Element in traces should be string type')

        logging.info(__name__ +' : start to measure and wait till it is finished')

        while self._visainstrument.query('sens:hold:func?') == 'SING': #self._visainstrument.query('*ESR?') != '1':
            qt.msleep(0.1)
            # print 'wait for the end of the sweep measurement'

        else:

            temp = []
            for trace in traces:
                # # print 'append'

                temp.append(self.get_data(trace, data_format = data_format))

            return temp

    def measure(self):# to be checked
        '''
        creates a trace to measure Sparam and displays it

        Input:

        Output:
            None

        '''
        logging.info(__name__ +\
                     ' : start to measure and wait untill it is finished')

        self._visainstrument.write('initiate:cont off')

        self._visainstrument.write('*CLS') # use of it?

        # self._visainstrument.write('INITiate1:IMMediate; *OPC')
        self._visainstrument.write('sens:hold:func sing')
        # self._visainstrument.write('TRIG:IMM')
