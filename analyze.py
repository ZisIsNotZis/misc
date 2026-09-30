import numpy as np
a = np.loadtxt('out', 'S31,S7,B,B,3f', skiprows=1, delimiter=',')
f, f_ = np.unique(a['f0'], return_inverse=True)
dev, dev_ = np.unique(a['f1'], return_inverse=True)
ngl, ngl_ = np.unique(a['f2'], return_inverse=True)
opt, opt_ = np.unique(a['f3'], return_inverse=True)
A = np.full((len(f), len(dev), len(ngl), len(opt), 3), np.nan, 'f')
A[f_, dev_, ngl_, opt_] = a['f4']
