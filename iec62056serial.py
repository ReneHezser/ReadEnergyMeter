# file: iec62056serial.py
#
# 2010 Dunker594 <team594 [at] hushmail [dot] com>
#
# This is very basic. Read 62056-21.pdf for further character timing stuff etc.
#
# There is little or no error checking so beware

############################################################################################################################

import sys
import serial
import signal
import time
import iec62056core

#======================================
# Setup iec65026.ser variables:

ser = serial.Serial()

ser.port = "/dev/ttyUSB0"					# set interface instance
ser.baudrate = 300						# set baudrate to 300
ser.parity = serial.PARITY_EVEN					# set parity to even parity
ser.bytesize = serial.SEVENBITS					# number of bits per byte
ser.stopbits = serial.STOPBITS_ONE				# number of stop bits
ser.timeout = 0.05						# timeout block read - set to 50ms (42ms) (value for 300bd) - check pdf
ser.xonxoff = False						# disable software flow control
ser.rtscts = False						# disable hardware (RTS/CTS) flow control
ser.dsrdtr = False						# disable hardware (DSR/DTR) flow control
ser.writeTimeout = 0						# timeout for write
ser.interCharTimeout = 0					# detect when the receiver has stopped seeing any new bytes (alledgedly)

#======================================
# Setup some more global variables

wdTimeout = 2
device_address = ""
signOnStr = "/?!\r\n"
signOffStr = "\x01B0\x03"

#======================================

#TO FINISH########## openPort() ############################################################################################

# error check to see if port is there and is opened ok

def openPort():
	try:
		ser.open()
		return ser.port + " opened successfully"
	except:
		print ("Error, unable to open port: " + ser.port)		# log error and exit
		print ("Exiting...")
		sys.exit(1)

#TO FINISH########## closePort() ###########################################################################################

# error check to see if port is there and is closed ok

def closePort():
	try:
		ser.close()
		return ser.port + " closed successfully"
	except:
		pass
	return

#################### wdTimer(timeout) ######################################################################################

# usage wdTimer(timeout_in_seconds) or wdTimer() >> default is 2 seconds, also use iec62056.wdTimeout = n before calling

class wdTimer(Exception):
	def __init__(self, timeout = wdTimeout):
		self.time = timeout
	def __enter__(self):
		signal.signal(signal.SIGALRM, self.handler)
		signal.alarm(self.time)
	def __exit__(self, type, value, traceback):
		signal.alarm(0)
	def handler(self, signum, frame):
		raise self

#TO FINISH########## writeRaw(inData) ######################################################################################

# needs some error checking stuff here and return something appropriate (the data written !)

#def writeRaw(inData):
#	return inData[:ser.write(inData)]

def writeRaw(inData):						# inData[:ser.write(inData)]; inData := only the bytes written (if error)
	inData[:ser.write(inData)]				# time.sleep was needed in Perl because a following closePort would close
	time.sleep(xmitWait(inData))				# the port immediately leaving data still to be written, also, a delay is
	return inData						# needed for baudrate change ie. finish writing and then change baudrate
#	return inData[:ser.write(inData)]			# time.sleep.xmitWait must be in main() if this line is used instead

#TO FINISH########## xmitWait(inData)) #CHECK###############################################################################

# xmitDelay is the time taken for data written to the port to finish being transmitted
# xmitDelay is dependent on no of chars, parity if used, no of stop bits, no of data bits

def xmitWait(inData):
	charDelay = {300:34.0, 600:17.0, 1200:8.5, 2400:4.25, 4800:2.13, 9600:1.07, 19200:0.54} # might need increasing a tad
	return (charDelay[ser.baudrate] * len(inData) / 1000)					# use 33.0 for 300 and it shits itself

#################### writePortBCC(inData) ##################################################################################

def writePortBCC(inData):
	inData += iec62056core.genBCC(inData)
	return writeRaw(inData)

#################### readRaw() #############################################################################################

def readRaw():
	ser.flushInput()
	readBuffer  = ''
	readBytes = ''
	while ('' == readBuffer):
		readBuffer = ser.read(1)				# poll for 1st received byte
		time.sleep(0.025)						# polling sample time (25ms)
	while ('' != readBuffer):
		readBytes += readBuffer					# build received message
		readBuffer = ser.read(1)				# read 1 byte at a time
	return readBytes

##################### readPort() ###########################################################################################

# check all functions everywhere for what happens when no chars are received - trap and process errors

def readPort():
	try:
		with wdTimer(wdTimeout):				# default timeout of 2 seconds before 1st char received
			return readRaw()
	except wdTimer:
		print ("Error, no chars received")			# timeout tidying / error logging goes here
		return ""

#################### signOn() ##############################################################################################

# To set device address use iec62056.meterID = "device_address" See page 22 EN62056-21:2002 for format of device address.

def signOn():
	return writeRaw(signOnStr[:2] + device_address + signOnStr[2:]) # no block check character used for the sign on string

#################### signOff() #############################################################################################

def signOff():
#	time.sleep(0.2)							# maybe delay here before sending ???
	return writePortBCC(signOffStr)					# q (0x71) is the block check character for "\x01B0\x03"

#################### updateBaud() ##########################################################################################


