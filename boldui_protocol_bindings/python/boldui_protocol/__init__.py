from ._boldui_protocol import *

R2A_MAGIC = b"BOLDUI\x00"
A2R_MAGIC = b"BOLDUI\x01"
R2EA_MAGIC = b"BOLDUI\x02"
EA2R_MAGIC = b"BOLDUI\x03"

LATEST_MAJOR_VER = 0
LATEST_MINOR_VER = 1

LATEST_EA_MAJOR_VER = 0
LATEST_EA_MINOR_VER = 1

SceneId = st.uint32
ResourceId = st.uint32
NullOpId = OpId(st.uint32(0), st.uint32(0))
