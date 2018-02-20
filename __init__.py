#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import logging
import socket
import fcntl
import struct
import warnings
import datetime
import threading
from time import gmtime, strftime
from modules import app, cbpi
from .contextmanagers import cursor, cleared
from .gpio import CharLCD as GpioCharLCD
from i2c import CharLCD

#LCDVERSION = '3.7.22'
#The LCD-library and LCD-driver are taken from RPLCD Project version 1.0.
#The documentation:   http://rplcd.readthedocs.io/en/stable/ very good and readable.
#Git is here:         https://github.com/dbrgn/RPLCD.
#LCD_Address should be something like 0x27, 0x3f etc. See parameters in Craftbeerpi3.
#To determine address of LCD use comand promt in Raspi: sudo i2cdetect -y 1 or sudo i2cdetect -y 0
#assembled by JamFfm
#17.02.2018 add feature to change Multidispaly <-> Singlediplay without CBPI reboot
#17.02.2018 add feature to change Kettle Id for Singlediplay without CBPI reboot
#17.02.2018 add feature to change refresh rate for Multidisplay without CBPI reboot
#17.02.2018 add feature to change refresh rate for Multidisplay in parameters with choose of value from 1-6s because more than 6s is too much delay in switching actors
#18.02.2018 improve stability (no value of a temp sensor)
#

@cbpi.initalizer(order=3000)
def init(cbpi):

    global LCDaddress
    LCDaddress = int(set_lcd_address(),16)
    cbpi.app.logger.info('LCDDisplay  - LCD_Address %s %s' % (set_lcd_address(),LCDaddress))
    
    #This is just for the logfile at start
    refreshlog = float(set_parameter_refresh())
    cbpi.app.logger.info('LCDDisplay  - Refreshrate %s' % (refreshlog))

    #This is just for the logfile at start
    multidisplaylog = str(set_parameter_multidisplay())
    cbpi.app.logger.info('LCDDisplay  - Multidisplay %s' % (multidisplaylog))

    #This is just for the logfile at start
    id1log = int(set_parameter_id1())
    cbpi.app.logger.info("LCDDisplay  - Kettlenumber used %s" % (id1log))


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
      cbpi.add_config_parameter('LCD_Refresh', 3, 'select', 'Time to remain till next display in sec, NO! CBPi reboot required',[1,2,3,4,5,6])
      ref = cbpi.get_config_parameter('LCD_Refresh', None)
  return ref

def set_parameter_multidisplay():  
  multi = cbpi.get_config_parameter('LCD_Multidisplay', None)
  if multi is None:
      cbpi.add_config_parameter('LCD_Multidisplay', 'on', 'select', 'Toggle between all Kettles or show only one Kette constantly, NO! CBPi reboot required', ['on','off'])
      multi=cbpi.get_config_parameter('LCD_Multidisplay', None)
  return multi

def set_parameter_id1():  
  kid1 = cbpi.get_config_parameter("LCD_Singledisplay", None)
  if kid1 is None:
      cbpi.add_config_parameter("LCD_Singledisplay", 1, "number", "Choose Kettle (Number), NO! CBPi reboot required")
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
#cooler symbol should look like icecubes
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
    ip_addr = 'Not connected'
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

def show_multidisplay(refresh):
    
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

        #line3 
        line3 = (u"Targ. Temp:%6.2f%s" % (float(value.target_temp),(u"°C")))[:20]

        #line4 needs errorhandling because there may be tempvalue without sensordates and so it is none and than an error is thrown
        try:
            line4 = (u"Curr. Temp:%6.2f%s" % (float(current_sensor_value),(u"°C")))[:20]
        except:
            cbpi.app.logger.info("LCDDisplay  - current_sensor_value exception %s" % (current_sensor_value))
            line4 = (u"Curr. Temp: %s" % (("No Data")))[:20]
            
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



def show_singlemode(id1):
    cbpi.app.logger.info("LCDDisplay  - id1 an Funktion übergeben %s" % (id1))
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

    #line3
    line3 = (u"Targ. Temp:%6.2f%s" % (float(cbpi.cache.get("kettle")[id1].target_temp),(u"°C"))).ljust(20)[:20]

    #line4 needs errorhandling because there may be tempvalue without sensordates and so it is none and than an error is thrown
    try:
        line4 = (u"Curr. Temp:%6.2f%s" % (float(current_sensor_value_id1),(u"°C"))).ljust(20)[:20]
    except:
        cbpi.app.logger.info("LCDDisplay  - singlemode current_sensor_value_id1 exception %s" % (current_sensor_value_id1))
        line4 = (u"Curr. Temp: %s" % (("No Data")))[:20]
    
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

def show_fermentation_multidisplay(refresh):
    for idx, value in cbpi.cache["fermenter"].iteritems():
        current_sensor_value = (cbpi.get_sensor_value(value.sensor))
        #INFO value = modules.fermenter.Fermenter
        #INFO FermenterId = modules.fermenter.Fermenter.id

        #get the state of the heater of the current fermenter, if there is none, except takes place
        try:
            heater_of_fermenter = int(cbpi.cache.get("fermenter").get(value.id).heater)
            #cbpi.app.logger.info("LCDDisplay  - fheater id %s" % (heater_of_fermenter))

            fheater_status = int(cbpi.cache.get("actors").get(heater_of_fermenter).state)
            #cbpi.app.logger.info("LCDDisplay  - fheater status (0=off, 1=on) %s" % (fheater_status))
        except:
            fheater_status = 0

        #get the state of the cooler of the current fermenter, if there is none, except takes place
               
        try:
            cooler_of_fermenter = int(cbpi.cache.get("fermenter").get(value.id).cooler)
            #cbpi.app.logger.info("LCDDisplay  - fcooler id %s" % (cooler_of_fermenter))

            fcooler_status = int(cbpi.cache.get("actors").get(cooler_of_fermenter).state)
            #cbpi.app.logger.info("LCDDisplay  - fcooler status (0=off, 1=on) %s" % (fcooler_status))
        except:
            fcooler_status = 0
        pass

        line1 = (u'%s' % (value.brewname,))[:20]
     
        #line2
        z = 0
        for key, value1 in cbpi.cache["fermenter_task"].iteritems():
            #INFO value1 = modules.fermenter.FermenterStep
            #cbpi.app.logger.info("LCDDisplay  - value1 %s" % (value1.fermenter_id))
            if value1.timer_start is not None and value1.fermenter_id == value.id:
                line2 = interval(value.name,(value1.timer_start- time.time()))
                z = 1
            elif z == 0:
                line2 = (u'%s' % (value.name,))[:20]
            pass
        
        #line3    
        line3 = (u"Targ. Temp:%6.2f%s" % (float(value.target_temp),(u"°C")))[:20]
        
        #line4 needs errorhandling because there may be tempvalue without sensordates and so it is none and than an error is thrown
        try:
            line4 = (u"Curr. Temp:%6.2f%s" % (float(current_sensor_value),(u"°C")))[:20]
        except:
            cbpi.app.logger.info("LCDDisplay  - fermentmode current_sensor_value exception %s" % (current_sensor_value))
            line4 = (u"Curr. Temp: %s" % (("No Data")))[:20]
        pass

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
    lcd.write_string((u"%s" % (cbpi.get_config_parameter("brewery_name","No Brewery"))).ljust(20)[:20])
    lcd.cursor_pos =(2, 0)
    lcd.write_string((u"IP: %s" % ipdet).ljust(20)[:20])
    lcd.cursor_pos = (3, 0)
    lcd.write_string((strftime(u"%Y-%m-%d %H:%M:%S", time.localtime())).ljust(20))
pass   

def interval(fermentername, seconds):
    """
    gives back intervall as tuppel
    @return: (weeks, days, hours, minutes, seconds)
    formats string for line 2
    returns the formatted string for line 2 of fermenter multiview    
    """    
    WEEK = 60 * 60 * 24 * 7
    DAY = 60 * 60 * 24
    HOUR = 60 * 60
    MINUTE = 60
    
    weeks = seconds // WEEK
    seconds = seconds % WEEK
    days = seconds // DAY
    seconds = seconds % DAY
    hours = seconds // HOUR
    seconds = seconds % HOUR
    minutes = seconds // MINUTE
    seconds = seconds % MINUTE

    if weeks >= 1:
        remaining_time = (u"W%d D%d %02d:%02d" % (int(weeks), int(days), int(hours), int(minutes)))
        return ((u"%s %s" % ((fermentername).ljust(8)[:7],remaining_time))[:20])
    elif weeks == 0 and days >= 1:
        remaining_time = (u"D%d %02d:%02d:%02d" % (int(days), int(hours), int(minutes), int(seconds)))
        return ((u"%s %s" % ((fermentername).ljust(8)[:7],remaining_time))[:20])
    elif weeks == 0 and days == 0:
        remaining_time = (u"%02d:%02d:%02d" % (int(hours), int(minutes), int(seconds)))
        return ((u"%s %s" % ((fermentername).ljust(11)[:10],remaining_time))[:20])
    else:
        pass
    pass

##Background Task to load the data
@cbpi.backgroundtask(key="lcdjob", interval=0.7)
def lcdjob(api):
    ## YOUR CODE GOES HERE    
    ## This is the main job

    if get_ip('wlan0') != 'Not connected':
        ip = get_ip('wlan0')
    elif get_ip('eth0') != 'Not connected':
        ip = get_ip('eth0')
    elif get_ip('enxb827eb488a6e')!= 'Not connected':
        ip = get_ip('enxb827eb488a6e')
    else:
        ip ='Not connected'
    
    s = cbpi.cache.get("active_step")

    refreshTime = float(set_parameter_refresh())

    multidisplay_status = str(set_parameter_multidisplay())
    
    if s is not None and multidisplay_status == "on":    
        show_multidisplay(refreshTime)
        
    elif s is not None and multidisplay_status == "off":       
        show_singlemode(int(set_parameter_id1()))

    elif is_fermenter_step_running() == "active":
        show_fermentation_multidisplay(refreshTime)

    else:
        show_standby(ip)
    pass
