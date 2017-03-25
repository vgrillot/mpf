"""raspPinball hardware plateform"""

import logging
from mpf.platforms.rasppinball.keypad import Keypad

from mpf.devices.driver import ConfiguredHwDriver
from mpf.core.platform import MatrixLightsPlatform, LedPlatform, SwitchPlatform, DriverPlatform
from mpf.platforms.interfaces.switch_platform_interface import SwitchPlatformInterface
from mpf.platforms.interfaces.driver_platform_interface import DriverPlatformInterface
from mpf.platforms.interfaces.rgb_led_platform_interface import RGBLEDPlatformInterface
from mpf.platforms.base_serial_communicator import BaseSerialCommunicator

#from neopixel import *
from neopixel import neopixel


#class HardwarePlatform(MatrixLightsPlatform, LedPlatform, SwitchPlatform, DriverPlatform):
class HardwarePlatform(SwitchPlatform, DriverPlatform, LedPlatform):
    """Platform class for the raspPinball hardware.

    Args:
        machine: The main ``MachineController`` instance.

    """

    okey = None
    osw = None
    fake_keys = [" ", "H", "AH", "H", " ", "M", " ", "I", "J", "I", " ", "J", "I", " ", "J", "K", " ",  "N", " ", "M", "H", "H"]
    fake_idx = 0
    fake_cnt = 0


    def __init__(self, machine):
        """Initialise raspPinball platform."""
        super(HardwarePlatform, self).__init__(machine)
        self.log = logging.getLogger('RASPPINBALL')
        self.log.info("Configuring raspPinball hardware.")
        self._poll_task = None
        self.strips = dict()
        self.switches = dict()
        self.drivers = dict()
        self.leds = dict()
        self.serial_connections = dict()

    def __repr__(self):
        """Return string representation."""
        return '<Platform.raspPinball>'

    def initialize(self):
        """Initialise connections to raspPinball hardware."""
        self.log.info("Initialize raspPinball hardware.")

        self.config = self.machine.config['rasppinball']
        self.machine.config_validator.validate_config("rasppinball", self.config)
        #self.machine_type = (
        #    self.machine.config['hardware']['driverboards'].lower())


        #  keypad
        self._kp = Keypad()
        self.old_key = ""
        self.key = ""
        #  leds
        self.init_strips()

    def stop(self):
        # TODO: send a stop to arduino
        pass

    def init_strips(self):
        """read strips config and init objects"""
        #!!161126:VG:init_strips
        # read only one for now...
        #self.machine.config_validator.validate_config("rasp_strip_leds", rasp_strip_leds)
        #strip_config = self.config
        #self.strip = neopixel.Adafruit_NeoPixel(
        #    strip_config['count'], strip_config['pin'], strip_config['freq'], strip_config['dma'],
        #    strip_config['invert'], strip_config['brightness'])

        self.strip = Adafruit_NeoPixel(64, 18, 800000, 5, False, 255)
        # Intialize the library (must be called once before other functions).
        self.strip.begin()
        #self.strips[strip_name] = self.strip
        self.strip.updated = False

    def fake_keypad(self):
        c = self.fake_keys[self.fake_idx]

        if c == ' ':
            max = 800
        else:
            max = 10

        self.fake_cnt += 1
        if self.fake_cnt > max:
            self.fake_cnt = 0
            self.fake_idx += 1

        try:
            c = self.fake_keys[self.fake_idx]
        except:
            c = " "
            self.fake_idx = 0

        return c

    def update_kb(self):
        s = self._kp.getKeys()
        #self.key = ""
        #s = self.fake_keypad()
        #if len(s) > 0:
        #    self.log.info(s)
        #    print("KB:", s)
        if s != self.old_key:
            #print("Keys:%s" % s)

            #   disable sw
            for num, sw in self.switches.items():
                if (num in self.old_key) and (not num in s):
                    print ("%s OFF" % num)
                    self.machine.switch_controller.process_switch_by_num(sw.number, state=0, platform=self, logical=False)

            for num, sw in self.switches.items():
                if (not num in self.old_key) and (num in s):
                    print ("%s ON" % num)
                    self.machine.switch_controller.process_switch_by_num(sw.number, state=1, platform=self, logical=False)

            self.old_key = s


    def tick(self, dt):
        """check with tick..."""
        del dt
        self.update_kb()

        if self.strip.updated:
            self.strip.updated = False
            self.strip.show()


    def get_hw_switch_states(self):
        """Get initial hardware switch states."""
        hw_states = dict()
        #k = self._kp.keypad()
        k = ""
        for number, sw in self.switches.items():
            if number == k:
                hw_states[number] = 1
            else:
                hw_states[number] = 0
        return hw_states


    def configure_switch(self, config: dict):
        """Configure a switch.

        Args:
            config: Config dict.
        """
        #print(config)
        number = config['number']
        print("configure_switch(%s)" % (number))
        switch = RASPSwitch(config, number)
        self.switches[number] = switch
        return switch


    #def configure_driver(self, config):
    def configure_driver(self, config: dict):
        """Configure a driver.

        Args:
            config: Config dict.
        """
        #print(config)
        number = config['number']
        print("configure_driver(%s)" % (number))
        driver = RASPDriver(config, number)
        self.drivers[number] = driver
        return driver


    def configure_led(self, config, channels):
        """Subclass this method in a platform module to configure an LED.

        This method should return a reference to the LED's platform interface
        object which will be called to access the hardware.

        Args:
            channels (int): Number of channels (typically 3 for RGB).
            config (dict): Config of LED.

        """
        number = config['number']
        print("configure_led(%s)" % number)
        #strip = self.strips[0]
        strip = self.strip
        led = RASPLed(config, number, strip)
        self.leds[number] = led
        return led


    def clear_hw_rule(self, switch, coil):
        """Clear a hardware rule.

        This is used if you want to remove the linkage between a switch and
        some driver activity. For example, if you wanted to disable your
        flippers (so that a player pushing the flipper buttons wouldn't cause
        the flippers to flip), you'd call this method with your flipper button
        as the *sw_num*.

        """
        self.log.info("clear_hw_rule(%s %s %s)" %
                       (switch.hw_switch.number, coil.config['label'], coil.hw_driver.number))
        #raise NotImplementedError
        pass

    def set_pulse_on_hit_rule(self, enable_switch, coil):
        """Set pulse on hit rule on driver.

        Pulses a driver when a switch is hit. When the switch is released the pulse continues. Typically used for
        autofire coils such as pop bumpers.
        """
        self.log.info("set_pulse_on_hit_rule(%s %s %s)" %
                       (enable_switch.hw_switch.number, coil.config['label'], coil.hw_driver.number))
        #raise NotImplementedError
        pass

    def set_pulse_on_hit_and_release_rule(self, enable_switch, coil):
        """Set pulse on hit and release rule to driver.

        Pulses a driver when a switch is hit. When the switch is released the pulse is canceled. Typically used on
        the main coil for dual coil flippers without eos switch.
        """
        self.log.info("set_pulse_on_hit_and_release_rule(%s %s %s)" %
                       (enable_switch.hw_switch.number, coil.config['label'], coil.hw_driver.number))
        #raise NotImplementedError
        pass

    def set_pulse_on_hit_and_enable_and_release_rule(self, enable_switch, coil):
        """Set pulse on hit and enable and relase rule on driver.

        Pulses a driver when a switch is hit. Then enables the driver (may be with pwm). When the switch is released
        the pulse is canceled and the driver gets disabled. Typically used for single coil flippers.
        """
        self.log.info("set_pulse_on_hit_and_enable_and_release_rule(%s %s %s)" %
                       (enable_switch.hw_switch.number, coil.config['label'], coil.hw_driver.number))
        #raise NotImplementedError
        pass

    def set_pulse_on_hit_and_enable_and_release_and_disable_rule(self, enable_switch, disable_switch, coil):
        """Set pulse on hit and enable and release and disable rule on driver.

    Pulses a driver when a switch is hit. Then enables the driver (may be with pwm). When the switch is released
        the pulse is canceled and the driver gets disabled. When the second disable_switch is hit the pulse is canceled
        and the driver gets disabled. Typically used on the main coil for dual coil flippers with eos switch.
        """
        self.log.info("set_pulse_on_hit_and_enable_and_release_and_disable_rule(%s %s %s %s)" %
                       (enable_switch.hw_switch.number, disable_switch.hw_switch.number, coil.config['label'], coil.hw_driver.number))
        #raise NotImplementedError
        pass


    def _connect_to_hardware(self):
        """Connect to each port from the config.

        This process will cause the connection threads to figure out which processor they've connected to
        and to register themselves.
        """
        for port in self.config['ports']:
            self.serial_connections.add(RaspSerialCommunicator(
                platform=self, port=port,
                baud=self.config['baud']))


class RASPDriver(DriverPlatformInterface):

    def __init__(self, config, number):
        """Initialise driver."""
        super().__init__(config, number)
        self.log = logging.getLogger('RASPDriver')
        #self.proc = platform.proc
        #self.machine = platform.machine
        #self.pdbconfig = getattr(platform, "pdbconfig", None)

        self.log.info("Driver Settings for %s", self.number)

    def disable(self, coil):
        """Disable the driver."""
        self.log.info("RASPDriver.Disable(%s %s)" % (coil.config['label'], coil.hw_driver.number))
        pass

    def enable(self, coil):
        """Enable this driver, which means it's held "on" indefinitely until it's explicitly disabled."""
        self.log.info("RASPDriver.Enable(%s %s)" % (coil.config['label'], coil.hw_driver.number))
        pass

    def get_board_name(self):
        """Return the name of the board of this driver."""
        pass

    def pulse(self, coil, milliseconds):
        """Pulse a driver.

        Pulse this driver for a pre-determined amount of time, after which
        this driver is turned off automatically. Note that on most platforms,
        pulse times are a max of 255ms. (Beyond that MPF will send separate
        enable() and disable() commands.

        Args:
            milliseconds: The number of ms to pulse this driver for. You should
                raise a ValueError if the value is out of range for your
                platform.

        Returns:
            A integer of the actual time this driver is going to be pulsed for.
            MPF uses this for timing in certain situations to make sure too
            many drivers aren't activated at once.

        """
        self.log.info("RASPDriver.Pulse(%s %s, %d ms)" %
                       (coil.config['label'], coil.hw_driver.number, milliseconds))
        return milliseconds


class RASPSwitch(SwitchPlatformInterface):

    def __init__(self, config, number):
        """Initialise switch."""
        super().__init__(config, number)
        self.log = logging.getLogger('RASPSwitch')
        #self.notify_on_nondebounce = notify_on_nondebounce
        #self.hw_rules = {"closed_debounced": [],
        #                 "closed_nondebounced": [],
        #                 "open_debounced": [],
        #                 "open_nondebounced": []}



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
        #self.log.info("color(%s -> %s)" % (self.number, new_color))
        #print("color(%s -> %s)" % (self.number, new_color))
        self.current_color = new_color
        self.strip.setPixelColor(self.number, self.current_color)
        self.strip.updated = True



class RaspSerialCommunicator(BaseSerialCommunicator):
    """Protocol implementation to the Arduino"""

    def __init__(self, platform, port, baud):
        """Initialise communicator.

        Args:
            platform(mpf.platforms.fast.fast.HardwarePlatform): the fast hardware platform
            port: serial port
            baud: baud rate
        """
        self.received_msg = ''
        super().__init__(platform, port, baud)



    def _parse_msg(self, msg):
        """Parse a message.

        Msg may be partial.
        Args:
            msg: Bytes of the message (part) received.
        """
        self.received_msg += msg

        while True:
            pos = self.received_msg.find(b'\r')

            # no more complete messages
            if pos == -1:
                break


    @asyncio.coroutine
    def _identify_connection(self):
        """Initialise and identify connection."""
        raise NotImplementedError("Implement!")




