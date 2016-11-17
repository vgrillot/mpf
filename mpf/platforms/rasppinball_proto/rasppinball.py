"""raspPinball hardware plateform"""

import logging
from mpf.platforms.rasppinball.keypad import keypad


from mpf.devices.driver import ConfiguredHwDriver
from mpf.core.platform import MatrixLightsPlatform, LedPlatform, SwitchPlatform, DriverPlatform


#class HardwarePlatform(MatrixLightsPlatform, LedPlatform, SwitchPlatform, DriverPlatform):
class HardwarePlatform(SwitchPlatform, DriverPlatform):

    """Platform class for the OPP hardware.

    Args:
        machine: The main ``MachineController`` instance.

    """

    def __init__(self, machine):
        """Initialise OPP platform."""
        super(HardwarePlatform, self).__init__(machine)
        self.log = logging.getLogger('RASPPINBALL')
        self.log.info("Configuring raspPinball hardware.")

        self._poll_task = None
        self.features['tickless'] = True

        #self.config = self.machine.config['rasppinball']
        #self.machine.config_validator.validate_config("rasppinball", self.config)

        self._kp = keypad()


    def __repr__(self):
        """Return string representation."""
        return '<Platform.raspPinball>'

    def initialize(self):
        """Initialise connections to raspPinball hardware."""
        pass

    def stop():
        pass

    def get_hw_switch_states(self):
        """Get initial hardware switch states."""
        hw_states = dict()
        k = self._kp.keypad()
        print (k)
        for c in 'ABCDEFGHIJKLMNOP':
            if c in k:
                hw_states[c] = 1
                print (k)
            else:
                hw_states[c] = 0
        return hw_states

    def configure_switch(self, config: dict):
        """Configure a switch.

        Args:
            config: Config dict.
        """
        print("configure_switch")
        number = self._get_dict_index(config['number'])
        return number


    def configure_driver(self, config):
        print("configure_driver")
        number = self._get_dict_index(config['number'])
        return number
        


    def clear_hw_rule(self, switch, coil):
        """Clear a hardware rule.

        This is used if you want to remove the linkage between a switch and
        some driver activity. For example, if you wanted to disable your
        flippers (so that a player pushing the flipper buttons wouldn't cause
        the flippers to flip), you'd call this method with your flipper button
        as the *sw_num*.

        """
        self.log.debug("Clearing HW Rule for switch: %s, coils: %s", switch.hw_switch.number,
                       coil.hw_driver.number)




#    @staticmethod
#    def _done(future):
#        """Evaluate result of task.
#
#        Will raise exceptions from within task.
#        """
#        future.result()

#    @asyncio.coroutine
#    def _poll_sender(self):
#        """Poll switches."""
#        while True:
#            for chain_serial in self.read_input_msg:
#                self.send_to_processor(chain_serial, self.read_input_msg[chain_serial])
#                yield from self.opp_connection[chain_serial].writer.drain()
#                # the line above saturates the link and seems to overhelm the hardware. limit it to 100Hz
#                yield from asyncio.sleep(.01, loop=self.machine.clock.loop)

