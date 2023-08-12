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
                case 2: return DrawRoundRect.Load(deserializer);
                case 3: return DrawCenteredText.Load(deserializer);
                case 4: return DrawImage.Load(deserializer);
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
            case DrawRoundRect x: return x.GetHashCode();
            case DrawCenteredText x: return x.GetHashCode();
            case DrawImage x: return x.GetHashCode();
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
            case DrawRoundRect x: return x.Equals((DrawRoundRect)other);
            case DrawCenteredText x: return x.Equals((DrawCenteredText)other);
            case DrawImage x: return x.Equals((DrawImage)other);
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

        public sealed class DrawRoundRect: CmdsCommand, IEquatable<DrawRoundRect>, ICloneable {
            public OpId paint;
            public OpId rect;
            public OpId radius;

            public DrawRoundRect(OpId _paint, OpId _rect, OpId _radius) {
                if (_paint == null) throw new ArgumentNullException(nameof(_paint));
                paint = _paint;
                if (_rect == null) throw new ArgumentNullException(nameof(_rect));
                rect = _rect;
                if (_radius == null) throw new ArgumentNullException(nameof(_radius));
                radius = _radius;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(2);
                paint.Serialize(serializer);
                rect.Serialize(serializer);
                radius.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static DrawRoundRect Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                DrawRoundRect obj = new DrawRoundRect(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is DrawRoundRect other && Equals(other);

            public static bool operator ==(DrawRoundRect left, DrawRoundRect right) => Equals(left, right);

            public static bool operator !=(DrawRoundRect left, DrawRoundRect right) => !Equals(left, right);

            public bool Equals(DrawRoundRect other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!paint.Equals(other.paint)) return false;
                if (!rect.Equals(other.rect)) return false;
                if (!radius.Equals(other.radius)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + paint.GetHashCode();
                    value = 31 * value + rect.GetHashCode();
                    value = 31 * value + radius.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class DrawCenteredText: CmdsCommand, IEquatable<DrawCenteredText>, ICloneable {
            public OpId text;
            public OpId paint;
            public OpId center;

            public DrawCenteredText(OpId _text, OpId _paint, OpId _center) {
                if (_text == null) throw new ArgumentNullException(nameof(_text));
                text = _text;
                if (_paint == null) throw new ArgumentNullException(nameof(_paint));
                paint = _paint;
                if (_center == null) throw new ArgumentNullException(nameof(_center));
                center = _center;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(3);
                text.Serialize(serializer);
                paint.Serialize(serializer);
                center.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static DrawCenteredText Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                DrawCenteredText obj = new DrawCenteredText(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is DrawCenteredText other && Equals(other);

            public static bool operator ==(DrawCenteredText left, DrawCenteredText right) => Equals(left, right);

            public static bool operator !=(DrawCenteredText left, DrawCenteredText right) => !Equals(left, right);

            public bool Equals(DrawCenteredText other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!text.Equals(other.text)) return false;
                if (!paint.Equals(other.paint)) return false;
                if (!center.Equals(other.center)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + text.GetHashCode();
                    value = 31 * value + paint.GetHashCode();
                    value = 31 * value + center.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class DrawImage: CmdsCommand, IEquatable<DrawImage>, ICloneable {
            public OpId res;
            public OpId top_left;

            public DrawImage(OpId _res, OpId _top_left) {
                if (_res == null) throw new ArgumentNullException(nameof(_res));
                res = _res;
                if (_top_left == null) throw new ArgumentNullException(nameof(_top_left));
                top_left = _top_left;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(4);
                res.Serialize(serializer);
                top_left.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static DrawImage Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                DrawImage obj = new DrawImage(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is DrawImage other && Equals(other);

            public static bool operator ==(DrawImage left, DrawImage right) => Equals(left, right);

            public static bool operator !=(DrawImage left, DrawImage right) => !Equals(left, right);

            public bool Equals(DrawImage other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!res.Equals(other.res)) return false;
                if (!top_left.Equals(other.top_left)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + res.GetHashCode();
                    value = 31 * value + top_left.GetHashCode();
                    return value;
                }
            }

        }
    }


} // end of namespace _boldui_protocol
