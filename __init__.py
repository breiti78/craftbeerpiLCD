#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
import socket
import fcntl
import struct

import warnings

from time import gmtime, strftime
from modules import app, cbpi

from .contextmanagers import cursor, cleared
from .gpio import CharLCD as GpioCharLCD

from i2c import CharLCD

lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1,
              cols=20, rows=4, dotsize=8,
              charmap='A00',
              auto_linebreaks=True,
              backlight_enabled=True)

## Set refresh interval here
###refresh = 5
#get config from parameters: meantime it can be configurated here
#multidisplay not equal on: only kettle with id1 = x is shown at LCD and it does not pulse
#multidisplay on: all kettles are shown periodically (as refreshtime is defined)
###multidisplay = "on"
#id1 is the kettlenumber like in hardwaretable in ide defined
###id1 = 1

def set_parameter_refresh():

  ref = cbpi.get_config_parameter('LCD_Refresh', None)
  if ref is None:
      cbpi.add_config_parameter("LCD_Refresh", 5, "number", "Time to remain till next display in sec")
      ref = cbpi.get_config_parameter('LCD_Refresh', None)
  return ref

refresh = float(set_parameter_refresh())
cbpi.app.logger.info("LCDDisplay  - Refeshrate %s" % (refresh))

def set_parameter_multidisplay():
  
  multi = cbpi.get_config_parameter('LCD_Multidisplay', None)
  if multi is None:
      cbpi.add_config_parameter("LCD_Multidisplay", "on", "select", "Toggle between all Kettles or show only one Kette constantly", ["on","off"])
      multi=cbpi.get_config_parameter('LCD_Multidisplay', None)
  return multi

multidisplay = str(set_parameter_multidisplay())
cbpi.app.logger.info("LCDDisplay  - Multidisplay %s" % (multidisplay))

def set_parameter_id1():
  
  kid1 = cbpi.get_config_parameter("LCD_singledisplay", None)
  if kid1 is None:
      cbpi.add_config_parameter("LCD_singledisplay", 1, "number", "Choose Kettle (Number)")
      kid1 = cbpi.get_config_parameter('LCD_singledisplay', None)
  return kid1

id1 = int(set_parameter_id1())
cbpi.app.logger.info("LCDDisplay  - Kettlenumber used %s" % (id1))
def get_ip(interface):
    ip_addr = "Not connected"
    so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ip_addr = socket.inet_ntoa(fcntl.ioctl(so.fileno(), 0x8915, struct.pack('256s', interface[:15]))[20:24])
    finally:
        return ip_addr

def get_version_fo(path):
    version = ""
    try:
        if path is not "":
            fo = open(path, "r")
        else:
            fo = open("/home/pi/craftbeerpi3/config/version.yaml","r")
        version = fo.read();
        fo.close()
    finally:
        return version
version = (get_version_fo(""))

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

                line1 = (u'%s' % (s.name,))[:20]

                #line2 when steptimer is runnig show remaining time instead of kettlename
                if s.timer_end is not None:
                    time_remaining = time.strftime(u"%H:%M:%S", time.gmtime(s.timer_end - time.time()))
                    line2 = ((u"%s %s" % ((value.name).ljust(12)[:11], time_remaining)).ljust(20)[:20])
                else:
                    line2 = ((u'%s' % (value.name,))[:20])

                line3 = (u"Targe Temp:%6.2f%s" % (float(value.target_temp),(u"°C")))[:20]
                line4 = (u"Curre Temp:%6.2f%s" % ((current_sensor_value),(u"°C")))[:20]

                lcd.cursor_pos = (0, 0)
                lcd.write_string(line1)
                lcd.cursor_pos = (1, 0)
                lcd.write_string(line2)
                lcd.cursor_pos = (2, 0)
                lcd.write_string(line3)
                lcd.cursor_pos = (3, 0)
                lcd.write_string(line4)

                time.sleep(refresh)

                pass
        else:
            #lcd.clear()

            current_sensor_value_id1 = float(cbpi.get_sensor_value(id1))

            line1 = (u'%s' % (s.name,)).ljust(20)[:20]

            #line2 when steptimer is runnig show remaining time instead of kettlename
            if s.timer_end is not None:
                time_remaining = time.strftime(u"%H:%M:%S", time.gmtime(s.timer_end - time.time()))
                line2 = ((u"%s %s" % ((cbpi.cache.get("kettle")[id1].name).ljust(12)[:11],time_remaining)).ljust(20)[:20])
            else:
                line2 = ((u'%s' % (cbpi.cache.get("kettle")[id1].name)).ljust(20)[:20])

            line3 = (u"Targe Temp:%6.2f%s" % (float(cbpi.cache.get("kettle")[id1].target_temp),(u"°C"))).ljust(20)[:20]
            line4 = (u"Curre Temp:%6.2f%s" % ((current_sensor_value_id1),(u"°C"))).ljust(20)[:20]


            lcd.cursor_pos = (0, 0)
            lcd.write_string(line1)
            lcd.cursor_pos = (1, 0)
            lcd.write_string(line2)
            lcd.cursor_pos = (2, 0)
            lcd.write_string(line3)
            lcd.cursor_pos = (3, 0)
            lcd.write_string(line4)

    else:
        lcd.cursor_pos = (0, 0)
        lcd.write_string((u"CraftBeerPi %s" % version).ljust(20))
        lcd.cursor_pos = (1, 0)
        lcd.write_string((u'%s' % (cbpi.get_config_parameter('brewery_name','No Brewery'))).ljust(20)[:20])
        lcd.cursor_pos =(2, 0)
        lcd.write_string((u"IP: %s" % ip).ljust(20)[:20])
        lcd.cursor_pos = (3, 0)
        lcd.write_string((strftime(u"%Y-%m-%d %H:%M:%S", time.localtime())).ljust(20))
    pass
