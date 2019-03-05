# py23 compatible
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import json

from .utils import NoneDict

__all__ = ["features", "DAPMessage", "DAPRequest", "DAPEvent", "DAPResponse", "DAPErrorResponse",
    "DAPInitializedEvent", "DAPStoppedEvent", "DAPContinueEvent", "DAPExitedEvent",
    "DAPTerminatedEvent", "DAPThreadEvent", "DAPOutputEvent", "DAPBreakpointEvent",
    "DAPModuleEvent", "DAPLoadedSourceEvent", "DAPProcessEvent", "DAPCapabilitiesEvent",
    "DAPRunInTerminalRequest", "DAPRunInTerminalResponse", "DAPSetBreakpointsResponse", "DAPSetFunctionBreakpointsResponse",
    "DAPContinueResponse", "DAPInitializeResponse", "DAPStackTraceResponse", "DAPScopesResponse",
    "DAPVariablesResponse", "DAPSetVariableResponse", "DAPSourceResponse", "DAPThreadsResponse",
    "DAPEvaluateResponse"]

# enabled features
features = {
    "supportsExceptionInfoRequest": False,
    "supportTerminateDebuggee": False,
    "supportsTerminateThreadsRequest": False,
    "supportsDataBreakpoints": False,
    "supportsStepInTargetsRequest": False,
    "supportsSetExpression": False,
    "supportsGotoTargetsRequest": False,
    "supportsFunctionBreakpoints": False,

    # TODO
    "supportsConditionalBreakpoints": False,
    "supportsHitConditionalBreakpoints": False,
}



class DAPMessage(object):
    """
    DAPMessage is base class for all debug adapter protocol
    """

    def __init__(self):
        self.seq = None

    def set_seq(self, seq):
        """
        Sets sequence number to seq
        """

        self.seq = seq
        return self

    @staticmethod
    def recv(socket):
        """
        Retrieves single DAPMessage from socket

        Returns None on failure
        """

        body = DAPMessage.recv_raw(socket)

        if body is not None:
            kwargs = body["arguments"]
            if kwargs is None:
                kwargs = {}
            rq = DAPRequest(command=body["command"], **kwargs)
            rq.set_seq(body["seq"])
            return rq

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
            data += socket.recv(content_size-len(data))
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

        data = self.serialize(self.seq)
        # print("SENT: " + str(data))
        DAPMessage.send_text(socket, data)

    def serialize(self, seq):
        """
        Serializes this message to JSON
        """

        message = {}
        message["seq"] = seq
        message["type"] = self.get_type()

        self.serialize_context(message)

        return json.dumps(message)

    def serialize_context(self, message):
        """
        Serializes inner body of this message

        Abstract method
        """

        pass

    def get_type(self):
        """
        Returns type of this message
        """

        raise NotImplementedError()

    @staticmethod
    def send_text(socket, text):
        """
        Sends the raw text message as DAPMessage
        """

        socket.sendall("Content-Length: " + str(len(text)) + "\r\n")
        socket.sendall("\r\n")
        socket.sendall(text)

    @staticmethod
    def remove_nones(dict):
        """
        Removes all Nones from dict
        """

        d = {}
        for key in dict:
            if dict[key] is not None:
                d[key] = dict[key]
        return d


class DAPRequest(DAPMessage):
    def __init__(self, command, **kwargs):
        self.command = command
        self.kwargs = DAPMessage.remove_nones(kwargs)

    def serialize_context(self, message):
        message["command"] = self.command
        message["args"] = self.kwargs

    def get_type(self):
        return "type"


class DAPEvent(DAPMessage):
    def __init__(self, event):
        self.event = event

    def serialize_context(self, message):
        message["event"] = self.event
        self.serialize_event_context(message)

    def serialize_event_context(self, message):
        raise NotImplementedError()

    def get_type(self):
        return "event"


class DAPResponse(DAPMessage):
    def __init__(self, rqs, command, success=True, message=None):
        self.rqs = rqs
        self.command = command
        self.success = success
        self.message = message

    def serialize_context(self, message):
        message["request_seq"] = self.rqs
        message["command"] = self.command
        message["success"] = self.success
        if self.message is not None:
            message["success"] = self.message
        self.serialize_response_context(message)

    def serialize_response_context(self, message):
        pass

    def get_type(self):
        return "response"


class DAPErrorResponse(DAPResponse):
    def __init__(self, rqs, command, message="", detailed_message=None):
        DAPResponse.__init__(self, rqs, command, success=False, message=message)
        self.dm = detailed_message

    def serialize_response_context(self, message):
        message["body"] = {}
        if self.dm is not None:
            message["body"]["error"] = self.dm


class DAPInitializedEvent(DAPEvent):
    def __init__(self):
        DAPEvent.__init__(self, "initialized")

    def serialize_event_context(self, message):
        pass


class DAPStoppedEvent(DAPEvent):
    def __init__(self, reason, description=None, thread_id=None, preserve_focus_hint=None, text=None, all_threads_stopped=None):
        DAPEvent.__init__(self, "stopped")

        self.reason = reason
        self.description = description
        self.thread_id = thread_id
        self.preserve_focus_hint = preserve_focus_hint
        self.text = text
        self.all_threads_stopped = all_threads_stopped

    def serialize_event_context(self, message):
        body = {}
        message["body"] = body

        body["reason"] = self.reason

        if self.description is not None:
            body["description"] = self.description
        if self.thread_id is not None:
            body["threadId"] = self.thread_id
        if self.preserve_focus_hint is not None:
            body["preserveFocusHint"] = self.preserve_focus_hint
        if self.text is not None:
            body["text"] = self.text
        if self.all_threads_stopped is not None:
            body["allThreadsStopped"] = self.all_threads_stopped


class DAPContinueEvent(DAPEvent):
    def __init__(self, thread_id, all_threads_continue=None):
        DAPEvent.__init__(self, "continued")

        self.thread_id = thread_id
        self.all_threads_continue = all_threads_continue

    def serialize_event_context(self, message):
        body = {}
        message["body"] = body

        body["threadId"] = self.thread_id

        if self.all_threads_continue is not None:
            body["allThreadsContinued"] = self.all_threads_continue


class DAPExitedEvent(DAPEvent):
    def __init__(self, ec):
        DAPEvent.__init__(self, "exited")

        self.ec = ec

    def serialize_event_context(self, message):
        body = {}
        message["body"] = body

        body["exitCode"] = self.ec


class DAPTerminatedEvent(DAPEvent):
    def __init__(self, restart=None):
        DAPEvent.__init__(self, "terminated")

        self.restart = restart

    def serialize_event_context(self, message):
        if self.restart is not None:
            body = {}
            message["body"] = body

            body["restart"] = self.restart


class DAPThreadEvent(DAPEvent):
    def __init__(self, reason, thread_id):
        DAPEvent.__init__(self, "thread")

        self.reason = reason
        self.thread_id = thread_id

    def serialize_event_context(self, message):
        body = {}
        message["body"] = body

        body["reason"] = self.reason
        body["threadId"] = self.thread_id


class DAPOutputEvent(DAPEvent):
    def __init__(self, output, category=None, variables_reference=None, source=None, line=None, column=None, data=None):
        DAPEvent.__init__(self, "output")

        self.output = output
        self.category = category
        self.variables_reference = variables_reference
        self.source = source
        self.line = line
        self.column = column
        self.data = data

    def serialize_event_context(self, message):
        body = {}
        message["body"] = body

        if self.category is not None:
            body["category"] = self.category

        body["output"] = self.output

        if self.variables_reference is not None:
            body["variablesReference"] = self.variables_reference

        if self.source is not None:
            body["source"] = self.source

        if self.line is not None:
            body["line"] = self.line

        if self.column is not None:
            body["column"] = self.column

        if self.data is not None:
            body["data"] = self.data


class DAPBreakpointEvent(DAPEvent):
    def __init__(self, reason, breakpoint):
        DAPEvent.__init__(self, "breakpoint")

        self.reason = reason
        self.breakpoint = breakpoint

    def serialize_event_context(self, message):
        body = {}
        message["body"] = body

        body["reason"] = self.reason
        body["breakpoint"] = self.breakpoint


class DAPModuleEvent(DAPEvent):
    def __init__(self, reason, module):
        DAPEvent.__init__(self, "module")

        self.reason = reason
        self.module = module

    def serialize_event_context(self, message):
        body = {}
        message["body"] = body

        body["reason"] = self.reason
        body["module"] = self.module


class DAPLoadedSourceEvent(DAPEvent):
    def __init__(self, reason, source):
        DAPEvent.__init__(self, "loadedSource")

        self.reason = reason
        self.source = source

    def serialize_event_context(self, message):
        body = {}
        message["body"] = body

        body["reason"] = self.reason
        body["source"] = self.source


class DAPProcessEvent(DAPEvent):
    def __init__(self, name, process_id=None, is_local=None, start_method=None):
        DAPEvent.__init__(self, "process")

        self.name = name
        self.process_id = process_id
        self.is_local = is_local
        self.start_method = start_method

    def serialize_event_context(self, message):
        body = {}
        message["body"] = body

        body["name"] = self.name

        if self.process_id is not None:
            body["systemProcessId"] = self.process_id

        if self.is_local is not None:
            body["isLocalProcess"] = self.is_local

        if self.start_method is not None:
            body["startMethod"] = self.start_method


class DAPCapabilitiesEvent(DAPEvent):
    def __init__(self, capabilities):
        DAPEvent.__init__(self, "capabilities")

        self.capabilities = capabilities

    def serialize_event_context(self, message):
        body = {}
        message["body"] = body

        body["capabilities"] = self.capabilities


class DAPRunInTerminalRequest(DAPRequest):
    def __init__(self, cwd, args, kind=None, title=None, env=None):
        DAPRequest.__init__(self, "runInTerminal", kind, title, cwd, args, env)


class DAPRunInTerminalResponse(DAPResponse):
    def __init__(self, rqs, process_id=None, shell_process_id=None):
        DAPResponse.__init__(self, rqs, "runInTerminal")
        self.process_id = process_id
        self.shell_process_id = shell_process_id

    def serialize_response_context(self, message):
        body = {}
        message["body"] = body

        if self.process_id is not None:
            body["processId"] = self.process_id

        if self.shell_process_id is not None:
            body["shellProcessId"] = self.shell_process_id


### ONLY SUPPORTED RESPONSES (and thus requests) ARE IMPLEMENTED!

class DAPSetBreakpointsResponse(DAPResponse):
    def __init__(self, rqs, breakpoints):
        DAPResponse.__init__(self, rqs, "setBreakpoints")
        self.breakpoints = breakpoints

    def serialize_response_context(self, message):
        body = {}
        message["body"] = body

        body["breakpoints"] = self.breakpoints


class DAPSetFunctionBreakpointsResponse(DAPResponse):
    def __init__(self, rqs, breakpoints):
        DAPResponse.__init__(self, rqs, "setFunctionBreakpoints")
        self.breakpoints = breakpoints

    def serialize_response_context(self, message):
        body = {}
        message["body"] = body

        body["breakpoints"] = self.breakpoints


class DAPContinueResponse(DAPResponse):
    def __init__(self, rqs, all_threads_continue=None):
        DAPResponse.__init__(self, rqs, "continue")
        self.all_threads_continue = all_threads_continue

    def serialize_response_context(self, message):
        body = {}
        message["body"] = body

        if self.all_threads_continue is not None:
            body["allThreadsContinued"] = self.all_threads_continue

# next has no special response

# step has no special response

# step out has no special response

# pause has no special response

class DAPInitializeResponse(DAPResponse):
    def __init__(self, rqs, capabilities):
        DAPResponse.__init__(self, rqs, "initialize")
        self.capabilities = capabilities

    def serialize_response_context(self, message):
        body = {}
        message["body"] = self.capabilities


class DAPStackTraceResponse(DAPResponse):
    def __init__(self, rqs, stack_frames):
        DAPResponse.__init__(self, rqs, "stackTrace")
        self.stack_frames = stack_frames

    def serialize_response_context(self, message):
        body = {}
        message["body"] = body

        body["stackFrames"] = self.stack_frames
        body["totalFrames"] = len(self.stack_frames)


class DAPScopesResponse(DAPResponse):
    def __init__(self, rqs, scopes):
        DAPResponse.__init__(self, rqs, "scopes")
        self.scopes = scopes

    def serialize_response_context(self, message):
        body = {}
        message["body"] = body

        body["scopes"] = self.scopes


class DAPVariablesResponse(DAPResponse):
    def __init__(self, rqs, variables):
        DAPResponse.__init__(self, rqs, "variables")
        self.variables = variables

    def serialize_response_context(self, message):
        body = {}
        message["body"] = body

        body["variables"] = self.variables


class DAPSetVariableResponse(DAPResponse):
    def __init__(self, rqs, value, type=None, variables_reference=None, named_variables=None, indexed_variables=None):
        DAPResponse.__init__(self, rqs, "setVariable")
        self.value = value
        self.type = type
        self.variables_reference = variables_reference
        self.named_variables = named_variables
        self.indexed_variables = indexed_variables

    def serialize_response_context(self, message):
        body = {}
        message["body"] = body

        body["value"] = self.value
        if self.type is not None:
            body["type"] = self.type
        if self.variables_reference is not None:
            body["variablesReference"] = self.variables_reference
        if self.named_variables is not None:
            body["namedVariables"] = self.named_variables
        if self.indexed_variables is not None:
            body["indexedVariables"] = self.indexed_variables


class DAPSourceResponse(DAPResponse):
    def __init__(self, rqs, source, mime_type=None):
        DAPResponse.__init__(self, rqs, "source")
        self.source = source
        self.mime_type = mime_type

    def serialize_response_context(self, message):
        body = {}
        message["body"] = body

        body["source"] = self.source
        if self.mime_type is not None:
            body["mimeType"] = self.mime_type


class DAPThreadsResponse(DAPResponse):
    def __init__(self, rqs, threads):
        DAPResponse.__init__(self, rqs, "threads")
        self.threads = threads

    def serialize_response_context(self, message):
        body = {}
        message["body"] = body

        body["threads"] = self.threads


class DAPEvaluateResponse(DAPResponse):
    def __init__(self, rqs, result, type=None, presentation_hint=None, variables_reference=None, named_variables=None, indexed_variables=None):
        DAPResponse.__init__(self, rqs, "evaluate")
        self.result = result
        self.type = type
        self.presentation_hint = presentation_hint
        self.variables_reference = variables_reference
        self.named_variables = named_variables
        self.indexed_variables = indexed_variables

    def serialize_response_context(self, message):
        body = {}
        message["body"] = body

        body["value"] = self.value
        if self.type is not None:
            body["type"] = self.type
        if self.presentation_hint is not None:
            body["presentationHint"] = self.presentation_hint
        if self.variables_reference is not None:
            body["variablesReference"] = self.variables_reference
        if self.named_variables is not None:
            body["namedVariables"] = self.named_variables
        if self.indexed_variables is not None:
            body["indexedVariables"] = self.indexed_variables
