#!/usr/bin/env python3
import numpy as np
from pulse import PulseShape, Pulse

class Readout(object):
    """This class is used to generate and demodulate multi-tone qubit readout

    """

    def __init__(self, max_qubit=9):
        # define variables
        self.max_qubit = max_qubit
        self.n_readout = max_qubit
        self.sample_rate = 1E9
        self.n_pts = 1000
        self.match_main_size = False
        self.distribute_phases = False
        self.frequencies = np.zeros(self.max_qubit)
        # predistortion
        self.predistort = False
        self.measured_rise = np.zeros(self.max_qubit)
        self.target_rise = np.zeros(self.max_qubit)
        # quasi-random phases
        # self.phases = 2 * np.pi * np.random.rand(max_qubit)
        self.phases = 2 * np.pi * np.array([0.8847060, 0.2043214, 0.9426104,
            0.6947334, 0.8752361, 0.2246747, 0.6503154, 0.7305004, 0.1309068])
        # demodulation
        self.demod_skip = 0.0
        self.demod_length = 1.0E-6
        self.freq_offset = 0.0
        self.use_phase_ref = False
        self.iq_ratio = 1.0
        self.iq_skew = 0

    def set_parameters(self, config={}):
        """Set base parameters using config from from Labber driver

        Parameters
        ----------
        config : dict
            Configuration as defined by Labber driver configuration window

        """

        # get other parameters
        self.n_readout = int(config.get('Number of readout tones'))
        self.match_main_size = config.get('Match main sequence waveform size')
        self.distribute_phases = config.get('Distribute readout phases')
        self.n_pts = int(config.get('Number of points'))
        # predistortion
        self.predistort = config.get('Predistort readout waveform')
        if self.predistort:
            for n in range(self.max_qubit):
                # pre-distortion settings are currently same for all qubits
                linewidth = config.get('Resonator linewidth')
                self.measured_rise[n] = 1.0 / (2 * np.pi * linewidth)
                self.target_rise[n] = config.get('Target rise time')
        # demodulation
        for n in range(self.max_qubit):
            self.frequencies[n] = config.get('Readout frequency #%d' % (n+1))
        self.demod_skip = config.get('Demodulation - Skip')
        self.demod_length = config.get('Demodulation - Length')
        self.freq_offset = config.get('Demodulation - Frequency offset')
        self.use_phase_ref = config.get('Use phase reference signal')
        self.iq_ratio = config.get('Readout I/Q ratio')
        self.iq_skew = config.get('Readout IQ skew') * np.pi / 180
        # number of records, will be remoevd in later version
        self.n_records = config.get('Demodulation - Number of records', 1)

    def create_waveform(self, t_start=0.0):
        """Generate readout waveform

        Parameters
        ----------
        t_start : float
            Start time for readout waveform, relative to start of sequence

        Returns
        -------
        waveform : complex numpy array
            Complex waveforms with I/Q signal for qubit reaodut

        """

        for n in range(self.n_readout):
            pulse = self.pulses_readout[n]

            duration = pulse.total_duration()
            # Pulse is referenced to center of oulse
            t0 = t_start + duration / 2
            # get the range of indices in use
            indices = np.arange(
                max(np.floor(t_start*self.sample_rate), 0),
                min(np.ceil((t_start+duration)*self.sample_rate), self.n_pts),
                dtype=int
            )
            # return directly if no indices
            if len(indices) == 0:
                continue

            # calculate time values for the pulse indices
            t = indices / self.sample_rate
            # calculate the pulse envelope for the selected indices
            y = pulse.calculate_envelope(t0, t)
            waveform = np.zeros_like(t, dtype=complex)


            # get parameters
            omega = 2 * np.pi * pulse.frequency
            if self.distribute_phases:
                # phi = 2 * np.pi * n / self.n_readout
                # phi = 2 * np.pi * np.random.rand()
                phi = self.phases[n] + pulse.phase
            else:
                phi = pulse.phase
            # apply pre-distortion
            if self.predistort:
                # add inverted exponential
                y += ((self.measured_rise[n] / self.target_rise[n] - 1) *
                      np.exp(-(t - t[0]) / self.target_rise[n]))

            # remove phase drift due to LO-RF difference
            phi -= 2 * np.pi * self.freq_offset * t_start

            # add IQ skew
            phi_s = self.iq_skew

            # apply SSBM transform
            waveform += (y.real * np.cos(omega * t - phi) +
                        -y.imag * np.cos(omega * t - phi + np.pi / 2))
            waveform += 1j * (y.real * np.sin(omega * t - phi + phi_s) +
                             -y.imag * np.sin(omega * t - phi + np.pi / 2
                                              + phi_s))

        # apply SSBM transform
        if self.iq_ratio != 1.0:
            waveform.real *= self.iq_ratio

        return waveform

    def demodulate(self, n, signal, ref=None):
        """Calculate complex signal from data and reference

        Parameters
        ----------
        n : int
            Qubit number for which to demodulate

        signal : dict
            Dictionary with signal data

        ref : dict
            Dictionary with reference data

        Returns
        -------
        values : complex numpy array
            Complex array matching number of segments in input

        """
        # get parameters
        frequency = self.frequencies[n] - self.freq_offset
        n_segment = int(self.n_records)
        # get input data from dict, with keys {'y': value, 't0': t0, 'dt': dt}
        if signal is None:
            return np.zeros(n_segment, dtype=complex)
        vY = signal['y']
        dt = signal['dt']
        # get shape of input data
        shape = signal.get('shape', vY.shape)
        # override segment parameter if input data has more than one dimension
        if len(shape) > 1:
            n_segment = shape[0]
        # avoid exceptions if no time step is given
        if dt == 0:
            dt = 1.0
        # get indices for data trimming
        n0 = int(round(self.demod_skip / dt))
        n_total = vY.size
        length = 1 + int(round(self.demod_length / dt))
        length = min(length, int(n_total / n_segment) - n0)
        if length <= 1:
            return np.zeros(n_segment, dtype=complex)

        # define data to use, put in 2d array of segments
        vData = np.reshape(vY, (n_segment, int(n_total / n_segment)))
        # calculate cos/sin vectors, allow segmenting
        vTime = dt * (n0 + np.arange(length, dtype=float))
        vCos = np.cos(2 * np.pi * vTime * frequency)
        vSin = np.sin(2 * np.pi * vTime * frequency)
        # calc I/Q
        dI = 2 * np.trapz(vCos * vData[:, n0:n0 + length]) / float(length - 1)
        dQ = 2 * np.trapz(vSin * vData[:, n0:n0 + length]) / float(length - 1)
        values = dI + 1j * dQ
        if self.use_phase_ref and ref is not None:
            # skip reference if trace length doesn't match
            if len(ref['y']) != len(vY):
                return values
            vRef = np.reshape(ref['y'], (n_segment, int(n_total / n_segment)))
            Iref = (2 * np.trapz(vCos * vRef[:, n0:n0 + length]) /
                    float(length - 1))
            Qref = (2 * np.trapz(vSin * vRef[:, n0:n0 + length]) /
                    float(length - 1))
            # subtract the reference angle
            dAngleRef = np.arctan2(Qref, Iref)
            values /= (np.cos(dAngleRef) + 1j * np.sin(dAngleRef))
        return values

    def demodulate_iq(self, n, signal_i, signal_q, ref=None):
        """Calculate complex signal from complex data and reference

        Parameters
        ----------
        n : int
            Qubit number for which to demodulate

        signal_i : dict
            Dictionary with in-phase signal data

        signal_q : dict
            Dictionary with qudrature signal data

        ref : dict
            Dictionary with reference data

        Returns
        -------
        values : complex numpy array
            Complex array matching number of segments in input

        """
        # get parameters
        frequency = self.frequencies[n] - self.freq_offset
        n_segment = int(self.n_records)
        # get input data from dict, with keys {'y': value, 't0': t0, 'dt': dt}
        if signal_i is None or signal_q is None:
            return np.zeros(n_segment, dtype=complex)
        vI = signal_i['y']
        vQ = signal_q['y']
        if vI.shape != vQ.shape:
            raise ValueError('I and Q must have the same shape.')

        # override segment parameter if input data has more than one dimension
        shape = signal_i.get('shape', vI.shape)
        if len(shape) > 1:
            n_segment = shape[0]
        dt = signal_i['dt']
        # avoid exceptions if no time step is given
        if dt == 0:
            dt = 1.0
        # get indices for data trimming
        n0 = int(round(self.demod_skip / dt))
        n_total = vI.size
        length = 1 + int(round(self.demod_length / dt))
        length = min(length, int(n_total / n_segment) - n0)
        if length <= 1:
            return np.zeros(n_segment, dtype=complex)

        # define data to use, put in 2d array of segments
        vData = np.reshape(vI+1j*vQ, (n_segment, int(n_total / n_segment)))
        # calculate cos/sin vectors, allow segmenting
        vTime = dt * (n0 + np.arange(length, dtype=float))
        vS = np.exp(-2j * np.pi * vTime * frequency)

        # calc I/Q
        dI = np.trapz((vS*vData[:, n0:n0+length]).real)/float(length-1)
        dQ = -np.trapz((vS*vData[:, n0:n0+length]).imag)/float(length-1)
        values = dI + 1j * dQ
        if self.use_phase_ref and ref is not None:
            # skip reference if trace length doesn't match
            if len(ref['y']) != len(vI):
                return values
            vRef = np.reshape(ref['y'], (n_segment, int(n_total / n_segment)))
            vCos = np.cos(2 * np.pi * vTime * frequency)
            vSin = np.sin(2 * np.pi * vTime * frequency)
            Iref = (2 * np.trapz(vCos * vRef[:, n0:n0 + length]) /
                    float(length - 1))
            Qref = (2 * np.trapz(vSin * vRef[:, n0:n0 + length]) /
                    float(length - 1))
            # subtract the reference angle
            dAngleRef = np.arctan2(Qref, Iref)
            values /= (np.cos(dAngleRef) + 1j * np.sin(dAngleRef))
        return values


if __name__ == '__main__':
    pass
