using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class A2RUpdate: IEquatable<A2RUpdate>, ICloneable {
        public Serde.ValueArray<A2RUpdateScene> updated_scenes;
        public Serde.ValueArray<HandlerBlock> run_blocks;
        public Serde.ValueArray<ExternalAppRequest> external_app_requests;

        public A2RUpdate(Serde.ValueArray<A2RUpdateScene> _updated_scenes, Serde.ValueArray<HandlerBlock> _run_blocks, Serde.ValueArray<ExternalAppRequest> _external_app_requests) {
            if (_updated_scenes == null) throw new ArgumentNullException(nameof(_updated_scenes));
            updated_scenes = _updated_scenes;
            if (_run_blocks == null) throw new ArgumentNullException(nameof(_run_blocks));
            run_blocks = _run_blocks;
            if (_external_app_requests == null) throw new ArgumentNullException(nameof(_external_app_requests));
            external_app_requests = _external_app_requests;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            TraitHelpers.serialize_vector_A2RUpdateScene(updated_scenes, serializer);
            TraitHelpers.serialize_vector_HandlerBlock(run_blocks, serializer);
            TraitHelpers.serialize_vector_ExternalAppRequest(external_app_requests, serializer);
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

        public static A2RUpdate Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            A2RUpdate obj = new A2RUpdate(
            	TraitHelpers.deserialize_vector_A2RUpdateScene(deserializer),
            	TraitHelpers.deserialize_vector_HandlerBlock(deserializer),
            	TraitHelpers.deserialize_vector_ExternalAppRequest(deserializer));
            deserializer.decrease_container_depth();
            return obj;
        }

        public static A2RUpdate BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static A2RUpdate BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            A2RUpdate value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is A2RUpdate other && Equals(other);

        public static bool operator ==(A2RUpdate left, A2RUpdate right) => Equals(left, right);

        public static bool operator !=(A2RUpdate left, A2RUpdate right) => !Equals(left, right);

        public bool Equals(A2RUpdate other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!updated_scenes.Equals(other.updated_scenes)) return false;
            if (!run_blocks.Equals(other.run_blocks)) return false;
            if (!external_app_requests.Equals(other.external_app_requests)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + updated_scenes.GetHashCode();
                value = 31 * value + run_blocks.GetHashCode();
                value = 31 * value + external_app_requests.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public A2RUpdate Clone() => (A2RUpdate)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
