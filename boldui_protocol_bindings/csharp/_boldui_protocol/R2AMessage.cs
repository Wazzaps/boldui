using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public abstract class R2AMessage: IEquatable<R2AMessage>, ICloneable {

        public abstract void Serialize(Serde.ISerializer serializer);

        public static R2AMessage Deserialize(Serde.IDeserializer deserializer) {
            int index = deserializer.deserialize_variant_index();
            switch (index) {
                case 0: return Update.Load(deserializer);
                case 1: return Open.Load(deserializer);
                case 2: return Error.Load(deserializer);
                default: throw new Serde.DeserializationException("Unknown variant index for R2AMessage: " + index);
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

        public static R2AMessage BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static R2AMessage BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            R2AMessage value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override int GetHashCode() {
            switch (this) {
            case Update x: return x.GetHashCode();
            case Open x: return x.GetHashCode();
            case Error x: return x.GetHashCode();
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }
        public override bool Equals(object obj) => obj is R2AMessage other && Equals(other);

        public bool Equals(R2AMessage other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (GetType() != other.GetType()) return false;
            switch (this) {
            case Update x: return x.Equals((Update)other);
            case Open x: return x.Equals((Open)other);
            case Error x: return x.Equals((Error)other);
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public R2AMessage Clone() => (R2AMessage)MemberwiseClone();

        object ICloneable.Clone() => Clone();


        public sealed class Update: R2AMessage, IEquatable<Update>, ICloneable {
            public R2AUpdate value;

            public Update(R2AUpdate _value) {
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
                	R2AUpdate.Deserialize(deserializer));
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

        public sealed class Open: R2AMessage, IEquatable<Open>, ICloneable {
            public R2AOpen value;

            public Open(R2AOpen _value) {
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(1);
                value.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Open Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Open obj = new Open(
                	R2AOpen.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Open other && Equals(other);

            public static bool operator ==(Open left, Open right) => Equals(left, right);

            public static bool operator !=(Open left, Open right) => !Equals(left, right);

            public bool Equals(Open other) {
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

        public sealed class Error: R2AMessage, IEquatable<Error>, ICloneable {
            public _boldui_protocol.Error value;

            public Error(_boldui_protocol.Error _value) {
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(2);
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
    }


} // end of namespace _boldui_protocol
