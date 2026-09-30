# 加速
* 更快的数据类型: bf16/fp16 + (tf32) + (mixed)
* 更大的 batch
  * 更大的 effective batch
* 更快的 optimizer
* 更快的 data loader
* 更快的 operator
  * kernel
  * jit

# 降显存
* 更小的数据类型: bf16/fp16 + (tf32) + (mixed)
  * 量化
    * 二重量化
* 更小的 batch
* 占显存更小的 optimizer
  * 量化 optimizer
* 占显存更小的 operator
  * kernel
  * jit
* offload
  * gradient checkpoint
  * zero offload

WANDB_DISABLED=true python main.py --do_train --train_file ../../qa.json --prompt_column eq --response_column a --preprocessing_num_workers 6 --model_name_or_path THUDM/chatglm2-6b --output_dir tmp --pre_seq_len 256 --max_source_length 150 --max_target_length 108 --per_device_train_batch_size 8 --optim adamw_torch_fused --learning_rate 1e-2 --logging_steps 100 --save_steps .5 --num_train_epochs 2 --fp16_full_eval --tf32 true --torch_compile_backend inductor