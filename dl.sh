#!/bin/bash
#diff <(grep -o 'load \S*' dl.sh|cut -c6-|sort) <(ls hub|grep ^model|cut -c9-|sed s@--@/@|sort)|grep \>
{ #r1 qwen
huggingface-cli download deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B
huggingface-cli download deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
huggingface-cli download deepseek-ai/DeepSeek-R1-Distill-Llama-8B
huggingface-cli download deepseek-ai/DeepSeek-R1-Distill-Qwen-14B
huggingface-cli download deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
# huggingface-cli download deepseek-ai/DeepSeek-R1-Distill-Llama-70B
huggingface-cli download casperhansen/deepseek-r1-distill-qwen-1.5b-awq
huggingface-cli download casperhansen/deepseek-r1-distill-qwen-7b-awq
huggingface-cli download casperhansen/deepseek-r1-distill-llama-8b-awq
huggingface-cli download casperhansen/deepseek-r1-distill-qwen-14b-awq
huggingface-cli download casperhansen/deepseek-r1-distill-qwen-32b-awq
# huggingface-cli download casperhansen/deepseek-r1-distill-llama-70b-awq
#r1 qwen GGUF
# huggingface-cli download unsloth/DeepSeek-R1-Distill-Qwen-32B-GGUF
#r1 GGUF
# huggingface-cli download unsloth/DeepSeek-R1-GGUF DeepSeek-R1-UD-IQ1_S
#r1 align
#r1 fuse GGUF
# huggingface-cli download bartowski/FuseO1-DeekSeekR1-QwQ-SkyT1-32B-Preview-GGUF
#v3 GGUF
# huggingface-cli download unsloth/DeepSeek-V3-GGUF DeepSeek-V3-Q2_K_XS
#vl2
#janus
# huggingface-cli download deepseek-ai/Janus-Pro-1B
# huggingface-cli download deepseek-ai/Janus-Pro-7B
}&

{ #qwen2.5
huggingface-cli download Qwen/Qwen2.5-0.5B-Instruct
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct
huggingface-cli download Qwen/Qwen2.5-3B-Instruct
huggingface-cli download Qwen/Qwen2.5-7B-Instruct
huggingface-cli download Qwen/Qwen2.5-14B-Instruct
huggingface-cli download Qwen/Qwen2.5-32B-Instruct
# huggingface-cli download Qwen/Qwen2.5-72B-Instruct
huggingface-cli download Qwen/Qwen2.5-0.5B-Instruct-AWQ
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct-AWQ
huggingface-cli download Qwen/Qwen2.5-3B-Instruct-AWQ
huggingface-cli download Qwen/Qwen2.5-7B-Instruct-AWQ
huggingface-cli download Qwen/Qwen2.5-14B-Instruct-AWQ
huggingface-cli download Qwen/Qwen2.5-32B-Instruct-AWQ
# huggingface-cli download Qwen/Qwen2.5-72B-Instruct-AWQ
#qwen2.5 1m
huggingface-cli download Qwen/Qwen2.5-7B-Instruct-1M
huggingface-cli download Qwen/Qwen2.5-14B-Instruct-1M
huggingface-cli download graelo/Qwen2.5-7B-Instruct-1M-AWQ
huggingface-cli download graelo/Qwen2.5-14B-Instruct-1M-AWQ
#qwen2.5 code
huggingface-cli download Qwen/Qwen2.5-Coder-0.5B-Instruct
huggingface-cli download Qwen/Qwen2.5-Coder-1.5B-Instruct
huggingface-cli download Qwen/Qwen2.5-Coder-3B-Instruct
huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct
huggingface-cli download Qwen/Qwen2.5-Coder-14B-Instruct
huggingface-cli download Qwen/Qwen2.5-Coder-32B-Instruct
huggingface-cli download Qwen/Qwen2.5-Coder-0.5B-Instruct-AWQ
huggingface-cli download Qwen/Qwen2.5-Coder-1.5B-Instruct-AWQ
huggingface-cli download Qwen/Qwen2.5-Coder-3B-Instruct-AWQ
huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct-AWQ
huggingface-cli download Qwen/Qwen2.5-Coder-14B-Instruct-AWQ
huggingface-cli download Qwen/Qwen2.5-Coder-32B-Instruct-AWQ
#qwen2.5 vl
huggingface-cli download Qwen/Qwen2.5-VL-3B-Instruct
huggingface-cli download Qwen/Qwen2.5-VL-7B-Instruct
huggingface-cli download Qwen/Qwen2.5-VL-3B-Instruct-AWQ
huggingface-cli download Qwen/Qwen2.5-VL-7B-Instruct-AWQ
#qwen2 audio
# huggingface-cli download Qwen/Qwen2-Audio-7B-Instruct
#qwq GGUF
# huggingface-cli download bartowski/QwQ-32B-Preview-GGUF
#qvq GGUF
# huggingface-cli download bartowski/QVQ-72B-Preview-GGUF
}&

# { #sd GGUF
# huggingface-cli download stduhpf/SD3.5-Large-GGUF-mixed-sdcpp legacy/sd3.5_large-iq4_nl.gguf
# huggingface-cli download stduhpf/SD3.5-Large-Turbo-GGUF-mixed-sdcpp legacy/sd3.5_large_turbo-iq4_nl.gguf
# huggingface-cli download comfyanonymous/flux_text_encoders clip_l.safetensors t5xxl_fp16.safetensors
# huggingface-cli download black-forest-labs/FLUX.1-dev ae.safetensors
# }&

# { #flux GGUF
# huggingface-cli download leejet/FLUX.1-dev-gguf flux1-dev-q4_k.gguf
# huggingface-cli download leejet/FLUX.1-schnell-gguf flux1-schnell-q4_k.gguf
# }&

# { #whisper GGUF
# huggingface-cli download ggerganov/whisper.cpp ggml-tiny-q5_1.bin ggml-base-q5_1.bin ggml-small-q5_1.bin ggml-medium-q5_0.bin ggml-large-v3-q5_0.bin ggml-large-v3-turbo-q5_0.bin
# }&

# { #bark
# huggingface-cli download suno/bark-small --include \*.bin \*.json \*.txt
# huggingface-cli download suno/bark --include \*.bin \*.json \*.txt
# }&

wait
