from mpf.tests.MpfTestCase import MpfTestCase


class TestScoring(MpfTestCase):

    def getConfigFile(self):
        return 'config.yaml'

    def getMachinePath(self):
        return 'tests/machine_files/scoring/'

    def test_scoring(self):
        # start game with two players
        self.machine.ball_controller.num_balls_known = 0
        self.hit_switch_and_run("s_ball_switch1", 1)
        self.advance_time_and_run(2)

        # start game with two players
        self.hit_and_release_switch("s_start")
        self.hit_and_release_switch("s_start")
        self.assertNotEqual(None, self.machine.game)
        self.assertEqual(2, self.machine.game.num_players)
        self.assertEqual(1, self.machine.game.player.number)

        self.advance_time_and_run(1)
        self.release_switch_and_run("s_ball_switch1", 20)

        self.assertFalse(self.machine.mode_controller.is_active('mode1'))

        self.post_event("test_event1")
        self.assertEqual(0, self.machine.game.player.score)
        self.assertEqual(0, self.machine.game.player.var_c)

        # start mode 1
        self.post_event('start_mode1')
        self.assertTrue(self.machine.mode_controller.is_active('mode1'))

        self.post_event("test_add_machine_var")
        self.machine_run()
        self.assertMachineVarEqual(23, "my_var")

        self.post_event("test_set_machine_var")
        self.machine_run()
        self.assertMachineVarEqual(100, "my_var")

        self.post_event("test_add_machine_var")
        self.machine_run()
        self.assertMachineVarEqual(123, "my_var")

        # test setting string
        self.post_event('test_set_string')
        self.assertEqual('HELLO', self.machine.game.player.string_test)

        # event should score 100 now
        self.post_event("test_event1")
        self.assertEqual(100, self.machine.game.player.score)
        self.assertEqual(1, self.machine.game.player.vars['var_a'])
        self.assertEqual(0, self.machine.game.player.var_c)
        self.machine.game.player.ramps = 3
        self.assertMachineVarEqual(100, "my_var2")

        self.post_event("test_event1")
        self.assertEqual(200, self.machine.game.player.score)
        self.assertEqual(2, self.machine.game.player.vars['var_a'])
        self.assertEqual(3, self.machine.game.player.var_c)
        self.assertMachineVarEqual(200, "my_var2")

        self.post_event("test_set_100")
        self.assertEqual(100, self.machine.game.player.test1)
        self.post_event("test_set_200")
        self.assertEqual(200, self.machine.game.player.test1)
        self.post_event("test_set_100")
        self.assertEqual(100, self.machine.game.player.test1)

        # start mode 2
        self.post_event('start_mode2')
        self.assertTrue(self.machine.mode_controller.is_active('mode2'))

        # event should score 1000 now (and block the 100 from mode1)
        self.post_event("test_event1")
        self.assertEqual(1200, self.machine.game.player.score)
        # var_a is blocked
        self.assertEqual(2, self.machine.game.player.vars['var_a'])
        # but we count var_b
        self.assertEqual(1, self.machine.game.player.vars['var_b'])
        self.assertEqual(33, self.machine.game.player.var_c)

        # switch players
        self.hit_switch_and_run("s_ball_switch1", 1)
        self.release_switch_and_run("s_ball_switch1", 20)
        self.assertEqual(2, self.machine.game.player.number)

        self.assertEqual(0, self.machine.game.player.score)

        # modes should be unloaded
        self.assertFalse(self.machine.mode_controller.is_active('mode1'))
        self.assertFalse(self.machine.mode_controller.is_active('mode2'))

        # mode is unloaded. should not score
        self.post_event("test_event1")
        self.assertEqual(0, self.machine.game.player.score)

        # load mode two
        self.post_event('start_mode2')
        self.assertTrue(self.machine.mode_controller.is_active('mode2'))

        self.post_event("test_event1")
        self.assertEqual(1000, self.machine.game.player.score)
        # var_a is 0
        self.assertEqual(0, self.machine.game.player.var_a)
        # but we count var_b
        self.assertEqual(1, self.machine.game.player.vars['var_b'])

        # switch players again
        self.hit_switch_and_run("s_ball_switch1", 1)
        self.release_switch_and_run("s_ball_switch1", 20)
        self.assertEqual(1, self.machine.game.player.number)

        # mode2 should auto start
        self.assertFalse(self.machine.mode_controller.is_active('mode1'))
        self.assertTrue(self.machine.mode_controller.is_active('mode2'))
        self.assertTrue(self.machine.modes.mode2.active)

        # same score as during last ball
        self.assertEqual(1200, self.machine.game.player.score)
        self.assertEqual(2, self.machine.game.player.vars['var_a'])
        self.assertEqual(1, self.machine.game.player.vars['var_b'])

        # should still score 1000 points
        self.post_event("test_event1")
        self.assertEqual(2200, self.machine.game.player.score)
        self.assertEqual(2, self.machine.game.player.vars['var_a'])
        self.assertEqual(2, self.machine.game.player.vars['var_b'])

        self.post_event("start_mode3")
        self.advance_time_and_run()

        self.assertPlayerVarEqual(2200, "score")
        self.assertEqual(1000, self.machine.game.player_list[1].score)
        self.post_event("score_player2")
        self.assertPlayerVarEqual(2200, "score")
        self.assertEqual(1023, self.machine.game.player_list[1].score)

        self.post_event("score_player1")
        self.assertPlayerVarEqual(2242, "score")
        self.assertEqual(1023, self.machine.game.player_list[1].score)

        self.post_event("reset_player2")
        self.assertPlayerVarEqual(2242, "score")
        self.assertEqual(10, self.machine.game.player_list[1].score)

        # stop game and mode
        self.machine.service.start_service()
        self.advance_time_and_run()

        # it should not crash
        self.post_event("test_event1")
        self.advance_time_and_run()
