using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class R2AOpen: IEquatable<R2AOpen>, ICloneable {
        public string path;

        public R2AOpen(string _path) {
            if (_path == null) throw new ArgumentNullException(nameof(_path));
            path = _path;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            serializer.serialize_str(path);
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

        public static R2AOpen Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            R2AOpen obj = new R2AOpen(
            	deserializer.deserialize_str());
            deserializer.decrease_container_depth();
            return obj;
        }

        public static R2AOpen BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static R2AOpen BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            R2AOpen value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is R2AOpen other && Equals(other);

        public static bool operator ==(R2AOpen left, R2AOpen right) => Equals(left, right);

        public static bool operator !=(R2AOpen left, R2AOpen right) => !Equals(left, right);

        public bool Equals(R2AOpen other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!path.Equals(other.path)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + path.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public R2AOpen Clone() => (R2AOpen)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
