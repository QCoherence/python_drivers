# =======================================
#                       Pulsing computer communication
# =======================================
import os
import socket

from instrument import Instrument
import types
from time import sleep
import logging
import pickle
import lib.config
import numpy as np


class highland_T560(Instrument):
    '''
        None
    '''

    def __init__(self, name, host='10.0.0.4', reset=False):
        '''
           None
        '''
        logging.info(__name__ + ' : Initializing instrument Highland T560 delay generator')
        Instrument.__init__(self, name, tags=['physical'])

        self._numcards = int(4)
        self._channels = ('A','B','C','D')

        self._host = host
        self._localhost = ''

        self._port = 10001 # opened remotely
        self._meas_start = 1000 # default value (after reset is done)

        self.add_function('get_all')
        self.add_function('reset')
#         self.add_function('ch_off')

        self.add_parameter('chA_width',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=2, maxval=1e10,
            units='ns'
            )
        self.add_parameter('chA_delay',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=1e10,
            units='ns'
            )

        self.add_parameter('chB_width',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=2, maxval=1e10,
            units='ns'
            )
        self.add_parameter('chB_delay',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=1e10,
            units='ns'
            )

        self.add_parameter('chC_width',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=2, maxval=1e10,
            units='ns'
            )
        self.add_parameter('chC_delay',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=1e10,
            units='ns'
            )

        self.add_parameter('chD_width',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=2, maxval=1e10,
            units='ns'
            )
        self.add_parameter('chD_delay',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=1e10,
            units='ns'
            )
            
        self.add_parameter('polarity',
            type=types.StringType,
            option_list=['POS','NEG'],
            flags=Instrument.FLAG_GETSET,
            channels=self._channels,
            channel_prefix='ch%c_'
            )
        self.add_parameter('status',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            option_list=['ON','OFF'],
            channels=self._channels,
            channel_prefix='ch%c_'
            )
        self.add_parameter('period',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='ns'
            )
        # self.add_parameter('period_multiplier',
            # type=types.IntType,
            # flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            # minval=1,
            # units='none'
            # )
        

        if reset:
            self._reset()
        self._initialize()
        self.get_all()


    def ask(self, msg):
        return self._ask(msg)

    def _ask(self, msg, buffer=1024):
        sout = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sout.settimeout(5)
        sout.connect((self._host, self._port))
        sout.sendall(msg+'\r')
        return sout.recvfrom(buffer)[0]

    def reset(self):
        self._reset()
    def _reset(self):
        self._ask('LOAD DEFAULT')
        self._initialize()

    def _initialize(self):

#        self._ask('TRIGGER SYN')

        self._ask('AUTOINSTALL 1')
#        self._ask('TLevel 2.5')
        self._ask('CLOCK IN')
        self._ask('TRIGGER INT')
#        self._ask('TRIGGER POS')
        self._ask('VERBOSE 0')
        self._ask('TDIV 88')
        
        self.ask('adelay 0n')
        self.ask('bdelay 0n')
        self.ask('cdelay 0n')
        self.ask('ddelay 0n')
        
        self.ask('awidth 0n')
        self.ask('bwidth 0n')
        self.ask('cwidth 0n')
        self.ask('dwidth 0n')
        
        self.ask('aset POS')
        self.ask('bset POS')
        self.ask('cset POS')
        self.ask('dset POS')
        
        

    def get_all(self):
        self.get_chA_delay()
        self.get_chB_delay()
        self.get_chC_delay()
        self.get_chD_delay()
        
        self.get_chA_width()
        self.get_chB_width()
        self.get_chC_width()
        self.get_chD_width()
        
        self.get_chA_status()
        self.get_chB_status()
        self.get_chC_status()
        self.get_chD_status()
        
        self.get_chA_polarity()
        self.get_chB_polarity()
        self.get_chC_polarity()
        self.get_chD_polarity()
        
        self.get_period()

#    def do_get_delay(self, channel):
#        return 1e9*float(self._ask(channel+'DELAY'))

#    def do_set_delay(self, val,channel):
#        print channel
#        msg= '{}Delay {:.2f}'.format(channel,val)
#        self._ask(msg)
#        self.set_period(self.get_period(query=False), update = False, channel=channel, param='delay', param_val=val)

    def do_get_status(self,channel):
        return self._ask(channel+'SET').split(' ')[5]

    def do_set_status(self,s,channel):
        if s.upper() in  ['ON','OFF']:
            self._ask(channel +'SET '+ s.upper())
        else:
            pass

    def do_get_polarity(self,channel):
        return self._ask(channel+'SET').split(' ')[3]

    def do_set_polarity(self,pol,channel):
        if pol.upper() in  ['POS','NEG']:
            self._ask(channel +'SET '+ pol.upper())
        else:
            pass


    def do_set_chA_delay(self, delay):
        """
            Set the delay of the channel A.
                Input:
                    - delay (float) : delay in nanosecond
        """
        
        if delay + self.do_get_chA_width() < self.do_get_period()*self.do_get_trigDiv() - 50 :
            self._ask('adelay '+str(delay)+'n')
        else:
            raise ValueError('The period is too short to contain your pulse.')


    def do_set_chB_delay(self, delay):
        """
            Set the delay of the channel B.
                Input:
                    - delay (float) : delay in nanosecond
        """
        
        if delay + self.do_get_chB_width() < self.do_get_period() *self.do_get_trigDiv()- 50 :
            self._ask('bdelay '+str(delay)+'n')
        else:
            raise ValueError('The period is too short to contain your pulse.')


    def do_set_chC_delay(self, delay):
        """
            Set the delay of the channel C.
                Input:
                    - delay (float) : delay in nanosecond
        """
        
        if delay + self.do_get_chC_width() < self.do_get_period() - 50 :
            self._ask('cdelay '+str(delay)+'n')
        else:
            raise ValueError('The period is too short to contain your pulse.')


    def do_set_chD_delay(self, delay):
        """
            Set the delay of the channel D.
                Input:
                    - delay (float) : delay in nanosecond
        """
        
        if delay + self.do_get_chD_width() < self.do_get_period() - 50 :
            self._ask('ddelay '+str(delay)+'n')
        else:
            raise ValueError('The period is too short to contain your pulse.')



    def do_get_chA_delay(self):
        """
            Get the delay of the channel A.
                Ouput:
                    - delay (float) : delay in nanosecond
        """
        
        return float(self._ask('adelay'))*1e9



    def do_get_chB_delay(self):
        """
            Get the delay of the channel B.
                Ouput:
                    - delay (float) : delay in nanosecond
        """
        
        return float(self._ask('bdelay'))*1e9



    def do_get_chC_delay(self):
        """
            Get the delay of the channel C.
                Ouput:
                    - delay (float) : delay in nanosecond
        """
        
        return float(self._ask('cdelay'))*1e9



    def do_get_chD_delay(self):
        """
            Get the delay of the channel D.
                Ouput:
                    - delay (float) : delay in nanosecond
        """
        
        return float(self._ask('ddelay'))*1e9



    def do_set_chA_width(self, width):
        """
            Set the width of the channel A.
                Input:
                    - width (float) : width in nanosecond
        """

        if width + self.do_get_chA_delay() < self.do_get_period()*self.do_get_trigDiv() - 50 :
            self._ask('awidth '+str(width)+'n')
        else:
            raise ValueError('The period is too short to contain your pulse.')


    def do_set_chB_width(self, width):
        """
            Set the width of the channel B.
                Input:
                    - width (float) : width in nanosecond
        """
        
        if width + self.do_get_chB_delay() < self.do_get_period() - 50 :
            self._ask('bwidth '+str(width)+'n')
        else:
            raise ValueError('The period is too short to contain your pulse.')



    def do_set_chC_width(self, width):
        """
            Set the width of the channel C.
                Input:
                    - width (float) : width in nanosecond
        """

        if width + self.do_get_chC_delay() < self.do_get_period() - 50 :
            self._ask('cwidth '+str(width)+'n')
        else:
            raise ValueError('The period is too short to contain your pulse.')



    def do_set_chD_width(self, width):
        """
            Set the width of the channel D.
                Input:
                    - width (float) : width in nanosecond
        """

        if width + self.do_get_chD_delay() < self.do_get_period() - 50 :
            self._ask('dwidth '+str(width)+'n')
        else:
            raise ValueError('The period is too short to contain your pulse.')



    def do_get_chA_width(self):
        """
            Set the width of the channel A.
                Ouput:
                    - width (float) : width in nanosecond
        """
        
        return float(self._ask('awidth'))*1e9



    def do_get_chB_width(self):
        """
            Set the width of the channel B.
                Ouput:
                    - width (float) : width in nanosecond
        """
        
        return float(self._ask('bwidth'))*1e9



    def do_get_chC_width(self):
        """
            Set the width of the channel C.
                Ouput:
                    - width (float) : width in nanosecond
        """
        
        return float(self._ask('cwidth'))*1e9



    def do_get_chD_width(self):
        """
            Set the width of the channel D.
                Ouput:
                    - width (float) : width in nanosecond
        """
        
        return float(self._ask('dwidth'))*1e9



    # def do_set_period_multiplier(self, period_multiplier):
        # """
            # Set the period multiplier. The physical period is period_multiplier*(12.5 ns).
                # Input:
                    # - period_multiplier (int) : period multiplier (dimensionless)
        # """
        
        
        # self._ask('tdiv '+str(period_multiplier))
        # self.get_period(self)

    # def do_get_period_multiplier(self):
        # """
            # Get the period multiplier. The physical period is period_multiplier*(12.5 ns).
                # Output:
                    # - period_multiplier (int) : period multiplier (dimensionless)
        # """
        
        # return int(self._ask('tdiv'))
        

    def do_set_period(self, period):
        """
            Set the closest period available with the Highland.
            
            Input:
                - period (Float): Period of the pulser in [ns].
            
            Output:
                - None
        """
        
        #We get the mutlplier of the internal clock
        #The minimal step in time is 12.5ns
        #The minimal step in multiplier is 8
        multiplier = round(period/12.5/8.)
        
        #We calculate the Tdiv to set
        tdiv = multiplier*8.
        period = tdiv * 12.5
        
        conditions = np.array([ self.get_chA_delay() + self.get_chA_width(),
                                self.get_chB_delay() + self.get_chB_width(), 
                                self.get_chC_delay() + self.get_chC_width(), 
                                self.get_chD_delay() + self.get_chD_width()])
        
        booleenCondition = conditions > period
            
        #Next we check if the period is longer than all channel width + delay
        if booleenCondition.any():
            raise ValueError('Period too short to contain the channel: '+str(self._channels[conditions.argmax()]))
        else:
            self._ask('tdiv '+str(tdiv))



    def do_get_period(self):
        """
            Get the period (a multiple of the internal trigger period 12.5 ns).
                Input:
                    - period (float) : period in nanoseconds
        """
        return float(self._ask('tdiv'))*12.5

#    def do_set_period(self,val, update=True, channel=None, param=None, param_val=None):
#        up = update
#        sq_len = 60.0
#        for ch in self._channels:
#            st = self.get('ch%c_status'%ch, query=False).upper()
#            if st =='ON':
#                if ch == channel:
#                    if param=='width':
#                        ch_len = 60 + param_val + self.get('ch%c_delay'%ch, query=False)
#                    elif param=='delay':
#                        ch_len = 60 + self.get('ch%c_width'%ch, query=False) + param_val
#                    else:
#                        ch_len = 60 + self.get('ch%c_width'%ch, query=False) + self.get('ch%c_delay'%ch, query=False)
#                else:
#                    ch_len = 60 + self.get('ch%c_width'%ch, query=False) + self.get('ch%c_delay'%ch, query=False)
#            else:
#                ch_len = 60
#            if ch_len > sq_len:
#                sq_len = ch_len
#        if sq_len > val:
#            freq = 1e9/sq_len
#            up = True
#        else:
#            freq = 1e9/val
#        if freq > 16e6:
#            freq = 16e6
#        if up:
#            self._ask('SY {:.2f}'.format(freq))




    def do_get_trigDiv(self):
        return float(self._ask('TD'))
