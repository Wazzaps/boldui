using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public abstract class OpsOperation: IEquatable<OpsOperation>, ICloneable {

        public abstract void Serialize(Serde.ISerializer serializer);

        public static OpsOperation Deserialize(Serde.IDeserializer deserializer) {
            int index = deserializer.deserialize_variant_index();
            switch (index) {
                case 0: return Value.Load(deserializer);
                case 1: return Var.Load(deserializer);
                case 2: return GetTime.Load(deserializer);
                case 3: return Add.Load(deserializer);
                case 4: return Neg.Load(deserializer);
                case 5: return MakePoint.Load(deserializer);
                case 6: return MakeRectFromPoints.Load(deserializer);
                case 7: return MakeRectFromSides.Load(deserializer);
                default: throw new Serde.DeserializationException("Unknown variant index for OpsOperation: " + index);
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

        public static OpsOperation BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static OpsOperation BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            OpsOperation value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override int GetHashCode() {
            switch (this) {
            case Value x: return x.GetHashCode();
            case Var x: return x.GetHashCode();
            case GetTime x: return x.GetHashCode();
            case Add x: return x.GetHashCode();
            case Neg x: return x.GetHashCode();
            case MakePoint x: return x.GetHashCode();
            case MakeRectFromPoints x: return x.GetHashCode();
            case MakeRectFromSides x: return x.GetHashCode();
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }
        public override bool Equals(object obj) => obj is OpsOperation other && Equals(other);

        public bool Equals(OpsOperation other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (GetType() != other.GetType()) return false;
            switch (this) {
            case Value x: return x.Equals((Value)other);
            case Var x: return x.Equals((Var)other);
            case GetTime x: return x.Equals((GetTime)other);
            case Add x: return x.Equals((Add)other);
            case Neg x: return x.Equals((Neg)other);
            case MakePoint x: return x.Equals((MakePoint)other);
            case MakeRectFromPoints x: return x.Equals((MakeRectFromPoints)other);
            case MakeRectFromSides x: return x.Equals((MakeRectFromSides)other);
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public OpsOperation Clone() => (OpsOperation)MemberwiseClone();

        object ICloneable.Clone() => Clone();


        public sealed class Value: OpsOperation, IEquatable<Value>, ICloneable {
            public _boldui_protocol.Value value;

            public Value(_boldui_protocol.Value _value) {
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(0);
                value.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Value Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Value obj = new Value(
                	_boldui_protocol.Value.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Value other && Equals(other);

            public static bool operator ==(Value left, Value right) => Equals(left, right);

            public static bool operator !=(Value left, Value right) => !Equals(left, right);

            public bool Equals(Value other) {
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

        public sealed class Var: OpsOperation, IEquatable<Var>, ICloneable {
            public VarId value;

            public Var(VarId _value) {
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(1);
                value.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Var Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Var obj = new Var(
                	VarId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Var other && Equals(other);

            public static bool operator ==(Var left, Var right) => Equals(left, right);

            public static bool operator !=(Var left, Var right) => !Equals(left, right);

            public bool Equals(Var other) {
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

        public sealed class GetTime: OpsOperation, IEquatable<GetTime>, ICloneable {
            public double low_clamp;
            public double high_clamp;

            public GetTime(double _low_clamp, double _high_clamp) {
                low_clamp = _low_clamp;
                high_clamp = _high_clamp;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(2);
                serializer.serialize_f64(low_clamp);
                serializer.serialize_f64(high_clamp);
                serializer.decrease_container_depth();
            }

            internal static GetTime Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                GetTime obj = new GetTime(
                	deserializer.deserialize_f64(),
                	deserializer.deserialize_f64());
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is GetTime other && Equals(other);

            public static bool operator ==(GetTime left, GetTime right) => Equals(left, right);

            public static bool operator !=(GetTime left, GetTime right) => !Equals(left, right);

            public bool Equals(GetTime other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!low_clamp.Equals(other.low_clamp)) return false;
                if (!high_clamp.Equals(other.high_clamp)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + low_clamp.GetHashCode();
                    value = 31 * value + high_clamp.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class Add: OpsOperation, IEquatable<Add>, ICloneable {
            public OpId a;
            public OpId b;

            public Add(OpId _a, OpId _b) {
                if (_a == null) throw new ArgumentNullException(nameof(_a));
                a = _a;
                if (_b == null) throw new ArgumentNullException(nameof(_b));
                b = _b;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(3);
                a.Serialize(serializer);
                b.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Add Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Add obj = new Add(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Add other && Equals(other);

            public static bool operator ==(Add left, Add right) => Equals(left, right);

            public static bool operator !=(Add left, Add right) => !Equals(left, right);

            public bool Equals(Add other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!a.Equals(other.a)) return false;
                if (!b.Equals(other.b)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + a.GetHashCode();
                    value = 31 * value + b.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class Neg: OpsOperation, IEquatable<Neg>, ICloneable {
            public OpId a;

            public Neg(OpId _a) {
                if (_a == null) throw new ArgumentNullException(nameof(_a));
                a = _a;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(4);
                a.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Neg Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Neg obj = new Neg(
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Neg other && Equals(other);

            public static bool operator ==(Neg left, Neg right) => Equals(left, right);

            public static bool operator !=(Neg left, Neg right) => !Equals(left, right);

            public bool Equals(Neg other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!a.Equals(other.a)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + a.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class MakePoint: OpsOperation, IEquatable<MakePoint>, ICloneable {
            public OpId left;
            public OpId top;

            public MakePoint(OpId _left, OpId _top) {
                if (_left == null) throw new ArgumentNullException(nameof(_left));
                left = _left;
                if (_top == null) throw new ArgumentNullException(nameof(_top));
                top = _top;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(5);
                left.Serialize(serializer);
                top.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static MakePoint Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                MakePoint obj = new MakePoint(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is MakePoint other && Equals(other);

            public static bool operator ==(MakePoint left, MakePoint right) => Equals(left, right);

            public static bool operator !=(MakePoint left, MakePoint right) => !Equals(left, right);

            public bool Equals(MakePoint other) {
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

        public sealed class MakeRectFromPoints: OpsOperation, IEquatable<MakeRectFromPoints>, ICloneable {
            public OpId left_top;
            public OpId right_bottom;

            public MakeRectFromPoints(OpId _left_top, OpId _right_bottom) {
                if (_left_top == null) throw new ArgumentNullException(nameof(_left_top));
                left_top = _left_top;
                if (_right_bottom == null) throw new ArgumentNullException(nameof(_right_bottom));
                right_bottom = _right_bottom;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(6);
                left_top.Serialize(serializer);
                right_bottom.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static MakeRectFromPoints Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                MakeRectFromPoints obj = new MakeRectFromPoints(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is MakeRectFromPoints other && Equals(other);

            public static bool operator ==(MakeRectFromPoints left, MakeRectFromPoints right) => Equals(left, right);

            public static bool operator !=(MakeRectFromPoints left, MakeRectFromPoints right) => !Equals(left, right);

            public bool Equals(MakeRectFromPoints other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!left_top.Equals(other.left_top)) return false;
                if (!right_bottom.Equals(other.right_bottom)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + left_top.GetHashCode();
                    value = 31 * value + right_bottom.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class MakeRectFromSides: OpsOperation, IEquatable<MakeRectFromSides>, ICloneable {
            public OpId left;
            public OpId top;
            public OpId right;
            public OpId bottom;

            public MakeRectFromSides(OpId _left, OpId _top, OpId _right, OpId _bottom) {
                if (_left == null) throw new ArgumentNullException(nameof(_left));
                left = _left;
                if (_top == null) throw new ArgumentNullException(nameof(_top));
                top = _top;
                if (_right == null) throw new ArgumentNullException(nameof(_right));
                right = _right;
                if (_bottom == null) throw new ArgumentNullException(nameof(_bottom));
                bottom = _bottom;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(7);
                left.Serialize(serializer);
                top.Serialize(serializer);
                right.Serialize(serializer);
                bottom.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static MakeRectFromSides Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                MakeRectFromSides obj = new MakeRectFromSides(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is MakeRectFromSides other && Equals(other);

            public static bool operator ==(MakeRectFromSides left, MakeRectFromSides right) => Equals(left, right);

            public static bool operator !=(MakeRectFromSides left, MakeRectFromSides right) => !Equals(left, right);

            public bool Equals(MakeRectFromSides other) {
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
