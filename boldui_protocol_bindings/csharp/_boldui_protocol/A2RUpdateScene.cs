using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class A2RUpdateScene: IEquatable<A2RUpdateScene>, ICloneable {
        public uint id;
        public Serde.ValueDictionary<uint, OpId> attrs;
        public Serde.ValueArray<OpsOperation> ops;
        public Serde.ValueArray<CmdsCommand> cmds;
        public Serde.ValueArray<Watch> watches;
        public Serde.ValueArray<EventHandler> event_handlers;

        public A2RUpdateScene(uint _id, Serde.ValueDictionary<uint, OpId> _attrs, Serde.ValueArray<OpsOperation> _ops, Serde.ValueArray<CmdsCommand> _cmds, Serde.ValueArray<Watch> _watches, Serde.ValueArray<EventHandler> _event_handlers) {
            id = _id;
            if (_attrs == null) throw new ArgumentNullException(nameof(_attrs));
            attrs = _attrs;
            if (_ops == null) throw new ArgumentNullException(nameof(_ops));
            ops = _ops;
            if (_cmds == null) throw new ArgumentNullException(nameof(_cmds));
            cmds = _cmds;
            if (_watches == null) throw new ArgumentNullException(nameof(_watches));
            watches = _watches;
            if (_event_handlers == null) throw new ArgumentNullException(nameof(_event_handlers));
            event_handlers = _event_handlers;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            serializer.serialize_u32(id);
            TraitHelpers.serialize_map_u32_to_OpId(attrs, serializer);
            TraitHelpers.serialize_vector_OpsOperation(ops, serializer);
            TraitHelpers.serialize_vector_CmdsCommand(cmds, serializer);
            TraitHelpers.serialize_vector_Watch(watches, serializer);
            TraitHelpers.serialize_vector_EventHandler(event_handlers, serializer);
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
            	TraitHelpers.deserialize_map_u32_to_OpId(deserializer),
            	TraitHelpers.deserialize_vector_OpsOperation(deserializer),
            	TraitHelpers.deserialize_vector_CmdsCommand(deserializer),
            	TraitHelpers.deserialize_vector_Watch(deserializer),
            	TraitHelpers.deserialize_vector_EventHandler(deserializer));
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
            if (!attrs.Equals(other.attrs)) return false;
            if (!ops.Equals(other.ops)) return false;
            if (!cmds.Equals(other.cmds)) return false;
            if (!watches.Equals(other.watches)) return false;
            if (!event_handlers.Equals(other.event_handlers)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + id.GetHashCode();
                value = 31 * value + attrs.GetHashCode();
                value = 31 * value + ops.GetHashCode();
                value = 31 * value + cmds.GetHashCode();
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
