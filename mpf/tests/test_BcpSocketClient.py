import unittest
from unittest.mock import MagicMock

from mpf.core.bcp.bcp_socket_client import decode_command_string, encode_command_string
from mpf.tests.MpfTestCase import MpfTestCase
from mpf.tests.loop import MockQueueSocket


class TestBcpSocketClientEncoding(unittest.TestCase):

    def test_decode_command_string(self):
        # test strings
        string_in = 'play?some_value=7&another_value=2'
        command = 'play'
        kwargs = dict(some_value='7', another_value='2')

        actual_command, actual_kwargs = decode_command_string(string_in)

        self.assertEqual(command, actual_command)
        self.assertEqual(kwargs, actual_kwargs)

        # test ints, floats, bools, and none
        string_in = 'play?some_int=int:7&some_float=float:2.0&some_none' \
                    '=NoneType:&some_true=bool:True&some_false=bool:False'
        command = 'play'
        kwargs = dict(some_int=7, some_float=2.0, some_none=None,
                      some_true=True, some_false=False)

        actual_command, actual_kwargs = decode_command_string(string_in)

        self.assertEqual(command, actual_command)
        self.assertEqual(kwargs, actual_kwargs)

    def test_encode_command_string(self):
        # test strings
        command = 'play'
        kwargs = dict(some_value='7', another_value='2')
        expected_strings = ('play?some_value=7&another_value=2',
                            'play?another_value=2&some_value=7')

        actual_string = encode_command_string(command, **kwargs)

        self.assertIn(actual_string, expected_strings)

        # test ints, floats, bools, and none
        command = 'play'
        kwargs = dict(some_int=7, some_float=2.0, some_none=None,
                      some_true=True, some_false=False)
        expected_snippets = ('play?',
                             'some_int=int:7',
                             'some_float=float:2.0',
                             'some_none=NoneType:',
                             'some_true=bool:True',
                             'some_false=bool:False')

        actual_string = encode_command_string(command, **kwargs)

        for snippet in expected_snippets:
            self.assertIn(snippet, actual_string)

    def test_json_encoding_decoding(self):
        # test with dicts
        command = 'play'
        kwargs = dict()
        kwargs['dict1'] = dict(key1='value1', key2='value2')
        kwargs['dict2'] = dict(key3='value3', key4='value4')

        encoded_string = encode_command_string(command, **kwargs)
        decoded_command, decoded_dict = decode_command_string(encoded_string)

        self.assertEqual('play', decoded_command)
        self.assertIn('dict1', decoded_dict)
        self.assertIn('dict2', decoded_dict)
        self.assertEqual(decoded_dict['dict1']['key1'], 'value1')
        self.assertEqual(decoded_dict['dict1']['key2'], 'value2')
        self.assertEqual(decoded_dict['dict2']['key3'], 'value3')
        self.assertEqual(decoded_dict['dict2']['key4'], 'value4')

        # test with list
        command = 'play'
        kwargs = dict()
        kwargs['dict1'] = dict(key1='value1', key2='value2')
        kwargs['dict2'] = list()
        kwargs['dict2'].append(dict(key3='value3', key4='value4'))
        kwargs['dict2'].append(dict(key3='value5', key4='value6'))

        encoded_string = encode_command_string(command, **kwargs)
        decoded_command, decoded_dict = decode_command_string(encoded_string)

        self.assertEqual('play', decoded_command)
        self.assertIn('dict1', decoded_dict)
        self.assertIn('dict2', decoded_dict)
        self.assertEqual(decoded_dict['dict1']['key1'], 'value1')
        self.assertEqual(decoded_dict['dict1']['key2'], 'value2')
        self.assertEqual(decoded_dict['dict2'][0],
                         dict(key3='value3', key4='value4'))
        self.assertEqual(decoded_dict['dict2'][1],
                         dict(key3='value5', key4='value6'))


class MockBcpQueueSocket(MockQueueSocket):

    """Mock Queue Socket for BCP which emulates reset."""

    def send(self, data):
        if data == b'reset\n':
            self.recv_queue.append(b'reset_complete\n')
            return len(data)
        return super().send(data)


class TestBcpSocketClient(MpfTestCase):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)

        # use normal client
        self.machine_config_patches['bcp'] = {}
        self.machine_config_patches['bcp']['servers'] = []

    def get_use_bcp(self):
        return True

    def setUp(self):
        super().setUp()
        self._bcp_client = self.machine.bcp.transport.get_named_client("local_display")

    def _mock_loop(self):
        self.client_socket = MockBcpQueueSocket()
        self.clock.mock_socket("localhost", 5050, self.client_socket)

    def testReceiveMessages(self):
        # test message with bytes
        receiver = MagicMock()
        self.machine.bcp.interface.register_command_callback("receive_bytes", receiver)
        self.client_socket.recv_queue.append(b'receive_bytes?name=default&bytes=4096\n')
        data = b'0' * 4096
        self.client_socket.recv_queue.append(data)
        self.advance_time_and_run()
        receiver.assert_called_once_with(name="default", client=self._bcp_client, rawbytes=data)
        receiver.reset_mock()

        # data and cmd in two packets
        self.client_socket.recv_queue.append(b'receive_bytes?name=defa')
        self.client_socket.recv_queue.append(b'ult&bytes=4096\n')
        data = b'0' * 4096
        self.client_socket.recv_queue.append(data[0:1000])
        self.client_socket.recv_queue.append(data[1000:])
        self.advance_time_and_run()
        receiver.assert_called_once_with(name="default", client=self._bcp_client, rawbytes=data)
        receiver.reset_mock()

        # test message without bytes
        receiver2 = MagicMock()
        self.machine.bcp.interface.register_command_callback("receive_msg", receiver2)
        self.client_socket.recv_queue.append(b'receive_msg?param1=1&param2=2\n')
        self.advance_time_and_run()
        receiver2.assert_called_once_with(param1="1", param2="2", client=self._bcp_client)
        receiver2.reset_mock()

        # unknown method. should not crash
        self._bcp_client.send = MagicMock()
        self.client_socket.recv_queue.append(b'invalid_method?param1=1&param2=2\n')
        self.advance_time_and_run()


class TestBcpSocketMultipleClients(MpfTestCase):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)

        # use bcp mock
        self.machine_config_patches['bcp'] = {}
        self.machine_config_patches['bcp']['servers'] = []

    def get_use_bcp(self):
        return True

    def setUp(self):
        super().setUp()
        self._bcp_client_1 = self.machine.bcp.transport.get_named_client("local_display")
        self._bcp_client_2 = self.machine.bcp.transport.get_named_client("another_display")

    def _mock_loop(self):
        self.client_socket_1 = MockBcpQueueSocket()
        self.clock.mock_socket("localhost", 5050, self.client_socket_1)
        self.client_socket_2 = MockBcpQueueSocket()
        self.clock.mock_socket("localhost", 9001, self.client_socket_2)

    def getConfigFile(self):
        return 'multiple_connections_config.yaml'

    def getMachinePath(self):
        return 'tests/machine_files/bcp/'

    def testReceiveMessages(self):
        # test message without bytes
        receiver = MagicMock()
        self.machine.bcp.interface.register_command_callback("receive_msg", receiver)

        self.client_socket_1.recv_queue.append(b'receive_msg?param1=1&param2=2\n')
        self.advance_time_and_run()
        receiver.assert_called_once_with(param1="1", param2="2", client=self._bcp_client_1)
        receiver.reset_mock()

        self.client_socket_2.recv_queue.append(b'receive_msg?param1=1&param2=2\n')
        self.advance_time_and_run()
        receiver.assert_called_once_with(param1="1", param2="2", client=self._bcp_client_2)

