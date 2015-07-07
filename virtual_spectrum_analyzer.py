# -*- coding: utf-8 -*-
from instrument import Instrument
import instruments
import numpy
import types
import logging

class virtual_spectrum_analyzer(Instrument):
    '''
    This is a driver for the virtual instrument that records emission spectra

    Usage:
    Initialize with
    <name> = qt.instruments.create('name', 'virtual_readout_IQ_multi', spectrum='name_spectrum', mwsrc_pulse='name_microwave_source_used_pulse', mwsrc_read_out='name_microwave_source_used_read_out')
    '''
    
    def __init__(self, name, spectrum, mwsrc_read_out, nums=128, segsize= 2048, amp0=500, amp1=500):
        '''
            Initialize the virtual instruments
                
                Input:
                    name            : Name of the virtual instruments
                    spectrum        : Name given to the Spectrum M3i4142
                    nums (int)      : number of consequtive measurements
                                        default = 128
                            
                    segsize (int)   : Size of the memory allocated in the card [Sample]
                                        default = 2048
                                        
                    amp0 (int)      : half of the range of the channel 0 [mV]
                                        default = 500
                                        
                    amp1 (int)      : half of the range of the channel 1 [mV]
                                        default = 500
                
                Output:
                    None
        '''
        
        Instrument.__init__(self, name, tags=['virtual'])
        
        
        self.add_parameter('input_term_ch0', option_list=['50', '1 M'], units='Ω', flags=Instrument.FLAG_GETSET, type=types.StringType)
        self.add_parameter('input_term_ch1', option_list=['50', '1 M'], units='Ω', flags=Instrument.FLAG_GETSET, type=types.StringType)

        self.add_parameter('input_amp_ch0', option_list=[200, 500, 1000, 2000, 5000, 10000], units='mV', flags=Instrument.FLAG_GETSET, type=types.IntType, default=200)
        self.add_parameter('input_amp_ch1', option_list=[200, 500, 1000, 2000, 5000, 10000], units='mV', flags=Instrument.FLAG_GETSET, type=types.IntType, default=200)
        
        #The maxvalue of the samplerate is only of 250 MS.Hz because we use the two channels of the board
        self.add_parameter('samplerate', units='MS.Hz', maxval=400, flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('segmentsize', minval=16, units='S', flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('repetitions', minval=1, flags=Instrument.FLAG_GETSET, type=types.IntType)
#        self.add_parameter('acquisitionTime', units='ms', flags=Instrument.FLAG_GET, type=types.FloatType)
        self.add_parameter('bandwidth', units='Hz', option_list=[10, 100, 1000, 10000, 100000], flags=Instrument.FLAG_GET, type=types.FloatType)
        self.add_parameter('status', flags=Instrument.FLAG_GETSET, option_list=['on', 'off'], type=types.StringType)
#        self.add_parameter('detuning', units='MHz', flags=Instrument.FLAG_GETSET, type=types.FloatType)
        self.add_parameter('startfrequency', units='GHz', minval=100e-6, maxval=12.75, flags=Instrument.FLAG_GETSET, type=types.FloatType)
        self.add_parameter('stopfrequency', units='GHz', minval=100e-6, maxval=12.75, flags=Instrument.FLAG_GETSET, type=types.FloatType)
        self.add_parameter('numsteps', units='', minval=1, maxval=10**5+1, flags=Instrument.FLAG_GETSET, type=types.FloatType)
        self.add_parameter('power', units='dBm', minval=-20, maxval=30, flags=Instrument.FLAG_GETSET, type=types.FloatType)
        self.add_parameter('averages', units='', minval=1, maxval=10**6, flags=Instrument.FLAG_GETSET, type=types.FloatType)
        
        # Defining some stuff
        self._instruments = instruments.get_instruments()
        self._spectrum = self._instruments.get(spectrum)
        
        self._microwave_generator = self._instruments.get(mwsrc_read_out)

        self._spectrum.set_input_amp_ch0(200)
        self._spectrum.set_input_amp_ch1(200)
        self._spectrum.set_input_term_ch0('50')
        self._spectrum.set_input_term_ch1('50')
#        self._spectrum.set_pretrigger(8)
        #Default detuning [MHz]
#        self._detuning = 0
        
        #We initialize the card
        #Number of segments
        self._nums=nums
        #We don't want to record data before the trigger so, we put the posttrigger time equal to the segment size
        #We initialize the card on two channel multiple recording mode
        #self._spectrum.init_channel01_multiple_recording(nums=self._nums, segsize=segsize, posttrigger=segsize-8,amp0=amp0,amp1=amp1)

        
        self.get_all()

    def get_all(self):
        '''
            Get all parameters of the virtual device
            
            Input:
                None
            
            Output:
                None
        '''
        self.get_input_term_ch0()
        self.get_input_term_ch1()
        
        self.get_input_amp_ch0()
        self.get_input_amp_ch1()
        
        self.get_samplerate()
        self.get_segmentsize()
        self.get_repetitions()
#        self.get_acquisitionTime()
#        self.get_bandWidth()
        
#        self.get_detuning()
#        self.get_frequency()
        self.get_power()
        self.get_status()




#########################################################
#
#
#                Frequency
#
#
#########################################################

    def do_set_startfrequency(self, frequency=1.):
        '''
            Set the frequency of the detector

            Input:
                frequency (float): Frequency at which the instrument will be tuned [GHz]

            Output:
                None
        '''
        
        logging.info(__name__+' : Set the frequency of the detector')
        self._microwave_generator.set_frequency(frequency*1e9)


    def do_get_startfrequency(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been tuned [GHz]
        '''
        
        logging.info(__name__+' : Get the frequency of the intrument')
        return float(self._microwave_generator.get_frequency())*1e-9 

    def do_set_stopfrequency(self, frequency=1.):
        '''
            Set the frequency of the detector

            Input:
                frequency (float): Frequency at which the instrument will be tuned [GHz]

            Output:
                None
        '''
        
        logging.info(__name__+' : Set the frequency of the detector')
        self._microwave_generator.set_frequency(frequency*1e9)


    def do_get_stopfrequency(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been tuned [GHz]
        '''
        
        logging.info(__name__+' : Get the frequency of the intrument')
        return float(self._microwave_generator.get_frequency())*1e-9


#########################################################################
#
#
#                           Microwave on/off
#
#
#########################################################################

    def do_set_status(self, status):
        '''
            Switch on/off the microwave generator.

            Input:
                status (String): Status of the microwave generator ['on', 'off']

            Output:
                None
        '''
        
        self._microwave_generator.set_status(status)

    def do_get_status(self):
        '''
            Get the status of the microwave generator.

            Input:
                None

            Output:
                status (String): Status of the microwave generator
        '''
        
        return self._microwave_generator.get_status()

#########################################################################
#
#
#                           Power
#
#
#########################################################################

    def do_get_power(self):
        '''
            Return the value of the power
            
            Input:
                None
            
            Output:
                None
        '''
        
        return self._microwave_generator.get_power()


    def do_set_power(self, power = 10.0):
        '''
            Set the value of the power
            
            Input:
                power (float): power of the microwave [dBm]
            
            Output:
                None
        '''
        
        self._microwave_generator.set_power(power)


#########################################################################
#
#
#                           Detuning
#
#
#########################################################################

#    def do_get_detuning(self):
#        '''
#            Get the detuning between the microwave generator used for the read out and the microwave generator used for the microwave pulse
#            detuning = mwsrc_pulse - mwsrc_read_out
#            
#            Input:
#                None
#            
#            Output:
#                detuning (float): detuning between the two microwave generators [MHz]
#        '''
#        
#        return self._detuning


#    def do_set_detuning(self, detuning=0.):
#        '''
#            Set the detuning between the microwave generator used for the microwave pulse and the microwave generator used for the read out
#            frequency difference = mwsrc_pulse - mwsrc_read_out

#            Input:
#                detuning (float): Detuning between the two microwave generators [MHz]

#            Output:
#                None
#        '''
#        
#        logging.info(__name__+' : Set the detuning between the two microwave generators')
#        
#        self._detuning = detuning
#        self.set_frequency(self.get_frequency(query=False))


#########################################################################
#
#
#                           Bandwidth
#
#
#########################################################################

    def do_get_bandWidth(self):
#        '''
#            Get the bandwidth of the measurement

#            Input:
#                None
#            Output:
#                bandWidth (int)   : The bandWidth of the measurement [Hz]
#        '''
        
        return 1./float(self.get_acquisitionTime())



#########################################################################
#
#
#                           Acquisition time
#
#
#########################################################################

    def do_get_acquisitionTime(self):
        '''
            Get the time that the measure will spend

            Input:
                None
            Output:
                acquisitionTime (int)   : The time that the measure will spend [ms]
        '''
        
        return float(self.get_numberSample())/float(self.get_samplerate()*1e3)



#########################################################################
#
#
#                           Memory size
#
#
#########################################################################

    def do_get_repetitions(self):
        '''
            Gets the number of segments

            Input:
                None
            Output:
               repetitions (int)   : The number of segments
        '''
        
        return self._nums
    
    def do_set_repetitions(self, nums):
        '''
            Sets the number of segments

            Input:
               repetitions (int)   : The number of segments
            Output:
                None
        '''
        
        self._nums = nums
        segsize = self.get_segmentsize(query=False)
        self._spectrum.set_memsize(segsize*nums)

        
    def do_get_segmentsize(self):
        '''
            Gets the length of one segment

            Input:
                None
            Output:
               segsize (int)   : The segment size setted on the board [Sample]
        '''
        
        return self._spectrum.get_segmentsize()



    def do_set_segmentsize(self, segsize):
        '''
            Sets the number of sample that are going to be recorded info one segment

            Input:
                segsize (int)   : The segment size setted on the board [Sample]
            Output:
                None
        '''
        
        self._spectrum.set_segmentsize(segsize)

        #We want to keep pretrigger part as small as possible, i.e. 8 samples
        self._spectrum.set_post_trigger(segsize-8)
        self._spectrum.set_memsize(segsize*self._nums)
        
        #We update the acquisition time and the bandwidth
#        self.get_acquisitionTime()
#        self.get_bandWidth()


#########################################################################
#
#
#                           Sample rate
#
#
#########################################################################


    def do_set_samplerate(self, rate):
        '''
            Set the samplerate of the board

            Input:
                rate (int): The samplerate wanted for the board [MHz]
            Output:
                None
        '''
        self._spectrum.set_samplerate(rate)
        
        #We update the acquisition time and the bandwidth
#        self.get_acquisitionTime()
#        self.get_bandWidth()


    def do_get_samplerate(self):
        '''
            Get the samplerate of the board

            Input:
                None
            Output:
                samplerate (int)    : The samplerate tuned on the board [MHz]
        '''
        return self._spectrum.get_samplerate()

#########################################################################
#
#
#                           Impedance
#
#
#########################################################################

    def do_get_input_term_ch0(self):
        '''
            Get channel 0 impedance termination
            
            Input:
                
                None
                
            Output:
                
                Impedance (string) : Impedance in ohms
        '''
        
        return self._spectrum.get_input_term_ch0()

    def do_set_input_term_ch0(self, impedance):
        '''
            Set the value of the impedance of channel 0 to 50 Ω or 1 MΩ
            
            Input:
                impedance (int) : Value of the termination [Ω]
            
            Output:
                None
        '''
        
        self._spectrum.set_input_term_ch0(impedance)



    def do_get_input_term_ch1(self):
        '''
            Get channel 1 impedance termination
            
            Input:
                
                None
                
            Output:
                
                Impedance (string) : Impedance in ohms
        '''
        
        return self._spectrum.get_input_term_ch1()

    def do_set_input_term_ch1(self, impedance):
        '''
            Set the value of the impedance of channel 1 to 50 Ω or 1 MΩ
            
            Input:
                impedance (int) : Value of the termination [Ω]
            
            Output:
                None
        '''
        
        self._spectrum.set_input_term_ch1(impedance)


    def do_get_filter_ch0(self):
        '''
            Get channel 0 filter
            
            Input:
                
                None
                
            Output:
                
                Impedance (string) : Impedance in ohms
        '''
        
        return self._spectrum.get_input_term_ch0()

    def do_set__filter_ch0(self, filt):
        '''
            Set the value of the impedance of channel channel 0 filter
            
            Input:
                impedance (int) : Value of the termination [Ω]
            
            Output:
                None
        '''
        
        self._spectrum.set_filter_ch0(filt)


    def do_get_filter_ch1(self):
        '''
            Get channel 1 filter
            
            Input:
                
                None
                
            Output:
                
                Impedance (string) : Impedance in ohms
        '''
        
        return self._spectrum.get_input_term_ch1()

    def do_set__filter_ch1(self, filt):
        '''
            Set the value of the impedance of channel channel 0 filter
            
            Input:
                impedance (int) : Value of the termination [Ω]
            
            Output:
                None
        '''
        
        self._spectrum.set_filter_ch1(filt)


        
#########################################################################
#
#
#                           Amplitude
#
#
#########################################################################


    def do_set_input_amp_ch0(self, amp):
        '''
        Sets the amplitude of the range of channel 0
        The range defines the precision of the analog-digital conversion

        Input:
            amp (int): amplitude of the channel in millivolts

        Output:
            None
        '''
        
        self._spectrum.set_input_amp_ch0(amp)


    def do_get_input_amp_ch0(self):
        '''
        Gets the amplitude of the range of channel 0
        The range defines the precision of the analog-digital conversion

        Input:
            None

        Output:
            amp (int): amplitude of the channel in millivolts
        '''

        return self._spectrum.get_input_amp_ch0()



    def do_set_input_amp_ch1(self, amp):
        '''
        Sets the amplitude of the range of channel 1
        The range defines the precision of the analog-digital conversion

        Input:
            amp (int): amplitude of the channel in millivolts

        Output:
            None
        '''

        self._spectrum.set_input_amp_ch1(amp)


    def do_get_input_amp_ch1(self):
        '''
        Gets the amplitude of the range of channel 1
        The range defines the precision of the analog-digital conversion

        Input:
            None

        Output:
            amp (int): amplitude of the channel in millivolts
        '''
        return self._spectrum.get_input_amp_ch1()

#########################################################################
#
#
#                           Measure Data Point
#
#
#########################################################################


    def measure_data_point(self,frequency,bandwidth,averages,samplerate):


        self._microwave_generator.set_frequency(frequency*1e9)
        self._spectrum.set_timeout(100)
#       qt.msleep(0.0001)
    
        '''
            Run a measurement thanks to the spectrum card_status
            We assume that :
                - I correspond to the channel 0
                - Q correspond to the channel 1
            Input:
                 None
            Output:
                date (float[channel_0], float[channel_1]) : Data coming from the measurement [mV]
        '''
        B=samplerate*1e6/bandwidth

        sampsize=int(numpy.ceil(samplerate*1e6/bandwidth/4096)*4096)*averages
        detuning=samplerate*1e6/sampsize
        detuning=numpy.ceil(samplerate*1e6/sampsize*averages*2500)/1e6
        self._spectrum.set_segmentsize(sampsize)
        if (sampsize)>2560000 :
            self._spectrum.set_memsize(2560000)
        else:
            self._spectrum.set_memsize(sampsize)
#        self._spectrum.set_repetitions(averages)
        self._spectrum.set_post_trigger(sampsize-8)
        self._spectrum.set_samplerate(samplerate)
        Z=float(self._spectrum.get_input_term_ch0())
        #We prepare the recording
        #self._spectrum.force_trigger()
        
        #We record the result
#        self.result_0, self.result_1 =  self._spectrum.readout_doublechannel_multimode_float()
        aver_data =self._spectrum.readout_singlechannel_FIFO_data(averages,sampsize)
#        aver_data=Vdata**2/Z
        #data =  self._spectrum.readout_singlechannel_FIFO_data(averages,sampsize)
        a=aver_data
        if averages >1:
            aver_data=numpy.average(aver_data,axis=0)
#        else:
#            aver_data=Vdata
        if aver_data != ():
            FFT = numpy.fft.rfft(aver_data, len(aver_data))
#       phase = np.angle(FFT[:len(signal) // 2])
            frequency = numpy.linspace(0, samplerate*1e6/2, sampsize/averages/2)
            BW=samplerate*1e6/sampsize*averages
            normalization = 2./len(aver_data)
            FFT = numpy.abs(FFT[:len(aver_data) // 2])
            FFT = normalization*FFT
            FFT = FFT**2/Z
            PSDW=FFT
            PSD=10*numpy.log10(FFT*1e3)   #dBm/Hz
            num_p=numpy.floor((detuning*1e6+bandwidth/2)/BW)
            power=0
        else :
            FFT=numpy.zeros_like(data)
            rang=()
            power=0

        power=10*numpy.log10(PSDW[float(num_p)]*bandwidth*1e3)

        return power
        
#        frequency = frequency[:len(frequency) //2]

    def measure_sweep(self,startfrequency,stopfrequency,numsteps,bandwidth,averages,samplerate):

        f_vec=numpy.linspace(startfrequency,stopfrequency,numsteps)
        data=()
        for f in f_vec:
            p=self.measure_data_point(f,bandwidth,averages,samplerate)
            if data == ():
                data=[ f, p]
            else:
                data=numpy.vstack((data,[f,p]))
        return data

    def measure_fourier_dBmHz(self,frequency,numsteps,bandwidth,averages,samplerate):

        self._spectrum.set_timeout(100)
        B=samplerate*1e6/bandwidth
        self._microwave_generator.set_frequency(frequency*1e9)
        sampsize=int(numpy.ceil(samplerate*1e6/bandwidth/4096)*4096)*averages
        self._spectrum.set_segmentsize(sampsize)
        if (sampsize)>2560000 :
            self._spectrum.set_memsize(2560000)
        else:
            self._spectrum.set_memsize(sampsize)
#        self._spectrum.set_repetitions(averages)
        self._spectrum.set_post_trigger(sampsize-8)
        self._spectrum.set_samplerate(samplerate)
        Z=float(self._spectrum.get_input_term_ch0())
        #We prepare the recording
        #self._spectrum.force_trigger()
        
        #We record the result
#        self.result_0, self.result_1 =  self._spectrum.readout_doublechannel_multimode_float()
        aver_data =self._spectrum.readout_singlechannel_FIFO_data(averages,sampsize)
#        aver_data=Vdata**2/Z
        #data =  self._spectrum.readout_singlechannel_FIFO_data(averages,sampsize)
        a=aver_data
        if averages >1:
            aver_data=numpy.average(aver_data,axis=0)
#        else:
#            aver_data=Vdata
        if aver_data != ():
            FFT = numpy.fft.rfft(aver_data, len(aver_data))
#       phase = np.angle(FFT[:len(signal) // 2])
            frequency = numpy.linspace(0, samplerate*1e6/2, sampsize/averages/2)
            BW=samplerate*1e6/sampsize*averages
            normalization = 2./len(aver_data)
            FFT = numpy.abs(FFT[:len(aver_data) // 2])
            FFT = normalization*FFT
            FFT = FFT**2/Z
            PSDW=FFT
            PSD=10*numpy.log10(FFT*1e3)   #dBm/Hz
        else :

            PSD=()
#        a=numpy.vstack((frequency,PSD))

        return a


    def measure_fourier_WHz(self,frequency,numsteps,bandwidth,averages,samplerate):

        self._spectrum.set_timeout(100)
        B=samplerate*1e6/bandwidth
        self._microwave_generator.set_frequency(frequency*1e9)
        sampsize=int(numpy.ceil(samplerate*1e6/bandwidth/4096)*4096)*averages
        self._spectrum.set_segmentsize(sampsize)
        if (sampsize)>2560000 :
            self._spectrum.set_memsize(2560000)
        else:
            self._spectrum.set_memsize(sampsize)
#        self._spectrum.set_repetitions(averages)
        self._spectrum.set_post_trigger(sampsize-8)
        self._spectrum.set_samplerate(samplerate)
        Z=float(self._spectrum.get_input_term_ch0())
        #We prepare the recording
        #self._spectrum.force_trigger()
        
        #We record the result
#        self.result_0, self.result_1 =  self._spectrum.readout_doublechannel_multimode_float()
        aver_data =self._spectrum.readout_singlechannel_FIFO_data(averages,sampsize)
#        aver_data=Vdata**2/Z
        #data =  self._spectrum.readout_singlechannel_FIFO_data(averages,sampsize)
        a=aver_data
        if averages >1:
            aver_data=numpy.average(aver_data,axis=0)
#        else:
#            aver_data=Vdata
        if aver_data != ():
            FFT = numpy.fft.rfft(aver_data, len(aver_data))
#       phase = np.angle(FFT[:len(signal) // 2])
            frequency = numpy.linspace(0, samplerate*1e6/2, sampsize/averages/2)
            BW=samplerate*1e6/sampsize*averages
            normalization = 2./len(aver_data)
            FFT = numpy.abs(FFT[:len(aver_data) // 2])
            FFT = normalization*FFT
            FFT = FFT**2/Z
            PSDW=FFT
        else :

            PSDW=()
        a=numpy.vstack((frequency,PSDW))
        

        return a



    def measure_single(self,frequency,bandwidth,samplerate):

        self._spectrum.set_timeout(100)
        '''
            Run a measurement thanks to the spectrum card_status
            We assume that :
                - I correspond to the channel 0
                - Q correspond to the channel 1
            Input:
                 None
            Output:
                date (float[channel_0], float[channel_1]) : Data coming from the measurement [mV]
        '''
        B=samplerate*1e6/bandwidth
        sampsize=int(numpy.ceil(samplerate*1e6/bandwidth/4096)*4096)
        detuning=numpy.ceil(samplerate*1e6/sampsize*12000)/1e9
        self._microwave_generator.set_frequency((frequency-detuning)*1e9)
        self._spectrum.set_segmentsize(sampsize)
        if (sampsize)>2560000 :
            self._spectrum.set_memsize(2560000)
        else:
            self._spectrum.set_memsize(sampsize)
#        self._spectrum.set_repetitions(averages)
        self._spectrum.set_post_trigger(sampsize-8)
        self._spectrum.set_samplerate(samplerate)
        Z=float(self._spectrum.get_input_term_ch0())
        #We prepare the recording
        #self._spectrum.force_trigger()
        #We record the result
#        self.result_0, self.result_1 =  self._spectrum.readout_doublechannel_multimode_float()
        aver_data =self._spectrum.readout_singlechannel_FIFO_data(1,sampsize)
        if aver_data != ():
            FFT = numpy.fft.rfft(aver_data, len(aver_data))
#       phase = np.angle(FFT[:len(signal) // 2])
            frequency = numpy.linspace(0, samplerate*1e6/2, sampsize/2)
            BW=samplerate*1e6/sampsize
            normalization = 2./len(aver_data)
            FFT = numpy.abs(FFT[:len(aver_data) // 2])
            FFT = normalization*FFT
            FFT = FFT**2/Z
            PSD=10*numpy.log10(FFT*1e3)   #dBm/Hz
            num_p=numpy.floor((detuning*1e9+bandwidth/2)/BW)
            power=0
        else :
            FFT=numpy.zeros_like(data)
            rang=()
            power=0
        power=10*numpy.log10(FFT[float(num_p)]*bandwidth*1e3)

        return power

    def measure_trace(self,startfrequency,stopfrequency,numsteps,bandwidth,samplerate):

        f_vec=numpy.linspace(startfrequency,stopfrequency,numsteps)
        data=()
        for f in f_vec:
            p=self.measure_single(f,bandwidth,samplerate)
            if data == ():
                data=[ f, p]
            else:
                data=numpy.vstack((data,[f,p]))
        return data



