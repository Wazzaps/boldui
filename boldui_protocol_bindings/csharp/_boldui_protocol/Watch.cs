using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class Watch: IEquatable<Watch>, ICloneable {
        public OpId condition;
        public HandlerBlock handler;

        public Watch(OpId _condition, HandlerBlock _handler) {
            if (_condition == null) throw new ArgumentNullException(nameof(_condition));
            condition = _condition;
            if (_handler == null) throw new ArgumentNullException(nameof(_handler));
            handler = _handler;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            condition.Serialize(serializer);
            handler.Serialize(serializer);
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

        public static Watch Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            Watch obj = new Watch(
            	OpId.Deserialize(deserializer),
            	HandlerBlock.Deserialize(deserializer));
            deserializer.decrease_container_depth();
            return obj;
        }

        public static Watch BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static Watch BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            Watch value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is Watch other && Equals(other);

        public static bool operator ==(Watch left, Watch right) => Equals(left, right);

        public static bool operator !=(Watch left, Watch right) => !Equals(left, right);

        public bool Equals(Watch other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!condition.Equals(other.condition)) return false;
            if (!handler.Equals(other.handler)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + condition.GetHashCode();
                value = 31 * value + handler.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public Watch Clone() => (Watch)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
