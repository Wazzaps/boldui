using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class R2EAUpdate: IEquatable<R2EAUpdate>, ICloneable {
        public Serde.ValueArray<(string, Value)> changed_vars;

        public R2EAUpdate(Serde.ValueArray<(string, Value)> _changed_vars) {
            if (_changed_vars == null) throw new ArgumentNullException(nameof(_changed_vars));
            changed_vars = _changed_vars;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            TraitHelpers.serialize_vector_tuple2_str_Value(changed_vars, serializer);
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

        public static R2EAUpdate Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            R2EAUpdate obj = new R2EAUpdate(
            	TraitHelpers.deserialize_vector_tuple2_str_Value(deserializer));
            deserializer.decrease_container_depth();
            return obj;
        }

        public static R2EAUpdate BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static R2EAUpdate BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            R2EAUpdate value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is R2EAUpdate other && Equals(other);

        public static bool operator ==(R2EAUpdate left, R2EAUpdate right) => Equals(left, right);

        public static bool operator !=(R2EAUpdate left, R2EAUpdate right) => !Equals(left, right);

        public bool Equals(R2EAUpdate other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!changed_vars.Equals(other.changed_vars)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + changed_vars.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public R2EAUpdate Clone() => (R2EAUpdate)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
