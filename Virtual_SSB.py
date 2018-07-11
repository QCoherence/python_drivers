# Work in PROGRESS
# made by Remy Dassonneville in 2016-2017

from instrument import Instrument
import instruments
import numpy as np
import types
import logging

# from lib.math import fit # to be able to do some fit during the measurements
# import ATS9360.DataTreatment as dt
# import qt


class Virtual_SSB(Instrument):
    '''
    TO DO: complete it!!!
    This is the driver for the virtual instrument which records the useful
    parameters in the use of a Single Side Band modulator (SSB)

    Usage:
    Initialize with:
    <name> = qt.instruments.create('name', 'Virtual_SSB' )
    '''

    def __init__(self, name):
        '''
        Initialize the virtual instrument

            Input:
                - name: Name of the virtual instruments
            Output:
                None
        '''
        # No real Instrument here ...
        Instrument.__init__(self, name, tags=['virtual'])
        # #Import instruments
        self._instruments = instruments.get_instruments()

        ########################################################################
        #                    parameters
        ########################################################################
        # GET_SET
        self.add_parameter('freq_start',
                            flags=Instrument.FLAG_GETSET,
                            units='GHz',
                            minval = 1e-4,
                            maxval= 40,
                            type=types.FloatType)

        self.add_parameter('freq_stop',
                            flags=Instrument.FLAG_GETSET,
                            units='GHz',
                            minval = 1e-4,
                            maxval= 40,
                            type=types.FloatType)

        self.add_parameter('conversion_loss',
                            flags=Instrument.FLAG_GETSET,
                            units='dB',
                            type=types.FloatType)

        self.add_parameter('band_type',
                            flags=Instrument.FLAG_GETSET,
                            option_list= [-1, +1],
                            type=types.FloatType)

        self.add_parameter('LO_power',
                            flags=Instrument.FLAG_GETSET,
                            units = 'dBm',
                            option_list= (5., 15.),
                            type=types.FloatType)

        self.add_parameter('IF_frequency',
                            flags=Instrument.FLAG_GETSET,
                            units = 'GHz',
                            # minval = 1e-4,
                            # maxval= 0.5,
                            type=types.FloatType)


        self._freqstart = 4.
        self._freqstop = 8.
        self._conversionloss = 6.
        self._LOpower = 5.
        self._bandtype = -1
        self._IFfreq = 0.08

        ################## Should we? ##########################################
        # self.add_parameter('awg_channel',
        #                     flags=Instrument.FLAG_GETSET,
        #                     option_list= (1, 2, 3, 4),
        #                     type=types.FloatType)
        #
        # self.add_parameter('mw_src',
        #                     flags=Instrument.FLAG_GETSET,
        #                     option_list= (1, 2),
        #                     type=types.FloatType)

        # self._awgchannel = 1
        # self._mwsrc = 1

################################################################################

    def do_get_freq_start(self):
        '''
        Get the frequency start of the frequency range of the SSB.
        Input:
            None
        Output:
            freq_start [GHz]
        '''
        return self._freqstart

    def do_set_freq_start(self, f):
        '''
        Set the frequency start of the frequency range of the SSB.
        Input:
            freq_start [GHz]
        Output:
            None
        '''
        self._freqstart = f

    def do_get_freq_stop(self):
        '''
        Get the frequency stop of the frequency range of the SSB.
        Input:
            None
        Output:
            freq_stop [GHz]
        '''
        return self._freqstop

    def do_set_freq_stop(self, f):
        '''
        Set the frequency stop of the frequency range of the SSB.
        Input:
            freq_stop [GHz]
        Output:
            None
        '''
        self._freqstop = f

    def do_get_conversion_loss(self):
        '''
        Get the conversion loss of the SSB from IF to RF
        Input:
            None
        Output:
            conversion loss [dB]
        '''
        return self._conversionloss

    def do_set_conversion_loss(self, cvl):
        '''
        Set the conversion loss of the SSB from IF to RF
        Input:
            cvl [dB]
        Output:
            None
        '''
        self._conversionloss = cvl

    def do_get_LO_power(self):
        '''
        Get the Local Oscillator power to be at an optimal working point of the SSB
        Input:
            None
        Output:
            LO_power [dBm]
        '''
        return self._LOpower

    def do_set_LO_power(self, lopow):
        '''
        Set the Local Oscillator power to be at an optimal working point of the SSB
        Input:
            lopow [dBm]: should be 5 or 15
        Output:
            None
        '''
        self._LOpower = lopow

    def do_get_band_type(self):
        '''
        Get the bandtype of the SSB
        Input:
            None
        Output:
            band_type:
                -1 : the SSB is a Lower Side Band
                +1 : the SSB is a Upper Side Band
        '''
        return self._bandtype

    def do_set_band_type(self, bt):
        '''
        Set the bandtype of the SSB
        Input:
            bt:
                -1 : the SSB is a Lower Side Band (LSB)
                +1 : the SSB is a Upper Side Band (USB)
        Output:
            None
        '''
        self._bandtype = bt

    def do_get_IF_frequency(self):
        '''
        Get the IF frequency of the SSB
        Input:
            None
        Output:
            IFfreq [GHz]
        '''
        return self._IFfreq

    def do_set_IF_frequency(self, IFfreq):
        '''
        Set the IF frequency of the SSB
        Input:
            IFfreq [GHz]
        Output:
            None
        '''
        self._IFfreq = IFfreq
