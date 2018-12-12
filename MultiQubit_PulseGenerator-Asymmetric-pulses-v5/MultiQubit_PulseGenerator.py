#!/usr/bin/env python
import importlib
import os
import sys
import logging

import numpy as np

from BaseDriver import LabberDriver
from sequence_builtin import CPMG, PulseTrain, Rabi
from sequence_rb import SingleQubit_RB, TwoQubit_RB
from sequence import SequenceToWaveforms
log = logging.getLogger('LabberDriver')

# dictionary with built-in sequences
SEQUENCES = {'Rabi': Rabi,
             'CP/CPMG': CPMG,
             'Pulse train': PulseTrain,
             '1-QB Randomized Benchmarking': SingleQubit_RB,
             '2-QB Randomized Benchmarking': TwoQubit_RB,
             'Custom': type(None)}


class Driver(LabberDriver):
    """This class implements a multi-qubit pulse generator."""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection."""
        # init variables
        self.sequence = None
        self.sequence_to_waveforms = SequenceToWaveforms()
        self.waveforms = {}
        # always create a sequence at startup
        name = self.getValue('Sequence')
        self.sendValueToOther('Sequence', name)
        self.signal = [np.zeros(0, dtype=np.complex)
                         for n in range(2)]
        self.signal_final = [np.zeros(0, dtype=np.complex)
                         for n in range(2)]

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation."""
        # only do something here if changing the sequence type
        if quant.name == 'Sequence':
            # create new sequence if sequence type changed
            new_type = SEQUENCES[value]

            if not isinstance(self.sequence, new_type):
                # create a new sequence object
                if value == 'Custom':
                    # for custom python files
                    path = self.getValue('Custom Python file')
                    (path, modName) = os.path.split(path)
                    sys.path.append(path)
                    modName = modName.split('.py')[0]  # strip suffix
                    mod = importlib.import_module(modName)
                    # the custom sequence class has to be named
                    # 'CustomSequence'
                    if not isinstance(self.sequence, mod.CustomSequence):
                        self.sequence = mod.CustomSequence()
                else:
                    # standard built-in sequence
                    self.sequence = new_type()

        elif (quant.name == 'Custom Python file' and
              self.getValue('Sequence') == 'Custom'):
            # for custom python files
            path = self.getValue('Custom Python file')
            (path, modName) = os.path.split(path)
            modName = modName.split('.py')[0]  # strip suffix
            sys.path.append(path)
            mod = importlib.import_module(modName)
            # the custom sequence class has to be named 'CustomSequence'
            if not isinstance(self.sequence, mod.CustomSequence):
                self.sequence = mod.CustomSequence()
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation."""
        # ignore if no sequence
        if self.sequence is None:
            return quant.getValue()

        # check type of quantity
        if (quant.name.startswith('Voltage, QB') or
                quant.name.startswith('Single-shot, QB')):
            # perform demodulation, check if config is updated
            if self.isConfigUpdated():
                # update sequence object with current driver configuation
                config = self.instrCfg.getValuesDict()
                self.sequence.set_parameters(config)
                self.sequence_to_waveforms.set_parameters(config)
            # get qubit index and waveforms
            n = int(quant.name.split(', QB')[1]) - 1
            demod_iq = self.getValue('Demodulation - IQ')
            if demod_iq:
                signal_i = self.getValue('Demodulation - Input I')
                signal_q = self.getValue('Demodulation - Input Q')
            else:
                signal = self.getValue('Demodulation - Input')
            ref = self.getValue('Demodulation - Reference')
            # perform demodulation
            if demod_iq:
                value = self.sequence_to_waveforms.readout.demodulate_iq(
                    n, signal_i, signal_q, ref)
            else:
                value = self.sequence_to_waveforms.readout.demodulate(
                    n, signal, ref)
            # average values if not single-shot
            if not quant.name.startswith('Single-shot, QB'):
                value = np.mean(value)
        # """Perform the Get Value instrument operation."""
        # # ignore if no sequence
        # if self.sequence is None:
        #     return quant.getValue()

        # # check type of quantity
        # if (quant.name.startswith('Voltage, QB') or
        #         quant.name.startswith('Single-shot, QB')):
        #     # perform demodulation, check if config is updated
        #     if self.isConfigUpdated():
        #         # update sequence object with current driver configuation
        #         config = self.instrCfg.getValuesDict()
        #         self.sequence.set_parameters(config)
        #         self.sequence_to_waveforms.set_parameters(config)
        #     # get qubit index and waveforms
        #         for n in range(0,2):
        #             # n = int(quant.name.split(', QB')[1]) - 1
        #             demod_iq = self.getValue('Demodulation - IQ')
        #             if demod_iq:
        #                 signal_i = self.getValue('Demodulation - Input I')
        #                 signal_q = self.getValue('Demodulation - Input Q')
        #             else:
        #                 signal = self.getValue('Demodulation - Input')
        #             ref = self.getValue('Demodulation - Reference')
        #             # perform demodulation
        #             if demod_iq:
        #                 self.signal[n] = self.sequence_to_waveforms.readout.demodulate_iq(
        #                     n, signal_i, signal_q, ref)
        #             else:
        #                 self.signal[n] = self.sequence_to_waveforms.readout.demodulate(
        #                     n, signal, ref)
        #         # rot12 = self.getValue('Rotate - 12')
        #         # rot21 = self.getValue('Rotate - 21')
        #         # rot11 = self.getValue('Rotate - 11')
        #         # rot22 = self.getValue('Rotate - 22')
        #         # scale11 = self.getValue('Scale - 11')
        #         # scale12 = self.getValue('Scale - 12')
        #         # scale21 = self.getValue('Scale - 21')
        #         # scale22 = self.getValue('Scale - 22')
        #         # self.signal_final[0] = scale11 * np.exp(1j*rot11) * (self.signal[0] + scale12 * np.exp(1j*rot12) * self.signal[1])
        #         # self.signal_final[1] = scale22 * np.exp(1j*rot22) * (self.signal[1] + scale21 * np.exp(1j*rot21) * self.signal[0])
        #     m = int(quant.name.split(', QB')[1]) - 1
        #     # average values if not single-shot
        #     if not quant.name.startswith('Single-shot, QB'):
        #         value = np.mean(self.signal[m])
        #     else:
        #         value = self.signal[m]

        elif quant.isVector():
            # traces, check if waveform needs to be re-calculated
            if self.isConfigUpdated():
                # update sequence object with current driver configuation
                config = self.instrCfg.getValuesDict()
                self.sequence.set_parameters(config)
                self.sequence_to_waveforms.set_parameters(config)
                # calcluate waveforms
                self.waveforms = self.sequence_to_waveforms.get_waveforms(
                    self.sequence.get_sequence(config))
            # get correct data from waveforms stored in memory
            value = self.getWaveformFromMemory(quant)
        else:
            # for all other cases, do nothing
            value = quant.getValue()
        return value

    def getWaveformFromMemory(self, quant):
        """Return data from already calculated waveforms."""
        # check which data to return
        if quant.name[-1] in ('1', '2', '3', '4', '5', '6', '7', '8', '9'):
            # get name and number of qubit waveform asked for
            name = quant.name[:-1]
            n = int(quant.name[-1]) - 1
            # get correct vector
            if name == 'Trace - I':
                if self.getValue('Swap IQ'):
                    value = self.waveforms['xy'][n].imag
                else:
                    value = self.waveforms['xy'][n].real
            elif name == 'Trace - Q':
                if self.getValue('Swap IQ'):
                    value = self.waveforms['xy'][n].real
                else:
                    value = self.waveforms['xy'][n].imag
            elif name == 'Trace - Z':
                value = self.waveforms['z'][n]
            elif name == 'Trace - G':
                value = self.waveforms['gate'][n]

        elif quant.name == 'Trace - Readout trig':
            value = self.waveforms['readout_trig']
        elif quant.name == 'Trace - Readout I':
            value = self.waveforms['readout_iq'].real
        elif quant.name == 'Trace - Readout Q':
            value = self.waveforms['readout_iq'].imag

        # return data as dict with sampling information
        dt = 1 / self.sequence_to_waveforms.sample_rate
        value = quant.getTraceDict(value, dt=dt)
        return value

    def getReadout(self, quant):
        """Return data from already calculated waveforms."""
        # check which data to return

        return value


if __name__ == '__main__':
    pass
