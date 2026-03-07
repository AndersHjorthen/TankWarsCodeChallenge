"""Tests for src/json_protocol.py -- JSONProtocol encode/decode."""

import json
import pytest
from src.json_protocol import JSONProtocol, _testObject


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class SimpleObj:
    """Minimal serialisable object for tests."""

    def __init__(self, name, value):
        self.name = name
        self.value = value


# ---------------------------------------------------------------------------
# Encode
# ---------------------------------------------------------------------------

class TestJSONProtocolEncode:
    def test_encode_returns_bytes(self):
        jp = JSONProtocol()
        result = jp.encode({"key": "val"})
        assert isinstance(result, bytes)

    def test_encode_ends_with_newline(self):
        jp = JSONProtocol()
        result = jp.encode({"a": 1})
        assert result.endswith(b"\n")

    def test_encode_valid_json_before_newline(self):
        jp = JSONProtocol()
        result = jp.encode({"a": 1})
        payload = result.decode().rstrip("\n")
        parsed = json.loads(payload)
        assert parsed == {"a": 1}

    def test_encode_object_with_dict(self):
        jp = JSONProtocol()
        obj = SimpleObj("test", 42)
        result = jp.encode(obj)
        parsed = json.loads(result.decode().rstrip("\n"))
        assert parsed["name"] == "test"
        assert parsed["value"] == 42

    def test_encode_list(self):
        jp = JSONProtocol()
        result = jp.encode([1, 2, 3])
        parsed = json.loads(result.decode().rstrip("\n"))
        assert parsed == [1, 2, 3]

    def test_encode_nested_object(self):
        jp = JSONProtocol()
        obj = _testObject(1, "aa", [3, 4])
        result = jp.encode(obj)
        parsed = json.loads(result.decode().rstrip("\n"))
        assert parsed["ii"] == 1
        assert parsed["aa"] == "aa"
        assert parsed["ll"] == [3, 4]


# ---------------------------------------------------------------------------
# Decode
# ---------------------------------------------------------------------------

class TestJSONProtocolDecode:
    def test_decode_single_message(self):
        jp = JSONProtocol()
        data = b'{"key": "val"}\n'
        result = jp.decode(data)
        assert len(result) == 1
        assert result[0] == {"key": "val"}

    def test_decode_multiple_messages_in_one_buffer(self):
        jp = JSONProtocol()
        data = b'{"a": 1}\n{"b": 2}\n'
        result = jp.decode(data)
        assert len(result) == 2
        assert result[0] == {"a": 1}
        assert result[1] == {"b": 2}

    def test_decode_partial_message_buffering(self):
        jp = JSONProtocol()
        # Send an incomplete message
        result1 = jp.decode(b'{"key": ')
        assert result1 == []

        # Complete the message
        result2 = jp.decode(b'"val"}\n')
        assert len(result2) == 1
        assert result2[0] == {"key": "val"}

    def test_decode_empty_bytes(self):
        jp = JSONProtocol()
        result = jp.decode(b"")
        assert result == []

    def test_decode_preserves_buffer_across_calls(self):
        jp = JSONProtocol()
        jp.decode(b'{"a":')
        jp.decode(b' 1}\n{"b')
        result = jp.decode(b'": 2}\n')
        # The first message was completed in the second call, so it
        # should have been returned then. Let's test the full flow properly.
        jp2 = JSONProtocol()
        r1 = jp2.decode(b'{"a":')
        assert r1 == []
        r2 = jp2.decode(b' 1}\n{"b')
        assert len(r2) == 1
        assert r2[0] == {"a": 1}
        r3 = jp2.decode(b'": 2}\n')
        assert len(r3) == 1
        assert r3[0] == {"b": 2}

    def test_decode_three_messages_split_across_two_calls(self):
        jp = JSONProtocol()
        msg = b'{"x":1}\n{"y":2}\n{"z"'
        r1 = jp.decode(msg)
        assert len(r1) == 2
        r2 = jp.decode(b':3}\n')
        assert len(r2) == 1
        assert r2[0] == {"z": 3}


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

class TestJSONProtocolRoundTrip:
    def test_round_trip_dict(self):
        jp = JSONProtocol()
        original = {"name": "test", "values": [1, 2, 3]}
        encoded = jp.encode(original)
        decoded = jp.decode(encoded)
        assert len(decoded) == 1
        assert decoded[0] == original

    def test_round_trip_object(self):
        jp = JSONProtocol()
        original = _testObject(1, "aa", [3, 4])
        encoded = jp.encode(original)
        decoded = jp.decode(encoded)
        assert len(decoded) == 1
        reconstructed = _testObject(**decoded[0])
        assert reconstructed == original

    def test_round_trip_multiple_objects(self):
        jp = JSONProtocol()
        obj1 = _testObject(1, "first", [10])
        obj2 = _testObject(2, "second", [20, 30])
        encoded = jp.encode(obj1) + jp.encode(obj2)
        decoded = jp.decode(encoded)
        assert len(decoded) == 2
        assert _testObject(**decoded[0]) == obj1
        assert _testObject(**decoded[1]) == obj2

    def test_round_trip_with_partial_delivery(self):
        """Simulate network chunking: encode one message and deliver in pieces."""
        jp_enc = JSONProtocol()
        jp_dec = JSONProtocol()
        original = {"status": "ok", "count": 42}
        encoded = jp_enc.encode(original)

        # Deliver first half
        mid = len(encoded) // 2
        r1 = jp_dec.decode(encoded[:mid])
        assert r1 == []

        # Deliver second half
        r2 = jp_dec.decode(encoded[mid:])
        assert len(r2) == 1
        assert r2[0] == original


# ---------------------------------------------------------------------------
# Separate instances have independent buffers
# ---------------------------------------------------------------------------

class TestJSONProtocolIndependence:
    def test_separate_instances_independent(self):
        jp1 = JSONProtocol()
        jp2 = JSONProtocol()

        jp1.decode(b'{"a":')
        result = jp2.decode(b'{"b": 2}\n')

        assert len(result) == 1
        assert result[0] == {"b": 2}

        # jp1 should still have partial buffer
        r2 = jp1.decode(b' 1}\n')
        assert len(r2) == 1
        assert r2[0] == {"a": 1}
