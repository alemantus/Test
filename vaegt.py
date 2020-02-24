from pad4pi import rpi_gpio
from time import *
import time
from RPLCD_i2c import CharLCD
from RPLCD_i2c import Alignment, CursorMode, ShiftMode
from RPLCD_i2c import cursor, cleared
import RPi.GPIO as GPIO  # import GPIO
from hx711 import HX711
import numpy
import pandas
import sys
import os
import statistics

menuStat = 0
roomNumber = ["0","0"]
input = "safe"
stopWatch = 0
control = 0
zeroControl = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

hx = HX711(dout_pin=27, pd_sck_pin=17)
hx.set_scale_ratio(-23.264)
hx.reset()
hx.set_debug_mode(False)

command = os.popen('mount /dev/sda1 /home/pi/Documents/LCD/usb')
print(command.read())

#hx.set_reading_format("MSB", "MSB")
KEYPAD = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"]
]

ROW_PINS = [5, 6, 13, 19] # BCM numbering
COL_PINS = [26, 20, 21, 16] # BCM numbering
factory = rpi_gpio.KeypadFactory()

# Try factory.create_4_by_3_keypad
# and factory.create_4_by_4_keypad for reasonable defaults
keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS)
#mylcd = I2C_LCD_driver.lcd()
mylcd = CharLCD(address=0x3f, port=1, cols=20, rows=4, dotsize=8)

def printKey(key):
    input = key
    global input
    global stopWatch
    stopWatch = 0
    #print(key)

def resetVar():
    menuStat = 0
    control = 0
    i = 0
    stopWatch = 0
    gut = 1

# printKey will be called each time a keypad button is pressed
keypad.registerKeyPressHandler(printKey)

while 1:
    try:
        global input
        global stopWatch
        mylcd.cursor_mode = CursorMode.blink
        


        if(menuStat == 0):
            #command = os.popen('umount /home/pi/Documents/LCD/usb')
            #print(command.read())
            print("test1")
            mylcd.clear()
            mylcd.cursor_pos = (0, 0)
            mylcd.write_string("Vaerelses Nr:")
            mylcd.cursor_pos = (1, 0)
            mylcd.write_string("Drink type:")
            mylcd.cursor_pos = (3, 0)
            mylcd.write_string("Stjerne for afslut")
            mylcd.cursor_pos = (0, 14)
            menuStat = 1
            i = 0
            startWeight = 50
            mylcd.cursor_pos = (2, 0)
            mylcd.write_string("Vent venligst")
            #i tilfælde af en dårlig måling
            while(1):
                if(zeroControl == 0):
                    hx.zero()
                    time.sleep(0.1)
                    startWeight=hx.get_weight_mean(20)
                   # startWeight = hx.get_raw_data_mean(20)
                    print(startWeight)
                else:
                    break

                if(startWeight < 20 and startWeight > -20):
                    zeroControl=1
                    break

                
            mylcd.cursor_pos = (2, 0)
            mylcd.write_string("             ")
            mylcd.cursor_pos = (0, 14)
            input = "safe"
            
        elif(menuStat == 1):
            if(input.isdigit()):
                roomNumber[0+i] = input
                mylcd.cursor_pos = (0, 14+i)
                mylcd.write_string(roomNumber[0+i])
                i = i + 1
                input = "safe"
                if(i==2):
                    menuStat = 2
                    i = 0
                    mylcd.cursor_pos = (1, 14)


        elif(menuStat == 2):
            zeroControl = 0
            roomNumberInt = int(''.join(roomNumber))
            if (roomNumberInt > 56):
                menuStat = 0

            if(input == "A" or input == "B" or input == "C" or input == "D"):
                drinkType = input
                mylcd.cursor_pos = (1, 14)

                mylcd.write_string(drinkType)
                mylcd.cursor_pos = (2, 0)
                mylcd.write_string("Vent venligst")

                startWeight=hx.get_weight_mean(20)
                mylcd.cursor_pos = (2, 0)
                time.sleep(0.1)            
                mylcd.write_string("Aaben doeren      ")
                #print(startWeight)
                menuStat = 3
                #if(GPIO.input(4) == 1):
                #    menuStat = 3
                #else:
                #   while(GPIO.input(4)==0):
                #        mylcd.cursor_pos = (2, 0)                
                #        mylcd.write_string("Luk og aaben igen")


        elif(menuStat == 3):
            if(GPIO.input(4) == 0 and control == 0):
                control = 1
                
                #print("test2")
                mylcd.cursor_pos = (2, 0)
                mylcd.write_string("Doeren er aaben..")
                
            elif(GPIO.input(4) == 1 and control == 1):
                #print("test3")
                #hx.zero()
                mylcd.cursor_pos = (2, 0)
                mylcd.write_string("Vent venligst..  ")
                time.sleep(0.1)
                endWeight=hx.get_weight_mean(20)
                print("test3")
                #print(endWeight)
                compareWeight=(endWeight*(-1))/330
                #print(round(compareWeight))

                #print(compareWeight-round(compareWeight))
                #print((-1)*endWeight-330*round(compareWeight))
                #print(compareWeight%round(compareWeight))




                #if((-1)*endWeight-330*round(compareWeight)<25*round(compareWeight) and (-1)*endWeight-330*round(compareWeight)>-25*round(compareWeight)):
                if(compareWeight-round(compareWeight)<0.2 and compareWeight-round(compareWeight)>(-0.2)):
                    print(round(compareWeight))
                    mylcd.cursor_pos = (2, 0)       
                    mylcd.write_string("antal: " + str(round(compareWeight))+ " rum: " + str(roomNumberInt))
                   
                    

                    df = pandas.read_csv('/home/pi/Documents/LCD/usb/data.csv')
                    prevBill = df.loc[roomNumberInt-1, 'antal'+drinkType]
                    currentBill = prevBill+round(compareWeight)
                    df.loc[roomNumberInt-1, 'antal'+drinkType] = currentBill

                    #print((df.iloc[roomNumberInt-1,1:4].sum())*8)
                    df.to_csv('/home/pi/Documents/LCD/usb/data.csv',index=False)

                    moneyToPay= (df.iloc[roomNumberInt-1].sum()-roomNumberInt)*8
                    
                    mylcd.cursor_pos = (3, 0) 
                    mylcd.write_string("Din regning: " + str(moneyToPay) + "kr ")
                    time.sleep(1)

                    hx.zero()
                    zeroControl = 1
                   # resetVar()
                    menuStat = 0
                    control = 0
                    i = 0
                    stopWatch = 0
                    

                    
                    
                


        time.sleep(0.1)
        stopWatch = stopWatch + 0.1

        if (stopWatch > 10 and menuStat < 3):
            #resetVar()
            menuStat = 0
            control = 0
            i = 0
            stopWatch = 0
        elif(stopWatch > 20):
            menuStat = 0
            control = 0
            i = 0
            stopWatch = 0    
            #resetVar()
        
        if(input == "*"): 
            #resetVar()
            menuStat = 0
            control = 0
            i = 0
            stopWatch = 0

        if(input == "#"): 
            menuStat = 0
            control = 0
            i = 0
            stopWatch = 0
            zeroControl = 0
            


        
    except (KeyboardInterrupt, SystemExit):
        mylcd.clear()
        GPIO.cleanup()
        sys.exit()

