using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class Color: IEquatable<Color>, ICloneable {
        public ushort r;
        public ushort g;
        public ushort b;
        public ushort a;

        public Color(ushort _r, ushort _g, ushort _b, ushort _a) {
            r = _r;
            g = _g;
            b = _b;
            a = _a;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            serializer.serialize_u16(r);
            serializer.serialize_u16(g);
            serializer.serialize_u16(b);
            serializer.serialize_u16(a);
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

        public static Color Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            Color obj = new Color(
            	deserializer.deserialize_u16(),
            	deserializer.deserialize_u16(),
            	deserializer.deserialize_u16(),
            	deserializer.deserialize_u16());
            deserializer.decrease_container_depth();
            return obj;
        }

        public static Color BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static Color BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            Color value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is Color other && Equals(other);

        public static bool operator ==(Color left, Color right) => Equals(left, right);

        public static bool operator !=(Color left, Color right) => !Equals(left, right);

        public bool Equals(Color other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!r.Equals(other.r)) return false;
            if (!g.Equals(other.g)) return false;
            if (!b.Equals(other.b)) return false;
            if (!a.Equals(other.a)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + r.GetHashCode();
                value = 31 * value + g.GetHashCode();
                value = 31 * value + b.GetHashCode();
                value = 31 * value + a.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public Color Clone() => (Color)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
