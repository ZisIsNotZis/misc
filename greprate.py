#!/bin/env python
from sys import argv
from re import compile, IGNORECASE
from multiprocessing import Pool
import numpy as np
def f(f): return len(re.findall(f := open(f).read()))/len(f)


re = compile(argv[1], IGNORECASE)
argv = np.array(argv, 'O')[2:]
print(*argv[np.array(Pool().map(f, argv), 'f').argsort()[-200:]], sep='\n')
