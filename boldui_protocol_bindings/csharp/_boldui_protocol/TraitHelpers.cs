using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {
    static class TraitHelpers {
        public static void serialize_map_str_to_Value(Serde.ValueDictionary<string, Value> value, Serde.ISerializer serializer) {
            serializer.serialize_len(value.Count);
            int[] offsets = new int[value.Count];
            int count = 0;
            foreach (KeyValuePair<string, Value> entry in value) {
                offsets[count++] = serializer.get_buffer_offset();
                serializer.serialize_str(entry.Key);
                entry.Value.Serialize(serializer);
            }
            serializer.sort_map_entries(offsets);
        }

        public static Serde.ValueDictionary<string, Value> deserialize_map_str_to_Value(Serde.IDeserializer deserializer) {
            long length = deserializer.deserialize_len();
            var obj = new Dictionary<string, Value>();
            int previous_key_start = 0;
            int previous_key_end = 0;
            for (long i = 0; i < length; i++) {
                int key_start = deserializer.get_buffer_offset();
                var key = deserializer.deserialize_str();
                int key_end = deserializer.get_buffer_offset();
                if (i > 0) {
                    deserializer.check_that_key_slices_are_increasing(
                        new Serde.Range(previous_key_start, previous_key_end),
                        new Serde.Range(key_start, key_end));
                }
                previous_key_start = key_start;
                previous_key_end = key_end;
                var value = Value.Deserialize(deserializer);
                obj[key] = value;
            }
            return new Serde.ValueDictionary<string, Value>(obj);
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

    }


} // end of namespace _boldui_protocol
