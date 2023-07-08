import {uint32} from "./serde/types.ts";
import {OpId} from "./_boldui_protocol/_boldui_protocol.ts";

export * from "./_boldui_protocol/_boldui_protocol.ts";
export {BincodeSerializer} from "./bincode/bincodeSerializer.ts";
export {BincodeDeserializer} from "./bincode/bincodeDeserializer.ts";

export const R2A_MAGIC = new Uint8Array([66, 79, 76, 68, 85, 73, 0]);
export const A2R_MAGIC = new Uint8Array([66, 79, 76, 68, 85, 73, 1]);
export const R2EA_MAGIC = new Uint8Array([66, 79, 76, 68, 85, 73, 2]);
export const EA2R_MAGIC = new Uint8Array([66, 79, 76, 68, 85, 73, 3]);

export const LATEST_MAJOR_VER = 0;
export const LATEST_MINOR_VER = 1;

export const LATEST_EA_MAJOR_VER = 0;
export const LATEST_EA_MINOR_VER = 1;

export type SceneId = uint32;
export const NullOpId = new OpId(0, 0);
