using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class A2RExtendedHelloResponse: IEquatable<A2RExtendedHelloResponse>, ICloneable {
        public A2RExtendedHelloResponse() {
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

        public static A2RExtendedHelloResponse Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            A2RExtendedHelloResponse obj = new A2RExtendedHelloResponse(
            	);
            deserializer.decrease_container_depth();
            return obj;
        }

        public static A2RExtendedHelloResponse BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static A2RExtendedHelloResponse BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            A2RExtendedHelloResponse value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is A2RExtendedHelloResponse other && Equals(other);

        public static bool operator ==(A2RExtendedHelloResponse left, A2RExtendedHelloResponse right) => Equals(left, right);

        public static bool operator !=(A2RExtendedHelloResponse left, A2RExtendedHelloResponse right) => !Equals(left, right);

        public bool Equals(A2RExtendedHelloResponse other) {
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
        public A2RExtendedHelloResponse Clone() => (A2RExtendedHelloResponse)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
