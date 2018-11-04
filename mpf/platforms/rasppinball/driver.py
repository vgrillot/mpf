"""
RaspPinball Driver management
"""

# !!181104:VG:Creation (refactoring, splitter main unit)


import logging
from mpf.platforms.interfaces.driver_platform_interface import DriverPlatformInterface


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
        self.platform.communicator.driver_disable(coil.hw_driver.number)
        pass

    def enable(self, coil):
        """Enable this driver, which means it's held "on" indefinitely until it's explicitly disabled."""
        self.log.info("RASPDriver.Enable(%s %s)" % (coil.config['label'], coil.hw_driver.number))
        self.platform.communicator.driver_enable(coil.hw_driver.number)
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
