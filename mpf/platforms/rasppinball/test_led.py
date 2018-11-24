"""raspPinball hardware platform"""

import sys
sys.path.insert(0, '/home/sysop/pinball/led2/python/build/lib.linux-armv7l-3.4')


import logging
import asyncio
import time

#try:
#    from mpf.platforms.raspinball.neopixel import *  # don't find it on raspberry
#except ImportError:
#from neopixel import * # ok sur raspberry


from neopixel import * # ok sur raspberry


def test_led():
    strip = Adafruit_NeoPixel(64, 10, 800000, 5, False, 255)
    strip.begin()
    for i in range(0, 50):
        strip.setPixelColorRGB(0, 0, 0, 0)
        strip.show()
        #sleep(5)
        strip.setPixelColorRGB(0, 0, 0xFF, 0)
        strip.show()
        #sleep(5)
    strip.setPixelColorRGB(0, 0xFF, 0, 0)
    strip.show()

if __name__ == "__main__":
    test_led()



