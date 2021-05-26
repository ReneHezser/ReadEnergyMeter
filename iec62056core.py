# file: iec62056core.py
#
# 2010 Dunker594 <team594 [at] hushmail [dot] com>
#
# There is little or no error checking so beware

#################### genBCC(bccStr) ########################################################################################

# Generate block check character from given string (string must contain SOH or STX and end with ETX)

def genBCC(bccStr):
	inData = map(ord, bccStr)			# convert the string of data to be written to a list of individual bytes
	posSTX = -1; posSOH = -1; posETX = -1; startPos = -1; x = 0
	for i in inData:
		if posSOH == -1:
			if i == 0x01: posSOH = x
		if posSTX == -1:
			if i == 0x02: posSTX = x
		if startPos == -1:
			if (posSOH > -1) | (posSTX > -1): startPos = x + 1
		if i == 0x03: posETX = x
		x += 1
	if (posSOH + posSTX + posETX) == -3:
		print ("error, SOH, STX and ETX do not exist - unable to generate BCC") # log
	elif (posSOH + posSTX) == -2:
		print ("error, SOH and STX do not exist - unable generate BCC") # log
	elif posETX == -1:
		print ("error, ETX does not exist - unable generate BCC") # log
	elif posETX < startPos:
		print ("error, ETX is before SOH/STX - unable to generate BCC") # log
	else:
		if (startPos + posETX) > 0:
			x = startPos; BCC = inData[x]
			while x < posETX:
				x += 1
				BCC = BCC ^ inData[x]
			return chr(BCC)			# returns BCC as a single char to append to the data to be written to the meter
	return ""					# on error exit with empty BCC char

#################### genSiemensP2 ##########################################################################################

# From iec62056-21 the meter P0 password requests are in the form:
# SOH P 0 ( X X X X ) ETX 'BCC'
# where X X X X is a 4 character 'outcode' sent from the meter to solicit a P2 password reponse in the form:
# SOH P 2 ( Y Y Y Y ) ETX 'BCC'
# where Y Y Y Y is the corresponding 'incode' sent back to the meter. 'BCC' is the block check character.
# Different maufacturers and models may have a number of different algos.

# My test Siemens meter only seems to request P0 password requests in the form SOH P 0 ( X X X 0 ) ETX 'BCC' and only digits
# [0..9]are used. P2 answers are obviously in hex. Thats only 1000 * 64k possible answers. Not too many to fuzz then ;o)
# Unless, ofcourse, we can work out the algo...

def genSiemensP2(outcode):
	M4 = int(outcode[3], 16) << 2 & 0x0C | int(outcode[0], 16) >> 2 & 0x03
	M3 = int(outcode[0], 16) << 2 & 0x0C | int(outcode[1], 16) >> 2 & 0x03
	M2 = int(outcode[1], 16) << 2 & 0x0C | int(outcode[2], 16) >> 2 & 0x03
	M1 = int(outcode[2], 16) << 2 & 0x0C | int(outcode[3], 16) >> 2 & 0x03
	X = M3 ^ M4; Y = M2 ^ M4; Z = M1 ^ M4 + 1
	R1 = ((X << 8) + (Y << 4) + Z) & 0x0FFF
	if R1 == 0:	R1 += 1
	R2 = R1 * 0x20; count = 0
	while count <= 0x10:
		if (R2 & 0x01 == 0x01):
			R2 = R2 ^ 0x012
		R2 = R2 >> 1
		count += 1
	L1 = R2 & 0x0F; L2 = L1 & 0x0C; L3 = L1 & 0x03
	S2 = X ^ L1; S1 = Y ^ L1; S0 = Z ^ L1
	K1 = ((S2 << 8) + (S1 << 4) + S0) & 0x0FFF
	K1 *= 4; K1 = K1 + L3 * 0x04000; K1 = K1 + (L2 >> 2)
	incode = ""; x = 12
	while x >= 0:
		K2 = (K1 >> x) & 0x000F
		incode = incode + hex((K2))[2:].upper()
		x -= 4
	return incode # returns incode (Y Y Y Y from above) as a 4 character string of hexadecimal characters [0..9, A..F]

################## genString(inStr) ########################################################################################

# returns a whitespace padded printable string with non-printable characters represented

def genString(inStr):								# generate string from data
	inData = map(ord, inStr)						# generate list of inStr bytes
	outString = "";
	bit7chars = ("NUL ", "SOH ", "STX ", "ETX ", "EOT ", "ENQ ", "ACK ", "BEL ", "BS ", "HT ",
	"LF ", "VT ", "FF ", "CR ", "SO ", "SI ", "DLE ", "DC1 ", "DC2 ", "DC3 ", "DC4 ", "NAK ", "SYN ",
	"ETB ", "CAN ", "EM ", "SUB ", "ESC ", "FS ", "GS ", "RS ", "US ", "SP ", "! ", "\" ", "# ", "$ ",
	"% ", "& ", "' ", "( ", ") ", "* ", "+ ", ", ", "- ", ". ", "/ ", "0 ", "1 ", "2 ", "3 ", "4 ",
	"5 ", "6 ", "7 ", "8 ", "9 ", ": ", "; ", "< ", "= ", "> ", "? ", "@ ", "A ", "B ", "C ", "D ",
	"E ", "F ", "G ", "H ", "I ", "J ", "K ", "L ", "M ", "N ", "O ", "P ", "Q ", "R ", "S ", "T ",
	"U ", "V ", "W ", "X ", "Y ", "Z ", "[ ", "\\ ", "] ", "^ ", "_ ", "` ", "a ", "b ", "c ", "d ",
	"e ", "f ", "g ", "h ", "i ", "j ", "k ", "l ", "m ", "n ", "o ", "p ", "q ", "r ", "s ", "t ",
	"u ", "v ", "w ", "x ", "y ", "z ", "{ ", "| ", "} ", "~ ", "DEL ");
	for i in inData:
		outString += bit7chars[i]					# build printable string
	outString = outString[:-1]						# remove last trailing space
	return outString							# return string

#TO FINISH########## processIDMessage() ####################################################################################

# print statements need removing for return strings - class it all up?

# 50ms after signing on my Siemens meter sends the following:
#  /  F  M  l  4  A  0  0  0  0  V  8  0 CR LF
# 2f 46 4d 6c 34 41 30 30 30 30 56 38 30 0d 0a

def processIDMessage(readData):
	baudID = 0
	str1 = str2 = str3 = str4 = ""
	if 7 <= len(readData) <= 23:
		flag = readData[1:4]
		manufacturerFlags = {}
		try:
			with open("flags", "r") as inFile:
				for line in inFile:
					if (line[0] != "#") & (len(line) > 2):
						value = line.lstrip().rstrip()
						key = value[:3]
						value = value[3:].lstrip()
						if len(key) > 2: manufacturerFlags[key] = value 	# needs 'if' cos blank line with only a few tabs and spaces gets thru
		except:
			print ("Unable to open manufacturer \"flags\" definition file")	# log this error
		flagU = flag.upper()
		if flagU in manufacturerFlags:
			str1 = flag + " : " + manufacturerFlags[flagU]
		else:
			print (flag + " : Manufacturer flag not in definition file")	# log this error
		if flag[2:3].islower():
			str2 = "  " + flag[2:3] + " : Last character of flag is in lower case, 20ms min reaction time"
		baudFlag = readData[4:5]
		baudID = getBaudID(baudFlag)
		if baudID != 0:
			str3 = "  " + str(baudFlag) + " : Baudrate changeover identification, rate = " + str(baudID) + "bd"
		else:
			print ("  " + str(baudFlag) + " : Unknown baudrate identifier")	# log this error
		str4 = " ID : Meter identification string = " + readData[5:-2]		# check if last 2 chars are \r\n maybe
	else:
		print ("Received meter ID is invalid")					# log this error
	return (baudID, str1, str2, str3, str4)

#################### getBaudID(inChar) #####################################################################################

def getBaudID(inChar):
	baudID = {"0":300, "1":600, "A":600, "2":1200, "B":1200, "3": 2400, "C":2400, "4":4800, "D":4800, "5":9600, "E":9600, "6":19200, "F":19200}
	if inChar in baudID:
		return baudID[inChar]
	else:
		return 0

############################################################################################################################


