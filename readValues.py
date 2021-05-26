import sys
import glob
import serial
import time
import iec62056core
import iec62056serial
from binascii import hexlify

def SignInAndSetSpeed():
	#---------- send sign on string
	print (">  " + iec62056core.genString(iec62056serial.signOn()))

	#---------- receive meter id message
	readData = iec62056serial.readPort()
	print ("<  " + iec62056core.genString(readData) + "   >>>   Data: " + hexlify(readData) + " Length: " + str(len(readData)))
	idMessages = iec62056core.processIDMessage(readData)
	#i = 1
	#while i < len(idMessages):
	#	if idMessages[i] != "":
	#		print idMessages[i]
	#	i += 1

	#---------- send option select
	# send ACK 0 5 1 CR LF (0 = normal mode / 5 = 9600bd / 1 = programming mode)
	print (">  " + iec62056core.genString(iec62056serial.writeRaw("\x06051\r\n")))
	print ("0 = normal mode  / 5 = 9600bd / 1 = programming mode")

	#---------- change to new baudrate (and set timeout?)
	#iec62056serial.ser.timeout = 0.02 # not needed, its MINIMUM reaction time !
	print ("Switching to " + str(idMessages[0]) + "bd")
	iec62056serial.ser.baudrate = idMessages[0]

	#---------- receive P0 password request
	readData = iec62056serial.readPort()
	print ("<  " + iec62056core.genString(readData) + "   >>>   Data: " + hexlify(readData) + " Length: " + str(len(readData)))

	#---------- send P2 password response
	#P0outcode = readData[5:-3] # for Siemens
	P0outcode = "00000000" # for me this is the password the smartmeter accepts
	P2response = "\x01P2\x02(" + iec62056core.genSiemensP2(P0outcode) + ")\x03"		# if P2 password response is wrong meter
	#print "SIEMENS:"+iec62056core.genSiemensP2(P0outcode)
	P2response = "\x01P1\x02(00000000)\x03"
	print (">  " + iec62056core.genString(iec62056serial.writePortBCC(P2response)))		# sends a break message and disconnects

	#---------- receive ACK or BREAK
	readData = iec62056serial.readPort()
	print ("<  " + iec62056core.genString(readData) + "   >>>   Data: " + hexlify(readData) + " Length: " + str(len(readData)))

def ReadValue(obisName):
	# BCC will be generated.  So do not add to the command
	command = "\x01R5\x02" + obisName + "\x03"
	print (">  " + iec62056core.genString(iec62056serial.writePortBCC(command)))
	readData = iec62056serial.readPort()
	print ("<  " + iec62056core.genString(readData) + "   >>>   Data: " + hexlify(readData) + " Length: " + str(len(readData)))

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/ttyUSB*') # ubuntu is /dev/ttyUSB0
    elif sys.platform.startswith('darwin'):
        # ports = glob.glob('/dev/tty.*')
        ports = glob.glob('/dev/tty.SLAB_USBtoUART*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except serial.SerialException as e:
            if e.errno == 13:
                raise e
            pass
        except OSError:
            pass
	
    if len(ports) == 0:
        print ("no serial ports found")

    return result
	   

start_time = time.time()
serial_ports()
#---------- open port ---------------------------------------------------------
print (iec62056serial.openPort())

try:
	SignInAndSetSpeed()

	ReadValue("1.7.0()")
	ReadValue("1.8.0()")
	ReadValue("2.7.0()")
	ReadValue("2.8.0()")

finally:
	#---------- send sign off string
	print (">  " + iec62056core.genString(iec62056serial.signOff()))

	#---------- close port
	print (iec62056serial.closePort())

	elapsed_time = time.time() - start_time
	print ("Duration: " + str(elapsed_time))
