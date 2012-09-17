import sys,gps
port = 6
gps = GPSDevice(port)
gps.open()
for record in gps.read_all():
    if sys.argv[0] == 'forever':
        print record
    else:
        if record['sentence'] == 'GLL':
            print 'I am hanging out at long %s, lat %s at %s' % (
                  record['longitude'],
                  record['latitude'],
                  record['time'])
            break