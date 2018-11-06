"""
RaspPinball Switch management
"""

# !!181104:VG:Creation (refactoring, splitter main unit)


import logging
from mpf.platforms.interfaces.switch_platform_interface import SwitchPlatformInterface


class RASPSwitch(SwitchPlatformInterface):

    def __init__(self, config, number):
        """Initialise switch."""
        super().__init__(config, number)
        self.log = logging.getLogger('RASPSwitch')
        self.log.info("Switch settings for %s", self.number)

        #self.notify_on_nondebounce = notify_on_nondebounce
        #self.hw_rules = {"closed_debounced": [],
        #                 "closed_nondebounced": [],
        #                 "open_debounced": [],
        #                 "open_nondebounced": []}
