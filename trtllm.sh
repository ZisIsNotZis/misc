#!/bin/bash
# Set environment variables for the model parameters
export TRITON_MAX_BATCH_SIZE=16
export INSTANCE_COUNT=1
export MAX_QUEUE_DELAY_MS=5000000  # 5 seconds in microseconds
export MAX_QUEUE_SIZE=16            # Allow up to 8 requests to queue
export DECOUPLED_MODE=false
export LOGITS_DATATYPE=TYPE_FP16

docker run -d --net host --shm-size 200g --ulimit memlock=-1 --ulimit stack=67108864 --gpus all -w /app -v $(pwd)/hf/hub/models--Qwen--Qwen2.5-0.5B-Instruct:/app/a nvcr.io/nvidia/tritonserver:25.01-trtllm-python-py3 sh -c "
    # Convert the model checkpoint (using weight-only int4 precision)
    python3 examples/qwen/convert_checkpoint.py --model_dir a/snapshots/7ae557604adf67be50417f59c2c2f167def9a775 --dtype float16 --use_weight_only --weight_only_precision int4 --output_dir b &&

    # Build the TensorRT engine with detailed options
    trtllm-build --checkpoint_dir b --gpt_attention_plugin float16 --remove_input_padding enable --kv_cache_type paged --gemm_plugin float16 --output_dir c &&

    # Fill templates for the ensemble configuration
    python3 tools/fill_template.py -i /app/all_models/inflight_batcher_llm/ensemble/config.pbtxt triton_max_batch_size:$TRITON_MAX_BATCH_SIZE,logits_datatype:$LOGITS_DATATYPE &&

    # Preprocessing config
    python3 tools/fill_template.py -i /app/all_models/inflight_batcher_llm/preprocessing/config.pbtxt tokenizer_dir:a/snapshots/7ae557604adf67be50417f59c2c2f167def9a775,triton_max_batch_size:$TRITON_MAX_BATCH_SIZE,preprocessing_instance_count:$INSTANCE_COUNT &&

    # TensorRT LLM backend config with updated batching delay and queue size
    python3 tools/fill_template.py -i /app/all_models/inflight_batcher_llm/tensorrt_llm/config.pbtxt triton_backend:tensorrtllm,triton_max_batch_size:$TRITON_MAX_BATCH_SIZE,decoupled_mode:$DECOUPLED_MODE,engine_dir:c,max_queue_delay_microseconds:$MAX_QUEUE_DELAY_MS,batching_strategy:inflight_fused_batching,max_queue_size:$MAX_QUEUE_SIZE,encoder_input_features_data_type:TYPE_FP16,logits_datatype:$LOGITS_DATATYPE &&

    # Postprocessing config
    python3 tools/fill_template.py -i /app/all_models/inflight_batcher_llm/postprocessing/config.pbtxt tokenizer_dir:a/snapshots/7ae557604adf67be50417f59c2c2f167def9a775,triton_max_batch_size:$TRITON_MAX_BATCH_SIZE,postprocessing_instance_count:$INSTANCE_COUNT &&

    # BLS config
    python3 tools/fill_template.py -i /app/all_models/inflight_batcher_llm/tensorrt_llm_bls/config.pbtxt triton_max_batch_size:$TRITON_MAX_BATCH_SIZE,decoupled_mode:$DECOUPLED_MODE,bls_instance_count:$INSTANCE_COUNT,logits_datatype:$LOGITS_DATATYPE &&

    # Launch Triton Server with the model repository
    python3 scripts/launch_triton_server.py --model_repo=all_models/inflight_batcher_llm &&

    # Keep the container running
    sleep 99999
  "

# curl localhost:8000/v2/models/tensorrt_llm_bls/generate -d'{"text_input":"<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\n<|im_start|>user\nWrite a 100+ words story that mostly start with same letter. Remember, 100+ words.<|im_end|>\n<|im_start|>assistant\n","max_tokens":999, "stop_words":"<|im_end|>"}'

VLLM_ATTENTION_BACKEND=FLASHINFER _vlm/bin/vllm serve Qwen/Qwen2.5-0.5B-Instruct-GPTQ-Int4 --quantization gptq --kv-cache-dtype fp8_e5m2 --cpu-offload-gb 20 --preemption-mode swap --scheduler-delay-factor 5 --max-num-batched-tokens 4096 --enable-chunked-prefill --enable-prefix-caching --device cuda

VLLM_ATTENTION_BACKEND=FLASHINFER _vlm/bin/vllm serve Qwen/Qwen2.5-0.5B-Instruct-AWQ --quantization awq --kv-cache-dtype fp8_e5m2 --cpu-offload-gb 20 --preemption-mode swap --scheduler-delay-factor 5 --max-num-batched-tokens 4096 --enable-chunked-prefill --enable-prefix-caching --device cuda

VLLM_ATTENTION_BACKEND=FLASHINFER _vlm/bin/vllm serve hf/hub/models--unsloth--DeepSeek-R1-Distill-Qwen-7B-GGUF/snapshots/097680e4eed7a83b3df6b0bb5e5134099cadf1b0/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf --tokenizer Qwen/Qwen2.5-7B-Instruct --quantization gguf --kv-cache-dtype fp8_e5m2 --cpu-offload-gb 20 --preemption-mode swap --scheduler-delay-factor 5 --enable-chunked-prefill --enable-prefix-caching --device cuda

_vlm/bin/vllm serve hf/hub/models--Qwen--Qwen2.5-7B-Instruct-GGUF/snapshots/bb5d59e06d9551d752d08b292a50eb208b07ab1f/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf --tokenizer Qwen/Qwen2.5-7B-Instruct --quantization gguf --kv-cache-dtype fp8_e5m2 --cpu-offload-gb 20 --preemption-mode swap --scheduler-delay-factor 5 --max-num-batched-tokens 4096 --enable-chunked-prefill --enable-prefix-caching --device cuda

VLLM_ATTENTION_BACKEND=FLASHINFER _vlm/bin/vllm serve Qwen2.5-7B-Instruct-AWQ --kv-cache-dtype fp8_e5m2 --cpu-offload-gb 20 --preemption-mode swap --scheduler-delay-factor 5 --max-num-batched-tokens 4096 --enable-chunked-prefill --enable-prefix-caching --device cuda

curl -s <REDACTED:host-ip>:8000/v1/chat/completions -HContent-Type:application/json -d'{"model":"'`curl -s localhost:8000/v1/models|jq -r .data[0].id`'","messages":[{"role":"system","content":"Prove 1+1=2."}],"temperature":0.7,"top_p":0.8,"repetition_penalty":1.05,"max_tokens":999}'|jq -r .choices[0].message.content

Namespace( model_tag='Qwen/Qwen2.5-7B-Instruct-AWQ', config='', host=None, port=8000, uvicorn_log_level='info', allow_credentials=False, allowed_origins=['*'], allowed_methods=['*'], allowed_headers=['*'], api_key=None, lora_modules=None, prompt_adapters=None, chat_template=None, chat_template_content_format='auto', response_role='assistant', ssl_keyfile=None, ssl_certfile=None, ssl_ca_certs=None, ssl_cert_reqs=0, root_path=None, middleware=[], return_tokens_as_token_ids=False, disable_frontend_multiprocessing=False, enable_request_id_headers=False, enable_auto_tool_choice=False, enable_reasoning=False, reasoning_parser=None, tool_call_parser=None, tool_parser_plugin='', model='Qwen/Qwen2.5-7B-Instruct-AWQ', task='auto', tokenizer=None, skip_tokenizer_init=False, revision=None, code_revision=None, tokenizer_revision=None, tokenizer_mode='auto', trust_remote_code=False, allowed_local_media_path=None, download_dir=None, load_format='auto', config_format=<ConfigFormat.AUTO: 'auto'>, dtype='auto', kv_cache_dtype='auto', max_model_len=None, guided_decoding_backend='xgrammar', logits_processor_pattern=None, model_impl='auto', distributed_executor_backend=None, pipeline_parallel_size=1, tensor_parallel_size=1, max_parallel_loading_workers=None, ray_workers_use_nsight=False, block_size=None, enable_prefix_caching=None, disable_sliding_window=False, use_v2_block_manager=True, num_lookahead_slots=0, seed=0, swap_space=4, cpu_offload_gb=0, gpu_memory_utilization=0.9, num_gpu_blocks_override=None, max_num_batched_tokens=None, max_num_partial_prefills=1, max_long_partial_prefills=1, long_prefill_token_threshold=0, max_num_seqs=None, max_logprobs=20, disable_log_stats=False, quantization=None, rope_scaling=None, rope_theta=None, hf_overrides=None, enforce_eager=False, max_seq_len_to_capture=8192, disable_custom_all_reduce=False, tokenizer_pool_size=0, tokenizer_pool_type='ray', tokenizer_pool_extra_config=None, limit_mm_per_prompt=None, mm_processor_kwargs=None, disable_mm_preprocessor_cache=False, enable_lora=False, enable_lora_bias=False, max_loras=1, max_lora_rank=16, lora_extra_vocab_size=256, lora_dtype='auto', long_lora_scaling_factors=None, max_cpu_loras=None, fully_sharded_loras=False, enable_prompt_adapter=False, max_prompt_adapters=1, max_prompt_adapter_token=0, device='auto', num_scheduler_steps=1, multi_step_stream_outputs=True, scheduler_delay_factor=0.0, enable_chunked_prefill=None, speculative_model=None, speculative_model_quantization=None, num_speculative_tokens=None, speculative_disable_mqa_scorer=False, speculative_draft_tensor_parallel_size=None, speculative_max_model_len=None, speculative_disable_by_batch_size=None, ngram_prompt_lookup_max=None, ngram_prompt_lookup_min=None, spec_decoding_acceptance_method='rejection_sampler', typical_acceptance_sampler_posterior_threshold=None, typical_acceptance_sampler_posterior_alpha=None, disable_logprobs_during_spec_decoding=None, model_loader_extra_config=None, ignore_patterns=[], preemption_mode=None, served_model_name=None, qlora_adapter_name_or_path=None, otlp_traces_endpoint=None, collect_detailed_traces=None, disable_async_output_proc=False, scheduling_policy='fcfs', scheduler_cls='vllm.core.scheduler.Scheduler', override_neuron_config=None, override_pooler_config=None, compilation_config=None, kv_transfer_config=None, worker_cls='auto', generation_config=None, override_generation_config=None, enable_sleep_mode=False, calculate_kv_scales=False, additional_config=None, disable_log_requests=False, max_log_len=None, disable_fastapi_docs=False, enable_prompt_tokens_details=False, dispatch_function=<function ServeSubcommand.cmd at 0x76e9a8ab49a0>)