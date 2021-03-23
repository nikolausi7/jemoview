#!/usr/bin/python3
# -*- coding: utf-8 -*-
# aufruf: python3 jemoview.py oder python jemoview.py (je nachdem ob python V3 als python3 oder python installiert ist)
#
# jeti model viewer
global version
version = 'jemoview; version 2021-03-23'
#
# program extracts all relevant information from an input jeti transmitter file (.jsn)
# and prints it in a csv format using ';' as standard delimiter, suitable for excel/calc programs
#
# Copyright (c) 2020, werinza (nikolausi / Klaus)
# All Rights Reserved, Open Source MIT license applies to this program and related works
#

import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

global options
options = {'language' : 'de', 'csv' : 'model-folder'}

global aferatg_txt
aferatg_txt = ['Quer', 'Klappen', 'Höhe', 'Seite', 'Störkl.', 'Drossel', 'Fahrwerk',  
        'Ailerons', 'Flaps', 'Elevator', 'Rudder', 'Airbrake.', 'Throttle', 'Gear']

global fileout      # current output file is set in selectInput

# following globals are set in  extract()
global aferatgt     # list of servo count for main functions defined by aferatg_txt, plus tail features at end
global funktionen   # list of labels of used functions
global flightmolist # list of labels of used flight modes
global flightmoid   # list of id of used flight modes
global flightmoseq  # list of flight modes as displayed by transmitter
global luaid        # list of ids of lua apps
global sensorlist   # list of sensors and their measurements
global servolist    # list of labels of used servos
global stopwatch    # list of labels of used timers
global stopwatchid  # list of id of used timers


# --------------------------------     utility functions    --------------------------------------

# check if servo balancer used
def checkBala(aList):
# check all elements of list if value == 0
    status = 0
    for jj in range(len(aList)):
        if aList[jj] != 0:
            status = 1
    return getYesNo(status)


# evaluate curvetype
def getCurve(aInt):
    if options['language'] == 'de':
        curvetypes = ['Standard', 'konstant', 'x>0', 'x<0', '|x|', '+positiv', '-negativ',
            'symmetrisch', '3-Punkt', '5-Punkt', '7-Punkt', '9-Punkt', 'Gyro']
    else:
        curvetypes = ['Standard', 'Constant', 'x>0', 'x<0', '|x|', '+positive', '-negative',
            '±symmetric', '3-point', '5-point', '7-point', '9-point', 'Gyro']
    if aInt < len(curvetypes):
        return curvetypes[aInt]
    else:
        return zefix(1)
    
        
# getSwitch evaluates the internal switch representation which is a string made of 7 commas and 8 integers, example "12,0,0,1,1,-4000,-1,4"
# switch is on first or seventh position
def getSwitch(aString):
    # first position, but P3 and P4 are swapped due to a probable bug in transmitter, proportional and pyhysical switches
    switches1 = [
        'nix', 'P1', 'P2', 'P4', 'P3', 'P5', 'P6', 'P7', 'P8', 'SA', 'SB',
        'SC', 'SD', 'SE', 'SF', 'SG', 'SH', 'SI', 'SJ', 'SK', 'SL', 'P9',
        'P10', 'SM', 'SN', 'SO', 'SP'
    ]  
    # seventh position, values from  0 to 31, logical switches
    log = [
        'Log1', 'Log2', 'Log3', 'Log4', 'Log5', 'Log6', 'Log7', 'Log8', 'Log9',
        'Log10', 'Log11', 'Log12', 'Log13', 'Log14', 'Log15', 'Log16', 'Log17',
        'Log18', 'Log19', 'Log20', 'Log21', 'Log22', 'Log23', 'Log24', '?zefix?',
        '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?'
    ]
    # seventh position, values from  32 to 47, voice commands
    voi = [
        'V01', 'V02', 'V03', 'V04', 'V05', 'V06', 'V07', 'V08', 'V09', 'V10',
        'V11', 'V12', 'V13', 'V14', 'V15', '?zefix?'
    ]
    # seventh position, values from 48 to 63, telemetry controls
    mx = [
        'MX1', 'MX2', 'MX3', 'MX4', 'MX5', 'MX6', 'MX7', 'MX8', 'MX9', 'MX10',
        'MX11', 'MX12', 'MX13', 'MX14', 'MX15', 'MX16'
    ]
    # seventh position, values from 64 to 79, accelerometers, special treatment in getSwitch for 76 -79
    gx = [
        'GX', 'GY', 'GZ', 'G/L', 'G/R', 'GXL', 'GXR', 'GHi', '?zefix?', '?zefix?',
        '?zefix?', '?zefix?', 'timer', 'function', 'servo', 'flight mode'
    ]
    # seventh position, values from 80 to 89, sequencers
    seq = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8', 'Q9', 'Q10']
    # seventh position, values from 90 to 129, CH = channels of ppm inputs, Tr = digital trims, C0 = user apps
    sonst = [
        'CH1', 'CH2', 'CH3', 'CH4', 'CH5', 'CH6', 'CH7', 'CH8', '?zefix?', '?zefix?',
        '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', 'Tr1', 'Tr2', 'Tr3',
        'Tr4', 'Tr5', 'Tr6', '?zefix?', '?zefix?', '?zefix?', '?zefix?', 'C01', 'C02',
        'C03', 'C04', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?',
        'Log.MAX', '?zefix?', '?zefix?'
    ]
    switches7 = log + voi + mx + gx + seq + sonst

    # check if aString has exactly 7 commas und 8 integers
    xx = aString.split(',')  # is a list of strings
    if len(xx) != 8:
        return '-'
    for ii in xx:  # ii is a string
        if ii[0] in ('-', '+'):
            if not ii[1:].isdigit():
                return '-'
        elif not ii.isdigit():
            return '-'

    # switch number is at first or seventh position
    xx = aString.split(',')[0]
    switchNo1 = int(xx)
    yy = aString.split(',')[6]
    switchNo7 = int(yy)
    # if seventh position is between 76 and 79 then it takes precedence over first position
    if switchNo7 == 76:  # is a timer, transmitter displays T + number
        if stopwatch[switchNo1] == 'nix':
            return '??'
        jj = stopwatchid.index(switchNo1)
        if switchNo1 < 10:
            return 'T0' + str(jj) + '  (' + stopwatch[switchNo1] + ')'
        else:
            return 'T' + str(jj) + '  (' + stopwatch[switchNo1] + ')'
    if switchNo7 == 77:  # is a function, transmitter displays 3 chars if standard function, and U + number if user defined (function >= 14)
        if funktionen[switchNo1] == 'nix':
            return '??'
        if switchNo1 <= 13:
            return funktionen[switchNo1]
        else:
            return 'U' + str(switchNo1 - 13) + '  (' + funktionen[switchNo1]  + ')'
    if switchNo7 == 78:  # is a servo, transmitter displays O + number
        if servolist[switchNo1 +1] == 'nix':
            return '??'
        return 'O' + str(switchNo1 + 1) + '  (' + servolist[switchNo1 + 1]  + ')'
    if switchNo7 == 79:  # is a flight mode, transmitter displays FM + number
        if switchNo1 not in flightmoid:
            return '??'
        jj = flightmoid.index(switchNo1)
        kk = flightmoseq.index(switchNo1) + 1
        return 'FM' + str(kk) + '  (' + flightmolist[jj]  + ')'
    # if first position empty, take seventh position
    if switchNo1 == 0:  
        if switchNo7 >= 0:
            if switches7[switchNo7] == '?zefix?':
                return zefix(1)
            return switches7[switchNo7]
        else:
            return '-'
    else:  # otherwise return first position 'nix'
        return switches1[switchNo1]
    

# format integer als time string h:mm:ss
def getTime(aInt):
    timeT = aInt
    if timeT == 0:
        return '+0:00:00'
    if timeT < 0:
        timeout = '-'
        timeT *= -1
    else:
        timeout = '+'
    timeH = int(timeT / 3600)
    timeout = timeout + str(timeH) + ':'
    timeT = timeT % 3600
    timeM = int(timeT / 60)
    if timeM < 10:
        timeout = timeout + '0' + str(timeM) + ':'
    else:
        timeout = timeout + str(timeM) + ':'
    timeS = int(timeT % 60)
    if timeS < 10:
        timeout = timeout + '0' + str(timeS)
    else:
        timeout = timeout + str(timeS)
    return timeout


# getYesNo translates 0 into no and 1 into yes
def getYesNo(aInt):
    if aInt == 0:
        if options['language'] == 'de':
            return 'nein'
        else:
            return 'no'
    if aInt == 1:
        if options['language'] == 'de':
            return 'ja'
        else:
            return 'yes'
    else:
        return zefix(1)

    
# print a dictionary, fileout is current output file as set in selectInput
def printDict(aDict):
    for key in aDict:
        value = aDict[key]
        out = '\n' + str(key) + ';' + str(value) + ';'
        fileout.write(out)
        
        
# set decimal point, divide aValue by 10 for aInt times to get intended float value (internal values are int only)
def setDecPoint(aInt, aValue):
    while aInt > 0:
        aValue = float(aValue) / 10
        aInt -= 1
    return aValue

    
# write one of two strings using appropriate language, fileout is current output file as set in selectInput 
def writeLine(deStr, enStr):
    if options['language'] == 'de':
        fileout.write(deStr)
    else:
        fileout.write(enStr)
        
        
# write the essence of values (global or specific)
def writeEssence(labels, values):
    # check if all values are identical then print first line one as global, otherwise print all lines
    glob = True
    for ii in range(len(values)):
        if values[0] != values[ii]:
            glob = False
    if glob:
        fileout.write('\n' + 'Global')
        fileout.write(values[0])
    else:
        for ii in range(len(values)):
            fileout.write(labels[ii])
            fileout.write(values[ii])


# handle zefix marker
def zefix(aInt):
    global zefixmark  # needed to preserve value between calls
    if aInt == 0:
        zefixmark = 0
    if aInt == 1:
        zefixmark += 1
        return '?zefix?'
    if aInt == 2:
        return zefixmark


# following functions are called by extract()
# ----------------------------------  one function per dictionary at top level, sorted alphabetically     -----------------

def accel(modelData):
    writeLine('\n\nBewegunssensor', '\n\nAccelerometer')
    printDict(modelData['Accel'])


def alarms(modelData):
    writeLine('\n\nAlarme:', '\n\nAlarms:')
    out = '\nNummer;Sensor;Wert;X <= / >;Schwellwert;Audio;AktivierungSw;Wiederholen;Sprachausgabe;Aktiv'
    outEn = '\nNumber;Sensor;Value;X <= / >;Threshold;Audio;ActivationSw;Repeat;Ann cur val by voice;Enabled'
    writeLine(out, outEn)
    if options['language'] == 'de':
        rept = ['nein', 'ja', '3x']
    else:
        rept = ['no', 'yes', '3x']
    ind = 0
    for item in modelData['Alarms']['Data']:  # is list of dicts
        ind += 1
        activt = getYesNo(item['Active'])
        sw = getSwitch(item['Switch'])
        gt = '<='
        if item['Var-Greater'] == 1:
            gt = '>'
        audio = item['File']
        id = item['Sensor-ID']
        param = item['Sensor-Param']
        dec = item['Decimals']
        value = setDecPoint(dec, item['Value'])
        if item['Repeat'] < len(rept):
            rep = rept[item['Repeat']]
        else:
            rep = zefix(1)
        voi = getYesNo(item['Voice'])
        sensor = ''
        parm = ''
        if id in sensorlist:
            sensor = sensorlist[id][0]
            parm = sensorlist[id][param]
        if ind == 1:
            if options['language'] == 'de':
                sensor = 'Empfänger'
                parm = 'RX-Spannung'
            else:
                sensor = 'Receiver'
                parm = 'Voltage Rx'
        out = '\n' + str(ind) + ';' + sensor + ';' + parm + ';' + gt + ';' + str(value) + ';' + audio + ';' + sw + ';' + rep + ';' + voi + ';' + activt
        writeLine(out, out)


def audio(modelData):
    writeLine('\n\nAudio Player:', '\n\nAudio Player:')
    printDict(modelData['Audio'])


def commands(modelData):
    writeLine('\n\nSprachkommandos:', '\n\nVoice Commands :')
    printDict(modelData['Commands'])


def common(modelData):
    # model time and its reset mode will be evaluated by timers()
    
    # image and colors
    empty = True
    if 'Img' in modelData['Common']:
        txt = modelData['Common']['Img']
        if len(txt) > 0:
            if empty:
                writeLine('\n\nModellbild & Farbgebung', '\n\nModel Image & Colors')
                empty = False
            outDe = '\n' + 'Modellbild' + ';' + txt
            outEn = '\n' + 'Model image' + ';' + txt
            writeLine(outDe, outEn)
    if 'ImgBgPth' in modelData['Common']:
        txt = modelData['Common']['ImgBgPth']
        if len(txt) > 0:
            if empty:
                writeLine('\n\nModellbild & Farbgebung', '\n\nModel Image & Colors')
                empty = False
            outDe = '\n' + 'Hintergrundbild' + ';' + txt
            outEn = '\n' + 'Background image' + ';' + txt
            writeLine(outDe, outEn)
    
    writeLine('\n\nSpezielle Modelloptionen:', '\n\nOther Model Options:')
    switch = getSwitch(modelData['Common']['Autotrim-Switch'])
    if switch != '-':
        writeLine('\nAutotrimm-Schalter;' + switch, '\nAuto-Trim switch;' + switch)
    switch = getSwitch(modelData['Common']['Trainer-Switch'])
    if switch != '-':
        writeLine('\nTrainerschalter;' + switch, '\nTrainer switch;' + switch)
    switch = getSwitch(modelData['Common']['Logging-Switch'])
    if switch != '-':
        writeLine('\nStart-Logging Schalter;' + switch, '\nStart-Logging switch;' + switch)
    else:
        writeLine('\nStart-Logging Schalter;Auto', '\nStart-Logging switch;Auto')    
    switch = getSwitch(modelData['Common']['Throtle-Cut-Switch'])
    if switch != '-':
        writeLine('\nMotor-AUS Schalter;' + switch, '\nThrottle-Cut switch;' + switch)
    switch = getSwitch(modelData['Common']['Throtle-Idle-Switch'])
    if switch != '-':
        writeLine('\nLeerlaufschalter;' + switch, '\nThrottle-Idle switch;' + switch)
    
    # check if 24 channels used
    if '24ch' in modelData['Common']: 
        switch = getYesNo(modelData['Common']['24ch'])
        writeLine('\n\nDrahtlosmodus/Trainer:', '\n\nWireless Modes/Trainer:')
        writeLine('\n24-Kanal Multimode aktiv;' + switch, '\n24-Channels Multimode active;' + switch)
    
    switch = getSwitch(modelData['Common']['RC-Switch'][0])
    if switch != '-':
        writeLine('\n\nRC Schalter;' + switch, '\n\nRC-Switch;' + switch)
    
    writeLine('\n\nAufzeichnung Senderstatus:',  '\n\nLogging transmitter status info:')
    switch = getYesNo(modelData['Common']['Log-Alms'])
    writeLine('\nAufzeichnung Alarme;' + switch, '\nLog alarms;' + switch)
    outDe = '\nAufzeichnung Geber'
    outEn = '\nLog input controls'
    empty = True
    for item in modelData['Common']['Save-Ctrl']:
        geber = getSwitch(item)
        if geber != '-':
            outDe = outDe + ';' + geber
            outEn = outEn + ';' + geber
            empty = False
    if empty:
        outDe = outDe + ';keine'
        outEn = outEn + ';none'
    writeLine(outDe, outEn)
    
    empty = True
    switch = getSwitch(modelData['Common']['Mnu-lft'])
    if switch != '-':
        if empty:
            empty = False
            writeLine('\n\nHauptseite:', '\n\nMain Screen:')
        writeLine('\nWähle vorherige Seite;' + switch, '\nSwitch to previous page;' + switch)
    switch = getSwitch(modelData['Common']['Mnu-rgt'])
    if switch != '-':
        if empty:
            empty = False
            writeLine('\n\nHauptseite:', '\n\nMain Screen:')
        writeLine('\nWähle folgende Seite;' + switch, '\nSwitch to following page;' + switch)
        
    # FM-Annonc: Announce current flight mode, will be evaluated by flightmodes()
    # Marker-Switch and Telemetry-Voice-Switch probably old relics and never used


def controls(modelData):  # Sticks/Switches setup (Voreinstellungen)
    writeLine('\n\nSticks/Schalter Setup:', '\n\nSticks/Switches Setup:')
    # controls, P3 and P4 are swapped due to a probable bug in transmitter
    switches1 = [
        'nix', 'P1', 'P2', 'P4', 'P3', 'P5', 'P6', 'P7', 'P8', 'SA', 'SB',
        'SC', 'SD', 'SE', 'SF', 'SG', 'SH', 'SI', 'SJ', 'SK', 'SL', 'P9',
        'P10', 'SM', 'SN', 'SO', 'SP'
    ]  
    empty = True
    for item in modelData['Controls']['Data']:  # is liste of dicts
        ind = int(item['ID'])
        pos = int(item['Req-Pos'])
        if pos > 0:
            outDe = '\n' + switches1[ind] + ';hat Einschalt Stellung'
            outEn = '\n' + switches1[ind] + ';has start-up position'
            writeLine(outDe, outEn)
            empty = False
    if empty:
        writeLine('\nkeine Einschalt Stellungen', '\nno start-up positions')


def ctrlsound(modelData):
    if 'CtrlSound' not in modelData:  # transmitter version <3
        return
    writeLine('\n\nProportionalgeber;Ton', '\n\nProportional Controls;Sound')
    empty = True
    for item in modelData['CtrlSound']['Data']:  # ist liste von dicts
        sw = getSwitch(item[0])
        if sw != '-' and item[1] > 0:
            if item[1] == 1:
                tonDe = 'Mitte'
                tonEn = 'Center'
            else:
                tonDe = 'Sprache'
                tonEn = 'Voice'
            writeLine('\n' + sw + ';' + tonDe, '\n' + sw + ';' + tonEn)
            empty = False
    if empty:
        writeLine('\nkeine Töne', '\nno sounds')


def displayedtelemetry(modelData):
    if (options['language'] == 'de'and flightmolist[0] == 'Standard') or (options['language'] == 'en'and flightmolist[0] == 'Default'):
        writeLine('\n\nTelemetrieanzeige der; Flugphase; ' + flightmolist[0], '\n\nDisplayed-Telemetry of; Flight Mode; ' + flightmolist[0])
    else:
        writeLine('\n\nTelemetrieanzeige der; Standard Flugphase; ' + flightmolist[0], '\n\nDisplayed-Telemetry of; Default Flight Mode; ' + flightmolist[0])
    if len(modelData['Displayed-Telemetry']) == 0:
        writeLine('\nkeine Anzeige', '\nno display')
        return
    writeLine('\nNummer;Inhalt;Zoom', '\nNumber;Content;Double')
    systemDe = [
        '?zefix?', 'Flugphasen', 'Antenne', '?zefix?', 'RX-Spannung', 'Besitzer',
        '?zefix?', 'Jetibox', 'Trim', 'Tx Akku', 'Flugzeit', 'Antenne 900MHz', '?zefix?',
        'Modellbild', '?zefix?'
    ]
    systemEn = [
        '?zefix?', 'Flight Modes', 'Antenna', '?zefix?', 'Voltage RX', 'User Name',
        '?zefix?', 'Jetibox', 'Trim', 'Tx Battery', 'Model Time', 'Antenna 900MHz', '?zefix?',
        'Model Image', '?zefix?'
    ]
    ind = 0
    for item in modelData['Displayed-Telemetry']:  # ist liste von dicts
        if int(item['Flight-Mode']) > 0:
            return
        ind += 1
        typ = int(item['Item-Type'])
        if typ == 0:  # empty display
            zoom = getYesNo(item['DblSize'])
            outDe = str(ind) + ';' + 'leer' + ';' + zoom
            outEn = str(ind) + ';' + 'empty' + ';' + zoom
        elif typ == 1:  # timers
            id = int(item['ID'])
            zoom = getYesNo(item['DblSize'])
            outDe = str(ind) + ';' + stopwatch[id] + ';' + zoom
            outEn = outDe
        elif typ == 2:  # sensors
            id = int(item['ID'])
            if id in sensorlist:
                sensor = sensorlist[id][0]
                parm = int(item['Param'])
                wertDe = sensorlist[id][parm]
                wertEn = wertDe
            else:
                sensor = 'Sensor'
                wertDe = 'fehlt'
                wertEn = 'missing'
            zoom = getYesNo(item['DblSize'])
            outDe = str(ind) + ';' + sensor + ' / ' + wertDe + ';' + zoom
            outEn = str(ind) + ';' + sensor + ' / ' + wertEn + ';' + zoom
        elif typ == 3:  # system
            id = int(item['ID'])
            zoom = getYesNo(item['DblSize'])
            if id < len(systemDe):
                txtDe = systemDe[id]
                txtEn = systemEn[id]
                if txtDe == '?zefix?' or txtEn == '?zefix?':
                    zefix(1)
            else:
                txt = zefix(1)
            if id == 7:
                zoom = '-'
            outDe = str(ind) + ';' + txtDe + ';' + zoom
            outEn = str(ind) + ';' + txtEn + ';' + zoom
        elif typ == 4:  # Lua App
            id = int(item['ID'])
            if id in luaid:
                sensor = 'Lua App  ' + str(id)
            zoom = '-'
            outDe = str(ind) + ';' + sensor + ';' + zoom
            outEn = outDe
        writeLine('\n' + outDe, '\n' + outEn)


def eventsounds(modelData):
    writeLine('\n\nSprachausgabe/Ereignis:', '\n\nSounds on Event')
    if len(modelData['Event-Sounds']['Data']) == 0:
        writeLine('\nkein Ereignis', '\nno event')
        return
    writeLine('\nSchalter;Datei;Wiederholen', '\nSwitch;File;Repeat')
    for item in modelData['Event-Sounds']['Data']:  # is list of dicts
        sw = getSwitch(item['Switch'])
        audio = item['File']
        rep = getYesNo(item['Repeat'])
        out = '\n' + sw + ';' + audio + ';' + rep
        writeLine(out, out)


def flightmodes1(modelData):  # sets flightmolist[] flightmoid[] flightmoseq[]
    ind = -1
    for item in modelData['Flight-Modes']['Data']:  # is list of dicts
        ind += 1
        flightmolist[ind] = item['Label']
        flightmoid[ind] = item['ID']
    flightmolist[10] = ind  # save last index of flight modes (i.e. number of flight modes -1)
    if ind >= 1:
        for jj in range(1, ind + 1):
            flightmoseq[jj - 1] = flightmoid[jj]
    flightmoseq[ind] = flightmoid[0]
    

def flightmodes2(modelData):
    writeLine('\n\nFlugphasen: allgemeine Daten  ', '\n\nFlight Modes: general data  ' )
    switch = getSwitch(modelData['Common']['FM-Annonc'])
    if switch != '-':
        writeLine('\nAnsage der gewählten Flugphase;' + switch, '\nAnnounce current flight mode;' + switch)
    
    outDe = '\nNummer;Titel;Verzögerung;Schalter;Audio'
    outEn = '\nNumber;Label;Delay;Switch;Audio'
    trimseq = 4 * [0]
    item = modelData['Flight-Modes']['Data'][0]  # all flight modes have same digitrim funcids
    digitrim = item['DigiTrim']  # is list of dicts
    for ii in range(4):
        trimseq[ii] = digitrim[ii]['FuncID']
    trimseq.sort()
    for ii in range(4):
        if funktionen[trimseq[ii]] != 'nix':
            outDe = outDe + ';' + 'Trim ' + funktionen[trimseq[ii]]
            outEn = outEn + ';' + 'Trim ' + funktionen[trimseq[ii]]
    writeLine(outDe, outEn)
    for item in modelData['Flight-Modes']['Data']:  # is list of dicts
        trim = 4 * ['nix']
        id = int(item['ID'])
        seq = flightmoseq.index(id) + 1
        label = item['Label']
        aud = item['Audio']
        delay = setDecPoint(1, item['Delay'])
        delayout = str(delay) + 's'
        sw = getSwitch(item['Switch'])
        if sw == '-' and id == flightmoid[0]:
            swDe = 'ist Standard'
            swEn = 'is default'
        else:
            swDe = sw
            swEn = sw
        outDe = '\n' + str(seq) + ';' + label + ';' + delayout  + ';' + swDe + ';' + aud
        outEn = '\n' + str(seq) + ';' + label + ';' + delayout + ';' + swEn + ';' + aud
        digitrim = item['DigiTrim']  # is list of dicts
        for ii in range(4):
            funcid = digitrim[ii]['FuncID']
            jj = trimseq.index(funcid)
            if funktionen[funcid] != 'nix':
                trim[jj] = str(digitrim[ii]['Value'])
            else:
                trim[jj] = 'nix'
        for ii in range(4):
            if trim[ii] != 'nix':
                outDe = outDe + ';' + trim[ii]
                outEn = outEn + ';' + trim[ii]
        writeLine(outDe, outEn)

    # Vtail-Delta-Ailvator
    if aferatgt[8] != '':
        writeLine('\n\nFlugphasen: ' + aferatgt[8], '\n\nFlight Modes: ' + aferatgt[8])
        if aferatgt[8] == 'V-Leitwerksmischer' or aferatgt[8] == 'V-Tail Mix':
            writeLine('\nFlugphase;Höhe S1 / S2;Seite S1 / S2', '\nFlight Mode;Elevator S1 / S2;Rudder S1 / S2')
        else:
            writeLine('\nFlugphase;Höhe S1 / S2;Quer S1 / S2', '\nFlight Mode;Elevator S1 / S2;Ailerons S1 / S2')
        out_buf_l = []
        out_buf_w = []
        for item in modelData['Flight-Modes']['Data']:  # ist liste von dicts
            label = item['Label']
            w1 = str(item['VTail-Delta-Ailv'][0])
            w2 = str(item['VTail-Delta-Ailv'][1])
            w5 = str(item['VTail-Delta-Ailv'][4])
            w6 = str(item['VTail-Delta-Ailv'][5])
            outl = '\n' + label
            outw = ';' + w1 + ' / ' + w2 + ';' + w5 + ' / ' + w6
            out_buf_l.append(outl)
            out_buf_w.append(outw)
        writeEssence(out_buf_l, out_buf_w)

    # Aileron Differential
    if aferatgt[0] < 2:
        return
    writeLine('\n\nQuerruderdifferenzierung', '\n\nAileron Differential')
    if aferatgt[0] == 2:
        writeLine('\nFlugphase;Geber;Wirkung;Pos S1 / S2;Neg S1 / S2', '\nFlight Mode;Control;Adjust;Up S1 / S2;Down S1 / S2')
    if aferatgt[0] == 4:
        writeLine('\nFlugphase;Geber;Wirkung;Pos S1 / S2 / S3 / S4;Neg S1 / S2 / S3 / S4', 
            '\nFlight Mode;Control;Adjust;Up S1 / S2 / S3 / S4;Down S1 / S2 / S3 / S4')
    out_buf_l = []
    out_buf_w = []
    for item in modelData['Flight-Modes']['Data']:  # ist liste von dicts
        label = item['Label']
        qd_sw = getSwitch(item['ADiffSwitch'])
        wirk = str(item['ADiffVal'])
        qd_neg_s1 = str(item['ADiffPos'][0])
        qd_neg_s2 = str(item['ADiffPos'][1])
        qd_neg_s3 = str(item['ADiffPos'][2])
        qd_neg_s4 = str(item['ADiffPos'][3])
        qd_pos_s1 = str(item['ADiffNeg'][0])
        qd_pos_s2 = str(item['ADiffNeg'][1])
        qd_pos_s3 = str(item['ADiffNeg'][2])
        qd_pos_s4 = str(item['ADiffNeg'][3])
        outl = '\n' + label
        outw = ';' + qd_sw + ';' + wirk + ';' + qd_neg_s1 + ' / ' + qd_neg_s2 + ';' + qd_pos_s1 + ' / ' + qd_pos_s2
        if aferatgt[0] == 4:
            outw = ';' + qd_sw + ';' + wirk + ';' + qd_neg_s1 + ' / ' + qd_neg_s2 + ' / ' + qd_neg_s3 + ' / ' + qd_neg_s4 + ';' + qd_pos_s1 + ' / ' + qd_pos_s2 + ' / ' + qd_pos_s3 + ' / ' + qd_pos_s4
        out_buf_l.append(outl)
        out_buf_w.append(outw)
    writeEssence(out_buf_l, out_buf_w)

    # Butterfly/Flaps
    writeLine('\n\nButterfly', '\n\nButterfly/Flaps')
    if options['language'] == 'de':
        out_title = '\nFlugphase;Geber;Offset'
        if aferatgt[0] == 2:
            out_title = out_title + ';' + 'Quer S1 / S2' + ';' + 'Dif. Einst. S1 / S2'
        if aferatgt[0] == 4:
            out_title = out_title + ';' + 'Quer S1 / S2 / S3 / S4' + ';' + 'Dif Einst. S1 / S2 / S3 / S4'
        if aferatgt[1] == 2:
            out_title = out_title + ';' + 'Klappen S1 / S2'
        if aferatgt[1] == 4:
            out_title = out_title + ';' + 'Klappen S1 / S2 / S3 / S4'
        if aferatgt[2] == 1:
            out_title = out_title + ';' + 'Höhe S1'
        if aferatgt[2] == 2:
            out_title = out_title + ';' + 'Höhe S1 / S2'
        out_title = out_title + ';' + 'Höhe Kurve' + ';' + 'Fein. Geber' + ';' + 'Dif. Einst.' + ';' + 'Quer' + ';' + 'Klappen' + ';' + 'Höhe'
    else:
        out_title = '\nFlight Mode;Control;Offset'
        if aferatgt[0] == 2:
            out_title = out_title + ';' + 'Ailerons S1 / S2' + ';' + 'Dif. adjust S1 / S2'
        if aferatgt[0] == 4:
            out_title = out_title + ';' + 'Ailerons S1 / S2 / S3 / S4' + ';' + 'Dif. adjust S1 / S2 / S3 / S4'
        if aferatgt[1] == 2:
            out_title = out_title + ';' + 'Flaps S1 / S2'
        if aferatgt[1] == 4:
            out_title = out_title + ';' + 'Flaps S1 / S2 / S3 / S4'
        if aferatgt[2] == 1:
            out_title = out_title + ';' + 'Elevator S1'
        if aferatgt[2] == 2:
            out_title = out_title + ';' + 'Elevator S1 / S2'
        out_title = out_title + ';' + 'Elevator Curve' + ';' + 'Tuning Control' + ';' + 'Dif. Adjust' + ';' + 'Ailerons' + ';' + 'Flaps' + ';' + 'Elevator'
    writeLine(out_title, out_title)
    # Ailerons max 4 values, Dif max 4 values, Flaps max 4 values, Elevator max 2 values, Curve yes if not Standard
    out_buf_l = []
    out_buf_w = []
    for item in modelData['Flight-Modes']['Data']:  # ist liste von dicts
        label = item['Label']
        but_sw = getSwitch(item['BrakeSw'])
        offset = str(item['BkOffset'])
        but_qr_s1 = str(item['BrakeMix'][0])
        but_qr_s2 = str(item['BrakeMix'][1])
        but_qr_s3 = str(item['BrakeMix'][2])
        but_qr_s4 = str(item['BrakeMix'][3])
        but_wk_s1 = str(item['BrakeMix'][4])
        but_wk_s2 = str(item['BrakeMix'][5])
        but_wk_s3 = str(item['BrakeMix'][6])
        but_wk_s4 = str(item['BrakeMix'][7])
        but_hr_s1 = str(item['BrakeMix'][8])
        but_hr_s2 = str(item['BrakeMix'][9])
        but_qr_d1 = str(item['BrakeDiff'][0])
        but_qr_d2 = str(item['BrakeDiff'][1])
        but_qr_d3 = str(item['BrakeDiff'][2])
        but_qr_d4 = str(item['BrakeDiff'][3])
        curve = getCurve(item['BrakeElevCurve']['Curve-Type'])
        but_tun_sw = getSwitch(item['BkAdjustSwitch'])
        but_tun_dif = str(item['BrakeAdjust'][3])
        but_tun_qr = str(item['BrakeAdjust'][0])
        but_tun_wk = str(item['BrakeAdjust'][1])
        but_tun_hr = str(item['BrakeAdjust'][2])
        outl = '\n' + label
        outw = ';' + but_sw + ';' + offset
        if aferatgt[0] == 2:
            outw = outw + ';' + but_qr_s1 + ' / ' + but_qr_s2 + ';' + but_qr_d1 + ' / ' + but_qr_d2
        if aferatgt[0] == 4:
            outw = outw + ';' + but_qr_s1 + ' / ' + but_qr_s2 + ' / ' + but_qr_s3 + ' / ' + but_qr_s4 + ';' + but_qr_d1 + ' / ' + but_qr_d2 + ' / ' + but_qr_d3 + ' / ' + but_qr_d4
        if aferatgt[1] == 2:
            outw = outw + ';' + but_wk_s1 + ' / ' + but_wk_s2
        if aferatgt[1] == 4:
            outw = outw + ';' + but_wk_s1 + ' / ' + but_wk_s2 + ' / ' + but_wk_s3 + ' / ' + but_wk_s4
        if aferatgt[2] == 1:
            outw = outw + ';' + but_hr_s1
        if aferatgt[2] == 2:
            outw = outw + ';' + but_hr_s1 + ' / ' + but_hr_s1
        outw = outw + ';' + curve + ';' + but_tun_sw + ';' + but_tun_dif + ';' + but_tun_qr + ';' + but_tun_wk + ';' + but_tun_hr
        out_buf_l.append(outl)
        out_buf_w.append(outw)
    writeEssence(out_buf_l, out_buf_w)


def functions1(modelData): # set funktionen[]
    for item in modelData['Functions']['Data']:  # is list of dicts
        id = item['ID']
        funktionen[id] = item['Label']


def functions2(modelData):
    writeLine('\n\nFunktions+Geberzuordnung:', '\n\nFunctions Assignment:')
    writeLine('\nNummer;Funktion;Geber;Trim;Trim max', '\nNumber;Function;Control;Trim;Trim max')
    for item in modelData['Functions']['Data']:  # is list of dicts
        id = item['ID']
        label = item['Label']
        control = getSwitch(item['Control'])
        trimcontrol = getSwitch(item['Trim-Control'])
        trimmax = item['Trim-Max']
        out = str(id) + ';' + label + ';' + control
        if trimcontrol != '-':
            out = out + ';' + trimcontrol + ';' + str(trimmax)
        writeLine('\n' + out, '\n' + out)


def functionspecs(modelData):
    # collect headings at Flight-Mode 0
    if options['language'] == 'de':
        out_title_trim = 'Flugphase'
        out_title_dr = 'Flugphase'
        out_title_expo = 'Flugphase'
        out_title_sw = 'Flugphase'
        out_title_curve = 'Flugphase'
        for item in modelData['Function-Specs']:  # is list of dicts
            flm = int(item['Flight-Mode'])
            if flm == 0:
                flmt = flightmolist[flm]
                fun = int(item['Function-Id'])
                funt = funktionen[fun]
                out_title_trim = out_title_trim + ';' + funt + ' Trim'
                out_title_dr = out_title_dr + ';' + funt + ' DR'
                out_title_expo = out_title_expo + ';' + funt + ' Expo'
                out_title_sw = out_title_sw + ';' + funt + ' Schalter'
                out_title_curve = out_title_curve + ';' + funt + ' Kurve'
            else:
                break
    else:
        out_title_trim = 'Flight Mode'
        out_title_dr = 'Flight Mode'
        out_title_expo = 'Flight Mode'
        out_title_sw = 'Flight Mode'
        out_title_curve = 'Flight Mode'
        for item in modelData['Function-Specs']:  # is list of dicts
            flm = int(item['Flight-Mode'])
            if flm == 0:
                flmt = flightmolist[flm]
                fun = int(item['Function-Id'])
                funt = funktionen[fun]
                out_title_trim = out_title_trim + ';' + funt + ' Trim'
                out_title_dr = out_title_dr + ';' + funt + ' DR'
                out_title_expo = out_title_expo + ';' + funt + ' Expo'
                out_title_sw = out_title_sw + ';' + funt + ' Switch'
                out_title_curve = out_title_curve + ';' + funt + ' Curve'
            else:
                break
            
    # collect data
    out_buf_l = []
    out_trim_w = []
    out_trim = ''
    out_dr_w = []
    out_dr = ''
    out_expo_w = []
    out_expo = ''
    out_drsw_w = []
    out_drsw = ''
    out_curve_w = []
    out_curve = ''
    no_sw = True
    flmold = -1
    # store data
    for item in modelData['Function-Specs']:  # ist liste von dicts
        flm = int(item['Flight-Mode'])
        flmt = flightmolist[flm]
        fun = int(item['Function-Id'])
        funt = funktionen[fun]
        trim1 = item['Ph-Trim'][0]
        trim2 = item['Ph-Trim'][1]
        trim3 = item['Ph-Trim'][2]
        trim4 = item['Ph-Trim'][3]
        drneg = item['DR-Neg'][0]
        drpos = item['DR-Pos'][0]
        sw = getSwitch(item['DR-Switch'])
        if sw != '-':
            no_sw = False
        exneg = item['Expo-Neg'][0]
        expos = item['Expo-Pos'][0]
        curve = getCurve(item['Curve-Type'])
        if flm == flmold:  # continue with same flight mode and append data
            hit = False
            for txt in aferatg_txt:
                if funt == txt:
                    hit = True
                    ii = aferatg_txt.index(funt) % 7
                    out_trim = out_trim + ';' + str(trim1)
                    if aferatgt[ii] == 2:
                        out_trim = out_trim + ' / ' + str(trim2)
                    if aferatgt[ii] == 3:
                        out_trim = out_trim + ' / ' + str(trim2) + ' / ' + str(trim3)
                    if aferatgt[ii] == 4:
                        out_trim = out_trim + ' / ' + str(trim2) + ' / ' + str(trim3) + ' / ' + str(trim4)
            if hit == False:
                out_trim = out_trim + ';' + str(trim1)
            out_dr = out_dr + ';' + str(drneg) + ' / ' + str(drpos)
            out_expo = out_expo + ';' + str(exneg) + ' / ' + str(expos)
            out_drsw = out_drsw + ';' + sw
            out_curve = out_curve + ';' + curve
        else:  # next flight mode with first function
            if flmold != -1:
                out_trim_w.append(out_trim)
                out_dr_w.append(out_dr)
                out_expo_w.append(out_expo)
                out_drsw_w.append(out_drsw)
                out_curve_w.append(out_curve)
            flmold = flm
            out_buf_l.append('\n' + flmt)
            hit = False
            for txt in aferatg_txt:
                if funt == txt:
                    hit = True
                    ii = aferatg_txt.index(funt) % 7
                    out_trim = ';' + str(trim1)
                    if aferatgt[ii] == 2:
                        out_trim = out_trim + ' / ' + str(trim2)
                    if aferatgt[ii] == 3:
                        out_trim = out_trim + ' / ' + str(trim2) + ' / ' + str(trim3)
                    if aferatgt[ii] == 4:
                        out_trim = out_trim + ' / ' + str(trim2) + ' / ' + str(trim3) + ' / ' + str(trim4)
            if hit == False:
                out_trim = ';' + str(trim1)
            out_dr = ';' + str(drneg) + ' / ' + str(drpos)
            out_expo = ';' + str(exneg) + ' / ' + str(expos)
            out_drsw = ';' + sw
            out_curve = ';' + curve
    out_trim_w.append(out_trim)
    out_dr_w.append(out_dr)
    out_expo_w.append(out_expo)
    out_drsw_w.append(out_drsw)
    out_curve_w.append(out_curve)

    # write data
    writeLine('\n\nFlugphasentrimmung;(Servos)', '\n\nFlight Mode Trim;(Servos)')
    writeLine('\n' + out_title_trim, '\n' + out_title_trim)
    writeEssence(out_buf_l, out_trim_w)
    writeLine('\n\nDual Rate                   ;   Werte für;   Position 1',
        '\n\nDual Rate                   ;   values of;   Position 1')
    writeLine('\n' + out_title_dr, '\n' + out_title_dr)
    writeEssence(out_buf_l, out_dr_w)
    writeLine('\n\nDual Rate Schalter', '\n\nDual Rate switches')
    if no_sw:
        writeLine('\nkeine Schalter', '\nno switches')
    else:
        writeLine('\n' + out_title_sw, '\n' + out_title_sw)
        writeEssence(out_buf_l, out_drsw_w)
    writeLine('\n\nExponential', '\n\nExponential')
    writeLine('\n' + out_title_expo, '\n' + out_title_expo)
    writeEssence(out_buf_l, out_expo_w)
    writeLine('\n\nFunktionskurven', '\n\nFunction Curves')
    writeLine('\n' + out_title_curve, '\n' + out_title_curve)
    writeEssence(out_buf_l, out_curve_w)


def globalstr(modelData):
    writeLine('\n\nGlobale Einstellungen:', '\n\nGlobal Settings:')
    txTyp = {
        652: 'DC-16V2',
        653: 'DS-16V2',
        674: 'DC-16',
        675: 'DS-16',
        676: 'DS-14',
        677: 'DC-14',
        678: 'DC-24',
        679: 'DS-24',
        680: 'DS-12'
    }
    TxVers = False
    for item in modelData['Global']:
        if item == 'Version':
            value = int(modelData['Global'][item])
            if value == 1:  # transmitter version <5, no type
                continue
            if value in txTyp:
                outDe = '\nSender Typ' + ';' + txTyp[value]
                outEn = '\nTransmitter type' + ';' + txTyp[value]
            else:
                outDe = '\nSender Typ' + ';' + '?zefix?'
                outEn = '\nTransmitter type' + ';' + '?zefix?'
                zefix(1)
            writeLine(outDe, outEn)
            continue
        if item == 'TxVers':
            TxVers = True
            txt = modelData['Global'][item]
            outDe = '\nSender Version' + ';' + txt
            outEn = '\nTransmitter version'  + ';' + txt
            writeLine(outDe, outEn)
            continue
        if item == 'Filename':
            txt = modelData['Global'][item]
            outDe = '\nDateiname' + ';' + txt
            outEn = '\nFilename' + ';' + txt
            writeLine(outDe, outEn)
            continue
        if item == 'Model-Type':
            typDe = ['Flugzeug', 'Heli', 'Truck/Boat', 'X-Copter']
            typEn = ['Aero', 'Heli', 'General', 'X-Copter']
            ind = int(modelData['Global'][item]) - 1
            if ind < len(typDe):
                outDe = '\nModelltyp' + ';' + typDe[ind]
                outEn = '\nModel type' + ';' + typEn[ind]
            else:
                outDe = '\nModelltyp' + ';' + '?zefix?'
                outEn = '\nModel type' + ';' + '?zefix?'
                zefix(1)
            writeLine(outDe, outEn)
            continue
        if item == 'Receiver-ID1' or item == 'Receiver-ID2':
            if options['language'] == 'de':
                itemt = item.replace('Receiver', 'Empfänger')
            else:
                itemt = item 
            value = int(modelData['Global'][item])
            if value > 0:
                z2 = int(value / 65536)
                z1 = value - z2 * 65536
                out = itemt + ';' + str(z1) + ':' + str(z2)
            else:
                out = itemt + ';' + '-'
            writeLine('\n' + out, '\n' + out)
            continue
        if item == 'Name' or item == 'Desc':
            txt = modelData['Global'][item]
            out = '\n' + item + ';' + txt
            writeLine(out, out)
            continue
        if item == 'Rx-ID900':
            value = int(modelData['Global'][item])
            if value > 0:
                z2 = int(value / 65536)
                z1 = value - z2 * 65536
                out = item + ';' + str(z1) + ':' + str(z2)
            else:
                out = item + ';' + '-'
            writeLine('\n' + out, '\n' + out)
            continue
        if item == 'Rx-900Sw':
            value = str(modelData['Global'][item])
            sw = getSwitch(value)
            out = '\n' + item + ';' + sw
            writeLine(out, out)
            continue
        if item == 'Type':
            continue
        else:
            outDe = str(item) + ';' + str(modelData['Global'][item])
            outEn = str(item) + ';' + str(modelData['Global'][item])
        writeLine('\n' + outDe, '\n' + outEn)
    if not TxVers:
        writeLine('\nSender Version;< 3', '\nTransmitter Version;< 3')


def iqsdata(modelData):
    writeLine('\n\nIQSData:', '\n\nIQSData:')
    printDict(modelData['IQSData'])


def logswitch(modelData):
    writeLine('\n\nLogische Schalter:', '\n\nLogical Switches:')
    logtyp = ['...', 'AND', 'OR', 'Multi', 'XOR', 'A▲B▼', 'A>B', 'A<B', 'A=B']
    cond = ['x<', 'x>', 'Lin', '|x|<', '|x|>', '|x|=', 'x~']
    # search the last logical switch which is not equal to default
    last = len(modelData['LogSwitch']['Data'])
    empty = True
    for ii in range(last - 1, -1, -1):
        item = modelData['LogSwitch']['Data'][ii]
        enabled = item['Enabled']
        label = item['Label']
        sw1 = getSwitch(item['Switch1'])
        if item['Log-Type'] < len(logtyp):
            zutxt = logtyp[item['Log-Type']]
        else:
            zutxt = zefix(1)
        sw2 = getSwitch(item['Switch2'])
        if enabled != 0 or label != '' or sw1 != '-' or zutxt != '...' or sw2 != '-':
            empty = False
            last = ii
            break
    if empty:
        writeLine('\nkeine Schalter', '\nno switches')
        return
    writeLine('\nNummer;Titel;Aktiv;Geber1;Spezifkation1;Geber2;Spezifkation2;Zustand;Verzögerung', 
        '\nNumber;Label;Enabled;Control1;Specification1;Control2;Specification2;Condition;Delay')
    for item in modelData['LogSwitch']['Data']:  # ist liste von dicts
        ind = int(item['Index'])
        if ind > last:
            return
        enabled = getYesNo(item['Enabled'])
        label = item['Label']
        sw1 = getSwitch(item['Switch1'])
        cond1 = item['Cond1']
        if cond1 < len(cond):
            cond1txt = cond[cond1]
            if cond1 <= 1:
                if item['Value1'] == 0:
                    cond1txt = ''
        else:
            cond1txt = zefix(1)
        sw2 = getSwitch(item['Switch2'])
        cond2 = item['Cond2']
        if cond2 < len(cond):
            cond2txt = cond[cond2]
            if cond2 <= 1:
                if item['Value2'] == 0:
                    cond2txt = ''
        else:
            cond2txt = zefix(1)
        if item['Log-Type'] < len(logtyp):
            zutxt = logtyp[item['Log-Type']]
        else:
            zutxt = zefix(1)
        if 'Up-Type' in item:
            uptyp = '/'
            if item['Up-Type'] == 1:
                uptyp = '|'
            dntyp = '\\'
            if item['Dn-Type'] == 1:
                dntyp = '|'
            delaya = setDecPoint(1, int(item['Up-Time']))
            delayd = setDecPoint(1, int(item['Dn-Time']))
            delayout = ';' + uptyp + '  ' + str(delaya) + 's   ' + dntyp + '  ' + str(delayd) + 's'
        else:
            delayout = ';' + '/  0.0s   \  0.0s'
        out = '\nLog' + str(ind + 1) + ';' + label + ';' + enabled + ';' + sw1 + ';' + cond1txt + ';' + sw2 + ';' + cond2txt + ';' + zutxt + delayout
        writeLine(out, out)


def lua(modelData):
    writeLine('\n\nLua:', '\n\nLua:')
    if 'Lua' not in modelData:
        writeLine('\nkeine Lua App', '\nno Lua App')
        return
    anz = len(modelData['Lua'])
    if anz == 0:
        writeLine('\nkeine Lua App', '\nno Lua App')
        return
    ind = 1
    for item in modelData['Lua']:  # is list of dicts
        luaid[ind] = item['appID']
        out = '\n' + str(ind) + ';Lua App ID;' + str(luaid[ind])
        # assumption: luadata come in groups of 3 elements, first element is a string followed by 2 data elements
        # we display only those groups which contain a switch or a sensor and ignore all others
        luadata = item['data']
        counter = 0
        out3 = ''
        for dat in luadata:
            if len(out3) > 0:
                out = out + ';' + out2 + ';' + out3
            out3 = ''
            if counter % 3 == 0:
                out2 = str(dat)
            else:
                sw = getSwitch(str(dat))
                if sw != '-':
                    if len(out3) == 0:
                        out3 = sw
                    else:
                        out3 = out3 + ';' + sw
                if type(dat) == int:
                    if dat in sensorlist:
                        if len(out3) == 0:
                            out3 = sensorlist[dat][0]
                        else:
                            out3 = out3 + ';' + sensorlist[dat][0]
            counter += 1
        if len(out3) > 0:
            out = out + ';' + out2 + ';' + out3
        writeLine(out, out)
        ind += 1


def luactrl(modelData):
    writeLine('\n\nLua-Ctrl:', '\n\nLua-Ctrl:')
    printDict(modelData['Lua-Ctrl'])


def mixesmain(modelData):
    writeLine('\n\nFreie Mischer: Übersicht', '\n\nFree Mixes: Overview')
    if len(modelData['Mixes-Main']['Data']) == 0:
        writeLine('\nkeine Mischer', '\nno mixes')
        return
    writeLine('\nVon;Zu;Flugphasen;Asymetricher Gas Mischer', '\nFrom;To;Flight Mode;Throttle Asymmetric Mix')
    anz_mix = 0
    for item in modelData['Mixes-Main']['Data']:  # is list of lists
        anz_mix += 1
        von = funktionen[item[0]]
        auf = funktionen[item[1]]
        wirkDe = 'Flugphasen abhängig'
        wirkEn = 'Flight Mode dependent'
        if item[2] == 1:
            wirkDe = 'Global'
            wirkEn = 'Global'
        asymDe = 'nein'
        asymEn = 'no'
        if von == 'Drossel' or von == 'Throttle':
            asymDe = getYesNo(item[3])
            asymEn = getYesNo(item[3])
        outDe = '\n' + von + ';' + auf + ';' + wirkDe + ';' + asymDe
        outEn = '\n' + von + ';' + auf + ';' + wirkEn + ';' + asymEn
        writeLine(outDe, outEn)

    writeLine('\n\nFreie Mischer: Flugphasen;;;;;Verzögerung', '\n\nFree Mixes: Flight Modes;;;;;Delay')
    writeLine('\nMischer;Flugphase;Master-Wert;Schalter;Kurve;-Basis+       -Schalter+;Mix-Ausgabe +;Mix-Ausgabe -;nur vorwärts;Master Link;Slave Link;Trim;Slave Dual-Rate',
        '\nMix;Flight Mode;Master Value;Switch;Curve;-Source+    -Switch+;Mix Output +;Mix Output -;Single direction;Master Link;Slave Link;Trim;Slave Dual-Rate')
    if options['language'] == 'de':
        links = ['nein', '+  ja', '-  ja']
    else:
        links = ['no', '+  yes', '-  yes']
    for ii in range(anz_mix):
        for jj in range(flightmolist[10] + 1):
            item = modelData['Mixes-Main']['Data'][ii]
            if options['language'] == 'de':
                out = funktionen[item[0]] + ' zu ' + funktionen[item[1]]
            else:
                out = funktionen[item[0]] + ' to ' + funktionen[item[1]]
            kk = jj * anz_mix + ii
            dic = modelData['Mixes-Values'][kk]
            flugphase = flightmolist[int(dic['Flight-Mode'])]
            wert = dic['Intensity']
            sw = getSwitch(dic['Switch'])
            curve = getCurve(dic['Curve-Type'])
            delay1 = setDecPoint(1, int(dic['DelayN']))
            delay2 = setDecPoint(1, int(dic['DelayP']))
            delay3 = setDecPoint(1, int(dic['DelaySwN']))
            delay4 = setDecPoint(1, int(dic['DelaySwP']))
            delayout = str(delay1) + 's  ' + str(delay2) + 's   ' + str(delay3) + 's  ' + str(delay4) + 's'
            mp1 = str(dic['S-Output'][0])
            mp2 = str(dic['S-Output'][1])
            mp3 = str(dic['S-Output'][2])
            mp4 = str(dic['S-Output'][3])
            if 'S-OutputN' in dic:
                mn1 = str(dic['S-OutputN'][0])
                mn2 = str(dic['S-OutputN'][1])
                mn3 = str(dic['S-OutputN'][2])
                mn4 = str(dic['S-OutputN'][3])
            else:  # transmitter version <3
                mn1 = 0
                mn2 = 0
                mn3 = 0
                mn4 = 0
            mixpo = '-'
            mixno = '-'
            for txt in aferatg_txt:
                if funktionen[item[1]] == txt:
                    ll = aferatg_txt.index(txt) % 7
                    if aferatgt[ll] == 1:
                        mixpo = '-'
                        mixno = '-'
                    if aferatgt[ll] == 2:
                        mixpo = mp1 + ' / ' + mp2
                        mixno = mn1 + ' / ' + mn2
                    if aferatgt[ll] == 3:
                        mixpo = mp1 + ' / ' + mp2 + ' / ' + mp3
                        mixno = mn1 + ' / ' + mn2 + ' / ' + mn3
                    if aferatgt[ll] == 4:
                        mixpo = mp1 + ' / ' + mp2 + ' / ' + mp3 + ' / ' + mp4
                        mixno = mn1 + ' / ' + mn2 + ' / ' + mn3 + ' / ' + mn4
            vorw = getYesNo(dic['Direction'])
            if dic['M-Link'] < len(links):
                ml = links[dic['M-Link']]
            else:
                ml = zefix(1)
            if dic['S-Link'] < len(links):
                sl = links[dic['S-Link']]
            else:
                sl = zefix(1)
            trim = getYesNo(dic['M-Trim'])
            sdr = getYesNo(dic['S-DR'])
            if item[2] == 1:  # is global
                flugphase = 'Global'
            out = out + ';' + flugphase + ';' + str(wert) + ';' + sw + ';' + curve + ';' + delayout + ';' + mixpo + ';' + mixno + ';' + vorw + ';' + ml + ';' + sl + ';' + trim + ';' + sdr
            writeLine('\n' + out, '\n' + out)
            if item[2] == 1:  # is global
                break


def mixesvalues(modelData):
    writeLine('\n\nMixes-Values:', '\n\nMixes-Values:')
    for item in modelData['Mixes-Values']:  # is list of dicts
        printDict(item)


def sequence(modelData):
    writeLine('\n\nSequenzer:', '\n\nSequencer:')
    out_titleDe = '\nNummer;Titel;Schalter;Beeinflusst Kanal;Sequenzertyp;Zyklisch wiederholt;Sequenz immer beenden'
    out_titleEn = '\nNumber;Label;Switch;Overwrite channel;Type of path;Cycling;Always finish sequence'
    empty = True
    done = False
    for item in modelData['Sequence']:  # is list of dicts
        leer = True
        id = item['ID']
        sw = getSwitch(item['Switch'])
        label = item['Label']
        servo = item['Override']
        serout = servolist[servo]
        if serout == 'nix':
            serout = '-'
        if sw != '-' or label != '' or servo > 0:
            leer = False
        asymDe = 'symmetrisch'
        asymEn = 'symmetrical'
        if getYesNo(item['Asymm']) == 'ja' or getYesNo(item['Asymm']) == 'yes':
            asymDe = 'asymmetrisch'
            asymEn = 'asymmetrical'
        cyc = getYesNo(item['Cycle'])
        fin = getYesNo(item['Finish'])
        outDe = '\nQ' + str(id) + ';' + label + ';' + sw + ';' + serout + ';' + asymDe + ';' + cyc + ';' + fin
        outEn = '\nQ' + str(id) + ';' + label + ';' + sw + ';' + serout + ';' + asymEn + ';' + cyc + ';' + fin
        if not leer:
            if not done:
                writeLine(out_titleDe, out_titleEn)
                done = True
            writeLine(outDe, outEn)
            empty = False
    if empty:
        writeLine('\nkeine Sequenzer', '\nno sequencer')


def servos1(modelData): # set servolist[]
    # servo labels as defined by jeti, codes start at 257 (Querruder1/Aileron1)
    servoNamesDe = ['Querruder1', 'Querruder2', 'Querruder3', 'Querruder4', 'Klappe1',
        'Klappe2', 'Klappe3', 'Klappe4', 'Seite1', 'Seite2', 'Höhe1', 'Höhe2',
        '?zefix?', '?zefix?', 'Drossel1', 'Drossel2', 'Drossel3', 'Drossel4',
        'Fahrwerk1', 'Fahrwerk2', 'Fahrwerk3', 'Fahrwerk4', 'Störkl.1',
        'Störkl.2', 'Roll', 'Nick', 'Pitch', '?zefix?', 'Heck', '?zefix?',
        'Gyroempf.', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?',
        '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?',
        '?zefix?', 'Gyroempf.2', 'Gyroempf.3', 'Gimbal R', 'Gimbal P', 'Gimbal Y',
        'Mode', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?',
        '?zefix?', '?zefix?']
    servoNamesEn = ['Aileron1', 'Aileron2', 'Aileron3', 'Aileron4', 'Flap1',
        'Flap2', 'Flap3', 'Flap4', 'Rudder1', 'Rudder2', 'Elevator1', 'Elevator2',
        '?zefix?', '?zefix?', 'Throttle1', 'Throttle2', 'Throttle3', 'Throttle4',
        'Gear1', 'Gear2', 'Gear3', 'Gear4', 'Airbrake1',
        'Airbrake2', 'Roll', 'Elevator', 'Pitch', '?zefix?', 'Yaw', '?zefix?',
        'Gyro sens.', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?',
        '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?',
        '?zefix?', 'Gyro sens.2', 'Gyro sens.3', 'Gimbal R', 'Gimbal P', 'Gimbal Y',
        'Mode', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?', '?zefix?',
        '?zefix?', '?zefix?']

    if options['language'] == 'de':
        servoNames = servoNamesDe
    else:
        servoNames = servoNamesEn
    # servo codes between 288 and 304 are used for user defined names and stored in servoOther
    servoOther = 16 * ['nix']  # non-standard names
    # code does not work correctly if above assumptions are wrong (might happen if 24 non standard servos used)
    for item in modelData['Servos']['Data']:  # is list of dicts
        servo = int(item['Servo-Code'])
        if servo >= 288 and servo < 300:
            servoOther[servo - 288] = servo
    # assign non-standard functions to other servos,
    # first non-standard function at 14 corresponds to servo 288 (and servoOther[0]), 15 to 289 etc
    # last one assumed to be 29  (16 alltogether)
    ind = 13 # the magic 14 -1
    for ii in range(16):
        ind += 1
        if str(servoOther[ii]) != 'nix':
            if funktionen[ind] != 'nix':
                servoOther[ii] = funktionen[ind]
            else:
                servoOther[ii] = 'nix'
    # now detail all servos
    for item in modelData['Servos']['Data']:  # is list of dicts
        ind = int(item['Index']) + 1
        servo = int(item['Servo-Code'])
        # assign names
        if servo > 256:
            if servo <= 287:  # standard servos
                name = servoNames[servo - 257]
            elif servo >= 300:  # standard servos
                if servo - 257 < len(servoNames):
                    name = servoNames[servo - 257]
                else:
                    name = '?zefix?'
            else:  # other servos
                name = str(servoOther[servo - 288])
            servolist[ind] = name
            if name == '?zefix?':
                zefix(1)


def servos2(modelData):
    writeLine('\n\nServozuordnung:', '\n\nServo Assignment:')
    writeLine('\nSteckplatz;Servo;Mittenverstellung;Max. positiv;Max. negativ;Limit positiv;Limit negativ;Wegumkehr;Verzögerung pos/neg;Servobalancer',
        '\nSlot;Servo;Subtrim;Max positive;Max negative;Max positive limit;Max negative limit;Reverse;Delay positive/negative;Servo balancer')
    # now detail all servos
    for item in modelData['Servos']['Data']:  # is list of dicts
        ind = int(item['Index']) + 1
        name = servolist[ind]
        middle = item['Middle']
        maxp = item['Max-Positive']
        maxn = item['Max-Negative']
        maxpl = item['Max-Positive-Limit']
        maxnl = item['Max-Negative-Limit']
        reverse = ';' + getYesNo(item['Servo-Reverse'])
        delayp = setDecPoint(1, int(item['Delay-Positive']))
        delayn = setDecPoint(1, int(item['Delay-Negative']))
        delayout = ';' + str(delayp) + 's   ' + str(delayn) + 's'
        if 'Curve' in item:
            balancer = checkBala(item['Curve'])
        if name != 'nix':
            out = '\n' + str(ind) + ';' + name + ';' + str(middle) + ';' + str(maxp) + ';' + str(maxn) + ';' + str(maxpl) + ';' + str(maxnl) + reverse + delayout + ';' + balancer
            writeLine(out, out)

def snaprolls(modelData):
    if aferatgt[8] == 'V-Leitwerksmischer' or aferatgt[8] == 'V-Tail Mix' or aferatgt[8] == 'Delta/Elevon Mischer' or aferatgt[8] == 'Delta/Elevon Mix':
        return  # no snap roll if v-tail or delta
    writeLine('\n\nSnap Rolls:', '\n\nSnap Rolls:')
    out_titleDe = '\nFlugphase;Mode;Master Switch;Schalter Höhe/rechts;Schalter Tiefe/rechts;Schalter Höhe/links;Schalter Tiefe/links'
    out_titleEn = '\nFlight Mode;Mode;Master Switch;Sw up/right;Sw down/right;Sw up/left;Sw down/left'
    empty = True
    done = False
    for item in modelData['SnapRolls']:  # is list of dicts
        leer = True
        out = ''
        flm = int(item['Flight-Mode'])
        flmt = flightmolist[flm]
        mode = item['Mode']
        if mode == 0:
            modet = 'Master'
            sw = getSwitch(item['Master-Sw'])
            if sw != '-':
                leer = False
        else:
            modet = 'Single'
            sw = '-'
            leer = False
        out = flmt + ';' + str(modet) + ';' + sw
        for ii in range(4):
            swx = getSwitch(item['Switch'][ii])
            out = out + ';' + swx
        if not leer:
            if not done:
                writeLine(out_titleDe, out_titleEn)
                done = True
            writeLine('\n' + out, '\n' + out)
            empty = False
    if empty:
        writeLine('\nkeine Snap Rolls', '\nno snap rolls')


def telctrl(modelData):
    if 'Tel-Ctrl' not in modelData:  # transmitter version <3
        return
    writeLine('\n\nTelemetriegeber:', '\n\nTelemetry Controls:')
    # search the last telctrl which is not equal to default
    last = len(modelData['Tel-Ctrl']['Data'])
    empty = True
    for ii in range(last - 1, -1, -1):
        item = modelData['Tel-Ctrl']['Data'][ii]
        enabled = item['Enabled']
        label = item['Label']
        id = item['Sensor-ID']
        sw = getSwitch(item['Switch'])
        prop = item['Prop']
        if enabled != 0 or label != '' or id != 0 or sw != '-' or prop != 0:
            empty = False
            last = ii
            break
    if empty:
        writeLine('\nkeine Telemetriegeber', '\nno telemetry controls')
        return
    writeLine('\nNummer;Titel;Sensor;Messwert;Gebertyp;X < = > / Min;Schwellwert / Mitte;Toleranz / Max;Dauer / Glättung;Standardw %;Switch;Aktiv',
        '\nNumber;Label;Sensor;Measurement;Type of control;X < = > / Min;Decision level / Center;Hysteresis / Max;Duration / Filtering;Default %;Switch;Enabled')
    comp = ['<', '>', '=']
    for item in modelData['Tel-Ctrl']['Data']:  # is list of dicts
        ind = int(item['Index'])
        if ind > last:
            return
        enabled = getYesNo(int(item['Enabled']))
        label = item['Label']
        id = item['Sensor-ID']
        if id in sensorlist:
            sensor = sensorlist[id][0]
            wert = sensorlist[id][item['Param']]
            out = 'MX' + str(ind + 1) + ';' + label + ';' + sensor + ';' + wert
        else:
            out = 'MX' + str(ind + 1) + ';' + label + ';' + '-' + ';' + '-'
        if item['Prop'] == 0:
            out = out + ';Switch'
            dat = item['Bin-Data']  # is list
            dec = item['Decimals']
            w1 = comp[dat[0]]
            w2 = setDecPoint(dec, dat[2])
            w3 = setDecPoint(dec, dat[3])
            w4 = setDecPoint(1, dat[1])
            stand = item['Default']
            sw = getSwitch(item['Switch'])
            out = out + ';' + str(w1) + ';' + str(w2) + ';' + str(w3) + ';' + str(w4) + ';' + str(stand) + ';' + sw
        else:
            out = out + ';Proportional'
            dat = item['Prop-Data']  # is list
            dec = item['Decimals']
            w1 = setDecPoint(dec, dat[0])
            w2 = setDecPoint(dec, dat[1])
            w3 = setDecPoint(dec, dat[2])
            w4 = setDecPoint(0, dat[3])
            stand = item['Default']
            sw = getSwitch(item['Switch'])
            out = out + ';' + str(w1) + ';' + str(w2) + ';' + str(w3) + ';' + str(w4) + ';' + str(stand) + ';' + sw
        out = out + ';' + enabled
        writeLine('\n' + out, '\n' + out)


def telemdetect(modelData):
    writeLine('\n\nSensoren und Einstellungen:', '\n\nSensors & Variables:')
    out_titleDe = '\nSensor;Messwert;Wiederholen;Trigger;Wichtigkeit'
    out_titleEn = '\nSensor;Measurement;Repeat;Trigger;Priority'
    writeLine(out_titleDe, out_titleEn)
    prioDe = ['Niedrig', 'Mittel', 'Hoch']
    prioEn = ['Low', 'Medium', 'High']
    # first extract U-Rx, A1 and A2 from Voice
    voc = ['U-Rx', 'A1', 'A2']
    voctDe = ['Rx-Spannung', 'Antenne 1', 'Antenne 2']
    voctEn = ['Voltage Rx', 'Antenna 1', 'Antenna 2']
    for ii in range(3):
        rep = getYesNo(modelData['Voice'][voc[ii]][0])
        trig = getYesNo(modelData['Voice'][voc[ii]][1])
        priotDe = prioDe[modelData['Voice'][voc[ii]][2]]
        priotEn = prioEn[modelData['Voice'][voc[ii]][2]]
        outDe = '\nEmpfänger;' + voctDe[ii] + ';' + rep + ';' + trig + ';' + priotDe
        outEn = '\nReceiver;' + voctEn[ii] + ';' + rep + ';' + trig + ';' + priotEn
        writeLine(outDe, outEn)
    if len(modelData['Telem-Detect']['Data']) == 0:
        return
    id = ''
    device = 65 * ['nix']
    for item in modelData['Telem-Detect']['Data']:  # is list of dicts
        ind = int(item['Param'])
        if ind == 0:  # next device / sensor
            if id != '':
                sensorlist[id] = device  # store parameter of previous device
            id = item['ID']
            device = 65 * ['nix']
        device[ind] = item['Label']
        rep = getYesNo(item['Rep'])
        trig = getYesNo(item['Trig'])
        priotDe = prioDe[item['Prio']]
        priotEn = prioEn[item['Prio']]
        outDe = '\n' + str(device[0]) + ';' + str(device[ind]) + ';' + rep + ';' + trig + ';' + priotDe
        outEn = '\n' + str(device[0]) + ';' + str(device[ind]) + ';' + rep + ';' + trig + ';' + priotEn
        writeLine(outDe, outEn)
    sensorlist[id] = device  # store parameter of last device


def telemvoice(modelData):
    writeLine('\n\nEinzelsprachansagen:', '\n\nSingle voice announcements')
    if 'Telem-Voice' not in modelData:  # introduced in V4
        writeLine('\nkeine Sprachansagen', '\nno voice announcements')
        return
    if len(modelData['Telem-Voice']['Data']) == 0:
        writeLine('\nkeine Sprachansagen', '\nno voice announcements')
        return
    writeLine('\nSensor;Messwert;Schalter', '\nSensor;Measurement;Switch')
    for item in modelData['Telem-Voice']['Data']:  # is list of dicts
        key = item['ID']
        parm = int(item['Param'])
        sw = getSwitch(item['Sw'])
        if key in sensorlist:
            outDe = sensorlist[key][0] + ';' + sensorlist[key][parm] + ';' + sw
            outEn = sensorlist[key][0] + ';' + sensorlist[key][parm] + ';' + sw
        else:
            outDe = 'Sensor fehlt:;' + str(key) + ';' + sw
            outEn = 'Sensor missing:;' + str(key) + ';' + sw
        writeLine('\n' + outDe, '\n' + outEn)


def timers1(modelData): # fill stopwatch[]
    if len(modelData['Timers']['Data']) == 0:
        return
    jj = 0
    for item in modelData['Timers']['Data']:  # is list of dicts
        id = int(item['ID'])
        stopwatch[id] = item['Label']
        jj += 1
        stopwatchid[jj] = id
    

def timers2(modelData):
    writeLine('\n\nStoppuhren:', '\n\nTimers:')
    # first evaluate common data
    if 'Model-Time2' in modelData['Common']: # transmitter version >=3
        modeltime = getTime(modelData['Common']['Model-Time2']).strip('+')
        writeLine('\nFlugzeit;' + modeltime, '\nModel Time;' + modeltime)
        if options['language'] == 'de':
            reset = [ 'Kein', 'kurz', 'Alle']
        else:
            reset = [ 'None', 'Short reset', 'All']
        mode = modelData['Common']['Time-Reset']
        if mode < len(reset):
            resmod = reset[mode]
        else:
            resmod = zefix(1)
        writeLine('\nZurücksetzen-Timer; beim Start:;' + resmod, '\nTimers reset; at power up:;' + resmod)
    
    if len(modelData['Timers']['Data']) == 0:
        writeLine('\nkeine Stoppuhren', '\nno timers')
        return
    if options['language'] == 'de':
        timtyp = ['Standard', 'durchlaufend', 'Rundenzeit']
        reptyp = ['Kein', 'Beep 1', 'Beep 2', 'Sprache', 'Sprache (Pos.)']
    else:
        timtyp = ['Standard', 'Free-Running', 'Laps']
        reptyp = ['None', 'Beep 1', 'Beep 2', 'Voice', 'Voice (Up)']
    writeLine('\nStoppuhr Nummer;Name;Startwert;Zielwert;Timer-Typ;Signalisierung;Schalter;Resetschalter', 
        '\nTimer Number;Label;Initial value;Target value;Timer type;Report type;Switch;Reset switch')
    jj = 0
    for item in modelData['Timers']['Data']:  # is list of dicts
        jj += 1
        initial = int(item['Init-Time'])
        initialo = getTime(initial / 1000)
        target = int(item['Dest-Time'])
        targeto = getTime(target / 1000)
        typ = item['Tim-Type']
        if typ < len(timtyp):
            typo = timtyp[typ]
        else:
            typo = zefix(1)
        report = item['Report-Type']
        if report < len(reptyp):
            reporto = reptyp[report]
        else:
            reporto = zefix(1)
        sw = getSwitch(item['Switch'])
        if 'Sw-Rst' in item:
            reset = getSwitch(item['Sw-Rst'])
        else: # transmitter version <3
            reset = '-'
        out = '\n' + str(jj) + ';' + item['Label'] + ';' + initialo + ';' + targeto + ';' + typo + ';' + reporto + ';' + sw + ';' + reset
        writeLine(out, out)


def typespecific(modelData):
    writeLine('\n\nGrundeinstellungen:', '\n\nBasic Properties')
    if modelData['Type-Specific']['Model-Type'] != 'Aero':
        printDict(modelData['Type-Specific'])
        return
    
    if options['language'] == 'de':
        wing = ['1 Querruder', '2 Querruder', '2 QR | 1 WK', '2 QR | 2 WK', '4 QR | 2 WK', '2 QR | 4 WK', '4 QR | 4 WK']
    else:
        wing = ['0 Flaps | 1 Ail', '0 Flaps | 2 Ail', '1 Flap | 2 Ail', '2 Flaps | 2 Ail', '4 Flaps | 2 Ail', '2 Flaps | 4 Ail', '4 Flaps | 4 Ail']
    wing_qr = [1, 2, 2, 2, 4, 2, 4]
    wing_wk = [0, 0, 1, 2, 2, 4, 4]
    if options['language'] == 'de':
        tail = ['Kreuz- od T-LW: 1HR 1SR', 'V-LW 2 Servos', 'Ailvator 2HR 1SR', '2HR / 2SR', 'kein LW (Delta/Elevon)', 'Kein']
    else:
        tail = ['Normal   1H1V', 'V-Tail   2H', 'Ailvator 2H1V', 'Normal   2H2V', 'None - Elevon/Delta', 'None']
    tail_hr = [1, 2, 2, 2, 2, 0]
    tail_sr = [1, 2, 1, 2, 1, 0]
    for item in modelData['Type-Specific']:
        outDe = ''
        outEn = ''
        if item == 'Type' or item == 'Model-Type':
            continue
        if item == 'Wing-Type':
            ind = int(modelData['Type-Specific'][item])
            if ind < len(wing):
                outDe = 'Tragfläche' + ';' + wing[ind]
                outEn = 'Wing type' + ';' + wing[ind]
                aferatgt[0] = wing_qr[ind]
                aferatgt[1] = wing_wk[ind]
            else:
                outDe = 'Tragfläche' + ';' + '?zefix?'
                outEn = 'Wing type' + ';' + '?zefix?'
                zefix(1)
                aferatgt[0] = 0
                aferatgt[1] = 0
        if item == 'Tail-Type':
            ind = int(modelData['Type-Specific'][item])
            if ind < len(tail):
                outDe = 'Leitwerk' + ';' + tail[ind]
                outEn = 'Tail type' + ';' + tail[ind]
                aferatgt[2] = tail_hr[ind]
                aferatgt[3] = tail_sr[ind]
            else:
                outDe = 'Leitwerk' + ';' + '?zefix?'
                outEn = 'Tail type' + ';' + '?zefix?'
                zefix(1)
                aferatgt[2] = 0
                aferatgt[3] = 0
            if options['language'] == 'de':
                if ind == 1:
                    aferatgt[8] = 'V-Leitwerksmischer'
                if ind == 2:
                    aferatgt[8] = 'Ailevator'
                    if aferatgt[0] >= 2:
                        aferatgt[7] = 1
                if ind == 4:
                    aferatgt[8] = 'Delta/Elevon Mischer'
                    aferatgt[7] = 1
            else:
                if ind == 1:
                    aferatgt[8] = 'V-Tail Mix'
                if ind == 2:
                    aferatgt[8] = 'Ailevator'
                    if aferatgt[0] >= 2:
                        aferatgt[7] = 1
                if ind == 4:
                    aferatgt[8] = 'Delta/Elevon Mix'
                    aferatgt[7] = 1
        if item == 'Motor-Count':
            anz = int(modelData['Type-Specific'][item])
            outDe = 'Antrieb(e)' + ';' + str(anz)
            outEn = 'Engine count' + ';' + str(anz)
            aferatgt[5] = anz
        if item == 'Gear-Servos':
            anz = int(modelData['Type-Specific'][item])
            outDe = 'Fahrwerk-Servos' + ';' + str(anz)
            outEn = 'Gear servos' + ';' + str(anz)
            aferatgt[6] = anz
        if item == 'Airbrake-Servos':
            anz = int(modelData['Type-Specific'][item])
            outDe = 'Störklappenservos' + ';' + str(anz)
            outEn = 'Airbrake servos' + ';' + str(anz)
            aferatgt[4] = anz
        for ii in range(3):
            wertDe = 'nein'
            wertEn = 'no'
            txt = 'Gyro' + str(ii + 1)
            if item == txt:
                if int(modelData['Type-Specific'][item]) == 1:
                    wertDe = 'ja'
                    wertEn = 'yes'
                outDe = txt + ';' + wertDe
                outEn = txt + ';' + wertEn
        if len(outDe) > 0 or len(outEn) > 0:
            writeLine('\n' + outDe, '\n' + outEn)


def usermenu(modelData):
    writeLine('\n\nBenutzermenü:', '\n\nUser-Menu:')
    printDict(modelData['User-Menu'])


def vario(modelData):
    writeLine('\n\nVario:', '\n\nVario:')
    if 'Setting' not in modelData['Vario']:
        writeLine('\nDaten in veraltetem Format;Sender updaten', '\nDeprecated data format;update transmitter')
        return
    empty = True
    if options['language'] == 'de':
        modes = ['Aus', 'Alarm JB Profi', 'Wert EX', 'Lua']
    else:
        modes = ['Off', 'JB Profi Alarm', 'EX Value', 'Lua']
    mode = modelData['Vario']['Mode']
    if mode < len(modes):
        modet = modes[mode]
    else:
        modet = zefix(1)
    sw = getSwitch(modelData['Vario']['Switch'])
    setting = modelData['Vario']['Setting']  # is list of dicts
    for ii in range(len(modelData['Vario']['Setting'])):
        id = modelData['Vario']['Setting'][ii]['Sensor-ID']
        param = int(modelData['Vario']['Setting'][ii]['Sensor-Par'])
        dec = int(modelData['Vario']['Setting'][ii]['Decimals'])
        deadzpos = str(setDecPoint(dec, int(modelData['Vario']['Setting'][ii]['DeadZPos'])))
        deadzneg = str(setDecPoint(dec, int(modelData['Vario']['Setting'][ii]['DeadZNeg'])))
        minw = str(setDecPoint(dec, int(modelData['Vario']['Setting'][ii]['Min'])))
        center = str(setDecPoint(dec, int(modelData['Vario']['Setting'][ii]['Center'])))
        maxw = str(setDecPoint(dec, int(modelData['Vario']['Setting'][ii]['Max'])))
        enabled = getYesNo(modelData['Vario']['Setting'][ii]['En'])
        if id in sensorlist:
            sensor = sensorlist[id][0]
            parm = sensorlist[id][param]
            if empty:
                writeLine('\nMode;' + modet, '\nMode;' + modet)
                writeLine('\nSchalter;' + sw, '\nSwitch;' + sw)
                writeLine('\nSensor;Messwert;Totzone -;Totzone +;Weite -;Center;Weite +;Aktiv',
                    '\nSensor;Measurement;Dead Zone -;Dead Zone +;Range -;Center;Range +;Enabled')
                empty = False
            out = '\n' + sensor + ';' + parm + ';' + deadzneg + ';' + deadzpos + ';' + minw + ';' + center + ';' + maxw + ';' + enabled
            writeLine(out, out)
    if empty:
        writeLine('\nkein Vario', '\nno vario')


def voice(modelData):
    writeLine('\n\nSprachausgabe:', '\n\nVoice Output:')
    outDe = ''
    outEn = ''
    sw = getSwitch(modelData['Voice']['TimerSw'])
    if sw != '-':
        timer = modelData['Voice']['Timer-ID']
        outDe = '\nTimer;' + stopwatch[timer] + ';Switch;' + sw
        writeLine(outDe, outDe)
    writeLine('\nTelemetrie', '\nTelemetry')
    sw = getSwitch(modelData['Voice']['RepeatSw'])
    if sw != '-':
        time = modelData['Voice']['Timeout']
        outDe = '\nWiederh. nach;' + str(time) + 'sec;Switch;' + sw
        outEn = '\nRepeat every;' + str(time) + 'sec;Switch;' + sw
        writeLine(outDe, outEn)
    sw = getSwitch(modelData['Voice']['TrigSw'])
    if sw != '-':
        outDe = '\nTrigger Schalter;' + sw
        outEn = '\nTrigger Switch;' + sw
        writeLine(outDe, outEn)
    if outDe == '':
        writeLine('\nkeine Sprachausgabe', '\nno voice output')


def voicerec(modelData):
    writeLine('\n\nVoiceRec:', '\n\nVoiceRec:')
    printDict(modelData['VoiceRec'])


#--------------------------------    function to extract all dicts from model file    --------------------------------------
def extract(modelData):
    # these globals must be declared here again to avoid variable shadowing
    global aferatgt  # number of servos: aileron flaps elevator ruder airbrake throttle gear butterfly(1=needs butterfly) delta/v-lw
    global aferatg_txt
    global funktionen
    global flightmolist
    global flightmoid
    global flightmoseq
    global luaid
    global sensorlist
    global servolist
    global stopwatch
    global stopwatchid

    # set initial values for all global arrays
    aferatgt = [0, 0, 0, 0, 0, 0, 0, 0, '']
    funktionen = 51 * ['nix']
    flightmolist = 11 * ['nix']
    flightmoid = 11 * ['nix']
    flightmoseq = 11 * ['nix']
    luaid = 31 * [0]
    sensorlist = {}
    servolist = 25 * ['nix']
    stopwatch = 11 * ['nix']
    stopwatchid = 11 * ['nix']
    zefix(0)
        
    # evaluate all dicts of top level
    globalstr(modelData)
    typespecific(modelData)         # sets aferatgt[]
    functions1(modelData)           # sets funktionen[] 
    servos1(modelData)              # sets servolist[]
    flightmodes1(modelData)         # sets flightmolist[] flightmoid[] flightmoseq[]  and reads aferatgt[]
    timers1(modelData)              # sets stopwatch[] stopwatchid[] 
    common(modelData)               
    controls(modelData)
    ctrlsound(modelData)
    functions2(modelData)           
    servos2(modelData)              # reads funktionen[]
    flightmodes2(modelData)         # reads aferatgt[]
    functionspecs(modelData)        # reads funktionen[] flightmolist[] aferatgt[]
    mixesmain(modelData)            # reads funktionen[] flightmolist[] aferatgt[]
    snaprolls(modelData)            # reads flightmolist[] aferatgt[]
    sequence(modelData)             # reads servolist[]
    timers2(modelData)              
    logswitch(modelData)
    eventsounds(modelData)
    voice(modelData)                # reads stopwatch[]
    telemdetect(modelData)          # sets sensorlist[]
    telemvoice(modelData)           # sets sensorlist[]
    telctrl(modelData)              # sets sensorlist[]
    lua(modelData)                  # sets luaid[] and reads sensorlist[]
    displayedtelemetry(modelData)   # reads luaid[] sensorlist[] stopwatch[]
    vario(modelData)                # reads sensorlist[]
    alarms(modelData)               # reads sensorlist[]
    
    # currently not evaluated
    #mixesvalues(modelData)        # data processed by mixesmain()
    #luactrl(modelData)            # purpose unknown
    #iqsdata(modelData)            # purpose unknown
    #commands(modelData)           # purpose unknown
    #accel(modelData)              # accelerometer, unknown which values are default or modified
    #audio(modelData)              # dx-24 needed for testing
    #voicerec(modelData)           # dx-24 needed for testing
    #usermenu(modelData)           # low priority


#------------------------   function to select model files and then call extract function for each selected model  ----
def selectInput():
    # this global must be declared here again to avoid variable shadowing (because it is set)
    global fileout
    
    initdir = os.getcwd()
    if options['language'] == 'de':
        txt1 = 'eine oder mehrere jsn Modell Dateien auswählen'
        txt2 = 'jsn Dateien'
    else:
        txt1 = 'select one or more jsn model files'
        txt2 = 'jsn files'
    filelist = filedialog.askopenfiles(
        mode='r',
        title=txt1,
        initialdir=initdir,
        filetypes=[(txt2, ['.jsn'])],
        multiple=True)
    if not filelist:
        return None
    
    for item in filelist:
        fileName = item.name  # is a fully qualified name
        print('\ninput', fileName)
        # input encoding UTF-8 mandatory for portability and German umlaute äöü, is standard for python
        # non UTF-8 characters like hex B0 (used by SM sensors for centigrades)
        # will be replaced by character � (by errors='replace')
        try:
            with open(fileName, 'r', encoding='utf-8', errors='replace') as filein:
                try:
                    modelData = json.load(filein)  # resulting modelData is a dict
                except json.decoder.JSONDecodeError as e:
                    if options['language'] == 'de':
                        out = 'Datei ' + fileName + ' ist kein gültiges Modell\n' + str(e)
                    else:
                        out = 'file ' + fileName + ' is not a valid model\n' + str(e)
                    print(out)
                    tk.messagebox.showinfo(title='jemoview', message=out)
                    continue
        except OSError as e:
            if options['language'] == 'de':
                out = 'Datei ' + fileName, ' nicht lesbar\n' + str(e)
            else:
                out = 'file ' + fileName, ' not readable\n' + str(e)
            print(out)
            tk.messagebox.showinfo(title='jemoview', message=out)
            continue
        filein.close()
        if 'Global' not in modelData:
            if options['language'] == 'de':
                out = 'Datei ' + fileName + ' ist kein gültiges Modell\n'
            else:
                out = 'file ' + fileName + ' is not a valid model\n'
            print(out)
            tk.messagebox.showinfo(title='jemoview', message=out)
            continue

        # check where to store resulting csv files, default is same folder as model file
        filecsv = fileName.replace('.jsn', '.csv')
        if options['csv'] == 'subfolder':
            basNam = os.path.basename(filecsv)
            dirNam = os.path.dirname(filecsv)
            dirNamCsv = dirNam + os.path.sep + 'csv'
            filecsv = dirNamCsv + os.path.sep + basNam
            if not os.path.exists(dirNamCsv):
                try:
                    os.mkdir(dirNamCsv)
                except OSError as e:
                    if options['language'] == 'de':
                        out = 'konnte Unterordner csv nicht anlegen\n' + str(e)
                    else:
                        out = 'could not create subfolder csv\n' + str(e)
                    print(out)
                    tk.messagebox.showinfo(title='jemoview', message=out)
                    continue
                    
        # create output
        try:
            with open(filecsv, 'w', encoding='utf-8', errors='replace') as fileout:
                fileout.write(version)
                # extract content of model
                extract(modelData)
                fileout.write('\n') # last line
        except:
            if options['language'] == 'de':
                out = 'Fehler bei Modell\n' + fileName + '\nGrund: '
            else:
                out = 'error at model\n' + fileName + '\nreason: '
            out = out + str(sys.exc_info()[0]) + '\n' + str(sys.exc_info()[1])
            print(out)
            tk.messagebox.showinfo(title='jemoview', message=out)
            continue
        
        if zefix(2) > 0:
            if options['language'] == 'de':
                out = 'Datenlücke bei Modell\n' + fileName + '\nbitte Modell im jetiforum.de einstellen'
            else:
                out = 'Missing data for model\n' + fileName + '\nplease post model at jetiforum.de'
            print(out)
            tk.messagebox.showinfo(title='jemoview', message=out)
        print('output', filecsv)
        fileout.close()
    
    if options['language'] == 'de':
        out = 'bereit für weitere Modelle'
    else:
        out = 'ready for next models'
    tk.messagebox.showinfo(title='jemoview', message=out)
    return


#------------------------------- set options, called from main loop -------------------


def setLang(langOpt):
    options['language'] = langOpt
    if langOpt == 'de':
        labelCsv['text'] = 'wo sollen die csv Ergebnis Dateien gespeichert werden'
        buttonCsv1['text'] = '1) im selben Ordner \nwie Model Datei'
        buttonCsv2['text'] = '2) in Unterordner csv \nvon Model Datei Ordner'
        buttonEn['bg'] = app["bg"]
        buttonDe['bg'] = 'white'
    if langOpt == 'en':
        labelCsv['text'] = 'where to store the resulting csv files'
        buttonCsv1['text'] = '1) in same folder as model file'
        buttonCsv2['text'] = '2) in subfolder of model folder'
        buttonDe['bg'] = app['bg']
        buttonEn['bg'] = 'white'
    return


def setCsv(csvOpt):
    if csvOpt == 1:
        options['csv'] = 'model-folder'
        buttonCsv2['bg'] = app['bg']
        buttonCsv1['bg'] = 'white'
    else:
        options['csv'] = 'subfolder'
        buttonCsv1['bg'] = app['bg']
        buttonCsv2['bg'] = 'white'
    return


#------------------------------------     main   loop -------------------

app = tk.Tk()
app.title(version)

# Create a canvas
app.geometry('400x370+400+300')

frameLang = tk.Frame(master=app, relief=tk.RIDGE, borderwidth=5)
frameCsv = tk.Frame(master=app,
                    height=100,
                    width=100,
                    relief=tk.RIDGE,
                    borderwidth=5)
frameStart = tk.Frame(master=app,
                      height=100,
                      width=100,
                      relief=tk.RIDGE,
                      borderwidth=5)

# language option
buttonDe = tk.Button(master=frameLang,
                     text='Sprache Deutsch',
                     font=('Times', 12, 'bold'),
                     bg='white',
                     command=lambda: setLang('de'))
buttonDe.pack(side=tk.LEFT)
buttonEn = tk.Button(master=frameLang,
                     text='Language English',
                     font=('Times', 12, 'bold'),
                     relief=tk.FLAT,
                     command=lambda: setLang('en'))
buttonEn.pack(side=tk.RIGHT)

# csv option buttons
labelCsv = tk.Label(
    master=frameCsv,
    text='wo sollen die csv Ergebnis Dateien gespeichert werden',
    font=('Times', 12, 'bold'),
    padx=20)
labelCsv.pack()
buttonCsv1 = tk.Button(master=frameCsv,
                       text='1) im selben Ordner \nwie Model Datei',
                       font=('Times', 12, 'bold'),
                       bg='white',
                       width=40,
                       padx=5,
                       command=lambda: setCsv(1))
buttonCsv1.pack()
backgr = frameCsv["bg"]
buttonCsv2 = tk.Button(master=frameCsv,
                       text='2) in Unterordner csv \nvon Model Datei Ordner',
                       font=('Times', 12, 'bold'),
                       bg=backgr,
                       width=40,
                       padx=5,
                       command=lambda: setCsv(2))
buttonCsv2.pack()

# start button
tk.Button(master=frameStart,
          text='Start',
          font=('Times', 15, 'bold'),
          width=15,
          fg='blue',
          padx=20,
          pady=20,
          command=lambda: selectInput()).pack(side=tk.LEFT)
# exit button
tk.Button(master=frameStart,
          text='Exit',
          font=('Times', 15, 'bold'),
          width=15,
          fg='red',
          padx=20,
          pady=20,
          command=lambda: sys.exit()).pack(side=tk.RIGHT)

# pack frames
tk.Label(master=app,
         text=' ',
         font=('Times', 10, 'bold'),
         width=50,
         fg='black').pack()
frameLang.pack()
tk.Label(master=app,
         text=' ',
         font=('Times', 10, 'bold'),
         width=50,
         fg='black').pack()
frameCsv.pack()
tk.Label(master=app,
         text=' ',
         font=('Times', 10, 'bold'),
         width=50,
         fg='black').pack()
frameStart.pack()

app.mainloop()
