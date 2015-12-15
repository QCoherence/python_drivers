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
        return data >> 4



    def std_averaging(self, current_std, new_std):

        return np.sqrt((self.treated_buffer*current_std**2. + new_std**2.)\
                      /(self.treated_buffer + 1.))



    def many_sequences_per_buffer(self, data, queue_treatment, parameters):
        """
            Organise data when the number of acquired sequences are smaller
            than the number of records per buffer.
        """

        # For the first buffer, we initialize the data stored attribute
        # witht the correct shape
        if self.treated_buffer == 0:
            self.data_stored = np.array([]).reshape(parameters['nb_sequence'], 0)
        # If there are data stored from previous buffer
        elif self.data_stored.shape[0] != parameters['nb_sequence']:

            # Data used correspond to the data saved previously and
            # data coming from the new buffer. We build an array combining
            # these two sources of data.
            self.process(np.vstack((self.data_stored,\
                                   data[:parameters['nb_sequence'] - self.data_stored.shape[0]])),\
                        queue_treatment, parameters)

        # We iterate to empty the buffer by sending data in package
        # corresponding to a whole sequence.
        i = 0
        while (i + 2)*parameters['nb_sequence'] - self.data_stored.shape[0] <= parameters['records_per_buffer']:

            self.process(data[(i + 1)*parameters['nb_sequence'] - self.data_stored.shape[0]\
                            :(i + 2)*parameters['nb_sequence'] - self.data_stored.shape[0]],\
                        queue_treatment, parameters)
            i += 1

        # If thre is data left but not enough to sen a package, we store
        # them for the next buffer.
        i -= 1
        if (i + 2)*parameters['nb_sequence'] - self.data_stored.shape[0] != data.shape[0]:

            self.data_stored = data[(i + 2)*parameters['nb_sequence'] - self.data_stored.shape[0]:]
        # If not, we reinitialize the data stored attribute with an empty
        # array
        else:
            self.data_stored = np.array([]).reshape(parameters['nb_sequence'], 0)



    def less_sequence_per_buffer(self, data, queue_treatment, parameters):
        """
            Organise data when the number of acquired sequences are greater
            than the number of records per buffer.
        """

        # For the first buffer, we initialize the data stored attribute
        if self.treated_buffer == 0:
            self.data_stored = data
        else:

            # If the new data are not enough to reach the number of sequence
            # we store the whole measured buffer
            if self.data_stored.shape[0] + data.shape[0] < parameters['nb_sequence']:

                self.data_stored  = np.vstack((self.data_stored, data))
            # Otherwise, only a part of the buffer is use to store.
            # The other part is stored for the next buffer
            else:
                self.process(np.vstack((self.data_stored,\
                                        data[:parameters['nb_sequence']\
                                        - self.data_stored.shape[0]])),\
                            queue_treatment, parameters)

                self.data_stored = data[parameters['nb_sequence'] - self.data_stored.shape[0]:]



    def treat_data(self, queue_data, queue_treatment, parameters):
        """
            Launch a loop to treat all the buffers acquired by the board.
            At each iteration, the method call "process" which should be
            defined in a child class.
        """

        start_time = time.time()
        self.treated_buffer = 0

        # We acquire as many buffer as the board has acquired
        while parameters['measured_buffers'] is None or \
              self.treated_buffer < parameters['measured_buffers']:

            # We obtain the data in a 2D array (acquired_sample, records)
            data = self.data_2D(queue_data.get(), parameters)

            # If the number of sequence is equal to the number of records per buffer
            # Then we can treat data immediately
            if data.shape[0] == parameters['nb_sequence']:

                self.process(data, queue_treatment, parameters)
            # If the number of sequence is smaller than the  number of acquired buffer
            # We have to treat data per package, each package corresponding to
            # a sequence.
            elif data.shape[0] > parameters['nb_sequence']:

                self.many_sequences_per_buffer(data, queue_treatment, parameters)
            # If the number of sequence is larger than the number of records per
            # buffer
            else:
                self.less_sequence_per_buffer(data, queue_treatment, parameters)


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

    def process(self, data, queue_treatment, parameters):

        self.data = np.append(self.data, data)

        queue_treatment.put(self.data)



class Average(DataTreatment):
    """
        Class performing the average of the acquired data.
    """

    def __init__(self):

        self.data = 0.

    def process(self, data, queue_treatment, parameters):
        """
            Calculate the average of the current buffer and average it with
            the previous measured data.
            Return the data in the memory buffer as the following:
            (data)
        """

        # We obtain the data in volt
        data = self.data_in_volt(data)

        # We obtain the current averaging for both and save them for
        # the next iteration
        self.data = self.mean_averaging(self.data, np.mean(data, axis=0))
        # self.std  = self.std_averaging(self.std, np.std(data, axis=0))

        # Send the result with the amplitude in V
        # queue_treatment.put((data))
        queue_treatment.put((self.data))



class AmplitudePhase(DataTreatment):
    """
        Return the amplitude and the phase of the acquired oscillations by
        using the cos, sin method.
        Return the amplitude in V and the phase in rad
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



    def process(self, data, queue_treatment, parameters):
        """
            Return the amplitude and the phase of the acquired oscillations by
            using the cos, sin method.
            Return the amplitude in V and the phase in rad as
            (amp_mean, amp_std, phase_mean, phase_std)
        """

        # We obtain the data in volt
        data = self.data_in_volt(data)

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



class AmplitudePhaseMarker(DataTreatment):
    """
        Return the amplitude and the phase of the acquired oscillations by
        using the cos, sin method.
        Return the amplitude in V and the phase in rad
    """



    def __init__(self, samplerate, frequency, start, stop):
        """
            Input:
                - samplerate (float): in sample per second
                - frequency (float): Frequency of the down-converted signal in hertz
                - start (float): time from which data are meaningfull in second
                - stop (float):  time to which data stop to be meaningfull in second
        """

        # Find start and stop in array index
        self.start = int(round(start*samplerate, 0))
        self.stop  = int(round(stop*samplerate, 0))

        # We calculate the sin and cos
        time = np.arange(self.stop - self.start)/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        # Data save
        self.amp_mean = 0.
        self.amp_std  = 0.
        self.phase_mean = 0.
        self.phase_std  = 0.



    def process(self, data, queue_treatment, parameters):
        """
            Return the amplitude and the phase of the acquired oscillations by
            using the cos, sin method.
            Return the amplitude in V and the phase in rad as
            (amp_mean, amp_std, phase_mean, phase_std)
        """

        # We obtain the data in volt
        data = self.data_in_volt(data)

        # Build cos and sin
        cos = np.mean(data[:,self.start:self.stop]*self.cos, axis=1)
        sin = np.mean(data[:,self.start:self.stop]*self.sin, axis=1)

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

        # We save the input power in V
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



    def process(self, data, queue_treatment, parameters):
        """
            Return the amplitude and the phase of the acquired oscillations by
            using the cos, sin method.
            Return the amplitude in dB and the phase in rad as
            (amp_mean, amp_std, phase_mean, phase_std)
        """

        # Data in volt
        data = self.data_in_volt(data)

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



class DBPhaseMarker(DataTreatment):
    """
        Return the amplitude and the phase of the acquired oscillations by
        using the cos, sin method.
        Return the amplitude in V and the phase in rad
    """



    def __init__(self, samplerate, frequency, start, stop, input_power,
                 impedance = 50):
        """
            Input:
                - samplerate (float): in sample per second
                - frequency (float): Frequency of the down-converted signal in hertz
                - start (float): time from which data are meaningfull in second
                - stop (float):  time to which data stop to be meaningfull in second
                - input_power (float): in dBm
                - impedance (float): by default 50 ohm
        """

        # Find start and stop in array index
        self.start = int(round(start*samplerate, 0))
        self.stop  = int(round(stop*samplerate, 0))

        # We calculate the sin and cos
        time = np.arange(self.stop - self.start)/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        # Data save
        self.amp_mean = 0.
        self.amp_std  = 0.
        self.phase_mean = 0.
        self.phase_std  = 0.

        self.impedance = impedance

        # We save the input power in V
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


    def process(self, data, queue_treatment, parameters):
        """
            Return the amplitude and the phase of the acquired oscillations by
            using the cos, sin method.
            Return the amplitude in V and the phase in rad as
            (amp_mean, amp_std, phase_mean, phase_std)
        """

        # We obtain the data in volt
        data = self.data_in_volt(data)

        # Build cos and sin
        cos = np.mean(data[:,self.start:self.stop]*self.cos, axis=1)
        sin = np.mean(data[:,self.start:self.stop]*self.sin, axis=1)

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



    def process(self, data, queue_treatment, parameters):
        """
            Return the amplitude and the phase of the acquired oscillations by
            using the cos, sin method.
            Return the amplitude in dB and the phase in rad as
            (amp_mean, amp_std, phase_mean, phase_std)
        """

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
    """
        Return the amplitude and the phase of the acquired sequences by
        using the cos, sin method.
        Take into account an integer number of oscillations (bigest one) for the
        calculation.
        Return the amplitude in V and the phase in rad
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

        self.amp_mean = 0.
        self.amp_std  = 0.

        self.phase_mean = 0.
        self.phase_std  = 0.



    def process(self, data, queue_treatment, parameters):

        # Data in volt
        data = self.data_in_volt(data)

        # Build cos and sin
        cos = np.mean(data[:,:self.nb_points]*self.cos, axis=1)
        sin = np.mean(data[:,:self.nb_points]*self.sin, axis=1)

        amp      = 2.*np.sqrt(cos**2. + sin**2.)
        amp_mean = self.mean_averaging(self.amp_mean, amp)

        phase      = np.angle(cos + 1j*sin)
        phase_mean = self.mean_averaging(self.phase_mean, phase)

        if self.treated_buffer < 2:

            self.amp_std   = amp_mean
            self.phase_std = phase_mean
        else:
            self.amp_std = np.sqrt((self.treated_buffer - 1.)*self.amp_std**2.\
                                     /self.treated_buffer
                                     + (amp - self.amp_mean)**2.\
                                    /(self.treated_buffer + 1.))

            self.phase_std = np.sqrt((self.treated_buffer - 1.)*self.phase_std**2.\
                                     /self.treated_buffer
                                     + (phase - self.phase_mean)**2.\
                                    /(self.treated_buffer + 1.))

        self.amp_mean   = amp_mean
        self.phase_mean = phase_mean

        # We send the result with the amplitude in V
        queue_treatment.put((self.amp_mean, self.amp_std,\
                             self.phase_mean, self.phase_std))



class RealImagPerSequence(DataTreatment):
    """
        Return the amplitude and the phase of the acquired sequences by
        using the cos, sin method.
        Take into account an integer number of oscillations (bigest one) for the
        calculation.
        Return the amplitude in V and the phase in rad
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

        self.real_mean = 0.
        self.real_std  = 0.
        self.imag_mean = 0.
        self.imag_std  = 0.


    def process(self, data, queue_treatment, parameters):

            # Build cos and sin
            real = 2.*np.mean(data[:,:self.nb_points]*self.cos, axis=1)
            imag = 2.*np.mean(data[:,:self.nb_points]*self.sin, axis=1)

            # We obtain the current averaging for both
            real_mean = self.mean_averaging(self.real_mean, real)
            imag_mean = self.mean_averaging(self.imag_mean, imag)

            # If we can calculate the standard deviation
            if self.treated_buffer < 2:

                self.real_std = real_mean
                self.imag_std = imag_mean
            else:

                self.real_std = np.sqrt((self.treated_buffer - 1.)*self.real_std**2.\
                                         /self.treated_buffer
                                         + (real - self.real_mean)**2.\
                                        /(self.treated_buffer + 1.))

                self.imag_std = np.sqrt((self.treated_buffer - 1.)*self.imag_std**2.\
                                         /self.treated_buffer
                                         + (imag - self.imag_mean)**2.\
                                        /(self.treated_buffer + 1.))


            self.real_mean = real_mean
            self.imag_mean = imag_mean

            queue_treatment.put((self.real_mean, self.real_std, self.imag_mean, self.imag_std))



class AmplitudeHistogram(DataTreatment):
    """
        Return an array of amplitude of the acquired sequences by
        using the cos, sin method.
        Take into account an integer number of oscillations (bigest one) for the
        calculation.
        Return the amplitude in V.
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
        self.amp = np.array([])



    def process(self, data, queue_treatment, parameters):

        # We obtain the data in volt
        data = self.data_in_volt(data)

        # Build cos and sin
        cos = np.mean(data[:,:self.nb_points]*self.cos, axis=1)
        sin = np.mean(data[:,:self.nb_points]*self.sin, axis=1)

        # We obtain the current amplitude
        self.amp = np.concatenate((self.amp, 2.*np.sqrt(cos**2. + sin**2.)))

        # We send the result
        queue_treatment.put((self.amp))



class PhaseHistogram(DataTreatment):
    """
        Return an array of phase of the acquired sequences by
        using the cos, sin method.
        Take into account an integer number of oscillations (bigest one) for the
        calculation.
        Return the phase in rad.
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
        self.phase = np.array([])



    def process(self, data, queue_treatment, parameters):

        # We obtain the data in volt
        data = self.data_in_volt(data)

        # Build cos and sin
        cos = np.mean(data[:,:self.nb_points]*self.cos, axis=1)
        sin = np.mean(data[:,:self.nb_points]*self.sin, axis=1)

        # We obtain the current amplitude
        self.phase = np.concatenate((self.phase, np.angle(cos + +1j*sin)))

        # We send the result
        queue_treatment.put((self.phase))
