using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public abstract class EA2RMessage: IEquatable<EA2RMessage>, ICloneable {

        public abstract void Serialize(Serde.ISerializer serializer);

        public static EA2RMessage Deserialize(Serde.IDeserializer deserializer) {
            int index = deserializer.deserialize_variant_index();
            switch (index) {
                case 0: return CreatedExternalWidget.Load(deserializer);
                case 1: return SpontaneousUpdate.Load(deserializer);
                case 2: return UpdateHandled.Load(deserializer);
                case 3: return Error.Load(deserializer);
                default: throw new Serde.DeserializationException("Unknown variant index for EA2RMessage: " + index);
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

        public static EA2RMessage BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static EA2RMessage BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            EA2RMessage value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override int GetHashCode() {
            switch (this) {
            case CreatedExternalWidget x: return x.GetHashCode();
            case SpontaneousUpdate x: return x.GetHashCode();
            case UpdateHandled x: return x.GetHashCode();
            case Error x: return x.GetHashCode();
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }
        public override bool Equals(object obj) => obj is EA2RMessage other && Equals(other);

        public bool Equals(EA2RMessage other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (GetType() != other.GetType()) return false;
            switch (this) {
            case CreatedExternalWidget x: return x.Equals((CreatedExternalWidget)other);
            case SpontaneousUpdate x: return x.Equals((SpontaneousUpdate)other);
            case UpdateHandled x: return x.Equals((UpdateHandled)other);
            case Error x: return x.Equals((Error)other);
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public EA2RMessage Clone() => (EA2RMessage)MemberwiseClone();

        object ICloneable.Clone() => Clone();


        public sealed class CreatedExternalWidget: EA2RMessage, IEquatable<CreatedExternalWidget>, ICloneable {
            public Serde.ValueArray<byte> texture_info;

            public CreatedExternalWidget(Serde.ValueArray<byte> _texture_info) {
                if (_texture_info == null) throw new ArgumentNullException(nameof(_texture_info));
                texture_info = _texture_info;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(0);
                TraitHelpers.serialize_vector_u8(texture_info, serializer);
                serializer.decrease_container_depth();
            }

            internal static CreatedExternalWidget Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                CreatedExternalWidget obj = new CreatedExternalWidget(
                	TraitHelpers.deserialize_vector_u8(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is CreatedExternalWidget other && Equals(other);

            public static bool operator ==(CreatedExternalWidget left, CreatedExternalWidget right) => Equals(left, right);

            public static bool operator !=(CreatedExternalWidget left, CreatedExternalWidget right) => !Equals(left, right);

            public bool Equals(CreatedExternalWidget other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!texture_info.Equals(other.texture_info)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + texture_info.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class SpontaneousUpdate: EA2RMessage, IEquatable<SpontaneousUpdate>, ICloneable {
            public SpontaneousUpdate() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(1);
                serializer.decrease_container_depth();
            }

            internal static SpontaneousUpdate Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                SpontaneousUpdate obj = new SpontaneousUpdate(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is SpontaneousUpdate other && Equals(other);

            public static bool operator ==(SpontaneousUpdate left, SpontaneousUpdate right) => Equals(left, right);

            public static bool operator !=(SpontaneousUpdate left, SpontaneousUpdate right) => !Equals(left, right);

            public bool Equals(SpontaneousUpdate other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    return value;
                }
            }

        }

        public sealed class UpdateHandled: EA2RMessage, IEquatable<UpdateHandled>, ICloneable {
            public UpdateHandled() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(2);
                serializer.decrease_container_depth();
            }

            internal static UpdateHandled Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                UpdateHandled obj = new UpdateHandled(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is UpdateHandled other && Equals(other);

            public static bool operator ==(UpdateHandled left, UpdateHandled right) => Equals(left, right);

            public static bool operator !=(UpdateHandled left, UpdateHandled right) => !Equals(left, right);

            public bool Equals(UpdateHandled other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    return value;
                }
            }

        }

        public sealed class Error: EA2RMessage, IEquatable<Error>, ICloneable {
            public _boldui_protocol.Error value;

            public Error(_boldui_protocol.Error _value) {
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(3);
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
