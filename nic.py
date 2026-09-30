import time
# import numpy as np
i = 0
while 1:
    i, j = [(i[0], [int(i[j])for j in (2, 3, 10, 11)])for i in open('/proc/net/dev').readlines()[2:]for i in [i.split()]], i
    if j:
        print([(i[0], [i-j for i, j in zip(i[1], j[1])])for i, j in zip(i, j)])
#     i,j = np.loadtxt('/proc/net/dev',int,skiprows=2,usecols=(2,3,10,11)),i
#     print(i-j)
    time.sleep(1)
