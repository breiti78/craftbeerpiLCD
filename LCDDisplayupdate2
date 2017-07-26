from modules import app, cbpi
import time
import lcddriver
import logging
from time import gmtime, strftime
import socket
import fcntl
import struct

lcd = lcddriver.lcd()

## Set refresh interval here
refresh = 5
#get config from parameters: meantime it can be configurated here
#multidisplay not equal on: only kettle with id1 = x is shown at LCD and it does not pulse
#multidisplay on: all kettles are shown periodically (as refreshtime is defined)
multidisplay = "on"
#id1 is the kettlenumber like in hardwaretable in ide defined
id1 = 1

cbpi.app.logger.info("LCDDisplay Multidisplay %s" % (multidisplay))
cbpi.app.logger.info("LCDDisplay Kettlenumber used %s" % (id1))

def get_ip(interface):
    ip_addr = "Not connected"
    so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ip_addr = socket.inet_ntoa(fcntl.ioctl(so.fileno(), 0x8915, struct.pack('256s', interface[:15]))[20:24])
    finally:
        return ip_addr
    
##Background Task to load the data
@cbpi.backgroundtask(key="lcdjob", interval=0.7)
def lcdjob(api):
    ## YOUR CODE GOES HERE
    
    s = cbpi.cache.get("active_step")
    
    if get_ip('wlan0') == "Not connected":
        ip = get_ip('eth0')
    else:
        ip = get_ip('wlan0')

    if s is not None:
        
        if multidisplay == "on":
            lcd.clear()    
            for idx, value in cbpi.cache["kettle"].iteritems():
                current_sensor_value = float(cbpi.get_sensor_value(value.sensor))
                
                line1 = ('%s' % (s.name,)).ljust(20)[:20]
                
                #line2 when steptimer is runnig show remaining time instead of kettlename
                if s.timer_end is not None:
                    time_remaining = time.strftime("%H:%M:%S", time.gmtime(s.timer_end - time.time()))
                    line2 = ("Remai Time: %s" % (time_remaining)).ljust(20)[:20]
                else:
                    line2 = ('%s' % (value.name,)).ljust(20)[:20]
                    
                line3 = ("Targe Temp:%6.2f%s" % (float(value.target_temp),(chr(223)+"C"))).ljust(20)[:20]
                line4 = ("Curre Temp:%6.2f%s" % ((current_sensor_value),(chr(223)+"C"))).ljust(20)[:20]
                
                lcd.display_string(line1, 1)
                lcd.display_string(line2, 2)
                lcd.display_string(line3, 3)
                lcd.display_string(line4, 4)
                
                time.sleep(refresh)
                
                pass
        else:
            #lcd.clear()
            
            current_sensor_value_id1 = float(cbpi.get_sensor_value(id1))
                
            line1 = ('%s' % (s.name,)).ljust(20)[:20]
                
            #line2 when steptimer is runnig show remaining time instead of kettlename
            if s.timer_end is not None:
                time_remaining = time.strftime("%H:%M:%S", time.gmtime(s.timer_end - time.time()))
                line2 = ("Remai Time: %s" % (time_remaining)).ljust(20)[:20]
            else:
                line2 = ('%s' % (cbpi.cache.get("kettle")[id1].name)).ljust(20)[:20]
                
            line3 = ("Targe Temp:%6.2f%s" % (float(cbpi.cache.get("kettle")[id1].target_temp),(chr(223)+"C"))).ljust(20)[:20]
            line4 = ("Curre Temp:%6.2f%s" % ((current_sensor_value_id1),(chr(223)+"C"))).ljust(20)[:20]
                

            lcd.display_string(line1, 1)
            lcd.display_string(line2, 2)
            lcd.display_string(line3, 3)
            lcd.display_string(line4, 4)
            
    else:
        lcd.display_string(("CraftBeerPi 3.0.2").ljust(20)[:20], 1)
        lcd.display_string((cbpi.get_config_parameter("brewery_name","No Brewery")).ljust(20)[:20], 2)
        lcd.display_string(("IP: %s" % ip).ljust(20)[:20], 3)
        lcd.display_string((strftime("%Y-%m-%d %H:%M:%S", time.localtime())).ljust(20)[:20], 4)
    pass
	
	

