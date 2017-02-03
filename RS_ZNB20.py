from instrument import Instrument
import visa
import logging
import types
from numpy import pi
import numpy as np

class RS_ZNB20(Instrument):
    '''
    This is the python driver for the ZNB20

    Usage:
    Initialize with
    <name> = instruments.create('name', 'ZNB20', address='<GPIB address>', reset=True|False)
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
        self._visainstrument = rm.open_resource(self._address)

        self._zerospan = False

        self.add_parameter('span', flags=Instrument.FLAG_GETSET, units='Hz', minval=1, maxval=20e9-100e3, type=types.FloatType)
        self.add_parameter('centerfreq', flags=Instrument.FLAG_GETSET, units='Hz', minval=100e3, maxval=20e9, type=types.FloatType)
        self.add_parameter('startfreq', flags=Instrument.FLAG_GETSET, units='Hz', minval=100e3, maxval=20e9, type=types.FloatType)
        self.add_parameter('stopfreq', flags=Instrument.FLAG_GETSET, units='Hz', minval=100e3, maxval=20e9, type=types.FloatType)
        self.add_parameter('power', flags=Instrument.FLAG_GETSET, units='dBm', maxval=10.0, type=types.FloatType)
        self.add_parameter('averages', flags=Instrument.FLAG_GETSET, units='', maxval=100000, type=types.FloatType)
        self.add_parameter('Average', flags=Instrument.FLAG_GETSET, option_list=['ON', 'OFF'], type=types.StringType)
        self.add_parameter('nop', flags=Instrument.FLAG_GETSET, units='', minval=1, maxval=100000, type=types.FloatType)
        self.add_parameter('bandwidth', flags=Instrument.FLAG_GETSET, units='Hz', minval=1, maxval=1e6, type=types.FloatType)
        self.add_parameter('status', flags=Instrument.FLAG_GETSET, option_list=['ON', 'OFF'], type=types.StringType)

#        self.add_parameter('zerospan', flags=Instrument.FLAG_GETSET, type=types.BooleanType)

        self.add_function ('get_all')
        self.add_function('reset')
#        self.add_function('get_freqpoints')
#        self.add_function('get_tracedata')
#        self.add_function('get_sweeptime')
        self.add_function('avg_clear')

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
        self.get_centerfreq()
        self.get_span()
        self.get_startfreq()
        self.get_stopfreq()
        self.get_averages()
        self.get_Average()
        self.get_nop()
        self.get_bandwidth()
        self.get_status()


###########################################################################################################################################################################
#
#                                                           Communication with device
#
############################################################################################################################################################################

    def get_sweeptime(self):
		return float(self._visainstrument.query('sweep:time?'))

    def avg_clear(self):
		self._visainstrument.write('average:clear')

    def meas_over(self):
		return bool(int(self._visainstrument.query('*ESR?')))

    def measure(self):
        '''
        init measurement
        Input:
        Output:
            None
        '''
        logging.info(__name__ + ' : start to measure and wait till it is finished')
        self._visainstrument.write('initiate:cont off')
        self._visainstrument.write('init:imm ')
        self._visainstrument.write('*OPC')

    # get_tracedata part

    def get_tracedata(self):
        '''
        Get the data of the current trace
        Input:
            None
        Output:
            complex trace values
        '''
        dstring=self._visainstrument.query('calculate:Data? Sdata')
        self._visainstrument.write('init:cont on')
        real,im= np.reshape(np.array(dstring.split(','),dtype=float),(-1,2)).T
        return real+im*1j

    def get_freqpoints(self, query = False):
        return np.linspace(self.get_startfreq(query),self.get_stopfreq(query),self.get_nop(query))

#########################################################
#
#                  Write and Read from VISA
#
#########################################################
    def tell(self, cmd):
        self._visainstrument.write(cmd)
    def query(self, cmd):
        res= self._visainstrument.query(cmd)
        print res
        return res
#########################################################
#
#                Frequency
#
#########################################################
    def do_set_centerfreq(self, centerfreq=1.):
        '''
            Set the center frequency of the instrument
            Input:
                frequency (float): Center frequency at which the instrument will measure [Hz]
            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency of the intrument')
        self._visainstrument.write('frequency:center '+str(centerfreq))
        self.get_startfreq()
        self.get_stopfreq()

    def do_get_centerfreq(self):
        '''
            Get the frequency of the instrument
            Input:
                None
            Output:
                frequency (float): frequency at which the instrument has been tuned [Hz]
        '''

        logging.info(__name__+' : Get the frequency of the intrument')
        return self._visainstrument.query('frequency:center?')

    def do_set_span(self, span=1.):
        '''
            Set the frequency span of the instrument
            Input:
                frequency (float): Frequency span at which the instrument will measure [Hz]
            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency of the intrument')
        self._visainstrument.write('frequency:span '+str(span))
        self.get_startfreq()
        self.get_stopfreq()


    def do_get_span(self):
        '''
            Get the frequency of the instrument
            Input:
                None
            Output:
                frequency (float): frequency at which the instrument has been tuned [Hz]
        '''
        logging.info(__name__+' : Get the frequency of the intrument')
        return self._visainstrument.query('frequency:span?')


    def do_set_startfreq(self, startfreq=1.):
        '''
            Set the start frequency of the instrument
            Input:
                frequency (float): Frequency at which the instrument will be tuned [Hz]
            Output:
                None
        '''
        logging.info(__name__+' : Set the frequency of the intrument')
        self._visainstrument.write('frequency:start '+str(startfreq))
        self.get_centerfreq()
        self.get_span()



    def do_get_startfreq(self):
        '''
            Get the frequency of the instrument
            Input:
                None
            Output:
                frequency (float): frequency at which the instrument has been tuned [Hz]
        '''
        logging.info(__name__+' : Get the frequency of the intrument')
        return self._visainstrument.query('frequency:start?')

    def do_set_stopfreq(self, stopfreq=1.):
        '''
            Set the stop frequency of the instrument
            Input:
                frequency (float): stop frequency at which the instrument will be tuned [Hz]
            Output:
                None
        '''
        logging.info(__name__+' : Set the stop frequency of the intrument')
        self._visainstrument.write('frequency:stop '+str(stopfreq))
        self.get_centerfreq()
        self.get_span()


    def do_get_stopfreq(self):
        '''
            Get the stop frequency of the instrument
            Input:
                None
            Output:
                frequency (float): stop frequency at which the instrument has been tuned [Hz]
        '''
        logging.info(__name__+' : Get the stop frequency of the intrument')
        return self._visainstrument.query('frequency:stop?')

#########################################################
#
#                Power
#
#########################################################

    def do_set_power(self, power=-10):
        '''
            Set the power of the instrument
            Input:
                power (float): power at which the instrument will be tuned [dBm]
            Output:
                None
        '''
        logging.info(__name__+' : Set the power of the intrument')
        self._visainstrument.write('source:power '+str(power))

    def do_get_power(self):
        '''
            Get the power of the instrument
            Input:
                None
            Output:
                power (float): power at which the instrument has been tuned [dBm]
        '''
        logging.info(__name__+' : Get the power of the intrument')
        return self._visainstrument.query('source:power?')

#########################################################
#
#                Averages
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
        logging.info(__name__+' : Set the averages of the intrument')
        self._visainstrument.write('average:count '+str(averages))
        if self.get_Average().upper() == 'ON':
            self._visainstrument.write('sens:sweep:count '+str(averages))

    def do_get_averages(self):
        '''
            Get the phase of the instrument
            Input:
                None
            Output:
                phase (float): averages of the instrument
        '''
        logging.info(__name__+' : Get the averages of the intrument')
        return self._visainstrument.query('average:count?')

    def do_set_Average(self, status='off'):
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
        if status == 'ON':
            self._visainstrument.write('sens:sweep:count '+str(self.get_averages()))
        else:
            self._visainstrument.write('sens:sweep:count 1')
        self._visainstrument.write('average %s' % status)


    def do_get_Average(self):
        '''
        Reads the output status from the instrument
        Input:
            None
        Output:
            status (string) : 'on' or 'off'
        '''
        logging.debug(__name__ + ' : get status')
        stat = self._visainstrument.query('average?')

        if (stat=='1'):
          return 'ON'
        elif (stat=='0'):
          return 'OFF'
        else:
          raise ValueError('Output status not specified : %s' % stat)
        return


#########################################################
#
#                Bandwidth
#
#########################################################

    def do_set_bandwidth(self, bandwidth=1000):
        '''
            Set the power of the instrument
            Input:
                power (float): power at which the instrument will be tuned [dBm]
            Output:
                None
        '''
        logging.info(__name__+' : Set the power of the intrument')
        self._visainstrument.write('sens:band '+str(bandwidth))

    def do_get_bandwidth(self):
        '''
            Get the BW of the instrument
            Input:
                None
            Output:
                BW (float): IF bandwidth
        '''

        logging.info(__name__+' : Get the BW of the intrument')
        return self._visainstrument.query('sens:band?')

#########################################################
#
#                Points
#
#########################################################

    def do_set_nop(self, points=1001):
        '''
            Set the number of points in the trace

            Input:
                points (int): number of points in the trace
            Output:
                None
        '''
        logging.info(__name__+' : Set the power of the intrument')
        self._visainstrument.write('sens:sweep:points '+str(points))

    def do_get_nop(self):
        '''
            Get the number of points in the trace
            Input:
                None
            Output:
                points (int): the number of points in the trace
        '''

        logging.info(__name__+' : Get the BW of the intrument')
        return self._visainstrument.query('sens:sweep:points?')

#########################################################
#
#                Zerospan
#
#########################################################

#    def do_set_zerospan(self,val):
#        '''
#        Zerospan is a virtual "zerospan" mode. In Zerospan physical span is set to
#        the minimal possible value (2Hz) and "averages" number of points is set.
#        Input:
#            val (bool) : True or False
#        Output:
#            None
#        '''
#        logging.debug(__name__ + ' : setting status to "%s"' % status)
#        if val not in [True, False]:
#            raise ValueError('set_zerospan(): can only set True or False')
#        if val:
#          self._oldnop = self.get_points()
#          self._oldspan = self.get_span()
#          if self.get_span() > 0.002:
#            Warning('Setting ZVL span to 2Hz for zerospan mode')
#            self.set_span(0.002)

#        av = self.get_averages()
#        self._zerospan = val
#        if val:
#            self.set_average(False)
#            self.set_averages(av)
#            if av<2:
#              av = 2
#        else:
#          self.set_average(True)
#          self.set_span(self._oldspan)
#          self.set_points(self._oldnop)
#          self.get_averages()
#        self.get_points()

#    def do_get_zerospan(self):
#        '''
#        Check weather the virtual zerospan mode is turned on
#        Input:
#            None
#        Output:
#            val (bool) : True or False
#        '''
#        return self._zerospan

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
          return 'ON'
        elif (stat=='0'):
          return 'OFF'
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
