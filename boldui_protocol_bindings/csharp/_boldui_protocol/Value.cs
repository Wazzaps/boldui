using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public abstract class Value: IEquatable<Value>, ICloneable {

        public abstract void Serialize(Serde.ISerializer serializer);

        public static Value Deserialize(Serde.IDeserializer deserializer) {
            int index = deserializer.deserialize_variant_index();
            switch (index) {
                case 0: return Sint64.Load(deserializer);
                case 1: return Double.Load(deserializer);
                case 2: return String.Load(deserializer);
                case 3: return Color.Load(deserializer);
                case 4: return Resource.Load(deserializer);
                case 5: return VarRef.Load(deserializer);
                case 6: return Point.Load(deserializer);
                case 7: return Rect.Load(deserializer);
                default: throw new Serde.DeserializationException("Unknown variant index for Value: " + index);
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

        public static Value BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static Value BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            Value value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override int GetHashCode() {
            switch (this) {
            case Sint64 x: return x.GetHashCode();
            case Double x: return x.GetHashCode();
            case String x: return x.GetHashCode();
            case Color x: return x.GetHashCode();
            case Resource x: return x.GetHashCode();
            case VarRef x: return x.GetHashCode();
            case Point x: return x.GetHashCode();
            case Rect x: return x.GetHashCode();
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }
        public override bool Equals(object obj) => obj is Value other && Equals(other);

        public bool Equals(Value other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (GetType() != other.GetType()) return false;
            switch (this) {
            case Sint64 x: return x.Equals((Sint64)other);
            case Double x: return x.Equals((Double)other);
            case String x: return x.Equals((String)other);
            case Color x: return x.Equals((Color)other);
            case Resource x: return x.Equals((Resource)other);
            case VarRef x: return x.Equals((VarRef)other);
            case Point x: return x.Equals((Point)other);
            case Rect x: return x.Equals((Rect)other);
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public Value Clone() => (Value)MemberwiseClone();

        object ICloneable.Clone() => Clone();


        public sealed class Sint64: Value, IEquatable<Sint64>, ICloneable {
            public long value;

            public Sint64(long _value) {
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(0);
                serializer.serialize_i64(value);
                serializer.decrease_container_depth();
            }

            internal static Sint64 Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Sint64 obj = new Sint64(
                	deserializer.deserialize_i64());
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Sint64 other && Equals(other);

            public static bool operator ==(Sint64 left, Sint64 right) => Equals(left, right);

            public static bool operator !=(Sint64 left, Sint64 right) => !Equals(left, right);

            public bool Equals(Sint64 other) {
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

        public sealed class Double: Value, IEquatable<Double>, ICloneable {
            public double value;

            public Double(double _value) {
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(1);
                serializer.serialize_f64(value);
                serializer.decrease_container_depth();
            }

            internal static Double Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Double obj = new Double(
                	deserializer.deserialize_f64());
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Double other && Equals(other);

            public static bool operator ==(Double left, Double right) => Equals(left, right);

            public static bool operator !=(Double left, Double right) => !Equals(left, right);

            public bool Equals(Double other) {
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

        public sealed class String: Value, IEquatable<String>, ICloneable {
            public string value;

            public String(string _value) {
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(2);
                serializer.serialize_str(value);
                serializer.decrease_container_depth();
            }

            internal static String Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                String obj = new String(
                	deserializer.deserialize_str());
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is String other && Equals(other);

            public static bool operator ==(String left, String right) => Equals(left, right);

            public static bool operator !=(String left, String right) => !Equals(left, right);

            public bool Equals(String other) {
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

        public sealed class Color: Value, IEquatable<Color>, ICloneable {
            public _boldui_protocol.Color value;

            public Color(_boldui_protocol.Color _value) {
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(3);
                value.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Color Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Color obj = new Color(
                	_boldui_protocol.Color.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Color other && Equals(other);

            public static bool operator ==(Color left, Color right) => Equals(left, right);

            public static bool operator !=(Color left, Color right) => !Equals(left, right);

            public bool Equals(Color other) {
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

        public sealed class Resource: Value, IEquatable<Resource>, ICloneable {
            public uint value;

            public Resource(uint _value) {
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(4);
                serializer.serialize_u32(value);
                serializer.decrease_container_depth();
            }

            internal static Resource Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Resource obj = new Resource(
                	deserializer.deserialize_u32());
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Resource other && Equals(other);

            public static bool operator ==(Resource left, Resource right) => Equals(left, right);

            public static bool operator !=(Resource left, Resource right) => !Equals(left, right);

            public bool Equals(Resource other) {
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

        public sealed class VarRef: Value, IEquatable<VarRef>, ICloneable {
            public VarId value;

            public VarRef(VarId _value) {
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(5);
                value.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static VarRef Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                VarRef obj = new VarRef(
                	VarId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is VarRef other && Equals(other);

            public static bool operator ==(VarRef left, VarRef right) => Equals(left, right);

            public static bool operator !=(VarRef left, VarRef right) => !Equals(left, right);

            public bool Equals(VarRef other) {
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

        public sealed class Point: Value, IEquatable<Point>, ICloneable {
            public double left;
            public double top;

            public Point(double _left, double _top) {
                left = _left;
                top = _top;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(6);
                serializer.serialize_f64(left);
                serializer.serialize_f64(top);
                serializer.decrease_container_depth();
            }

            internal static Point Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Point obj = new Point(
                	deserializer.deserialize_f64(),
                	deserializer.deserialize_f64());
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Point other && Equals(other);

            public static bool operator ==(Point left, Point right) => Equals(left, right);

            public static bool operator !=(Point left, Point right) => !Equals(left, right);

            public bool Equals(Point other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!left.Equals(other.left)) return false;
                if (!top.Equals(other.top)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + left.GetHashCode();
                    value = 31 * value + top.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class Rect: Value, IEquatable<Rect>, ICloneable {
            public double left;
            public double top;
            public double right;
            public double bottom;

            public Rect(double _left, double _top, double _right, double _bottom) {
                left = _left;
                top = _top;
                right = _right;
                bottom = _bottom;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(7);
                serializer.serialize_f64(left);
                serializer.serialize_f64(top);
                serializer.serialize_f64(right);
                serializer.serialize_f64(bottom);
                serializer.decrease_container_depth();
            }

            internal static Rect Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Rect obj = new Rect(
                	deserializer.deserialize_f64(),
                	deserializer.deserialize_f64(),
                	deserializer.deserialize_f64(),
                	deserializer.deserialize_f64());
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Rect other && Equals(other);

            public static bool operator ==(Rect left, Rect right) => Equals(left, right);

            public static bool operator !=(Rect left, Rect right) => !Equals(left, right);

            public bool Equals(Rect other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!left.Equals(other.left)) return false;
                if (!top.Equals(other.top)) return false;
                if (!right.Equals(other.right)) return false;
                if (!bottom.Equals(other.bottom)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + left.GetHashCode();
                    value = 31 * value + top.GetHashCode();
                    value = 31 * value + right.GetHashCode();
                    value = 31 * value + bottom.GetHashCode();
                    return value;
                }
            }

        }
    }


} // end of namespace _boldui_protocol
