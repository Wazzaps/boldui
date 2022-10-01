using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class R2AError: IEquatable<R2AError>, ICloneable {
        public ulong code;
        public string text;

        public R2AError(ulong _code, string _text) {
            code = _code;
            if (_text == null) throw new ArgumentNullException(nameof(_text));
            text = _text;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            serializer.serialize_u64(code);
            serializer.serialize_str(text);
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

        public static R2AError Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            R2AError obj = new R2AError(
            	deserializer.deserialize_u64(),
            	deserializer.deserialize_str());
            deserializer.decrease_container_depth();
            return obj;
        }

        public static R2AError BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static R2AError BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            R2AError value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is R2AError other && Equals(other);

        public static bool operator ==(R2AError left, R2AError right) => Equals(left, right);

        public static bool operator !=(R2AError left, R2AError right) => !Equals(left, right);

        public bool Equals(R2AError other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!code.Equals(other.code)) return false;
            if (!text.Equals(other.text)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + code.GetHashCode();
                value = 31 * value + text.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public R2AError Clone() => (R2AError)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
