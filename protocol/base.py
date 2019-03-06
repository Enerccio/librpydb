# py23 compatible
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import json

from collections.abc import Iterable


__all__ = ["DAPObject", "DAPMessage"]


class DAPObject(object):

    @staticmethod
    def determine_root_factory(data):
        pass

    @staticmethod
    def deserialize(data):
        factory = DAPObject.determine_root_factory(data)
        return DAPObject.deserialize_as(data, factory)

    @classmethod
    def deserialize_as(cls, data, factory):
        args = []
        kwargs = {}
        factory._deserialize(args, kwargs, [], data, [])
        return factory(*args, **kwargs)

    @classmethod
    def _deserialize(cls, args, kwargs, used_args, me, override):
        pass

    def serialize(self):
        me = {}
        self._serialize(me, [])
        return me

    def to_text(self):
        return json.dumps(self.serialize())

    def serialize_scalar(self, target_dict, target_property, value):
        if isinstance(value, dict):
            serialized = {}
            for key in value:
                if isinstance(value[key], DAPobject):
                    serialized[key] = value[key].serialize()
                else:
                    self.serialize_scalar(serialized, key, value[key])
        elif isinstance(value, Iterable):
            serialized = []
            for v in value:
                if isinstance(value[key], DAPobject):
                    serialized.append(v.serialize())
                else:
                    self.serialize_scalar(serialized, None, v)
        else:
            serialized = value

        if target_property is None:
            # is a list
            target_dict.append(serialized)
        else:
            target_dict[target_property] = serialized

    def _serialize(self, me, override):
        pass


class DAPMessage(DAPObject):
    """
    DAPMessage is base class for all debug adapter protocol messages
    """
    def __init__(self):
        DAPObject.__init__(self)

    @staticmethod
    def recv(socket):
        """
        Retrieves single DAPMessage from socket

        Returns None on failure
        """

        body = DAPMessage.recv_raw(socket)

        if body is not None:
            return DAPObject.deserialize(body)

    @staticmethod
    def recv_raw(socket):
        """
        Retrieves single DAPMessage from socket in raw form (json)

        Returns None on failure
        """

        headers = []

        cread_line = ""

        while True:
            c = socket.recv(1)
            if c == "":
                # end of stream
                return None
            cread_line += c

            if cread_line.endswith("\r\n"):
                if cread_line == "\r\n":
                    break
                else:
                    headers.append(cread_line)
                    cread_line = ""

        headers = DAPMessage.parse_headers(headers)

        content_size = int(headers["Content-Length"])

        data = ""

        while (len(data) < content_size):
            data += socket.recv(content_size - len(data))
            if data == "":
                return None

        body = json.loads(data, object_hook=NoneDict)
        # print("RECEIVED: " + str(body))
        return body

    @staticmethod
    def parse_headers(headers):
        """
        Transforms tags into dict
        """

        h = NoneDict({})
        for hl in headers:
            type, value = hl.split(":")
            type = type.strip()
            value = value.strip()
            h[type] = value
        return h

    def send(self, socket):
        """
        Sends this message to client
        """

        data = self.to_text()
        # print("SENT: " + str(data))
        DAPMessage.send_text(socket, data)

    @staticmethod
    def send_text(socket, text):
        """
        Sends the raw text message as DAPMessage
        """

        socket.sendall("Content-Length: " + str(len(text)) + "\r\n")
        socket.sendall("\r\n")
        socket.sendall(text)
