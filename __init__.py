from modules import app, cbpi
import time
import lcddriver
import logging
from time import gmtime, strftime
lcd = lcddriver.lcd()

## Set refresh interval here
refresh = 5

import socket
import fcntl
import struct

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


##Background Task to load the data
@cbpi.backgroundtask(key="lcdjob", interval=1)
def lcdjob(self):
    ## YOUR CODE GOES HERE
    s = cbpi.cache.get("active_step")
    
    if s is not None:
        lcd.clear()
        line1 = '%s' % (s.name,)
        
        for idx, value in cbpi.cache["kettle"].iteritems():
            current_sensor_value = cbpi.get_sensor_value(value.sensor)
            line2 = '%s' % (value.name,)
            line3 = 'Target Temp: %s' % (value.target_temp,)
            line4 = 'Current Temp: %s' % (current_sensor_value,)
            lcd.display_string(line1, 1)
            lcd.display_string(line2, 2)
            lcd.display_string(line3, 3)
            lcd.display_string(line4, 4)
            time.sleep(refresh)
            lcd.clear()
    
    else:
        lcd.display_string("CraftBeerPi 3.0", 1)
        lcd.display_string(cbpi.get_config_parameter("brewery_name","No Brewery"), 2)
        ip=get_ip_address('wlan0')  ## eth0
        lcd.display_string("IP: %s" % ip, 3)
        lcd.display_string(strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 4)
    pass
	
	
