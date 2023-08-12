using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {
    static class TraitHelpers {
        public static void serialize_map_u32_to_OpId(Serde.ValueDictionary<uint, OpId> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            int[] offsets = new int[value.Count];
            int count = 0;
            foreach (KeyValuePair<uint, OpId> entry in value) {
                offsets[count++] = serializer.get_buffer_offset();
                serializer.serialize_u32(entry.Key);
                entry.Value.Serialize(serializer);
            }
            serializer.sort_map_entries(offsets);
        }

        public static Serde.ValueDictionary<uint, OpId> deserialize_map_u32_to_OpId(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            var obj = new Dictionary<uint, OpId>();
            int previous_key_start = 0;
            int previous_key_end = 0;
            for (long i = 0; i < length; i++) {
                int key_start = deserializer.get_buffer_offset();
                var key = deserializer.deserialize_u32();
                int key_end = deserializer.get_buffer_offset();
                if (i > 0) {
                    deserializer.check_that_key_slices_are_increasing(
                        new Serde.Range(previous_key_start, previous_key_end),
                        new Serde.Range(key_start, key_end));
                }
                previous_key_start = key_start;
                previous_key_end = key_end;
                var value = OpId.Deserialize(deserializer);
                obj[key] = value;
            }
            return new Serde.ValueDictionary<uint, OpId>(obj);
        }

        public static void serialize_option_Error(Serde.Option<Error> value, Serde.ISerializer serializer) {
            if (value.IsSome(out var val)) {
                serializer.serialize_option_tag(true);
                val.Serialize(serializer);
            } else {
                serializer.serialize_option_tag(false);
            }
        }

        public static Serde.Option<Error> deserialize_option_Error(Serde.IDeserializer deserializer) {
            bool tag = deserializer.deserialize_option_tag();
            if (!tag) {
                return Serde.Option<Error>.None;
            } else {
                return Serde.Option<Error>.Some(Error.Deserialize(deserializer));
            }
        }

        public static void serialize_tuple2_str_Value((string, Value) value, Serde.ISerializer serializer) {
            serializer.serialize_str(value.Item1);
            value.Item2.Serialize(serializer);
        }

        public static (string, Value) deserialize_tuple2_str_Value(Serde.IDeserializer deserializer) {
            return (
                deserializer.deserialize_str(),
                Value.Deserialize(deserializer)
            );
        }

        public static void serialize_vector_A2RUpdateScene(Serde.ValueArray<A2RUpdateScene> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            foreach (var item in value) {
                item.Serialize(serializer);
            }
        }

        public static Serde.ValueArray<A2RUpdateScene> deserialize_vector_A2RUpdateScene(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            A2RUpdateScene[] obj = new A2RUpdateScene[length];
            for (int i = 0; i < length; i++) {
                obj[i] = A2RUpdateScene.Deserialize(deserializer);
            }
            return new Serde.ValueArray<A2RUpdateScene>(obj);
        }

        public static void serialize_vector_CmdsCommand(Serde.ValueArray<CmdsCommand> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            foreach (var item in value) {
                item.Serialize(serializer);
            }
        }

        public static Serde.ValueArray<CmdsCommand> deserialize_vector_CmdsCommand(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            CmdsCommand[] obj = new CmdsCommand[length];
            for (int i = 0; i < length; i++) {
                obj[i] = CmdsCommand.Deserialize(deserializer);
            }
            return new Serde.ValueArray<CmdsCommand>(obj);
        }

        public static void serialize_vector_EventHandler(Serde.ValueArray<EventHandler> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            foreach (var item in value) {
                item.Serialize(serializer);
            }
        }

        public static Serde.ValueArray<EventHandler> deserialize_vector_EventHandler(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            EventHandler[] obj = new EventHandler[length];
            for (int i = 0; i < length; i++) {
                obj[i] = EventHandler.Deserialize(deserializer);
            }
            return new Serde.ValueArray<EventHandler>(obj);
        }

        public static void serialize_vector_ExternalAppRequest(Serde.ValueArray<ExternalAppRequest> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            foreach (var item in value) {
                item.Serialize(serializer);
            }
        }

        public static Serde.ValueArray<ExternalAppRequest> deserialize_vector_ExternalAppRequest(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            ExternalAppRequest[] obj = new ExternalAppRequest[length];
            for (int i = 0; i < length; i++) {
                obj[i] = ExternalAppRequest.Deserialize(deserializer);
            }
            return new Serde.ValueArray<ExternalAppRequest>(obj);
        }

        public static void serialize_vector_HandlerBlock(Serde.ValueArray<HandlerBlock> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            foreach (var item in value) {
                item.Serialize(serializer);
            }
        }

        public static Serde.ValueArray<HandlerBlock> deserialize_vector_HandlerBlock(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            HandlerBlock[] obj = new HandlerBlock[length];
            for (int i = 0; i < length; i++) {
                obj[i] = HandlerBlock.Deserialize(deserializer);
            }
            return new Serde.ValueArray<HandlerBlock>(obj);
        }

        public static void serialize_vector_HandlerCmd(Serde.ValueArray<HandlerCmd> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            foreach (var item in value) {
                item.Serialize(serializer);
            }
        }

        public static Serde.ValueArray<HandlerCmd> deserialize_vector_HandlerCmd(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            HandlerCmd[] obj = new HandlerCmd[length];
            for (int i = 0; i < length; i++) {
                obj[i] = HandlerCmd.Deserialize(deserializer);
            }
            return new Serde.ValueArray<HandlerCmd>(obj);
        }

        public static void serialize_vector_OpId(Serde.ValueArray<OpId> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            foreach (var item in value) {
                item.Serialize(serializer);
            }
        }

        public static Serde.ValueArray<OpId> deserialize_vector_OpId(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            OpId[] obj = new OpId[length];
            for (int i = 0; i < length; i++) {
                obj[i] = OpId.Deserialize(deserializer);
            }
            return new Serde.ValueArray<OpId>(obj);
        }

        public static void serialize_vector_OpsOperation(Serde.ValueArray<OpsOperation> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            foreach (var item in value) {
                item.Serialize(serializer);
            }
        }

        public static Serde.ValueArray<OpsOperation> deserialize_vector_OpsOperation(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            OpsOperation[] obj = new OpsOperation[length];
            for (int i = 0; i < length; i++) {
                obj[i] = OpsOperation.Deserialize(deserializer);
            }
            return new Serde.ValueArray<OpsOperation>(obj);
        }

        public static void serialize_vector_R2AReply(Serde.ValueArray<R2AReply> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            foreach (var item in value) {
                item.Serialize(serializer);
            }
        }

        public static Serde.ValueArray<R2AReply> deserialize_vector_R2AReply(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            R2AReply[] obj = new R2AReply[length];
            for (int i = 0; i < length; i++) {
                obj[i] = R2AReply.Deserialize(deserializer);
            }
            return new Serde.ValueArray<R2AReply>(obj);
        }

        public static void serialize_vector_ResourceChunk(Serde.ValueArray<ResourceChunk> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            foreach (var item in value) {
                item.Serialize(serializer);
            }
        }

        public static Serde.ValueArray<ResourceChunk> deserialize_vector_ResourceChunk(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            ResourceChunk[] obj = new ResourceChunk[length];
            for (int i = 0; i < length; i++) {
                obj[i] = ResourceChunk.Deserialize(deserializer);
            }
            return new Serde.ValueArray<ResourceChunk>(obj);
        }

        public static void serialize_vector_ResourceDealloc(Serde.ValueArray<ResourceDealloc> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            foreach (var item in value) {
                item.Serialize(serializer);
            }
        }

        public static Serde.ValueArray<ResourceDealloc> deserialize_vector_ResourceDealloc(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            ResourceDealloc[] obj = new ResourceDealloc[length];
            for (int i = 0; i < length; i++) {
                obj[i] = ResourceDealloc.Deserialize(deserializer);
            }
            return new Serde.ValueArray<ResourceDealloc>(obj);
        }

        public static void serialize_vector_Value(Serde.ValueArray<Value> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            foreach (var item in value) {
                item.Serialize(serializer);
            }
        }

        public static Serde.ValueArray<Value> deserialize_vector_Value(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            Value[] obj = new Value[length];
            for (int i = 0; i < length; i++) {
                obj[i] = Value.Deserialize(deserializer);
            }
            return new Serde.ValueArray<Value>(obj);
        }

        public static void serialize_vector_Watch(Serde.ValueArray<Watch> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            foreach (var item in value) {
                item.Serialize(serializer);
            }
        }

        public static Serde.ValueArray<Watch> deserialize_vector_Watch(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            Watch[] obj = new Watch[length];
            for (int i = 0; i < length; i++) {
                obj[i] = Watch.Deserialize(deserializer);
            }
            return new Serde.ValueArray<Watch>(obj);
        }

        public static void serialize_vector_tuple2_str_Value(Serde.ValueArray<(string, Value)> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            foreach (var item in value) {
                TraitHelpers.serialize_tuple2_str_Value(item, serializer);
            }
        }

        public static Serde.ValueArray<(string, Value)> deserialize_vector_tuple2_str_Value(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            (string, Value)[] obj = new (string, Value)[length];
            for (int i = 0; i < length; i++) {
                obj[i] = TraitHelpers.deserialize_tuple2_str_Value(deserializer);
            }
            return new Serde.ValueArray<(string, Value)>(obj);
        }

        public static void serialize_vector_u8(Serde.ValueArray<byte> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            foreach (var item in value) {
                serializer.serialize_u8(item);
            }
        }

        public static Serde.ValueArray<byte> deserialize_vector_u8(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            byte[] obj = new byte[length];
            for (int i = 0; i < length; i++) {
                obj[i] = deserializer.deserialize_u8();
            }
            return new Serde.ValueArray<byte>(obj);
        }

    }


} // end of namespace _boldui_protocol
