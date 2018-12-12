#!/usr/bin/env python3
import logging
import random as rnd

import numpy as np

from gates import Gate
from sequence import Sequence
import time

log = logging.getLogger('LabberDriver')

def log_gates(g):

    if g == Gate.ARP:
        val = 'ARP'
    elif g == Gate.ZX2p:
        val = 'ZX2p'
    elif g == Gate.ZX2m:
        val = 'ZX2m'
    elif g == Gate.ZY2p:
        val = 'ZY2p'
    elif g == Gate.ZY2m:
        val = 'ZY2m'
    elif g == Gate.Z2p:
        val = 'Z2p'
    elif g == Gate.Z2m:
        val = 'Z2m'
    elif g == Gate.Zp:
        val = 'Zp'
    elif g == Gate.Zm:
        val = 'Zm'
    elif g == Gate.Zalign:
        val = 'I'
    elif g == Gate.Z0:
        val = 'I'
    else:
        val = 'No idea what this gate is'
    return val

def log_2qb_gates(gate_seq1A, gate_seq1B, gate_seq2A, gate_seq2B):
    log.log(30, '==============================')
    for g1A, g1B, g2A, g2B in zip(gate_seq1A, gate_seq1B, gate_seq2A, gate_seq2B):
        log.log(30, '{}; {}; {}; {}'.format(log_gates(g1A), log_gates(g1B), log_gates(g2A), log_gates(g2B)))
    log.log(30, '==============================')

def add_singleQ_cliffordB(index, gate_seq, pad_with_I=True):
    """Add single qubit clifford (24)."""
    length_before = len(gate_seq)
    # Paulis
    if index == 0:
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)h
    elif index == 1:
        # X+
        gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)
    elif index == 2:
        # Y+
        gate_seq.append(Gate.ZY2p)
        gate_seq.append(Gate.ZY2p)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)
    elif index == 3:
        # Z+
        gate_seq.append(Gate.Zp)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)

    # 2pi/3 rotations
    elif index == 4:
        # Y/2+ X/2+
        gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)
    elif index == 5:
        # Y/2- X/2+
        gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.Z2p)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)
    elif index == 6:
        # Y/2+ X/2-
        gate_seq.append(Gate.ZX2m)
        # gate_seq.append(Gate.ZX2p)
        # gate_seq.append(Gate.ZX2p)
        # gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.Z2p)
        gate_seq.append(Gate.Z0)
    elif index == 7:
        # Y/2- X/2-
        gate_seq.append(Gate.ZX2m)
        # gate_seq.append(Gate.ZX2p)
        # gate_seq.append(Gate.ZX2p)
        # gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.Z0)
    elif index == 8:
        # X/2+ Y/2+
        gate_seq.append(Gate.ZY2p)
        gate_seq.append(Gate.Z2p)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)
    elif index == 9:
        # X/2- Y/2+
        gate_seq.append(Gate.ZY2p)
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)
    elif index == 10:
        # X/2+ Y/2-
        gate_seq.append(Gate.ZY2m)
        # gate_seq.append(Gate.ZY2p)
        # gate_seq.append(Gate.ZY2p)
        # gate_seq.append(Gate.ZY2p)
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.Z0)
    elif index == 11:
        # X/2- Y/2-
        gate_seq.append(Gate.ZY2m)
        # gate_seq.append(Gate.ZY2p)
        # gate_seq.append(Gate.ZY2p)
        # gate_seq.append(Gate.ZY2p)
        gate_seq.append(Gate.Z2p)
        gate_seq.append(Gate.Z0)

    # pi/2 rotations
    elif index == 12:
        # X/2+
        gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)
    elif index == 13:
        # X/2-
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.ZX2p)
        # gate_seq.append(Gate.ZX2p)
        # gate_seq.append(Gate.ZX2p)
        # gate_seq.append(Gate.Z0)
    elif index == 14:
        # Y/2+
        gate_seq.append(Gate.ZY2p)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)
    elif index == 15:
        # Y/2-
        gate_seq.append(Gate.ZY2m)
        # gate_seq.append(Gate.ZY2p)
        # gate_seq.append(Gate.ZY2p)
        # gate_seq.append(Gate.ZY2p)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)
    elif index == 16:
        # X/2+ Y/2+ X/2-
        gate_seq.append(Gate.Z2p)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)
    elif index == 17:
        # X/2+ Y/2- X/2+
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)

    # Hadamard-Like
    elif index == 18:
        # Y/2+ X+
        gate_seq.append(Gate.Zm)
        gate_seq.append(Gate.ZY2p)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)
    elif index == 19:
        # Y/2- X+
        gate_seq.append(Gate.Zp)
        gate_seq.append(Gate.ZY2m)
        # gate_seq.append(Gate.ZY2p)
        # gate_seq.append(Gate.ZY2p)
        # gate_seq.append(Gate.ZY2p)
        gate_seq.append(Gate.Z0)
    elif index == 20:
        # X/2+ Y+
        gate_seq.append(Gate.ZX2m)
        # gate_seq.append(Gate.ZX2p)
        # gate_seq.append(Gate.ZX2p)
        # gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.Zp)
        gate_seq.append(Gate.Z0)
    elif index == 21:
        # X/2- Y+
        gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.Zm)
        gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)
    elif index == 22:
        # X/2+ Y/2+ X/2+
        gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.Z2m)
        # gate_seq.append(Gate.Z0)
    elif index == 23:
        # X/2- Y/2+ X/2-
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        # gate_seq.append(Gate.Z0)
    else:
        raise ValueError(
            'index is out of range. it should be smaller than 24 and greater'
            ' or equal to 0: ', str(index))

    length_after = len(gate_seq)
    if pad_with_I:
        # Force the clifford to have a length of 3 gates
        for i in range(3-(length_after-length_before)):
            gate_seq.append(Gate.I)

def add_singleQ_cliffordC(index, gate_seq, pad_with_I=True):
    """Add single qubit clifford (24)."""
    length_before = len(gate_seq)
    # Paulis
    if index == 0:
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 1:
        # X+
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 2:
        # Y+
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 3:
        # Z+
        gate_seq.append(Gate.Zp)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)

    # 2pi/3 rotations
    elif index == 4:
        # Y/2+ X/2+
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 5:
        # Y/2- X/2+
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Z2p)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 6:
        # Y/2+ X/2-
        # gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Z2p)
        # gate_seq.append(Gate.Z0)
    elif index == 7:
        # Y/2- X/2-
        # gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Z2m)
        # gate_seq.append(Gate.Z0)
    elif index == 8:
        # X/2+ Y/2+
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.Z2p)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 9:
        # X/2- Y/2+
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 10:
        # X/2+ Y/2-
        # gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.Z2m)
        # gate_seq.append(Gate.Z0)
    elif index == 11:
        # X/2- Y/2-
        # gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.Z2p)
        # gate_seq.append(Gate.Z0)

    # pi/2 rotations
    elif index == 12:
        # X/2+
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 13:
        # X/2-
        # gate_seq.append(Gate.ZX2m)
        # gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Z0)
    elif index == 14:
        # Y/2+
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 15:
        # Y/2-
        # gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.ZY2m)
        # gate_seq.append(Gate.Z0)
        # gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 16:
        # X/2+ Y/2+ X/2-
        gate_seq.append(Gate.Z2p)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 17:
        # X/2+ Y/2- X/2+
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)

    # Hadamard-Like
    elif index == 18:
        # Y/2+ X+
        gate_seq.append(Gate.Zm)
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 19:
        # Y/2- X+
        gate_seq.append(Gate.Zp)
        # gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.ZY2m)
        # gate_seq.append(Gate.Z0)
    elif index == 20:
        # X/2+ Y+
        # gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Zp)
        # gate_seq.append(Gate.Z0)
    elif index == 21:
        # X/2- Y+
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Zm)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 22:
        # X/2+ Y/2+ X/2+
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.Z0)
    elif index == 23:
        # X/2- Y/2+ X/2-
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Z0)
    else:
        raise ValueError(
            'index is out of range. it should be smaller than 24 and greater'
            ' or equal to 0: ', str(index))

    length_after = len(gate_seq)
    if pad_with_I:
        # Force the clifford to have a length of 3 gates
        for i in range(3-(length_after-length_before)):
            gate_seq.append(Gate.I)

def add_singleQ_cliffordA(index, gate_seq, pad_with_I=True):
    """Add single qubit clifford (24)."""
    length_before = len(gate_seq)
    # Paulis
    if index == 0:
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 1:
        # X+
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Z0)
    elif index == 2:
        # Y+
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.Z0)
    elif index == 3:
        # Z+
        gate_seq.append(Gate.Zp)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)

    # 2pi/3 rotations
    elif index == 4:
        # Y/2+ X/2+
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.Z0)
    elif index == 5:
        # Y/2- X/2+
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Z2p)
        gate_seq.append(Gate.Z0)
    elif index == 6:
        # Y/2+ X/2-
        gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.Z2p)
        gate_seq.append(Gate.Z0)
    elif index == 7:
        # Y/2- X/2-
        gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.Z0)
    elif index == 8:
        # X/2+ Y/2+
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.Z2p)
        gate_seq.append(Gate.Z0)
    elif index == 9:
        # X/2- Y/2+
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.Z0)
    elif index == 10:
        # X/2+ Y/2-
        gate_seq.append(Gate.ZY2p)
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.Z0)
    elif index == 11:
        # X/2- Y/2-
        gate_seq.append(Gate.ZY2p)
        gate_seq.append(Gate.Z2p)
        gate_seq.append(Gate.Z0)

    # pi/2 rotations
    elif index == 12:
        # X/2+
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 13:
        # X/2-
        gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 14:
        # Y/2+
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 15:
        # Y/2-
        gate_seq.append(Gate.ZY2p)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 16:
        # X/2+ Y/2+ X/2-
        gate_seq.append(Gate.Z2p)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)
    elif index == 17:
        # X/2+ Y/2- X/2+
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.Z0)
        gate_seq.append(Gate.Z0)

    # Hadamard-Like
    elif index == 18:
        # Y/2+ X+
        gate_seq.append(Gate.Zm)
        gate_seq.append(Gate.ZY2m)
        gate_seq.append(Gate.Z0)
    elif index == 19:
        # Y/2- X+
        gate_seq.append(Gate.Zp)
        gate_seq.append(Gate.ZY2p)
        gate_seq.append(Gate.Z0)
    elif index == 20:
        # X/2+ Y+
        gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.Zp)
        gate_seq.append(Gate.Z0)
    elif index == 21:
        # X/2- Y+
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Zm)
        gate_seq.append(Gate.Z0)
    elif index == 22:
        # X/2+ Y/2+ X/2+
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.ZX2m)
        gate_seq.append(Gate.Z2m)
    elif index == 23:
        # X/2- Y/2+ X/2-
        gate_seq.append(Gate.Z2m)
        gate_seq.append(Gate.ZX2p)
        gate_seq.append(Gate.ZX2p)
    else:
        raise ValueError(
            'index is out of range. it should be smaller than 24 and greater'
            ' or equal to 0: ', str(index))

    length_after = len(gate_seq)
    if pad_with_I:
        # Force the clifford to have a length of 3 gates
        for i in range(3-(length_after-length_before)):
            gate_seq.append(Gate.I)


def add_twoQ_clifford(index, gate_seq_1A, gate_seq_1B, gate_seq_2A, gate_seq_2B):
    """Add single qubit clifford (11520 = 576 + 5184 + 5184 + 576)."""
    if (index < 0):
        raise ValueError(
            'index is out of range. it should be smaller than 11520 and '
            'greater or equal to 0: ', str(index))
    elif (index < 576):
        add_singleQ_based_twoQ_clifford(index, gate_seq_1A, gate_seq_1B, gate_seq_2A, gate_seq_2B)
    elif (index < 5184 + 576):
        add_CNOT_like_twoQ_clifford(index, gate_seq_1A, gate_seq_1B, gate_seq_2A, gate_seq_2B)
    elif (index < 5184 + 5184 + 576):
        add_iSWAP_like_twoQ_clifford(index, gate_seq_1A, gate_seq_1B, gate_seq_2A, gate_seq_2B)
    elif (index < 576 + 5184 + 5184 + 576):
        add_SWAP_like_twoQ_clifford(index, gate_seq_1A, gate_seq_1B, gate_seq_2A, gate_seq_2B)
    else:
        raise ValueError(
            'index is out of range. it should be smaller than 11520 and '
            'greater or equal to 0: ', str(index))

    pass


def add_singleQ_S1(index, gate_seqA, gate_seqB):
    """Add single qubit clifford from S1.

    (I-like-subset of single qubit clifford group) (3)
    """
    if index == 0:
        gate_seqA.append(Gate.Z0)
        gate_seqA.append(Gate.Z0)  # auxiliary
        gate_seqA.append(Gate.Z0)  # auxiliary
        gate_seqB.append(Gate.Z0)
        gate_seqB.append(Gate.Z0)  # auxiliary
        gate_seqB.append(Gate.Z0)  # auxiliary
    elif index == 1:
        # X/2 Y/2
        gate_seqA.append(Gate.Z2p)
        gate_seqA.append(Gate.ZX2m)
        gate_seqA.append(Gate.Z0)  # auxiliary
        gate_seqB.append(Gate.Z2p)
        gate_seqB.append(Gate.ZX2p)
        gate_seqB.append(Gate.Z0)  # auxiliary
    elif index == 2:
        #-Y/2 -X/2
        gate_seqA.append(Gate.ZX2p)
        gate_seqA.append(Gate.Z2m)
        gate_seqA.append(Gate.Z0)  # auxiliary
        gate_seqB.append(Gate.ZX2m)
        gate_seqB.append(Gate.Z2m)
        gate_seqB.append(Gate.Z0)  # auxiliary


def add_singleQ_S1_X2p(index, gate_seqA, gate_seqB):
    """Add single qubit clifford from S1_X2p.

    (X2p-like-subset of single qubit clifford group) (3)
    """
    if index == 0:
        gate_seqA.append(Gate.ZX2m)
        gate_seqA.append(Gate.Z0)  # auxiliary
        gate_seqA.append(Gate.Z0)  # auxiliary
        gate_seqB.append(Gate.ZX2p)
        gate_seqB.append(Gate.Z0)  # auxiliary
        gate_seqB.append(Gate.Z0)  # auxiliary
    elif index == 1:
        # X/2 Y/2 X/2
        gate_seqA.append(Gate.Z2p)
        gate_seqA.append(Gate.ZX2m)
        gate_seqA.append(Gate.ZX2m)
        gate_seqB.append(Gate.Z2p)
        gate_seqB.append(Gate.ZX2p)
        gate_seqB.append(Gate.ZX2p)
    elif index == 2:
        gate_seqA.append(Gate.ZY2p)
        gate_seqA.append(Gate.Z0)  # auxiliary
        gate_seqA.append(Gate.Z0)  # auxiliary
        gate_seqB.append(Gate.ZY2m)
        gate_seqB.append(Gate.Z0)  # auxiliary
        gate_seqB.append(Gate.Z0)  # auxiliary


def add_singleQ_S1_Y2p(index, gate_seqA, gate_seqB):
    """Add single qubit clifford from S1_Y2p.

    (Y2p-like-subset of single qubit clifford group) (3)
    """
    if index == 0:
        gate_seqA.append(Gate.ZY2m)
        gate_seqA.append(Gate.Z0)  # auxiliary
        gate_seqA.append(Gate.Z0)  # auxiliary
        gate_seqB.append(Gate.ZY2p)
        gate_seqB.append(Gate.Z0)  # auxiliary
        gate_seqB.append(Gate.Z0)  # auxiliary
    elif index == 1:
        # +X/2 +Y originally
        gate_seqA.append(Gate.Z2p)
        gate_seqA.append(Gate.ZY2m)
        gate_seqA.append(Gate.Z2p)
        # gate_seqA.append(Gate.Z0)  # auxiliary
        gate_seqB.append(Gate.Z2p)
        gate_seqB.append(Gate.ZY2p)
        gate_seqB.append(Gate.Z2p)
        # gate_seqB.append(Gate.Z0)  # auxiliary
    elif index == 2:
        # X/2 -Y/2 -X/2
        gate_seqA.append(Gate.Z2m)
        gate_seqA.append(Gate.Z0)
        gate_seqA.append(Gate.Z0)
        gate_seqB.append(Gate.Z2m)
        gate_seqB.append(Gate.Z0)
        gate_seqB.append(Gate.Z0)


def add_singleQ_based_twoQ_clifford(index, gate_seq_1A, gate_seq_1B, gate_seq_2A, gate_seq_2B, **kwargs):
    """Add single-qubit-gates-only-based two Qubit Clifford.

    (24*24 = 576)
    (gate_seq_1: gate seq. of qubit #1, gate_seq_t: gate seq. of qubit #2)
    """
    index_1 = index % 24  # randomly sample from single qubit cliffords (24)
    # randomly sample from single qubit cliffords (24)
    index_2 = (index // 24) % 24
    add_singleQ_cliffordA(index_1, gate_seq_1A)
    add_singleQ_cliffordB(index_1, gate_seq_1B)
    add_singleQ_cliffordA(index_2, gate_seq_2A)
    add_singleQ_cliffordB(index_2, gate_seq_2B)


def add_CNOT_like_twoQ_clifford(index, gate_seq_1A, gate_seq_1B, gate_seq_2A, gate_seq_2B, **kwargs):
    """Add CNOT like two Qubit Clifford.

    (24*24*3*3 = 5184)
    (gate_seq_1: gate seq. of qubit #1, gate_seq_t: gate seq. of qubit #2)
    """
    index_1 = index % 3  # randomly sample from S1 (3)
    index_2 = (index // 3) % 3  # randomly sample from S1 (3)
    # randomly sample from single qubit cliffords (24)
    index_3 = (index // 3 // 3) % 24
    # randomly sample from single qubit cliffords (24)
    index_4 = (index // 3 // 3 // 24) % 24

    generator = kwargs.get('generator', 'CZ')
    if generator == 'CZ':
        add_singleQ_S1(index_1, gate_seq_1A, gate_seq_1B)
        add_singleQ_S1_Y2p(index_2, gate_seq_2A, gate_seq_2B)
        gate_seq_1A.append(Gate.Zalign)
        gate_seq_1B.append(Gate.Zalign)
        gate_seq_2A.append(Gate.Zalign)
        gate_seq_2B.append(Gate.Zalign)
        gate_seq_1A.append(Gate.ARP)
        gate_seq_1B.append(Gate.ARP)
        gate_seq_2A.append(Gate.ARP)
        gate_seq_2B.append(Gate.ARP)
        gate_seq_1A.append(Gate.Zalign)
        gate_seq_1B.append(Gate.Zalign)
        gate_seq_2A.append(Gate.Zalign)
        gate_seq_2B.append(Gate.Zalign)
        add_singleQ_cliffordA(index_3, gate_seq_1A)
        add_singleQ_cliffordB(index_3, gate_seq_1B)
        add_singleQ_cliffordA(index_4, gate_seq_2A)
        add_singleQ_cliffordB(index_4, gate_seq_2B)
    elif generator == 'iSWAP':
        pass


def add_iSWAP_like_twoQ_clifford(index, gate_seq_1A, gate_seq_1B, gate_seq_2A, gate_seq_2B, **kwargs):
    """Add iSWAP like two Qubit Clifford.

    (24*24*3*3 = 5184)
    (gate_seq_1: gate seq. of qubit #1, gate_seq_t: gate seq. of qubit #2)
    """
    generator = kwargs.get('generator', 'CZ')
    index_1 = index % 3  # randomly sample from S1_Y2p (3)
    index_2 = (index // 3) % 3  # randomly sample from S1_X2p(3)
    # randomly sample from single qubit cliffords (24)
    index_3 = (index // 3 // 3) % 24
    # randomly sample from single qubit cliffords (24)
    index_4 = (index // 3 // 3 // 24) % 24

    if generator == 'CZ':
        add_singleQ_S1_Y2p(index_1, gate_seq_1A, gate_seq_1B)
        add_singleQ_S1_X2p(index_2, gate_seq_2A, gate_seq_2B)
        gate_seq_1A.append(Gate.Zalign)
        gate_seq_1B.append(Gate.Zalign)
        gate_seq_2A.append(Gate.Zalign)
        gate_seq_2B.append(Gate.Zalign)
        gate_seq_1A.append(Gate.ARP)
        gate_seq_1B.append(Gate.ARP)
        gate_seq_2A.append(Gate.ARP)
        gate_seq_2B.append(Gate.ARP)
        gate_seq_1A.append(Gate.Zalign)
        gate_seq_1B.append(Gate.Zalign)
        gate_seq_2A.append(Gate.Zalign)
        gate_seq_2B.append(Gate.Zalign)
        gate_seq_1A.append(Gate.ZY2m)
        gate_seq_1B.append(Gate.ZY2p)
        gate_seq_2A.append(Gate.ZX2p)
        gate_seq_2B.append(Gate.ZX2m)
        gate_seq_1A.append(Gate.Zalign)
        gate_seq_1B.append(Gate.Zalign)
        gate_seq_2A.append(Gate.Zalign)
        gate_seq_2B.append(Gate.Zalign)
        gate_seq_1A.append(Gate.ARP)
        gate_seq_1B.append(Gate.ARP)
        gate_seq_2A.append(Gate.ARP)
        gate_seq_2B.append(Gate.ARP)
        gate_seq_1A.append(Gate.Zalign)
        gate_seq_1B.append(Gate.Zalign)
        gate_seq_2A.append(Gate.Zalign)
        gate_seq_2B.append(Gate.Zalign)
        add_singleQ_cliffordA(index_3, gate_seq_1A)
        add_singleQ_cliffordB(index_3, gate_seq_1B)
        add_singleQ_cliffordA(index_4, gate_seq_2A)
        add_singleQ_cliffordB(index_4, gate_seq_2B)
    elif generator == 'iSWAP':
        pass


def add_SWAP_like_twoQ_clifford(index, gate_seq_1A, gate_seq_1B, gate_seq_2A, gate_seq_2B, **kwargs):
    """Add SWAP like two Qubit Clifford.

    (24*24*= 576)
    (gate_seq_1: gate seq. of qubit #1, gate_seq_t: gate seq. of qubit #2)
    """
    index_1 = index % 24  # randomly sample from single qubit cliffords (24)
    # randomly sample from single qubit cliffords (24)
    index_2 = (index // 24) % 24
    generator = kwargs.get('generator', 'CZ')
    if generator == 'CZ':
        gate_seq_1A.append(Gate.Z0)
        gate_seq_1B.append(Gate.Z0)
        gate_seq_2A.append(Gate.ZY2m)
        gate_seq_2B.append(Gate.ZY2p)
        gate_seq_1A.append(Gate.Zalign)
        gate_seq_1B.append(Gate.Zalign)
        gate_seq_2A.append(Gate.Zalign)
        gate_seq_2B.append(Gate.Zalign)
        gate_seq_1A.append(Gate.ARP)
        gate_seq_1B.append(Gate.ARP)
        gate_seq_2A.append(Gate.ARP)
        gate_seq_2B.append(Gate.ARP)
        gate_seq_1A.append(Gate.Zalign)
        gate_seq_1B.append(Gate.Zalign)
        gate_seq_2A.append(Gate.Zalign)
        gate_seq_2B.append(Gate.Zalign)
        gate_seq_1A.append(Gate.ZY2m)
        gate_seq_1B.append(Gate.ZY2p)
        gate_seq_2A.append(Gate.ZY2p)
        gate_seq_2B.append(Gate.ZY2m)
        gate_seq_1A.append(Gate.Zalign)
        gate_seq_1B.append(Gate.Zalign)
        gate_seq_2A.append(Gate.Zalign)
        gate_seq_2B.append(Gate.Zalign)
        gate_seq_1A.append(Gate.ARP)
        gate_seq_1B.append(Gate.ARP)
        gate_seq_2A.append(Gate.ARP)
        gate_seq_2B.append(Gate.ARP)
        gate_seq_1A.append(Gate.Zalign)
        gate_seq_1B.append(Gate.Zalign)
        gate_seq_2A.append(Gate.Zalign)
        gate_seq_2B.append(Gate.Zalign)
        gate_seq_1A.append(Gate.ZY2p)
        gate_seq_1B.append(Gate.ZY2m)
        gate_seq_2A.append(Gate.ZY2m)
        gate_seq_2B.append(Gate.ZY2p)
        gate_seq_1A.append(Gate.Zalign)
        gate_seq_1B.append(Gate.Zalign)
        gate_seq_2A.append(Gate.Zalign)
        gate_seq_2B.append(Gate.Zalign)
        gate_seq_1A.append(Gate.ARP)
        gate_seq_1B.append(Gate.ARP)
        gate_seq_2A.append(Gate.ARP)
        gate_seq_2B.append(Gate.ARP)
        gate_seq_1A.append(Gate.Zalign)
        gate_seq_1B.append(Gate.Zalign)
        gate_seq_2A.append(Gate.Zalign)
        gate_seq_2B.append(Gate.Zalign)
        add_singleQ_cliffordA(index_1, gate_seq_1A)
        add_singleQ_cliffordB(index_2, gate_seq_1B)
        add_singleQ_cliffordA(index_2, gate_seq_2A)
        add_singleQ_cliffordB(index_2, gate_seq_2B)

    elif generator == 'iSWAP':
        pass


class SingleQubit_RB(Sequence):
    """Single qubit randomized benchmarking."""

    prev_randomize = -999.999  # store the previous value
    prev_N_cliffords = -999.999  # store the previous value
    prev_interleave = -999.999  # store the previous value
    prev_interleaved_gateA = -999.999  # store the previous value
    prev_interleaved_gateB = -999.999  # store the previous value
    prev_sequence = ''
    prev_gate_seq = []
    prev_sequence_num = int(0)

    def generate_sequence(self, config):
        """Generate sequence by adding gates/pulses to waveforms."""
        # get parameters
        t = time.time()

        sequence = config['Sequence']
        state = config['Parameter #1']
        seqnum = int(config['Parameter #6'])
        # Number of Cliffords to generate
        N_cliffords = int(config['Number of Cliffords'])
        randomize = config['Randomize']
        interleave = config['Interleave 1-QB Gate']
        if interleave is True:
            interleaved_gateB = config['Interleaved 1-QB Gate']
            if interleaved_gateB == 'ZXp':
                val = 'ZXm'
            elif interleaved_gateB == 'ZXm':
                val = 'ZXp'
            elif interleaved_gateB == 'ZX2p':
                val = 'ZX2m'
            elif interleaved_gateB == 'ZX2m':
                val = 'ZX2p'
            elif interleaved_gateB == 'ZYp':
                val = 'ZYm'
            elif interleaved_gateB == 'ZYm':
                val = 'ZYp'
            elif interleaved_gateB == 'ZY2p':
                val = 'ZY2m'
            elif interleaved_gateB == 'ZY2m':
                val = 'ZY2p'
            elif interleaved_gateB == 'Z0':
                val = 'Z0'
            elif interleaved_gateB == 'Zp':
                val = 'Zp'
            elif interleaved_gateB == 'Zm':
                val = 'Zm'
            elif interleaved_gateB == 'Z2p':
                val = 'Z2p'
            elif interleaved_gateB == 'Z2m':
                val = 'Z2m'
            elif interleaved_gateB == 'VZp':
                val = 'VZp'
            interleaved_gateA = val
        else:
            interleaved_gateA = -999.999
            interleaved_gateB = -999.999
        # generate new randomized clifford gates only if configuration changes
        if (self.prev_sequence != sequence or
            # self.prev_sequence_num != sequence_num or
            self.prev_randomize != randomize or
            self.prev_N_cliffords != N_cliffords or
            self.prev_interleave != interleave or
            self.prev_interleaved_gateB != interleaved_gateB or
            self.prev_interleaved_gateA != interleaved_gateA):

            self.prev_randomize = randomize
            self.prev_N_cliffords = N_cliffords
            self.prev_interleave = interleave
            self.prev_sequence = sequence
            # self.prev_sequence_num = sequence_num

            multi_gate_seq = []
            for n in range(int(self.n_qubit/2)):
                # Generate 1QB RB sequence
                single_gate_seqA = []
                #single_gate_seqA.append(Gate.Xp)
                single_gate_seqB = []
                #single_gate_seqB.append(Gate.Zip)
                for i in range(N_cliffords):
                    if n == 0:
                        rndnum = rnd.randint(0, 23)
                    else:
                        rndnum = rnd.randint(0, 23)
                        # log.log(30, 'Random number: {}'.format(rndnum))
                    add_singleQ_cliffordA(rndnum, single_gate_seqA,
                                         pad_with_I=False)
                    add_singleQ_cliffordB(rndnum, single_gate_seqB,
                                         pad_with_I=False)
                    # If interleave gate,
                    if interleave is True:
                        self.prev_interleaved_gateB = interleaved_gateB
                        self.prev_interleaved_gateA = interleaved_gateA
                        single_gate_seqA.append(
                            Gate.__getattr__(interleaved_gateA))
                        single_gate_seqB.append(
                            Gate.__getattr__(interleaved_gateB))

                recovery_gateA, recovery_gateB = self.get_recovery_gate(single_gate_seqB)
                    # qubit_state = np.matrix('1; 0')
                    # initial state: ground state, following the QC community's convention
                    # log.log(30,'CLifford Seq #'+str(i))
                    # log.log(30,'qb init state = '+str(qubit_state))
                    # qubit_state = np.matmul(self.evaluate_sequence(single_gate_seqB), qubit_state)
                    # out = np.abs(np.matmul(self.evaluate_sequence(recovery_gateB), qubit_state))
                    # log.log(30,'Recovery gate seq * gate seq * init state = '+str(out[0][0])+' '+str(out[1][0]))


                for rec_gateA, rec_gateB in zip(recovery_gateA, recovery_gateB):
                    single_gate_seqA.append(rec_gateA)
                    single_gate_seqB.append(rec_gateB)
                # single_gate_seqB.insert(0, Gate.Zlong)
                # single_gate_seqA.insert(0, Gate.Zlong)
                if state:
                    single_gate_seqB.insert(0, Gate.ZX2p)
                    single_gate_seqA.insert(0, Gate.ZX2m)
                    single_gate_seqB.insert(0, Gate.ZX2p)
                    single_gate_seqA.insert(0, Gate.ZX2m)

                single_gate_seqB.insert(0, Gate.Zalign)
                single_gate_seqA.insert(0, Gate.Zalign)
                single_gate_seqB.insert(0, Gate.Xp)
                single_gate_seqA.insert(0, Gate.Xp)
                single_gate_seqB.insert(0, Gate.Zip)
                single_gate_seqA.insert(0, Gate.Zip)
                single_gate_seqB.insert(0, Gate.Zalign)
                single_gate_seqA.insert(0, Gate.Zalign)

                # single_gate_seqA.append(Gate.Zlong)
                # single_gate_seqB.append(Gate.Zlong)

                single_gate_seqA.append(Gate.Zrp)
                single_gate_seqB.append(Gate.Zrp)
                msg = '{}'.format(len(single_gate_seqA))
                # log.log(int(30), msg)
                # logging.basicConfig()
                multi_gate_seq.append(single_gate_seqA)
                multi_gate_seq.append(single_gate_seqB)

            # transpose list of lists
            multi_gate_seq = list(map(list, zip(*multi_gate_seq)))
            self.add_gates(multi_gate_seq)
            self.prev_gate_seq = multi_gate_seq
        else:
            self.add_gates(self.prev_gate_seq)
        log.log(30,'The time to do this was '+str(time.time()-t))



    def evaluate_sequence(self, gate_seq):
        """Evaluate Single Qubit Gate Sequence."""
# http://www.vcpc.univie.ac.at/~ian/hotlist/qc/talks/bloch-sphere-rotations.pdf
        singleQ_gate = np.matrix([[1, 0], [0, 1]])
        for i in range(len(gate_seq)):
            if (gate_seq[i] == Gate.I):
                pass
            elif (gate_seq[i] == Gate.ZX2p):
                singleQ_gate = np.matmul(
                    np.matrix([[1, -1j], [-1j, 1]]) / np.sqrt(2), singleQ_gate)
            elif (gate_seq[i] == Gate.ZX2m):
                singleQ_gate = np.matmul(
                    np.matrix([[1, 1j], [1j, 1]]) / np.sqrt(2), singleQ_gate)
            elif (gate_seq[i] == Gate.ZY2p):
                singleQ_gate = np.matmul(
                    np.matrix([[1, -1], [1, 1]]) / np.sqrt(2), singleQ_gate)
            elif (gate_seq[i] == Gate.ZY2m):
                singleQ_gate = np.matmul(
                    np.matrix([[1, 1], [-1, 1]]) / np.sqrt(2), singleQ_gate)
            elif (gate_seq[i] == Gate.ZXp):
                singleQ_gate = np.matmul(
                    np.matrix([[0, -1j], [-1j, 0]]), singleQ_gate)
            elif (gate_seq[i] == Gate.ZXm):
                singleQ_gate = np.matmul(
                    np.matrix([[0, 1j], [1j, 0]]), singleQ_gate)
            elif (gate_seq[i] == Gate.ZYp):
                singleQ_gate = np.matmul(
                    np.matrix([[0, -1], [1, 0]]), singleQ_gate)
            elif (gate_seq[i] == Gate.ZYm):
                singleQ_gate = np.matmul(
                    np.matrix([[0, 1], [-1, 0]]), singleQ_gate)
            elif (gate_seq[i] in (Gate.Zp, Gate.Zm, Gate.VZp)):
                singleQ_gate = np.matmul(
                    np.matrix([[-1j, 0], [0, 1j]]), singleQ_gate)
            elif (gate_seq[i] in (Gate.Z2p, Gate.VZ2p)):
                singleQ_gate = np.matmul(
                    np.matrix([[1-1j, 0], [0, 1+1j]]) / np.sqrt(2), singleQ_gate)
            elif (gate_seq[i] in (Gate.Z2m, Gate.VZ2m)):
                singleQ_gate = np.matmul(
                    np.matrix([[1+1j, 0], [0, 1-1j]]) / np.sqrt(2), singleQ_gate)
        return singleQ_gate

    def get_recovery_gate(self, gate_seq):
        """Get recovery gate."""
        qubit_state = np.matrix('1; 0')
        # initial state: ground state, following the QC community's convention
        qubit_state = np.matmul(self.evaluate_sequence(gate_seq), qubit_state)

        # find recovery gate which makes qubit_state return to initial state
        if (np.abs(np.linalg.norm(qubit_state.item((0, 0))) - 1) < 0.1):
            # ground state -> I
            recovery_gateA = [Gate.Z0,Gate.Z0,Gate.Z0]
            recovery_gateB = [Gate.Z0,Gate.Z0,Gate.Z0]
        elif (np.abs(np.linalg.norm(qubit_state.item((1, 0))) - 1) < 0.1):
            # excited state -> X Pi
            recovery_gateA = [Gate.ZX2m, Gate.ZX2m, Gate.Z0]
            recovery_gateB = [Gate.ZX2p, Gate.ZX2p, Gate.Z0]
        elif (np.linalg.norm(qubit_state.item((1, 0)) /
                             qubit_state.item((0, 0)) -1) < 0.1):
            # X State  -> Y +Pi/2
            recovery_gateA = [Gate.ZY2m,Gate.ZY2m,Gate.ZY2m]
            recovery_gateB = [Gate.ZY2p,Gate.ZY2p,Gate.ZY2p]
            # recovery_gateA = [Gate.ZY2m,Gate.Z0,Gate.Z0]
            # recovery_gateB = [Gate.ZY2p,Gate.Z0,Gate.Z0]
        elif (np.linalg.norm(qubit_state.item((1, 0)) /
                             qubit_state.item((0, 0)) + 1) < 0.1):
            # -X State -> Y -Pi/2
            recovery_gateA = [Gate.ZY2m,Gate.Z0,Gate.Z0]
            recovery_gateB = [Gate.ZY2p,Gate.Z0,Gate.Z0]
            # recovery_gateA = [Gate.ZY2m,Gate.ZY2m,Gate.ZY2m]
            # recovery_gateB = [Gate.ZY2p,Gate.ZY2p,Gate.ZY2p]

        elif (np.linalg.norm(qubit_state.item((1, 0)) /
                             qubit_state.item((0, 0)) - 1j) < 0.1):
            # Y State -> X -Pi/2
            recovery_gateA = [Gate.ZX2m,Gate.Z0,Gate.Z0]
            recovery_gateB = [Gate.ZX2p,Gate.Z0,Gate.Z0]
            # recovery_gateA = [Gate.ZX2m,Gate.ZX2m,Gate.ZX2m]
            # recovery_gateB = [Gate.ZX2p,Gate.ZX2p,Gate.ZX2p]
        elif (np.linalg.norm(qubit_state.item((1, 0)) /
                             qubit_state.item((0, 0)) + 1j) < 0.1):
            # -Y State -> X +Pi/2
            recovery_gateA = [Gate.ZX2m,Gate.ZX2m,Gate.ZX2m]
            recovery_gateB = [Gate.ZX2p,Gate.ZX2p,Gate.ZX2p]
            # recovery_gateA = [Gate.ZX2m,Gate.Z0,Gate.Z0]
            # recovery_gateB = [Gate.ZX2p,Gate.Z0,Gate.Z0]
        else:
            raise InstrumentDriver.Error(
                'Error in calculating recovery gate. qubit state:' +
                str(qubit_state))
        return recovery_gateA, recovery_gateB


class TwoQubit_RB(Sequence):
    """Two qubit randomized benchmarking."""

    prev_randomize = -999.999  # store the previous value
    prev_N_cliffords = -999.999  # store the previous value
    prev_interleave = -999.999  # store the previous value
    prev_interleaved_gate = -999.999  # store the previous value
    prev_sequence = ''
    prev_gate_seq = []

    def generate_sequence(self, config):
        """Generate sequence by adding gates/pulses to waveforms."""
        # get parameters
        sequence = config['Sequence']
        state = config['Parameter #1']
        qubits_to_benchmark = np.fromstring(
            config['Qubits to Benchmark'], dtype=int, sep='-')
        # Number of Cliffords to generate
        N_cliffords = int(config['Number of Cliffords'])
        randomize = config['Randomize']
        interleave = config['Interleave 2-QB Gate']
        sequence_num = int(config['Parameter #2'])
        if interleave is True:
            interleaved_gate = config['Interleaved 2-QB Gate']
        else:
            interleaved_gate = -999.999

        # generate new randomized clifford gates only if configuration changes
        if (self.prev_sequence != sequence or
            self.prev_sequence_num != sequence_num or
            self.prev_randomize != randomize or
            self.prev_N_cliffords != N_cliffords or
            self.prev_interleave != interleave or
                self.prev_interleaved_gate != interleaved_gate):

            self.prev_randomize = randomize
            self.prev_N_cliffords = N_cliffords
            self.prev_interleave = interleave
            self.prev_sequence = sequence
            self.prev_sequence_num = sequence_num

            multi_gate_seq = []

            # Generate 2QB RB sequence
            gate_seq_1A = [] # modified to represent 4 qubits
            gate_seq_1B = []
            gate_seq_2A = []
            gate_seq_2B = []
            for i in range(N_cliffords):
                rndnum = rnd.randint(0, 11519)
                # rndnum = sequence_num
                # log.log(30, rndnum)
                add_twoQ_clifford(rndnum, gate_seq_1A, gate_seq_1B, gate_seq_2A, gate_seq_2B)
                # If interleave gate,
                if interleave is True:
                    self.prev_interleaved_gate = interleaved_gate
                    if interleaved_gate == 'CZ':
                        gate_seq_1A.append(Gate.Zalign)
                        gate_seq_1B.append(Gate.Zalign)
                        gate_seq_2A.append(Gate.Zalign)
                        gate_seq_2B.append(Gate.Zalign)
                        gate_seq_1A.append(Gate.ARP)
                        gate_seq_1B.append(Gate.ARP)
                        gate_seq_2A.append(Gate.ARP)
                        gate_seq_2B.append(Gate.ARP)
                        gate_seq_1A.append(Gate.Zalign)
                        gate_seq_1B.append(Gate.Zalign)
                        gate_seq_2A.append(Gate.Zalign)
                        gate_seq_2B.append(Gate.Zalign)
                    elif interleaved_gate == 'CZEcho':
                        # CZEcho is a composite gate, so get each gate
                        gate = Gate.CZEcho.value
                        for g in gate.sequence:
                            gate_seq_1A.append(g[0])
                            gate_seq_1B.append(g[1])
                            gate_seq_2A.append(g[2])
                            gate_seq_2B.append(g[3])

            # get recovery gate seq

            (recovery_seq_1A, recovery_seq_1B, recovery_seq_2A, recovery_seq_2B) = self.get_recovery_gate(
                gate_seq_1B, gate_seq_2B)
            log_2qb_gates(gate_seq_1A, gate_seq_1B, gate_seq_2A, gate_seq_2B)
            gate_seq_1A.extend(recovery_seq_1A)
            gate_seq_1B.extend(recovery_seq_1B)
            gate_seq_2A.extend(recovery_seq_2A)
            gate_seq_2B.extend(recovery_seq_2B)
            log_2qb_gates(recovery_seq_1A, recovery_seq_1B, recovery_seq_2A, recovery_seq_2B)

            gate_seq_1A.insert(0, Gate.ZX2m)
            gate_seq_1B.insert(0, Gate.ZX2p)
            gate_seq_2A.insert(0, Gate.Z0)
            gate_seq_2B.insert(0, Gate.Z0)
            gate_seq_1A.insert(0, Gate.ZX2m)
            gate_seq_1B.insert(0, Gate.ZX2p)
            gate_seq_2A.insert(0, Gate.Z0)
            gate_seq_2B.insert(0, Gate.Z0)
            gate_seq_1A.insert(0, Gate.Zalign)
            gate_seq_1B.insert(0, Gate.Zalign)
            gate_seq_2A.insert(0, Gate.Zalign)
            gate_seq_2B.insert(0, Gate.Zalign)
            gate_seq_1A.insert(0, Gate.Xp)
            gate_seq_1B.insert(0, Gate.Xp)
            gate_seq_2A.insert(0, Gate.Xp)
            gate_seq_2B.insert(0, Gate.Xp)
            gate_seq_1A.insert(0, Gate.Zip)
            gate_seq_1B.insert(0, Gate.Zip)
            gate_seq_2A.insert(0, Gate.Zip)
            gate_seq_2B.insert(0, Gate.Zip)
            gate_seq_1A.insert(0, Gate.Zalign)
            gate_seq_1B.insert(0, Gate.Zalign)
            gate_seq_2A.insert(0, Gate.Zalign)
            gate_seq_2B.insert(0, Gate.Zalign)

            # single_gate_seqA.append(Gate.Zlong)
            # single_gate_seqB.append(Gate.Zlong)

            if state:
                gate_seq_1A.append(Gate.ZX2m)
                gate_seq_1B.append(Gate.ZX2p)
                gate_seq_2A.append(Gate.ZX2m)
                gate_seq_2B.append(Gate.ZX2p)
                gate_seq_1A.append(Gate.ZX2m)
                gate_seq_1B.append(Gate.ZX2p)
                gate_seq_2A.append(Gate.ZX2m)
                gate_seq_2B.append(Gate.ZX2p)

            gate_seq_1A.append(Gate.Zrp)
            gate_seq_1B.append(Gate.Zrp)
            gate_seq_2A.append(Gate.Zrp)
            gate_seq_2B.append(Gate.Zrp)

            # Assign two qubit gate sequence to where we want
            # if (self.n_qubit > qubits_to_benchmark[0]):
            #     for i in range(qubits_to_benchmark[0] - 1):
            #         multi_gate_seq.append([None] * len(gate_seq_1))
            #     multi_gate_seq.append(gate_seq_2B)
            #     multi_gate_seq.append(gate_seq_2A)
            #     multi_gate_seq.append(gate_seq_1B)
            #     multi_gate_seq.append(gate_seq_1A)
            #     for i in range(self.n_qubit - qubits_to_benchmark[1]):
            #         multi_gate_seq.append([None] * len(gate_seq_1A))
            # else:
            #     raise ValueError(
            #         '"Number of qubits" should be bigger than'
            #         '"Qubits to Benchmark"')

            # transpose list of lists
            multi_gate_seq.append(gate_seq_1A)
            multi_gate_seq.append(gate_seq_1B)
            multi_gate_seq.append(gate_seq_2A)
            multi_gate_seq.append(gate_seq_2B)

            # transpose list of lists
            multi_gate_seq = list(map(list, zip(*multi_gate_seq)))
            self.add_gates(multi_gate_seq)
            self.prev_gate_seq = multi_gate_seq
        else:
            self.add_gates(self.prev_gate_seq)

        #     # self.add_gates(multi_gate_seq)
        #     for gates in multi_gate_seq:
        #         if gates[0] == Gate.CZ:
        #             self.add_gate(qubit=[0, 1, 2, 3], gate=gates[0])
        #         else:
        #             self.add_gate(qubit=[0, 1, 2, 3], gate=gates)
        #     self.prev_gate_seq = multi_gate_seq
        # else:
        #     for gates in self.prev_gate_seq:
        #         if gates[0] == Gate.CZ:
        #             self.add_gate(qubit=[0, 1, 2, 3], gate=gates[0])
        #         else:
        #             self.add_gate(qubit=[0, 1, 2, 3], gate=gates)

    def evaluate_sequence(self, gate_seq_1, gate_seq_2):
        """Evaulate Two Qubit Gate Sequence."""
        twoQ_gate = np.matrix(
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        for i in range(len(gate_seq_1)):
            gate_1 = np.matrix([[1, 0], [0, 1]])
            gate_2 = np.matrix([[1, 0], [0, 1]])
            if (gate_seq_1[i] == Gate.Z0):
                pass
            if (gate_seq_1[i] == Gate.Zalign):
                pass
            elif (gate_seq_1[i] == Gate.ZX2p):
                gate_1 = np.matmul(
                    np.matrix([[1, -1j], [-1j, 1]]) / np.sqrt(2), gate_1)
            elif (gate_seq_1[i] == Gate.ZX2m):
                gate_1 = np.matmul(
                    np.matrix([[1, 1j], [1j, 1]]) / np.sqrt(2), gate_1)
            elif (gate_seq_1[i] == Gate.ZY2p):
                gate_1 = np.matmul(
                    np.matrix([[1, -1], [1, 1]]) / np.sqrt(2), gate_1)
            elif (gate_seq_1[i] == Gate.ZY2m):
                gate_1 = np.matmul(
                    np.matrix([[1, 1], [-1, 1]]) / np.sqrt(2), gate_1)
            elif (gate_seq_1[i] == Gate.ZXp):
                gate_1 = np.matmul(np.matrix([[0, -1j], [-1j, 0]]), gate_1)
            elif (gate_seq_1[i] == Gate.ZXm):
                gate_1 = np.matmul(np.matrix([[0, 1j], [1j, 0]]), gate_1)
            elif (gate_seq_1[i] == Gate.ZYp):
                gate_1 = np.matmul(np.matrix([[0, -1], [1, 0]]), gate_1)
            elif (gate_seq_1[i] == Gate.ZYm):
                gate_1 = np.matmul(np.matrix([[0, 1], [-1, 0]]), gate_1)
            elif (gate_seq_1[i] in (Gate.Zp, Gate.Zm, Gate.VZp)):
                gate_1 = np.matmul(
                    np.matrix([[-1j, 0], [0, 1j]]), gate_1)
            elif (gate_seq_1[i] in (Gate.Z2p, Gate.VZ2p)):
                gate_1 = np.matmul(
                    np.matrix([[1-1j, 0], [0, 1+1j]]) / np.sqrt(2), gate_1)
            elif (gate_seq_1[i] in (Gate.Z2m, Gate.VZ2m)):
                gate_1 = np.matmul(
                    np.matrix([[1+1j, 0], [0, 1-1j]]) / np.sqrt(2), gate_1)

            if (gate_seq_2[i] == Gate.Z0):
                pass
            elif (gate_seq_2[i] == Gate.Zalign):
                pass
            elif (gate_seq_2[i] == Gate.ZX2p):
                gate_2 = np.matmul(
                    np.matrix([[1, -1j], [-1j, 1]]) / np.sqrt(2), gate_2)
            elif (gate_seq_2[i] == Gate.ZX2m):
                gate_2 = np.matmul(
                    np.matrix([[1, 1j], [1j, 1]]) / np.sqrt(2), gate_2)
            elif (gate_seq_2[i] == Gate.ZY2p):
                gate_2 = np.matmul(
                    np.matrix([[1, -1], [1, 1]]) / np.sqrt(2), gate_2)
            elif (gate_seq_2[i] == Gate.ZY2m):
                gate_2 = np.matmul(
                    np.matrix([[1, 1], [-1, 1]]) / np.sqrt(2), gate_2)
            elif (gate_seq_2[i] == Gate.ZXp):
                gate_2 = np.matmul(np.matrix([[0, -1j], [-1j, 0]]), gate_2)
            elif (gate_seq_2[i] == Gate.ZXm):
                gate_2 = np.matmul(np.matrix([[0, 1j], [1j, 0]]), gate_2)
            elif (gate_seq_2[i] == Gate.ZYp):
                gate_2 = np.matmul(np.matrix([[0, -1], [1, 0]]), gate_2)
            elif (gate_seq_2[i] == Gate.ZYm):
                gate_2 = np.matmul(np.matrix([[0, 1], [-1, 0]]), gate_2)
            elif (gate_seq_2[i] in (Gate.Zp, Gate.Zm, Gate.VZp)):
                gate_2 = np.matmul(
                    np.matrix([[-1j, 0], [0, 1j]]), gate_2)
            elif (gate_seq_2[i] in (Gate.Z2p, Gate.VZ2p)):
                gate_2 = np.matmul(
                    np.matrix([[1-1j, 0], [0, 1+1j]]) / np.sqrt(2), gate_2)
            elif (gate_seq_2[i] in (Gate.Z2m, Gate.VZ2m)):
                gate_2 = np.matmul(
                    np.matrix([[1+1j, 0], [0, 1-1j]]) / np.sqrt(2), gate_2)

            gate_12 = np.kron(gate_1, gate_2)
            if (gate_seq_1[i] == Gate.ARP or gate_seq_2[i] == Gate.ARP):
                gate_12 = np.matmul(
                    np.matrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0],
                               [0, 0, 0, -1]]), gate_12)

            twoQ_gate = np.matmul(gate_12, twoQ_gate)

        return twoQ_gate

    def get_recovery_gate(self, gate_seq_1, gate_seq_2):
        """Get recovery 2QB gate."""
        qubit_state = np.matrix(
            '1; 0; 0; 0')  # initial state: ground state |00>
        # initial state: ground state |00>
        qubit_state = np.matmul(self.evaluate_sequence(
            gate_seq_1, gate_seq_2), qubit_state)

        # find recovery gate which makes qubit_state return to initial state
        total_num_cliffords = 11520
        recovery_seq_1A = []
        recovery_seq_1B = []
        recovery_seq_2A = []
        recovery_seq_2B = []

        log.log(30, 'Qubit state: {}'.format(qubit_state))

        # Search recovery gate in two Qubit clifford group
        index_val = 0
        for i in range(total_num_cliffords):
            add_twoQ_clifford(i, recovery_seq_1A, recovery_seq_1B, recovery_seq_2A, recovery_seq_2B)
            qubit_final_state = np.matmul(self.evaluate_sequence(
                recovery_seq_1B, recovery_seq_2B), qubit_state)
            index_val = i
            # numerical error threshold: 1e-4
            if np.abs(np.abs(qubit_final_state[0]) - 1) < 1e-6:
                break
            else:
                recovery_seq_1A = []
                recovery_seq_1B = []
                recovery_seq_2A = []
                recovery_seq_2B = []

        log.log(30, 'index val: {}'.format(index_val))
        recovery_seq_1A = []
        recovery_seq_1B = []
        recovery_seq_2A = []
        recovery_seq_2B = []
        add_twoQ_clifford(index_val, recovery_seq_1A, recovery_seq_1B, recovery_seq_2A, recovery_seq_2B)

        if (recovery_seq_1B == [] and recovery_seq_2B == []):
            recovery_seq_1A = [None]
            recovery_seq_1B = [None]
            recovery_seq_2A = [None]
            recovery_seq_2B = [None]
        return (recovery_seq_1A, recovery_seq_1B, recovery_seq_2A, recovery_seq_2B)

if __name__ == '__main__':
    help(log.log)