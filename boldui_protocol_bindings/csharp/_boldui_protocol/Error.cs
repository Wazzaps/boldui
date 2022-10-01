using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class Error: IEquatable<Error>, ICloneable {
        public ulong code;
        public string text;

        public Error(ulong _code, string _text) {
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

        public static Error Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            Error obj = new Error(
            	deserializer.deserialize_u64(),
            	deserializer.deserialize_str());
            deserializer.decrease_container_depth();
            return obj;
        }

        public static Error BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static Error BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            Error value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is Error other && Equals(other);

        public static bool operator ==(Error left, Error right) => Equals(left, right);

        public static bool operator !=(Error left, Error right) => !Equals(left, right);

        public bool Equals(Error other) {
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
        public Error Clone() => (Error)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
