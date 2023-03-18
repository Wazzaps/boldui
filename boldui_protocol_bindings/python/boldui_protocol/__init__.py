from ._boldui_protocol import *

R2A_MAGIC = b"BOLDUI\x00"
A2R_MAGIC = b"BOLDUI\x01"

LATEST_MAJOR_VER = 0
LATEST_MINOR_VER = 1

SceneId = st.uint32
NullOpId = OpId(st.uint32(0), st.uint32(0))
