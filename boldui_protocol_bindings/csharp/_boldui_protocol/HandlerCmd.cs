using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public abstract class HandlerCmd: IEquatable<HandlerCmd>, ICloneable {

        public abstract void Serialize(Serde.ISerializer serializer);

        public static HandlerCmd Deserialize(Serde.IDeserializer deserializer) {
            int index = deserializer.deserialize_variant_index();
            switch (index) {
                case 0: return Nop.Load(deserializer);
                case 1: return ReparentScene.Load(deserializer);
                case 2: return UpdateVar.Load(deserializer);
                case 3: return If.Load(deserializer);
                default: throw new Serde.DeserializationException("Unknown variant index for HandlerCmd: " + index);
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

        public static HandlerCmd BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static HandlerCmd BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            HandlerCmd value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override int GetHashCode() {
            switch (this) {
            case Nop x: return x.GetHashCode();
            case ReparentScene x: return x.GetHashCode();
            case UpdateVar x: return x.GetHashCode();
            case If x: return x.GetHashCode();
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }
        public override bool Equals(object obj) => obj is HandlerCmd other && Equals(other);

        public bool Equals(HandlerCmd other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (GetType() != other.GetType()) return false;
            switch (this) {
            case Nop x: return x.Equals((Nop)other);
            case ReparentScene x: return x.Equals((ReparentScene)other);
            case UpdateVar x: return x.Equals((UpdateVar)other);
            case If x: return x.Equals((If)other);
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public HandlerCmd Clone() => (HandlerCmd)MemberwiseClone();

        object ICloneable.Clone() => Clone();


        public sealed class Nop: HandlerCmd, IEquatable<Nop>, ICloneable {
            public Nop() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(0);
                serializer.decrease_container_depth();
            }

            internal static Nop Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Nop obj = new Nop(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Nop other && Equals(other);

            public static bool operator ==(Nop left, Nop right) => Equals(left, right);

            public static bool operator !=(Nop left, Nop right) => !Equals(left, right);

            public bool Equals(Nop other) {
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

        public sealed class ReparentScene: HandlerCmd, IEquatable<ReparentScene>, ICloneable {
            public uint scene;
            public A2RReparentScene to;

            public ReparentScene(uint _scene, A2RReparentScene _to) {
                scene = _scene;
                if (_to == null) throw new ArgumentNullException(nameof(_to));
                to = _to;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(1);
                serializer.serialize_u32(scene);
                to.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static ReparentScene Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                ReparentScene obj = new ReparentScene(
                	deserializer.deserialize_u32(),
                	A2RReparentScene.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is ReparentScene other && Equals(other);

            public static bool operator ==(ReparentScene left, ReparentScene right) => Equals(left, right);

            public static bool operator !=(ReparentScene left, ReparentScene right) => !Equals(left, right);

            public bool Equals(ReparentScene other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!scene.Equals(other.scene)) return false;
                if (!to.Equals(other.to)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + scene.GetHashCode();
                    value = 31 * value + to.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class UpdateVar: HandlerCmd, IEquatable<UpdateVar>, ICloneable {
            public VarId var;
            public OpId value;

            public UpdateVar(VarId _var, OpId _value) {
                if (_var == null) throw new ArgumentNullException(nameof(_var));
                var = _var;
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(2);
                var.Serialize(serializer);
                value.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static UpdateVar Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                UpdateVar obj = new UpdateVar(
                	VarId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is UpdateVar other && Equals(other);

            public static bool operator ==(UpdateVar left, UpdateVar right) => Equals(left, right);

            public static bool operator !=(UpdateVar left, UpdateVar right) => !Equals(left, right);

            public bool Equals(UpdateVar other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!var.Equals(other.var)) return false;
                if (!value.Equals(other.value)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + var.GetHashCode();
                    value = 31 * value + value.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class If: HandlerCmd, IEquatable<If>, ICloneable {
            public OpId condition;
            public HandlerCmd then;
            public HandlerCmd or_else;

            public If(OpId _condition, HandlerCmd _then, HandlerCmd _or_else) {
                if (_condition == null) throw new ArgumentNullException(nameof(_condition));
                condition = _condition;
                if (_then == null) throw new ArgumentNullException(nameof(_then));
                then = _then;
                if (_or_else == null) throw new ArgumentNullException(nameof(_or_else));
                or_else = _or_else;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(3);
                condition.Serialize(serializer);
                then.Serialize(serializer);
                or_else.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static If Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                If obj = new If(
                	OpId.Deserialize(deserializer),
                	HandlerCmd.Deserialize(deserializer),
                	HandlerCmd.Deserialize(deserializer));
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