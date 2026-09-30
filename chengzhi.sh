ssh -L8889:localhost:8888 -J<REDACTED:user>@<REDACTED:host>:<REDACTED:port> <REDACTED:user>@localhost -p<REDACTED:port>
jupyter-notebook &
ssh -NRlocalhost:8888:localhost:8888 <REDACTED:user>@<REDACTED:host> -p<REDACTED:port>