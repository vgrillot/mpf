"""raspPinball hardware plateform"""

import logging
import asyncio

from mpf.platforms.rasppinball.keypad import Keypad

from mpf.devices.driver import ConfiguredHwDriver
from mpf.core.platform import MatrixLightsPlatform, LedPlatform, SwitchPlatform, DriverPlatform
from mpf.platforms.interfaces.switch_platform_interface import SwitchPlatformInterface
from mpf.platforms.interfaces.driver_platform_interface import DriverPlatformInterface
from mpf.platforms.interfaces.rgb_led_platform_interface import RGBLEDPlatformInterface
from mpf.platforms.base_serial_communicator import BaseSerialCommunicator

from neopixel import * # ok sur raspberry
#from neopixel import neopixel #don't find it on raspberry


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
        #self.serial_connections = dict()
        self.communicator = None

    def __repr__(self):
        """Return string representation."""
        return '<Platform.raspPinball>'

    def initialize(self):
        """Initialise connections to raspPinball hardware."""
        self.log.info("Initialize raspPinball hardware.")

        self.config = self.machine.config['rasppinball']
        self.machine.config_validator.validate_config("rasppinball", self.config)
        print("***************************")
        print(self.config)
        #self.machine_type = (
        #    self.machine.config['hardware']['driverboards'].lower())

        self._connect_to_hardware()


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
        #print(config)
        number = config['number']
        self.log.debug("configure_switch(%s)" % (number))
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

    def process_received_message(self, msg: str):
        """Send an incoming message from the FAST controller to the proper method for servicing.

        Args:
            msg: messaged which was received
        """
        all = msg.split(":")
        if len(all) < 2:
          self.log.warning("Recv bad formated cmd", msg)
          return
        cmd, all_param = all[:2]
        params = all_param.split(";")

        if cmd == "":
            pass
        elif cmd == "SWU":      # switch update
            sw_id = params[0]
            sw_state = int(params[1])
            self.machine.switch_controller.process_switch_by_num(sw_id, state=sw_state, platform=self, logical=False)
        elif cmd == "DBG":      # debug message
            self.log.debug("RECV:%s" % msg)
        elif cmd == "INF":      # debug message
            self.log.info("RECV:%s" % msg)
        elif cmd == "WRN":  # warning message
            self.log.warning("RECV:%s" % msg)
        elif cmd == "ERR":  # warning message
            self.log.error("RECV:%s" % msg)
        elif cmd == "TCK": # arduino is alive !
            self.log.debug("TCK ok:%d" % int(params[0]))
        else:
            self.log.warning("RECV:UNKNOWN FRAME: [%s]" % msg)




class RASPDriver(DriverPlatformInterface):

    def __init__(self, config, number, platform):
        """Initialise driver."""
        super().__init__(config, number)
        self.platform = platform
        self.log = logging.getLogger('RASPDriver')
        self.log.info("Driver Settings for %s", self.number)

    def disable(self, coil):
        """Disable the driver."""
        self.log.info("RASPDriver.Disable(%s %s)" % (coil.config['label'], coil.hw_driver.number))
        self.platform.communicator.driver_disable(self, coil.hw_driver.number)
        pass

    def enable(self, coil):
        """Enable this driver, which means it's held "on" indefinitely until it's explicitly disabled."""
        self.log.info("RASPDriver.Enable(%s %s)" % (coil.config['label'], coil.hw_driver.number))
        self.platform.communicator.driver_enable(self, coil.hw_driver.number)
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
        self.platform.communicator.driver_pulse(coil.hw_driver.number, milliseconds)
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
        #self.log.info("RASPLes.color(%s : %s -> %s)" % (self.number, color, new_color))
        #print("color(%s -> %s)" % (self.number, new_color))
        try:
            self.current_color = new_color
            #self.strip.setPixelColor(int(self.number), self.current_color)
            self.strip.setPixelColorRGB(int(self.number), color[0], color[1], color[2])

            self.strip.updated = True
        except Exception as e:
            self.log.error("led update error" + str(e))



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
        try:
          self.received_msg += msg.decode()
        except:
          self.log.warning("invalid parse frame '%s'" % msg)

        while True:
            pos = self.received_msg.find('\r')
            if pos == -1: # no full msg
                break
            m = self.received_msg[:pos].strip()
            if not len(m):
                break
            self.platform.process_received_message(m)
            self.received_msg = self.received_msg[pos + 1:]

    @asyncio.coroutine
    def _identify_connection(self):
        """Initialise and identify connection."""
        pass #nothing to identify...
        #raise NotImplementedError("Implement!")

    def __send_msg(self, s):
      s = "!%s:" % s
      self.log.info('SEND:%s' % s)
      self.send(s.encode())
   
    def rule_clear(self, coil_pin, enable_sw_id):
        msg = "RC:%s:%s" % (coil_pin, enable_sw_id)
        self.__send_msg(msg)

    def rule_add(self, hwrule_type, coil_pin, enable_sw_id='0', disable_sw_id='0', duration=10):
        msg = "RA:%d:%s:%s:%s:%d" % (hwrule_type, coil_pin, enable_sw_id, disable_sw_id, duration)
        self.__send_msg(msg)

    def driver_pulse(self, coil_pin, duration):
        #!!170418:VG:Add duration
        msg = "DP:%s:%d" % (coil_pin, duration)
        self.__send_msg(msg)

    def driver_enable(self, coil_pin):
        msg = "DE:%s" % (coil_pin)
        self.__send_msg(msg)

    def driver_disable(self, coil_pin):
        msg = "DD:%s" % (coil_pin)
        self.__send_msg(msg)




