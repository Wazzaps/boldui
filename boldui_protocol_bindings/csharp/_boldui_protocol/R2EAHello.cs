using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class R2EAHello: IEquatable<R2EAHello>, ICloneable {
        public ushort min_protocol_major_version;
        public ushort min_protocol_minor_version;
        public ushort max_protocol_major_version;
        public uint extra_len;

        public R2EAHello(ushort _min_protocol_major_version, ushort _min_protocol_minor_version, ushort _max_protocol_major_version, uint _extra_len) {
            min_protocol_major_version = _min_protocol_major_version;
            min_protocol_minor_version = _min_protocol_minor_version;
            max_protocol_major_version = _max_protocol_major_version;
            extra_len = _extra_len;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            serializer.serialize_u16(min_protocol_major_version);
            serializer.serialize_u16(min_protocol_minor_version);
            serializer.serialize_u16(max_protocol_major_version);
            serializer.serialize_u32(extra_len);
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

        public static R2EAHello Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            R2EAHello obj = new R2EAHello(
            	deserializer.deserialize_u16(),
            	deserializer.deserialize_u16(),
            	deserializer.deserialize_u16(),
            	deserializer.deserialize_u32());
            deserializer.decrease_container_depth();
            return obj;
        }

        public static R2EAHello BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static R2EAHello BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            R2EAHello value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is R2EAHello other && Equals(other);

        public static bool operator ==(R2EAHello left, R2EAHello right) => Equals(left, right);

        public static bool operator !=(R2EAHello left, R2EAHello right) => !Equals(left, right);

        public bool Equals(R2EAHello other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!min_protocol_major_version.Equals(other.min_protocol_major_version)) return false;
            if (!min_protocol_minor_version.Equals(other.min_protocol_minor_version)) return false;
            if (!max_protocol_major_version.Equals(other.max_protocol_major_version)) return false;
            if (!extra_len.Equals(other.extra_len)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + min_protocol_major_version.GetHashCode();
                value = 31 * value + min_protocol_minor_version.GetHashCode();
                value = 31 * value + max_protocol_major_version.GetHashCode();
                value = 31 * value + extra_len.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public R2EAHello Clone() => (R2EAHello)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
