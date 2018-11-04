"""
RaspPinball Les management
"""

# !!181104:VG:Creation (refactoring, splitter main unit)


import logging
from mpf.platforms.interfaces.rgb_led_platform_interface import RGBLEDPlatformInterface


class RASPLed(RGBLEDPlatformInterface):

    def __init__(self, config, number, strip):
        """Initialise led."""
        self.number = number
        self.current_color = '000000'
        self.log = logging.getLogger('RASPLed')
        self.strip = strip

    def color(self, color):
        """Set the LED to the specified color.

        Args:
            color: a list of int colors. one for each channel.

        Returns:
            None
        """
        #self._color = color
        new_color = "{0}{1}{2}".format(hex(int(color[0]))[2:].zfill(2),
                                       hex(int(color[1]))[2:].zfill(2),
                                       hex(int(color[2]))[2:].zfill(2))
        #self.log.info("RASPLes.color(%s : %s -> %s)" % (self.number, color, new_color))
        #print("color(%s -> %s)" % (self.number, new_color))
        try:
            self.current_color = new_color
            #self.strip.setPixelColor(int(self.number), self.current_color)
            self.strip.setPixelColorRGB(int(self.number), color[0], color[1], color[2])

            self.strip.updated = True
        except Exception as e:
            self.log.error("led update error" + str(e))
