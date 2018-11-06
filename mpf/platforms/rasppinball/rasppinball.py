"""raspPinball hardware platform"""

import sys


import logging
import asyncio
import time

from mpf.platforms.rasppinball.keypad import Keypad

from mpf.devices.driver import ConfiguredHwDriver
from mpf.core.platform import MatrixLightsPlatform, LedPlatform, SwitchPlatform, DriverPlatform

try:
    from neopixel import neopixel #don't find it on raspberry
except ImportError:
    sys.path.insert(0, '/home/sysop/pinball/led2/python/build/lib.linux-armv7l-3.4')
    from neopixel import * # ok sur raspberry


from mpf.platforms.rasppinball.driver import RASPDriver
from mpf.platforms.rasppinball.switch import RASPSwitch
from mpf.platforms.rasppinball.led import RASPLed
from mpf.platforms.rasppinball.serial import RaspSerialCommunicator

class HardwarePlatform(SwitchPlatform, DriverPlatform, LedPlatform):
    """Platform class for the raspPinball hardware.

    Args:
        machine: The main ``MachineController`` instance.

    """

    def __init__(self, machine):
        """Initialise raspPinball platform."""
        # super(HardwarePlatform, self).__init__(machine)
        super().__init__(machine)
        self.log = logging.getLogger('RASPPINBALL')
        self.log.info("Configuring raspPinball hardware.")
        self._poll_task = None
        self.strips = dict()
        self.switches = dict()
        self.drivers = dict()
        self.leds = dict()
        #self.serial_connections = dict()
        self.communicator = None
        self.init_done = False

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

        self._connect_to_hardware()

        #  keypad
        self._kp = Keypad()
        self.old_key = ""
        self.key = ""
        #  leds
        self.init_strips()
        self.init_done = True

    def stop(self):
        #!!170723:add msg halt platform
        self.communicator.msg_halt_platform()

    def init_strips(self):
        """read strips config and init objects"""
        #!!161126:VG:init_strips
        # read only one for now...
        #self.machine.config_validator.validate_config("rasp_strip_leds", rasp_strip_leds)
        #strip_config = self.config
        #self.strip = neopixel.Adafruit_NeoPixel(
        #    strip_config['count'], strip_config['pin'], strip_config['freq'], strip_config['dma'],
        #    strip_config['invert'], strip_config['brightness'])

        #self.strip = Adafruit_NeoPixel(64, 18, 800000, 5, False, 255)
        self.strip = Adafruit_NeoPixel(64, 10, 800000, 5, False, 255)
        # Intialize the library (must be called once before other functions).
        self.strip.begin()
        #self.strips[strip_name] = self.strip
        self.strip.updated = False

    def update_kb(self):
        s = self._kp.getKeys()
        if s != self.old_key:
            #print("Keys:%s" % s)

            #   disable sw
            for num, sw in self.switches.items():
                if (num in self.old_key) and (not num in s):
                    #print ("%s OFF" % num)
                    self.machine.switch_controller.process_switch_by_num(sw.number, state=0, platform=self, logical=False)

            for num, sw in self.switches.items():
                if (not num in self.old_key) and (num in s):
                    #print ("%s ON" % num)
                    self.machine.switch_controller.process_switch_by_num(sw.number, state=1, platform=self, logical=False)

            self.old_key = s

    def tick(self, dt):
        """check with tick..."""
        del dt
        self.update_kb()

        #if self.strip.updated:
        #    self.strip.updated = False
        self.strip.show()

        #  resent frame not acked by Arduino
        self.communicator.resent_frames()

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

    def _get_pulse_ms_value(self, coil):
        if coil.config['pulse_ms']:
            return coil.config['pulse_ms']
        else:
            # use mpf default_pulse_ms
            return self.machine.config['mpf']['default_pulse_ms']

    def configure_switch(self, config: dict):
        """Configure a switch.

        Args:
            config: Config dict.
        """
        number = config['number']
        self.log.debug("configure_switch(%s)" % number)
        switch = RASPSwitch(config, number)
        self.switches[number] = switch
        return switch

    def configure_driver(self, config: dict):
        """Configure a driver.

        Args:
            config: Config dict.
        """
        #print(config)
        number = config['number']
        self.log.debug("configure_driver(%s)" % (number))
        driver = RASPDriver(config, number, self)
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
        self.log.debug("configure_led(%s)" % number)
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
        self.log.info("clear_hw_rule(coil=%s sw=%s)" %
                       (coil.hw_driver.number, switch.hw_switch.number))
        self.communicator.rule_clear(coil.hw_driver.number, switch.hw_switch.number)

    def set_pulse_on_hit_rule(self, enable_switch, coil):
        """Set pulse on hit rule on driver.

        Pulses a driver when a switch is hit. When the switch is released the pulse continues. Typically used for
        autofire coils such as pop bumpers.
        """
        self.log.info("set_pulse_on_hit_rule(coil=%s sw=%s)" %
                       (coil.hw_driver.number, enable_switch.hw_switch.number))
        self.communicator.rule_add(1, coil.hw_driver.number, enable_switch.hw_switch.number, 
                                   duration=self._get_pulse_ms_value(coil))

    def set_pulse_on_hit_and_release_rule(self, enable_switch, coil):
        """Set pulse on hit and release rule to driver.

        Pulses a driver when a switch is hit. When the switch is released the pulse is canceled. Typically used on
        the main coil for dual coil flippers without eos switch.
        """
        self.log.info("set_pulse_on_hit_and_release_rule(coil=%s sw=%s)" %
                       (coil.hw_driver.number, enable_switch.hw_switch.number))
        self.communicator.rule_add(2, coil.hw_driver.number, enable_switch.hw_switch.number,
                                   duration=self._get_pulse_ms_value(coil))

    def set_pulse_on_hit_and_enable_and_release_rule(self, enable_switch, coil):
        """Set pulse on hit and enable and relase rule on driver.

        Pulses a driver when a switch is hit. Then enables the driver (may be with pwm). When the switch is released
        the pulse is canceled and the driver gets disabled. Typically used for single coil flippers.
        """
        self.log.info("set_pulse_on_hit_and_enable_and_release_rule(coil=%s sw=%s)" %
                       (coil.hw_driver.number, enable_switch.hw_switch.number))
        self.communicator.rule_add(3, coil.hw_driver.number, enable_switch.hw_switch.number,
                                   duration=self._get_pulse_ms_value(coil))

    def set_pulse_on_hit_and_enable_and_release_and_disable_rule(self, enable_switch, disable_switch, coil):
        """Set pulse on hit and enable and release and disable rule on driver.

    Pulses a driver when a switch is hit. Then enables the driver (may be with pwm). When the switch is released
        the pulse is canceled and the driver gets disabled. When the second disable_switch is hit the pulse is canceled
        and the driver gets disabled. Typically used on the main coil for dual coil flippers with eos switch.
        """
        self.log.info("set_pulse_on_hit_and_enable_and_release_and_disable_rule(coil=%s sw=%s dis_sw=%s)" %
                       (coil.hw_driver.number, enable_switch.hw_switch.number, disable_switch.hw_switch.number))
        self.communicator.rule_add(4, coil.hw_driver.number, enable_switch.hw_switch.number, disable_sw_id=disable_switch.hw_switch.number,
                                   duration=self._get_pulse_ms_value(coil))

    def _connect_to_hardware(self):
        """Connect to each port from the config.

        This process will cause the connection threads to figure out which processor they've connected to
        and to register themselves.
        """
        if False:  # !!!TEMP:need to validate config...
            if len(self.config['ports']) > 1:
                self.log.fatal("only one slave com port is supported")
            if len(self.config['ports']) == 0:
                self.log.warning("no communication port setted!")
                return
            port = self.config['ports'][0]
            self.communicator = RaspSerialCommunicator(
                platform=self, port=port,
                baud=self.config['baud'])
        self.communicator = RaspSerialCommunicator(
            platform=self, port='/dev/ttyAMA0',
            baud=115200)
        self.communicator.msg_init_platform()

    def process_received_message(self, msg: str):
        """Send an incoming message from the FAST controller to the proper method for servicing.

        Args:
            msg: messaged which was received
        """

        if not self.init_done:
            return  # init incomplete, don't try to process anything...

        all = msg.split(":")
        if len(all) < 2:
            self.log.warning("Recv bad formated cmd", msg)
            return
        cmd, all_param = all[:2]
        params = all_param.split(";")

        self.strip.setPixelColorRGB(0, 0, 0, 0)
        if cmd == "":
            pass

        elif cmd == "SWU":      # switch update
            sw_id = params[0]
            sw_state = int(params[1])
            if not self.switches:
                self.log.error("SWU:switches not configured")
            else:
                self.machine.switch_controller.process_switch_by_num(sw_id, state=sw_state, platform=self, logical=False)
                self.strip.setPixelColorRGB(0, 0, 0, 0xff)  # blue

        elif cmd == "DBG":      # debug message
            self.log.debug("RECV:%s" % msg)

        elif cmd == "INF":      # information message
            self.log.info("RECV:%s" % msg)

        elif cmd == "WRN":  # warning message
            self.log.warning("RECV:%s" % msg)
            self.strip.setPixelColorRGB(0, 0xff, 0xff, 0)  # yellow

        elif cmd == "ERR":  # error message
            self.log.error("RECV:%s" % msg)
            self.strip.setPixelColorRGB(0, 0xff, 0, 0)  # red

        elif cmd == "TCK":  # arduino is alive !
            self.log.debug("TCK ok:%d" % int(params[0]))

        elif cmd == "ACK":  # ack of frame
            self.communicator.ack_frame(int(params[0]), params[1] == "OK")
            self.strip.setPixelColorRGB(0, 0, 0xff, 0)  # green

        else:
            self.log.warning("RECV:UNKNOWN FRAME: [%s]" % msg)

        l = len(self.communicator.frames)
        #TODO: self.machine['frame_cnt'] = l
        self.strip.show()
        self.machine.events.post_async('raspberry_frame_count', frame_cnt=l, frames=self.communicator.frames)
   












