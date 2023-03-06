pub use bincode;
pub use serde;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

pub const R2A_MAGIC: &[u8] = b"BOLDUI\x00";
pub const A2R_MAGIC: &[u8] = b"BOLDUI\x01";
pub const LATEST_MAJOR_VER: u16 = 0;
pub const LATEST_MINOR_VER: u16 = 1;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct R2AHello {
    pub min_protocol_major_version: u16,
    pub min_protocol_minor_version: u16,
    pub max_protocol_major_version: u16,
    pub extra_len: u32,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct R2AExtendedHello {}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum R2AMessage {
    Update(R2AUpdate),
    Open(R2AOpen),
    Error(Error),
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct R2AUpdate {
    pub replies: Vec<R2AReply>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct R2AReply {
    pub path: String,
    pub params: Vec<Value>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct R2AOpen {
    pub path: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Error {
    pub code: u64,
    pub text: String,
}

#[derive(Serialize, Deserialize, Debug, Copy, Clone, PartialEq, Eq)]
pub struct Color {
    pub r: u16,
    pub g: u16,
    pub b: u16,
    pub a: u16,
}

impl Color {
    pub fn from_hex(rgb: u32) -> Self {
        Self {
            r: (((rgb & 0xff0000) >> 16) as u16) << 8,
            g: (((rgb & 0x00ff00) >> 8) as u16) << 8,
            b: ((rgb & 0x0000ff) as u16) << 8,
            a: 0xffff,
        }
    }
    pub fn from_rgb8(r: u8, g: u8, b: u8) -> Self {
        Self {
            r: (r as u16) << 8,
            g: (g as u16) << 8,
            b: (b as u16) << 8,
            a: 0xffff,
        }
    }
    pub fn from_rgba8(r: u8, g: u8, b: u8, a: u8) -> Self {
        Self {
            r: (r as u16) << 8,
            g: (g as u16) << 8,
            b: (b as u16) << 8,
            a: (a as u16) << 8,
        }
    }
    pub fn from_rgb16(r: u16, g: u16, b: u16) -> Self {
        Self { r, g, b, a: 0xffff }
    }
    pub fn from_rgba16(r: u16, g: u16, b: u16, a: u16) -> Self {
        Self { r, g, b, a }
    }
}

// Make sure to update typecheck in `HandlerCmd::UpdateVar` handler in `eval_handler_cmd` when adding types
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub enum Value {
    Sint64(i64),
    Double(f64),
    String(String),
    Color(Color),
    Point {
        left: f64,
        top: f64,
    },
    Rect {
        left: f64,
        top: f64,
        right: f64,
        bottom: f64,
    },
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct A2RHelloResponse {
    pub protocol_major_version: u16,
    pub protocol_minor_version: u16,
    pub extra_len: u32,
    pub error: Option<Error>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct A2RExtendedHelloResponse {}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum A2RMessage {
    Update(A2RUpdate),
    Error(Error),
    CompressedUpdate(Vec<u8>),
}

pub type SceneId = u32;

#[derive(Serialize, Deserialize, Debug, Copy, Clone, Default, Eq, PartialEq)]
pub struct OpId {
    pub scene_id: SceneId,
    pub idx: u32,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct VarId {
    pub key: String,
    pub scene: SceneId,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum OpsOperation {
    Value(Value),
    Var(VarId),
    // TODO: Replace with `OpId`s
    GetTime {
        low_clamp: f64,
        high_clamp: f64,
    },
    Add {
        a: OpId,
        b: OpId,
    },
    Neg {
        a: OpId,
    },
    Mul {
        a: OpId,
        b: OpId,
    },
    Div {
        a: OpId,
        b: OpId,
    },
    Eq {
        a: OpId,
        b: OpId,
    },
    Min {
        a: OpId,
        b: OpId,
    },
    Max {
        a: OpId,
        b: OpId,
    },
    MakePoint {
        left: OpId,
        top: OpId,
    },
    MakeRectFromPoints {
        left_top: OpId,
        right_bottom: OpId,
    },
    MakeRectFromSides {
        left: OpId,
        top: OpId,
        right: OpId,
        bottom: OpId,
    },
    ToString {
        a: OpId,
    },
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum CmdsCommand {
    Clear {
        color: OpId,
    },
    DrawRect {
        paint: OpId,
        rect: OpId,
    },
    DrawCenteredText {
        text: OpId,
        paint: OpId,
        center: OpId,
    },
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Watch {
    pub condition: OpId,
    pub handler: HandlerBlock,
}

#[derive(Serialize, Deserialize, Debug, Clone, Eq, PartialEq)]
pub enum EventType {
    Click { rect: OpId },
}

#[derive(Serialize, Deserialize, Debug, Clone, Default)]
pub struct A2RUpdateScene {
    pub id: SceneId,
    pub paint: OpId,
    pub backdrop: OpId,
    pub transform: OpId,
    pub clip: OpId,
    pub uri: String,

    pub ops: Vec<OpsOperation>,
    pub cmds: Vec<CmdsCommand>,
    pub var_decls: BTreeMap<String, Value>,
    pub watches: Vec<Watch>,
    pub event_handlers: Vec<(EventType, HandlerBlock)>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum A2RReparentScene {
    /// Place as first sub-scene of target scene
    Inside(SceneId),

    /// Place as next sibling of target scene
    After(SceneId),

    /// Create window from scene
    Root,

    /// Will be deleted at the end of the update if not connected again
    Disconnect,

    /// Will not be rendered or processed at all, default state
    Hide,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum HandlerCmd {
    Nop,
    AllocateWindowId,
    ReparentScene {
        scene: SceneId,
        to: A2RReparentScene,
    },
    UpdateVar {
        var: VarId,
        value: OpId,
    },
    DebugMessage {
        msg: String,
    },
    Reply {
        path: String,
        params: Vec<OpId>,
    },
    If {
        condition: OpId,
        then: Box<HandlerCmd>,
        or_else: Box<HandlerCmd>,
    },
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct HandlerBlock {
    pub ops: Vec<OpsOperation>,
    pub cmds: Vec<HandlerCmd>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct A2RUpdate {
    pub updated_scenes: Vec<A2RUpdateScene>,
    pub run_blocks: Vec<HandlerBlock>,
}

// #[cfg(test)]
// mod tests {
//     use super::*;
//
//     #[test]
//     fn it_works() {
//         assert_eq!(1, 1);
//     }
// }
