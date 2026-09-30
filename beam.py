from requests import post
from sys import argv
def lst(_): return _ if isinstance(_, list)else (_,)


n = int(argv[1])
s = (0, f'<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\n<|im_start|>user\n{argv[2]}\n<|im_start|>assistant\n'),
while True:
    s = sorted((s[0]-_['logprob'], s[1]+_['token'])for s, _ in zip(s, lst(post('http://localhost:8080/completion', json={'prompt': [s[1]for s in s], 'n_predict': 1, 'n_probs': n}).json()))for _ in _['completion_probabilities'][0]['top_logprobs'])[:n]
    print(s[0][1])
