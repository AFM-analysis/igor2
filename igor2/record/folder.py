import struct

from .base import TextRecord


class FolderStartRecord (TextRecord):
    pass


class FolderEndRecord (TextRecord):
    pass


class LongFolderStartRecord (FolderStartRecord):
    """Folder start used when the name does not fit in 31 bytes.

    Igor Pro 8 writes record type 101 instead of type 9. The payload
    is a uint32 byte count followed by exactly that many name bytes.
    A type 10 record closes the folder, as with a short name.
    """

    def __init__(self, *args, **kwargs):
        super(LongFolderStartRecord, self).__init__(*args, **kwargs)
        order = self.byte_order or '='
        data = bytes(self.data)
        if len(data) < 4:
            raise ValueError(
                'long folder name record is shorter than its length field')
        nlen = struct.unpack_from(order + 'I', data)[0]
        name = data[4:]
        if nlen != len(name):
            raise ValueError(
                'long folder name length {} does not match {} name bytes'
                .format(nlen, len(name)))
        # Keep the counted bytes. TextRecord would stop at the NUL that
        # sits inside the length field of every little-endian name.
        self.null_terminated_text = name
