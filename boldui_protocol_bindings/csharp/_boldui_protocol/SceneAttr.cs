using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Numerics;

namespace _boldui_protocol {

    public abstract class SceneAttr: IEquatable<SceneAttr>, ICloneable {

        public abstract void Serialize(Serde.ISerializer serializer);

        public static SceneAttr Deserialize(Serde.IDeserializer deserializer) {
            int index = deserializer.deserialize_variant_index();
            switch (index) {
                case 0: return Transform.Load(deserializer);
                case 1: return Paint.Load(deserializer);
                case 2: return BackdropPaint.Load(deserializer);
                case 3: return Clip.Load(deserializer);
                case 4: return Uri.Load(deserializer);
                case 5: return Size.Load(deserializer);
                case 6: return WindowId.Load(deserializer);
                case 7: return WindowInitialPosition.Load(deserializer);
                case 8: return WindowInitialState.Load(deserializer);
                case 9: return WindowTitle.Load(deserializer);
                case 10: return WindowIcon.Load(deserializer);
                case 11: return WindowDecorations.Load(deserializer);
                default: throw new Serde.DeserializationException("Unknown variant index for SceneAttr: " + index);
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

        public static SceneAttr BincodeDeserialize(byte[] input) => BincodeDeserialize(new ArraySegment<byte>(input));

        public static SceneAttr BincodeDeserialize(ArraySegment<byte> input) {
            if (input == null) {
                 throw new Serde.DeserializationException("Cannot deserialize null array");
            }
            Serde.IDeserializer deserializer = new Bincode.BincodeDeserializer(input);
            SceneAttr value = Deserialize(deserializer);
            if (deserializer.get_buffer_offset() < input.Count) {
                 throw new Serde.DeserializationException("Some input bytes were not read");
            }
            return value;
        }
        public override int GetHashCode() {
            switch (this) {
            case Transform x: return x.GetHashCode();
            case Paint x: return x.GetHashCode();
            case BackdropPaint x: return x.GetHashCode();
            case Clip x: return x.GetHashCode();
            case Uri x: return x.GetHashCode();
            case Size x: return x.GetHashCode();
            case WindowId x: return x.GetHashCode();
            case WindowInitialPosition x: return x.GetHashCode();
            case WindowInitialState x: return x.GetHashCode();
            case WindowTitle x: return x.GetHashCode();
            case WindowIcon x: return x.GetHashCode();
            case WindowDecorations x: return x.GetHashCode();
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }
        public override bool Equals(object obj) => obj is SceneAttr other && Equals(other);

        public bool Equals(SceneAttr other) {
            if (other == null) return false;
            if (ReferenceEquals(this, other)) return true;
            if (GetType() != other.GetType()) return false;
            switch (this) {
            case Transform x: return x.Equals((Transform)other);
            case Paint x: return x.Equals((Paint)other);
            case BackdropPaint x: return x.Equals((BackdropPaint)other);
            case Clip x: return x.Equals((Clip)other);
            case Uri x: return x.Equals((Uri)other);
            case Size x: return x.Equals((Size)other);
            case WindowId x: return x.Equals((WindowId)other);
            case WindowInitialPosition x: return x.Equals((WindowInitialPosition)other);
            case WindowInitialState x: return x.Equals((WindowInitialState)other);
            case WindowTitle x: return x.Equals((WindowTitle)other);
            case WindowIcon x: return x.Equals((WindowIcon)other);
            case WindowDecorations x: return x.Equals((WindowDecorations)other);
            default: throw new InvalidOperationException("Unknown variant type");
            }
        }

        /// <summary>Creates a shallow clone of the object.</summary>
        public SceneAttr Clone() => (SceneAttr)MemberwiseClone();

        object ICloneable.Clone() => Clone();


        public sealed class Transform: SceneAttr, IEquatable<Transform>, ICloneable {
            public Transform() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(0);
                serializer.decrease_container_depth();
            }

            internal static Transform Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Transform obj = new Transform(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Transform other && Equals(other);

            public static bool operator ==(Transform left, Transform right) => Equals(left, right);

            public static bool operator !=(Transform left, Transform right) => !Equals(left, right);

            public bool Equals(Transform other) {
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

        public sealed class Paint: SceneAttr, IEquatable<Paint>, ICloneable {
            public Paint() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(1);
                serializer.decrease_container_depth();
            }

            internal static Paint Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Paint obj = new Paint(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Paint other && Equals(other);

            public static bool operator ==(Paint left, Paint right) => Equals(left, right);

            public static bool operator !=(Paint left, Paint right) => !Equals(left, right);

            public bool Equals(Paint other) {
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

        public sealed class BackdropPaint: SceneAttr, IEquatable<BackdropPaint>, ICloneable {
            public BackdropPaint() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(2);
                serializer.decrease_container_depth();
            }

            internal static BackdropPaint Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                BackdropPaint obj = new BackdropPaint(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is BackdropPaint other && Equals(other);

            public static bool operator ==(BackdropPaint left, BackdropPaint right) => Equals(left, right);

            public static bool operator !=(BackdropPaint left, BackdropPaint right) => !Equals(left, right);

            public bool Equals(BackdropPaint other) {
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

        public sealed class Clip: SceneAttr, IEquatable<Clip>, ICloneable {
            public Clip() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(3);
                serializer.decrease_container_depth();
            }

            internal static Clip Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Clip obj = new Clip(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Clip other && Equals(other);

            public static bool operator ==(Clip left, Clip right) => Equals(left, right);

            public static bool operator !=(Clip left, Clip right) => !Equals(left, right);

            public bool Equals(Clip other) {
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

        public sealed class Uri: SceneAttr, IEquatable<Uri>, ICloneable {
            public Uri() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(4);
                serializer.decrease_container_depth();
            }

            internal static Uri Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Uri obj = new Uri(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Uri other && Equals(other);

            public static bool operator ==(Uri left, Uri right) => Equals(left, right);

            public static bool operator !=(Uri left, Uri right) => !Equals(left, right);

            public bool Equals(Uri other) {
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

        public sealed class Size: SceneAttr, IEquatable<Size>, ICloneable {
            public Size() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(5);
                serializer.decrease_container_depth();
            }

            internal static Size Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                Size obj = new Size(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is Size other && Equals(other);

            public static bool operator ==(Size left, Size right) => Equals(left, right);

            public static bool operator !=(Size left, Size right) => !Equals(left, right);

            public bool Equals(Size other) {
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

        public sealed class WindowId: SceneAttr, IEquatable<WindowId>, ICloneable {
            public WindowId() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(6);
                serializer.decrease_container_depth();
            }

            internal static WindowId Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                WindowId obj = new WindowId(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is WindowId other && Equals(other);

            public static bool operator ==(WindowId left, WindowId right) => Equals(left, right);

            public static bool operator !=(WindowId left, WindowId right) => !Equals(left, right);

            public bool Equals(WindowId other) {
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

        public sealed class WindowInitialPosition: SceneAttr, IEquatable<WindowInitialPosition>, ICloneable {
            public WindowInitialPosition() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(7);
                serializer.decrease_container_depth();
            }

            internal static WindowInitialPosition Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                WindowInitialPosition obj = new WindowInitialPosition(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is WindowInitialPosition other && Equals(other);

            public static bool operator ==(WindowInitialPosition left, WindowInitialPosition right) => Equals(left, right);

            public static bool operator !=(WindowInitialPosition left, WindowInitialPosition right) => !Equals(left, right);

            public bool Equals(WindowInitialPosition other) {
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

        public sealed class WindowInitialState: SceneAttr, IEquatable<WindowInitialState>, ICloneable {
            public WindowInitialState() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(8);
                serializer.decrease_container_depth();
            }

            internal static WindowInitialState Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                WindowInitialState obj = new WindowInitialState(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is WindowInitialState other && Equals(other);

            public static bool operator ==(WindowInitialState left, WindowInitialState right) => Equals(left, right);

            public static bool operator !=(WindowInitialState left, WindowInitialState right) => !Equals(left, right);

            public bool Equals(WindowInitialState other) {
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

        public sealed class WindowTitle: SceneAttr, IEquatable<WindowTitle>, ICloneable {
            public WindowTitle() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(9);
                serializer.decrease_container_depth();
            }

            internal static WindowTitle Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                WindowTitle obj = new WindowTitle(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is WindowTitle other && Equals(other);

            public static bool operator ==(WindowTitle left, WindowTitle right) => Equals(left, right);

            public static bool operator !=(WindowTitle left, WindowTitle right) => !Equals(left, right);

            public bool Equals(WindowTitle other) {
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

        public sealed class WindowIcon: SceneAttr, IEquatable<WindowIcon>, ICloneable {
            public WindowIcon() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(10);
                serializer.decrease_container_depth();
            }

            internal static WindowIcon Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                WindowIcon obj = new WindowIcon(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is WindowIcon other && Equals(other);

            public static bool operator ==(WindowIcon left, WindowIcon right) => Equals(left, right);

            public static bool operator !=(WindowIcon left, WindowIcon right) => !Equals(left, right);

            public bool Equals(WindowIcon other) {
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

        public sealed class WindowDecorations: SceneAttr, IEquatable<WindowDecorations>, ICloneable {
            public WindowDecorations() {
            }

            public override void Serialize(Serde.ISerializer serializer) {
                serializer.increase_container_depth();
                serializer.serialize_variant_index(11);
                serializer.decrease_container_depth();
            }

            internal static WindowDecorations Load(Serde.IDeserializer deserializer) {
                deserializer.increase_container_depth();
                WindowDecorations obj = new WindowDecorations(
                	);
                deserializer.decrease_container_depth();
                return obj;
            }
            public override bool Equals(object obj) => obj is WindowDecorations other && Equals(other);

            public static bool operator ==(WindowDecorations left, WindowDecorations right) => Equals(left, right);

            public static bool operator !=(WindowDecorations left, WindowDecorations right) => !Equals(left, right);

            public bool Equals(WindowDecorations other) {
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
    }


} // end of namespace _boldui_protocol
