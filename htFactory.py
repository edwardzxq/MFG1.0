#!/usr/bin/env python
###############################################################################
##                                                                           ##
## Copyright (c) Calix Networks, Inc.                                        ##
## All rights reserved.                                                      ##
##                                                                           ##
###############################################################################
##
## VERSION      : 1.0
## DATE         : 2015/07/28 16:52:08
##
## Changes in V1.0 (2016.09.18 by qshi)
##               The Infor,Warning and Error mssage change to be well-formed
##               (i.e. changes from <Error> to <Error> ...</Error>) in Ex-25985
##               Also the ending label added for debug and verbose log.
##
## Changes in V0.9 (2016.08 by simon)
##               -p option added for platfrom automation test added in EX-26288
##
## Changes in V0.8 (2016.07.13 by qshi)
##               desc field added in EX-26170
##
## Changes in V0.7 (2016.04.28 by qshi)
##               verbose dump to log feature added
##
## Changes in V0.6 (2016.02.19 by qshi)
##               Add htDebug sub-class
##
## Changes in V0.5 (2016.01 by qshi)
##               Support XInclude (See ESA-760)
##
## Changes in V0.4 (2016.01 by qshi)
##               Move the htTestCommon out of this file and make it as
##               individual file.
##
## Changes in v0.3 (2015.11 by Kenny)
##               Re-run the failed ports(less than or equal three) for POTS Tone
##
## Changes in v0.2 (20150.10 by qshi)
##               Re-run the failed port(s) for DSL Analog test
##               Save the Summary for each test
##               Save the Debug info if one test failed
##               Show the summary and debug when "-d" specified
##
## AUTHOR       : Qing Shi
## DESCRIPTION  : Primarily used for manufacturing test
##
###############################################################################

import sys
import subprocess
import getopt
from xml.etree import ElementTree as ET
from xml.etree import ElementInclude as EI
from htLog import *
from htError import *
from htBaseCommand import *
from htDefault import *
import hstUtil
from hstUtil import *
from htSensors import *
from htDsl import *
from htBcm import *
from htPots import *
from htTelnet import *
from htDebug import *

# ESA-760, support up to 2 depth of XInclude parsing
m_XINCLUDE_DEPTH = 2
# Search all subelements, on all levels beneath the current element.
m_XPATH_PATTERN  = ".//"

HELPMSG = "         *** Manufacturing Test Suite *** \n \
        \n \
        Usage: ./htFactory.py [-t <TestItem> | [-v] [-n] [-f] ] [-r] [-V] [-d] [-D] [-h] [-p] [-l <count>]\n \
        -h  :   show the help menu \n \
        -v  :   Verbose mode. Display the output on console \n \
        -n  :   Do *Not* output the final checking result(PASSED/FAILD) \n \
                Applies for some version test items. \n \
        -f  :   Forced to kill cardmgr. Used for DSL test items only.\n \
        -r  :   Re-run the test again \n \
        -V  :   Show the version of this script \n \
        -d  :   Dump the last run log of one test item in Debug log\n \
        -D  :   Dump the last run log of one test item in Detail log\n \
        -A  :   Dump *All* test items output from Detail log\n \
        -p  :   Run platform software automation cases \n \
        -l  :   Run the platform software automation case repeatedly with <count> times \n \
        -t  :   Test the items. Avaialbe items are shown below: \n \
                ddr         :   Memory Test \n \
                cpldv       :   Show the CPLD version \n \
                    -n -v option may be needed \n \
                cpldnv      :   Show the CPLD version on network card\n \
                    -n -v option may be needed \n \
                cpldrw      :   Verify the CPLD R/W operation \n \
                powerver1   :   Show version of Power chip 1 on MB \n \
                powerver2   :   Show version of Power chip 2 on MB \n \
                powerver3   :   Show version of Power chip 3 on MB \n \
                powerver4   :   Show version of Power chip 4 on DB \n \
                powerver5   :   Show version of Power chip 5 on DB \n \
                powerver6   :   Show version of Power chip 6 on DB \n \
                    -n -v option may be needed for power version test \n \
                power4      :   Verify Voltage and Current of Power chip 4 on DB \n \
                    Applies for Combo and Overlay cards. \n \
                power5      :   Verify Voltage and Current of Power chip 5 on DB \n \
                power6      :   Verify Voltage and Current of Power chip 6 on DB \n \
                \n \
                cpu         :   CPU test \n \
                i2c         :   I2C checking \n \
                i2csfp      :   I2C SFP model present checking \n \
                pci         :   PCI checking \n \
                emmc        :   EMMC checking \n \
                sensors     :   Sensors checking \n \
                hotsc       :   Hot Swap Controller checking \n \
                rtc         :   RTC checking \n \
                timing      :   Si5341 Timing status checking \n \
                slotid      :   Slot id checking \n \
                vcpvp       :   BCM VP chip detect \n \
                \n \
                bpeth       :   Backplane Ethernet checking \n \
                ftaeth      :   FTA Ethernet checking       \n \
                bpmate      :   Slot to Slot Ethernet checking \n \
                ftauart     :   FTA UART checking \n \
                matesiglb   :   Mate Signal test for only one card via loopback \n \
                    -f must be specified as cardmgr needs to be killed \n \
                matesig     :   Mate Signal test for two cards \n \
                    -f must be specified as cardmgr needs to be killed \n \
                \n \
                ledon       :   Turn on all LEDs on(some with green color and blink) \n \
                ledy        :   Changes some LED color to yellow and blink \n \
                ledoff      :   Turn off all LEDs \n \
                \n \
                slottrlb    :   Slot to Slot traffic test via backplane loopback \n \
                katanas     :   Katana Sensors checking \n \
                katanam     :   Katana Memory Test \n \
                katanatrlb  :   Katana Traffic via Internal Loopback Test \n \
                katanatrsfp :   Katana Traffic via SFP loopback modules Test \n \
                sgmiika2cpu :   SGMII(Katana to CPU) traffic test \n \
                sfp         :   SFP loopback modules Test(No Katana) \n \
                    applicable for VCP cards \n \
                \n \
                afe         :   DSL AFE port test \n \
                dsla        :   DSL Analog Test \n \
                dslbd       :   DSL Bonding Test \n \
                dsllb       :   DSL Loop Test \n \
                dslv        :   DSL BLV Test \n \
                dlvclk      :   DSL DLV Test including 64K clock \n \
                    Do *Not* run this on both cards at the same time \n \
                vcc10gkrlb  :   10G-KR test via VCC loopback connector \n \
                    applicable for DSL SLV Test \n \
                    or VCP 10G Kr lb \n \
                vccoob      :   OOB test via VCC loopback connector(DSL SLV Test) \n \
                    *All DSL* test itesm must be followed by -f option except \n \
                    afe and vccoob. \n \
                vcp64kclk   :   64K Reference clock on VCP cards \n \
                cpu2vplink  :   Link test between CPU and VP chip for VCP \n \
                vphpi       :   HPI bus test \n \
                subhpi      :   HPI bus test for subscriber board on E3-48c r2 \n \
                uphpi       :   HPI bus test for board with uplink DSP on E3-48c r2 \n \
                dslula      :   Uplink DSL Analog test \n \
                uplinkafe   :   Uplink AFE port test \n \
                \n \
                potst       :   POTS Tone Test \n \
                potslv      :   POTS Loop Voltage Test \n \
                potsrv      :   POTS Ring Voltage Test \n \
                potsb       :   POTS Battery Test \n \
                potslc      :   POTS Loop Current Test \n \
                \n \
                dooropen    :   Test whether the Door is open for E3-48c r2 \n \
                doorclose   :   Test whether the Door is close for E3-48c r2 \n \
                almpin      :   Alarm pin test for E3-48c r2 \n \
                linepwr1    :   Line Power 1 test for E3-48c r2 \n \
                linepwr2    :   Line Power 2 test for E3-48c r2 \n \
                linepwr3    :   Line Power 3 test for E3-48c r2 \n \
                phyconn     :   Physical connection using two 2 RJ21 connectors for E3-48c \n \
                killcard    :   Util only. \n \
                    -f option must be specified \n \
                potsbistcfg :   Util only for POTS BIST limitations. \n \
                    available for Combo card only \n \
                \n \
                Example: \n \
                    1) Test the PCI:                htFactory.py -t pci \n \
                    2) Dump the last run of PCI:    htFactory.py -t pci -d \n \
                    3) Dump all verbose log:        htFactory.py -A \n \
                "
#EX-26077
def usage():
    print getSpecBoardHlpMsg()

def show_version():
    print "Version 1.0"

class testCmdParse:
    def __init__(self,cmd):
        self.curCmdIdx = -1
        self.singleCmd = True
        self.inCmd = []
        self.inCmd.append(cmd)
        self.outCmdHandler = None

    def add(self,newchild):
        self.inCmd.append(newchild);

    def ready(self):
        self.curCmdIdx += 1
        #Is there any command follows?
        cmdNext = self.inCmd[self.curCmdIdx].get(g_CMDNEXT)
        if cmdNext is None:
            return True
        else:
            if cmdNext.lower() == g_CMDNEXT_YES:
                self.singleCmd = False
                return False
            else:
                return True

    def getCmdHandler(self):
        cmdName = self.inCmd[0].get(g_CMDNAME)
        if not cmdName:
            print "The Command is Empty!"
            return None

        cmdType = self.inCmd[0].get(g_CMDTYPE)
        cmdNext = self.inCmd[0].get(g_CMDNEXT)
        #create one special class if one type keyword specified
        if cmdType:
            #Temp sensors is special case
            if cmdType == g_CMDTYPE_SENSORS:
                self.outCmdHandler = htTestSensors(self.inCmd)
            elif cmdType == g_CMDTYPE_DSLHMI:
                self.outCmdHandler = htTestDsl(self.inCmd)
            elif cmdType == g_CMDTYPE_BCM:
                self.outCmdHandler = htTestBcm(self.inCmd)
            elif cmdType == g_CMDTYPE_POTS:
                self.outCmdHandler = htTestPots(self.inCmd)
            elif cmdType == g_CMDTYPE_MB_TELNET:
                self.outCmdHandler = htTelnet(self.inCmd)
            elif cmdType == g_CMDTYPE_DBG:
                self.outCmdHandler = htDebug(self.inCmd)
            elif cmdType == g_CMDTYPE_UTIL:
                self.outCmdHandler = htTestDefault(self.inCmd)
        else:
            self.outCmdHandler = htTestDefault(self.inCmd)

        return self.outCmdHandler

tstItem_name = None
arg_verbose = False
# Display final checked result?
arg_rstShown = True
# Forced to kill cardmgr?
arg_forced = False
arg_repeated = False
# Dump single test item?
arg_dump_single_dbg = False
arg_dump_single_detail =  False
# Run platform sw automation?
arg_plat_sw_automation = False
# Loop count of running platform sw automation repeatedly
arg_plat_sw_loop_count = 1

def parseCmdLine():
    global tstItem_name, arg_verbose, arg_rstShown, \
            arg_forced, arg_repeated, arg_dump_single_dbg, \
            arg_dump_single_detail,arg_plat_sw_automation, \
            arg_plat_sw_loop_count
    try:
        opts, args = getopt.getopt(sys.argv[1:],'t:vnfrdDAVhpl:')
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-t'):
            tstItem_name = arg.upper()
        elif opt in ('-v'):
            arg_verbose = True
        elif opt in ('-n'):
            arg_rstShown = False
        elif opt in ('-f'):
            arg_forced = True
        elif opt in ('-r'):
            arg_repeated = True
        elif opt in ('-d'):
            arg_dump_single_dbg = True
        # EX-25985
        elif opt in ('-D'):
            arg_dump_single_detail = True
        elif opt in ('-V'):
            show_version()
            sys.exit(0)
        # EX-25985
        elif opt in ('-A'):
            milog = miLog()
            milog.dumpAll()
            sys.exit(0)
        elif opt in ('-h'):
            usage()
            sys.exit(2)
        elif opt in ('-p'):
            arg_plat_sw_automation = True
        elif opt in ('-l'):
            arg_plat_sw_loop_count = eval(arg)
        else:
            sys.exit(2)

def runCmds():
    #1517 is VDSLR2 EqptType. This is demo. We should first get the EqptType from BID
    if tstItem_name is not None:
        if tstItem_name.upper() == "ALL":
            print g_ERR_TBD
            exit(0)

    cmdMapFile = None
    pCmdMapping = None
    boardInfo = getBidEx()
    if boardInfo is not None:
        if arg_plat_sw_automation:
            setPlatSwAutomation()

        cmdMapFile = getCmdMapFile(boardInfo['EqptType'])
        if cmdMapFile is not None:
            pCmdMapping = ET.parse(cmdMapFile)
            # ESA-760
            depth = 0
            while (depth < m_XINCLUDE_DEPTH):
                EI.include(pCmdMapping.getroot())
                depth += 1
            # debug
            #ET.dump(pCmdMapping.getroot())
        else:
            print g_ERR_CMD_MAPPING_FILE_NOT_FOUND
            exit(-1)
    else:
        print g_ERR_USE_DEFAULT_CMD_MAP
        cmdMapFile = getCmdMapFile('1517')
        if cmdMapFile is not None:
            pCmdMapping = ET.parse(cmdMapFile)
        else:
            print g_ERR_CMD_MAPPING_FILE_NOT_FOUND
            exit(-1)

    bTstItem = False
    for tstKey, tstVal in getTstItemMapping(boardInfo['EqptType']):
        testCmd = tstKey.upper()
        if testCmd == tstItem_name:
            bTstItem = True
            cmdParse    = None
            testCmd     = None
            childNotEmpty = False
            cmdMappingList=pCmdMapping.findall(tstVal)
            # ESA-760
            if not cmdMappingList:
                itemXPath = m_XPATH_PATTERN + tstVal
                cmdMappingList = pCmdMapping.findall(itemXPath)

            # ESAA-523
            milog = miLog()
            passCnt = 0
            failCnt = 0
            summaryMsg  = ""
            detailMsg   = ""
            debugMsg    = ""
            tstNameFmtStr = "\nTestName:[{}] \n".format(tstItem_name)
            tstNameEndFmtStr = "\nTestName:[/{}] \n".format(tstItem_name)
            summaryMsg  = tstNameFmtStr +  summaryMsg
            summaryMsg  = summaryMsg + g_HEADERFMTSTR
            startTime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(time.time()))
            tmpDebugStr     = ""
            tmpDetailStr    = ""

			
            if arg_dump_single_dbg:
                milog.dumpTest(tstItem_name)
                continue

            if arg_dump_single_detail:
                milog.dumpTest(tstItem_name,g_DUMP_DETAIL_STR)
                continue

            # ESA-1227
            debugMsg = tstNameFmtStr
            milog.prt_debug(debugMsg)				
            # ESA-747
            if not cmdMappingList:
                testResult = g_cmp_FAIL
                tmpDebugStr= g_ERR_ITEM_NOT_FOUND_F(cmdMapFile)
            else:
                # # ESA-1227
                detailMsg = tstNameFmtStr
                milog.prt_detail(detailMsg)
                # debugMsg = tstNameFmtStr
                # milog.prt_debug(debugMsg)

                testResult = g_cmp_PASS
                # ESA-1476. Only get the last item as the findall returns a list
                # containing all matching elements in *document* order.
                cmdMappingList = cmdMappingList[-1:]
                for cmdMappingElem in cmdMappingList:
                    for child in cmdMappingElem.getchildren():
                        #print child.attrib['name'],':',child.text.strip()
                        if cmdParse is None:
                            childNotEmpty = True
                            cmdParse = testCmdParse(child)
                        else:
                            cmdParse.add(child)

                        if cmdParse:
                            if cmdParse.ready():
                                testCmdHandler = cmdParse.getCmdHandler()
                                if testCmdHandler is not None:
                                    testCmdHandler.preProcess(verbose=arg_verbose, \
                                            rstshown=arg_rstShown, killcard=arg_forced,\
                                            repeated=arg_repeated)
                                    testCmdHandler.process()
                                    # ESAA-480
                                    tmpResult = testCmdHandler.postProcess()
                                    # ESA-1227
                                    #tmpDetailStr = testCmdHandler.getDetailMsg()
                                    # ESA-1283. Move log from the end to here since there
                                    # is one case of hybrid(e.g. SGMIIKA2CPU test which is
                                    # the combination of BCM and linux commands).

                                    # EX-25985 does the same as debug log(add ending label)
                                    # to get the detail information for the phyconn test
                                    # if this test pass.
                                    #tmpDetailStr = tmpDetailStr + tstNameEndFmtStr
                                    #milog.prt_detail(tmpDetailStr)

                                    if tmpResult == g_cmp_FAIL:
                                        testResult = g_cmp_FAIL
                                        # ESAA-523
                                        #if testCmdHandler.getDebugMsg() is not None:
                                         #   tmpDebugStr = tmpDebugStr + testCmdHandler.getDebugMsg()
                                        # EX-25985
                                        #tmpDebugStr = tmpDebugStr + tstNameEndFmtStr
                                        # ESA-1283 Put log there since there is one hybrid case.
                                        #milog.prt_debug(tmpDebugStr)

                                    cmdParse = None
                                else:
                                    print g_ERR_HANDLER_NOT_FOUND
                        else:
                            print g_ERR_TEST_CMD_EMPTY

                #The cmdParse should be None. If it's not, there is one possibility
                #that the value of next in last command of config xml file(config/xxx.xml)
                #is still yes. To cover this inadvertent incorrectness, add code below
                if cmdParse is not None:
                    #No ready() invoked. Forced to run the handler
                    testCmdHandler = cmdParse.getCmdHandler()
                    if testCmdHandler is not None:
                        testCmdHandler.preProcess(verbose=arg_verbose, \
                                rstshown=arg_rstShown, killcard=arg_forced,\
                                repeated=arg_repeated)
                        testCmdHandler.process()
                        # ESAA-480
                        tmpResult = testCmdHandler.postProcess()
                        #tmpDetailStr = testCmdHandler.getDetailMsg()
                        # ESA-1283

                        # EX-25985 does the same as debug log(add ending label)
                        #tmpDetailStr = tmpDetailStr + tstNameEndFmtStr
                        #milog.prt_detail(tmpDetailStr)

                        if tmpResult == g_cmp_FAIL:
                            testResult = g_cmp_FAIL
                            # ESAA-523
                            #tmpDebugStr = tmpDebugStr + testCmdHandler.getDebugMsg()
                            # EX-25985
                            #tmpDebugStr = tmpDebugStr + tstNameEndFmtStr
                            # ESA-1283
                            #milog.prt_debug(tmpDebugStr)

                        cmdParse = None
                    else:
                         print g_ERR_HANDLER_NOT_FOUND

                if childNotEmpty:            
                    tmpDetailStr = testCmdHandler.getDetailMsg()
                    # ESA-1283. Move log from the end to here since there
                    # is one case of hybrid(e.g. SGMIIKA2CPU test which is
                    # the combination of BCM and linux commands).

                    # EX-25985 does the same as debug log(add ending label)
                    # to get the detail information for the phyconn test
                    # if this test pass.
                    tmpDetailStr = tmpDetailStr + tstNameEndFmtStr
                    milog.prt_detail(tmpDetailStr)
                    if testResult == g_cmp_FAIL:
                        tmpDebugStr = tmpDebugStr + testCmdHandler.getDebugMsg()

            if testResult == g_cmp_FAIL:
                    
                        # ESAA-523
                        #if testCmdHandler.getDebugMsg() is not None:
                    #tmpDebugStr = tmpDebugStr + testCmdHandler.getDebugMsg()
                        # EX-25985
                tmpDebugStr = tmpDebugStr + tstNameEndFmtStr
                        # ESA-1283 Put log there since there is one hybrid case.
                milog.prt_debug(tmpDebugStr)            
            # ESAA-523
            endTime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(time.time()))
            if testResult == g_cmp_PASS:
                passCnt += 1
            else:
                failCnt += 1

            tmpStr = "| {:>4} | {:>4} | {} | {} |\n".format(str(passCnt),str(failCnt),startTime,endTime)
            summaryMsg = summaryMsg + tmpStr
            summaryMsg = summaryMsg + g_FOOTERFMRSTR
            milog.prt_summary(summaryMsg)

            # ESAA-480
            if arg_rstShown:
                print testResult

    if bTstItem == False:
        if tstItem_name is None:
            usage()
        else:
            print g_ERR_TEST_ITEM_NOT_FOUND

if __name__ == "__main__":
    parseCmdLine()
    while (arg_plat_sw_loop_count > 0):
        runCmds()
        arg_plat_sw_loop_count -= 1
