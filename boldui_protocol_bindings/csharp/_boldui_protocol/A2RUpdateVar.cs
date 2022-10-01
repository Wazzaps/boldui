using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class A2RUpdateVar: IEquatable<A2RUpdateVar>, ICloneable {
        public VarId var;
        public Serde.ValueArray<OpsOperation> ops;

        public A2RUpdateVar(VarId _var, Serde.ValueArray<OpsOperation> _ops) {
            if (_var == null) throw new ArgumentNullException(nameof(_var));
            var = _var;
            if (_ops == null) throw new ArgumentNullException(nameof(_ops));
            ops = _ops;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            var.Serialize(serializer);
            TraitHelpers.serialize_vector_OpsOperation(ops, serializer);
            serializer.decrease_container_depth();
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

        public static A2RUpdateVar Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            A2RUpdateVar obj = new A2RUpdateVar(
            	VarId.Deserialize(deserializer),
            	TraitHelpers.deserialize_vector_OpsOperation(deserializer));
            deserializer.decrease_container_depth();
            return obj;
        }

        public static A2RUpdateVar BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static A2RUpdateVar BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            A2RUpdateVar value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is A2RUpdateVar other && Equals(other);

        public static bool operator ==(A2RUpdateVar left, A2RUpdateVar right) => Equals(left, right);

        public static bool operator !=(A2RUpdateVar left, A2RUpdateVar right) => !Equals(left, right);

        public bool Equals(A2RUpdateVar other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!var.Equals(other.var)) return false;
            if (!ops.Equals(other.ops)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + var.GetHashCode();
                value = 31 * value + ops.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public A2RUpdateVar Clone() => (A2RUpdateVar)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
