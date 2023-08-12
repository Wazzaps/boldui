pub use bincode;
pub use serde;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

pub const R2A_MAGIC: &[u8] = b"BOLDUI\x00";
pub const A2R_MAGIC: &[u8] = b"BOLDUI\x01";
pub const R2EA_MAGIC: &[u8] = b"BOLDUI\x02";
pub const EA2R_MAGIC: &[u8] = b"BOLDUI\x03";
pub const WM_REQ_MAGIC: &[u8] = b"BOLDUI\x04";
pub const WM_RES_MAGIC: &[u8] = b"BOLDUI\x05";
pub const LATEST_MAJOR_VER: u16 = 0;
pub const LATEST_MINOR_VER: u16 = 1;
pub const LATEST_EA_MAJOR_VER: u16 = 0;
pub const LATEST_EA_MINOR_VER: u16 = 1;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct R2AHello {
    pub min_protocol_major_version: u16,
    pub min_protocol_minor_version: u16,
    pub max_protocol_major_version: u16,
    pub extra_len: u32,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct R2EAHello {
    pub min_protocol_major_version: u16,
    pub min_protocol_minor_version: u16,
    pub max_protocol_major_version: u16,
    pub extra_len: u32,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct R2AExtendedHello {}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct R2EAExtendedHello {}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum R2AMessage {
    Update(R2AUpdate),
    Open(R2AOpen),
    Error(Error),
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum R2EAMessage {
    Update(R2EAUpdate),
    Open(R2EAOpen),
    Error(Error),
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct R2AUpdate {
    pub replies: Vec<R2AReply>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct R2EAUpdate {
    pub changed_vars: Vec<(String, Value)>,
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
pub struct R2EAOpen {
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

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct Paint {
    pub color: Color,
    // TODO: image effects, etc
}

#[derive(Serialize, Deserialize, Debug, Copy, Clone, PartialEq)]
pub struct Point {
    pub left: f64,
    pub top: f64,
}

#[derive(Serialize, Deserialize, Debug, Copy, Clone, PartialEq)]
pub struct Rect {
    pub left: f64,
    pub top: f64,
    pub right: f64,
    pub bottom: f64,
}

// Make sure to update typecheck in `HandlerCmd::UpdateVar` handler in `eval_handler_cmd` when adding types
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub enum Value {
    Sint64(i64),
    Double(f64),
    String(String),
    Color(Color),
    Resource(ResourceId),
    VarRef(VarId),
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
pub struct EA2RHelloResponse {
    pub protocol_major_version: u16,
    pub protocol_minor_version: u16,
    pub extra_len: u32,
    pub error: Option<Error>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct EA2RExtendedHelloResponse {}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum A2RMessage {
    Update(A2RUpdate),
    Error(Error),
    CompressedUpdate(Vec<u8>),
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum EA2RMessage {
    CreatedExternalWidget { texture_info: Vec<u8> },
    SpontaneousUpdate,
    UpdateHandled,
    Error(Error),
}

pub type SceneId = u32;
pub type ResourceId = u32;

#[derive(Serialize, Deserialize, Debug, Copy, Clone, Default, Eq, PartialEq)]
pub struct OpId {
    pub scene_id: SceneId,
    pub idx: u32,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialOrd, Ord, Eq, PartialEq)]
pub struct VarId {
    pub key: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum OpsOperation {
    Value(Value),
    Var(VarId),
    GetTime,
    GetTimeAndClamp {
        low: OpId,
        high: OpId,
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
    FloorDiv {
        a: OpId,
        b: OpId,
    },
    Eq {
        a: OpId,
        b: OpId,
    },
    Neq {
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
    Or {
        a: OpId,
        b: OpId,
    },
    And {
        a: OpId,
        b: OpId,
    },
    GreaterThan {
        a: OpId,
        b: OpId,
    },
    Abs {
        a: OpId,
    },
    Sin {
        a: OpId,
    },
    Cos {
        a: OpId,
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
    MakeColor {
        r: OpId,
        g: OpId,
        b: OpId,
        a: OpId,
    },
    ToString {
        a: OpId,
    },
    /// Also works for videos
    GetImageDimensions {
        res: OpId,
    },
    GetPointTop {
        point: OpId,
    },
    GetPointLeft {
        point: OpId,
    },
    If {
        condition: OpId,
        then: OpId,
        or_else: OpId,
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
    DrawRoundRect {
        paint: OpId,
        rect: OpId,
        radius: OpId,
    },
    DrawCenteredText {
        text: OpId,
        paint: OpId,
        center: OpId,
    },
    DrawImage {
        res: OpId,
        top_left: OpId,
    },
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Watch {
    pub condition: OpId,
    pub handler: HandlerBlock,
}

#[derive(Serialize, Deserialize, Debug, Clone, Eq, PartialEq)]
pub enum EventType {
    MouseDown { rect: OpId },
    MouseUp { rect: OpId },
    MouseMove { rect: OpId },
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct EventHandler {
    event_type: EventType,
    handler: HandlerBlock,
    continue_handling: OpId,
}

#[derive(Serialize, Deserialize, Debug, Clone, Default)]
pub struct A2RUpdateScene {
    pub id: SceneId,
    pub attrs: BTreeMap<u32, OpId>,
    pub ops: Vec<OpsOperation>,
    pub cmds: Vec<CmdsCommand>,
    pub watches: Vec<Watch>,
    pub event_handlers: Vec<EventHandler>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum A2RReparentScene {
    /// Place as first sub-scene of target scene
    Inside(OpId),

    /// Place as next sibling of target scene
    After(OpId),

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
        scene: OpId,
        to: A2RReparentScene,
    },
    SetVar {
        var: VarId,
        value: OpId,
    },
    SetVarByRef {
        var: OpId,
        value: OpId,
    },
    DeleteVar {
        var: VarId,
        value: OpId,
    },
    DeleteVarByRef {
        var: OpId,
        value: OpId,
    },
    DebugMessage {
        msg: String,
    },
    Reply {
        path: String,
        params: Vec<OpId>,
    },
    Open {
        path: String,
    },
    If {
        condition: OpId,
        then: Vec<HandlerCmd>,
        or_else: Vec<HandlerCmd>,
    },
}

#[derive(Serialize, Deserialize, Debug, Clone, Default)]
pub struct HandlerBlock {
    pub ops: Vec<OpsOperation>,
    pub cmds: Vec<HandlerCmd>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ResourceChunk {
    pub id: ResourceId,
    pub offset: u64,
    pub data: Vec<u8>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ResourceDealloc {
    pub id: ResourceId,
    pub offset: u64,
    pub length: u64,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ExternalAppRequest {
    pub scene_id: SceneId,
    pub uri: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct A2RUpdate {
    pub updated_scenes: Vec<A2RUpdateScene>,
    pub run_blocks: Vec<HandlerBlock>,
    pub resource_chunks: Vec<ResourceChunk>,
    pub resource_deallocs: Vec<ResourceDealloc>,
    pub external_app_requests: Vec<ExternalAppRequest>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
#[repr(u32)]
pub enum SceneAttr {
    /// 2D transformation matrix
    Transform = 0,
    /// Affects how the scene is rendered, e.g. tint or foreground blur
    Paint,
    /// Affects how parts under the scene are rendered, e.g. tint or background blur
    BackdropPaint,
    /// Masks the scene
    Clip,
    /// The URI of the scene
    Uri,
    /// The initial size of the window (or the fixed size of the subscene)
    Size,
    /// An opaque id passed from the renderer as a query parameter, used to associate `open` requests with the opened window
    WindowId,
    /// The initial position of the window
    WindowInitialPosition,
    /// The initial state of the window, one of:
    WindowInitialState,
    /// The title of the window
    WindowTitle,
    /// The icon of the window
    WindowIcon,
    /// Whether the window should have decorations, one of:
    WindowDecorations,
}

#[derive(Debug, Clone)]
#[repr(C)]
pub struct WmHello {
    pub action: WmHelloAction,
}

#[derive(Debug, Clone)]
#[repr(u8)]
pub enum WmHelloAction {
    ConnectApp,
    AttachRenderer,
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
