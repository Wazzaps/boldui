using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public abstract class A2RReparentScene: IEquatable<A2RReparentScene>, ICloneable {

        public abstract void Serialize(Serde.ISerializer serializer);

        public static A2RReparentScene Deserialize(Serde.IDeserializer deserializer) {
            int index = deserializer.deserialize_variant_index();
            switch (index) {
                case 0: return Inside.Load(deserializer);
                case 1: return After.Load(deserializer);
                case 2: return Root.Load(deserializer);
                case 3: return Disconnect.Load(deserializer);
                case 4: return Hide.Load(deserializer);
                default: throw new Serde.DeserializationException("Unknown variant index for A2RReparentScene: " + index);
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

        public static A2RReparentScene BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static A2RReparentScene BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            A2RReparentScene value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override int GetHashCode() {
            switch (this) {
            case Inside x: return x.GetHashCode();
            case After x: return x.GetHashCode();
            case Root x: return x.GetHashCode();
            case Disconnect x: return x.GetHashCode();
            case Hide x: return x.GetHashCode();
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }
        public override bool Equals(object obj) => obj is A2RReparentScene other && Equals(other);

        public bool Equals(A2RReparentScene other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (GetType() != other.GetType()) return false;
            switch (this) {
            case Inside x: return x.Equals((Inside)other);
            case After x: return x.Equals((After)other);
            case Root x: return x.Equals((Root)other);
            case Disconnect x: return x.Equals((Disconnect)other);
            case Hide x: return x.Equals((Hide)other);
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public A2RReparentScene Clone() => (A2RReparentScene)MemberwiseClone();

        object ICloneable.Clone() => Clone();


        public sealed class Inside: A2RReparentScene, IEquatable<Inside>, ICloneable {
            public OpId value;

            public Inside(OpId _value) {
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(0);
                value.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Inside Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Inside obj = new Inside(
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Inside other && Equals(other);

            public static bool operator ==(Inside left, Inside right) => Equals(left, right);

            public static bool operator !=(Inside left, Inside right) => !Equals(left, right);

            public bool Equals(Inside other) {
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

        public sealed class After: A2RReparentScene, IEquatable<After>, ICloneable {
            public OpId value;

            public After(OpId _value) {
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(1);
                value.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static After Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                After obj = new After(
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is After other && Equals(other);

            public static bool operator ==(After left, After right) => Equals(left, right);

            public static bool operator !=(After left, After right) => !Equals(left, right);

            public bool Equals(After other) {
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

        public sealed class Root: A2RReparentScene, IEquatable<Root>, ICloneable {
            public Root() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(2);
                serializer.decrease_container_depth();
            }

            internal static Root Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Root obj = new Root(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Root other && Equals(other);

            public static bool operator ==(Root left, Root right) => Equals(left, right);

            public static bool operator !=(Root left, Root right) => !Equals(left, right);

            public bool Equals(Root other) {
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

        public sealed class Disconnect: A2RReparentScene, IEquatable<Disconnect>, ICloneable {
            public Disconnect() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(3);
                serializer.decrease_container_depth();
            }

            internal static Disconnect Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Disconnect obj = new Disconnect(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Disconnect other && Equals(other);

            public static bool operator ==(Disconnect left, Disconnect right) => Equals(left, right);

            public static bool operator !=(Disconnect left, Disconnect right) => !Equals(left, right);

            public bool Equals(Disconnect other) {
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

        public sealed class Hide: A2RReparentScene, IEquatable<Hide>, ICloneable {
            public Hide() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(4);
                serializer.decrease_container_depth();
            }

            internal static Hide Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Hide obj = new Hide(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Hide other && Equals(other);

            public static bool operator ==(Hide left, Hide right) => Equals(left, right);

            public static bool operator !=(Hide left, Hide right) => !Equals(left, right);

            public bool Equals(Hide other) {
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
    }


} // end of namespace _boldui_protocol
