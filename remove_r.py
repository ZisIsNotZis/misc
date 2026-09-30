from os import readv, writev
from time import sleep
raw = bytearray(1048576)
buf = memoryview(raw)
o = []
while J := readv(0, [raw]):
    I = 0
    while 0 <= (j := raw.find(13, I, J)) < J-1:
        if 0 <= (i := raw.rfind(10, I, j)):
            o.append(buf[I:i])
            if len(o) >= 1024:
                writev(1, o)
                o.clear()
        elif not I:
            o.append(b'\r')
        I = j+1
    if J > I:
        o.append(buf[I:J])
    writev(1, o)
    o.clear()
    sleep(1)
