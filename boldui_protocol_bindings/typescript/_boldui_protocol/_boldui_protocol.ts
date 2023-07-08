
import { Serializer, Deserializer } from '../serde/mod.ts';
import { BcsSerializer, BcsDeserializer } from '../bcs/mod.ts';
import { Optional, Seq, Tuple, ListTuple, unit, bool, int8, int16, int32, int64, int128, uint8, uint16, uint32, uint64, uint128, float32, float64, char, str, bytes } from '../serde/mod.ts';

export class A2RExtendedHelloResponse {
constructor () {
}

public serialize(serializer: Serializer): void {
}

static deserialize(deserializer: Deserializer): A2RExtendedHelloResponse {
  return new A2RExtendedHelloResponse();
}

}
export class A2RHelloResponse {

constructor (public protocol_major_version: uint16, public protocol_minor_version: uint16, public extra_len: uint32, public error: Optional<Error>) {
}

public serialize(serializer: Serializer): void {
  serializer.serializeU16(this.protocol_major_version);
  serializer.serializeU16(this.protocol_minor_version);
  serializer.serializeU32(this.extra_len);
  Helpers.serializeOptionError(this.error, serializer);
}

static deserialize(deserializer: Deserializer): A2RHelloResponse {
  const protocol_major_version = deserializer.deserializeU16();
  const protocol_minor_version = deserializer.deserializeU16();
  const extra_len = deserializer.deserializeU32();
  const error = Helpers.deserializeOptionError(deserializer);
  return new A2RHelloResponse(protocol_major_version,protocol_minor_version,extra_len,error);
}

}
interface FullMatchA2RMessage<R> {
  Update: (value: A2RMessageVariantUpdate) => R,
  Error: (value: A2RMessageVariantError) => R,
  CompressedUpdate: (value: A2RMessageVariantCompressedUpdate) => R,
}

interface PartialMatchA2RMessage<R> {
  Update?: (value: A2RMessageVariantUpdate) => R,
  Error?: (value: A2RMessageVariantError) => R,
  CompressedUpdate?: (value: A2RMessageVariantCompressedUpdate) => R,
  _: (value: A2RMessage) => R,

}

type MatchA2RMessage<R> = PartialMatchA2RMessage<R> | FullMatchA2RMessage<R>;

export abstract class A2RMessage {
  static _variant: string = undefined as unknown as string;
abstract serialize(serializer: Serializer): void;

static deserialize(deserializer: Deserializer): A2RMessage {
  const index = deserializer.deserializeVariantIndex();
  switch (index) {
    case 0: return A2RMessageVariantUpdate.load(deserializer);
    case 1: return A2RMessageVariantError.load(deserializer);
    case 2: return A2RMessageVariantCompressedUpdate.load(deserializer);
    default: throw new window.Error("Unknown variant index for A2RMessage: " + index);
  }
}
match<R>(handlers: MatchA2RMessage<R>): R {
  let handler = (handlers as any)[(this.constructor as any)._variant];
  return (handler || (handlers as any)['_'])(this);
}

}


export class A2RMessageVariantUpdate extends A2RMessage {
  static _variant = "Update";

constructor (public value: A2RUpdate) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(0);
  this.value.serialize(serializer);
}

static load(deserializer: Deserializer): A2RMessageVariantUpdate {
  const value = A2RUpdate.deserialize(deserializer);
  return new A2RMessageVariantUpdate(value);
}

}

export class A2RMessageVariantError extends A2RMessage {
  static _variant = "Error";

constructor (public value: Error) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(1);
  this.value.serialize(serializer);
}

static load(deserializer: Deserializer): A2RMessageVariantError {
  const value = Error.deserialize(deserializer);
  return new A2RMessageVariantError(value);
}

}

export class A2RMessageVariantCompressedUpdate extends A2RMessage {
  static _variant = "CompressedUpdate";

constructor (public value: Seq<uint8>) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(2);
  Helpers.serializeVectorU8(this.value, serializer);
}

static load(deserializer: Deserializer): A2RMessageVariantCompressedUpdate {
  const value = Helpers.deserializeVectorU8(deserializer);
  return new A2RMessageVariantCompressedUpdate(value);
}

}
interface FullMatchA2RReparentScene<R> {
  Inside: (value: A2RReparentSceneVariantInside) => R,
  After: (value: A2RReparentSceneVariantAfter) => R,
  Root: (value: A2RReparentSceneVariantRoot) => R,
  Disconnect: (value: A2RReparentSceneVariantDisconnect) => R,
  Hide: (value: A2RReparentSceneVariantHide) => R,
}

interface PartialMatchA2RReparentScene<R> {
  Inside?: (value: A2RReparentSceneVariantInside) => R,
  After?: (value: A2RReparentSceneVariantAfter) => R,
  Root?: (value: A2RReparentSceneVariantRoot) => R,
  Disconnect?: (value: A2RReparentSceneVariantDisconnect) => R,
  Hide?: (value: A2RReparentSceneVariantHide) => R,
  _: (value: A2RReparentScene) => R,

}

type MatchA2RReparentScene<R> = PartialMatchA2RReparentScene<R> | FullMatchA2RReparentScene<R>;

export abstract class A2RReparentScene {
  static _variant: string = undefined as unknown as string;
abstract serialize(serializer: Serializer): void;

static deserialize(deserializer: Deserializer): A2RReparentScene {
  const index = deserializer.deserializeVariantIndex();
  switch (index) {
    case 0: return A2RReparentSceneVariantInside.load(deserializer);
    case 1: return A2RReparentSceneVariantAfter.load(deserializer);
    case 2: return A2RReparentSceneVariantRoot.load(deserializer);
    case 3: return A2RReparentSceneVariantDisconnect.load(deserializer);
    case 4: return A2RReparentSceneVariantHide.load(deserializer);
    default: throw new window.Error("Unknown variant index for A2RReparentScene: " + index);
  }
}
match<R>(handlers: MatchA2RReparentScene<R>): R {
  let handler = (handlers as any)[(this.constructor as any)._variant];
  return (handler || (handlers as any)['_'])(this);
}

}


export class A2RReparentSceneVariantInside extends A2RReparentScene {
  static _variant = "Inside";

constructor (public value: uint32) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(0);
  serializer.serializeU32(this.value);
}

static load(deserializer: Deserializer): A2RReparentSceneVariantInside {
  const value = deserializer.deserializeU32();
  return new A2RReparentSceneVariantInside(value);
}

}

export class A2RReparentSceneVariantAfter extends A2RReparentScene {
  static _variant = "After";

constructor (public value: uint32) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(1);
  serializer.serializeU32(this.value);
}

static load(deserializer: Deserializer): A2RReparentSceneVariantAfter {
  const value = deserializer.deserializeU32();
  return new A2RReparentSceneVariantAfter(value);
}

}

export class A2RReparentSceneVariantRoot extends A2RReparentScene {
  static _variant = "Root";
constructor () {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(2);
}

static load(deserializer: Deserializer): A2RReparentSceneVariantRoot {
  return new A2RReparentSceneVariantRoot();
}

}

export class A2RReparentSceneVariantDisconnect extends A2RReparentScene {
  static _variant = "Disconnect";
constructor () {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(3);
}

static load(deserializer: Deserializer): A2RReparentSceneVariantDisconnect {
  return new A2RReparentSceneVariantDisconnect();
}

}

export class A2RReparentSceneVariantHide extends A2RReparentScene {
  static _variant = "Hide";
constructor () {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(4);
}

static load(deserializer: Deserializer): A2RReparentSceneVariantHide {
  return new A2RReparentSceneVariantHide();
}

}
export class A2RUpdate {

constructor (public updated_scenes: Seq<A2RUpdateScene>, public run_blocks: Seq<HandlerBlock>, public external_app_requests: Seq<ExternalAppRequest>) {
}

public serialize(serializer: Serializer): void {
  Helpers.serializeVectorA2rUpdateScene(this.updated_scenes, serializer);
  Helpers.serializeVectorHandlerBlock(this.run_blocks, serializer);
  Helpers.serializeVectorExternalAppRequest(this.external_app_requests, serializer);
}

static deserialize(deserializer: Deserializer): A2RUpdate {
  const updated_scenes = Helpers.deserializeVectorA2rUpdateScene(deserializer);
  const run_blocks = Helpers.deserializeVectorHandlerBlock(deserializer);
  const external_app_requests = Helpers.deserializeVectorExternalAppRequest(deserializer);
  return new A2RUpdate(updated_scenes,run_blocks,external_app_requests);
}

}
export class A2RUpdateScene {

constructor (public id: uint32, public paint: OpId, public backdrop: OpId, public transform: OpId, public clip: OpId, public uri: str, public dimensions: OpId, public ops: Seq<OpsOperation>, public cmds: Seq<CmdsCommand>, public var_decls: Map<str,Value>, public watches: Seq<Watch>, public event_handlers: Seq<Tuple<[EventType, HandlerBlock]>>) {
}

public serialize(serializer: Serializer): void {
  serializer.serializeU32(this.id);
  this.paint.serialize(serializer);
  this.backdrop.serialize(serializer);
  this.transform.serialize(serializer);
  this.clip.serialize(serializer);
  serializer.serializeStr(this.uri);
  this.dimensions.serialize(serializer);
  Helpers.serializeVectorOpsOperation(this.ops, serializer);
  Helpers.serializeVectorCmdsCommand(this.cmds, serializer);
  Helpers.serializeMapStrToValue(this.var_decls, serializer);
  Helpers.serializeVectorWatch(this.watches, serializer);
  Helpers.serializeVectorTuple2EventTypeHandlerBlock(this.event_handlers, serializer);
}

static deserialize(deserializer: Deserializer): A2RUpdateScene {
  const id = deserializer.deserializeU32();
  const paint = OpId.deserialize(deserializer);
  const backdrop = OpId.deserialize(deserializer);
  const transform = OpId.deserialize(deserializer);
  const clip = OpId.deserialize(deserializer);
  const uri = deserializer.deserializeStr();
  const dimensions = OpId.deserialize(deserializer);
  const ops = Helpers.deserializeVectorOpsOperation(deserializer);
  const cmds = Helpers.deserializeVectorCmdsCommand(deserializer);
  const var_decls = Helpers.deserializeMapStrToValue(deserializer);
  const watches = Helpers.deserializeVectorWatch(deserializer);
  const event_handlers = Helpers.deserializeVectorTuple2EventTypeHandlerBlock(deserializer);
  return new A2RUpdateScene(id,paint,backdrop,transform,clip,uri,dimensions,ops,cmds,var_decls,watches,event_handlers);
}

}
interface FullMatchCmdsCommand<R> {
  Clear: (value: CmdsCommandVariantClear) => R,
  DrawRect: (value: CmdsCommandVariantDrawRect) => R,
  DrawRoundRect: (value: CmdsCommandVariantDrawRoundRect) => R,
  DrawCenteredText: (value: CmdsCommandVariantDrawCenteredText) => R,
}

interface PartialMatchCmdsCommand<R> {
  Clear?: (value: CmdsCommandVariantClear) => R,
  DrawRect?: (value: CmdsCommandVariantDrawRect) => R,
  DrawRoundRect?: (value: CmdsCommandVariantDrawRoundRect) => R,
  DrawCenteredText?: (value: CmdsCommandVariantDrawCenteredText) => R,
  _: (value: CmdsCommand) => R,

}

type MatchCmdsCommand<R> = PartialMatchCmdsCommand<R> | FullMatchCmdsCommand<R>;

export abstract class CmdsCommand {
  static _variant: string = undefined as unknown as string;
abstract serialize(serializer: Serializer): void;

static deserialize(deserializer: Deserializer): CmdsCommand {
  const index = deserializer.deserializeVariantIndex();
  switch (index) {
    case 0: return CmdsCommandVariantClear.load(deserializer);
    case 1: return CmdsCommandVariantDrawRect.load(deserializer);
    case 2: return CmdsCommandVariantDrawRoundRect.load(deserializer);
    case 3: return CmdsCommandVariantDrawCenteredText.load(deserializer);
    default: throw new window.Error("Unknown variant index for CmdsCommand: " + index);
  }
}
match<R>(handlers: MatchCmdsCommand<R>): R {
  let handler = (handlers as any)[(this.constructor as any)._variant];
  return (handler || (handlers as any)['_'])(this);
}

}


export class CmdsCommandVariantClear extends CmdsCommand {
  static _variant = "Clear";

constructor (public color: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(0);
  this.color.serialize(serializer);
}

static load(deserializer: Deserializer): CmdsCommandVariantClear {
  const color = OpId.deserialize(deserializer);
  return new CmdsCommandVariantClear(color);
}

}

export class CmdsCommandVariantDrawRect extends CmdsCommand {
  static _variant = "DrawRect";

constructor (public paint: OpId, public rect: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(1);
  this.paint.serialize(serializer);
  this.rect.serialize(serializer);
}

static load(deserializer: Deserializer): CmdsCommandVariantDrawRect {
  const paint = OpId.deserialize(deserializer);
  const rect = OpId.deserialize(deserializer);
  return new CmdsCommandVariantDrawRect(paint,rect);
}

}

export class CmdsCommandVariantDrawRoundRect extends CmdsCommand {
  static _variant = "DrawRoundRect";

constructor (public paint: OpId, public rect: OpId, public radius: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(2);
  this.paint.serialize(serializer);
  this.rect.serialize(serializer);
  this.radius.serialize(serializer);
}

static load(deserializer: Deserializer): CmdsCommandVariantDrawRoundRect {
  const paint = OpId.deserialize(deserializer);
  const rect = OpId.deserialize(deserializer);
  const radius = OpId.deserialize(deserializer);
  return new CmdsCommandVariantDrawRoundRect(paint,rect,radius);
}

}

export class CmdsCommandVariantDrawCenteredText extends CmdsCommand {
  static _variant = "DrawCenteredText";

constructor (public text: OpId, public paint: OpId, public center: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(3);
  this.text.serialize(serializer);
  this.paint.serialize(serializer);
  this.center.serialize(serializer);
}

static load(deserializer: Deserializer): CmdsCommandVariantDrawCenteredText {
  const text = OpId.deserialize(deserializer);
  const paint = OpId.deserialize(deserializer);
  const center = OpId.deserialize(deserializer);
  return new CmdsCommandVariantDrawCenteredText(text,paint,center);
}

}
export class Color {

constructor (public r: uint16, public g: uint16, public b: uint16, public a: uint16) {
}

public serialize(serializer: Serializer): void {
  serializer.serializeU16(this.r);
  serializer.serializeU16(this.g);
  serializer.serializeU16(this.b);
  serializer.serializeU16(this.a);
}

static deserialize(deserializer: Deserializer): Color {
  const r = deserializer.deserializeU16();
  const g = deserializer.deserializeU16();
  const b = deserializer.deserializeU16();
  const a = deserializer.deserializeU16();
  return new Color(r,g,b,a);
}

}
export class EA2RExtendedHelloResponse {
constructor () {
}

public serialize(serializer: Serializer): void {
}

static deserialize(deserializer: Deserializer): EA2RExtendedHelloResponse {
  return new EA2RExtendedHelloResponse();
}

}
export class EA2RHelloResponse {

constructor (public protocol_major_version: uint16, public protocol_minor_version: uint16, public extra_len: uint32, public error: Optional<Error>) {
}

public serialize(serializer: Serializer): void {
  serializer.serializeU16(this.protocol_major_version);
  serializer.serializeU16(this.protocol_minor_version);
  serializer.serializeU32(this.extra_len);
  Helpers.serializeOptionError(this.error, serializer);
}

static deserialize(deserializer: Deserializer): EA2RHelloResponse {
  const protocol_major_version = deserializer.deserializeU16();
  const protocol_minor_version = deserializer.deserializeU16();
  const extra_len = deserializer.deserializeU32();
  const error = Helpers.deserializeOptionError(deserializer);
  return new EA2RHelloResponse(protocol_major_version,protocol_minor_version,extra_len,error);
}

}
interface FullMatchEA2RMessage<R> {
  CreatedExternalWidget: (value: EA2RMessageVariantCreatedExternalWidget) => R,
  SpontaneousUpdate: (value: EA2RMessageVariantSpontaneousUpdate) => R,
  UpdateHandled: (value: EA2RMessageVariantUpdateHandled) => R,
  Error: (value: EA2RMessageVariantError) => R,
}

interface PartialMatchEA2RMessage<R> {
  CreatedExternalWidget?: (value: EA2RMessageVariantCreatedExternalWidget) => R,
  SpontaneousUpdate?: (value: EA2RMessageVariantSpontaneousUpdate) => R,
  UpdateHandled?: (value: EA2RMessageVariantUpdateHandled) => R,
  Error?: (value: EA2RMessageVariantError) => R,
  _: (value: EA2RMessage) => R,

}

type MatchEA2RMessage<R> = PartialMatchEA2RMessage<R> | FullMatchEA2RMessage<R>;

export abstract class EA2RMessage {
  static _variant: string = undefined as unknown as string;
abstract serialize(serializer: Serializer): void;

static deserialize(deserializer: Deserializer): EA2RMessage {
  const index = deserializer.deserializeVariantIndex();
  switch (index) {
    case 0: return EA2RMessageVariantCreatedExternalWidget.load(deserializer);
    case 1: return EA2RMessageVariantSpontaneousUpdate.load(deserializer);
    case 2: return EA2RMessageVariantUpdateHandled.load(deserializer);
    case 3: return EA2RMessageVariantError.load(deserializer);
    default: throw new window.Error("Unknown variant index for EA2RMessage: " + index);
  }
}
match<R>(handlers: MatchEA2RMessage<R>): R {
  let handler = (handlers as any)[(this.constructor as any)._variant];
  return (handler || (handlers as any)['_'])(this);
}

}


export class EA2RMessageVariantCreatedExternalWidget extends EA2RMessage {
  static _variant = "CreatedExternalWidget";

constructor (public texture_info: Seq<uint8>) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(0);
  Helpers.serializeVectorU8(this.texture_info, serializer);
}

static load(deserializer: Deserializer): EA2RMessageVariantCreatedExternalWidget {
  const texture_info = Helpers.deserializeVectorU8(deserializer);
  return new EA2RMessageVariantCreatedExternalWidget(texture_info);
}

}

export class EA2RMessageVariantSpontaneousUpdate extends EA2RMessage {
  static _variant = "SpontaneousUpdate";
constructor () {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(1);
}

static load(deserializer: Deserializer): EA2RMessageVariantSpontaneousUpdate {
  return new EA2RMessageVariantSpontaneousUpdate();
}

}

export class EA2RMessageVariantUpdateHandled extends EA2RMessage {
  static _variant = "UpdateHandled";
constructor () {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(2);
}

static load(deserializer: Deserializer): EA2RMessageVariantUpdateHandled {
  return new EA2RMessageVariantUpdateHandled();
}

}

export class EA2RMessageVariantError extends EA2RMessage {
  static _variant = "Error";

constructor (public value: Error) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(3);
  this.value.serialize(serializer);
}

static load(deserializer: Deserializer): EA2RMessageVariantError {
  const value = Error.deserialize(deserializer);
  return new EA2RMessageVariantError(value);
}

}
export class Error {

constructor (public code: uint64, public text: str) {
}

public serialize(serializer: Serializer): void {
  serializer.serializeU64(this.code);
  serializer.serializeStr(this.text);
}

static deserialize(deserializer: Deserializer): Error {
  const code = deserializer.deserializeU64();
  const text = deserializer.deserializeStr();
  return new Error(code,text);
}

}
interface FullMatchEventType<R> {
  Click: (value: EventTypeVariantClick) => R,
}

interface PartialMatchEventType<R> {
  Click?: (value: EventTypeVariantClick) => R,
  _: (value: EventType) => R,

}

type MatchEventType<R> = PartialMatchEventType<R> | FullMatchEventType<R>;

export abstract class EventType {
  static _variant: string = undefined as unknown as string;
abstract serialize(serializer: Serializer): void;

static deserialize(deserializer: Deserializer): EventType {
  const index = deserializer.deserializeVariantIndex();
  switch (index) {
    case 0: return EventTypeVariantClick.load(deserializer);
    default: throw new window.Error("Unknown variant index for EventType: " + index);
  }
}
match<R>(handlers: MatchEventType<R>): R {
  let handler = (handlers as any)[(this.constructor as any)._variant];
  return (handler || (handlers as any)['_'])(this);
}

}


export class EventTypeVariantClick extends EventType {
  static _variant = "Click";

constructor (public rect: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(0);
  this.rect.serialize(serializer);
}

static load(deserializer: Deserializer): EventTypeVariantClick {
  const rect = OpId.deserialize(deserializer);
  return new EventTypeVariantClick(rect);
}

}
export class ExternalAppRequest {

constructor (public scene_id: uint32, public uri: str) {
}

public serialize(serializer: Serializer): void {
  serializer.serializeU32(this.scene_id);
  serializer.serializeStr(this.uri);
}

static deserialize(deserializer: Deserializer): ExternalAppRequest {
  const scene_id = deserializer.deserializeU32();
  const uri = deserializer.deserializeStr();
  return new ExternalAppRequest(scene_id,uri);
}

}
export class HandlerBlock {

constructor (public ops: Seq<OpsOperation>, public cmds: Seq<HandlerCmd>) {
}

public serialize(serializer: Serializer): void {
  Helpers.serializeVectorOpsOperation(this.ops, serializer);
  Helpers.serializeVectorHandlerCmd(this.cmds, serializer);
}

static deserialize(deserializer: Deserializer): HandlerBlock {
  const ops = Helpers.deserializeVectorOpsOperation(deserializer);
  const cmds = Helpers.deserializeVectorHandlerCmd(deserializer);
  return new HandlerBlock(ops,cmds);
}

}
interface FullMatchHandlerCmd<R> {
  Nop: (value: HandlerCmdVariantNop) => R,
  AllocateWindowId: (value: HandlerCmdVariantAllocateWindowId) => R,
  ReparentScene: (value: HandlerCmdVariantReparentScene) => R,
  UpdateVar: (value: HandlerCmdVariantUpdateVar) => R,
  DebugMessage: (value: HandlerCmdVariantDebugMessage) => R,
  Reply: (value: HandlerCmdVariantReply) => R,
  If: (value: HandlerCmdVariantIf) => R,
}

interface PartialMatchHandlerCmd<R> {
  Nop?: (value: HandlerCmdVariantNop) => R,
  AllocateWindowId?: (value: HandlerCmdVariantAllocateWindowId) => R,
  ReparentScene?: (value: HandlerCmdVariantReparentScene) => R,
  UpdateVar?: (value: HandlerCmdVariantUpdateVar) => R,
  DebugMessage?: (value: HandlerCmdVariantDebugMessage) => R,
  Reply?: (value: HandlerCmdVariantReply) => R,
  If?: (value: HandlerCmdVariantIf) => R,
  _: (value: HandlerCmd) => R,

}

type MatchHandlerCmd<R> = PartialMatchHandlerCmd<R> | FullMatchHandlerCmd<R>;

export abstract class HandlerCmd {
  static _variant: string = undefined as unknown as string;
abstract serialize(serializer: Serializer): void;

static deserialize(deserializer: Deserializer): HandlerCmd {
  const index = deserializer.deserializeVariantIndex();
  switch (index) {
    case 0: return HandlerCmdVariantNop.load(deserializer);
    case 1: return HandlerCmdVariantAllocateWindowId.load(deserializer);
    case 2: return HandlerCmdVariantReparentScene.load(deserializer);
    case 3: return HandlerCmdVariantUpdateVar.load(deserializer);
    case 4: return HandlerCmdVariantDebugMessage.load(deserializer);
    case 5: return HandlerCmdVariantReply.load(deserializer);
    case 6: return HandlerCmdVariantIf.load(deserializer);
    default: throw new window.Error("Unknown variant index for HandlerCmd: " + index);
  }
}
match<R>(handlers: MatchHandlerCmd<R>): R {
  let handler = (handlers as any)[(this.constructor as any)._variant];
  return (handler || (handlers as any)['_'])(this);
}

}


export class HandlerCmdVariantNop extends HandlerCmd {
  static _variant = "Nop";
constructor () {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(0);
}

static load(deserializer: Deserializer): HandlerCmdVariantNop {
  return new HandlerCmdVariantNop();
}

}

export class HandlerCmdVariantAllocateWindowId extends HandlerCmd {
  static _variant = "AllocateWindowId";
constructor () {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(1);
}

static load(deserializer: Deserializer): HandlerCmdVariantAllocateWindowId {
  return new HandlerCmdVariantAllocateWindowId();
}

}

export class HandlerCmdVariantReparentScene extends HandlerCmd {
  static _variant = "ReparentScene";

constructor (public scene: uint32, public to: A2RReparentScene) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(2);
  serializer.serializeU32(this.scene);
  this.to.serialize(serializer);
}

static load(deserializer: Deserializer): HandlerCmdVariantReparentScene {
  const scene = deserializer.deserializeU32();
  const to = A2RReparentScene.deserialize(deserializer);
  return new HandlerCmdVariantReparentScene(scene,to);
}

}

export class HandlerCmdVariantUpdateVar extends HandlerCmd {
  static _variant = "UpdateVar";

constructor (public var_: VarId, public value: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(3);
  this.var_.serialize(serializer);
  this.value.serialize(serializer);
}

static load(deserializer: Deserializer): HandlerCmdVariantUpdateVar {
  const var_ = VarId.deserialize(deserializer);
  const value = OpId.deserialize(deserializer);
  return new HandlerCmdVariantUpdateVar(var_,value);
}

}

export class HandlerCmdVariantDebugMessage extends HandlerCmd {
  static _variant = "DebugMessage";

constructor (public msg: str) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(4);
  serializer.serializeStr(this.msg);
}

static load(deserializer: Deserializer): HandlerCmdVariantDebugMessage {
  const msg = deserializer.deserializeStr();
  return new HandlerCmdVariantDebugMessage(msg);
}

}

export class HandlerCmdVariantReply extends HandlerCmd {
  static _variant = "Reply";

constructor (public path: str, public params: Seq<OpId>) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(5);
  serializer.serializeStr(this.path);
  Helpers.serializeVectorOpId(this.params, serializer);
}

static load(deserializer: Deserializer): HandlerCmdVariantReply {
  const path = deserializer.deserializeStr();
  const params = Helpers.deserializeVectorOpId(deserializer);
  return new HandlerCmdVariantReply(path,params);
}

}

export class HandlerCmdVariantIf extends HandlerCmd {
  static _variant = "If";

constructor (public condition: OpId, public then: HandlerCmd, public or_else: HandlerCmd) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(6);
  this.condition.serialize(serializer);
  this.then.serialize(serializer);
  this.or_else.serialize(serializer);
}

static load(deserializer: Deserializer): HandlerCmdVariantIf {
  const condition = OpId.deserialize(deserializer);
  const then = HandlerCmd.deserialize(deserializer);
  const or_else = HandlerCmd.deserialize(deserializer);
  return new HandlerCmdVariantIf(condition,then,or_else);
}

}
export class OpId {

constructor (public scene_id: uint32, public idx: uint32) {
}

public serialize(serializer: Serializer): void {
  serializer.serializeU32(this.scene_id);
  serializer.serializeU32(this.idx);
}

static deserialize(deserializer: Deserializer): OpId {
  const scene_id = deserializer.deserializeU32();
  const idx = deserializer.deserializeU32();
  return new OpId(scene_id,idx);
}

}
interface FullMatchOpsOperation<R> {
  Value: (value: OpsOperationVariantValue) => R,
  Var: (value: OpsOperationVariantVar) => R,
  GetTime: (value: OpsOperationVariantGetTime) => R,
  GetTimeAndClamp: (value: OpsOperationVariantGetTimeAndClamp) => R,
  Add: (value: OpsOperationVariantAdd) => R,
  Neg: (value: OpsOperationVariantNeg) => R,
  Mul: (value: OpsOperationVariantMul) => R,
  Div: (value: OpsOperationVariantDiv) => R,
  FloorDiv: (value: OpsOperationVariantFloorDiv) => R,
  Eq: (value: OpsOperationVariantEq) => R,
  Min: (value: OpsOperationVariantMin) => R,
  Max: (value: OpsOperationVariantMax) => R,
  Abs: (value: OpsOperationVariantAbs) => R,
  Sin: (value: OpsOperationVariantSin) => R,
  Cos: (value: OpsOperationVariantCos) => R,
  MakePoint: (value: OpsOperationVariantMakePoint) => R,
  MakeRectFromPoints: (value: OpsOperationVariantMakeRectFromPoints) => R,
  MakeRectFromSides: (value: OpsOperationVariantMakeRectFromSides) => R,
  ToString: (value: OpsOperationVariantToString) => R,
}

interface PartialMatchOpsOperation<R> {
  Value?: (value: OpsOperationVariantValue) => R,
  Var?: (value: OpsOperationVariantVar) => R,
  GetTime?: (value: OpsOperationVariantGetTime) => R,
  GetTimeAndClamp?: (value: OpsOperationVariantGetTimeAndClamp) => R,
  Add?: (value: OpsOperationVariantAdd) => R,
  Neg?: (value: OpsOperationVariantNeg) => R,
  Mul?: (value: OpsOperationVariantMul) => R,
  Div?: (value: OpsOperationVariantDiv) => R,
  FloorDiv?: (value: OpsOperationVariantFloorDiv) => R,
  Eq?: (value: OpsOperationVariantEq) => R,
  Min?: (value: OpsOperationVariantMin) => R,
  Max?: (value: OpsOperationVariantMax) => R,
  Abs?: (value: OpsOperationVariantAbs) => R,
  Sin?: (value: OpsOperationVariantSin) => R,
  Cos?: (value: OpsOperationVariantCos) => R,
  MakePoint?: (value: OpsOperationVariantMakePoint) => R,
  MakeRectFromPoints?: (value: OpsOperationVariantMakeRectFromPoints) => R,
  MakeRectFromSides?: (value: OpsOperationVariantMakeRectFromSides) => R,
  ToString?: (value: OpsOperationVariantToString) => R,
  _: (value: OpsOperation) => R,

}

type MatchOpsOperation<R> = PartialMatchOpsOperation<R> | FullMatchOpsOperation<R>;

export abstract class OpsOperation {
  static _variant: string = undefined as unknown as string;
abstract serialize(serializer: Serializer): void;

static deserialize(deserializer: Deserializer): OpsOperation {
  const index = deserializer.deserializeVariantIndex();
  switch (index) {
    case 0: return OpsOperationVariantValue.load(deserializer);
    case 1: return OpsOperationVariantVar.load(deserializer);
    case 2: return OpsOperationVariantGetTime.load(deserializer);
    case 3: return OpsOperationVariantGetTimeAndClamp.load(deserializer);
    case 4: return OpsOperationVariantAdd.load(deserializer);
    case 5: return OpsOperationVariantNeg.load(deserializer);
    case 6: return OpsOperationVariantMul.load(deserializer);
    case 7: return OpsOperationVariantDiv.load(deserializer);
    case 8: return OpsOperationVariantFloorDiv.load(deserializer);
    case 9: return OpsOperationVariantEq.load(deserializer);
    case 10: return OpsOperationVariantMin.load(deserializer);
    case 11: return OpsOperationVariantMax.load(deserializer);
    case 12: return OpsOperationVariantAbs.load(deserializer);
    case 13: return OpsOperationVariantSin.load(deserializer);
    case 14: return OpsOperationVariantCos.load(deserializer);
    case 15: return OpsOperationVariantMakePoint.load(deserializer);
    case 16: return OpsOperationVariantMakeRectFromPoints.load(deserializer);
    case 17: return OpsOperationVariantMakeRectFromSides.load(deserializer);
    case 18: return OpsOperationVariantToString.load(deserializer);
    default: throw new window.Error("Unknown variant index for OpsOperation: " + index);
  }
}
match<R>(handlers: MatchOpsOperation<R>): R {
  let handler = (handlers as any)[(this.constructor as any)._variant];
  return (handler || (handlers as any)['_'])(this);
}

}


export class OpsOperationVariantValue extends OpsOperation {
  static _variant = "Value";

constructor (public value: Value) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(0);
  this.value.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantValue {
  const value = Value.deserialize(deserializer);
  return new OpsOperationVariantValue(value);
}

}

export class OpsOperationVariantVar extends OpsOperation {
  static _variant = "Var";

constructor (public value: VarId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(1);
  this.value.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantVar {
  const value = VarId.deserialize(deserializer);
  return new OpsOperationVariantVar(value);
}

}

export class OpsOperationVariantGetTime extends OpsOperation {
  static _variant = "GetTime";
constructor () {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(2);
}

static load(deserializer: Deserializer): OpsOperationVariantGetTime {
  return new OpsOperationVariantGetTime();
}

}

export class OpsOperationVariantGetTimeAndClamp extends OpsOperation {
  static _variant = "GetTimeAndClamp";

constructor (public low: OpId, public high: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(3);
  this.low.serialize(serializer);
  this.high.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantGetTimeAndClamp {
  const low = OpId.deserialize(deserializer);
  const high = OpId.deserialize(deserializer);
  return new OpsOperationVariantGetTimeAndClamp(low,high);
}

}

export class OpsOperationVariantAdd extends OpsOperation {
  static _variant = "Add";

constructor (public a: OpId, public b: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(4);
  this.a.serialize(serializer);
  this.b.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantAdd {
  const a = OpId.deserialize(deserializer);
  const b = OpId.deserialize(deserializer);
  return new OpsOperationVariantAdd(a,b);
}

}

export class OpsOperationVariantNeg extends OpsOperation {
  static _variant = "Neg";

constructor (public a: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(5);
  this.a.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantNeg {
  const a = OpId.deserialize(deserializer);
  return new OpsOperationVariantNeg(a);
}

}

export class OpsOperationVariantMul extends OpsOperation {
  static _variant = "Mul";

constructor (public a: OpId, public b: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(6);
  this.a.serialize(serializer);
  this.b.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantMul {
  const a = OpId.deserialize(deserializer);
  const b = OpId.deserialize(deserializer);
  return new OpsOperationVariantMul(a,b);
}

}

export class OpsOperationVariantDiv extends OpsOperation {
  static _variant = "Div";

constructor (public a: OpId, public b: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(7);
  this.a.serialize(serializer);
  this.b.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantDiv {
  const a = OpId.deserialize(deserializer);
  const b = OpId.deserialize(deserializer);
  return new OpsOperationVariantDiv(a,b);
}

}

export class OpsOperationVariantFloorDiv extends OpsOperation {
  static _variant = "FloorDiv";

constructor (public a: OpId, public b: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(8);
  this.a.serialize(serializer);
  this.b.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantFloorDiv {
  const a = OpId.deserialize(deserializer);
  const b = OpId.deserialize(deserializer);
  return new OpsOperationVariantFloorDiv(a,b);
}

}

export class OpsOperationVariantEq extends OpsOperation {
  static _variant = "Eq";

constructor (public a: OpId, public b: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(9);
  this.a.serialize(serializer);
  this.b.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantEq {
  const a = OpId.deserialize(deserializer);
  const b = OpId.deserialize(deserializer);
  return new OpsOperationVariantEq(a,b);
}

}

export class OpsOperationVariantMin extends OpsOperation {
  static _variant = "Min";

constructor (public a: OpId, public b: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(10);
  this.a.serialize(serializer);
  this.b.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantMin {
  const a = OpId.deserialize(deserializer);
  const b = OpId.deserialize(deserializer);
  return new OpsOperationVariantMin(a,b);
}

}

export class OpsOperationVariantMax extends OpsOperation {
  static _variant = "Max";

constructor (public a: OpId, public b: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(11);
  this.a.serialize(serializer);
  this.b.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantMax {
  const a = OpId.deserialize(deserializer);
  const b = OpId.deserialize(deserializer);
  return new OpsOperationVariantMax(a,b);
}

}

export class OpsOperationVariantAbs extends OpsOperation {
  static _variant = "Abs";

constructor (public a: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(12);
  this.a.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantAbs {
  const a = OpId.deserialize(deserializer);
  return new OpsOperationVariantAbs(a);
}

}

export class OpsOperationVariantSin extends OpsOperation {
  static _variant = "Sin";

constructor (public a: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(13);
  this.a.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantSin {
  const a = OpId.deserialize(deserializer);
  return new OpsOperationVariantSin(a);
}

}

export class OpsOperationVariantCos extends OpsOperation {
  static _variant = "Cos";

constructor (public a: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(14);
  this.a.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantCos {
  const a = OpId.deserialize(deserializer);
  return new OpsOperationVariantCos(a);
}

}

export class OpsOperationVariantMakePoint extends OpsOperation {
  static _variant = "MakePoint";

constructor (public left: OpId, public top: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(15);
  this.left.serialize(serializer);
  this.top.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantMakePoint {
  const left = OpId.deserialize(deserializer);
  const top = OpId.deserialize(deserializer);
  return new OpsOperationVariantMakePoint(left,top);
}

}

export class OpsOperationVariantMakeRectFromPoints extends OpsOperation {
  static _variant = "MakeRectFromPoints";

constructor (public left_top: OpId, public right_bottom: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(16);
  this.left_top.serialize(serializer);
  this.right_bottom.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantMakeRectFromPoints {
  const left_top = OpId.deserialize(deserializer);
  const right_bottom = OpId.deserialize(deserializer);
  return new OpsOperationVariantMakeRectFromPoints(left_top,right_bottom);
}

}

export class OpsOperationVariantMakeRectFromSides extends OpsOperation {
  static _variant = "MakeRectFromSides";

constructor (public left: OpId, public top: OpId, public right: OpId, public bottom: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(17);
  this.left.serialize(serializer);
  this.top.serialize(serializer);
  this.right.serialize(serializer);
  this.bottom.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantMakeRectFromSides {
  const left = OpId.deserialize(deserializer);
  const top = OpId.deserialize(deserializer);
  const right = OpId.deserialize(deserializer);
  const bottom = OpId.deserialize(deserializer);
  return new OpsOperationVariantMakeRectFromSides(left,top,right,bottom);
}

}

export class OpsOperationVariantToString extends OpsOperation {
  static _variant = "ToString";

constructor (public a: OpId) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(18);
  this.a.serialize(serializer);
}

static load(deserializer: Deserializer): OpsOperationVariantToString {
  const a = OpId.deserialize(deserializer);
  return new OpsOperationVariantToString(a);
}

}
export class R2AExtendedHello {
constructor () {
}

public serialize(serializer: Serializer): void {
}

static deserialize(deserializer: Deserializer): R2AExtendedHello {
  return new R2AExtendedHello();
}

}
export class R2AHello {

constructor (public min_protocol_major_version: uint16, public min_protocol_minor_version: uint16, public max_protocol_major_version: uint16, public extra_len: uint32) {
}

public serialize(serializer: Serializer): void {
  serializer.serializeU16(this.min_protocol_major_version);
  serializer.serializeU16(this.min_protocol_minor_version);
  serializer.serializeU16(this.max_protocol_major_version);
  serializer.serializeU32(this.extra_len);
}

static deserialize(deserializer: Deserializer): R2AHello {
  const min_protocol_major_version = deserializer.deserializeU16();
  const min_protocol_minor_version = deserializer.deserializeU16();
  const max_protocol_major_version = deserializer.deserializeU16();
  const extra_len = deserializer.deserializeU32();
  return new R2AHello(min_protocol_major_version,min_protocol_minor_version,max_protocol_major_version,extra_len);
}

}
interface FullMatchR2AMessage<R> {
  Update: (value: R2AMessageVariantUpdate) => R,
  Open: (value: R2AMessageVariantOpen) => R,
  Error: (value: R2AMessageVariantError) => R,
}

interface PartialMatchR2AMessage<R> {
  Update?: (value: R2AMessageVariantUpdate) => R,
  Open?: (value: R2AMessageVariantOpen) => R,
  Error?: (value: R2AMessageVariantError) => R,
  _: (value: R2AMessage) => R,

}

type MatchR2AMessage<R> = PartialMatchR2AMessage<R> | FullMatchR2AMessage<R>;

export abstract class R2AMessage {
  static _variant: string = undefined as unknown as string;
abstract serialize(serializer: Serializer): void;

static deserialize(deserializer: Deserializer): R2AMessage {
  const index = deserializer.deserializeVariantIndex();
  switch (index) {
    case 0: return R2AMessageVariantUpdate.load(deserializer);
    case 1: return R2AMessageVariantOpen.load(deserializer);
    case 2: return R2AMessageVariantError.load(deserializer);
    default: throw new window.Error("Unknown variant index for R2AMessage: " + index);
  }
}
match<R>(handlers: MatchR2AMessage<R>): R {
  let handler = (handlers as any)[(this.constructor as any)._variant];
  return (handler || (handlers as any)['_'])(this);
}

}


export class R2AMessageVariantUpdate extends R2AMessage {
  static _variant = "Update";

constructor (public value: R2AUpdate) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(0);
  this.value.serialize(serializer);
}

static load(deserializer: Deserializer): R2AMessageVariantUpdate {
  const value = R2AUpdate.deserialize(deserializer);
  return new R2AMessageVariantUpdate(value);
}

}

export class R2AMessageVariantOpen extends R2AMessage {
  static _variant = "Open";

constructor (public value: R2AOpen) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(1);
  this.value.serialize(serializer);
}

static load(deserializer: Deserializer): R2AMessageVariantOpen {
  const value = R2AOpen.deserialize(deserializer);
  return new R2AMessageVariantOpen(value);
}

}

export class R2AMessageVariantError extends R2AMessage {
  static _variant = "Error";

constructor (public value: Error) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(2);
  this.value.serialize(serializer);
}

static load(deserializer: Deserializer): R2AMessageVariantError {
  const value = Error.deserialize(deserializer);
  return new R2AMessageVariantError(value);
}

}
export class R2AOpen {

constructor (public path: str) {
}

public serialize(serializer: Serializer): void {
  serializer.serializeStr(this.path);
}

static deserialize(deserializer: Deserializer): R2AOpen {
  const path = deserializer.deserializeStr();
  return new R2AOpen(path);
}

}
export class R2AReply {

constructor (public path: str, public params: Seq<Value>) {
}

public serialize(serializer: Serializer): void {
  serializer.serializeStr(this.path);
  Helpers.serializeVectorValue(this.params, serializer);
}

static deserialize(deserializer: Deserializer): R2AReply {
  const path = deserializer.deserializeStr();
  const params = Helpers.deserializeVectorValue(deserializer);
  return new R2AReply(path,params);
}

}
export class R2AUpdate {

constructor (public replies: Seq<R2AReply>) {
}

public serialize(serializer: Serializer): void {
  Helpers.serializeVectorR2aReply(this.replies, serializer);
}

static deserialize(deserializer: Deserializer): R2AUpdate {
  const replies = Helpers.deserializeVectorR2aReply(deserializer);
  return new R2AUpdate(replies);
}

}
export class R2EAExtendedHello {
constructor () {
}

public serialize(serializer: Serializer): void {
}

static deserialize(deserializer: Deserializer): R2EAExtendedHello {
  return new R2EAExtendedHello();
}

}
export class R2EAHello {

constructor (public min_protocol_major_version: uint16, public min_protocol_minor_version: uint16, public max_protocol_major_version: uint16, public extra_len: uint32) {
}

public serialize(serializer: Serializer): void {
  serializer.serializeU16(this.min_protocol_major_version);
  serializer.serializeU16(this.min_protocol_minor_version);
  serializer.serializeU16(this.max_protocol_major_version);
  serializer.serializeU32(this.extra_len);
}

static deserialize(deserializer: Deserializer): R2EAHello {
  const min_protocol_major_version = deserializer.deserializeU16();
  const min_protocol_minor_version = deserializer.deserializeU16();
  const max_protocol_major_version = deserializer.deserializeU16();
  const extra_len = deserializer.deserializeU32();
  return new R2EAHello(min_protocol_major_version,min_protocol_minor_version,max_protocol_major_version,extra_len);
}

}
interface FullMatchR2EAMessage<R> {
  Update: (value: R2EAMessageVariantUpdate) => R,
  Open: (value: R2EAMessageVariantOpen) => R,
  Error: (value: R2EAMessageVariantError) => R,
}

interface PartialMatchR2EAMessage<R> {
  Update?: (value: R2EAMessageVariantUpdate) => R,
  Open?: (value: R2EAMessageVariantOpen) => R,
  Error?: (value: R2EAMessageVariantError) => R,
  _: (value: R2EAMessage) => R,

}

type MatchR2EAMessage<R> = PartialMatchR2EAMessage<R> | FullMatchR2EAMessage<R>;

export abstract class R2EAMessage {
  static _variant: string = undefined as unknown as string;
abstract serialize(serializer: Serializer): void;

static deserialize(deserializer: Deserializer): R2EAMessage {
  const index = deserializer.deserializeVariantIndex();
  switch (index) {
    case 0: return R2EAMessageVariantUpdate.load(deserializer);
    case 1: return R2EAMessageVariantOpen.load(deserializer);
    case 2: return R2EAMessageVariantError.load(deserializer);
    default: throw new window.Error("Unknown variant index for R2EAMessage: " + index);
  }
}
match<R>(handlers: MatchR2EAMessage<R>): R {
  let handler = (handlers as any)[(this.constructor as any)._variant];
  return (handler || (handlers as any)['_'])(this);
}

}


export class R2EAMessageVariantUpdate extends R2EAMessage {
  static _variant = "Update";

constructor (public value: R2EAUpdate) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(0);
  this.value.serialize(serializer);
}

static load(deserializer: Deserializer): R2EAMessageVariantUpdate {
  const value = R2EAUpdate.deserialize(deserializer);
  return new R2EAMessageVariantUpdate(value);
}

}

export class R2EAMessageVariantOpen extends R2EAMessage {
  static _variant = "Open";

constructor (public value: R2EAOpen) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(1);
  this.value.serialize(serializer);
}

static load(deserializer: Deserializer): R2EAMessageVariantOpen {
  const value = R2EAOpen.deserialize(deserializer);
  return new R2EAMessageVariantOpen(value);
}

}

export class R2EAMessageVariantError extends R2EAMessage {
  static _variant = "Error";

constructor (public value: Error) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(2);
  this.value.serialize(serializer);
}

static load(deserializer: Deserializer): R2EAMessageVariantError {
  const value = Error.deserialize(deserializer);
  return new R2EAMessageVariantError(value);
}

}
export class R2EAOpen {

constructor (public path: str) {
}

public serialize(serializer: Serializer): void {
  serializer.serializeStr(this.path);
}

static deserialize(deserializer: Deserializer): R2EAOpen {
  const path = deserializer.deserializeStr();
  return new R2EAOpen(path);
}

}
export class R2EAUpdate {

constructor (public changed_vars: Seq<Tuple<[str, Value]>>) {
}

public serialize(serializer: Serializer): void {
  Helpers.serializeVectorTuple2StrValue(this.changed_vars, serializer);
}

static deserialize(deserializer: Deserializer): R2EAUpdate {
  const changed_vars = Helpers.deserializeVectorTuple2StrValue(deserializer);
  return new R2EAUpdate(changed_vars);
}

}
interface FullMatchValue<R> {
  Sint64: (value: ValueVariantSint64) => R,
  Double: (value: ValueVariantDouble) => R,
  String: (value: ValueVariantString) => R,
  Color: (value: ValueVariantColor) => R,
  Point: (value: ValueVariantPoint) => R,
  Rect: (value: ValueVariantRect) => R,
}

interface PartialMatchValue<R> {
  Sint64?: (value: ValueVariantSint64) => R,
  Double?: (value: ValueVariantDouble) => R,
  String?: (value: ValueVariantString) => R,
  Color?: (value: ValueVariantColor) => R,
  Point?: (value: ValueVariantPoint) => R,
  Rect?: (value: ValueVariantRect) => R,
  _: (value: Value) => R,

}

type MatchValue<R> = PartialMatchValue<R> | FullMatchValue<R>;

export abstract class Value {
  static _variant: string = undefined as unknown as string;
abstract serialize(serializer: Serializer): void;

static deserialize(deserializer: Deserializer): Value {
  const index = deserializer.deserializeVariantIndex();
  switch (index) {
    case 0: return ValueVariantSint64.load(deserializer);
    case 1: return ValueVariantDouble.load(deserializer);
    case 2: return ValueVariantString.load(deserializer);
    case 3: return ValueVariantColor.load(deserializer);
    case 4: return ValueVariantPoint.load(deserializer);
    case 5: return ValueVariantRect.load(deserializer);
    default: throw new window.Error("Unknown variant index for Value: " + index);
  }
}
match<R>(handlers: MatchValue<R>): R {
  let handler = (handlers as any)[(this.constructor as any)._variant];
  return (handler || (handlers as any)['_'])(this);
}

}


export class ValueVariantSint64 extends Value {
  static _variant = "Sint64";

constructor (public value: int64) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(0);
  serializer.serializeI64(this.value);
}

static load(deserializer: Deserializer): ValueVariantSint64 {
  const value = deserializer.deserializeI64();
  return new ValueVariantSint64(value);
}

}

export class ValueVariantDouble extends Value {
  static _variant = "Double";

constructor (public value: float64) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(1);
  serializer.serializeF64(this.value);
}

static load(deserializer: Deserializer): ValueVariantDouble {
  const value = deserializer.deserializeF64();
  return new ValueVariantDouble(value);
}

}

export class ValueVariantString extends Value {
  static _variant = "String";

constructor (public value: str) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(2);
  serializer.serializeStr(this.value);
}

static load(deserializer: Deserializer): ValueVariantString {
  const value = deserializer.deserializeStr();
  return new ValueVariantString(value);
}

}

export class ValueVariantColor extends Value {
  static _variant = "Color";

constructor (public value: Color) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(3);
  this.value.serialize(serializer);
}

static load(deserializer: Deserializer): ValueVariantColor {
  const value = Color.deserialize(deserializer);
  return new ValueVariantColor(value);
}

}

export class ValueVariantPoint extends Value {
  static _variant = "Point";

constructor (public left: float64, public top: float64) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(4);
  serializer.serializeF64(this.left);
  serializer.serializeF64(this.top);
}

static load(deserializer: Deserializer): ValueVariantPoint {
  const left = deserializer.deserializeF64();
  const top = deserializer.deserializeF64();
  return new ValueVariantPoint(left,top);
}

}

export class ValueVariantRect extends Value {
  static _variant = "Rect";

constructor (public left: float64, public top: float64, public right: float64, public bottom: float64) {
  super();
}

public serialize(serializer: Serializer): void {
  serializer.serializeVariantIndex(5);
  serializer.serializeF64(this.left);
  serializer.serializeF64(this.top);
  serializer.serializeF64(this.right);
  serializer.serializeF64(this.bottom);
}

static load(deserializer: Deserializer): ValueVariantRect {
  const left = deserializer.deserializeF64();
  const top = deserializer.deserializeF64();
  const right = deserializer.deserializeF64();
  const bottom = deserializer.deserializeF64();
  return new ValueVariantRect(left,top,right,bottom);
}

}
export class VarId {

constructor (public scene: uint32, public key: str) {
}

public serialize(serializer: Serializer): void {
  serializer.serializeU32(this.scene);
  serializer.serializeStr(this.key);
}

static deserialize(deserializer: Deserializer): VarId {
  const scene = deserializer.deserializeU32();
  const key = deserializer.deserializeStr();
  return new VarId(scene,key);
}

}
export class Watch {

constructor (public condition: OpId, public handler: HandlerBlock) {
}

public serialize(serializer: Serializer): void {
  this.condition.serialize(serializer);
  this.handler.serialize(serializer);
}

static deserialize(deserializer: Deserializer): Watch {
  const condition = OpId.deserialize(deserializer);
  const handler = HandlerBlock.deserialize(deserializer);
  return new Watch(condition,handler);
}

}
export class Helpers {
  static serializeMapStrToValue(value: Map<str,Value>, serializer: Serializer): void {
    serializer.serializeLen(value.size);
    const offsets: number[] = [];
    for (const [k, v] of value.entries()) {
      offsets.push(serializer.getBufferOffset());
      serializer.serializeStr(k);
      v.serialize(serializer);
    }
    serializer.sortMapEntries(offsets);
  }

  static deserializeMapStrToValue(deserializer: Deserializer): Map<str,Value> {
    const length = deserializer.deserializeLen();
    const obj = new Map<str, Value>();
    let previousKeyStart = 0;
    let previousKeyEnd = 0;
    for (let i = 0; i < length; i++) {
        const keyStart = deserializer.getBufferOffset();
        const key = deserializer.deserializeStr();
        const keyEnd = deserializer.getBufferOffset();
        if (i > 0) {
            deserializer.checkThatKeySlicesAreIncreasing(
                [previousKeyStart, previousKeyEnd],
                [keyStart, keyEnd]);
        }
        previousKeyStart = keyStart;
        previousKeyEnd = keyEnd;
        const value = Value.deserialize(deserializer);
        obj.set(key, value);
    }
    return obj;
  }

  static serializeOptionError(value: Optional<Error>, serializer: Serializer): void {
    if (value) {
        serializer.serializeOptionTag(true);
        value.serialize(serializer);
    } else {
        serializer.serializeOptionTag(false);
    }
  }

  static deserializeOptionError(deserializer: Deserializer): Optional<Error> {
    const tag = deserializer.deserializeOptionTag();
    if (!tag) {
        return null;
    } else {
        return Error.deserialize(deserializer);
    }
  }

  static serializeTuple2EventTypeHandlerBlock(value: Tuple<[EventType, HandlerBlock]>, serializer: Serializer): void {
    value[0].serialize(serializer);
    value[1].serialize(serializer);
  }

  static deserializeTuple2EventTypeHandlerBlock(deserializer: Deserializer): Tuple<[EventType, HandlerBlock]> {
    return [
        EventType.deserialize(deserializer),
        HandlerBlock.deserialize(deserializer)
    ];
  }

  static serializeTuple2StrValue(value: Tuple<[str, Value]>, serializer: Serializer): void {
    serializer.serializeStr(value[0]);
    value[1].serialize(serializer);
  }

  static deserializeTuple2StrValue(deserializer: Deserializer): Tuple<[str, Value]> {
    return [
        deserializer.deserializeStr(),
        Value.deserialize(deserializer)
    ];
  }

  static serializeVectorA2rUpdateScene(value: Seq<A2RUpdateScene>, serializer: Serializer): void {
    serializer.serializeLen(value.length);
    value.forEach((item: A2RUpdateScene) => {
        item.serialize(serializer);
    });
  }

  static deserializeVectorA2rUpdateScene(deserializer: Deserializer): Seq<A2RUpdateScene> {
    const length = deserializer.deserializeLen();
    const list: Seq<A2RUpdateScene> = [];
    for (let i = 0; i < length; i++) {
        list.push(A2RUpdateScene.deserialize(deserializer));
    }
    return list;
  }

  static serializeVectorCmdsCommand(value: Seq<CmdsCommand>, serializer: Serializer): void {
    serializer.serializeLen(value.length);
    value.forEach((item: CmdsCommand) => {
        item.serialize(serializer);
    });
  }

  static deserializeVectorCmdsCommand(deserializer: Deserializer): Seq<CmdsCommand> {
    const length = deserializer.deserializeLen();
    const list: Seq<CmdsCommand> = [];
    for (let i = 0; i < length; i++) {
        list.push(CmdsCommand.deserialize(deserializer));
    }
    return list;
  }

  static serializeVectorExternalAppRequest(value: Seq<ExternalAppRequest>, serializer: Serializer): void {
    serializer.serializeLen(value.length);
    value.forEach((item: ExternalAppRequest) => {
        item.serialize(serializer);
    });
  }

  static deserializeVectorExternalAppRequest(deserializer: Deserializer): Seq<ExternalAppRequest> {
    const length = deserializer.deserializeLen();
    const list: Seq<ExternalAppRequest> = [];
    for (let i = 0; i < length; i++) {
        list.push(ExternalAppRequest.deserialize(deserializer));
    }
    return list;
  }

  static serializeVectorHandlerBlock(value: Seq<HandlerBlock>, serializer: Serializer): void {
    serializer.serializeLen(value.length);
    value.forEach((item: HandlerBlock) => {
        item.serialize(serializer);
    });
  }

  static deserializeVectorHandlerBlock(deserializer: Deserializer): Seq<HandlerBlock> {
    const length = deserializer.deserializeLen();
    const list: Seq<HandlerBlock> = [];
    for (let i = 0; i < length; i++) {
        list.push(HandlerBlock.deserialize(deserializer));
    }
    return list;
  }

  static serializeVectorHandlerCmd(value: Seq<HandlerCmd>, serializer: Serializer): void {
    serializer.serializeLen(value.length);
    value.forEach((item: HandlerCmd) => {
        item.serialize(serializer);
    });
  }

  static deserializeVectorHandlerCmd(deserializer: Deserializer): Seq<HandlerCmd> {
    const length = deserializer.deserializeLen();
    const list: Seq<HandlerCmd> = [];
    for (let i = 0; i < length; i++) {
        list.push(HandlerCmd.deserialize(deserializer));
    }
    return list;
  }

  static serializeVectorOpId(value: Seq<OpId>, serializer: Serializer): void {
    serializer.serializeLen(value.length);
    value.forEach((item: OpId) => {
        item.serialize(serializer);
    });
  }

  static deserializeVectorOpId(deserializer: Deserializer): Seq<OpId> {
    const length = deserializer.deserializeLen();
    const list: Seq<OpId> = [];
    for (let i = 0; i < length; i++) {
        list.push(OpId.deserialize(deserializer));
    }
    return list;
  }

  static serializeVectorOpsOperation(value: Seq<OpsOperation>, serializer: Serializer): void {
    serializer.serializeLen(value.length);
    value.forEach((item: OpsOperation) => {
        item.serialize(serializer);
    });
  }

  static deserializeVectorOpsOperation(deserializer: Deserializer): Seq<OpsOperation> {
    const length = deserializer.deserializeLen();
    const list: Seq<OpsOperation> = [];
    for (let i = 0; i < length; i++) {
        list.push(OpsOperation.deserialize(deserializer));
    }
    return list;
  }

  static serializeVectorR2aReply(value: Seq<R2AReply>, serializer: Serializer): void {
    serializer.serializeLen(value.length);
    value.forEach((item: R2AReply) => {
        item.serialize(serializer);
    });
  }

  static deserializeVectorR2aReply(deserializer: Deserializer): Seq<R2AReply> {
    const length = deserializer.deserializeLen();
    const list: Seq<R2AReply> = [];
    for (let i = 0; i < length; i++) {
        list.push(R2AReply.deserialize(deserializer));
    }
    return list;
  }

  static serializeVectorValue(value: Seq<Value>, serializer: Serializer): void {
    serializer.serializeLen(value.length);
    value.forEach((item: Value) => {
        item.serialize(serializer);
    });
  }

  static deserializeVectorValue(deserializer: Deserializer): Seq<Value> {
    const length = deserializer.deserializeLen();
    const list: Seq<Value> = [];
    for (let i = 0; i < length; i++) {
        list.push(Value.deserialize(deserializer));
    }
    return list;
  }

  static serializeVectorWatch(value: Seq<Watch>, serializer: Serializer): void {
    serializer.serializeLen(value.length);
    value.forEach((item: Watch) => {
        item.serialize(serializer);
    });
  }

  static deserializeVectorWatch(deserializer: Deserializer): Seq<Watch> {
    const length = deserializer.deserializeLen();
    const list: Seq<Watch> = [];
    for (let i = 0; i < length; i++) {
        list.push(Watch.deserialize(deserializer));
    }
    return list;
  }

  static serializeVectorTuple2EventTypeHandlerBlock(value: Seq<Tuple<[EventType, HandlerBlock]>>, serializer: Serializer): void {
    serializer.serializeLen(value.length);
    value.forEach((item: Tuple<[EventType, HandlerBlock]>) => {
        Helpers.serializeTuple2EventTypeHandlerBlock(item, serializer);
    });
  }

  static deserializeVectorTuple2EventTypeHandlerBlock(deserializer: Deserializer): Seq<Tuple<[EventType, HandlerBlock]>> {
    const length = deserializer.deserializeLen();
    const list: Seq<Tuple<[EventType, HandlerBlock]>> = [];
    for (let i = 0; i < length; i++) {
        list.push(Helpers.deserializeTuple2EventTypeHandlerBlock(deserializer));
    }
    return list;
  }

  static serializeVectorTuple2StrValue(value: Seq<Tuple<[str, Value]>>, serializer: Serializer): void {
    serializer.serializeLen(value.length);
    value.forEach((item: Tuple<[str, Value]>) => {
        Helpers.serializeTuple2StrValue(item, serializer);
    });
  }

  static deserializeVectorTuple2StrValue(deserializer: Deserializer): Seq<Tuple<[str, Value]>> {
    const length = deserializer.deserializeLen();
    const list: Seq<Tuple<[str, Value]>> = [];
    for (let i = 0; i < length; i++) {
        list.push(Helpers.deserializeTuple2StrValue(deserializer));
    }
    return list;
  }

  static serializeVectorU8(value: Seq<uint8>, serializer: Serializer): void {
    serializer.serializeLen(value.length);
    value.forEach((item: uint8) => {
        serializer.serializeU8(item);
    });
  }

  static deserializeVectorU8(deserializer: Deserializer): Seq<uint8> {
    const length = deserializer.deserializeLen();
    const list: Seq<uint8> = [];
    for (let i = 0; i < length; i++) {
        list.push(deserializer.deserializeU8());
    }
    return list;
  }

}

