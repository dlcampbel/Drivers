#!/usr/bin/env python3
import logging
from enum import Enum

import numpy as np
from numpy.random import normal, seed
from numpy.fft import rfft, irfft, rfftfreq

log = logging.getLogger('LabberDriver')


class PulseShape(Enum):
    """Define possible qubit pulses shapes."""

    GAUSSIAN = 'Gaussian'
    ZInit = 'LZ Initialize'
    SQUARE = 'Square'
    RAMP = 'Ramp'
    CZ = 'CZ'
    COSINE = 'Cosine'
    SINSQUARE = 'Sin Square'
    SINSQUAREHALF = 'Sin Square Half'
    LZ = 'Landau-Zener'
    BB = 'Bang-Bang'
    BB_Gaussian = 'Bang-Bang Gaussian'
    Biharmonic = 'Bi-harmonic'
    RANDOM = 'Random'


class PulseType(Enum):
    """Define possible qubit pulse types."""

    XY = 'XY'
    ZXY = 'ZXY'
    Z = 'Z'
    READOUT = 'Readout'


class Pulse(object):
    """Represents physical pulses played by an AWG.

    Parameters
    ----------
    shape : :obj:`PulseShape`
        Pulse shape (the default is PulseShape.GAUSSIAN).
    pulse_type : :obj:`PulseType`
        Pulse type (the default is PulseType.XY).

    Attributes
    ----------
    amplitude : float
        Pulse amplitude.
    width : float
        Pulse width.
    plateau : float
        Pulse plateau.
    frequency : float
        SSB frequency.
    phase : float
        Pulse phase.
    use_drag : bool
        If True, applies DRAG correction.
    drag_coefficient : float
        Drag coefficient.
    drag_detuning : float
        Applies a frequnecy detuning for DRAG pulses.
    truncation_range : float
        The truncation range of Gaussian pulses,
        in units of standard deviations.
    start_at_zero : bool
        If True, forces the pulse to start in 0.

    """

    def __init__(self, shape=PulseShape.GAUSSIAN, pulse_type=PulseType.XY):

        # set variables
        self.amplitude = 0.5
        self.amplitude2 = 0.5
        self.ffinal = 5e9
        self.ffinal2 = 5e9
        self.finitial = 4e9
        self.widthL = 10E-9
        self.widthR = 10E-9
        self.plateau = 0.0
        self.rampwidth = 10e-9
        self.frequency = 0.0
        self.phase = 0.0
        self.shape = shape
        self.use_drag = False
        self.drag_coefficient = 0.0
        self.drag_detuning = 0.0
        self.truncation_range = 5.0
        self.start_at_zero = False
        self.pulse_type = pulse_type
        self.duration = 0

        # For CZ pulses
        self.F_Terms = 1
        self.Coupling = 20E6
        self.Offset = 300E6
        self.Lcoeff = np.array([0.3])
        self.dfdV = 500E6
        self.qubit = None

        # For IQ mixer corrections
        self.iq_ratio = 1.0
        self.iq_skew = 0.0

    def total_duration(self):
        """Get the total duration for the pulse.

        Returns
        -------
        float
            Total duration in seconds.

        """
        # calculate total length of pulse
        if self.shape == PulseShape.SQUARE:
            duration = self.width + self.plateau
        elif self.shape == PulseShape.RAMP:
            duration = 2 * self.width + self.plateau
        elif self.shape == PulseShape.GAUSSIAN:
            duration = self.truncation_range * (self.widthL + self.widthR)/2 + self.plateau
        elif self.shape == PulseShape.RANDOM:
            duration = self.truncation_range * self.widthL + self.plateau
        elif self.shape == PulseShape.ZInit:
            duration = self.truncation_range * (self.widthL + self.widthR)/2 + self.plateau
        elif self.shape == PulseShape.SINSQUARE:
            # duration = (self.widthL + self.widthR)/2 + self.plateau
            duration = (self.widthL + self.widthR)/2 + self.plateau - (self.widthL + self.widthR)/np.pi
        elif self.shape == PulseShape.SINSQUAREHALF:
            # duration = (self.widthL + self.widthR)/2 + self.plateau
            duration = (self.widthL+self.widthR)/4 + self.plateau - (self.widthL+self.widthR)/(2*np.pi)
        elif self.shape == PulseShape.LZ:
            # duration = (self.widthL + self.widthR)/2 + self.plateau
            duration = self.truncation_range * self.widthR / 2 + self.widthL/2 + self.plateau - self.widthL/np.pi
        elif self.shape == PulseShape.BB:
            duration = self.widthL + self.widthR# + 6.72e-9 # + 7.9e-9 (Q1 and Q2) 
        elif self.shape == PulseShape.Biharmonic:
            duration = int(self.plateau) * self.widthL + 3*self.widthL
        elif self.shape == PulseShape.BB_Gaussian:
            # duration = (self.widthL + self.widthR)/2 + self.plateau
            duration =  self.duration + 22.15e-9 #self.plateau + self.truncation_range * self.widthL +
        elif self.shape == PulseShape.CZ:
            duration = self.widthL + self.plateau
        elif self.shape == PulseShape.COSINE:
            duration = self.widthL + self.plateau
        return duration

    def calculate_envelope(self, t0, t):
        """Calculate pulse envelope.

        Parameters
        ----------
        t0 : float
            Pulse position, referenced to center of pulse.

        t : numpy array
            Array with time values for which to calculate the pulse envelope.

        Returns
        -------
        waveform : numpy array
            Array containing pulse envelope.

        """
        # calculate the actual value for the selected indices
        if self.pulse_type == PulseType.ZXY:
            self.amplitude = self.ffinal - self.finitial
            self.amplitude2 = self.ffinal2 - self.finitial
        else:
            self.Offset = 0

        if self.shape == PulseShape.SQUARE:
            # reduce risk of rounding errors by putting checks between samples
            if len(t) > 1:
                t0 += (t[1] - t[0]) / 2.0

            values = ((t >= (t0 - (self.width + self.plateau) / 2)) &
                      (t < (t0 + (self.width + self.plateau) / 2)))

            values = values * self.amplitude + self.Offset

        elif self.shape == PulseShape.RAMP:
            # rising and falling slopes
            vRise = ((t - (t0 - self.plateau / 2 - self.width)) /
                     self.width)
            vRise[vRise < 0.0] = 0.0
            vRise[vRise > 1.0] = 1.0
            vFall = (((t0 + self.plateau / 2 + self.width) - t) /
                     self.width)
            vFall[vFall < 0.0] = 0.0
            vFall[vFall > 1.0] = 1.0
            values = vRise * vFall

            values = values * self.amplitude + self.Offset

        elif self.shape == PulseShape.GAUSSIAN:
            # width is two t std
            # std = self.width/2;
            # alternate; std is set to give total pulse area same as a square
            stdL = self.widthL / np.sqrt(2 * np.pi)
            stdR = self.widthR / np.sqrt(2 * np.pi)
            if self.plateau == 0:
                # pure gaussian, no plateau
                if stdL > 0:
                    values = np.exp(-(t - t0)**2 / (2 * stdL**2))
                else:
                    values = np.zeros_like(t)
            else:
                # add plateau


                values = np.array(((t >= (t0 - self.plateau / 2 + (self.widthL-self.widthR)/2)) &
                                   (t < (t0 + self.plateau / 2 + (self.widthL-self.widthR)/2))), dtype=float)
                if stdL > 0:
                    # before plateau
                    values += (
                        (t < (t0 - self.plateau / 2 + (self.widthL-self.widthR)/2)) *
                        np.exp(-(t - (t0 - self.plateau / 2 + (self.widthL-self.widthR)/2))**2 /
                                (2 * stdL**2))
                    )
                    # after plateau
                    values += (
                        (t >= (t0 + self.plateau / 2 + (self.widthL-self.widthR)/2)) *
                        np.exp(-(t - (t0 + self.plateau / 2 + (self.widthL-self.widthR)/2))**2 /
                                (2 * stdR**2))
                    )

            if self.start_at_zero:
                values = values - values.min()
                values = values / values.max()
            values = values * self.amplitude + self.Offset

        elif self.shape == PulseShape.ZInit:
            # width is two t std
            # std = self.width/2;
            # alternate; std is set to give total pulse area same as a square
            stdL = self.widthL / np.sqrt(2 * np.pi)
            stdR = self.widthR / np.sqrt(2 * np.pi)
            if self.plateau == 0 and self.rampwidth == 0:
                # pure gaussian, no plateau
                if stdL > 0:
                    values = np.exp(-(t - t0)**2 / (2 * stdL**2))
                else:
                    values = np.zeros_like(t)
            else:
                # add plateau

                values0 = np.array(((t >= (t0 - self.plateau/2 + (self.widthL-self.widthR)/2)) &
                                   (t < (t0 + self.rampwidth/2 + (self.widthL-self.widthR)/2))), dtype=float)
                values2 = np.array(((t >= (t0 + self.rampwidth/2 + (self.widthL-self.widthR)/2)) &
                                   (t < (t0 + self.plateau/2 + (self.widthL-self.widthR)/2))), dtype=float)
                # values1 = np.array(((t >= (t0 - self.rampwidth/2 + (self.widthL-self.widthR)/2)) &
                #                    (t < (t0 + self.rampwidth/2 + (self.widthL-self.widthR)/2))), dtype=float)
                vRise = ((t - (t0 - self.rampwidth/2 + (self.widthL-self.widthR)/2)) /
                         self.rampwidth)
                vRise[vRise < 0.0] = 0.0
                vRise[vRise > 1.0] = 0.0
                if stdL > 0:
                    # before plateau
                    values0 += (
                        (t < (t0 - self.plateau / 2 + (self.widthL-self.widthR) / 2)) *
                        np.exp(-(t - (t0 - self.plateau / 2 + (self.widthL-self.widthR) / 2))**2 /
                                (2 * stdL**2))
                    )
                    # after plateau
                    values2 += (
                        (t >= (t0 + self.plateau / 2 + (self.widthL-self.widthR)/2)) *
                        np.exp(-(t - (t0 + self.plateau / 2 + (self.widthL-self.widthR)/2))**2 /
                                (2 * stdR**2))
                    )

            if self.start_at_zero:
                values = values - values.min()
                values = values / values.max()
            values = values2 * self.amplitude2 + values0 * self.amplitude + vRise * (self.amplitude2 - self.amplitude) + self.Offset

        elif self.shape == PulseShape.SINSQUARE:
            # width is two t std
            # std = self.width/2;
            # alternate; std is set to give total pulse area same as a square



            if self.plateau == 0:
                # pure gaussian, no plateau
                if self.widthL > 0:
                    values = -np.array(((t >= (t0 - self.widthL/2)) &
                                   (t < (t0 + self.widthL/2))), dtype=float) * np.sin(2 * np.pi * (t-(t0-self.widthL)) / (self.widthL))
                else:
                    values = np.zeros_like(t)
            else:
                # add plateau
                plateau = self.plateau - (self.widthL + self.widthR)/np.pi

                values = np.array(((t >= (t0 - plateau / 2 - self.widthR/4)) &
                                   (t < (t0 -self.widthR/4))), dtype=float)

                values += -np.array(((t <= (t0 + plateau / 2 + self.widthR/4)) &
                                   (t > (t0 +self.widthR/4))), dtype=float)
                if self.widthL > 0:
                    # before plateau
                    values += (
                        ((t < (t0 - plateau / 2 -self.widthR/4)) &
                            (t >= (t0 - plateau / 2 - self.widthL/4 - self.widthR/4))) *
                        np.sin(2*np.pi * (t - (t0 - plateau/2 - self.widthL/4 - self.widthR/4)) / (self.widthL))
                    )
                    # after plateau
                    values += (
                        ((t > (t0 + plateau / 2 + self.widthR/4)) &
                        (t <= (t0 + plateau / 2 + self.widthL/4 + self.widthR/4))) *
                        np.sin(2*np.pi * (t - (t0 + plateau/2 + self.widthL/4 + self.widthR/4)) / (self.widthL))
                    )

                if self.widthR > 0:
                    # before plateau
                    values += -(
                        ((t <= (t0 +self.widthR/4)) &
                            (t >= (t0 - self.widthR/4))) *
                        np.sin(2*np.pi * (t - t0) / (self.widthR))
                    )


            if self.start_at_zero:
                values = values - values.min()
                values = values / values.max()
            values = values * self.amplitude + self.Offset

        elif self.shape == PulseShape.SINSQUAREHALF:
            # width is two t std
            # std = self.width/2;
            # alternate; std is set to give total pulse area same as a square

            if self.plateau == 0:
                # pure gaussian, no plateau
                if self.widthL > 0:
                    values = -np.array(((t >= (t0 - self.widthL/2 + (self.widthL - self.widthR))) &
                                   (t < (t0 + self.widthL/2+ (self.widthL - self.widthR)))), dtype=float) * np.sin(2 * np.pi * (t-(t0-self.widthL)) / (self.widthL))
                else:
                    values = np.zeros_like(t)
            else:
                # add plateau
                plateau = self.plateau - (self.widthL + self.widthR)/(2*np.pi)

                t0p = t0 + (self.widthL - self.widthR)/8

                values = np.array(((t >= (t0p - plateau / 2)) &
                                   (t < (t0p + plateau / 2))), dtype=float)
                if self.widthL > 0:
                    # before plateau
                    values += (
                        ((t < (t0p - plateau / 2)) &
                            (t >= (t0p - plateau / 2 - self.widthL/4))) *
                        np.sin(2*np.pi * (t - (t0p - plateau/2 - self.widthL/4)) / (self.widthL))
                    )
                    # after plateau
                if self.widthR > 0:
                    values += (
                        ((t > (t0p + plateau / 2)) &
                        (t <= (t0p + plateau / 2 + self.widthR/4))) *
                        np.sin(2*np.pi * (t - (t0p + plateau/2 + self.widthR/4)) / self.widthR + np.pi)
                    )


            if self.start_at_zero:
                values = values - values.min()
                values = values / values.max()
            values = values * self.amplitude + self.Offset

        elif self.shape == PulseShape.LZ:
            # width is two t std
            # std = self.width/2;
            # alternate; std is set to give total pulse area same as a square

            if self.plateau == 0:
                # pure gaussian, no plateau
                if self.widthL > 0:
                    values = -np.array(((t >= (t0 - self.widthL/2 + (self.widthL - self.widthR))) &
                                   (t < (t0 + self.widthL/2+ (self.widthL - self.widthR)))), dtype=float) * np.sin(2 * np.pi * (t-(t0-self.widthL)) / (self.widthL))
                else:
                    values = np.zeros_like(t)
            else:
                # add plateau
                plateau = self.plateau - self.widthL/(np.pi)

                t0p = t0

                values = np.array(((t >= (t0p - plateau / 2)) &
                                   (t < (t0p + plateau / 2))), dtype=float)
                if self.widthL > 0:
                    # before plateau
                    values += (
                        ((t < (t0p - plateau / 2)) &
                            (t >= (t0p - plateau / 2 - self.widthL/2))) *
                        np.sin(2*np.pi * (t - (t0p - plateau/2 - self.widthL/2)) / (self.widthL)-np.pi/2)
                    )
                    # after plateau
                    values += (
                        ((t >= (t0p + plateau / 2)) &
                        (t < (t0p + plateau / 2 + self.widthL/2))) *
                        np.sin(2*np.pi * (t - (t0p + plateau/2 + self.widthL/2)) / self.widthL -np.pi/2)
                    )

                stdR = self.widthR / np.sqrt(2 * np.pi)
                if stdR > 0:
                    # after plateau
                    values += -(
                        (t >= (t0p + plateau / 2 + self.widthL/2)) *
                        np.exp(-(t - (t0 + plateau / 2 + self.widthL/2))**2 /
                                (2 * stdR**2))
                    )
                    # before plateau
                    values += -(
                        (t < (t0p - plateau / 2 - self.widthL/2)) *
                        np.exp(-(t - (t0 - plateau / 2 - self.widthL/2))**2 /
                                (2 * stdR**2))
                    )

            if self.start_at_zero:
                values = values - values.min()
                values = values / values.max()
            values = values * self.amplitude + self.Offset

        elif self.shape == PulseShape.BB:
            

            # pure gaussian, no plateaus
            if self.widthL > 0:
                values = -np.array(((t >= (t0 - self.widthL/2)) &
                               (t < (t0 + self.widthL/2))), dtype=float) * np.sin(2 * np.pi * (t-(t0-self.widthL)) / (self.widthL))
            else:
                values = np.zeros_like(t)
            values = values * self.amplitude + self.Offset
            return values

        elif self.shape == PulseShape.Biharmonic:
            if self.widthL > 0:
                stdL = self.widthL / np.sqrt(2 * np.pi)
                phase = self.widthR
                plateau = (int(self.plateau)+0.5) * self.widthL
                dt = t[1] - t[0]
                values = (
                        np.array(((t >= (t0 - plateau/2)) &
                               (t < (t0 + plateau/2))), dtype=float))
                if stdL > 0:
                    # before plateau
                    values += (
                        (t < (t0 - plateau / 2)) *
                        np.exp(-(t - (t0 - plateau / 2))**2 /
                                (2 * stdL**2))
                    )
                    # after plateau
                    values += (
                        (t >= (t0 + plateau / 2)) *
                        np.exp(-(t - (t0 + plateau / 2))**2 /
                                (2 * stdL**2))
                    )

                        # np.array(((t >= (t0 - self.widthL/2 - plateau/2)) &
                        #        (t <= (t0 + self.widthL/2 + plateau/2))), dtype=float) *
                #phase = 0.045

                values *= -(
                        np.sin(2 * np.pi * (t-(t0- plateau/2)) / self.widthL + 2 * np.pi * (phase))
                        + 1.0 * np.sin(4 * np.pi * (t-(t0 - plateau/2)) / self.widthL + 2 * np.pi * (self.phase + 2*phase))
                        )
                # vi = -(np.sin(2 * np.pi * ((t0 - self.widthL/2 - plateau/2)-(t0-self.widthL/2 - plateau/2)) / self.widthL + 2 * np.pi * (phase))
                #                 + 1.0 * np.sin(4 * np.pi * ((t0 - self.widthL/2 - plateau/2)-(t0-self.widthL/2 - plateau/2)) / self.widthL + 2 * np.pi * (self.phase + 2*phase)))
                # vf = -(np.sin(2 * np.pi * ((t0 + self.widthL/2 + plateau/2)-(t0-self.widthL/2 - plateau/2)) / self.widthL + 2 * np.pi * (phase))
                #                 + 1.0 * np.sin(4 * np.pi * ((t0 + self.widthL/2 + plateau/2)-(t0-self.widthL/2 - plateau/2)) / self.widthL + 2 * np.pi * (self.phase + 2*phase)))
                # dynoffset = (vi + vf)/2
                # dynoffset = (values[0] + values[-1])/2
                # dynoffset = 0
            else:
                values = np.zeros_like(t)
            values = (values) * self.amplitude + self.Offset 

        elif self.shape == PulseShape.RANDOM:
            # width is two t std
            # std = self.width/2;
            # alternate; std is set to give total pulse area same as a square
            stdL = self.widthL / np.sqrt(2 * np.pi)
            if self.plateau == 0:
                # pure gaussian, no plateau
                if stdL > 0:
                    values = np.exp(-(t - t0)**2 / (2 * stdL**2))
                else:
                    values = np.zeros_like(t)
            else:
                # add plateau


                values = np.array(((t >= (t0 - self.plateau / 2 + (self.widthL-self.widthL)/2)) &
                                   (t < (t0 + self.plateau / 2 + (self.widthL-self.widthL)/2))), dtype=float)
                if stdL > 0:
                    # before plateau
                    values += (
                        (t < (t0 - self.plateau / 2)) *
                        np.exp(-(t - (t0 - self.plateau / 2))**2 /
                                (2 * stdL**2))
                    )
                    # after plateau
                    values += (
                        (t >= (t0 + self.plateau / 2)) *
                        np.exp(-(t - (t0 + self.plateau / 2))**2 /
                                (2 * stdL**2))
                    )
                seed(seed = int(self.widthR))
                freqs = rfftfreq(len(t), t[1]-t[0])
                values *= irfft(rfft(normal(size = t.shape)) * np.exp(-freqs**2*self.widthL**2/4))

            values = values * self.amplitude + self.Offset

        elif self.shape == PulseShape.BB_Gaussian:
            
            if self.plateau == 0:
                # pure gaussian, no plateau
                if self.widthL > 0:
                    # std = self.widthL / np.sqrt(2*np.pi)
                    # values = np.exp(-(t - t0)**2 / (2*std**2))
                    values = np.zeros_like(t)
                else:
                    values = np.zeros_like(t)
            else:
                plateau = self.plateau
                std = self.widthL / np.sqrt(2*np.pi)
                if std > 0:
                    # before plateau
                    values = np.exp(-(t - (t0 - plateau/2))**2 / (2*std**2))

                    # after plateau
                    values += -np.exp(-(t - (t0 + plateau/2))**2 / (2*std**2))

                    # values = np.exp(-(t - t0)**2 / (2*std**2))
                else:
                    values = np.zeros_like(t)
            values = values * self.amplitude + self.Offset
            return values

        elif self.shape == PulseShape.CZ:
            # notation and calculations are based on
            # "Fast adiabatic qubit gates using only sigma_z control"
            # PRA 90, 022307 (2014)

            # Initial and final angles on the |11>-|02> bloch sphere
            theta_i = np.arctan(self.Coupling / self.Offset)
            theta_f = np.arctan(self.Coupling / self.amplitude)

            # Normalize fouriere coefficients to initial and final angles
            self.Lcoeff *= ((theta_f - theta_i) /
                            (2 * np.sum(self.Lcoeff[range(0,
                                                          self.F_Terms, 2)])))

            # defining helper variabels
            n = np.arange(1, self.F_Terms + 1, 1)
            n_points = 1000  # lNumber of points in the numerical integration

            # Calculate pulse width in tau variable - See paper for details
            tau = np.linspace(0, 1, n_points)
            theta_tau = np.zeros(n_points)
            for i in range(n_points):
                theta_tau[i] = np.sum((self.Lcoeff *
                                       (1 - np.cos(2 * np.pi * n * tau[i]))) +
                                      theta_i)
            t_tau = np.trapz(np.sin(theta_tau), x=tau)
            Width_tau = self.width / t_tau

            # Calculating angle and time as functions of tau
            tau = np.linspace(0, Width_tau, n_points)
            t_tau = np.zeros(n_points)
            for i in range(n_points):
                theta_tau[i] = np.sum((self.Lcoeff *
                                       (1 - np.cos(2 * np.pi * n * tau[i] /
                                                   Width_tau))) + theta_i)
                if i > 0:
                    t_tau[i] = np.trapz(np.sin(theta_tau[0:i]), x=tau[0:i])

            # Plateau is added as an extra extension of theta_f.
            theta_t = np.ones(len(t)) * theta_i
            for i in range(len(t)):
                if 0 < (t[i] - t0 + self.plateau / 2) < self.plateau:
                    theta_t[i] = theta_f
                elif (0 < (t[i] - t0 + self.width / 2 + self.plateau / 2) <
                        (self.width + self.plateau) / 2):
                    theta_t[i] = np.interp(
                        t[i] - t0 + self.width / 2 + self.plateau / 2,
                        t_tau, theta_tau)
                elif (0 < (t[i] - t0 + self.width / 2 + self.plateau / 2) <
                      (self.width + self.plateau)):
                    theta_t[i] = np.interp(
                        t[i] - t0 + self.width / 2 - self.plateau / 2,
                        t_tau, theta_tau)

            df = self.Coupling * (1 / np.tan(theta_t) - 1 / np.tan(theta_i))
            if self.qubit is None:
                # Use linear dependence if no qubit was given
                values = df / self.dfdV
            else:
                values = self.qubit.df_to_dV(df)

        elif self.shape == PulseShape.COSINE:
            tau = self.widthL
            if self.plateau == 0:
                values = (self.amplitude / 2 *
                          (1 - np.cos(2 * np.pi * (t - t0 + tau / 2) / tau)))
            else:
                values = np.ones_like(t) * self.amplitude
                values[t < t0 - self.plateau / 2] = self.amplitude / 2 * \
                    (1 - np.cos(2 * np.pi *
                                (t[t < t0 - self.plateau / 2] - t0 +
                                 self.plateau / 2 + tau / 2) / tau))
                values[t > t0 + self.plateau / 2] = self.amplitude / 2 * \
                    (1 - np.cos(2 * np.pi *
                                (t[t > t0 + self.plateau / 2] - t0 -
                                 self.plateau / 2 + tau / 2) / tau))

            values = values * self.amplitude + self.Offset

        # Make sure the waveform is zero outside the pulse
        values[t < (t0 - self.total_duration() / 2)] = self.Offset
        values[t > (t0 + self.total_duration() / 2)] = self.Offset
        return values

    def calculate_waveform(self, t0, t):
        """Calculate pulse waveform including phase shifts and SSB-mixing.

        Parameters
        ----------
        t0 : float
            Pulse position, referenced to center of pulse.

        t : numpy array
            Array with time values for which to calculate the pulse waveform.

        Returns
        -------
        waveform : numpy array
            Array containing pulse waveform.

        """
        y = self.calculate_envelope(t0, t)
        if self.use_drag:
            beta = self.drag_coefficient / (t[1] - t[0])
            y = y + 1j * beta * np.gradient(y)
            y = y * np.exp(1j * 2 * np.pi * self.drag_detuning *
                           (t - t0 + self.total_duration() / 2))

        if self.pulse_type in (PulseType.XY, PulseType.READOUT):
            # Apply phase and SSB
            phase = self.phase
            # single-sideband mixing, get frequency
            omega = 2 * np.pi * self.frequency
            # apply SSBM transform
            data_i = self.iq_ratio * (y.real * np.cos(omega * t - phase) +
                                      - y.imag * np.cos(omega * t - phase +
                                                        np.pi / 2))
            data_q = (y.real * np.sin(omega * t - phase + self.iq_skew) +
                      -y.imag * np.sin(omega * t - phase + self.iq_skew +
                                       np.pi / 2))
            y = data_i + 1j * data_q

        if self.pulse_type == PulseType.ZXY:
            # Apply phase and SSB
            phase = self.phase
            # single-sideband mixing, get frequency
            omega = 2 * np.pi * self.frequency
            # apply SSBM transform
            phase1 = 0.2
            if np.abs(self.frequency) > 1:
                data = (y - self.Offset) * np.cos(omega * t - phase1 - phase) + 0.55 * (y - self.Offset) * np.cos(2 * omega * t - 2 * phase1) + self.Offset
            else:
                data = (y - self.Offset) * np.cos(omega * t) + self.Offset
            y = data

        # Calibrate voltage to qubit spectra if given
        if self.shape in (PulseShape.COSINE, PulseShape.SQUARE, PulseShape.RAMP, PulseShape.GAUSSIAN, PulseShape.SINSQUARE, PulseShape.SINSQUAREHALF,PulseShape.LZ, PulseShape.BB, PulseShape.BB_Gaussian, PulseShape.ZInit, PulseShape.Biharmonic, PulseShape.RANDOM):
            if self.pulse_type == PulseType.ZXY:
                non_zero_vals = np.ones_like(y)
                non_zero_vals[np.abs(y)!=0] = 0
                y += non_zero_vals*self.Offset
                if self.qubit is None:
                    # Use linear dependence if no qubit was given
                    y = y / self.dfdV -  self.Offset / self.dfdV
                else:
                    y = self.qubit.f_to_V(y) - self.qubit.f_to_V(np.ones_like(y) * self.Offset)
        return y


if __name__ == '__main__':
    pass
