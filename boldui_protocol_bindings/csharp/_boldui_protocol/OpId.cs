using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class OpId: IEquatable<OpId>, ICloneable {
        public uint scene_id;
        public uint idx;

        public OpId(uint _scene_id, uint _idx) {
            scene_id = _scene_id;
            idx = _idx;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            serializer.serialize_u32(scene_id);
            serializer.serialize_u32(idx);
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

        public static OpId Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            OpId obj = new OpId(
            	deserializer.deserialize_u32(),
            	deserializer.deserialize_u32());
            deserializer.decrease_container_depth();
            return obj;
        }

        public static OpId BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static OpId BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            OpId value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is OpId other && Equals(other);

        public static bool operator ==(OpId left, OpId right) => Equals(left, right);

        public static bool operator !=(OpId left, OpId right) => !Equals(left, right);

        public bool Equals(OpId other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!scene_id.Equals(other.scene_id)) return false;
            if (!idx.Equals(other.idx)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + scene_id.GetHashCode();
                value = 31 * value + idx.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public OpId Clone() => (OpId)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
