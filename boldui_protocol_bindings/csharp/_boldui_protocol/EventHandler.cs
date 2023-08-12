using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public sealed class EventHandler: IEquatable<EventHandler>, ICloneable {
        public EventType event_type;
        public HandlerBlock handler;
        public OpId continue_handling;

        public EventHandler(EventType _event_type, HandlerBlock _handler, OpId _continue_handling) {
            if (_event_type == null) throw new ArgumentNullException(nameof(_event_type));
            event_type = _event_type;
            if (_handler == null) throw new ArgumentNullException(nameof(_handler));
            handler = _handler;
            if (_continue_handling == null) throw new ArgumentNullException(nameof(_continue_handling));
            continue_handling = _continue_handling;
        }

        public void Serialize(Serde.ISerializer serializer) {
            serializer.increase_container_depth();
            event_type.Serialize(serializer);
            handler.Serialize(serializer);
            continue_handling.Serialize(serializer);
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

        public static EventHandler Deserialize(Serde.IDeserializer deserializer) {
            deserializer.increase_container_depth();
            EventHandler obj = new EventHandler(
            	EventType.Deserialize(deserializer),
            	HandlerBlock.Deserialize(deserializer),
            	OpId.Deserialize(deserializer));
            deserializer.decrease_container_depth();
            return obj;
        }

        public static EventHandler BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static EventHandler BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            EventHandler value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override bool Equals(object obj) => obj is EventHandler other && Equals(other);

        public static bool operator ==(EventHandler left, EventHandler right) => Equals(left, right);

        public static bool operator !=(EventHandler left, EventHandler right) => !Equals(left, right);

        public bool Equals(EventHandler other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (!event_type.Equals(other.event_type)) return false;
            if (!handler.Equals(other.handler)) return false;
            if (!continue_handling.Equals(other.continue_handling)) return false;
            return true;
        }

        public override int GetHashCode() {
            unchecked {
                int value = 7;
                value = 31 * value + event_type.GetHashCode();
                value = 31 * value + handler.GetHashCode();
                value = 31 * value + continue_handling.GetHashCode();
                return value;
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public EventHandler Clone() => (EventHandler)MemberwiseClone();

        object ICloneable.Clone() => Clone();

    }

} // end of namespace _boldui_protocol
