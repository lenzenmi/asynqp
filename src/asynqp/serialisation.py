import struct
from .exceptions import AMQPError


def rethrow_as(expected_cls, to_throw):
    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except expected_cls as e:
                raise to_throw from e
        return wrapper
    return decorator


@rethrow_as(KeyError, AMQPError('bad table value type code'))
@rethrow_as(struct.error, AMQPError('bad table'))
def read_table(stream):
    return _read_table(stream)[0]


def read_long_string(stream):
    return _read_long_string(stream)[0]


def _read_table(stream):
    # TODO: more value types
    TABLE_VALUE_PARSERS = {
        b't': _read_bool,
        b's': _read_short_string,
        b'S': _read_long_string,
        b'F': _read_table
    }

    consumed = 0
    table = {}

    table_length, initial_long_size = _read_long(stream)
    consumed += initial_long_size

    while consumed < table_length + initial_long_size:
        key, x = _read_short_string(stream)
        consumed += x
        value_type_code = stream.read(1)
        consumed += 1

        value, x = TABLE_VALUE_PARSERS[value_type_code](stream)

        consumed += x
        table[key] = value

    return table, consumed


def _read_short_string(stream):
    str_length, x = _read_octet(stream)
    string = stream.read(str_length).decode('utf-8')
    return string, x + str_length


def _read_long_string(stream):
    str_length, x = _read_long(stream)
    bytestring = stream.read(str_length)
    if len(bytestring) != str_length:
        raise AMQPError("Long string had incorrect length")
    return bytestring.decode('utf-8'), x + str_length


def _read_octet(stream):
    x, = struct.unpack('!B', stream.read(1))
    return x, 1


def _read_bool(stream):
    x, = struct.unpack('!?', stream.read(1))
    return x, 1


def _read_long(stream):
    x, = struct.unpack('!L', stream.read(4))
    return x, 4



def short_string(string):
    bytes = string.encode('utf-8')
    return pack_octet(len(bytes)) + bytes


def long_string(string):
    bytes = string.encode('utf-8')
    return pack_long(len(bytes)) + bytes


def pack_table(d):
    bytes = b''
    for key in d:
        if not isinstance(d[key], str):
            raise NotImplementedError()
        bytes += short_string(key)
        bytes += b'S'
        bytes += long_string(d[key])
    return pack_long(len(bytes)) + bytes


def pack_octet(number):
    return struct.pack('!B', number)


def pack_short(number):
    return struct.pack('!H', number)


def pack_long(number):
    return struct.pack('!L', number)
