using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class A2RUpdateScene: IEquatable<A2RUpdateScene>, ICloneable {
        public uint id;
        public OpId paint;
        public OpId backdrop;
        public OpId transform;
        public OpId clip;
        public string uri;
        public Serde.ValueArray<OpsOperation> ops;
        public Serde.ValueArray<CmdsCommand> cmds;
        public Serde.ValueDictionary<string, Value> var_decls;
        public Serde.ValueArray<Watch> watches;
        public Serde.ValueArray<(EventType, HandlerBlock)> event_handlers;

        public A2RUpdateScene(uint _id, OpId _paint, OpId _backdrop, OpId _transform, OpId _clip, string _uri, Serde.ValueArray<OpsOperation> _ops, Serde.ValueArray<CmdsCommand> _cmds, Serde.ValueDictionary<string, Value> _var_decls, Serde.ValueArray<Watch> _watches, Serde.ValueArray<(EventType, HandlerBlock)> _event_handlers) {
            id = _id;
            if (_paint == null) throw new ArgumentNullException(nameof(_paint));
            paint = _paint;
            if (_backdrop == null) throw new ArgumentNullException(nameof(_backdrop));
            backdrop = _backdrop;
            if (_transform == null) throw new ArgumentNullException(nameof(_transform));
            transform = _transform;
            if (_clip == null) throw new ArgumentNullException(nameof(_clip));
            clip = _clip;
            if (_uri == null) throw new ArgumentNullException(nameof(_uri));
            uri = _uri;
            if (_ops == null) throw new ArgumentNullException(nameof(_ops));
            ops = _ops;
            if (_cmds == null) throw new ArgumentNullException(nameof(_cmds));
            cmds = _cmds;
            if (_var_decls == null) throw new ArgumentNullException(nameof(_var_decls));
            var_decls = _var_decls;
            if (_watches == null) throw new ArgumentNullException(nameof(_watches));
            watches = _watches;
            if (_event_handlers == null) throw new ArgumentNullException(nameof(_event_handlers));
            event_handlers = _event_handlers;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            serializer.serialize_u32(id);
            paint.Serialize(serializer);
            backdrop.Serialize(serializer);
            transform.Serialize(serializer);
            clip.Serialize(serializer);
            serializer.serialize_str(uri);
            TraitHelpers.serialize_vector_OpsOperation(ops, serializer);
            TraitHelpers.serialize_vector_CmdsCommand(cmds, serializer);
            TraitHelpers.serialize_map_str_to_Value(var_decls, serializer);
            TraitHelpers.serialize_vector_Watch(watches, serializer);
            TraitHelpers.serialize_vector_tuple2_EventType_HandlerBlock(event_handlers, serializer);
            serializer.decrease_container_depth();
        }

        public int BincodeSerialize(byte[] outputBuffer) => BincodeSerialize(new ArraySegment<byte>(outputBuffer));

        public int BincodeSerialize(ArraySegment<byte> outputBuffer) {
            Serde.ISerializer serializer = new Bincode.BincodeSerializer(outputBuffer);
            Serialize(serializer);
            return serializer.get_buffer_offset();
        }

        public byte[] BincodeSerialize()  {
            Serde.ISerializer serializer = new Bincode.BincodeSerializer();
            Serialize(serializer);
            return serializer.get_bytes();
        }

        public static A2RUpdateScene Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            A2RUpdateScene obj = new A2RUpdateScene(
            	deserializer.deserialize_u32(),
            	OpId.Deserialize(deserializer),
            	OpId.Deserialize(deserializer),
            	OpId.Deserialize(deserializer),
            	OpId.Deserialize(deserializer),
            	deserializer.deserialize_str(),
            	TraitHelpers.deserialize_vector_OpsOperation(deserializer),
            	TraitHelpers.deserialize_vector_CmdsCommand(deserializer),
            	TraitHelpers.deserialize_map_str_to_Value(deserializer),
            	TraitHelpers.deserialize_vector_Watch(deserializer),
            	TraitHelpers.deserialize_vector_tuple2_EventType_HandlerBlock(deserializer));
            deserializer.decrease_container_depth();
            return obj;
        }

        public static A2RUpdateScene BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static A2RUpdateScene BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            A2RUpdateScene value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is A2RUpdateScene other && Equals(other);

        public static bool operator ==(A2RUpdateScene left, A2RUpdateScene right) => Equals(left, right);

        public static bool operator !=(A2RUpdateScene left, A2RUpdateScene right) => !Equals(left, right);

        public bool Equals(A2RUpdateScene other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!id.Equals(other.id)) return false;
            if (!paint.Equals(other.paint)) return false;
            if (!backdrop.Equals(other.backdrop)) return false;
            if (!transform.Equals(other.transform)) return false;
            if (!clip.Equals(other.clip)) return false;
            if (!uri.Equals(other.uri)) return false;
            if (!ops.Equals(other.ops)) return false;
            if (!cmds.Equals(other.cmds)) return false;
            if (!var_decls.Equals(other.var_decls)) return false;
            if (!watches.Equals(other.watches)) return false;
            if (!event_handlers.Equals(other.event_handlers)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + id.GetHashCode();
                value = 31 * value + paint.GetHashCode();
                value = 31 * value + backdrop.GetHashCode();
                value = 31 * value + transform.GetHashCode();
                value = 31 * value + clip.GetHashCode();
                value = 31 * value + uri.GetHashCode();
                value = 31 * value + ops.GetHashCode();
                value = 31 * value + cmds.GetHashCode();
                value = 31 * value + var_decls.GetHashCode();
                value = 31 * value + watches.GetHashCode();
                value = 31 * value + event_handlers.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public A2RUpdateScene Clone() => (A2RUpdateScene)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
