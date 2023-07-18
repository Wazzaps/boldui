using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public abstract class EventType: IEquatable<EventType>, ICloneable {

        public abstract void Serialize(Serde.ISerializer serializer);

        public static EventType Deserialize(Serde.IDeserializer deserializer) {
            int index = deserializer.deserialize_variant_index();
            switch (index) {
                case 0: return MouseDown.Load(deserializer);
                case 1: return MouseUp.Load(deserializer);
                default: throw new Serde.DeserializationException("Unknown variant index for EventType: " + index);
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

        public static EventType BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static EventType BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            EventType value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override int GetHashCode() {
            switch (this) {
            case MouseDown x: return x.GetHashCode();
            case MouseUp x: return x.GetHashCode();
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }
        public override bool Equals(object obj) => obj is EventType other && Equals(other);

        public bool Equals(EventType other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (GetType() != other.GetType()) return false;
            switch (this) {
            case MouseDown x: return x.Equals((MouseDown)other);
            case MouseUp x: return x.Equals((MouseUp)other);
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public EventType Clone() => (EventType)MemberwiseClone();

        object ICloneable.Clone() => Clone();


        public sealed class MouseDown: EventType, IEquatable<MouseDown>, ICloneable {
            public OpId rect;

            public MouseDown(OpId _rect) {
                if (_rect == null) throw new ArgumentNullException(nameof(_rect));
                rect = _rect;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(0);
                rect.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static MouseDown Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                MouseDown obj = new MouseDown(
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is MouseDown other && Equals(other);

            public static bool operator ==(MouseDown left, MouseDown right) => Equals(left, right);

            public static bool operator !=(MouseDown left, MouseDown right) => !Equals(left, right);

            public bool Equals(MouseDown other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!rect.Equals(other.rect)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + rect.GetHashCode();
                    return value;
                }
            }

        }

        public sealed class MouseUp: EventType, IEquatable<MouseUp>, ICloneable {
            public OpId rect;

            public MouseUp(OpId _rect) {
                if (_rect == null) throw new ArgumentNullException(nameof(_rect));
                rect = _rect;
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(1);
                rect.Serialize(serializer);
                serializer.decrease_container_depth();
            }

            internal static MouseUp Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                MouseUp obj = new MouseUp(
                	OpId.Deserialize(deserializer));
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is MouseUp other && Equals(other);

            public static bool operator ==(MouseUp left, MouseUp right) => Equals(left, right);

            public static bool operator !=(MouseUp left, MouseUp right) => !Equals(left, right);

            public bool Equals(MouseUp other) {
                if (other == null) return false;
                if (ReferenceEquals(this, other)) return true;
                if (!rect.Equals(other.rect)) return false;
                return true;
            }

            public override int GetHashCode() {
                unchecked {
                    int value = 7;
                    value = 31 * value + rect.GetHashCode();
                    return value;
                }
            }

        }
    }


} // end of namespace _boldui_protocol
