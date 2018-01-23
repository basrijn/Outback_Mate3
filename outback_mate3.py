#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
from sqlite3 import Error
import paho.mqtt.publish as publish
import datetime
import time
import json
import platform
import config
import sensors
import requests
import ast
import math
import sharedfunctions
import base64
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.compat import iteritems


# Read SunSpec Header with logic from pymodbus example
def get_common_block(basereg):
    """ Read and return the sunspec common information
    block.

    :returns: A dictionary of the common block information
    """
    length = 69
    response = client.read_holding_registers(basereg, length + 2)  # FIXME +2???
    decoder = BinaryPayloadDecoder.fromRegisters(response.registers,
                                                 byteorder=Endian.Big,
                                                 wordorder=Endian.Big)

    return {
        'SunSpec_ID': decoder.decode_32bit_uint(),
        'SunSpec_DID': decoder.decode_16bit_uint(),
        'SunSpec_Length': decoder.decode_16bit_uint(),
        'Manufacturer': decoder.decode_string(size=32),
        'Model': decoder.decode_string(size=32),
        'Options': decoder.decode_string(size=16),
        'Version': decoder.decode_string(size=16),
        'SerialNumber': decoder.decode_string(size=32),
        'DeviceAddress': decoder.decode_16bit_uint(),
        'Next_DID': decoder.decode_16bit_uint(),
        'Next_DID_Length': decoder.decode_16bit_uint(),
    }


# Read SunSpec header
def getSunSpec(basereg):
    # Read two bytes from baseReg, a SUNSPEC device will start with 0x53756e53
    # As 8bit ints they are 21365, 28243
    try:
        response = client.read_holding_registers(basereg, 2)
    except:
        return None

    if response.registers[0] == 21365 and response.registers[1] == 28243:
        logline("INFO", ".. SunSpec device found. Reading Manufacturer info")
    else:
        return None

    # There is a 16 bit string at baseReg + 4 that contains Manufacturer
    response = client.read_holding_registers(basereg + 4, 16)

    decoder = BinaryPayloadDecoder.fromRegisters(response.registers,
                                                 byteorder=Endian.Big,
                                                 wordorder=Endian.Big)
    manufacturer = decoder.decode_string(16)
    if "OUTBACK_POWER" in manufacturer.upper():
        logline("INFO", ".. Outback Power device found")
    else:
        logline("INFO", ".. Not an Outback Power device. Detected " + manufacturer)
        return None

    try:
        register = client.read_holding_registers(basereg + 3)
    except:
        return None

    blockSize = int(register.registers[0])

    return blockSize


def getBlock(baseReg):
    try:
        register = client.read_holding_registers(baseReg)
    except:
        return None

    blockID = int(register.registers[0])

    # Peek at block style
    try:
        register = client.read_holding_registers(baseReg + 1)
    except:
        return None

    blockSize = int(register.registers[0])
    blockName = None

    try:
        blockName = mate3_did[blockID]
        # print "Detected a " + mate3_did[blockID] + " at " + str(baseReg) + " with size " + str(blockSize)
    except:
        print "ERROR: Unknown device type with DID=" + str(blockID)

    return {"size": blockSize, "DID": blockName}


# Make a shortcut for logline
logline = sharedfunctions.logline

print "------------------------------------------------"
print " MATE3 ModBus Interface"
print "------------------------------------------------"

mate3_ip = '192.168.1.112'
mate3_modbus = 502

sunspec_start_reg = 40000

# Define the dictionary mapping SUNSPEC DID's to Outback names
# Device IDs definitions = (DID)
# AXS_APP_NOTE.PDF from Outback website has the data
mate3_did = {
    64110: "Outback block", 64111: "Charge Controller Block", 64112: "Charge Controller Configuration block",
    64115: "Split Phase Radian Inverter Real Time Block", 64116: "Radian Inverter Configuration Block",
    64117: "Single Phase Radian Inverter Real Time Block", 64113: "FX Inverter Real Time Block",
    64114: "FX Inverter Configuration Block", 64119: "FLEXnet-DC Configuration Block",
    64118: "FLEXnet-DC Real Time Block",
    64120: "Outback System Control Block", 101: "SunSpec Inverter - Single Phase",
    102: "SunSpec Inverter - Split Phase",
    103: "SunSpec Inverter - Three Phase", 64255: "OpticsRE Statistics Block", 65535: "End of SunSpec"
}

# Try to build the mate3 MODBUS connection
logline("INFO", "Building MATE3 MODBUS connection")
# Mate3 connection
try:
    client = ModbusClient(mate3_ip, mate3_modbus)
except:
    client.close()
    logline("ERROR", ".. Failed to connect to MATE3. Enable SUNSPEC and check port. Exciting")
    exit()

logline("INFO", ".. Connected OK")

logline("INFO", "Make sure we are indeed connected to an Outback power system")
reg = sunspec_start_reg

# TEST TEST TEST
print get_common_block(baseReg)

size = getSunSpec(reg)
if size == None:
    logline("ERROR", "We have failed to detect an Outback system. Exciting")
    exit()
startReg = reg + size + 4

# Interrogation loop
while (True):
    reg = startReg
    for block in range(0, 30):
        # print "Getting data from Register=" + str(reg) + " last size was " + str(size)
        blockResult = getBlock(reg)

        if "Single Phase Radian Inverter Real Time Block" in blockResult['DID']:
            logline("INFO", ".. Reading inverter data")
            response = client.read_holding_registers(reg + 2, 1)
            logline("INFO", ".... Connected on HUB port " + str(response.registers[0]))
            # Inverter Output current
            response = client.read_holding_registers(reg + 7, 1)
            current_inverted = int(response.registers[0])
            logline("INFO", ".... Inverted output current (A) " + str(current_inverted))

            response = client.read_holding_registers(reg + 8, 1)
            current_charger = int(response.registers[0])
            logline("INFO", ".... Charger current (A) " + str(current_charger))

            response = client.read_holding_registers(reg + 9, 1)
            current_in = int(response.registers[0])
            logline("INFO", ".... Input current (A) " + str(current_in))

            response = client.read_holding_registers(reg + 30, 1)
            voltage_ac_in = int(response.registers[0])
            logline("INFO", ".... Voltage in (V) " + str(voltage_ac_in))

            response = client.read_holding_registers(reg + 13, 1)
            voltage_ac_out = int(response.registers[0])
            logline("INFO", ".... Voltage Out (V) " + str(voltage_ac_out))

            response = client.read_holding_registers(reg + 17, 1)
            voltage_batt = int(response.registers[0]) * 0.1
            logline("INFO", ".... Battery voltage (V) " + str(voltage_batt))

            response = client.read_holding_registers(reg + 18, 1)
            voltage_batt_target = int(response.registers[0]) * 0.1
            logline("INFO", ".... Battery target voltage - temp compensated (V) " + str(voltage_batt_target))

            response = client.read_holding_registers(reg + 27, 1)
            temp_batt = int(response.registers[0])
            logline("INFO", ".... Battery temperature (V) " + str(temp_batt))

            response = client.read_holding_registers(reg + 30, 1)
            voltage_ac_in = int(response.registers[0])
            logline("INFO", ".... Voltage in (V) " + str(voltage_ac_in))

            response = client.read_holding_registers(reg + 31, 1)
            voltage_ac_use = int(response.registers[0])
            logline("INFO", ".... AC USE (Y/N) " + str(voltage_ac_use))

        if "End of SunSpec" not in blockResult['DID']:
            reg = reg + blockResult['size'] + 2
        else:
            break

    time.sleep(3)
