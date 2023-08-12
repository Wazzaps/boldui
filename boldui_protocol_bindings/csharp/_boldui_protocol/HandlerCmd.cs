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
                case 1: return AllocateWindowId.Load(deserializer);
                case 2: return ReparentScene.Load(deserializer);
                case 3: return SetVar.Load(deserializer);
                case 4: return SetVarByRef.Load(deserializer);
                case 5: return DeleteVar.Load(deserializer);
                case 6: return DeleteVarByRef.Load(deserializer);
                case 7: return DebugMessage.Load(deserializer);
                case 8: return Reply.Load(deserializer);
                case 9: return Open.Load(deserializer);
                case 10: return If.Load(deserializer);
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
            case AllocateWindowId x: return x.GetHashCode();
            case ReparentScene x: return x.GetHashCode();
            case SetVar x: return x.GetHashCode();
            case SetVarByRef x: return x.GetHashCode();
            case DeleteVar x: return x.GetHashCode();
            case DeleteVarByRef x: return x.GetHashCode();
            case DebugMessage x: return x.GetHashCode();
            case Reply x: return x.GetHashCode();
            case Open x: return x.GetHashCode();
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
            case AllocateWindowId x: return x.Equals((AllocateWindowId)other);
            case ReparentScene x: return x.Equals((ReparentScene)other);
            case SetVar x: return x.Equals((SetVar)other);
            case SetVarByRef x: return x.Equals((SetVarByRef)other);
            case DeleteVar x: return x.Equals((DeleteVar)other);
            case DeleteVarByRef x: return x.Equals((DeleteVarByRef)other);
            case DebugMessage x: return x.Equals((DebugMessage)other);
            case Reply x: return x.Equals((Reply)other);
            case Open x: return x.Equals((Open)other);
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

        public sealed class AllocateWindowId: HandlerCmd, IEquatable<AllocateWindowId>, ICloneable {
            public AllocateWindowId() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(1);
                serializer.decrease_container_depth();
            }

            internal static AllocateWindowId Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                AllocateWindowId obj = new AllocateWindowId(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is AllocateWindowId other && Equals(other);

            public static bool operator ==(AllocateWindowId left, AllocateWindowId right) => Equals(left, right);

            public static bool operator !=(AllocateWindowId left, AllocateWindowId right) => !Equals(left, right);

            public bool Equals(AllocateWindowId other) {
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
            public OpId scene;
            public A2RReparentScene to;

            public ReparentScene(OpId _scene, A2RReparentScene _to) {
                if (_scene == null) throw new ArgumentNullException(nameof(_scene));
                scene = _scene;
                if (_to == null) throw new ArgumentNullException(nameof(_to));
                to = _to;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(2);
                scene.Serialize(serializer);
                to.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static ReparentScene Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                ReparentScene obj = new ReparentScene(
                	OpId.Deserialize(deserializer),
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

        public sealed class SetVar: HandlerCmd, IEquatable<SetVar>, ICloneable {
            public VarId var;
            public OpId value;

            public SetVar(VarId _var, OpId _value) {
                if (_var == null) throw new ArgumentNullException(nameof(_var));
                var = _var;
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(3);
                var.Serialize(serializer);
                value.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static SetVar Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                SetVar obj = new SetVar(
                	VarId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is SetVar other && Equals(other);

            public static bool operator ==(SetVar left, SetVar right) => Equals(left, right);

            public static bool operator !=(SetVar left, SetVar right) => !Equals(left, right);

            public bool Equals(SetVar other) {
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

        public sealed class SetVarByRef: HandlerCmd, IEquatable<SetVarByRef>, ICloneable {
            public OpId var;
            public OpId value;

            public SetVarByRef(OpId _var, OpId _value) {
                if (_var == null) throw new ArgumentNullException(nameof(_var));
                var = _var;
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(4);
                var.Serialize(serializer);
                value.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static SetVarByRef Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                SetVarByRef obj = new SetVarByRef(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is SetVarByRef other && Equals(other);

            public static bool operator ==(SetVarByRef left, SetVarByRef right) => Equals(left, right);

            public static bool operator !=(SetVarByRef left, SetVarByRef right) => !Equals(left, right);

            public bool Equals(SetVarByRef other) {
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

        public sealed class DeleteVar: HandlerCmd, IEquatable<DeleteVar>, ICloneable {
            public VarId var;
            public OpId value;

            public DeleteVar(VarId _var, OpId _value) {
                if (_var == null) throw new ArgumentNullException(nameof(_var));
                var = _var;
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(5);
                var.Serialize(serializer);
                value.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static DeleteVar Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                DeleteVar obj = new DeleteVar(
                	VarId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is DeleteVar other && Equals(other);

            public static bool operator ==(DeleteVar left, DeleteVar right) => Equals(left, right);

            public static bool operator !=(DeleteVar left, DeleteVar right) => !Equals(left, right);

            public bool Equals(DeleteVar other) {
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

        public sealed class DeleteVarByRef: HandlerCmd, IEquatable<DeleteVarByRef>, ICloneable {
            public OpId var;
            public OpId value;

            public DeleteVarByRef(OpId _var, OpId _value) {
                if (_var == null) throw new ArgumentNullException(nameof(_var));
                var = _var;
                if (_value == null) throw new ArgumentNullException(nameof(_value));
                value = _value;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(6);
                var.Serialize(serializer);
                value.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static DeleteVarByRef Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                DeleteVarByRef obj = new DeleteVarByRef(
                	OpId.Deserialize(deserializer),
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is DeleteVarByRef other && Equals(other);

            public static bool operator ==(DeleteVarByRef left, DeleteVarByRef right) => Equals(left, right);

            public static bool operator !=(DeleteVarByRef left, DeleteVarByRef right) => !Equals(left, right);

            public bool Equals(DeleteVarByRef other) {
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

        public sealed class DebugMessage: HandlerCmd, IEquatable<DebugMessage>, ICloneable {
            public string msg;

            public DebugMessage(string _msg) {
                if (_msg == null) throw new ArgumentNullException(nameof(_msg));
                msg = _msg;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(7);
                serializer.serialize_str(msg);
                serializer.decrease_container_depth();
            }

            internal static DebugMessage Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                DebugMessage obj = new DebugMessage(
                	deserializer.deserialize_str());
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is DebugMessage other && Equals(other);

            public static bool operator ==(DebugMessage left, DebugMessage right) => Equals(left, right);

            public static bool operator !=(DebugMessage left, DebugMessage right) => !Equals(left, right);

            public bool Equals(DebugMessage other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!msg.Equals(other.msg)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + msg.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class Reply: HandlerCmd, IEquatable<Reply>, ICloneable {
            public string path;
            public Serde.ValueArray<OpId> params;

            public Reply(string _path, Serde.ValueArray<OpId> _params) {
                if (_path == null) throw new ArgumentNullException(nameof(_path));
                path = _path;
                if (_params == null) throw new ArgumentNullException(nameof(_params));
                params = _params;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(8);
                serializer.serialize_str(path);
                TraitHelpers.serialize_vector_OpId(params, serializer);
                serializer.decrease_container_depth();
            }

            internal static Reply Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Reply obj = new Reply(
                	deserializer.deserialize_str(),
                	TraitHelpers.deserialize_vector_OpId(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Reply other && Equals(other);

            public static bool operator ==(Reply left, Reply right) => Equals(left, right);

            public static bool operator !=(Reply left, Reply right) => !Equals(left, right);

            public bool Equals(Reply other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!path.Equals(other.path)) return false;
                if (!params.Equals(other.params)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + path.GetHashCode();
                    value = 31 * value + params.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class Open: HandlerCmd, IEquatable<Open>, ICloneable {
            public string path;

            public Open(string _path) {
                if (_path == null) throw new ArgumentNullException(nameof(_path));
                path = _path;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(9);
                serializer.serialize_str(path);
                serializer.decrease_container_depth();
            }

            internal static Open Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Open obj = new Open(
                	deserializer.deserialize_str());
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Open other && Equals(other);

            public static bool operator ==(Open left, Open right) => Equals(left, right);

            public static bool operator !=(Open left, Open right) => !Equals(left, right);

            public bool Equals(Open other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!path.Equals(other.path)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + path.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class If: HandlerCmd, IEquatable<If>, ICloneable {
            public OpId condition;
            public Serde.ValueArray<HandlerCmd> then;
            public Serde.ValueArray<HandlerCmd> or_else;

            public If(OpId _condition, Serde.ValueArray<HandlerCmd> _then, Serde.ValueArray<HandlerCmd> _or_else) {
                if (_condition == null) throw new ArgumentNullException(nameof(_condition));
                condition = _condition;
                if (_then == null) throw new ArgumentNullException(nameof(_then));
                then = _then;
                if (_or_else == null) throw new ArgumentNullException(nameof(_or_else));
                or_else = _or_else;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(10);
                condition.Serialize(serializer);
                TraitHelpers.serialize_vector_HandlerCmd(then, serializer);
                TraitHelpers.serialize_vector_HandlerCmd(or_else, serializer);
                serializer.decrease_container_depth();
            }

            internal static If Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                If obj = new If(
                	OpId.Deserialize(deserializer),
                	TraitHelpers.deserialize_vector_HandlerCmd(deserializer),
                	TraitHelpers.deserialize_vector_HandlerCmd(deserializer));
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
