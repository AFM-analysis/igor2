#!/usr/bin/env python
"""IBW -> ASCII conversion"""

import pprint

import numpy

from igor2.binarywave import load
from igor2.script import Script


class WaveScript (Script):
    def _run(self, args):
        wave = load(args.infile)
        numpy.savetxt(
            args.outfile, wave['wave']['wData'], fmt='%g', delimiter='\t')
        self.plot_wave(args, wave)
        if args.verbose > 0:
            wave['wave'].pop('wData')
            pprint.pprint(wave)


s = WaveScript(description=__doc__)
s.run()
