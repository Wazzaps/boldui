# pyre-strict
from typing import BinaryIO
from dataclasses import dataclass
import typing
import serde_types as st
import bincode


@dataclass(frozen=True)
class A2RExtendedHelloResponse:
    pass

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, A2RExtendedHelloResponse)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "A2RExtendedHelloResponse":
        v, buffer = bincode.deserialize(input, A2RExtendedHelloResponse)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "A2RExtendedHelloResponse":
        return bincode.deserialize_stream(input, A2RExtendedHelloResponse)


@dataclass(frozen=True)
class A2RHelloResponse:
    protocol_major_version: st.uint16
    protocol_minor_version: st.uint16
    extra_len: st.uint32
    error: typing.Optional["Error"]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, A2RHelloResponse)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "A2RHelloResponse":
        v, buffer = bincode.deserialize(input, A2RHelloResponse)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "A2RHelloResponse":
        return bincode.deserialize_stream(input, A2RHelloResponse)


class A2RMessage:
    VARIANTS = []  # type: typing.Sequence[typing.Type[A2RMessage]]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, A2RMessage)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "A2RMessage":
        v, buffer = bincode.deserialize(input, A2RMessage)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "A2RMessage":
        return bincode.deserialize_stream(input, A2RMessage)


@dataclass(frozen=True)
class A2RMessage__Update(A2RMessage):
    INDEX = 0  # type: int
    value: "A2RUpdate"


@dataclass(frozen=True)
class A2RMessage__Error(A2RMessage):
    INDEX = 1  # type: int
    value: "Error"


@dataclass(frozen=True)
class A2RMessage__CompressedUpdate(A2RMessage):
    INDEX = 2  # type: int
    value: typing.Sequence[st.uint8]


A2RMessage.VARIANTS = [
    A2RMessage__Update,
    A2RMessage__Error,
    A2RMessage__CompressedUpdate,
]


class A2RReparentScene:
    VARIANTS = []  # type: typing.Sequence[typing.Type[A2RReparentScene]]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, A2RReparentScene)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "A2RReparentScene":
        v, buffer = bincode.deserialize(input, A2RReparentScene)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "A2RReparentScene":
        return bincode.deserialize_stream(input, A2RReparentScene)


@dataclass(frozen=True)
class A2RReparentScene__Inside(A2RReparentScene):
    INDEX = 0  # type: int
    value: st.uint32


@dataclass(frozen=True)
class A2RReparentScene__After(A2RReparentScene):
    INDEX = 1  # type: int
    value: st.uint32


@dataclass(frozen=True)
class A2RReparentScene__Root(A2RReparentScene):
    INDEX = 2  # type: int
    pass


@dataclass(frozen=True)
class A2RReparentScene__Disconnect(A2RReparentScene):
    INDEX = 3  # type: int
    pass


@dataclass(frozen=True)
class A2RReparentScene__Hide(A2RReparentScene):
    INDEX = 4  # type: int
    pass


A2RReparentScene.VARIANTS = [
    A2RReparentScene__Inside,
    A2RReparentScene__After,
    A2RReparentScene__Root,
    A2RReparentScene__Disconnect,
    A2RReparentScene__Hide,
]


@dataclass(frozen=True)
class A2RUpdate:
    updated_scenes: typing.Sequence["A2RUpdateScene"]
    run_blocks: typing.Sequence["HandlerBlock"]
    external_app_requests: typing.Sequence["ExternalAppRequest"]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, A2RUpdate)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "A2RUpdate":
        v, buffer = bincode.deserialize(input, A2RUpdate)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "A2RUpdate":
        return bincode.deserialize_stream(input, A2RUpdate)


@dataclass(frozen=True)
class A2RUpdateScene:
    id: st.uint32
    paint: "OpId"
    backdrop: "OpId"
    transform: "OpId"
    clip: "OpId"
    uri: str
    dimensions: "OpId"
    ops: typing.Sequence["OpsOperation"]
    cmds: typing.Sequence["CmdsCommand"]
    var_decls: typing.Dict[str, "Value"]
    watches: typing.Sequence["Watch"]
    event_handlers: typing.Sequence[typing.Tuple["EventType", "HandlerBlock"]]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, A2RUpdateScene)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "A2RUpdateScene":
        v, buffer = bincode.deserialize(input, A2RUpdateScene)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "A2RUpdateScene":
        return bincode.deserialize_stream(input, A2RUpdateScene)


class CmdsCommand:
    VARIANTS = []  # type: typing.Sequence[typing.Type[CmdsCommand]]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, CmdsCommand)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "CmdsCommand":
        v, buffer = bincode.deserialize(input, CmdsCommand)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "CmdsCommand":
        return bincode.deserialize_stream(input, CmdsCommand)


@dataclass(frozen=True)
class CmdsCommand__Clear(CmdsCommand):
    INDEX = 0  # type: int
    color: "OpId"


@dataclass(frozen=True)
class CmdsCommand__DrawRect(CmdsCommand):
    INDEX = 1  # type: int
    paint: "OpId"
    rect: "OpId"


@dataclass(frozen=True)
class CmdsCommand__DrawRoundRect(CmdsCommand):
    INDEX = 2  # type: int
    paint: "OpId"
    rect: "OpId"
    radius: "OpId"


@dataclass(frozen=True)
class CmdsCommand__DrawCenteredText(CmdsCommand):
    INDEX = 3  # type: int
    text: "OpId"
    paint: "OpId"
    center: "OpId"


CmdsCommand.VARIANTS = [
    CmdsCommand__Clear,
    CmdsCommand__DrawRect,
    CmdsCommand__DrawRoundRect,
    CmdsCommand__DrawCenteredText,
]


@dataclass(frozen=True)
class Color:
    r: st.uint16
    g: st.uint16
    b: st.uint16
    a: st.uint16

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, Color)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "Color":
        v, buffer = bincode.deserialize(input, Color)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "Color":
        return bincode.deserialize_stream(input, Color)


@dataclass(frozen=True)
class EA2RExtendedHelloResponse:
    pass

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, EA2RExtendedHelloResponse)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "EA2RExtendedHelloResponse":
        v, buffer = bincode.deserialize(input, EA2RExtendedHelloResponse)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "EA2RExtendedHelloResponse":
        return bincode.deserialize_stream(input, EA2RExtendedHelloResponse)


@dataclass(frozen=True)
class EA2RHelloResponse:
    protocol_major_version: st.uint16
    protocol_minor_version: st.uint16
    extra_len: st.uint32
    error: typing.Optional["Error"]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, EA2RHelloResponse)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "EA2RHelloResponse":
        v, buffer = bincode.deserialize(input, EA2RHelloResponse)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "EA2RHelloResponse":
        return bincode.deserialize_stream(input, EA2RHelloResponse)


class EA2RMessage:
    VARIANTS = []  # type: typing.Sequence[typing.Type[EA2RMessage]]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, EA2RMessage)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "EA2RMessage":
        v, buffer = bincode.deserialize(input, EA2RMessage)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "EA2RMessage":
        return bincode.deserialize_stream(input, EA2RMessage)


@dataclass(frozen=True)
class EA2RMessage__CreatedExternalWidget(EA2RMessage):
    INDEX = 0  # type: int
    texture_info: typing.Sequence[st.uint8]


@dataclass(frozen=True)
class EA2RMessage__SpontaneousUpdate(EA2RMessage):
    INDEX = 1  # type: int
    pass


@dataclass(frozen=True)
class EA2RMessage__UpdateHandled(EA2RMessage):
    INDEX = 2  # type: int
    pass


@dataclass(frozen=True)
class EA2RMessage__Error(EA2RMessage):
    INDEX = 3  # type: int
    value: "Error"


EA2RMessage.VARIANTS = [
    EA2RMessage__CreatedExternalWidget,
    EA2RMessage__SpontaneousUpdate,
    EA2RMessage__UpdateHandled,
    EA2RMessage__Error,
]


@dataclass(frozen=True)
class Error:
    code: st.uint64
    text: str

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, Error)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "Error":
        v, buffer = bincode.deserialize(input, Error)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "Error":
        return bincode.deserialize_stream(input, Error)


class EventType:
    VARIANTS = []  # type: typing.Sequence[typing.Type[EventType]]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, EventType)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "EventType":
        v, buffer = bincode.deserialize(input, EventType)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "EventType":
        return bincode.deserialize_stream(input, EventType)


@dataclass(frozen=True)
class EventType__MouseDown(EventType):
    INDEX = 0  # type: int
    rect: "OpId"


@dataclass(frozen=True)
class EventType__MouseUp(EventType):
    INDEX = 1  # type: int
    rect: "OpId"


EventType.VARIANTS = [
    EventType__MouseDown,
    EventType__MouseUp,
]


@dataclass(frozen=True)
class ExternalAppRequest:
    scene_id: st.uint32
    uri: str

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, ExternalAppRequest)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "ExternalAppRequest":
        v, buffer = bincode.deserialize(input, ExternalAppRequest)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "ExternalAppRequest":
        return bincode.deserialize_stream(input, ExternalAppRequest)


@dataclass(frozen=True)
class HandlerBlock:
    ops: typing.Sequence["OpsOperation"]
    cmds: typing.Sequence["HandlerCmd"]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, HandlerBlock)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "HandlerBlock":
        v, buffer = bincode.deserialize(input, HandlerBlock)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "HandlerBlock":
        return bincode.deserialize_stream(input, HandlerBlock)


class HandlerCmd:
    VARIANTS = []  # type: typing.Sequence[typing.Type[HandlerCmd]]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, HandlerCmd)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "HandlerCmd":
        v, buffer = bincode.deserialize(input, HandlerCmd)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "HandlerCmd":
        return bincode.deserialize_stream(input, HandlerCmd)


@dataclass(frozen=True)
class HandlerCmd__Nop(HandlerCmd):
    INDEX = 0  # type: int
    pass


@dataclass(frozen=True)
class HandlerCmd__AllocateWindowId(HandlerCmd):
    INDEX = 1  # type: int
    pass


@dataclass(frozen=True)
class HandlerCmd__ReparentScene(HandlerCmd):
    INDEX = 2  # type: int
    scene: st.uint32
    to: "A2RReparentScene"


@dataclass(frozen=True)
class HandlerCmd__UpdateVar(HandlerCmd):
    INDEX = 3  # type: int
    var: "VarId"
    value: "OpId"


@dataclass(frozen=True)
class HandlerCmd__DebugMessage(HandlerCmd):
    INDEX = 4  # type: int
    msg: str


@dataclass(frozen=True)
class HandlerCmd__Reply(HandlerCmd):
    INDEX = 5  # type: int
    path: str
    params: typing.Sequence["OpId"]


@dataclass(frozen=True)
class HandlerCmd__If(HandlerCmd):
    INDEX = 6  # type: int
    condition: "OpId"
    then: "HandlerCmd"
    or_else: "HandlerCmd"


HandlerCmd.VARIANTS = [
    HandlerCmd__Nop,
    HandlerCmd__AllocateWindowId,
    HandlerCmd__ReparentScene,
    HandlerCmd__UpdateVar,
    HandlerCmd__DebugMessage,
    HandlerCmd__Reply,
    HandlerCmd__If,
]


@dataclass(frozen=True)
class OpId:
    scene_id: st.uint32
    idx: st.uint32

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, OpId)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "OpId":
        v, buffer = bincode.deserialize(input, OpId)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "OpId":
        return bincode.deserialize_stream(input, OpId)


class OpsOperation:
    VARIANTS = []  # type: typing.Sequence[typing.Type[OpsOperation]]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, OpsOperation)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "OpsOperation":
        v, buffer = bincode.deserialize(input, OpsOperation)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "OpsOperation":
        return bincode.deserialize_stream(input, OpsOperation)


@dataclass(frozen=True)
class OpsOperation__Value(OpsOperation):
    INDEX = 0  # type: int
    value: "Value"


@dataclass(frozen=True)
class OpsOperation__Var(OpsOperation):
    INDEX = 1  # type: int
    value: "VarId"


@dataclass(frozen=True)
class OpsOperation__GetTime(OpsOperation):
    INDEX = 2  # type: int
    pass


@dataclass(frozen=True)
class OpsOperation__GetTimeAndClamp(OpsOperation):
    INDEX = 3  # type: int
    low: "OpId"
    high: "OpId"


@dataclass(frozen=True)
class OpsOperation__Add(OpsOperation):
    INDEX = 4  # type: int
    a: "OpId"
    b: "OpId"


@dataclass(frozen=True)
class OpsOperation__Neg(OpsOperation):
    INDEX = 5  # type: int
    a: "OpId"


@dataclass(frozen=True)
class OpsOperation__Mul(OpsOperation):
    INDEX = 6  # type: int
    a: "OpId"
    b: "OpId"


@dataclass(frozen=True)
class OpsOperation__Div(OpsOperation):
    INDEX = 7  # type: int
    a: "OpId"
    b: "OpId"


@dataclass(frozen=True)
class OpsOperation__FloorDiv(OpsOperation):
    INDEX = 8  # type: int
    a: "OpId"
    b: "OpId"


@dataclass(frozen=True)
class OpsOperation__Eq(OpsOperation):
    INDEX = 9  # type: int
    a: "OpId"
    b: "OpId"


@dataclass(frozen=True)
class OpsOperation__Min(OpsOperation):
    INDEX = 10  # type: int
    a: "OpId"
    b: "OpId"


@dataclass(frozen=True)
class OpsOperation__Max(OpsOperation):
    INDEX = 11  # type: int
    a: "OpId"
    b: "OpId"


@dataclass(frozen=True)
class OpsOperation__Or(OpsOperation):
    INDEX = 12  # type: int
    a: "OpId"
    b: "OpId"


@dataclass(frozen=True)
class OpsOperation__And(OpsOperation):
    INDEX = 13  # type: int
    a: "OpId"
    b: "OpId"


@dataclass(frozen=True)
class OpsOperation__GreaterThan(OpsOperation):
    INDEX = 14  # type: int
    a: "OpId"
    b: "OpId"


@dataclass(frozen=True)
class OpsOperation__Abs(OpsOperation):
    INDEX = 15  # type: int
    a: "OpId"


@dataclass(frozen=True)
class OpsOperation__Sin(OpsOperation):
    INDEX = 16  # type: int
    a: "OpId"


@dataclass(frozen=True)
class OpsOperation__Cos(OpsOperation):
    INDEX = 17  # type: int
    a: "OpId"


@dataclass(frozen=True)
class OpsOperation__MakePoint(OpsOperation):
    INDEX = 18  # type: int
    left: "OpId"
    top: "OpId"


@dataclass(frozen=True)
class OpsOperation__MakeRectFromPoints(OpsOperation):
    INDEX = 19  # type: int
    left_top: "OpId"
    right_bottom: "OpId"


@dataclass(frozen=True)
class OpsOperation__MakeRectFromSides(OpsOperation):
    INDEX = 20  # type: int
    left: "OpId"
    top: "OpId"
    right: "OpId"
    bottom: "OpId"


@dataclass(frozen=True)
class OpsOperation__MakeColor(OpsOperation):
    INDEX = 21  # type: int
    r: "OpId"
    g: "OpId"
    b: "OpId"
    a: "OpId"


@dataclass(frozen=True)
class OpsOperation__ToString(OpsOperation):
    INDEX = 22  # type: int
    a: "OpId"


@dataclass(frozen=True)
class OpsOperation__If(OpsOperation):
    INDEX = 23  # type: int
    condition: "OpId"
    then: "OpId"
    or_else: "OpId"


OpsOperation.VARIANTS = [
    OpsOperation__Value,
    OpsOperation__Var,
    OpsOperation__GetTime,
    OpsOperation__GetTimeAndClamp,
    OpsOperation__Add,
    OpsOperation__Neg,
    OpsOperation__Mul,
    OpsOperation__Div,
    OpsOperation__FloorDiv,
    OpsOperation__Eq,
    OpsOperation__Min,
    OpsOperation__Max,
    OpsOperation__Or,
    OpsOperation__And,
    OpsOperation__GreaterThan,
    OpsOperation__Abs,
    OpsOperation__Sin,
    OpsOperation__Cos,
    OpsOperation__MakePoint,
    OpsOperation__MakeRectFromPoints,
    OpsOperation__MakeRectFromSides,
    OpsOperation__MakeColor,
    OpsOperation__ToString,
    OpsOperation__If,
]


@dataclass(frozen=True)
class R2AExtendedHello:
    pass

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, R2AExtendedHello)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "R2AExtendedHello":
        v, buffer = bincode.deserialize(input, R2AExtendedHello)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "R2AExtendedHello":
        return bincode.deserialize_stream(input, R2AExtendedHello)


@dataclass(frozen=True)
class R2AHello:
    min_protocol_major_version: st.uint16
    min_protocol_minor_version: st.uint16
    max_protocol_major_version: st.uint16
    extra_len: st.uint32

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, R2AHello)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "R2AHello":
        v, buffer = bincode.deserialize(input, R2AHello)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "R2AHello":
        return bincode.deserialize_stream(input, R2AHello)


class R2AMessage:
    VARIANTS = []  # type: typing.Sequence[typing.Type[R2AMessage]]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, R2AMessage)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "R2AMessage":
        v, buffer = bincode.deserialize(input, R2AMessage)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "R2AMessage":
        return bincode.deserialize_stream(input, R2AMessage)


@dataclass(frozen=True)
class R2AMessage__Update(R2AMessage):
    INDEX = 0  # type: int
    value: "R2AUpdate"


@dataclass(frozen=True)
class R2AMessage__Open(R2AMessage):
    INDEX = 1  # type: int
    value: "R2AOpen"


@dataclass(frozen=True)
class R2AMessage__Error(R2AMessage):
    INDEX = 2  # type: int
    value: "Error"


R2AMessage.VARIANTS = [
    R2AMessage__Update,
    R2AMessage__Open,
    R2AMessage__Error,
]


@dataclass(frozen=True)
class R2AOpen:
    path: str

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, R2AOpen)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "R2AOpen":
        v, buffer = bincode.deserialize(input, R2AOpen)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "R2AOpen":
        return bincode.deserialize_stream(input, R2AOpen)


@dataclass(frozen=True)
class R2AReply:
    path: str
    params: typing.Sequence["Value"]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, R2AReply)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "R2AReply":
        v, buffer = bincode.deserialize(input, R2AReply)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "R2AReply":
        return bincode.deserialize_stream(input, R2AReply)


@dataclass(frozen=True)
class R2AUpdate:
    replies: typing.Sequence["R2AReply"]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, R2AUpdate)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "R2AUpdate":
        v, buffer = bincode.deserialize(input, R2AUpdate)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "R2AUpdate":
        return bincode.deserialize_stream(input, R2AUpdate)


@dataclass(frozen=True)
class R2EAExtendedHello:
    pass

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, R2EAExtendedHello)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "R2EAExtendedHello":
        v, buffer = bincode.deserialize(input, R2EAExtendedHello)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "R2EAExtendedHello":
        return bincode.deserialize_stream(input, R2EAExtendedHello)


@dataclass(frozen=True)
class R2EAHello:
    min_protocol_major_version: st.uint16
    min_protocol_minor_version: st.uint16
    max_protocol_major_version: st.uint16
    extra_len: st.uint32

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, R2EAHello)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "R2EAHello":
        v, buffer = bincode.deserialize(input, R2EAHello)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "R2EAHello":
        return bincode.deserialize_stream(input, R2EAHello)


class R2EAMessage:
    VARIANTS = []  # type: typing.Sequence[typing.Type[R2EAMessage]]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, R2EAMessage)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "R2EAMessage":
        v, buffer = bincode.deserialize(input, R2EAMessage)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "R2EAMessage":
        return bincode.deserialize_stream(input, R2EAMessage)


@dataclass(frozen=True)
class R2EAMessage__Update(R2EAMessage):
    INDEX = 0  # type: int
    value: "R2EAUpdate"


@dataclass(frozen=True)
class R2EAMessage__Open(R2EAMessage):
    INDEX = 1  # type: int
    value: "R2EAOpen"


@dataclass(frozen=True)
class R2EAMessage__Error(R2EAMessage):
    INDEX = 2  # type: int
    value: "Error"


R2EAMessage.VARIANTS = [
    R2EAMessage__Update,
    R2EAMessage__Open,
    R2EAMessage__Error,
]


@dataclass(frozen=True)
class R2EAOpen:
    path: str

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, R2EAOpen)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "R2EAOpen":
        v, buffer = bincode.deserialize(input, R2EAOpen)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "R2EAOpen":
        return bincode.deserialize_stream(input, R2EAOpen)


@dataclass(frozen=True)
class R2EAUpdate:
    changed_vars: typing.Sequence[typing.Tuple[str, "Value"]]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, R2EAUpdate)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "R2EAUpdate":
        v, buffer = bincode.deserialize(input, R2EAUpdate)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "R2EAUpdate":
        return bincode.deserialize_stream(input, R2EAUpdate)


class Value:
    VARIANTS = []  # type: typing.Sequence[typing.Type[Value]]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, Value)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "Value":
        v, buffer = bincode.deserialize(input, Value)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "Value":
        return bincode.deserialize_stream(input, Value)


@dataclass(frozen=True)
class Value__Sint64(Value):
    INDEX = 0  # type: int
    value: st.int64


@dataclass(frozen=True)
class Value__Double(Value):
    INDEX = 1  # type: int
    value: st.float64


@dataclass(frozen=True)
class Value__String(Value):
    INDEX = 2  # type: int
    value: str


@dataclass(frozen=True)
class Value__Color(Value):
    INDEX = 3  # type: int
    value: "Color"


@dataclass(frozen=True)
class Value__Point(Value):
    INDEX = 4  # type: int
    left: st.float64
    top: st.float64


@dataclass(frozen=True)
class Value__Rect(Value):
    INDEX = 5  # type: int
    left: st.float64
    top: st.float64
    right: st.float64
    bottom: st.float64


Value.VARIANTS = [
    Value__Sint64,
    Value__Double,
    Value__String,
    Value__Color,
    Value__Point,
    Value__Rect,
]


@dataclass(frozen=True)
class VarId:
    scene: st.uint32
    key: str

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, VarId)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "VarId":
        v, buffer = bincode.deserialize(input, VarId)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "VarId":
        return bincode.deserialize_stream(input, VarId)


@dataclass(frozen=True)
class Watch:
    condition: "OpId"
    handler: "HandlerBlock"

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, Watch)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "Watch":
        v, buffer = bincode.deserialize(input, Watch)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def bincode_deserialize_stream(input: BinaryIO) -> "Watch":
        return bincode.deserialize_stream(input, Watch)
