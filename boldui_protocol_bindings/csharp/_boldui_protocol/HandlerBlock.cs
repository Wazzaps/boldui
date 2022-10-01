using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class HandlerBlock: IEquatable<HandlerBlock>, ICloneable {
        public Serde.ValueArray<OpsOperation> ops;
        public Serde.ValueArray<HandlerCmd> cmds;

        public HandlerBlock(Serde.ValueArray<OpsOperation> _ops, Serde.ValueArray<HandlerCmd> _cmds) {
            if (_ops == null) throw new ArgumentNullException(nameof(_ops));
            ops = _ops;
            if (_cmds == null) throw new ArgumentNullException(nameof(_cmds));
            cmds = _cmds;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            TraitHelpers.serialize_vector_OpsOperation(ops, serializer);
            TraitHelpers.serialize_vector_HandlerCmd(cmds, serializer);
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

        public static HandlerBlock Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            HandlerBlock obj = new HandlerBlock(
            	TraitHelpers.deserialize_vector_OpsOperation(deserializer),
            	TraitHelpers.deserialize_vector_HandlerCmd(deserializer));
            deserializer.decrease_container_depth();
            return obj;
        }

        public static HandlerBlock BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static HandlerBlock BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            HandlerBlock value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is HandlerBlock other && Equals(other);

        public static bool operator ==(HandlerBlock left, HandlerBlock right) => Equals(left, right);

        public static bool operator !=(HandlerBlock left, HandlerBlock right) => !Equals(left, right);

        public bool Equals(HandlerBlock other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!ops.Equals(other.ops)) return false;
            if (!cmds.Equals(other.cmds)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + ops.GetHashCode();
                value = 31 * value + cmds.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public HandlerBlock Clone() => (HandlerBlock)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
