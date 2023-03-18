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
                case 3: return GetTimeAndClamp.Load(deserializer);
                case 4: return Add.Load(deserializer);
                case 5: return Neg.Load(deserializer);
                case 6: return Mul.Load(deserializer);
                case 7: return Div.Load(deserializer);
                case 8: return Eq.Load(deserializer);
                case 9: return Min.Load(deserializer);
                case 10: return Max.Load(deserializer);
                case 11: return MakePoint.Load(deserializer);
                case 12: return MakeRectFromPoints.Load(deserializer);
                case 13: return MakeRectFromSides.Load(deserializer);
                case 14: return ToString.Load(deserializer);
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
            case GetTimeAndClamp x: return x.GetHashCode();
            case Add x: return x.GetHashCode();
            case Neg x: return x.GetHashCode();
            case Mul x: return x.GetHashCode();
            case Div x: return x.GetHashCode();
            case Eq x: return x.GetHashCode();
            case Min x: return x.GetHashCode();
            case Max x: return x.GetHashCode();
            case MakePoint x: return x.GetHashCode();
            case MakeRectFromPoints x: return x.GetHashCode();
            case MakeRectFromSides x: return x.GetHashCode();
            case ToString x: return x.GetHashCode();
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
            case GetTimeAndClamp x: return x.Equals((GetTimeAndClamp)other);
            case Add x: return x.Equals((Add)other);
            case Neg x: return x.Equals((Neg)other);
            case Mul x: return x.Equals((Mul)other);
            case Div x: return x.Equals((Div)other);
            case Eq x: return x.Equals((Eq)other);
            case Min x: return x.Equals((Min)other);
            case Max x: return x.Equals((Max)other);
            case MakePoint x: return x.Equals((MakePoint)other);
            case MakeRectFromPoints x: return x.Equals((MakeRectFromPoints)other);
            case MakeRectFromSides x: return x.Equals((MakeRectFromSides)other);
            case ToString x: return x.Equals((ToString)other);
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
            public GetTime() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(2);
                serializer.decrease_container_depth();
            }

            internal static GetTime Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                GetTime obj = new GetTime(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is GetTime other && Equals(other);

            public static bool operator ==(GetTime left, GetTime right) => Equals(left, right);

            public static bool operator !=(GetTime left, GetTime right) => !Equals(left, right);

            public bool Equals(GetTime other) {
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

        public sealed class GetTimeAndClamp: OpsOperation, IEquatable<GetTimeAndClamp>, ICloneable {
            public OpId low;
            public OpId high;

            public GetTimeAndClamp(OpId _low, OpId _high) {
                if (_low == null) throw new ArgumentNullException(nameof(_low));
                low = _low;
                if (_high == null) throw new ArgumentNullException(nameof(_high));
                high = _high;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(3);
                low.Serialize(serializer);
                high.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static GetTimeAndClamp Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                GetTimeAndClamp obj = new GetTimeAndClamp(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is GetTimeAndClamp other && Equals(other);

            public static bool operator ==(GetTimeAndClamp left, GetTimeAndClamp right) => Equals(left, right);

            public static bool operator !=(GetTimeAndClamp left, GetTimeAndClamp right) => !Equals(left, right);

            public bool Equals(GetTimeAndClamp other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!low.Equals(other.low)) return false;
                if (!high.Equals(other.high)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + low.GetHashCode();
                    value = 31 * value + high.GetHashCode();
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
                serializer.serialize_variant_index(4);
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
                serializer.serialize_variant_index(5);
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

        public sealed class Mul: OpsOperation, IEquatable<Mul>, ICloneable {
            public OpId a;
            public OpId b;

            public Mul(OpId _a, OpId _b) {
                if (_a == null) throw new ArgumentNullException(nameof(_a));
                a = _a;
                if (_b == null) throw new ArgumentNullException(nameof(_b));
                b = _b;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(6);
                a.Serialize(serializer);
                b.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Mul Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Mul obj = new Mul(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Mul other && Equals(other);

            public static bool operator ==(Mul left, Mul right) => Equals(left, right);

            public static bool operator !=(Mul left, Mul right) => !Equals(left, right);

            public bool Equals(Mul other) {
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

        public sealed class Div: OpsOperation, IEquatable<Div>, ICloneable {
            public OpId a;
            public OpId b;

            public Div(OpId _a, OpId _b) {
                if (_a == null) throw new ArgumentNullException(nameof(_a));
                a = _a;
                if (_b == null) throw new ArgumentNullException(nameof(_b));
                b = _b;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(7);
                a.Serialize(serializer);
                b.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Div Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Div obj = new Div(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Div other && Equals(other);

            public static bool operator ==(Div left, Div right) => Equals(left, right);

            public static bool operator !=(Div left, Div right) => !Equals(left, right);

            public bool Equals(Div other) {
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

        public sealed class Eq: OpsOperation, IEquatable<Eq>, ICloneable {
            public OpId a;
            public OpId b;

            public Eq(OpId _a, OpId _b) {
                if (_a == null) throw new ArgumentNullException(nameof(_a));
                a = _a;
                if (_b == null) throw new ArgumentNullException(nameof(_b));
                b = _b;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(8);
                a.Serialize(serializer);
                b.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Eq Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Eq obj = new Eq(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Eq other && Equals(other);

            public static bool operator ==(Eq left, Eq right) => Equals(left, right);

            public static bool operator !=(Eq left, Eq right) => !Equals(left, right);

            public bool Equals(Eq other) {
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

        public sealed class Min: OpsOperation, IEquatable<Min>, ICloneable {
            public OpId a;
            public OpId b;

            public Min(OpId _a, OpId _b) {
                if (_a == null) throw new ArgumentNullException(nameof(_a));
                a = _a;
                if (_b == null) throw new ArgumentNullException(nameof(_b));
                b = _b;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(9);
                a.Serialize(serializer);
                b.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Min Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Min obj = new Min(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Min other && Equals(other);

            public static bool operator ==(Min left, Min right) => Equals(left, right);

            public static bool operator !=(Min left, Min right) => !Equals(left, right);

            public bool Equals(Min other) {
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

        public sealed class Max: OpsOperation, IEquatable<Max>, ICloneable {
            public OpId a;
            public OpId b;

            public Max(OpId _a, OpId _b) {
                if (_a == null) throw new ArgumentNullException(nameof(_a));
                a = _a;
                if (_b == null) throw new ArgumentNullException(nameof(_b));
                b = _b;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(10);
                a.Serialize(serializer);
                b.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Max Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Max obj = new Max(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Max other && Equals(other);

            public static bool operator ==(Max left, Max right) => Equals(left, right);

            public static bool operator !=(Max left, Max right) => !Equals(left, right);

            public bool Equals(Max other) {
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
                serializer.serialize_variant_index(11);
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
                serializer.serialize_variant_index(12);
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
                serializer.serialize_variant_index(13);
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

        public sealed class ToString: OpsOperation, IEquatable<ToString>, ICloneable {
            public OpId a;

            public ToString(OpId _a) {
                if (_a == null) throw new ArgumentNullException(nameof(_a));
                a = _a;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(14);
                a.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static ToString Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                ToString obj = new ToString(
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is ToString other && Equals(other);

            public static bool operator ==(ToString left, ToString right) => Equals(left, right);

            public static bool operator !=(ToString left, ToString right) => !Equals(left, right);

            public bool Equals(ToString other) {
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
    }


} // end of namespace _boldui_protocol
