from instrument import Instrument
import instruments
import types
import logging
import _Tektronix_AWG520.wfms as AWG520_wfms

class virtual_awgpulse_burst(Instrument):
    '''
    Defines a burst of pulses.
    level -- pulses amplitude
    pulse_length -- length of a pulse
    period -- period of the sequence, e.g. time between risefronts of two conseq. pulses
    length -- length of the burst
    delay -- delay between the burst end and the "measurement start"
    
    '''

    def __init__(self, name, awg, channel, conversion = 1, dt = 0, pulsedef=None, amplitude=2.0,\
                                                            offset=0.0, pulser=None, cardnr=None):
        '''
        awg has following properties:

        baseline offset
        
        multiple plateaus with each:

        start time
        ramp time
        ramp type
        height of plateau


        ending with:
        fall time
        fall type


        think about:
        channels
        '''
        Instrument.__init__(self, name, tags=['virtual'])
        
        # Defining some stuff 
        self._instruments = instruments.get_instruments()
        self._awg = self._instruments.get(awg)
        self._channel = channel
        self._clock = self._awg.get_clock()
        self._numpoints = self._awg.get_numpoints()
        self._amplitude = amplitude #FIXME ugly use of variables _amplitude and _offset
        self._offset = offset
        self._filename = 'ch%d.wfm' % self._channel
        
        #pulser
        self._pulser = self._instruments.get(pulser)
        self._cardnr = cardnr
        
#        self._npulse = 0 # Number of pulses in the bursts
#        self._period = 0 # Sequence period
#        self._plen = 0 # Length of a pulse in the burst
        
        self.add_parameter('delay',
                type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                units='ns')
        self.add_parameter('period',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='ns')
        self.add_parameter('pulse_length',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='ns')
                
        self.add_parameter('conversion',
                type=types.FloatType,
                flags=Instrument.FLAG_GET,
                units=' ')
        self._conversion = conversion  #Conversion factor to universal mV
        self.get_conversion()
        
        self.add_parameter('dt',
                type=types.FloatType,
                flags=Instrument.FLAG_GET,
                units='ns')
        self._dt = dt  #dt to universal zero
        self.get_dt()
        
        # Add parameters
        self.add_parameter('awg_amplitude', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='V')
        self.add_parameter('awg_offset', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='V')
        self.add_parameter('awg_status', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)

        self.add_parameter('baselevel', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='mV')
        self.add_parameter('starttime', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='ns')
        self.add_parameter('risetime', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='ns')
        self.add_parameter('risetype', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)

        self.add_parameter('level', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='mV')
        self.add_parameter('level0', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='mV')
        self.add_parameter('length', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='ns')
        self.add_parameter('falltime', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='ns')
        self.add_parameter('falltype', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)

        # Initializing AWG Channel
        w = AWG520_wfms.Channel_Zeros(self._numpoints)
        m1 = AWG520_wfms.Marker_Zeros(self._numpoints)
        m2 = AWG520_wfms.Marker_Zeros(self._numpoints)

        self._awg.send_waveform(w,m1,m2,self._filename, self._clock)
        self._awg.set('ch%d_filename' % self._channel, self._filename)
        self.set_awg_amplitude(amplitude)
        self.set_awg_offset(offset)

        if pulsedef is not None:
            self.set_pulsedef(pulsedef)

        self.get_all()

    # functions
    def get_all(self):
        self.get_awg_amplitude()
        self.get_awg_offset()
        self.get_awg_status()
        
        self.get_delay()
        self.get_period()
        self.get_pulse_length()

        self.get_baselevel()
        self.get_starttime()
        self.get_risetime()
        self.get_risetype()
        self.get_level()
        self.get_level0()
        self.get_length()
        self.get_falltime()
        self.get_falltype()
    
    def do_get_conversion(self):
        return self._conversion
        
#    def do_set_conversion(self):
#        print 'Do a careful calibration and restart QTLab'
           
    def do_get_dt(self):
        return self._dt
        
#    def do_set_dt(self):
#        print 'Do a careful calibration and restart QTLab'
        
    def set_pulsedef(self, pulsedef):
        self.unpack_pulsedef(pulsedef)
        self.resend_waveform()

    def unpack_pulsedef(self, pulsedef):
        self._baselevel = pulsedef[0][0]
        self._falltime = pulsedef[0][1]
        self._falltype = pulsedef[0][2]
        self._starttime = pulsedef[0][3]

        self._level = pulsedef[1][0]
        self._risetime = pulsedef[1][1]
        self._risetype = pulsedef[1][2]
        self._plen = pulsedef[1][3]
        
        self._level0 = pulsedef[2][0]
        self._period = pulsedef[2][3] + self._plen + self._risetime + self._falltime
        
        self._tail = pulsedef[(pulsedef.__len__() - 1)][3]
        
        self._npulse, extra_p = divmod(pulsedef.__len__(),2) 
        self._npulse -=1
        if extra_p:
            self._tail += (self._plen + self._risetime + self._falltime)

        self._length = self._period * self._npulse + self._tail
        
    def pack_pulsedef(self):
        self._npulse, self._tail = divmod(self._length,self._period)
        self._npulse = int(self._npulse)

        pulsedef = [(self._baselevel*1e-3*self._conversion, self._falltime*1e-9, self._falltype, self._starttime*1e-9)]
        interval = self._period - self._plen - self._risetime - self._falltime
        if interval < 0 :
            interval = 0
         
        tuple1 = (self._level*1e-3*self._conversion, self._risetime*1e-9, self._risetype, self._plen*1e-9)
        tuple2 = (self._level0*1e-3*self._conversion, self._falltime*1e-9, self._falltype, interval*1e-9)
        
        for n in range(self._npulse):
            pulsedef.extend([tuple1, tuple2])
        
        if (self._tail >= (self._plen + self._risetime + self._falltime)) and(self._npulse >= 0):
            self._tail -= (self._plen + self._risetime + self._falltime)
            pulsedef.extend([tuple1])

        tail_level = (self._level0*1e-3*self._conversion, self._falltime*1e-9, self._falltype, self._tail*1e-9)
        pulsedef.extend([tail_level])
        return pulsedef

    def resend_waveform(self):
        w_all = self.create_waveform()
        self._awg.resend_waveform(self._channel, w=w_all[0])

    def create_waveform(self):
        pulsedef = self.pack_pulsedef()
        waveform_period = self._numpoints/self._clock
        w_all = AWG520_wfms.Channel_MultiLevel_Pulse(self._clock, waveform_period, pulsedef, \
                                                amplitude=self._amplitude, offset=self._offset)
        return w_all

    def plot_waveform(self):
        w_all = self.create_waveform()
        AWG520_wfms.plot(w_all)

    def plot_waveform_raw(self):
        w_all = self.create_waveform()
        print 'amplitude = %f' % w_all[1]
        print 'offset = %f' % w_all[2]
        AWG520_wfms.plot(w_all[0])

    # parameters
    def _do_get_awg_amplitude(self):
        self._amplitude = self._awg.get('ch%d_amplitude' % self._channel)
        return self._amplitude

    def _do_set_awg_amplitude(self, amp):
        self._amplitude = amp
        return self._awg.set('ch%d_amplitude' % self._channel, amp)

    def _do_get_awg_offset(self):
        self._offset = self._awg.get('ch%d_offset' % self._channel)
        return self._offset

    def _do_set_awg_offset(self, offset):
        self._offset = offset
        return self._awg.set('ch%d_offset' % self._channel, offset)

    def _do_get_awg_status(self):
        return self._awg.get('ch%d_status' % self._channel)

    def _do_set_awg_status(self, status):
        return self._awg.set('ch%d_status' % self._channel, status)

    def _do_get_baselevel(self):
        return self._baselevel

    def _do_set_baselevel(self, baselevel, resend=True):
        self._baselevel = baselevel
        if resend:
            self.resend_waveform()

    def _do_get_starttime(self):
        return self._starttime

    def _do_set_starttime(self, starttime, resend=True):
        self._starttime = starttime
        st_p=self._pulser.get_measurement_start()
        delay = self.get_delay(query=False) + self._dt
        length = self._length
        
        self._pulser.set('card%d_fireA' % self._cardnr, st_p - delay - length - self._starttime)
        self._pulser.set('card%d_fireB' % self._cardnr, st_p - delay - length - self._starttime + self._numpoints*1e9/self._clock + 1)

        if resend:
            self.resend_waveform()
            self._pulser.update_all_cards()

    def _do_get_risetime(self):
        return self._risetime

    def _do_set_risetime(self, risetime, resend=True):
        self._risetime = risetime
        if resend:
            self.resend_waveform()
            
    def _do_get_risetype(self):
        return self._risetype

    def _do_set_risetype(self, risetype, resend=True):
        self._risetype = risetype
        if resend:
            self.resend_waveform()

    def _do_get_level(self):
        return self._level
        
    def _do_set_level(self, level,  resend=True):
        self._level = level
        if resend:
            self.resend_waveform()
    
    def _do_get_level0(self):
        return self._level0
        
    def _do_set_level0(self, level,  resend=True):
        self._level0 = level
        if resend:
            self.resend_waveform()

    def _do_get_period(self):
        return self._period
        
    def _do_set_period(self, period,  resend=True):
        self._period = period
        if resend:
            self.resend_waveform()

    def _do_get_pulse_length(self):
        return self._plen
        
    def _do_set_pulse_length(self, plen,  resend=True):
        self._plen = plen
        if resend:
            self.resend_waveform()

    def _do_get_length(self):
        return self._length

    def _do_set_length(self, length, resend=True):
        self._length = length
        st_p=self._pulser.get_measurement_start()
        delay = self.get_delay(query=False) + self._dt
        
        self._pulser.set('card%d_fireA' % self._cardnr, st_p - delay - length - self._starttime)
        self._pulser.set('card%d_fireB' % self._cardnr, st_p - delay - length - self._starttime + self._numpoints*1e9/self._clock + 1)

        if resend:
            self.resend_waveform()
            self._pulser.update_all_cards()
            
    def _do_get_falltime(self):
        return self._falltime

    def _do_set_falltime(self, falltime, resend=True):
        self._falltime = falltime
        if resend:
            self.resend_waveform()

    def _do_get_falltype(self):
        return self._falltype

    def _do_set_falltype(self, falltype, resend=True):
        self._falltype = falltype
        if resend:
            self.resend_waveform()

    def do_get_delay(self):
        return self._pulser.get_measurement_start() - self._pulser.get('card%d_fireA' % self._cardnr) - self._dt - self.get_length() - self._starttime
        
    def do_set_delay(self, val):
        st_p=self._pulser.get_measurement_start()
        len = self.get_length()
        
        self._pulser.set('card%d_fireA' % self._cardnr, st_p - val - len - self._starttime - self._dt)
        self._pulser.set('card%d_fireB' % self._cardnr, st_p - val - len - self._starttime - self._dt + self._numpoints*1e9/self._clock + 1)
        self._pulser.update_all_cards()
    # shortcuts

    def on(self):
        self.set_awg_status('on')

    def off(self):
        self.set_awg_status('off')
