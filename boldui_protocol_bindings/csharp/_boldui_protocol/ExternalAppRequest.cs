using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class ExternalAppRequest: IEquatable<ExternalAppRequest>, ICloneable {
        public uint scene_id;
        public string uri;

        public ExternalAppRequest(uint _scene_id, string _uri) {
            scene_id = _scene_id;
            if (_uri == null) throw new ArgumentNullException(nameof(_uri));
            uri = _uri;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            serializer.serialize_u32(scene_id);
            serializer.serialize_str(uri);
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

        public static ExternalAppRequest Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            ExternalAppRequest obj = new ExternalAppRequest(
            	deserializer.deserialize_u32(),
            	deserializer.deserialize_str());
            deserializer.decrease_container_depth();
            return obj;
        }

        public static ExternalAppRequest BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static ExternalAppRequest BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            ExternalAppRequest value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is ExternalAppRequest other && Equals(other);

        public static bool operator ==(ExternalAppRequest left, ExternalAppRequest right) => Equals(left, right);

        public static bool operator !=(ExternalAppRequest left, ExternalAppRequest right) => !Equals(left, right);

        public bool Equals(ExternalAppRequest other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!scene_id.Equals(other.scene_id)) return false;
            if (!uri.Equals(other.uri)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + scene_id.GetHashCode();
                value = 31 * value + uri.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public ExternalAppRequest Clone() => (ExternalAppRequest)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
