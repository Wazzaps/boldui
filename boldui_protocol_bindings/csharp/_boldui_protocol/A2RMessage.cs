using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public abstract class A2RMessage: IEquatable<A2RMessage>, ICloneable {

        public abstract void Serialize(Serde.ISerializer serializer);

        public static A2RMessage Deserialize(Serde.IDeserializer deserializer) {
            int index = deserializer.deserialize_variant_index();
            switch (index) {
                case 0: return Update.Load(deserializer);
                case 1: return Error.Load(deserializer);
                case 2: return CompressedUpdate.Load(deserializer);
                default: throw new Serde.DeserializationException("Unknown variant index for A2RMessage: " + index);
            }
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

        public static A2RMessage BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static A2RMessage BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            A2RMessage value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override int GetHashCode() {
            switch (this) {
            case Update x: return x.GetHashCode();
            case Error x: return x.GetHashCode();
            case CompressedUpdate x: return x.GetHashCode();
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }
        public override bool Equals(object obj) => obj is A2RMessage other && Equals(other);

        public bool Equals(A2RMessage other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (GetType() != other.GetType()) return false;
            switch (this) {
            case Update x: return x.Equals((Update)other);
            case Error x: return x.Equals((Error)other);
            case CompressedUpdate x: return x.Equals((CompressedUpdate)other);
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public A2RMessage Clone() => (A2RMessage)MemberwiseClone();

        object ICloneable.Clone() => Clone();


        public sealed class Update: A2RMessage, IEquatable<Update>, ICloneable {
            public A2RUpdate value;

            public Update(A2RUpdate _value) {
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(0);
                value.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Update Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Update obj = new Update(
                	A2RUpdate.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Update other && Equals(other);

            public static bool operator ==(Update left, Update right) => Equals(left, right);

            public static bool operator !=(Update left, Update right) => !Equals(left, right);

            public bool Equals(Update other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!value.Equals(other.value)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + value.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class Error: A2RMessage, IEquatable<Error>, ICloneable {
            public _boldui_protocol.Error value;

            public Error(_boldui_protocol.Error _value) {
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(1);
                value.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Error Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Error obj = new Error(
                	_boldui_protocol.Error.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Error other && Equals(other);

            public static bool operator ==(Error left, Error right) => Equals(left, right);

            public static bool operator !=(Error left, Error right) => !Equals(left, right);

            public bool Equals(Error other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!value.Equals(other.value)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + value.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class CompressedUpdate: A2RMessage, IEquatable<CompressedUpdate>, ICloneable {
            public Serde.ValueArray<byte> value;

            public CompressedUpdate(Serde.ValueArray<byte> _value) {
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(2);
                TraitHelpers.serialize_vector_u8(value, serializer);
                serializer.decrease_container_depth();
            }

            internal static CompressedUpdate Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                CompressedUpdate obj = new CompressedUpdate(
                	TraitHelpers.deserialize_vector_u8(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is CompressedUpdate other && Equals(other);

            public static bool operator ==(CompressedUpdate left, CompressedUpdate right) => Equals(left, right);

            public static bool operator !=(CompressedUpdate left, CompressedUpdate right) => !Equals(left, right);

            public bool Equals(CompressedUpdate other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!value.Equals(other.value)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + value.GetHashCode();
                    return value;
                }
            }

        }
    }


} // end of namespace _boldui_protocol
