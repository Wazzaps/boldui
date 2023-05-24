using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class EA2RHelloResponse: IEquatable<EA2RHelloResponse>, ICloneable {
        public ushort protocol_major_version;
        public ushort protocol_minor_version;
        public uint extra_len;
        public Serde.Option<Error> error;

        public EA2RHelloResponse(ushort _protocol_major_version, ushort _protocol_minor_version, uint _extra_len, Serde.Option<Error> _error) {
            protocol_major_version = _protocol_major_version;
            protocol_minor_version = _protocol_minor_version;
            extra_len = _extra_len;
            error = _error;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            serializer.serialize_u16(protocol_major_version);
            serializer.serialize_u16(protocol_minor_version);
            serializer.serialize_u32(extra_len);
            TraitHelpers.serialize_option_Error(error, serializer);
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

        public static EA2RHelloResponse Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            EA2RHelloResponse obj = new EA2RHelloResponse(
            	deserializer.deserialize_u16(),
            	deserializer.deserialize_u16(),
            	deserializer.deserialize_u32(),
            	TraitHelpers.deserialize_option_Error(deserializer));
            deserializer.decrease_container_depth();
            return obj;
        }

        public static EA2RHelloResponse BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static EA2RHelloResponse BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            EA2RHelloResponse value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is EA2RHelloResponse other && Equals(other);

        public static bool operator ==(EA2RHelloResponse left, EA2RHelloResponse right) => Equals(left, right);

        public static bool operator !=(EA2RHelloResponse left, EA2RHelloResponse right) => !Equals(left, right);

        public bool Equals(EA2RHelloResponse other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!protocol_major_version.Equals(other.protocol_major_version)) return false;
            if (!protocol_minor_version.Equals(other.protocol_minor_version)) return false;
            if (!extra_len.Equals(other.extra_len)) return false;
            if (!error.Equals(other.error)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + protocol_major_version.GetHashCode();
                value = 31 * value + protocol_minor_version.GetHashCode();
                value = 31 * value + extra_len.GetHashCode();
                value = 31 * value + error.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public EA2RHelloResponse Clone() => (EA2RHelloResponse)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
