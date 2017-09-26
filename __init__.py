#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import logging
import socket
import fcntl
import struct
import warnings
import datetime
from time import gmtime, strftime
from modules import app, cbpi
from .contextmanagers import cursor, cleared
from .gpio import CharLCD as GpioCharLCD
from i2c import CharLCD

#LCDVERSION = '3.7.7'
#The library and driver are taken from RPLCD Project version 1.0.
#The documentation:   http://rplcd.readthedocs.io/en/stable/ very good and readable.
#Git is here:         https://github.com/dbrgn/RPLCD.
#This version is needed because of CraftBeerPi3 Commits on Aug 31, 2017. 
#Commit: Loading all plugins before calling initializer methods. Now also..
#LCD_Address should be something like 0x27, 0x3f etc. See parameters in Craftbeerpi3.
#To determine address of LCD use comand promt in Raspi: sudo i2cdetect -y 1 or sudo i2cdetect -y 0
#assembled by JamFfm

@cbpi.initalizer(order=3000)
def init(cbpi):

    global LCDaddress
    LCDaddress = int(set_lcd_address(),16)
    cbpi.app.logger.info('LCDDisplay  - LCD_Address %s %s' % (set_lcd_address(),LCDaddress))
    
    global refresh
    refresh = float(set_parameter_refresh())
    cbpi.app.logger.info('LCDDisplay  - Refreshrate %s' % (refresh))

    global multidisplay
    multidisplay = str(set_parameter_multidisplay())
    cbpi.app.logger.info('LCDDisplay  - Multidisplay %s' % (multidisplay))

    global id1
    id1 = int(set_parameter_id1())
    cbpi.app.logger.info("LCDDisplay  - Kettlenumber used %s" % (id1))

    global lcd
    try:
        lcd = lcd(LCDaddress)
        lcd.create_char(0, bierkrug)
        lcd.create_char(1, cool)
    except:
        cbpi.notify('LCD Address is wrong', 'Change LCD Address in parameters,to detect comand promt in Raspi: sudo i2cdetect -y 1', type = 'danger', timeout=None)

#end of init    

def lcd(LCDaddress):
    try:
        lcd = CharLCD(i2c_expander='PCF8574', address=LCDaddress, port=1, cols=20, rows=4, dotsize=8, charmap='A00', auto_linebreaks=True, backlight_enabled=True)
        return lcd
    except:
        pass
    
def set_lcd_address():
  adr = cbpi.get_config_parameter('LCD_Address', None)
  if adr is None:
      cbpi.add_config_parameter('LCD_Address', '0x27', 'string', 'Address of the LCD, CBPi reboot required')
      adr = cbpi.get_config_parameter('LCD_Address', None)
  return adr

def set_parameter_refresh():
  ref = cbpi.get_config_parameter('LCD_Refresh', None)
  if ref is None:
      cbpi.add_config_parameter('LCD_Refresh', 5, 'number', 'Time to remain till next display in sec, CBPi reboot required')
      ref = cbpi.get_config_parameter('LCD_Refresh', None)
  return ref

def set_parameter_multidisplay():  
  multi = cbpi.get_config_parameter('LCD_Multidisplay', None)
  if multi is None:
      cbpi.add_config_parameter('LCD_Multidisplay', 'on', 'select', 'Toggle between all Kettles or show only one Kette constantly, CBPi reboot required', ['on','off'])
      multi=cbpi.get_config_parameter('LCD_Multidisplay', None)
  return multi

def set_parameter_id1():  
  kid1 = cbpi.get_config_parameter("LCD_Singledisplay", None)
  if kid1 is None:
      cbpi.add_config_parameter("LCD_Singledisplay", 1, "number", "Choose Kettle (Number), CBPi reboot required")
      kid1 = cbpi.get_config_parameter('LCD_Singledisplay', None)
  return kid1

#beerglass symbol
bierkrug = (
              0b11100,
              0b00000,
              0b11100,
              0b11111,
              0b11101,
              0b11101,
              0b11111,
              0b11100
        )
#cooler symbol
cool = (
            0b00011,
            0b11011,
            0b11000,
            0b00000,
            0b00110,
            0b00110,
            0b11011,
            0b11011
        )

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
cbpi_version = (get_version_fo(""))

def show_multidisplay():
    
    s = cbpi.cache.get("active_step")
    for idx, value in cbpi.cache["kettle"].iteritems():
        current_sensor_value = (cbpi.get_sensor_value(value.sensor))

        heater_of_kettle = int(cbpi.cache.get("kettle").get(value.id).heater)
        heater_status = int(cbpi.cache.get("actors").get(heater_of_kettle).state)

        line1 = (u'%s' % (s.name,))[:20]

        #line2 when steptimer is runnig show remaining time and kettlename
        if s.timer_end is not None:
            time_remaining = time.strftime(u"%H:%M:%S", time.gmtime(s.timer_end - time.time()))
            line2 = ((u"%s %s" % ((value.name).ljust(12)[:11], time_remaining)).ljust(20)[:20])
        else:
            line2 = ((u'%s' % (value.name,))[:20])

        line3 = (u"Targ. Temp:%6.2f%s" % (float(value.target_temp),(u"°C")))[:20]
        line4 = (u"Curr. Temp:%6.2f%s" % (float(current_sensor_value),(u"°C")))[:20]

        lcd.clear()
        lcd.cursor_pos = (0, 0)
        lcd.write_string(line1)
        lcd.cursor_pos = (0,19)
        if heater_status != 0:
            lcd.write_string(u"\x00")           
        lcd.cursor_pos = (1, 0)
        lcd.write_string(line2)
        lcd.cursor_pos = (2, 0)
        lcd.write_string(line3)
        lcd.cursor_pos = (3, 0)
        lcd.write_string(line4)

        time.sleep(refresh)

    pass

#variable for on off of the beerglassymbol (BierKrug) do not know better than use semioptimal global var.
global bk 
bk = 0


def show_singlemode():
    s = cbpi.cache.get("active_step")

    #read the current temperature of kettle with id1 from parameters  
    current_sensor_value_id1 = (cbpi.get_sensor_value(int(cbpi.cache.get("kettle").get(id1).sensor)))
                            
    #get the state of the heater of the current kettle
    heater_of_kettle = int(cbpi.cache.get("kettle").get(id1).heater)
    #cbpi.app.logger.info("LCDDisplay  - heater id %s" % (heater_of_kettle))

    heater_status = cbpi.cache.get("actors").get(heater_of_kettle).state
    #cbpi.app.logger.info("LCDDisplay  - heater status (0=off, 1=on) %s" % (heater_status))
    
    #line1 the stepname
    line1 = (u'%s' % (s.name,)).ljust(20)[:20]
    
    #line2 when steptimer is runnig show remaining time and kettlename
    if s.timer_end is not None:
        time_remaining = time.strftime(u"%H:%M:%S", time.gmtime(s.timer_end - time.time()))
        line2 = ((u"%s %s" % ((cbpi.cache.get("kettle")[id1].name).ljust(12)[:11],time_remaining)).ljust(20)[:20])
    else:
        line2 = ((u'%s' % (cbpi.cache.get("kettle")[id1].name)).ljust(20)[:20])

    line3 = (u"Targ. Temp:%6.2f%s" % (float(cbpi.cache.get("kettle")[id1].target_temp),(u"°C"))).ljust(20)[:20]
    line4 = (u"Curr. Temp:%6.2f%s" % (float(current_sensor_value_id1),(u"°C"))).ljust(20)[:20]
    
    lcd.cursor_pos = (0, 0)
    lcd.write_string(line1)
    lcd.cursor_pos = (0,19)
    if bk == 0 and heater_status != 0:
        lcd.write_string(u"\x00")
        global bk
        bk = 1    
    else:
        lcd.write_string(u" ")
        global bk
        bk = 0
    lcd.cursor_pos = (1, 0)
    lcd.write_string(line2)
    lcd.cursor_pos = (2, 0)
    lcd.write_string(line3)
    lcd.cursor_pos = (3, 0)
    lcd.write_string(line4)

def show_fermentation_multidisplay():
    for idx, value in cbpi.cache["fermenter"].iteritems():
        current_sensor_value = (cbpi.get_sensor_value(value.sensor))
        
        #cbpi.app.logger.info("LCDDisplay  - value %s" % (value.id))

        #get the state of the heater of the current fermenter
        
        heater_of_fermenter = int(cbpi.cache.get("fermenter").get(value.id).heater)
        #cbpi.app.logger.info("LCDDisplay  - fheater id %s" % (heater_of_fermenter))

        fheater_status = int(cbpi.cache.get("actors").get(heater_of_fermenter).state)
        #cbpi.app.logger.info("LCDDisplay  - fheater status (0=off, 1=on) %s" % (fheater_status))

        #get the state of the cooler of the current fermenter
               
        cooler_of_fermenter = int(cbpi.cache.get("fermenter").get(value.id).cooler)
        #cbpi.app.logger.info("LCDDisplay  - fcooler id %s" % (cooler_of_fermenter))

        fcooler_status = int(cbpi.cache.get("actors").get(cooler_of_fermenter).state)
        #cbpi.app.logger.info("LCDDisplay  - fcooler status (0=off, 1=on) %s" % (fcooler_status))        


        for key, value1 in cbpi.cache["fermenter_task"].iteritems():
            #cbpi.app.logger.info("LCDDisplay  - statusstep %s" % (value1.state))
            
            if value1.timer_start is not None:
                ftime_remaining = time.strftime(u"%H:%M:%S", time.gmtime(value1.timer_start - time.time()))
                #cbpi.app.logger.info("LCDDisplay  - remaining Time1 %s" % (ftime_remaining))
            else:
                pass 

        
        line1 = (u'%s' % (value.brewname,))[:20]

        if value1.timer_start is not None:
            line2 = ((u"%s %s" % ((value.name).ljust(12)[:11],ftime_remaining))[:20])
        else:
            line2 = (u'%s' % (value.name,))[:20]
        
        line3 = (u"Targ. Temp:%6.2f%s" % (float(value.target_temp),(u"°C")))[:20]
        line4 = (u"Curr. Temp:%6.2f%s" % (float(current_sensor_value),(u"°C")))[:20]

        lcd.clear()
        lcd.cursor_pos = (0, 0)
        lcd.write_string(line1)
        lcd.cursor_pos = (0,19)
        if fheater_status != 0:
            lcd.write_string(u"\x00")           
        if fcooler_status != 0:
            lcd.write_string(u"\x01")       
        lcd.cursor_pos = (1, 0)
        lcd.write_string(line2)
        lcd.cursor_pos = (2, 0)
        lcd.write_string(line3)
        lcd.cursor_pos = (3, 0)
        lcd.write_string(line4)

        time.sleep(refresh)

def is_fermenter_step_running():
    for key, value2 in cbpi.cache["fermenter_task"].iteritems():
        if value2.state == "A":
            return "active"
        else:
            pass

def show_standby(ipdet):
    lcd.cursor_pos = (0, 0)
    lcd.write_string((u"CraftBeerPi %s" % cbpi_version).ljust(20))
    lcd.cursor_pos = (1, 0)
    lcd.write_string((u'%s' % (cbpi.get_config_parameter('brewery_name','No Brewery'))).ljust(20)[:20])
    lcd.cursor_pos =(2, 0)
    lcd.write_string((u"IP: %s" % ipdet).ljust(20)[:20])
    lcd.cursor_pos = (3, 0)
    lcd.write_string((strftime(u"%Y-%m-%d %H:%M:%S", time.localtime())).ljust(20))
pass   

           
##Background Task to load the data
@cbpi.backgroundtask(key="lcdjob", interval=0.7)
def lcdjob(api):
    ## YOUR CODE GOES HERE    
    ## This is the main job

    if get_ip('wlan0') == "Not connected":
        ip = get_ip('eth0')
    else:
        ip = get_ip('wlan0')

    s = cbpi.cache.get("active_step")
    
    if s is not None and multidisplay == "on":
        show_multidisplay()

    elif s is not None and multidisplay == "off":
        show_singlemode()

    elif is_fermenter_step_running() == "active":
        show_fermentation_multidisplay()

    else:
        show_standby(ip)
    pass
