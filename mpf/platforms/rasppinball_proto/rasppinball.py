"""raspPinball hardware plateform"""

import logging
#import keypad


from mpf.devices.driver import ConfiguredHwDriver
from mpf.core.platform import MatrixLightsPlatform, LedPlatform, SwitchPlatform, DriverPlatform


#class HardwarePlatform(MatrixLightsPlatform, LedPlatform, SwitchPlatform, DriverPlatform):
class HardwarePlatform(SwitchPlatform):

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

        self.config = self.machine.config['rasppinball']
        self.machine.config_validator.validate_config("rasppinball", self.config)

        #self._kp = keypad.keypad()


    def __repr__(self):
        """Return string representation."""
        return '<Platform.raspPinball>'

#    def initialize(self):
#        """Initialise connections to OPP hardware."""
#        self._poll_task = self.machine.clock.loop.create_task(self._poll_sender())
#        self._poll_task.add_done_callback(self._done)

    def get_hw_switch_states(self):
        """Get initial hardware switch states."""
        hw_states = dict()
        #k = self._kp.keypad()
        k = None
        for c in 'ABCDEFGHIJKLMNOP':
            if c in k:
                hw_states[c] = 1
            else:
                hw_states[c] = 0
        return hw_states


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

