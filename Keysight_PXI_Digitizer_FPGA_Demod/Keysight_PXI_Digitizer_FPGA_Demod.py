#!/usr/bin/env python
import sys
sys.path.append('C:\Program Files (x86)\Keysight\SD1\Libraries\Python')

from BaseDriver import LabberDriver, Error, IdError
import keysightSD1

import numpy as np
import os


class Driver(LabberDriver):
    """ This class implements the Keysight PXI digitizer"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        # number of demod blocks in the FPGA
        self.num_of_demods = 5
        #self.demod_sample_size = self.num_of_demods * 15
        self.demod_sample_size = 100
        
        # set time step and resolution
        self.nBit = 16
        self.bitRange = float(2**(self.nBit-1)-1)
        # timeout
        self.timeout_ms = int(1000 * self.dComCfg['Timeout'])
        # get PXI chassis
        self.chassis = int(self.dComCfg.get('PXI chassis', 1))
        # create AWG instance
        self.dig = keysightSD1.SD_AIN()
        AWGPart = self.dig.getProductNameBySlot(
            self.chassis, int(self.comCfg.address))
        self.log('Serial:', self.dig.getSerialNumberBySlot(
            self.chassis, int(self.comCfg.address)))
        if not isinstance(AWGPart, str):
            raise Error('Unit not available')
        # check that model is supported
        dOptionCfg = self.dInstrCfg['options']
        for validId, validName in zip(dOptionCfg['model_id'], dOptionCfg['model_str']):
            if AWGPart.find(validId)>=0:
                # id found, stop searching
                break
        else:
            # loop fell through, raise ID error
            raise IdError(AWGPart, dOptionCfg['model_id'])
        # set model
        self.setModel(validName)
        # sampling rate and number of channles is set by model
        if validName in ('M3102', 'M3302'):
            # 500 MHz models
            self.dt = 2E-9
            self.nCh = 4
        else:
            # assume 100 MHz for all other models
            self.dt = 10E-9
            self.nCh = 4
        # create list of sampled data
        self.lTrace = [np.array([])] * self.nCh
        self.dig.openWithSlot(AWGPart, self.chassis, int(self.comCfg.address))
        # get hardware version - changes numbering of channels
        hw_version = self.dig.getHardwareVersion()
        if hw_version >= 4:
            # KEYSIGHT - channel numbers start with 1
            self.ch_index_zero = 1
        else:
            # SIGNADYNE - channel numbers start with 0
            self.ch_index_zero = 0
        self.log('HW:', hw_version)
        
        if self.getValue('Load FPGA'):
            Bitstream = os.path.join(os.path.dirname(__file__), 'firmware_FPGAFlow_Demod_v4_IQx5_2018-09-02T19_14_50.sbp')
        else:            
            Bitstream = os.path.join(os.path.dirname(__file__), 'firmware_FPGAFlow_Clean_2018-05-31T22_22_11.sbp')
        #Bitstream = os.path.join(os.path.dirname(__file__), 'firmware_FPGAFlow_Demod_v3_IQx5_2018-06-12T20_37_04.sbp')
        #Bitstream = os.path.join(os.path.dirname(__file__), 'firmware_FPGAFlow_Demod_v3_IQx5_2018-06-13T19_46_49.sbp')
        #Bitstream = os.path.join(os.path.dirname(__file__), 'firmware_FPGAFlow_Demod_v3_IQx5_wRef_2018-06-25T13_43_00.sbp')

        if (self.dig.FPGAload(Bitstream)) < 0:   
            raise Error('FPGA not loaded, check FPGA version...')

        for n in range(self.num_of_demods):
            LO_freq = self.getValue('LO freq ' + str(n+1))
            self.setFPGALOfreq(n+1,LO_freq)

        self.setFPGATrigger()
        self.setFPGADCoffset()
        self.smsb_info = np.zeros([self.num_of_demods,4],dtype = 'int16');
        


    def getHwCh(self, n):
        """Get hardware channel number for channel n. n starts at 0"""
        return n + self.ch_index_zero


    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        # do not check for error if close was called with an error
        try:
            # flush all memory
            for n in range(self.nCh):
                self.log('Close ch:', n, self.dig.DAQflush(self.getHwCh(n)))
            # close instrument
            self.dig.close()
        except:
            # never return error here
            pass


    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        # start with setting local quant value
        quant.setValue(value)
        # check if channel-specific, if so get channel + name
        if quant.name.startswith('Ch') and len(quant.name)>6:
            ch = int(quant.name[2]) - 1
            name = quant.name[6:]
        else:
            ch, name = None, ''
        if quant.name.startswith('FPGA Voltage') or quant.name.startswith('FPGA Single-shot'):
            demod_num = int(quant.name[-1]) - 1
        # proceed depending on command
        if quant.name in ('External Trig Source', 'External Trig Config',
                          'Trig Sync Mode'):
            extSource = int(self.getCmdStringFromValue('External Trig Source'))
            trigBehavior = int(self.getCmdStringFromValue('External Trig Config'))
            sync = int(self.getCmdStringFromValue('Trig Sync Mode'))
            self.dig.DAQtriggerExternalConfig(0, extSource, trigBehavior, sync)
        elif quant.name in ('Trig I/O', ):
            # get direction and sync from index of comboboxes
            direction = int(self.getCmdStringFromValue('Trig I/O'))
            self.dig.triggerIOconfig(direction)
        elif quant.name in ('Analog Trig Channel', 'Analog Trig Config', 'Trig Threshold'):
            # get trig channel
            trigCh = self.getValueIndex('Analog Trig Channel')
            mod = int(self.getCmdStringFromValue('Analog Trig Config'))
            threshold = self.getValue('Trig Threshold')
            self.dig.channelTriggerConfig(self.getHwCh(trigCh), mod, threshold)
        elif name in ('Range', 'Impedance', 'Coupling'):
            # set range, impedance, coupling at once
            rang = self.getRange(ch)
            imp = int(self.getCmdStringFromValue('Ch%d - Impedance' % (ch + 1)))
            coup = int(self.getCmdStringFromValue('Ch%d - Coupling' % (ch + 1)))
            self.dig.channelInputConfig(self.getHwCh(ch), rang, imp, coup)
        # FPGA configuration 
        if quant.name.startswith('LO freq'):
            demod_num = int(quant.name[-1])
            LO_freq = self.getValue('LO freq ' + str(demod_num))
            value = self.setFPGALOfreq(demod_num,LO_freq)
            quant.setValue(value)        
        elif quant.name in ('Skip time', 'Accum. time'):
            self.setFPGATrigger()
        elif quant.name in ('DC offset Ch1', 'DC offset Ch2','DC offset Ch3','DC offset Ch4'):
            self.setFPGADCoffset()
        return value


    def performGetValue(self, quant, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        # check if channel-specific, if so get channel + name
        if quant.name.startswith('Ch') and len(quant.name) > 6:
            ch = int(quant.name[2]) - 1
            name = quant.name[6:]
        else:
            ch, name = None, ''

        if quant.name.startswith('FPGA Voltage') or quant.name.startswith('FPGA Single-shot'):
            demod_num = int(quant.name[-1]) - 1

        if name == 'Signal' or quant.name.startswith('FPGA Voltage') or quant.name.startswith('FPGA Single-shot'):
            if self.isHardwareLoop(options):
                """Get data from round-robin type averaging"""
                (seq_no, n_seq) = self.getHardwareLoopIndex(options)
                nSample = int(self.getValue('Number of samples'))
                # if first sequence call, get data
                if seq_no == 0 and self.isFirstCall(options):
                    # show status before starting acquisition
                    self.reportStatus('Digitizer - Waiting for signal')
                    # get data
                    # self.getTracesHardware(n_seq)
                    self.getTraces(bArm=False, bMeasure=True, n_seq=n_seq)
                    # re-shape data and place in trace buffer
                    self.reshaped_traces = []
                    for trace in self.lTrace:
                        if len(trace) > 0:
                            trace = trace.reshape((n_seq, nSample))
                        self.reshaped_traces.append(trace)
                # after getting data, pick values to return
                if name == 'Signal':
                    return quant.getTraceDict(self.reshaped_traces[ch][seq_no], dt=self.dt)
                elif quant.name.startswith('FPGA Voltage I'):
                    return self.demod_output_I[demod_num]
                elif quant.name.startswith('FPGA Single-shot I'):
                    return quant.getTraceDict(self.demod_output_vector_I[demod_num][seq_no], dt=1)
                elif quant.name.startswith('FPGA Voltage Q'):
                    return self.demod_output_Q[demod_num]
                elif quant.name.startswith('FPGA Single-shot Q'):
                    return quant.getTraceDict(self.demod_output_vector_Q[demod_num][seq_no], dt=1)
                elif quant.name.startswith('FPGA Voltage'):
                    return self.demod_output_SSB[demod_num]
                elif quant.name.startswith('FPGA Single-shot'):
                    return quant.getTraceDict(self.demod_output_vector_SSB[demod_num][seq_no], dt=1)                
                elif quant.name.startswith('FPGA Single-shot REF'):
                    return quant.getTraceDict(self.demod_output_vector_ref[demod_num][seq_no], dt=1)                
                elif quant.name.startswith('FPGA Voltage NP'):
                    return self.demod_output_NP[demod_num]
                elif quant.name.startswith('FPGA Single-shot NP'):
                    return quant.getTraceDict(self.demod_output_vector_NP[demod_num][seq_no], dt=1)                
            # get traces if first call
            if self.isFirstCall(options):
                # don't arm if in hardware trig mode
                self.getTraces(bArm=(not self.isHardwareTrig(options)))
            # return correct data
            if name == 'Signal':
                value = quant.getTraceDict(self.lTrace[ch], dt=self.dt)
            elif quant.name.startswith('FPGA Voltage I'):
                value = self.demod_output_I[demod_num]
            elif quant.name.startswith('FPGA Single-shot I'): 
                value =  quant.getTraceDict(self.demod_output_vector_I[demod_num], dt=1)
            elif quant.name.startswith('FPGA Voltage Q'):
                value = self.demod_output_Q[demod_num]
            elif quant.name.startswith('FPGA Single-shot Q'): 
                value =  quant.getTraceDict(self.demod_output_vector_Q[demod_num], dt=1)
            elif quant.name.startswith('FPGA Voltage'):
                value = self.demod_output_SSB[demod_num]
            elif quant.name.startswith('FPGA Single-shot'): 
                value =  quant.getTraceDict(self.demod_output_vector_SSB[demod_num], dt=1)
            elif quant.name.startswith('FPGA Single-shot REF'): 
                value =  quant.getTraceDict(self.demod_output_vector_ref[demod_num], dt=1)
            elif quant.name.startswith('FPGA Voltage NP'):
                return self.demod_output_NP[demod_num]
            elif quant.name.startswith('FPGA Single-shot NP'):
                return quant.getTraceDict(self.demod_output_vector_NP[demod_num], dt=1)                
                
        else:
            # for all others, return local value
            value = quant.getValue()

        return value


    def performArm(self, quant_names, options={}):
        """Perform the instrument arm operation"""
        # make sure we are arming for reading traces, if not return - commented by RoniW
        #signal_names = ['Ch%d - Signal' % (n + 1) for n in range(4)]
        #signal_arm = [name in signal_names for name in quant_names]
        #if not np.any(signal_arm):
        #    return

        # arm by calling get traces
        if self.isHardwareLoop(options):
            # in hardware looping, number of records is set by the hardware looping
            (seq_no, n_seq) = self.getHardwareLoopIndex(options)
            self.getTraces(bArm=True, bMeasure=False, n_seq=n_seq)
        else:
            self.getTraces(bArm=True, bMeasure=False)


    def getTraces(self, bArm=True, bMeasure=True, n_seq=0):
        """Get all active traces"""
        # # test timing
        # import time
        # t0 = time.clock()
        # lT = []

        # find out which traces to get
        lCh = []
        iChMask = 0
        self.log('Start Trace:')

        for n in range(self.nCh):
            if self.getValue('Ch%d - Enabled' % (n + 1)):
                lCh.append(n)
                iChMask += 2**n
        # get current settings
        #nDemods = int(self.getValue('Number of Demods'))
        nDemods = self.num_of_demods
        
        nPts = max(int(self.getValue('Number of samples')), self.demod_sample_size)
        nCyclePerCall = int(self.getValue('Records per Buffer'))
        # in hardware loop mode, ignore records and use number of sequences
        if n_seq > 0:
            nSeg = n_seq
        else:
            nSeg = int(self.getValue('Number of records'))

        nAv = int(self.getValue('Number of averages'))
        # trigger delay is in 1/sample rate
        nTrigDelay = int(self.getValue('Trig Delay') / self.dt)

        if bArm:
            # clear old data
            self.dig.DAQflushMultiple(iChMask)
            self.lTrace = [np.array([])] * self.nCh
            self.lTrace_raw = [np.array([])] * self.nCh
            self.lTrace_raw[3] = np.zeros((nSeg * nPts))
            self.smsb_info_str = [];
            self.demod_output_vector_I  = np.zeros([self.num_of_demods,nSeg],dtype='complex')
            self.demod_output_I = np.zeros(self.num_of_demods,dtype='complex')
            self.demod_output_vector_Q  = np.zeros([self.num_of_demods,nSeg],dtype='complex')
            self.demod_output_Q = np.zeros(self.num_of_demods,dtype='complex')
            self.demod_output_vector_ref  = np.zeros([self.num_of_demods,nSeg],dtype='complex')
            self.demod_output_ref = np.zeros(self.num_of_demods,dtype='complex')
            self.demod_output_vector_SSB  = np.zeros([self.num_of_demods,nSeg],dtype='complex')
            self.demod_output_SSB = np.zeros(self.num_of_demods,dtype='complex')
            self.demod_output_vector_NP  = np.zeros([self.num_of_demods,nSeg],dtype='complex')
            self.demod_output_NP = np.zeros(self.num_of_demods,dtype='complex')
            self.moment_I2  = np.zeros([self.num_of_demods,nSeg],dtype='complex')
            self.moment_Q2  = np.zeros([self.num_of_demods,nSeg],dtype='complex')

            # configure trigger for all active channels
            for nCh in lCh:
                # init data
                self.lTrace[nCh] = np.zeros((nSeg * nPts))
                # channel number depens on hardware version
                ch = self.getHwCh(nCh)
                # extra config for trig mode
                if self.getValue('Trig Mode') == 'Digital trigger':
                    extSource = int(self.getCmdStringFromValue('External Trig Source'))
                    trigBehavior = int(self.getCmdStringFromValue('External Trig Config'))
                    sync = int(self.getCmdStringFromValue('Trig Sync Mode'))
                    self.dig.DAQtriggerExternalConfig(ch, extSource, trigBehavior, sync)
                    self.dig.DAQdigitalTriggerConfig(ch, extSource, trigBehavior)
                elif self.getValue('Trig Mode') == 'Analog channel':
                    digitalTriggerMode= 0
                    digitalTriggerSource = 0
                    trigCh = self.getValueIndex('Analog Trig Channel')
                    analogTriggerMask = 2**trigCh
                    self.dig.DAQtriggerConfig(ch, digitalTriggerMode, digitalTriggerSource, analogTriggerMask)
                # config daq and trig mode
                trigMode = int(self.getCmdStringFromValue('Trig Mode'))
                self.dig.DAQconfig(ch, nPts, nSeg*nAv, nTrigDelay, trigMode)
            # start acquiring data
            self.dig.DAQstartMultiple(iChMask)
        # lT.append('Start %.1f ms' % (1000*(time.clock()-t0)))
        #
        # return if not measure
        if not bMeasure:
            return
        # define number of cycles to read at a time
        nCycleTotal = nSeg * nAv
        nCall = int(np.ceil(nCycleTotal / nCyclePerCall))
        lScale = [(self.getRange(ch) / self.bitRange) for ch in range(self.nCh)]
        # keep track of progress in percent
        old_percent = -1
        #self.log('nCall:' + str(nCall), level = 30)

        # proceed depending on segment or not segment
        if nSeg <= 1:
            # non-segmented acquisiton
            for n in range(nCall):
                # number of cycles for this call, could be fewer for last call
                nCycle = min(nCyclePerCall, nCycleTotal - (n * nCyclePerCall))
                #self.log('nCycle:' + str(nCycle), level = 30)

                # capture traces one by one
                for nCh in lCh:
                    # channel number depens on hardware version
                    ch = self.getHwCh(nCh)
                    data = self.DAQread(self.dig, ch, nPts * nCycle,
                                        int(1000 + self.timeout_ms / nCall))
                    # stop if no data
                    if data.size == 0:
                        return
                    if nCh==3:
                        #self.log('self.lTrace_raw[nCh]:' + str(self.lTrace_raw[nCh]), level = 30)
                        self.lTrace_raw[nCh] = data
                        self.getDemodValues(self.lTrace_raw[nCh], nPts, nSeg, nCycle)

                    # average
                    data = data.reshape((nCycle, nPts)).mean(0)
                    # adjust scaling to account for summing averages
                    scale = lScale[nCh] * (nCycle / nAv)
                    # convert to voltage, add to total average
                    self.lTrace[nCh] += data * scale

                # report progress, only report integer percent
                if nCall >= 1:
                    new_percent = int(100 * n / nCall)
                    if new_percent > old_percent:
                        old_percent = new_percent
                        self.reportStatus(
                            'Acquiring traces ({}%)'.format(new_percent) + ', FPGA Demod status (keep below 124): ' + ''.join(self.smsb_info_str))

                # break if stopped from outside
                if self.isStopped():
                    break
                # lT.append('N: %d, Tot %.1f ms' % (n, 1000 * (time.clock() - t0)))

        else:
            # segmented acquisition, get caLls per segment
            (nCallSeg, extra_call) = divmod(nSeg, nCyclePerCall)
            # pre-calculate list of cycles/call, last call may have more cycles
            if nCallSeg == 0:
                nCallSeg = 1
                lCyclesSeg = [nSeg]
            else:
                lCyclesSeg = [nCyclePerCall] * nCallSeg
                lCyclesSeg[-1] = nCyclePerCall + extra_call
            # pre-calculate scale, should include scaling for averaging
            lScale = np.array(lScale, dtype=float) / nAv

            for n in range(nAv):
                count = 0
                # loop over number of calls per segment
                #self.log('lCyclesSeg:' + str(lCyclesSeg), level = 30)
                for m, nCycle in enumerate(lCyclesSeg):

                    # capture traces one by one
                    for nCh in lCh:
                        # channel number depens on hardware version
                        ch = self.getHwCh(nCh)
                        data = self.DAQread(self.dig, ch, nPts * nCycle,
                                            int(1000 + self.timeout_ms / nCall))
                        # stop if no data
                        if data.size == 0:
                            return
                        # store all data in one long vector
                        self.lTrace[nCh][count:(count + data.size)] += \
                            data * lScale[nCh]
                        if nCh==3:
                            self.lTrace_raw[nCh][count:(count + data.size)] = data
                            #self.log(str(self.lTrace_raw[nCh]))
                    count += data.size
                self.getDemodValues(self.lTrace_raw[3], nPts, nSeg, nSeg)
                # report progress, only report integer percent
                if nAv >= 1:
                    new_percent = int(100 * n / nAv)
                    #self.log('new_percent:old_percent' + str(new_percent) + ':' + str(old_percent), level = 30)                    
                    if new_percent > old_percent:
                        old_percent = new_percent
                        self.reportStatus(
                            'Acquiring traces ({}%)'.format(new_percent) + ', FPGA Demod status (keep below 124): ' + ''.join(self.smsb_info_str))
                    
                # break if stopped from outside
                if self.isStopped():
                    break

                # lT.append('N: %d, Tot %.1f ms' % (n, 1000 * (time.clock() - t0)))

        # # log timing info
        # self.log(': '.join(lT))


    def getRange(self, ch):
        """Get channel range, as voltage.  Index start at 0"""
        rang = float(self.getCmdStringFromValue('Ch%d - Range' % (ch + 1)))
        return rang


    def DAQread(self, dig, nDAQ, nPoints, timeOut):
        """Read data diretly to numpy array"""
        if dig._SD_Object__handle > 0:
            if nPoints > 0:
                data = (keysightSD1.c_short * nPoints)()
                nPointsOut = dig._SD_Object__core_dll.SD_AIN_DAQread(dig._SD_Object__handle, nDAQ, data, nPoints, timeOut)
                if nPointsOut > 0:
                    return np.frombuffer(data, dtype=np.int16, count=nPoints)
                else:
                    return np.array([], dtype=np.int16)
            else:
                return keysightSD1.SD_Error.INVALID_VALUE
        else:
            return keysightSD1.SD_Error.MODULE_NOT_OPENED

    def getDemodValues(self, data, nPts, nSeg, nCycle):
        """get Demod IQ data from Ch1/2/3 Trace"""
        accum_length = self.getValue('Accum. time')
        nAv = self.getValue('Number of averages')
        lScale = [(self.getRange(ch) / self.bitRange) for ch in range(self.nCh)]
        demod_temp_I  = np.zeros([self.num_of_demods,nCycle],dtype='complex')
        demod_temp_Q  = np.zeros([self.num_of_demods,nCycle],dtype='complex')
        demod_temp_ref  = np.zeros([self.num_of_demods,nCycle],dtype='complex')
        self.smsb_info_str = []
        nDemods = int(self.getValue('Number of Demods'))
        #nDemods = self.num_of_demods
        
        self.use_phase_ref = self.getValue('Use phase reference signal')
        
        for n in range(nDemods):
            y1_lsb = self.lTrace_raw[3][np.arange(0 + n*15,nPts*nCycle,nPts)]
            y1_msb = self.lTrace_raw[3][np.arange(1 + n*15,nPts*nCycle,nPts)]
            x1_lsb = self.lTrace_raw[3][np.arange(2 + n*15,nPts*nCycle,nPts)]
            x1_msb = self.lTrace_raw[3][np.arange(3 + n*15,nPts*nCycle,nPts)]
            y1x1_smsb = self.lTrace_raw[3][np.arange(4 + n*15,nPts*nCycle,nPts)]
            x1_smsb = y1x1_smsb.astype('int8')
            y1_smsb = y1x1_smsb.astype('int16') >> 8
            
            y2_lsb = self.lTrace_raw[3][np.arange(5 + n*15,nPts*nCycle,nPts)]
            y2_msb = self.lTrace_raw[3][np.arange(6 + n*15,nPts*nCycle,nPts)]
            x2_lsb = self.lTrace_raw[3][np.arange(7 + n*15,nPts*nCycle,nPts)]
            x2_msb = self.lTrace_raw[3][np.arange(8 + n*15,nPts*nCycle,nPts)]
            y2x2_smsb = self.lTrace_raw[3][np.arange(9 + n*15,nPts*nCycle,nPts)]
            x2_smsb = y2x2_smsb.astype('int8')
            y2_smsb = y2x2_smsb.astype('int16') >> 8

            y3_lsb = self.lTrace_raw[3][np.arange(10 + n*15,nPts*nCycle,nPts)]
            y3_msb = self.lTrace_raw[3][np.arange(11 + n*15,nPts*nCycle,nPts)]
            x3_lsb = self.lTrace_raw[3][np.arange(12 + n*15,nPts*nCycle,nPts)]
            x3_msb = self.lTrace_raw[3][np.arange(13 + n*15,nPts*nCycle,nPts)]
            y3x3_smsb = self.lTrace_raw[3][np.arange(14 + n*15,nPts*nCycle,nPts)]
            x3_smsb = y3x3_smsb.astype('int8')
            y3_smsb = y3x3_smsb.astype('int16') >> 8

            y1_int64 = y1_lsb.astype('uint16') + (y1_msb.astype('uint16') * (2**16))  + (y1_smsb.astype('int8') * (2**32))
            x1_int64 = x1_lsb.astype('uint16') + (x1_msb.astype('uint16') * (2**16))  + (x1_smsb.astype('int8') * (2**32))
            y2_int64 = y2_lsb.astype('uint16') + (y2_msb.astype('uint16') * (2**16))  + (y2_smsb.astype('int8') * (2**32))
            x2_int64 = x2_lsb.astype('uint16') + (x2_msb.astype('uint16') * (2**16))  + (x2_smsb.astype('int8') * (2**32))
            y3_int64 = y3_lsb.astype('uint16') + (y3_msb.astype('uint16') * (2**16))  + (y3_smsb.astype('int8') * (2**32))
            x3_int64 = x3_lsb.astype('uint16') + (x3_msb.astype('uint16') * (2**16))  + (x3_smsb.astype('int8') * (2**32))
            
            smsb_info_temp = [np.max(np.abs(x1_smsb)), np.max(np.abs(y1_smsb)), np.max(np.abs(x2_smsb)), np.max(np.abs(y2_smsb))]
            
            self.smsb_info[n][0] = smsb_info_temp[0]
            self.smsb_info[n][1] = smsb_info_temp[1]
            self.smsb_info[n][2] = smsb_info_temp[2]
            self.smsb_info[n][3] = smsb_info_temp[3]
            
            smsb_temp_info_str = ' [' + str(self.smsb_info[n][0]) + ', ' + str(self.smsb_info[n][1]) + ', ' + str(self.smsb_info[n][2]) + ', ' + str(self.smsb_info[n][3]) + ']'
            self.smsb_info_str.append(smsb_temp_info_str)
            warning_thr = 124 #warning indication that overflow can occur (int8)
            if smsb_info_temp[0] > warning_thr or smsb_info_temp[1] > warning_thr or smsb_info_temp[2] > warning_thr or smsb_info_temp[3] > warning_thr:
                smsb_temp_info_str2 = ' [' + str(smsb_info_temp[0]) + ', ' + str(smsb_info_temp[1]) + ', ' + str(smsb_info_temp[2]) + ', ' + str(smsb_info_temp[3]) + ']'
                warning_str = 'Warning! overflow may occur in FPGA demod block: ' + str(n) + ', ' + smsb_temp_info_str2
                self.log(warning_str, level = 30)
            
            #self.log('y1_lsb:' + str(y1_lsb.astype('uint16')), level = 30)
            #self.log('y1_msb:' + str(y1_msb.astype('uint16')), level = 30)
            #self.log('y1_smsb:' + str(y1_smsb.astype('int8')), level = 30)
            #self.log('y1_64:' + str(y1_int64.astype('int64')), level = 30)
            
            #self.log('x1_lsb:' + str(x1_lsb.astype('uint16')), level = 30)
            #self.log('x1_msb:' + str(x1_msb.astype('uint16')), level = 30)
            #self.log('x1_smsb:' + str(x1_smsb.astype('int8')), level = 30)
            #self.log('x1_64:' + str(x1_int64.astype('int64')), level = 30)
            
            #self.log('y2_lsb:' + str(y2_lsb.astype('uint16')), level = 30)
            #self.log('y2_msb:' + str(y2_msb.astype('uint16')), level = 30)
            #self.log('y2_smsb:' + str(y2_smsb.astype('int8')), level = 30)
            #self.log('y2_64:' + str(y2_int64.astype('int64')), level = 30)
            
            #self.log('x2_lsb:' + str(x2_lsb.astype('uint16')), level = 30)
            #self.log('x2_msb:' + str(x2_msb.astype('uint16')), level = 30)
            #self.log('x2_smsb:' + str(x2_smsb.astype('int8')), level = 30)
            #self.log('x2_64:' + str(x2_int64.astype('int64')), level = 30)

            #self.demod_output_vector_I[n] += ((x1_lsb.astype('uint16') + x1_msb.astype('int16')*(2**16))+ 1j*(y1_lsb.astype('uint16') + y1_msb.astype('int16')*(2**16)))/2**32/accum_length/nAv
            #self.demod_output_vector_Q[n] += ((x2_lsb.astype('uint16') + x2_msb.astype('int16')*(2**16))+ 1j*(y2_lsb.astype('uint16') + y2_msb.astype('int16')*(2**16)))/2**32/accum_length/nAv


            demod_temp_I = (x1_int64.astype('int64') + 1j * y1_int64.astype('int64') )/2**43/accum_length * lScale[0]
            demod_temp_Q = (x2_int64.astype('int64') + 1j * y2_int64.astype('int64') )/2**43/accum_length * lScale[1]   
            demod_temp_ref = (x3_int64.astype('int64') + 1j * y3_int64.astype('int64') )/2**43/accum_length * lScale[2]   

            if nSeg <= 1:
                demod_temp_I = demod_temp_I.reshape((nCycle, 1)).mean(0)
                demod_temp_Q = demod_temp_Q.reshape((nCycle, 1)).mean(0)
                demod_temp_ref = demod_temp_ref.reshape((nCycle, 1)).mean(0)
                self.demod_output_vector_I[n] += demod_temp_I/nAv * nCycle
                self.demod_output_vector_Q[n] += demod_temp_Q/nAv * nCycle
                self.demod_output_vector_ref[n] += demod_temp_ref/nAv * nCycle
                self.moment_I2[n] += np.power(np.abs(demod_temp_I),2)/nAv * nCycle
                self.moment_Q2[n] += np.power(np.abs(demod_temp_Q),2)/nAv * nCycle
            else:
                self.moment_I2[n] += np.power(np.abs(demod_temp_I),2)/nAv 
                self.moment_Q2[n] += np.power(np.abs(demod_temp_Q),2)/nAv
                self.demod_output_vector_I[n] += demod_temp_I/nAv
                self.demod_output_vector_Q[n] += demod_temp_Q/nAv
                self.demod_output_vector_ref[n] += demod_temp_ref/nAv

            if self.getValue('LO freq ' + str(n+1)) <= 0:
                self.demod_output_vector_SSB[n] = np.real(self.demod_output_vector_I[n]) + np.imag(self.demod_output_vector_Q[n]) - 1j*(np.imag(self.demod_output_vector_I[n]) - np.real(self.demod_output_vector_Q[n]))
            else:
                self.demod_output_vector_SSB[n] = np.real(self.demod_output_vector_I[n]) - np.imag(self.demod_output_vector_Q[n]) - 1j*(np.imag(self.demod_output_vector_I[n]) + np.real(self.demod_output_vector_Q[n]))

            if self.use_phase_ref:
                # subtract the reference angle
                dAngleRef = np.arctan2(self.demod_output_vector_ref[n].imag, self.demod_output_vector_ref[n].real)
                #self.log('dAngleRef: real:' + str(dAngleRef.real) + ', imag:' + str(dAngleRef.imag), level = 30)                
                #self.log('REF: real:' + str(self.demod_output_vector_ref[n].real) + ', imag:' + str(self.demod_output_vector_ref[n].imag), level = 30)                
                self.demod_output_vector_SSB[n] /= (np.cos(dAngleRef) - 1j * np.sin(dAngleRef))

            self.demod_output_I[n] = np.mean(self.demod_output_vector_I[n])
            self.demod_output_Q[n] = np.mean(self.demod_output_vector_Q[n])
            self.demod_output_ref[n] = np.mean(self.demod_output_vector_ref[n])

            self.demod_output_SSB[n] = np.mean(self.demod_output_vector_SSB[n])

            self.demod_output_vector_NP[n] = self.moment_I2[n] + self.moment_Q2[n]
            self.demod_output_NP[n] = np.mean(self.demod_output_vector_NP[n])



    def setFPGALOfreq(self, demod_num, demod_LO_freq):
        FPGA_PcPort_channel = 0            
        tmp_0 = np.zeros(2,dtype = int)
        tmp_1 = np.zeros(2,dtype = int)
        tmp_2 = np.zeros(2,dtype = int)
        tmp_3 = np.zeros(2,dtype = int)
        tmp_4 = np.zeros(2,dtype = int)
        tmp_5 = np.zeros(2,dtype = int)
        LO_freq = np.abs(demod_LO_freq)
        tmp_0[1] = (np.int32(LO_freq * (2**16) * 0 / 100e6 / 5) << 16) | np.int32(LO_freq * (2**16) / 100e6)
        tmp_1[1] = (np.int32(LO_freq * (2**16) * 1 / 100e6 / 5) << 16) | np.int32(LO_freq * (2**16) / 100e6)
        tmp_2[1] = (np.int32(LO_freq * (2**16) * 2 / 100e6 / 5) << 16) | np.int32(LO_freq * (2**16) / 100e6)
        tmp_3[1] = (np.int32(LO_freq * (2**16) * 3 / 100e6 / 5) << 16) | np.int32(LO_freq * (2**16) / 100e6)
        tmp_4[1] = (np.int32(LO_freq * (2**16) * 4 / 100e6 / 5) << 16) | np.int32(LO_freq * (2**16) / 100e6)            
        tmp_5[1] = 0
        
        lo_base_addr = int(0x110)
        lo_demod_addr = lo_base_addr + (demod_num - 1) * 5

        buffer = np.zeros((2,1),dtype = int)            
        buffer[1] = 0; # valid bit to finalize the configuration
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, buffer, 0x3, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA);                        

        self.dig.FPGAwritePCport(FPGA_PcPort_channel, tmp_5, 0x100, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA)
        
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, tmp_0, lo_demod_addr, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA)
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, tmp_1, lo_demod_addr+1, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA)
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, tmp_2, lo_demod_addr+2, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA)
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, tmp_3, lo_demod_addr+3, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA)
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, tmp_4, lo_demod_addr+4, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA)                        
        tmp_5[1] = 1
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, tmp_5, 0x100, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA)            

        buffer[1] = 1; # valid bit to finalize the configuration
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, buffer, 0x3, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA);                        

        value = np.sign(demod_LO_freq) * np.int32(LO_freq * (2**16) / 100e6) * 100e6 / 2**16
                
        return value

    def setFPGATrigger(self):
        FPGA_PcPort_channel = 0
        skip_time = np.int32(np.floor(self.getValue('Skip time')/10e-9) - 4)
        accum_length = np.int32(np.floor(self.getValue('Accum. time')/10e-9))
        wait_time = 100 # hardcoded wait time of 100ns in the FPGA
        total_window = skip_time + accum_length + wait_time # total_window is just a safe mechanism
        buffer = np.zeros((2,1),dtype = int)            
        buffer[1] = np.int32(skip_time);
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, buffer, 0x0, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA);
        buffer[1] = np.int32(accum_length + skip_time);
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, buffer, 0x1, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA);
        buffer[1] = np.int32(total_window);
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, buffer, 0x2, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA);
        buffer[1] = 1; # valid bit to finalize the configuration
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, buffer, 0x3, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA);                        

    def setFPGADCoffset(self):
        FPGA_PcPort_channel = 0
        buffer = np.zeros((2,1),dtype = int)            
        lScale = [(self.getRange(ch)/self.bitRange) for ch in range(self.nCh)]
        
        #self.log('scale:' + str(lScale), level = 30)
    
        buffer[1] = np.int32(self.getValue('DC offset Ch1')/lScale[0]);
        #self.log('input:' + str(self.getValue('DC offset Ch1')), level = 30)
        #self.log('corrected:' + str(np.int32(self.getValue('DC offset Ch1')/lScale[0])), level = 30)
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, buffer, 0x20, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA);
        buffer[1] = np.int32(self.getValue('DC offset Ch2')/lScale[1]);
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, buffer, 0x21, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA);
        buffer[1] = np.int32(self.getValue('DC offset Ch3')/lScale[2]);
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, buffer, 0x22, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA);
        buffer[1] = np.int32(self.getValue('DC offset Ch4')/lScale[3]);
        self.dig.FPGAwritePCport(FPGA_PcPort_channel, buffer, 0x23, keysightSD1.SD_AddressingMode.FIXED, keysightSD1.SD_AccessMode.NONDMA);


#    def getSignalHardwareLoop(self, ch, quant, options):
#        """Get data from round-robin type averaging"""
#        (seq_no, n_seq) = self.getHardwareLoopIndex(options)
#        nSample = int(self.getValue('Number of samples'))
#        # if first sequence call, get data
#        if seq_no == 0 and self.isFirstCall(options):
#            # show status before starting acquisition
#            self.reportStatus('Digitizer - Waiting for signal')
#            # get data
#            # self.getTracesHardware(n_seq)
#            self.getTraces(bArm=False, bMeasure=True, n_seq=n_seq)
#            # re-shape data and place in trace buffer
#            self.reshaped_traces = []
#            for trace in self.lTrace:
#                if len(trace) > 0:
#                    trace = trace.reshape((n_seq, nSample))
#                self.reshaped_traces.append(trace)
#        # after getting data, pick values to return
#        return quant.getTraceDict(self.reshaped_traces[ch][seq_no], dt=self.dt)


if __name__ == '__main__':
    pass
