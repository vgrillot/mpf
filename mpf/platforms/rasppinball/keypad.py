# #####################################################
# Python Library for 3x4 matrix keypad using
# 7 of the avialable GPIO pins on the Raspberry Pi. 
# 
# This could easily be expanded to handle a 4x4 but I 
# don't have one for testing. The KEYPAD constant 
# would need to be updated. Also the setting/checking
# of the colVal part would need to be expanded to 
# handle the extra column.
# 
# Written by Chris Crumpacker
# May 2013
#
# main structure is adapted from Bandono's
# matrixQPI which is wiringPi based.
# https://github.com/bandono/matrixQPi?source=cc
# #####################################################

import RPi.GPIO as GPIO

class Keypad():
    # CONSTANTS   
    KEYPAD = [
    ['A', 'B', 'C', 'D'],
    ['E', 'F', 'G', 'H'],
    ['I', 'J', 'K', 'L'],
    ['M', 'N', 'O', 'P']
    ]
    
    ROW         = [21, 20, 26, 19]
    COLUMN      = [16, 13, 6, 12]
    
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
    

    def getKey(self):
        
        # Set all columns as output low
        for j in range(len(self.COLUMN)):
            GPIO.setup(self.COLUMN[j], GPIO.OUT)
            GPIO.output(self.COLUMN[j], GPIO.LOW)
        
        # Set all rows as input
        for i in range(len(self.ROW)):
            GPIO.setup(self.ROW[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Scan rows for pushed key/button
        # A valid key press should set "rowVal"  between 0 and 3.
        rowVal = -1
        for i in range(len(self.ROW)):
            tmpRead = GPIO.input(self.ROW[i])
            if tmpRead == 0:
                rowVal = i
                
        # if rowVal is not 0 thru 3 then no button was pressed and we can exit
        if rowVal <0 or rowVal >3:
            self.exit()
            return
        
        # Convert columns to input
        for j in range(len(self.COLUMN)):
                GPIO.setup(self.COLUMN[j], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        # Switch the i-th row found from scan to output
        GPIO.setup(self.ROW[rowVal], GPIO.OUT)
        GPIO.output(self.ROW[rowVal], GPIO.HIGH)

        # Scan columns for still-pushed key/button
        # A valid key press should set "colVal"  between 0 and 2.
        colVal = -1
        for j in range(len(self.COLUMN)):
            tmpRead = GPIO.input(self.COLUMN[j])
            if tmpRead == 1:
                colVal=j
                
        # if colVal is not 0 thru 2 then no button was pressed and we can exit
        if colVal <0 or colVal >3:
            self.exit()
            return

        # Return the value of the key pressed
        self.exit()
        return self.KEYPAD[rowVal][colVal]



    def getKeys(self):
        result = []

        # Set all columns as output low
        for j in range(len(self.COLUMN)):
            GPIO.setup(self.COLUMN[j], GPIO.OUT)
            GPIO.output(self.COLUMN[j], GPIO.HIGH)

        # Set all rows as input
        for i in range(len(self.ROW)):
            GPIO.setup(self.ROW[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)

        #  run all the output and input now...
        for j in range(len(self.COLUMN)):
            GPIO.output(self.COLUMN[j], GPIO.LOW)
            for i in range(len(self.ROW)):
                tmpRead = GPIO.input(self.ROW[i])
                if tmpRead == 0:
                    result.append(self.KEYPAD[i][j])
            GPIO.output(self.COLUMN[j], GPIO.HIGH)

        # Scan rows for pushed key/button
        # Return the value of the key pressed
        self.exit()
        return result


    def exit(self):
        # Reinitialize all rows and columns as input at exit
        for i in range(len(self.ROW)):
                GPIO.setup(self.ROW[i], GPIO.IN, pull_up_down=GPIO.PUD_UP) 
        for j in range(len(self.COLUMN)):
                GPIO.setup(self.COLUMN[j], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
if __name__ == '__main__':
    # Initialize the keypad class
    kp = keypad()
    
    while True:
        # Loop while waiting for a keypress
        digit = None
        while digit == None:
            digit = kp.getKey()
        
        # Print the result
        print(digit) 
