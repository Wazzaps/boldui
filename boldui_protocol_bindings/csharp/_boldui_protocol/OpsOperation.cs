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
                case 8: return FloorDiv.Load(deserializer);
                case 9: return Eq.Load(deserializer);
                case 10: return Min.Load(deserializer);
                case 11: return Max.Load(deserializer);
                case 12: return Or.Load(deserializer);
                case 13: return And.Load(deserializer);
                case 14: return GreaterThan.Load(deserializer);
                case 15: return Abs.Load(deserializer);
                case 16: return Sin.Load(deserializer);
                case 17: return Cos.Load(deserializer);
                case 18: return MakePoint.Load(deserializer);
                case 19: return MakeRectFromPoints.Load(deserializer);
                case 20: return MakeRectFromSides.Load(deserializer);
                case 21: return MakeColor.Load(deserializer);
                case 22: return ToString.Load(deserializer);
                case 23: return If.Load(deserializer);
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
            case FloorDiv x: return x.GetHashCode();
            case Eq x: return x.GetHashCode();
            case Min x: return x.GetHashCode();
            case Max x: return x.GetHashCode();
            case Or x: return x.GetHashCode();
            case And x: return x.GetHashCode();
            case GreaterThan x: return x.GetHashCode();
            case Abs x: return x.GetHashCode();
            case Sin x: return x.GetHashCode();
            case Cos x: return x.GetHashCode();
            case MakePoint x: return x.GetHashCode();
            case MakeRectFromPoints x: return x.GetHashCode();
            case MakeRectFromSides x: return x.GetHashCode();
            case MakeColor x: return x.GetHashCode();
            case ToString x: return x.GetHashCode();
            case If x: return x.GetHashCode();
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
            case FloorDiv x: return x.Equals((FloorDiv)other);
            case Eq x: return x.Equals((Eq)other);
            case Min x: return x.Equals((Min)other);
            case Max x: return x.Equals((Max)other);
            case Or x: return x.Equals((Or)other);
            case And x: return x.Equals((And)other);
            case GreaterThan x: return x.Equals((GreaterThan)other);
            case Abs x: return x.Equals((Abs)other);
            case Sin x: return x.Equals((Sin)other);
            case Cos x: return x.Equals((Cos)other);
            case MakePoint x: return x.Equals((MakePoint)other);
            case MakeRectFromPoints x: return x.Equals((MakeRectFromPoints)other);
            case MakeRectFromSides x: return x.Equals((MakeRectFromSides)other);
            case MakeColor x: return x.Equals((MakeColor)other);
            case ToString x: return x.Equals((ToString)other);
            case If x: return x.Equals((If)other);
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

        public sealed class FloorDiv: OpsOperation, IEquatable<FloorDiv>, ICloneable {
            public OpId a;
            public OpId b;

            public FloorDiv(OpId _a, OpId _b) {
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

            internal static FloorDiv Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                FloorDiv obj = new FloorDiv(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is FloorDiv other && Equals(other);

            public static bool operator ==(FloorDiv left, FloorDiv right) => Equals(left, right);

            public static bool operator !=(FloorDiv left, FloorDiv right) => !Equals(left, right);

            public bool Equals(FloorDiv other) {
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
                serializer.serialize_variant_index(9);
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
                serializer.serialize_variant_index(10);
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
                serializer.serialize_variant_index(11);
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

        public sealed class Or: OpsOperation, IEquatable<Or>, ICloneable {
            public OpId a;
            public OpId b;

            public Or(OpId _a, OpId _b) {
                if (_a == null) throw new ArgumentNullException(nameof(_a));
                a = _a;
                if (_b == null) throw new ArgumentNullException(nameof(_b));
                b = _b;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(12);
                a.Serialize(serializer);
                b.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Or Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Or obj = new Or(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Or other && Equals(other);

            public static bool operator ==(Or left, Or right) => Equals(left, right);

            public static bool operator !=(Or left, Or right) => !Equals(left, right);

            public bool Equals(Or other) {
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

        public sealed class And: OpsOperation, IEquatable<And>, ICloneable {
            public OpId a;
            public OpId b;

            public And(OpId _a, OpId _b) {
                if (_a == null) throw new ArgumentNullException(nameof(_a));
                a = _a;
                if (_b == null) throw new ArgumentNullException(nameof(_b));
                b = _b;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(13);
                a.Serialize(serializer);
                b.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static And Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                And obj = new And(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is And other && Equals(other);

            public static bool operator ==(And left, And right) => Equals(left, right);

            public static bool operator !=(And left, And right) => !Equals(left, right);

            public bool Equals(And other) {
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

        public sealed class GreaterThan: OpsOperation, IEquatable<GreaterThan>, ICloneable {
            public OpId a;
            public OpId b;

            public GreaterThan(OpId _a, OpId _b) {
                if (_a == null) throw new ArgumentNullException(nameof(_a));
                a = _a;
                if (_b == null) throw new ArgumentNullException(nameof(_b));
                b = _b;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(14);
                a.Serialize(serializer);
                b.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static GreaterThan Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                GreaterThan obj = new GreaterThan(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is GreaterThan other && Equals(other);

            public static bool operator ==(GreaterThan left, GreaterThan right) => Equals(left, right);

            public static bool operator !=(GreaterThan left, GreaterThan right) => !Equals(left, right);

            public bool Equals(GreaterThan other) {
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

        public sealed class Abs: OpsOperation, IEquatable<Abs>, ICloneable {
            public OpId a;

            public Abs(OpId _a) {
                if (_a == null) throw new ArgumentNullException(nameof(_a));
                a = _a;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(15);
                a.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Abs Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Abs obj = new Abs(
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Abs other && Equals(other);

            public static bool operator ==(Abs left, Abs right) => Equals(left, right);

            public static bool operator !=(Abs left, Abs right) => !Equals(left, right);

            public bool Equals(Abs other) {
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

        public sealed class Sin: OpsOperation, IEquatable<Sin>, ICloneable {
            public OpId a;

            public Sin(OpId _a) {
                if (_a == null) throw new ArgumentNullException(nameof(_a));
                a = _a;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(16);
                a.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Sin Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Sin obj = new Sin(
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Sin other && Equals(other);

            public static bool operator ==(Sin left, Sin right) => Equals(left, right);

            public static bool operator !=(Sin left, Sin right) => !Equals(left, right);

            public bool Equals(Sin other) {
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

        public sealed class Cos: OpsOperation, IEquatable<Cos>, ICloneable {
            public OpId a;

            public Cos(OpId _a) {
                if (_a == null) throw new ArgumentNullException(nameof(_a));
                a = _a;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(17);
                a.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static Cos Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Cos obj = new Cos(
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Cos other && Equals(other);

            public static bool operator ==(Cos left, Cos right) => Equals(left, right);

            public static bool operator !=(Cos left, Cos right) => !Equals(left, right);

            public bool Equals(Cos other) {
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
                serializer.serialize_variant_index(18);
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
                serializer.serialize_variant_index(19);
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
                serializer.serialize_variant_index(20);
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

        public sealed class MakeColor: OpsOperation, IEquatable<MakeColor>, ICloneable {
            public OpId r;
            public OpId g;
            public OpId b;
            public OpId a;

            public MakeColor(OpId _r, OpId _g, OpId _b, OpId _a) {
                if (_r == null) throw new ArgumentNullException(nameof(_r));
                r = _r;
                if (_g == null) throw new ArgumentNullException(nameof(_g));
                g = _g;
                if (_b == null) throw new ArgumentNullException(nameof(_b));
                b = _b;
                if (_a == null) throw new ArgumentNullException(nameof(_a));
                a = _a;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(21);
                r.Serialize(serializer);
                g.Serialize(serializer);
                b.Serialize(serializer);
                a.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static MakeColor Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                MakeColor obj = new MakeColor(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is MakeColor other && Equals(other);

            public static bool operator ==(MakeColor left, MakeColor right) => Equals(left, right);

            public static bool operator !=(MakeColor left, MakeColor right) => !Equals(left, right);

            public bool Equals(MakeColor other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!r.Equals(other.r)) return false;
                if (!g.Equals(other.g)) return false;
                if (!b.Equals(other.b)) return false;
                if (!a.Equals(other.a)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + r.GetHashCode();
                    value = 31 * value + g.GetHashCode();
                    value = 31 * value + b.GetHashCode();
                    value = 31 * value + a.GetHashCode();
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
                serializer.serialize_variant_index(22);
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

        public sealed class If: OpsOperation, IEquatable<If>, ICloneable {
            public OpId condition;
            public OpId then;
            public OpId or_else;

            public If(OpId _condition, OpId _then, OpId _or_else) {
                if (_condition == null) throw new ArgumentNullException(nameof(_condition));
                condition = _condition;
                if (_then == null) throw new ArgumentNullException(nameof(_then));
                then = _then;
                if (_or_else == null) throw new ArgumentNullException(nameof(_or_else));
                or_else = _or_else;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(23);
                condition.Serialize(serializer);
                then.Serialize(serializer);
                or_else.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static If Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                If obj = new If(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is If other && Equals(other);

            public static bool operator ==(If left, If right) => Equals(left, right);

            public static bool operator !=(If left, If right) => !Equals(left, right);

            public bool Equals(If other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!condition.Equals(other.condition)) return false;
                if (!then.Equals(other.then)) return false;
                if (!or_else.Equals(other.or_else)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + condition.GetHashCode();
                    value = 31 * value + then.GetHashCode();
                    value = 31 * value + or_else.GetHashCode();
                    return value;
                }
            }

        }
    }


} // end of namespace _boldui_protocol
