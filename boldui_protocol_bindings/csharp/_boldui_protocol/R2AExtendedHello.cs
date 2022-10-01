using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class R2AExtendedHello: IEquatable<R2AExtendedHello>, ICloneable {
        public R2AExtendedHello() {
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
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

        public static R2AExtendedHello Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            R2AExtendedHello obj = new R2AExtendedHello(
            	);
            deserializer.decrease_container_depth();
            return obj;
        }

        public static R2AExtendedHello BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static R2AExtendedHello BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            R2AExtendedHello value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is R2AExtendedHello other && Equals(other);

        public static bool operator ==(R2AExtendedHello left, R2AExtendedHello right) => Equals(left, right);

        public static bool operator !=(R2AExtendedHello left, R2AExtendedHello right) => !Equals(left, right);

        public bool Equals(R2AExtendedHello other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public R2AExtendedHello Clone() => (R2AExtendedHello)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
