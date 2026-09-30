#!/bin/bash
# gcc/clang require o3 no-finite-math-only
# icc doesn't support cflag/cxxflag/o3 lto
# nvcc doesn't support cxxflag/o3 fast arch lto
CC=gcc
CX=g++
BLAS=Generic
f(){
	if ! [ -a $CC$BLAS$EX/bin/llama-bench ];then
		rm -rf $CC$BLAS$EX
		cmake -B$CC$BLAS$EX -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=$CC -DCMAKE_CXX_COMPILER=${CX:-g++} -DCMAKE_C_FLAGS="-Ofast -march=native" -DCMAKE_CXX_FLAGS="-Ofast -march=native" -DCMAKE_SYCL_FLAGS="-Ofast -march=native -flto=auto" -DCMAKE_CUDA_FLAGS="-Ofast -march=native -flto=auto" -DCMAKE_CUDA_ARCHITECTURES=89 -DBUILD_SHARED_LIBS=ON -DGGML_BACKEND_DL=ON `for _ in $@;do echo -DGGML_$_=ON;done` -DGGML_BLAS_VENDOR=$BLAS -DLLAMA_CURL=OFF
		find $CC$BLAS$EX -type f -print0|xargs -0 sed -i "s/-O[0-2]/-O3 -march=native -flto=auto/g;s/-O3/-Ofast -march=native -fno-finite-math-only/g"
	fi
	cmake --build $CC$BLAS$EX --config Release -- -j28 llama-cli llama-mtmd-cli llama-bench
}
set -ex
f CPU_ALL_VARIANTS BLAS VULKAN
BLAS=OpenBLAS f CPU_ALL_VARIANTS BLAS VULKAN
BLAS=FLAME f CPU_ALL_VARIANTS BLAS VULKAN
BLAS=Intel10_64lp f CPU_ALL_VARIANTS BLAS VULKAN
CC=clang CX=clang++ f CPU_ALL_VARIANTS BLAS VULKAN
CC=clang CX=clang++ BLAS=OpenBLAS f CPU_ALL_VARIANTS BLAS VULKAN
CC=clang CX=clang++ BLAS=FLAME f CPU_ALL_VARIANTS BLAS VULKAN
CC=clang CX=clang++  BLAS=Intel10_64lp f CPU_ALL_VARIANTS BLAS VULKAN
CC=icx CX=icpx f CPU_ALL_VARIANTS BLAS VULKAN SYCL
CC=icx CX=icpx EX=F16 f CPU_ALL_VARIANTS BLAS VULKAN SYCL SYCL_F16
CC=icx CX=icpx BLAS=OpenBLAS f CPU_ALL_VARIANTS BLAS VULKAN SYCL
CC=icx CX=icpx BLAS=OpenBLAS EX=F16 f CPU_ALL_VARIANTS BLAS VULKAN SYCL SYCL_F16
CC=icx CX=icpx BLAS=FLAME f CPU_ALL_VARIANTS BLAS VULKAN SYCL
CC=icx CX=icpx BLAS=FLAME EX=F16 f CPU_ALL_VARIANTS BLAS VULKAN SYCL SYCL_F16
CC=icx CX=icpx BLAS=Intel10_64lp f CPU_ALL_VARIANTS BLAS VULKAN SYCL
CC=icx CX=icpx BLAS=Intel10_64lp EX=F16 f CPU_ALL_VARIANTS BLAS VULKAN SYCL SYCL_F16

# cmake -Bgcpu -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_CXX_FLAGS='-Ofast -march=native -flto=auto' -DCMAKE_C_FLAGS='-Ofast -march=native -flto=auto' -D{GGML,SD,WHISPER,BARK,ENCODEC}_NATIVE=ON -DGGML_BLAS_VENDOR=OpenBLAS
# find gcpu -type f|xargs sed -i 's/-O[012]/-Ofast -march=native -flto=auto -s/g'
# find gcpu -type f|xargs sed -i 's/-O3/-Ofast -march=native -flto=auto -fno-finite-math-only/g'
# cmake --build gcpu --config Release -- -j24 llama-cli #llama-server llama-imatrix llama-quantize llama-quantize-stats llama-perplexity llama-bench llama-batched-bench whisper-bench whisper-cli whisper-server

# cmake -Bgcblas -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_CXX_FLAGS='-Ofast -march=native -flto=auto' -DCMAKE_C_FLAGS='-Ofast -march=native -flto=auto' -D{GGML,SD,WHISPER,BARK,ENCODEC}_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS
# find gcblas -type f|xargs sed -i 's/-O[012]/-Ofast -march=native -flto=auto -s/g'
# find gcblas -type f|xargs sed -i 's/-O3/-Ofast -march=native -flto=auto -fno-finite-math-only/g'
# cmake --build gcblas --config Release -- -j24 llama-cli #llama-server llama-imatrix llama-quantize llama-quantize-stats llama-perplexity llama-bench llama-batched-bench whisper-bench whisper-cli whisper-server

# cmake -Bicpu -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_CXX_FLAGS='-Ofast -march=native' -DCMAKE_C_FLAGS='-Ofast -march=native' -D{GGML,SD,WHISPER,BARK,ENCODEC}_NATIVE=ON -DGGML_BLAS_VENDOR=Intel10_64lp -DCMAKE_SYCL_FLAGS='-Ofast -march=native -fno-finite-math-only' -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx -DGGML_SYCL_F16=ON
# find icpu -type f|xargs sed -i 's/-O[012]/-Ofast -march=native -s/g'
# find icpu -type f|xargs sed -i 's/-O3/-Ofast -march=native -fno-finite-math-only/g'
# cmake --build icpu --config Release -- -j24 llama-cli #llama-server llama-imatrix llama-quantize llama-quantize-stats llama-perplexity llama-bench llama-batched-bench whisper-bench whisper-cli whisper-server

# cmake -Bicblas -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_CXX_FLAGS='-Ofast -march=native' -DCMAKE_C_FLAGS='-Ofast -march=native' -D{GGML,SD,WHISPER,BARK,ENCODEC}_BLAS=ON -DGGML_BLAS_VENDOR=Intel10_64lp -DCMAKE_SYCL_FLAGS='-Ofast -march=native -fno-finite-math-only' -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx -DGGML_SYCL_F16=ON
# find icblas -type f|xargs sed -i 's/-O[012]/-Ofast -march=native -s/g'
# find icblas -type f|xargs sed -i 's/-O3/-Ofast -march=native -fno-finite-math-only/g'
# cmake --build icblas --config Release -- -j24 llama-cli #llama-server llama-imatrix llama-quantize llama-quantize-stats llama-perplexity llama-bench llama-batched-bench whisper-bench whisper-cli whisper-server

# cmake -Bicsycl -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_CXX_FLAGS='-Ofast -march=native' -DCMAKE_C_FLAGS='-Ofast -march=native' -D{GGML,SD,WHISPER,BARK,ENCODEC}_SYCL=ON -DGGML_BLAS_VENDOR=Intel10_64lp -DCMAKE_SYCL_FLAGS='-Ofast -march=native -fno-finite-math-only' -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx -DGGML_SYCL_F16=ON
# find icsycl -type f|xargs sed -i 's/-O[012]/-Ofast -march=native -s/g'
# find icsycl -type f|xargs sed -i 's/-O3/-Ofast -march=native -fno-finite-math-only/g'
# cmake --build icsycl --config Release -- -j24 llama-cli #llama-server llama-imatrix llama-quantize llama-quantize-stats llama-perplexity llama-bench llama-batched-bench whisper-bench whisper-cli whisper-server

# cmake -Bccsycl -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_CXX_FLAGS='-Ofast -march=native' -DCMAKE_C_FLAGS='-Ofast -march=native' -D{GGML,SD,WHISPER,BARK,ENCODEC}_SYCL=ON -DGGML_BLAS_VENDOR=Intel10_64lp -DCMAKE_SYCL_FLAGS='-Ofast -march=native -fno-finite-math-only' -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DGGML_SYCL_F16=ON
# find ccsycl -type f|xargs sed -i 's/-O[012]/-Ofast -march=native -s/g'
# find ccsycl -type f|xargs sed -i 's/-O3/-Ofast -march=native -fno-finite-math-only/g'
# cmake --build ccsycl --config Release -- -j24 llama-cli #llama-server llama-imatrix llama-quantize llama-quantize-stats llama-perplexity llama-bench llama-batched-bench whisper-bench whisper-cli whisper-server

# cmake -Bnvcuda -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_CXX_FLAGS='-Ofast -march=native -flto=auto' -DCMAKE_C_FLAGS='-Ofast -march=native -flto=auto' -D{GGML,SD,WHISPER,BARK,ENCODEC}_CUDA=ON -DGGML_BLAS_VENDOR=OpenBLAS -DCMAKE_CUDA_FLAGS='-O3' -D{CMAKE_,}CUDA_ARCHITECTURES=89
# find nvcuda -type f|xargs sed -i 's/-O[012]/-Ofast -march=native -flto=auto -s/g'
# find nvcuda -type f|xargs sed -i 's/-O3/-O3 -s/g'
# cmake --build nvcuda --config Release -- -j24 llama-cli #llama-server llama-imatrix llama-quantize llama-quantize-stats llama-perplexity llama-bench llama-batched-bench whisper-bench whisper-cli whisper-server

# cmake -Bnvblascuda -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_CXX_FLAGS='-Ofast -march=native -flto=auto' -DCMAKE_C_FLAGS='-Ofast -march=native -flto=auto' -D{GGML,SD,WHISPER,BARK,ENCODEC}_{BLAS,CUDA}=ON -DGGML_BLAS_VENDOR=OpenBLAS -DCMAKE_CUDA_FLAGS='-O3' -D{CMAKE_,}CUDA_ARCHITECTURES=89
# find nvblascuda -type f|xargs sed -i 's/-O[012]/-Ofast -march=native -flto=auto -s/g'
# find nvblascuda -type f|xargs sed -i 's/-O3/-O3 -s/g'
# cmake --build nvblascuda --config Release -- -j24 llama-cli #llama-server llama-imatrix llama-quantize llama-quantize-stats llama-perplexity llama-bench llama-batched-bench whisper-bench whisper-cli whisper-server

# cmake -Bnvcudablas -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_CXX_FLAGS='-Ofast -march=native -flto=auto' -DCMAKE_C_FLAGS='-Ofast -march=native -flto=auto' -D{GGML,SD,BARK,ENCODEC}_{CUDA,CUBLAS}=ON -DWHISPER_CUDA=ON -DGGML_BLAS_VENDOR=OpenBLAS -DCMAKE_CUDA_FLAGS='-O3' -D{CMAKE_,}CUDA_ARCHITECTURES=89
# find nvcudablas -type f|xargs sed -i 's/-O[012]/-Ofast -march=native -flto=auto -s/g'
# find nvcudablas -type f|xargs sed -i 's/-O3/-O3 -s/g'
# cmake --build nvcudablas --config Release -- -j24 llama-cli #llama-server llama-imatrix llama-quantize llama-quantize-stats llama-perplexity llama-bench llama-batched-bench whisper-bench whisper-cli whisper-server

# cmake -Bnvblascudablas -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_CXX_FLAGS='-Ofast -march=native -flto=auto' -DCMAKE_C_FLAGS='-Ofast -march=native -flto=auto' -D{GGML,SD,BARK,ENCODEC}_{BLAS,CUDA,CUBLAS}=ON -DWHISPER_{BLAS,CUDA}=ON -DGGML_BLAS_VENDOR=OpenBLAS -DCMAKE_CUDA_FLAGS='-O3' -D{CMAKE_,}CUDA_ARCHITECTURES=89
# find nvblascudablas -type f|xargs sed -i 's/-O[012]/-Ofast -march=native -flto=auto -s/g'
# find nvblascudablas -type f|xargs sed -i 's/-O3/-O3 -s/g'
# cmake --build nvblascudablas --config Release -- -j24 llama-cli #llama-server llama-imatrix llama-quantize llama-quantize-stats llama-perplexity llama-bench llama-batched-bench whisper-bench whisper-cli whisper-server

# cmake -Bnvcpu -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_CXX_FLAGS='-Ofast -march=native -flto=auto' -DCMAKE_C_FLAGS='-Ofast -march=native -flto=auto' -D{GGML,SD,BARK,ENCODEC}_NATIVE=ON -DWHISPER_NATIVE=ON -DGGML_BLAS_VENDOR=OpenBLAS -DCMAKE_CUDA_FLAGS='-O3' -D{CMAKE_,}CUDA_ARCHITECTURES=89
# find nvcpu -type f|xargs sed -i 's/-O[012]/-Ofast -march=native -flto=auto -s/g'
# find nvcpu -type f|xargs sed -i 's/-O3/-O3 -s/g'
# cmake --build nvcpu --config Release -- -j24 llama-cli #llama-server llama-imatrix llama-quantize llama-quantize-stats llama-perplexity llama-bench llama-batched-bench whisper-bench whisper-cli whisper-server

# cmake -Bnvcblas -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_CXX_FLAGS='-Ofast -march=native -flto=auto' -DCMAKE_C_FLAGS='-Ofast -march=native -flto=auto' -D{GGML,SD,BARK,ENCODEC}_BLAS=ON -DWHISPER_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS -DCMAKE_CUDA_FLAGS='-O3' -D{CMAKE_,}CUDA_ARCHITECTURES=89
# find nvcblas -type f|xargs sed -i 's/-O[012]/-Ofast -march=native -flto=auto -s/g'
# find nvcblas -type f|xargs sed -i 's/-O3/-O3 -s/g'
# cmake --build nvcblas --config Release -- -j24 llama-cli #llama-server llama-imatrix llama-quantize llama-quantize-stats llama-perplexity llama-bench llama-batched-bench whisper-bench whisper-cli whisper-server

# cmake -Bnvcublas -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_CXX_FLAGS='-Ofast -march=native -flto=auto' -DCMAKE_C_FLAGS='-Ofast -march=native -flto=auto' -D{GGML,SD,BARK,ENCODEC}_CUBLAS=ON -DWHISPER_CUDA=ON -DGGML_BLAS_VENDOR=OpenBLAS -DCMAKE_CUDA_FLAGS='-O3' -D{CMAKE_,}CUDA_ARCHITECTURES=89
# find nvcublas -type f|xargs sed -i 's/-O[012]/-Ofast -march=native -flto=auto -s/g'
# find nvcublas -type f|xargs sed -i 's/-O3/-O3 -s/g'
# cmake --build nvcublas --config Release -- -j24 llama-cli #llama-server llama-imatrix llama-quantize llama-quantize-stats llama-perplexity llama-bench llama-batched-bench whisper-bench whisper-cli whisper-server