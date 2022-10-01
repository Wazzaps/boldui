using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public abstract class CmdsCommand: IEquatable<CmdsCommand>, ICloneable {

        public abstract void Serialize(Serde.ISerializer serializer);

        public static CmdsCommand Deserialize(Serde.IDeserializer deserializer) {
            int index = deserializer.deserialize_variant_index();
            switch (index) {
                case 0: return Clear.Load(deserializer);
                case 1: return DrawRect.Load(deserializer);
                default: throw new Serde.DeserializationException("Unknown variant index for CmdsCommand: " + index);
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

        public static CmdsCommand BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static CmdsCommand BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            CmdsCommand value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override int GetHashCode() {
            switch (this) {
            case Clear x: return x.GetHashCode();
            case DrawRect x: return x.GetHashCode();
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }
        public override bool Equals(object obj) => obj is CmdsCommand other && Equals(other);

        public bool Equals(CmdsCommand other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (GetType() != other.GetType()) return false;
            switch (this) {
            case Clear x: return x.Equals((Clear)other);
            case DrawRect x: return x.Equals((DrawRect)other);
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public CmdsCommand Clone() => (CmdsCommand)MemberwiseClone();

        object ICloneable.Clone() => Clone();


        public sealed class Clear: CmdsCommand, IEquatable<Clear>, ICloneable {
            public OpId color;

            public Clear(OpId _color) {
                if (_color == null) throw new ArgumentNullException(nameof(_color));
                color = _color;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(0);
                color.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Clear Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Clear obj = new Clear(
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Clear other && Equals(other);

            public static bool operator ==(Clear left, Clear right) => Equals(left, right);

            public static bool operator !=(Clear left, Clear right) => !Equals(left, right);

            public bool Equals(Clear other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!color.Equals(other.color)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + color.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class DrawRect: CmdsCommand, IEquatable<DrawRect>, ICloneable {
            public OpId paint;
            public OpId rect;

            public DrawRect(OpId _paint, OpId _rect) {
                if (_paint == null) throw new ArgumentNullException(nameof(_paint));
                paint = _paint;
                if (_rect == null) throw new ArgumentNullException(nameof(_rect));
                rect = _rect;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(1);
                paint.Serialize(serializer);
                rect.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static DrawRect Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                DrawRect obj = new DrawRect(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is DrawRect other && Equals(other);

            public static bool operator ==(DrawRect left, DrawRect right) => Equals(left, right);

            public static bool operator !=(DrawRect left, DrawRect right) => !Equals(left, right);

            public bool Equals(DrawRect other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!paint.Equals(other.paint)) return false;
                if (!rect.Equals(other.rect)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + paint.GetHashCode();
                    value = 31 * value + rect.GetHashCode();
                    return value;
                }
            }

        }
    }


} // end of namespace _boldui_protocol
