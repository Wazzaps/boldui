using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class R2AReply: IEquatable<R2AReply>, ICloneable {
        public string path;
        public Serde.ValueArray<Value> params;

        public R2AReply(string _path, Serde.ValueArray<Value> _params) {
            if (_path == null) throw new ArgumentNullException(nameof(_path));
            path = _path;
            if (_params == null) throw new ArgumentNullException(nameof(_params));
            params = _params;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            serializer.serialize_str(path);
            TraitHelpers.serialize_vector_Value(params, serializer);
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

        public static R2AReply Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            R2AReply obj = new R2AReply(
            	deserializer.deserialize_str(),
            	TraitHelpers.deserialize_vector_Value(deserializer));
            deserializer.decrease_container_depth();
            return obj;
        }

        public static R2AReply BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static R2AReply BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            R2AReply value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is R2AReply other && Equals(other);

        public static bool operator ==(R2AReply left, R2AReply right) => Equals(left, right);

        public static bool operator !=(R2AReply left, R2AReply right) => !Equals(left, right);

        public bool Equals(R2AReply other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!path.Equals(other.path)) return false;
            if (!params.Equals(other.params)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + path.GetHashCode();
                value = 31 * value + params.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public R2AReply Clone() => (R2AReply)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
