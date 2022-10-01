using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class VarId: IEquatable<VarId>, ICloneable {
        public string key;
        public uint scene;

        public VarId(string _key, uint _scene) {
            if (_key == null) throw new ArgumentNullException(nameof(_key));
            key = _key;
            scene = _scene;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            serializer.serialize_str(key);
            serializer.serialize_u32(scene);
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

        public static VarId Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            VarId obj = new VarId(
            	deserializer.deserialize_str(),
            	deserializer.deserialize_u32());
            deserializer.decrease_container_depth();
            return obj;
        }

        public static VarId BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static VarId BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            VarId value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is VarId other && Equals(other);

        public static bool operator ==(VarId left, VarId right) => Equals(left, right);

        public static bool operator !=(VarId left, VarId right) => !Equals(left, right);

        public bool Equals(VarId other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!key.Equals(other.key)) return false;
            if (!scene.Equals(other.scene)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + key.GetHashCode();
                value = 31 * value + scene.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public VarId Clone() => (VarId)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
