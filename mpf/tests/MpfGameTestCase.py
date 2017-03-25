"""Testcase to start and stop games."""
from unittest.mock import MagicMock

from mpf.tests.MpfTestCase import MpfTestCase


class MpfGameTestCase(MpfTestCase):

    """Testcase for games."""

    def __init__(self, methodName):
        """Patch minimal config into machine."""
        super().__init__(methodName)
        self.machine_config_patches['switches'] = dict()
        self.machine_config_patches['switches']['s_start'] = {"number": "", "tags": "start"}

    def start_two_player_game(self):
        """Start two player game."""
        self.start_game()
        self.add_player()

    def fill_troughs(self):
        """Fill all troughs."""
        for trough in self.machine.ball_devices.items_tagged("trough"):
            for switch in trough.config['ball_switches']:
                self.hit_switch_and_run(switch.name, 0)

        self.advance_time_and_run()

    def start_game(self):
        # game start should work
        self.assertGameIsNotRunning()
        self.hit_and_release_switch("s_start")
        self.advance_time_and_run()
        self.assertGameIsRunning()
        self.assertEqual(1, self.machine.game.num_players)
        self.assertPlayerNumber(1)

    def add_player(self):
        # add another player
        prev_players = self.machine.game.num_players
        self.hit_and_release_switch("s_start")
        self.advance_time_and_run(1)
        self.assertEqual(prev_players + 1, self.machine.game.num_players)

    def assertBallNumber(self, number):
        self.assertEqual(number, self.machine.game.player.ball)

    def drain_ball(self):
        self.machine.game.balls_in_play = 0
        self.advance_time_and_run()

    def assertPlayerNumber(self, number):
        self.assertEqual(number, self.machine.game.player.index + 1)

    def stop_game(self):
        # stop game
        self.assertGameIsRunning()
        self.machine.game.game_ending()
        self.advance_time_and_run()
        self.assertGameIsNotRunning()

    def assertGameIsRunning(self):
        self.assertIsNotNone(self.machine.game)

    def assertGameIsNotRunning(self):
        self.assertIsNone(self.machine.game)
