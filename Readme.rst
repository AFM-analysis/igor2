Igor2
=====

|PyPI Version| |Build Status| |Coverage Status|


Python parser for Igor Binary Waves (``.ibw``) and Packed Experiment
(``.pxp``) files written by WaveMetrics' IGOR Pro software.

Igor2 is the continuation of the inactive
`igor <https://github.com/wking/igor>`_ project.


Installation
------------
You can install igor2 via pip::

    pip install igor2


Usage
-----
This package is a direct replacement of `igor`. Your scripts should work
without any issues if you replace::


    import igor

with::

    import igor2 as igor


Reading wave samples
~~~~~~~~~~~~~~~~~~~~

The examples below use files from ``tests/data`` in the source repository.
For a one-dimensional numeric wave in an IBW file, ``wData`` contains the
samples. Use the wave header to convert sample indices to axis coordinates::

    import numpy as np
    from igor2 import binarywave

    wave = binarywave.load("tests/data/win-version5.ibw")["wave"]
    samples = wave["wData"]
    header = wave["wave_header"]
    if "sfA" in header:
        step, offset = header["sfA"][0], header["sfB"][0]
    else:
        step, offset = header["hsA"], header["hsB"]
    x = offset + step * np.arange(samples.size)

A PXP file can contain multiple waves in different data folders. Collect
them by their full Igor paths, then select the wave you need::

    from igor2 import packed
    from igor2.record import WaveRecord

    _, filesystem = packed.load("tests/data/polar-graphs-demo.pxp")
    waves = {}

    def collect_wave(path, name, record):
        if isinstance(record, WaveRecord):
            waves[b":".join(path + [name])] = record.wave["wave"]["wData"]

    packed.walk(filesystem, collect_wave)
    print(sorted(waves))
    radius = waves[b"root:radiusData"]

For acquisition data, use the experiment's channel names and units to
identify recorded traces. Reconstructing a stimulus that was generated
but never saved as a wave requires the acquisition protocol.

CLI
---
The package also installs two command-line-interface (CLI) scripts,
``igorbinarywave`` and ``igorpackedexperiment`` which can be used to dump files
to stdout. You should install the ``[CLI]`` extra for them to fully work::

    pip install igor2[CLI]

For details on their usage, use the ``--help`` option.  For example::

    igorbinarywave --help


Testing
-------

Run internal unit tests by cloning the repository and installing the
``[dev]`` extra and then running the tests::

    git clone https://github.com/AFM-analysis/igor2.git
    cd igor2
    pip install -e .[dev]
    pytest


Licence
-------

This project is distributed under the `GNU Lesser General Public
License Version 3`_ or greater, see the ``LICENSE`` file distributed
with the project for details.


.. _GNU Lesser General Public License Version 3:
    http://www.gnu.org/licenses/lgpl.txt


.. |PyPI Version| image:: https://img.shields.io/pypi/v/igor2.svg
   :target: https://pypi.python.org/pypi/igor2
.. |Build Status| image:: https://img.shields.io/github/actions/workflow/status/AFM-analysis/igor2/check.yml?branch=master
   :target: https://github.com/AFM-analysis/igor2/actions?query=workflow%3AChecks
.. |Coverage Status| image:: https://img.shields.io/codecov/c/github/AFM-analysis/igor2/master.svg
   :target: https://codecov.io/gh/AFM-analysis/igor2
