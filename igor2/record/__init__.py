# flake8: noqa: F401
"""Record parsers for IGOR's packed experiment files."""
from .base import Record, UnknownRecord, UnusedRecord
from .variables import VariablesRecord
from .history import HistoryRecord, RecreationRecord, GetHistoryRecord
from .wave import WaveRecord
from .procedure import ProcedureRecord
from .packedfile import PackedFileRecord
from .folder import FolderStartRecord, FolderEndRecord, LongFolderStartRecord


# From PackedFile.h
RECORD_TYPE = {
    0: UnusedRecord,
    1: VariablesRecord,
    2: HistoryRecord,
    3: WaveRecord,
    4: RecreationRecord,
    5: ProcedureRecord,
    6: UnusedRecord,
    7: GetHistoryRecord,
    8: PackedFileRecord,
    9: FolderStartRecord,
    10: FolderEndRecord,
    # Igor Pro 8 uses 101 when a folder name does not fit in 31 bytes.
    101: LongFolderStartRecord,
}
