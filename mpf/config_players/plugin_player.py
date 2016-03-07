from mpf.core.config_player import ConfigPlayer


class PluginPlayer(ConfigPlayer):
    """Base class for a remote ConfigPlayer that is registered as a plug-in to
    MPF. This class is created on the MPF side of things.
    """

    def register_player_events(self, config, mode=None, priority=0):
        """ Overrides this method in the base class and registers the
        config_player events to send the trigger via BCP instead of calling
        the local play() method.

        """
        event_list = list()

        for event, settings in config.items():
            self.machine.bcp.add_registered_trigger_event(event)
            event_list.append(event)

        return self.unload_player_events, event_list

    def unload_player_events(self, event_list):
        for event in event_list:
            self.machine.bcp.remove_registered_trigger_event(event)

    def play(self, settings, mode=None, caller=None, **kwargs):
        """Only used during shows."""
        self.machine.bcp.bcp_trigger(name='{}_play'.format(self.show_section),
                                     **settings)
