"""Read IGOR Packed Experiment files into records."""
import logging

from .struct import Structure as _Structure
from .struct import Field as _Field
from .util import byte_order as _byte_order
from .util import need_to_reorder_bytes as _need_to_reorder_bytes
from .util import _bytes
from .record import RECORD_TYPE as _RECORD_TYPE
from .record.base import UnknownRecord as _UnknownRecord
from .record.base import UnusedRecord as _UnusedRecord
from .record.folder import FolderStartRecord as _FolderStartRecord
from .record.folder import FolderEndRecord as _FolderEndRecord
from .record.variables import VariablesRecord as _VariablesRecord
from .record.wave import WaveRecord as _WaveRecord


logger = logging.getLogger(__name__)

# From PTN003:
# Igor writes other kinds of records in a packed experiment file, for
# storing things like pictures, page setup records, and miscellaneous
# settings.  The format for these records is quite complex and is not
# described in PTN003.  If you are writing a program to read packed
# files, you must skip any record with a record type that is not
# listed above.

# CR_STR = '\x15'  (\r)

PACKEDRECTYPE_MASK = 0x7FFF  # Record type = (recordType & PACKEDREC_TYPE_MASK)
SUPERCEDED_MASK = 0x8000  # Bit is set if the record is superceded by
# a later record in the packed file.


def setup_packed_file_record_header(byte_order='@'):
    record_header = _Structure(
        name='PackedFileRecordHeader',
        fields=[
            _Field('H', 'recordType',
                   help='Record type plus superceded flag.'),
            _Field('h', 'version',
                   help='Version information depends on the type of record.'),
            _Field('l', 'numDataBytes',
                   help='Number of data bytes in the record following this'
                   'record header.'),
        ],
        byte_order=byte_order)
    record_header.setup()
    return record_header


def load(filename, strict=True, ignore_unknown=True, initial_byte_order=None):
    """Load a packed experiment file.

    Parameters
    ----------
    filename : str or file-like object
        The path to the file or a file-like object representing the packed
        experiment file.
    strict : bool, optional
        This parameter is ignored. Defaults to True.
    ignore_unknown : bool, optional
        If True, ignore unknown record types. Defaults to True.
    initial_byte_order : str or None, optional
        The initial byte order to use for unpacking. Must be one of '>', '=',
        '<'. If None, '=' is used. Defaults to None.

    Returns
    -------
    records : list of Record
        The records in the packed experiment file.
    filesystem : dict
        The filesystem structure of the packed experiment file.
    """
    logger.debug('loading a packed experiment file from %s', filename)
    records = []
    if hasattr(filename, 'read'):
        f = filename  # filename is actually a stream object
    else:
        f = open(filename, 'rb')
    byte_order = None
    if initial_byte_order is None:
        initial_byte_order = '='
    try:
        while True:
            header_struct = setup_packed_file_record_header(
                byte_order=initial_byte_order)
            b = bytes(f.read(header_struct.size))
            if not b:
                break
            if len(b) < header_struct.size:
                raise ValueError(
                    ('not enough data for the next record header ({} < {})'
                     ).format(len(b), header_struct.size))
            logger.debug('reading a new packed experiment file record')
            header = header_struct.unpack_from(b)
            if header['version'] and not byte_order:
                need_to_reorder = _need_to_reorder_bytes(header['version'])
                byte_order = initial_byte_order = _byte_order(need_to_reorder)
                logger.debug(
                    'get byte order from version: %s (reorder? %s)',
                    byte_order, need_to_reorder)
                if need_to_reorder:
                    header_struct = setup_packed_file_record_header(
                        byte_order=byte_order)
                    header = header_struct.unpack_from(b)
                    logger.debug(
                        'reordered version: %s', header['version'])
            data = bytes(f.read(header['numDataBytes']))
            if len(data) < header['numDataBytes']:
                raise ValueError(
                    ('not enough data for the next record ({} < {}), '
                     'try loading with a different initial byte order'
                     ).format(len(b), header['numDataBytes']))
            record_type = _RECORD_TYPE.get(
                header['recordType'] & PACKEDRECTYPE_MASK, _UnknownRecord)
            logger.debug('the new record has type %s (%s).',
                         record_type, header['recordType'])
            if record_type in [_UnknownRecord, _UnusedRecord
                               ] and not ignore_unknown:
                raise KeyError('unkown record type {}'.format(
                    header['recordType']))
            records.append(record_type(header, data, byte_order=byte_order))
    finally:
        logger.debug('finished loading %s records from %s',
                     len(records), filename)
        if not hasattr(filename, 'read'):
            f.close()

    filesystem = _build_filesystem(records)

    return records, filesystem


def _build_filesystem(records):
    # From PTN003:
    """The name must be a valid Igor data folder name. See Object
    Names in the Igor Reference help file for name rules.

    When Igor Pro reads the data folder start record, it creates a new
    data folder with the specified name. Any subsequent variable, wave
    or data folder start records cause Igor to create data objects in
    this new data folder, until Igor Pro reads a corresponding data
    folder end record."""
    # From the Igor Manual, chapter 2, section 8, page II-123
    # http://www.wavemetrics.net/doc/igorman/II-08%20Data%20Folders.pdf
    """Like the Macintosh file system, Igor Pro's data folders use the
    colon character (:) to separate components of a path to an
    object. This is analogous to Unix which uses / and Windows which
    uses \\. (Reminder: Igor's data folders exist wholly in memory
    while an experiment is open. It is not a disk file system!)

    A data folder named "root" always exists and contains all other
    data folders.
    """
    # From the Igor Manual, chapter 4, page IV-2
    # http://www.wavemetrics.net/doc/igorman/IV-01%20Commands.pdf
    """For waves and data folders only, you can also use "liberal"
    names. Liberal names can include almost any character, including
    spaces and dots (see Liberal Object Names on page III-415 for
    details).
    """
    # From the Igor Manual, chapter 3, section 16, page III-416
    # http://www.wavemetrics.net/doc/igorman/III-16%20Miscellany.pdf
    """Liberal names have the same rules as standard names except you
    may use any character except control characters and the following:

      " ' : ;
    """
    filesystem = {'root': {}}
    dir_stack = [('root', filesystem['root'])]
    for record in records:
        cwd = dir_stack[-1][-1]
        if isinstance(record, _FolderStartRecord):
            name = record.null_terminated_text
            cwd[name] = {}
            dir_stack.append((name, cwd[name]))
        elif isinstance(record, _FolderEndRecord):
            dir_stack.pop()
        elif isinstance(record, (_VariablesRecord, _WaveRecord)):
            if isinstance(record, _VariablesRecord):
                sys_vars = record.variables['variables']['sysVars'].keys()
                for filename, value in record.namespace.items():
                    if len(dir_stack) > 1 and filename in sys_vars:
                        # From PTN003:
                        """When reading a packed file, any system
                        variables encountered while the current data
                        folder is not the root should be ignored.
                        """
                        continue
                    _check_filename(dir_stack, filename)
                    cwd[filename] = value
            else:  # WaveRecord
                filename = record.wave['wave']['wave_header']['bname']
                _check_filename(dir_stack, filename)
                cwd[filename] = record
    return filesystem


def _check_filename(dir_stack, filename):
    cwd = dir_stack[-1][-1]
    if filename in cwd:
        raise ValueError('collision on name {} in {}'.format(
            filename, ':'.join(d for d, cwd in dir_stack)))


def walk(filesystem, callback, dirpath=None):
    """Walk a packed experiment filesystem, operating on each key,value pair.
    """
    if dirpath is None:
        dirpath = []
    for key, value in sorted((_bytes(k), v) for k, v in filesystem.items()):
        callback(dirpath, key, value)
        if isinstance(value, dict):
            walk(filesystem=value, callback=callback, dirpath=dirpath + [key])
