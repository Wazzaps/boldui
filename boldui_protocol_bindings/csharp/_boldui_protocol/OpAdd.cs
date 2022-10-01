using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class OpAdd: IEquatable<OpAdd>, ICloneable {
        public OpId a;
        public OpId b;

        public OpAdd(OpId _a, OpId _b) {
            if (_a == null) throw new ArgumentNullException(nameof(_a));
            a = _a;
            if (_b == null) throw new ArgumentNullException(nameof(_b));
            b = _b;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            a.Serialize(serializer);
            b.Serialize(serializer);
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

        public static OpAdd Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            OpAdd obj = new OpAdd(
            	OpId.Deserialize(deserializer),
            	OpId.Deserialize(deserializer));
            deserializer.decrease_container_depth();
            return obj;
        }

        public static OpAdd BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static OpAdd BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            OpAdd value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is OpAdd other && Equals(other);

        public static bool operator ==(OpAdd left, OpAdd right) => Equals(left, right);

        public static bool operator !=(OpAdd left, OpAdd right) => !Equals(left, right);

        public bool Equals(OpAdd other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!a.Equals(other.a)) return false;
            if (!b.Equals(other.b)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + a.GetHashCode();
                value = 31 * value + b.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public OpAdd Clone() => (OpAdd)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
