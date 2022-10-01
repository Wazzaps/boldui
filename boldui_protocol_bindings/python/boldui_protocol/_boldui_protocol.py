# pyre-strict
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


@dataclass(frozen=True)
class A2RMessage__Update(A2RMessage):
    INDEX = 0  # type: int
    value: "A2RUpdate"


@dataclass(frozen=True)
class A2RMessage__Error(A2RMessage):
    INDEX = 1  # type: int
    value: "Error"


A2RMessage.VARIANTS = [
    A2RMessage__Update,
    A2RMessage__Error,
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

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, A2RUpdate)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "A2RUpdate":
        v, buffer = bincode.deserialize(input, A2RUpdate)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class A2RUpdateScene:
    id: st.uint32
    paint: "OpId"
    backdrop: "OpId"
    transform: "OpId"
    clip: "OpId"
    uri: str
    ops: typing.Sequence["OpsOperation"]
    cmds: typing.Sequence["CmdsCommand"]
    var_decls: typing.Dict[str, "Value"]

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, A2RUpdateScene)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "A2RUpdateScene":
        v, buffer = bincode.deserialize(input, A2RUpdateScene)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


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


@dataclass(frozen=True)
class CmdsCommand__Clear(CmdsCommand):
    INDEX = 0  # type: int
    color: "OpId"


@dataclass(frozen=True)
class CmdsCommand__DrawRect(CmdsCommand):
    INDEX = 1  # type: int
    paint: "OpId"
    rect: "OpId"


CmdsCommand.VARIANTS = [
    CmdsCommand__Clear,
    CmdsCommand__DrawRect,
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


@dataclass(frozen=True)
class HandlerCmd__Nop(HandlerCmd):
    INDEX = 0  # type: int
    pass


@dataclass(frozen=True)
class HandlerCmd__ReparentScene(HandlerCmd):
    INDEX = 1  # type: int
    scene: st.uint32
    to: "A2RReparentScene"


@dataclass(frozen=True)
class HandlerCmd__UpdateVar(HandlerCmd):
    INDEX = 2  # type: int
    var: "VarId"
    value: "OpId"


@dataclass(frozen=True)
class HandlerCmd__If(HandlerCmd):
    INDEX = 3  # type: int
    condition: "OpId"
    then: "HandlerCmd"
    or_else: "HandlerCmd"


HandlerCmd.VARIANTS = [
    HandlerCmd__Nop,
    HandlerCmd__ReparentScene,
    HandlerCmd__UpdateVar,
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
    low_clamp: st.float64
    high_clamp: st.float64


@dataclass(frozen=True)
class OpsOperation__Add(OpsOperation):
    INDEX = 3  # type: int
    a: "OpId"
    b: "OpId"


@dataclass(frozen=True)
class OpsOperation__Neg(OpsOperation):
    INDEX = 4  # type: int
    a: "OpId"


@dataclass(frozen=True)
class OpsOperation__MakePoint(OpsOperation):
    INDEX = 5  # type: int
    left: "OpId"
    top: "OpId"


@dataclass(frozen=True)
class OpsOperation__MakeRectFromPoints(OpsOperation):
    INDEX = 6  # type: int
    left_top: "OpId"
    right_bottom: "OpId"


@dataclass(frozen=True)
class OpsOperation__MakeRectFromSides(OpsOperation):
    INDEX = 7  # type: int
    left: "OpId"
    top: "OpId"
    right: "OpId"
    bottom: "OpId"


OpsOperation.VARIANTS = [
    OpsOperation__Value,
    OpsOperation__Var,
    OpsOperation__GetTime,
    OpsOperation__Add,
    OpsOperation__Neg,
    OpsOperation__MakePoint,
    OpsOperation__MakeRectFromPoints,
    OpsOperation__MakeRectFromSides,
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


@dataclass(frozen=True)
class R2AUpdate:
    pass

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, R2AUpdate)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "R2AUpdate":
        v, buffer = bincode.deserialize(input, R2AUpdate)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


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
    key: str
    scene: st.uint32

    def bincode_serialize(self) -> bytes:
        return bincode.serialize(self, VarId)

    @staticmethod
    def bincode_deserialize(input: bytes) -> "VarId":
        v, buffer = bincode.deserialize(input, VarId)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v
