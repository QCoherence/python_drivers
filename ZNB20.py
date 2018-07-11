# -*- coding: utf-8 -*-
# ZNB20.py is a driver for Rohde & Schwarz ZNB20 Vector Network Analyser
# written by Thomas Weissl, modified by Nico Roch and Yuriy Krupko, 2014
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

class ZNB20(Instrument):
    '''
    This is the python driver for the ZNB20

    Usage:
    Initialize with
    <name> = instruments.create('name', 'ZNB20', address='<GPIB address>',
    reset = True|False)
    '''

    def __init__(self, name, address, reset = False):
        '''
        Initializes the ZNB20

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

        self.add_parameter('frequencyspan',
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

        self.add_parameter('power',
                           flags       = Instrument.FLAG_GETSET,
                           units       = 'dBm',
                           maxval      = 30.0,
                           type        = types.FloatType)

        self.add_parameter('startpower',
                           flags       =Instrument.FLAG_GETSET,
                           units       ='dBm',
                           maxval      =30.0,
                           type        =types.FloatType)

        self.add_parameter('stoppower',
                           flags       =Instrument.FLAG_GETSET,
                           units       ='dBm',
                           maxval      =30.0,
                           type        =types.FloatType)

        self.add_parameter('averages',
                           flags       = Instrument.FLAG_GETSET,
                           units       = '',
                           maxval      = 100000,
                           type        = types.FloatType)

        self.add_parameter('averagestatus',
                           flags       = Instrument.FLAG_GETSET,
                           option_list = ['on', 'off'],
                           type        = types.StringType)

        self.add_parameter('points',
                           flags       = Instrument.FLAG_GETSET,
                           units       = '',
                           minval      = 1,
                           maxval      = 100000,
                           type        = types.FloatType)

        self.add_parameter('sweeps',
                           flags       = Instrument.FLAG_GETSET,
                           units       = '',
                           minval      = 1,
                           maxval      = 1000,
                           type        = types.FloatType)

        self.add_parameter('measBW',
                           flags       = Instrument.FLAG_GETSET,
                           units       = 'Hz',
                           minval      = 0.1,
                           maxval      = 500e3,
                           type        = types.FloatType)

        self.add_parameter('status',
                           flags       = Instrument.FLAG_GETSET,
                           option_list = ['on', 'off'],
                           type        = types.StringType)

        self.add_parameter('cwfrequency',
                           flags       = Instrument.FLAG_GETSET,
                           units       = 'GHz',
                           minval      = 1e-4,
                           maxval      = 20,
                           type        = types.FloatType)

        self.add_parameter('driving_mode',
                           flags       = Instrument.FLAG_GETSET,
                           option_list = ['Auto', 'Alternated', 'Chopped'],
                           type        = types.StringType)



        self.add_function('get_all')
        self.add_function('reset')

        if reset :

            self.reset()


###################################################################
#
#                Methods
#
###################################################################

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
        self.get_startpower()
        self.get_stoppower()
        self.get_averages()
        self.get_averagestatus()
        self.get_points()
        self.get_sweeps()
        self.get_measBW()
        self.get_status()
        self.get_cwfrequency()
        self.get_driving_mode()



###################################################################
#
#                           Initialisation
#
###################################################################

    def initialize_one_tone_spectroscopy(self, traces, Sparams):

        # Linear sweep in frequency
        self.set_sweeptype('lin')

        # Trigger to immediate
        self.set_trigger('imm')

        # We create traces in memory
        self.create_traces(traces, Sparams)

        # No partial measurement
        self.set_driving_mode('chopped')

        self.set_status('on')



    def initialize_two_tone_spectroscopy(self, traces, Sparams):

        # We measure all points at the sae frequency
        self.set_sweeptype('poin')

        # Trigger to external since the znb will triggered by  another device
        self.set_trigger('ext')

        # We create traces in memory
        self.create_traces(traces, Sparams)

        # We clear average
        self.averageclear()
        self.set_trigger_link('POIN')
        self.set_status('on')

    def initialize_one_tone_power_sweep(self, traces, Sparams):

        # Linear sweep in frequency
        self.set_sweeptype('POW')

        # Trigger to immediate
        self.set_trigger('imm')

        # We create traces in memory
        self.create_traces(traces, Sparams)

        # No partial measurement
        self.set_driving_mode('chopped')

        self.set_status('on')
###################################################################
#
#                           Trace
#
###################################################################



    def create_traces(self, traces, Sparams):
        """
            Create traces in the ZNB
            Input:
                - traces (tuple): Name of the traces from which we get data.
                                  Should be a tuple of string.
                                  ('trace1', 'trace2', ...)
                                  If only one trace write ('trace1',) to
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
        self._visainstrument.write('calc:parameter:del:all ')

        # For each traces we want, we create
        for trace, Sparam in zip(traces, Sparams):
            self._visainstrument.write('calc:parameter:sdef  "%s","%s"'
                                       % (trace, Sparam))

        # We display traces on the device
        # First we put display on
        self._visainstrument.write('disp:wind1:stat on')

        # Second we display all traces
        for i, trace in enumerate(traces):
            self._visainstrument.write('disp:wind1:trac%s:feed "%s"'
                                       % (i + 1, trace))

        # We set the update od the display on
        self._visainstrument.write('syst:disp:upd on')

        # We set continuous measurement on off
        # The measurement will be stopped after the setted number of sweep
        self._visainstrument.write('init:cont off')



    def _get_data(self, trace, data_format = 'db-phase'):
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
        self._visainstrument.write('calc:parameter:sel "%s"' % (trace))

        # Get data as a string
        val = self._visainstrument.query('calculate:Data? Sdata')

        # Transform the string in a numpy array
        # np.fromstring is faster than np.array
        val = np.fromstring(val, sep = ',')

        # Change the shape of the array to get the real an imaginary part
        real, imag = np.transpose(np.reshape(val, (-1, 2)))

        if data_format.lower() == 'real-imag':
            return real, imag
        elif data_format.lower() == 'db-phase':
            try : 
                return 20.*np.log10(abs(real + 1j*imag)), np.angle(real + 1j*imag)
            except RuntimeError : 
                print 'Division by zero error - Phase'
                return np.ones_like(real)
        elif data_format.lower() == 'amp-phase':
            try : 
                return abs(real + 1j*imag)**2., np.angle(real + 1j*imag)
            except RuntimeError : 
                print 'Division by zero error - Amplitude'
                return np.ones_like(real)
        else:
            raise ValueError("data-format must be: 'real-imag', 'db-phase', 'amp-phase'.")


    def get_traces(self, traces, data_format = 'db-phase'):
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

        logging.info(__name__ +\
                     ' : start to measure and wait till it is finished')

        while self._visainstrument.query('*ESR?') != '1':
            qt.msleep(0.1)
        else:

            temp = []
            for trace in traces:

                temp.append(self._get_data(trace, data_format = data_format))

            return temp


    def measure(self):
        '''
        creates a trace to measure Sparam and displays it

        Input:
            trace (string, Sparam ('S11','S21','S12','S22')

        Output:
            None

        '''
        logging.info(__name__ +\
                     ' : start to measure and wait untill it is finished')
        self._visainstrument.write('initiate:cont off')
        self._visainstrument.write('*CLS')
        self._visainstrument.write('INITiate1:IMMediate; *OPC')


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

    def set_trigger(self, trigger='IMM'):
        '''

        Define the source of the trigger: IMMediate (free run measurement or
        untriggered), EXTernal, MANual or MULTiple

        Input:
            trigger (string): IMM, EXT, MAN or MULT
        Output:
            None
        '''

        logging.debug(__name__ +\
        ' : The source of the trigger is set to %s' % trigger)

        if trigger.upper() in ('IMM', 'EXT', 'MAN', 'MULT'):
            self._visainstrument.write("TRIG:SOUR "+str(trigger.upper()))

        else:
            raise ValueError('set_trigger(): can only set IMM, EXT, MAN or MULT')

    def set_trigger_link(self, link='POIN'):
        '''
        Define the link of the trigger: SWEep (trigger event starts an entire
        sweep), SEGMent (trigger event starts a sweep segment), POINt (trigger
        event starts measurement at the next sweep point) or PPOint (trigger
        event starts the next partial measurement at the current or at the next
        sweep point).

        Input:
            lin (string): SWE, SEGM, POIN or PPO
        Output:
            None
        '''

        logging.debug(__name__ +\
                      ' : The link of the trigger is set to %s' % link)

        if link.upper() in ('SWE', 'SEGM', 'POIN', 'PPO'):
            self._visainstrument.write("TRIG:LINK '"+str(link.upper())+"'")
        else:
            raise ValueError('set_trigger(): can only set  SWE, SEGM, POIN or PPO')


    def set_sweeptype(self, sweeptype = 'LIN'):
        '''
        Define the type of the sweep:
        LINear | LOGarithmic | POWer | CW | POINt | SEGMent

        Input:
            sweeptype (string): LIN, LOG, POW, CW, POIN or SEGM
        Output:
            None
        '''
        logging.debug(__name__ +\
                      ' : The type of the sweep is set to %s' % sweeptype)

        if sweeptype.upper() in ('LIN', 'LOG', 'POW', 'CW', 'POIN', 'SEGM'):
            self._visainstrument.write("SWE:TYPE "+str(sweeptype.upper()))
        else:
            raise ValueError('set_sweeptype(): can only set LIN, LOG, POW, CW, POIN or SEGM')


#########################################################
#
#           Functions related to Segmented sweeps
#
#########################################################

    def define_segment(self, segment_number, startfrequency, stopfrequency, points, power, time, BW ,set_time='dwell'):
        '''
        Define a segment indexed by segment_number.

        Input:
            startfrequency [GHz]= define the frequency at which the segment start
            stopfrequency [GHz]= define the frequency at which the segment stop
            points: define the number of points measured
            power [dBm]: define the power of the VNA
            time [s]: if set_time==dwell it is a delay for each partial measurement in the segment
                      if set_time==sweeptime, we define the duration of the sweep in the segment
            BW [Hz]: define the Bandwidth
        Output:
            None
        '''
        logging.debug(__name__ + ' : we are defining the segment number %s' % segment_number)

        # self._visainstrument.write('SEGM%s:DEL' % segment_number)
        if set_time == 'dwell':
            self._visainstrument.write('SEGM%s:DEF:SEL DWEL' %segment_number)

            self._visainstrument.write('SEGM%s:DEF %sGHZ,%sGHZ,%s,%sDBM,%sS,%s,%sHZ' \
                %(segment_number,startfrequency, stopfrequency, points, power, time,0, BW ) )
            # print self._visainstrument.query('SEGM%s:DEF?' %segment_number)

            ####################################################################
            # we have to look at the errors checking of freq start and freq stop....
            ####################################################################

            asked_freq_start = self._visainstrument.query('SEGM%s:FREQ:STAR?'% segment_number)
            given_freq_start = str(startfrequency*1e9)

            if np.float(asked_freq_start) != np.float(given_freq_start):
                print'error in setting start frequency at %s' %startfrequency
                print asked_freq_start, given_freq_start
                # print self._visainstrument.query('SEGM%s:FREQ:STAR?'% segment_number), unicode('%s' %int(startfrequency*1e9))
                # print 'set at %s' %freq_start/1e9

            asked_freq_stop = self._visainstrument.query('SEGM%s:FREQ:STOP?'% segment_number)
            given_freq_stop = str(stopfrequency*1e9)

            if np.float(asked_freq_stop) != np.float(given_freq_stop):
                print'error in setting stop frequency at %s' %stopfrequency
                print asked_freq_stop, given_freq_stop

            if self._visainstrument.query('SEGM%s:SWE:POIN?'% segment_number) != unicode('%s' %points):
                print'error in setting number of points'

            asked_power = self._visainstrument.query('SEGM%s:POW?'% segment_number)
            given_power = str(power)
            if np.float(asked_power) != np.float(given_power):
                print'error in setting power'
                print asked_power, given_power

                # print np.float(self._visainstrument.query('SEGM%s:POW?'% segment_number)), power

            asked_dwell = self._visainstrument.query('SEGM%s:SWE:DWEL?'% segment_number)
            given_dwell = str(time)
            if np.float(asked_dwell) != np.float(given_dwell):
                print'error in setting dwell time'
                print asked_dwell, given_dwell

            if self._visainstrument.query('SEGM%s:BWID?'% segment_number)!=unicode('%s' %BW):
                print'error in setting the bandwidth'

        elif set_time == 'sweeptime':
            self._visainstrument.write('SEGM%s:DEF:SEL SWT' %segment_number)

            self._visainstrument.write('SEGM%s:DEF %sGHZ,%sGHZ,%s,%sDBM,%sS,%s,%sHZ' \
                %(segment_number,startfrequency, stopfrequency, points, power, time,0, BW ) )

            if self._visainstrument.query('SEGM%s:FREQ:STAR?'% segment_number) != unicode('%s' %int(startfrequency*1e9)):
                print'error in setting start frequency at %s' %startfrequency
                # print 'set at %s' %freq_start/1e9

            if self._visainstrument.query('SEGM%s:FREQ:STOP?'% segment_number)!=unicode('%s' %int(stopfrequency*1e9)):
                print'error in setting stop frequency at %s' %stopfrequency

            if self._visainstrument.query('SEGM%s:SWE:POIN?'% segment_number)!=unicode('%s' %points):
                print'error in setting number of points'

            if self._visainstrument.query('SEGM%s:POW?'% segment_number)!=unicode('%s' %power):
                print'error in setting power'

            if self._visainstrument.query('SEGM%s:SWE:POIN?'% segment_number)!=unicode('%s' %time):
                print'error in setting dwell time'

            if self._visainstrument.query('SEGM%s:BWID?'% segment_number)!=unicode('%s' %BW):
                print'error in setting the bandwidth'

        else:
            print 'set_time should be dweel or sweeptime'

    def define_power_sweep(self, startpow, stoppow, steppow, cwfrequency, BW, time, set_time='dwell'):
        '''
        Make a sweep in power where startpow can be greater than stoppow

        Input:
            startpow [dBm] : define the power at which begin the sweep
            stoppow [dBm]: define the power at which finish the sweep
            steppow [dBm]: define the step of the sweep
            cwfrequency [GHz]: constant wave frequency of the VNA
            time [s]: if set_time==dwell it is a delay for each partial measurement in the segment
                      if set_time==sweeptime, we define the duration of the sweep in the segment
            BW [Hz]: define the Bandwidth

        Output:
            None
        '''
        logging.debug(__name__ + ' : making a sweep in power from %s to %s with a step of %s' % (startpow, stoppow, steppow))

        #Destroy all the remaining segments from previous measurement
        self._visainstrument.write('SEGM:DEL:ALL')

        if np.float(self._visainstrument.query('SEGM:COUNT?'))!=0:
            print 'Error: segments not deleted'

        pow_vec=np.arange(startpow, stoppow + steppow, steppow)
        point=len(pow_vec)
        for i in np.arange(point):
            self.define_segment(i+1, cwfrequency, cwfrequency,1, pow_vec[i],time, BW, set_time )

        if np.float(self._visainstrument.query('SEGM:COUNT?'))!=point:
            print 'Error: not the number of segment wanted'

    def define_power_sweep_vec(self, pow_vec, cwfrequency, BW, time, set_time='dwell'):
        '''
        Define a sweep in power with a power vector.

        Input:
            pow_vec [dBm] : define the power vector
            cwfrequency [GHz]: constant wave frequency of the VNA
            time [s]: if set_time==dwell it is a delay for each partial measurement in the segment
                      if set_time==sweeptime, we define the duration of the sweep in the segment
            BW [Hz]: define the Bandwidth

        Output:
            None
        '''
        logging.debug(__name__ + ' : making a sweep in power' % ())

        #Delete all the remaining segments from previous measurement
        self._visainstrument.write('SEGM:DEL:ALL')

        if np.float(self._visainstrument.query('SEGM:COUNT?')) != 0:
            print 'Error: segments not deleted'

        point = len(pow_vec)
        for i in np.arange(point):
            self.define_segment(i+1, cwfrequency, cwfrequency,1, pow_vec[i],time, BW, set_time )

        if np.float(self._visainstrument.query('SEGM:COUNT?')) != point:
            print 'Error: not the number of segment wanted'


#########################################################
#
#                Frequency
#
#########################################################


    def do_set_centerfrequency(self, centerfrequency = 1.):
        '''
            Set the center frequency of the instrument

            Input:
                frequency (float): Center frequency at which the instrument
                                   will measure [Hz]

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
                frequency (float): frequency at which the instrument has been
                                   tuned [Hz]
        '''

        logging.info(__name__+' : Get the frequency of the instrument')
        return self._visainstrument.query('frequency:center?')

    def do_set_frequencyspan(self, frequencyspan = 1.):
        '''
            Set the frequency span of the instrument

            Input:
                frequency (float): Frequency span at which the instrument will
                                   measure [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency of the instrument')
        self._visainstrument.write('frequency:span '+str(frequencyspan))


    def do_get_frequencyspan(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been
                                   tuned [Hz]
        '''

        logging.info(__name__+' : Get the frequency of the instrument')
        return self._visainstrument.query('frequency:span?')


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
        self._visainstrument.write('frequency:start '+str(startfrequency))


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
        return self._visainstrument.query('frequency:start?')

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
        self._visainstrument.write('frequency:stop '+str(stopfrequency))


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
        return self._visainstrument.query('frequency:stop?')


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
        self._visainstrument.write('SOUR:FREQ:CW '+str(cwfrequency)+ 'GHz')

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
        return self._visainstrument.query('SOUR:FREQ:CW?')


#########################################################
#
#                Power
#
#########################################################


    def do_set_power(self, power = -40.):
        '''
            Set the power of the instrument


            Input:
                power (float): power at which the instrument will be tuned
                               [dBm]

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

                power (float): power at which the instrument has been tuned
                               [dBm]
        '''

        logging.info(__name__+' : Get the power of the instrument')
        return self._visainstrument.query('source:power?')


    def do_set_startpower(self, startpower=-40.):
        '''
            Set the start power of the instrument

            Input:
                power (float): start power at which the instrument will be tuned [dBm]

            Output:
                None
        '''

        logging.info(__name__+' : Set the start power of the instrument')
        self._visainstrument.write('SOUR:POW:STAR '+str(startpower))


    def do_get_startpower(self):
        '''
            Get the start power of the instrument

            Input:
                None

            Output:
                power (float): start power at which the instrument has been tuned [dBm]
        '''

        logging.info(__name__+' : Get the start power of the instrument')
        return self._visainstrument.query('SOUR:POW:STAR?')

    def do_set_stoppower(self, stoppower = -40.):
        '''
            Set the stop power of the instrument

            Input:
                power (float): stop power at which the instrument will be tuned [dBm]

            Output:
                None
        '''

        logging.info(__name__+' : Set the stop power of the instrument')
        self._visainstrument.write('SOUR:POW:STOP '+str(stoppower))


    def do_get_stoppower(self):
        '''
            Get the stop power of the instrument

            Input:
                None

            Output:
                power (float): stop power at which the instrument has been tuned [Hz]
        '''

        logging.info(__name__+' : Get the stop power of the instrument')
        return self._visainstrument.query('SOUR:POW:STOP?')


#########################################################
#
#                Averages
#
#########################################################

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

        if stat=='1':
          return 'on'
        elif stat=='0':
          return 'off'
        else:
          raise ValueError('Output status not specified : %s' % stat)

    def do_set_averagestatus(self, status = 'off'):
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
#                BW
#
#########################################################

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


#########################################################
#
#                Points
#
#########################################################

    def do_set_points(self, points = 1001):
        '''
            Set the points of the instrument


            Input:
                power (float): power to which the instrument will be tuned
                               [dBm]

            Output:
                None
        '''

        logging.info(__name__+' : Set the number of points for the sweep')
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
#                Sweeps
#
#########################################################

    def do_set_sweeps(self, sweeps = 1):
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
#                Status
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
        if status.upper() in ('ON', 'OFF'):
            status = status.upper()
        else:
            raise ValueError('set_status(): can only set on or off')
        self._visainstrument.write('output %s' % status)


#########################################################
#
#                Driving mode
#
#########################################################

    def do_get_driving_mode(self):
        '''
        Get the driving mode see page 423 of the manual for details

        Input:
            None

        Output:
            mode (string) : 'auto', 'alternated', 'chopped'
        '''

        logging.debug(__name__ + ' : get the drving mode')

        mode = self._visainstrument.write('COUP?')

        if mode.lower() == 'auto':
            return 'Auto'
        elif mode.lower() == 'none':
            return 'Alternated'
        elif mode.lower() == 'all':
            return 'Chopped'


    def do_set_driving_mode(self, mode):
        '''
        Set the driving mode see page 423 of the manual for details

        Input:
            mode (string) : 'auto', 'alternated', 'chopped'

        Output:
            None
        '''

        logging.debug(__name__ + ' : set the drving mode to %s' % mode)

        if mode.lower() == 'auto':
            self._visainstrument.write('COUP AUTO')
        elif mode.lower() == 'alternated':
            self._visainstrument.write('COUP NONE')
        elif mode.lower() == 'chopped':
            self._visainstrument.write('COUP ALL')
        else:
            raise ValueError("The mode must be 'auto', 'alternated' or 'chopped'")