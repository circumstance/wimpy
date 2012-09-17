# ******!*********!*********!*********!*********!*********!*********!*********
#
# Copyright (c) IBM Corporation, 2006. All Rights Reserved.
# Author: Simon Johnston (skjohn@us.ibm.com)
#
# Simple class which can interface to a serially connected GPS device that
# implements the NMEA standard.  The reference I used was found at:
#   http://www.gpsinformation.org/dale/nmea.htm
# The class currently decodes the following sentences:
#   GLL, GSA, GSV, RMC
#
# Classes:
#   GPSError - exception for GPSDevice (also wraps serial errors).
#   GPSDevice - GPS device interface (serial) class.
#
# Functions:
#   format_date - convert date from NMEA to ISO format.
#   format_time - convert time from NMEA to ISO format.
#   format_latlong - convert date from NMEA to standard decimal format.
#
# ******!*********!*********!*********!*********!*********!*********!*********

import datetime

import serial

class GPSError(Exception):
    """ Signal errors in the GPS communication, both NMEA sentence errors
        as well as wrapping up underlying serial I/O errors.
    """
    pass

class GPSDevice(object):
    """ General GPS Device interface for connecting to serial port GPS devices 
        using the default communication params specified by the National Marine 
        Electronics Association (NMEA) specifications. 
    """
    def __init__(self, commport):
        """ GPSDevice(port)
            Connects to the serial port specified, as the port numbers are 
            zero-based on windows the actual device string would be "COM" + 
            port+1.
        """
        self.commport = commport
        self.port = None
        
    def open(self):
        """ open()
            open the GPS device port, the NMEA default serial I/O parameters are 
            defined as 4800,8,N,1.
        """
        nmea_params = {
            'port': self.commport,
            'baudrate': 4800,
            'bytesize': serial.EIGHTBITS,
            'parity': serial.PARITY_NONE,
            'stopbits': serial.STOPBITS_ONE
        }
        if self.port:
            raise GPSError, 'Device port is already open'
        try:
            self.port = serial.Serial(**nmea_params)
            self.port.open()
        except serial.SerialException:
            raise GPSError, 'Caught serial error opening port, is device connected?'

    def read(self):
        """ read() -> dict
            rRad a single NMEA sentence from the device returning the data as a 
            dictionary. The 'sentence' key will identify the sentence type itself 
            with other parameters extracted and nicely formatted where possible.
        """
        sentence = 'error'
        line = self._read_raw()
        if line:
            parsed =  self._validate(line)
            if parsed:
                if _decode_func.has_key(parsed[0]):
                    return _decode_func[parsed[0]](parsed)
                else:
                    sentence = parsed[0]
        return {
            'sentence': sentence
        }

    def read_all(self):
        """ read_all() -> dict
            A generator allowing the user to read data from the device in a for loop 
            rather than having to craft their own looping method.
        """
        while 1: 
            try:
                record = self.read()
            except IOError:
                raise StopIteration
            yield record

    def close(self):
        """ close()
            Close the port, note you can no longer read from the device until you 
            re-open it.
        """
        if not self.port:
            raise GPSError, 'Device port not open, cannot close'
        self.port.close()
        self.port = None

    def _read_raw(self):
        """ _read_raw() -> str
            Internal method which reads a line from the device (line ends in \r\n).
        """
        if not self.port:
            raise GPSError, 'Device port not open, cannot read'
        return self.port.readline()

    def _checksum(self, data):
        """ _checksum(data) -> str
            Internal method which calculates the XOR checksum over the sentence (as 
            a string, not including the leading '$' or the final 3 characters, the 
            ',' and checksum itself).
        """
        checksum = 0
        for character in data:
            checksum = checksum ^ ord(character)
        hex_checksum = "%02x" % checksum
        return hex_checksum.upper()

    def _validate(self, sentence):
        """ _validate(sentence) -> str
            Internal method.
        """
        sentence.strip()
        if sentence.endswith('\r\n'):
            sentence = sentence[:len(sentence)-2]
        if not sentence.startswith('$GP'):
            #
            # Note that sentences that start with '$P' are proprietary
            # formats and are described as $P<MID><SID> where MID is the
            # manufacturer identified (Magellan is MGN etc.) and then the
            # SID is the manufacturers sentence identifier.
            #
            return None
        star = sentence.rfind('*')
        if star >= 0:
            check = sentence[star+1:]
            sentence = sentence[1:star]
            sum = self._checksum(sentence)
            if sum <> check:
                 return None
        sentence = sentence[2:]
        return sentence.split(',')

#
# The internal decoder functions start here. 
#
def format_date(datestr):
    """ format_date(datestr) -> str
        Internal function. Turn GPS DDMMYY into DD/MM/YY
    """
    year = int(datestr[4:])
    now = datetime.date.today()
    if year + 2000 > now.year:
        year = year + 1900
    else:
        year = yeat + 2000
    the_date = datetime.date(year, int(datestr[2:4]), int(datestr[:2]))
    return the_date.isoformat()

def format_time(timestr):
    """ format_time(timestr) -> str
        Internal function. Turn GPS HHMMSS into HH:MM:SS UTC
    """
    utc_str = '+00:00'
    the_time = datetime.time(int(timestr[:2]), int(timestr[2:4]), int(timestr[4:]))
    return the_time.strftime('%H:%M:%S') + utc_str

def format_latlong(data, direction):
    """ format_latlong(data, direction) -> str
        Internal function. Turn GPS HHMM.nnnn into standard HH.ddddd
    """
    # Check to see if it's HMM.nnnn or HHMM.nnnn or HHHMM.nnnn
    dot = data.find('.')
    if (dot > 5) or (dot < 3):
        raise ValueError, 'Incorrect formatting of "%s"' % data
    hours = data[0:dot-2]
    mins = float(data[dot-2:])
    if hours[0] == '0':
        hours = hours[1:]
    if direction in ['S', 'W']:
        hours = '-' + hours
    decimal = mins / 60.0 * 100.0
    decimal = decimal * 10000.0
    return '%s.%06d' % (hours, decimal)

def _convert(v, f, d):
    """ convert(v, f, d) -> value
        Internal function.
    """
    try:
        return f(v)
    except:
        return d

def _decode_gll(data):
    """ decode_gll(date) -> dict
        Internal function.
    """
    return {
        'sentence': data[0],
        'latitude': '%s' % format_latlong(data[1], data[2]),
        'longitude': '%s' % format_latlong(data[3], data[4]),
        'time': format_time(data[5]),
        'active': data[6]
    }

def _decode_gga(data):
    """ decode_gga(date) -> dict
        Internal function.
    """
    quality = ['invalid', 'GPS', 'DGPS', 'PPS', 'Real TIme', 'Float RTK',
               'Estimated', 'Manual', 'Simulation']
    qindex = _convert(data[6], int, '')
    if qindex >= len(quality):
        qstring = str(qindex)
    else:
        qstring = quality[qindex]
    return {
        'sentence': data[0],
        'time': format_time(data[1]),
        'latitude': '%s' % format_latlong(data[2], data[3]),
        'longitude': '%s' % format_latlong(data[4], data[5]),
        'quality': qstring,
        'tracked': _convert(data[7], int, ''),
        'dilution': _convert(data[8], float, ''),
        'altitude': '%s,%s' % (data[9], data[10]),
        'geoid_height': '%s,%s' % (data[11], data[12])
    }

def _decode_gsa(data):
    """ decode_gsa(date) -> dict
        Internal function.
    """
    return {
        'sentence': data[0],
        'selection': data[1],
        '3dfix': _convert(data[2], int, ''),
        'prns': data[3:14],
        'pdop': convert(data[15], float, ''),
        'horizontal_dilution': _convert(data[16], float, ''),
        'vertical_dilution': _convert(data[17], float, ''),
    }

def _decode_gsv(data):
    """ decode_gsv(date) -> dict
        Internal function.
    """
    return {
        'sentence': data[0],
        'satelite': _convert(data[2], int, ''),
        'inuse': _convert(data[1], int, ''),
        'inview': _convert(data[3], int, ''),
        'prn': _convert(data[4], int, ''),
        'elevation': _convert(data[5], float, ''),
        'azimuth': _convert(data[6], float, ''),
        'snr': _convert(data[7], int, '')
    }

def _decode_rmc(data):
    """ decode_rmc(date) -> dict
        Internal function.
    """
    return {
        'sentence': data[0],
        'time': format_time(data[1]),
        'active': data[2],
        'latitude': '%s' % format_latlong(data[3], data[4]),
        'longitude': '%s' % format_latlong(data[5], data[6]),
        'speed': _convert(data[7], float, ''),
        'angle': _convert(data[8], float, ''),
        'date': format_date(data[9]),
        'variation': '%s,%s' % (data[10], data[11])
    }

#
# Simple dictionary mapping the sentence types to their
# corresponding decoder functions.
#
_decode_func = {
    'GLL': _decode_gll,
    'GSA': _decode_gsa,
    'GSV': _decode_gsv,
    'RMC': _decode_rmc,
}

#
# Simple test case, this can be used to run indefinitely (formatting and printing
# each record) or run until it gets a GLL response and print the machines location.
#
if __name__ == '__main__':
    import sys
    port = 4
    gps = GPSDevice(port)
    gps.open()
    for record in gps.read_all():
        if sys.argv[0] == 'forever':
            print record
        else:
            if record['sentence'] == 'GLL':
                print 'I was at long %s, lat %s at %s' % (
                      record['longitude'],
                      record['latitude'],
                      record['time'])
                break
