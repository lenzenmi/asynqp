import asyncio
import asynqp
from unittest import mock
from asynqp import methods


class OutgoingMethodContext:
    def establish_the_connection(self):
        self.transport = mock.Mock(spec=asyncio.Transport)
        self.dispatcher = mock.Mock(spec=asynqp.Dispatcher)
        self.protocol = asynqp.AMQP(self.dispatcher)
        self.protocol.connection_made(self.transport)


class WhenDeserialisingConnectionStart:
    def given_a_connection_start_method_I_copied_from_the_rabbitmq_server(self):
        self.raw = b"\x00\x0A\x00\x0A\x00\t\x00\x00\x01%\x0ccapabilitiesF\x00\x00\x00X\x12publisher_confirmst\x01\x1aexchange_exchange_bindingst\x01\nbasic.nackt\x01\x16consumer_cancel_notifyt\x01\tcopyrightS\x00\x00\x00'Copyright (C) 2007-2013 GoPivotal, Inc.\x0binformationS\x00\x00\x005Licensed under the MPL.  See http://www.rabbitmq.com/\x08platformS\x00\x00\x00\nErlang/OTP\x07productS\x00\x00\x00\x08RabbitMQ\x07versionS\x00\x00\x00\x053.1.5\x00\x00\x00\x0eAMQPLAIN PLAIN\x00\x00\x00\x0Ben_US en_GB"

    def when_I_deserialise_the_method(self):
        self.result = methods.deserialise_method(self.raw)

    def it_should_have_the_correct_major_version(self):
        assert self.result.version_major == 0

    def it_should_have_the_correct_minor_version(self):
        assert self.result.version_minor == 9

    def it_should_have_the_expected_server_properties(self):
        assert self.result.server_properties == {
            'capabilities': {'publisher_confirms': True,
                             'exchange_exchange_bindings': True,
                             'basic.nack': True,
                             'consumer_cancel_notify': True},
            'copyright': 'Copyright (C) 2007-2013 GoPivotal, Inc.',
            'information': 'Licensed under the MPL.  See http://www.rabbitmq.com/',
            'platform': 'Erlang/OTP',
            'product': 'RabbitMQ',
            'version': '3.1.5'
        }

    def it_should_have_the_security_mechanisms(self):
        assert self.result.mechanisms == 'AMQPLAIN PLAIN'

    def it_should_have_the_correct_locales(self):
        assert self.result.locales == 'en_US en_GB'


class WhenSendingConnectionStartOK(OutgoingMethodContext):
    def given_a_method_to_send(self):
        method = methods.ConnectionStartOK({'somecrap': 'aboutme'}, 'AMQPLAIN', {'auth':'info'}, 'en_US')
        self.frame = asynqp.Frame(asynqp.FrameType.method, 0, method)

    def when_we_send_the_method(self):
        self.protocol.send_frame(self.frame)

    def it_should_send_the_correct_bytestring(self):
        self.transport.write.assert_called_once_with(b'\x01\x00\x00\x00\x00\x00>\x00\n\x00\x0b\x00\x00\x00\x15\x08somecrapS\x00\x00\x00\x07aboutme\x08AMQPLAIN\x00\x00\x00\x0e\x04authS\x00\x00\x00\x04info\x05en_US\xce')


class WhenDeserialisingConnectionTune:
    def given_a_connection_tune_method_I_copied_from_the_rabbitmq_server(self):
        self.raw = b'\x00\x0A\x00\x1E\x00\x00\x00\x02\x00\x00\x02\x58'

    def when_I_deserialise_the_method(self):
        self.result = methods.deserialise_method(self.raw)

    def it_should_have_the_correct_max_channel(self):
        assert self.result.channel_max == 0

    def it_should_have_the_correct_max_frame_length(self):
        assert self.result.frame_max == 131072

    def it_shoud_have_the_correct_heartbeat(self):
        assert self.result.heartbeat == 600


class WhenSendingConnectionTuneOK(OutgoingMethodContext):
    def given_a_method_to_send(self):
        method = methods.ConnectionTuneOK(1024, 131072, 10)
        self.frame = asynqp.Frame(asynqp.FrameType.method, 0, method)

    def when_I_serialise_the_method(self):
        self.protocol.send_frame(self.frame)

    def it_should_write_the_correct_bytestring(self):
        self.transport.write.assert_called_once_with(b'\x01\x00\x00\x00\x00\x00\x0C\x00\n\x00\x1F\x04\x00\x00\x02\x00\x00\x00\x0A\xCE')
