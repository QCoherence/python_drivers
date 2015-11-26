# This Python file uses the following encoding: utf-8
# ATS9360_NPT.py driver for The aquisition board Alzar ATS9360
# Etienne Dumur <etienne.dumur@neel.cnrs.fr> 2015
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

import numpy as np
import time
import multiprocessing as mp
import cProfile

class DataTreatment(object):
    """
        Canvas for data treatment class.
        Should only be used as parent class
    """


    @staticmethod
    def data_in_volt(data):
        """
            Get raw data coming from the board and transform them in V.
        """

        # Parameters of the board (are fixed).
        # bitshift         = 4  # Sould be int
        # bits_per_sample  = 12 # Sould be int
        # inputRange_volts = 400e-3 # Fixed for the ats9360

        # Right-shift 16-bit sample value by 4 to get 12-bit sample code
        data = data >> 4

        # AlazarTech digitizers are calibrated as follows
        # codeZero  = (1 << (bits_per_sample - 1)) - 0.5
        # codeRange = (1 << (bits_per_sample - 1)) - 0.5
        # Following this a proportionality of 2047.5 is applied
        # The calcul is inputRange_volts*(data - codeZero) / codeRange

        return 0.4*(data - 2047.5)/2047.5



    @staticmethod
    def data_2D(data, parameters):
        """
            From the data returned by the board,
            the method makes a 2D array of them knowing the board's parameters.
        """

        # We reshape them in 2D-array to enhance the averaging
        return np.reshape(data, (parameters['records_per_buffer'],
                                 parameters['acquired_samples']))



    def mean_averaging(self, current_average, new_data):

        return (self.treated_buffer*current_average + new_data)\
              /(self.treated_buffer + 1.)



    @staticmethod
    def bitwise(data):
        """
            Right-shift 16-bit sample value by 4 to get 12-bit sample code
        """
        return data << 4


    def std_averaging(self, current_std, new_std):

        return np.sqrt((self.treated_buffer*current_std**2. + new_std**2.)\
                      /(self.treated_buffer + 1.))


    def treat_data(self, queue_data, queue_treatment, parameters):
        """
            Launch a loop to treat all the buffers acquired by the board.
            At each iteration, the method call "process" which should be
            defined in a child class.
        """

        cProfile.runctx('self.run(queue_data, queue_treatment, parameters)', globals(), locals(), 'prof.prof')

    def run(self, queue_data, queue_treatment, parameters):
        start_time = time.time()
        self.treated_buffer = 0

        # We acquire as many buffer as the board has acquired
        while parameters['measured_buffers'] is None or \
              self.treated_buffer < parameters['measured_buffers']:

            # The process received the data with the bitewise operation
            # already done to optimise the code
            self.process(queue_data, queue_treatment, parameters)

            # Each loop implies a treatment of one buffer
            self.treated_buffer += 1

        # Return information about the data treatment
        elapsed_time = time.time() - start_time
        acquired_samples = parameters['acquired_samples']*parameters['records_per_buffer']\
                          *parameters['measured_buffers']
        acquired_bytes   = acquired_samples*2 # 2 bytes per sample

        parameters['message'] += 'Treatment completed in %f sec\n' % elapsed_time
        parameters['message'] += 'Treated %d bytes (%f Mbytes per sec)\n' %\
                                 (acquired_bytes, acquired_bytes/elapsed_time/1024**2)
        parameters['message'] += 'Treated %d samples (%f Ms per sec)\n' %\
                                 (acquired_samples, acquired_samples/elapsed_time/1e6)

        # Once the data are finished to be processed, we close the shared memory
        queue_data.close()
        queue_treatment.close()

        # Inform the parent process that the data treatment is finished
        if parameters['safe_treatment'][0]:
            parameters['safe_treatment'][1] = True
        else:
            parameters['safe_treatment'][0] = True



class Raw(DataTreatment):
    """
        Return the raw data without any treatment except the bitwise of 4 bits.
    """

    def __init__(self):

        self.data = np.array([])

    def process(self, queue_data, queue_treatment, parameters):

        self.data = np.append(queue_data.get(), data)

        queue_treatment.put(self.data)



class Average(DataTreatment):
    """
        Class performing the average of the acquired data.
    """

    def __init__(self):

        self.mean = 0.
        self.std  = 0.

    def process(self, queue_data, queue_treatment, parameters):
        """
            Calculate the average of the current buffer and average it with
            the previous measured data.
            Return the data in the memory buffer as the following:
            (data, std)
        """

        # We obtain the data in a 2D array (acquired_sample, records)
        data = self.data_2D(queue_data.get(), parameters)

        # We obtain the current averaging for both and save them for
        # the next iteration
        self.mean = self.mean_averaging(self.mean, np.mean(data, axis=0))
        self.std  = self.std_averaging(self.std, np.std(data, axis=0))

        # Send the result with the amplitude in mV
        queue_treatment.put((self.mean, self.std))



class AmplitudePhase(DataTreatment):
    """
        Return the amplitude and the phase of the acquired oscillations by
        using the cos, sin method.
        Return the amplitude in mV and the phase in rad
    """



    def __init__(self, acquisition_time, samplerate, frequency):
        """
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
                - frequency (float): in hertz
        """

        # We need an integer number of oscillations
        nb_oscillations = int(frequency*acquisition_time)

        if nb_oscillations < 1:
            raise ValueError('The number of acquired oscillations must be larger than 1')

        # We obtain the number of point in these oscillations
        self.nb_points  = int(nb_oscillations/frequency*samplerate)

        # We calculate the sin and cos
        time = np.arange(self.nb_points)/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        # Data save
        self.amp_mean = 0.
        self.amp_std  = 0.
        self.phase_mean = 0.
        self.phase_std  = 0.



    def process(self, queue_data, queue_treatment, parameters):
        """
            Return the amplitude and the phase of the acquired oscillations by
            using the cos, sin method.
            Return the amplitude in mV and the phase in rad as
            (amp_mean, amp_std, phase_mean, phase_std)
        """

        # We obtain the data in volt
        data = self.data_in_volt(queue_data.get())

        # We obtain the data in a 2D array (acquired_sample, records)
        data = self.data_2D(data, parameters)

        # Build cos and sin
        cos = np.mean(data[:,:self.nb_points]*self.cos, axis=1)
        sin = np.mean(data[:,:self.nb_points]*self.sin, axis=1)

        # Obtain amplitude and phase
        amp   = 2.*np.sqrt(cos**2. + sin**2.)
        phase = np.angle(cos + 1j*sin)

        # We obtain the current averaging for both and save them for
        # the next iteration
        self.amp_mean = self.mean_averaging(self.amp_mean, np.mean(amp, axis=0))
        self.amp_std  = self.std_averaging(self.amp_std, np.std(amp, axis=0))

        self.phase_mean = self.mean_averaging(self.phase_mean, np.mean(phase, axis=0))
        self.phase_std  = self.std_averaging(self.phase_std, np.std(phase, axis=0))

        # We send the result
        queue_treatment.put((self.amp_mean, self.amp_std,\
                             self.phase_mean, self.phase_std))



class DBPhase(DataTreatment):
    """
        Return the amplitude and the phase of the acquired oscillations by
        using the cos, sin method.
        Return the amplitude in dB and the phase in rad
    """



    def __init__(self, acquisition_time, samplerate, frequency, input_power,
                 impedance = 50.):
        """
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
                - frequency (float): in hertz
                - input_power (float): in dBm
                - impedance (float): by default 50 ohm
        """

        # We need an integer number of oscillations
        nb_oscillations = int(frequency*acquisition_time)

        if nb_oscillations < 1:
            raise ValueError('The number of acquired oscillations must be larger than 1')

        # We obtain the number of point in these oscillations
        self.nb_points  = int(nb_oscillations/frequency*samplerate)

        # We calculate the sin and cos
        time = np.arange(self.nb_points)/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        # Data save
        self.amp_mean = 0.
        self.amp_std  = 0.
        self.phase_mean = 0.
        self.phase_std  = 0.

        self.impedance = impedance

        # We save the input power in mV
        self.set_input_power(input_power)



    def set_input_power(self, input_power):
        """
            Set the input power.
            Input:
                - input_power (float): in dBm
        """

        # We save the input power in V
        self.input_amplitude = np.sqrt(1e-3*10**(input_power/10.)\
                                       *self.impedance)



    def process(self, queue_data, queue_treatment, parameters):
        """
            Return the amplitude and the phase of the acquired oscillations by
            using the cos, sin method.
            Return the amplitude in dB and the phase in rad as
            (amp_mean, amp_std, phase_mean, phase_std)
        """

        # Data in volt
        data = self.data_in_volt(queue_data.get())

        # We obtain the data in a 2D array (acquired_sample, records)
        data = self.data_2D(data, parameters)

        # Build cos and sin
        cos = np.mean(data[:,:self.nb_points]*self.cos, axis=1)
        sin = np.mean(data[:,:self.nb_points]*self.sin, axis=1)

        # Obtain amplitude and phase
        amp   = 2.*np.sqrt(cos**2. + sin**2.)
        phase = np.angle(cos + 1j*sin)

        # We obtain the current averaging for both and save them for
        # the next iteration
        self.amp_mean = self.mean_averaging(self.amp_mean, np.mean(amp, axis=0))
        self.amp_std  = self.std_averaging(self.amp_std, np.std(amp, axis=0))

        self.phase_mean = self.mean_averaging(self.phase_mean, np.mean(phase, axis=0))
        self.phase_std  = self.std_averaging(self.phase_std, np.std(phase, axis=0))

        queue_treatment.put((20.*np.log10(self.amp_mean/self.input_amplitude),\
                             20.*self.amp_std/self.amp_mean/np.log(10.),\
                             self.phase_mean, self.phase_std))



class RealImag(DataTreatment):
    """
        Return the amplitude and the phase of the acquired oscillations by
        using the cos, sin method.
        Return the real and imaginary part.
    """



    def __init__(self, acquisition_time, samplerate, frequency):
        """
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
                - frequency (float): in hertz
        """

        # We need an integer number of oscillations
        nb_oscillations = int(frequency*acquisition_time)

        if nb_oscillations < 1:
            raise ValueError('The number of acquired oscillations must be larger than 1')

        # We obtain the number of point in these oscillations
        self.nb_points  = int(nb_oscillations/frequency*samplerate)

        # We calculate the sin and cos
        time = np.arange(self.nb_points)/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        # Data save
        self.real_mean = 0.
        self.real_std  = 0.
        self.imag_mean = 0.
        self.imag_std  = 0.



    def process(self, queue_data, queue_treatment, parameters):
        """
            Return the amplitude and the phase of the acquired oscillations by
            using the cos, sin method.
            Return the amplitude in dB and the phase in rad as
            (amp_mean, amp_std, phase_mean, phase_std)
        """


        # We obtain the data in a 2D array (acquired_sample, records)
        data = self.data_2D(queue_data.get(), parameters)

        # Build cos and sin
        real = 2.*np.mean(data[:,:self.nb_points]*self.cos, axis=1)
        imag = 2.*np.mean(data[:,:self.nb_points]*self.sin, axis=1)

        # We obtain the current averaging for both and save them for
        # the next iteration
        self.real_mean = self.mean_averaging(self.real_mean, np.mean(real, axis=0))
        self.real_std  = self.std_averaging(self.real_std, np.std(real, axis =0))

        self.imag_mean = self.mean_averaging(self.imag_mean, np.mean(imag, axis=0))
        self.imag_std  = self.std_averaging(self.imag_std, np.std(imag, axis=0))

        queue_treatment.put((self.real_mean, self.real_std,\
                             self.imag_mean, self.imag_std))



class AmplitudePhasePerSequence(DataTreatment):



    def __init__(self, acquisition_time, samplerate, frequency):
        """
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
                - frequency (float): in hertz
        """

        # We need an integer number of oscillations
        nb_oscillations = int(frequency*acquisition_time)

        if nb_oscillations < 1:
            raise ValueError('The number of acquired oscillations must be larger than 1')

        # We obtain the number of point in these oscillations
        self.nb_points  = int(nb_oscillations/frequency*samplerate)

        # We calculate the sin and cos
        time = np.arange(self.nb_points)/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        self.amp_mean = 0.
        self.amp_std  = 0.

        self.phase_mean = 0.
        self.phase_std  = 0.



    def process(self, queue_data, queue_treatment, parameters):

        # Data in volt
        data = self.data_in_volt(queue_data.get())

        # We obtain the data in a 2D array (acquired_sample, records)
        data = self.data_2D(data, parameters)

        # Build cos and sin
        cos = np.mean(data[:,:self.nb_points]*self.cos, axis=1)
        sin = np.mean(data[:,:self.nb_points]*self.sin, axis=1)

        amp          = 2.*np.sqrt(cos**2. + sin**2.)
        amp_new_mean = self.mean_averaging(self.amp_mean, amp)

        phase          = np.angle(cos + 1j*sin)
        phase_new_mean = self.mean_averaging(self.phase_mean, phase)

        # Std formula explanation here:
        # http://jonisalonen.com/2013/deriving-welfords-method-for-computing-variance

        if self.treated_buffer == 0:

            self.amp_std = np.ones_like(cos)*np.nan
            self.amp_std = np.ones_like(cos)*np.nan
        else:

            self.amp_std = np.sqrt(((self.treated_buffer - 1.)*self.amp_std**2.\
                                     + (amp - amp_new_mean)*(amp - self.amp_mean))\
                                    /self.treated_buffer)

            self.phase_std = np.sqrt(((self.treated_buffer - 1.)*self.phase_std**2.\
                                     + (phase - phase_new_mean)*(phase - self.phase_mean))\
                                    /self.treated_buffer)


        self.amp_mean   = amp_new_mean
        self.phase_mean = phase_new_mean

        # We send the result with the amplitude in mV
        queue_treatment.put((self.amp_mean, self.amp_std,\
                             self.phase_mean, self.phase_std))
