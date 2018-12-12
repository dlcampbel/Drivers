#!/usr/bin/env python
import importlib
import os
import sys

import numpy as np

from BaseDriver import LabberDriver

# dictionary with built-in sequences

class Driver(LabberDriver):
    """This class implements a multi-qubit pulse generator."""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection."""
        # init variables
        self.Q1_scale = 1
        self.Q2_scale = 1
        self.Q1_rot = 0
        self.Q2_rot = 0
        self.Q1_offset = 0
        self.Q2_offset = 0
        self.Q1_fromQ2_rot = 0
        self.Q2_fromQ1_rot = 0
        self.Q1_fromQ2_scale = 1
        self.Q2_fromQ1_scale = 1
        self.Signal1 = complex(1,0)
        self.Signal2 = complex(1,0)

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation."""
        # only do something here if changing the sequence type
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation."""

        # check type of quantity
        if quant.name.startswith('Voltage, QB'):
            self.Q1_scale = self.getValue('Scale - Q1')
            self.Q2_scale = self.getValue('Scale - Q2')
            self.Q1_rot = self.getValue('Rotation - Q1')
            self.Q2_rot = self.getValue('Rotation - Q2')
            self.Q1_offset = self.getValue('Offset - Q1')
            self.Q2_offset = self.getValue('Offset - Q2')
            self.Q1_fromQ2_rot = self.getValue('Rotation - Q2 to Q1')
            self.Q2_fromQ1_rot = self.getValue('Rotation - Q1 to Q2')
            self.Q1_fromQ2_scale = self.getValue('Scale - Q2 to Q1')
            self.Q2_fromQ1_scale = self.getValue('Scale - Q1 to Q2')

            self.Signal1 = self.getValue('Signal Q1 - Input')
            self.Signal2 = self.getValue('Signal Q2 - Input')

            self.Signal1 += self.Q1_fromQ2_scale * self.Signal2 * np.exp(1j * self.Q1_fromQ2_rot)
            self.Signal2 += self.Q2_fromQ1_scale * self.Signal1 * np.exp(1j * self.Q2_fromQ1_rot)

            self.Signal1 *= np.exp(1j * self.Q1_rot)
            self.Signal1 -= self.Q1_offset * complex(1,0)
            self.Signal1 *= self.Q1_scale * complex(1,0)

            self.Signal2 *= np.exp(1j * self.Q2_rot)
            self.Signal2 -= self.Q2_offset * complex(1,0)
            self.Signal2 *= self.Q2_scale * complex(1,0)

            if quant.name[-1] == '1':
                value = self.Signal1
            elif quant.name[-1] == '2':
                value = self.Signal2
            else:
                raise
            
        else:
            # for all other cases, do nothing
            value = quant.getValue()
        return value


if __name__ == '__main__':
    pass
