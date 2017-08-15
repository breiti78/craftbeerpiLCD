# LCD add-on for CraftBeerPi 3

With this add-on you can display your Brewing steps temperatures on a 20x4 i2c LCD Display.
There are 2 different modes:

Multidisplay:
The script will loop thru your kettles and display the target and current temperatur.
In timer Mode it displayes the remaining time of the step when temperature is reached.

Single mode:
Only displayes one kettle but reacts a lttle bit faster on temperature changes.

Parameter:
There are several parameter to change in the parameter menue:
LCD_Adress: 		    This is the Adress of the LCD modul. You can detect it by using the following command:  
			              sudo i2cdetect -y 1 or sudo i2cdetect -y 0. 
                    Default 0x27
LCD_Multidisplay: 	Changes between the 2 modes. On means the Multidisplaymode is on. Off means singledisplaymode is on. 
                    Default "on".
LCD_Refresh:		    In Multidisplay mode this is the time to wait until switching to next kettle
                    Default 5 sec.
LCD_Singledisplay: 	Here you can change the kettle to be displayed in single mode. The number is the same as row number 
                    of kettles starting with 1.
                    Default is kettle 1.

If no brewing process is running it will show Craftbeer-Version, Brewery name, IP Adress and Date/Time

## Installation

Download and Install this Plugin via the CraftBeerPi user interface.

## Confiuration

Configure your i2c adress in the parameters menue
Some other parameters can be changed in the __init__.py file in the /home/pi/craftbeerpi3/modules/plugins/LCDDIsplay folder.

## Hints
After changing a LCD_xxxx parameter in the parameters menue or the file always a reboot is required. 
