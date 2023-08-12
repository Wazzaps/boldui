using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class ResourceDealloc: IEquatable<ResourceDealloc>, ICloneable {
        public uint id;
        public ulong offset;
        public ulong length;

        public ResourceDealloc(uint _id, ulong _offset, ulong _length) {
            id = _id;
            offset = _offset;
            length = _length;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            serializer.serialize_u32(id);
            serializer.serialize_u64(offset);
            serializer.serialize_u64(length);
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

        public static ResourceDealloc Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            ResourceDealloc obj = new ResourceDealloc(
            	deserializer.deserialize_u32(),
            	deserializer.deserialize_u64(),
            	deserializer.deserialize_u64());
            deserializer.decrease_container_depth();
            return obj;
        }

        public static ResourceDealloc BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static ResourceDealloc BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            ResourceDealloc value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is ResourceDealloc other && Equals(other);

        public static bool operator ==(ResourceDealloc left, ResourceDealloc right) => Equals(left, right);

        public static bool operator !=(ResourceDealloc left, ResourceDealloc right) => !Equals(left, right);

        public bool Equals(ResourceDealloc other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!id.Equals(other.id)) return false;
            if (!offset.Equals(other.offset)) return false;
            if (!length.Equals(other.length)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + id.GetHashCode();
                value = 31 * value + offset.GetHashCode();
                value = 31 * value + length.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public ResourceDealloc Clone() => (ResourceDealloc)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
