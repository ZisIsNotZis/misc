from pyarrow.parquet import read_table
from json import loads
from os import listdir
from re import sub, split
MODEL = {
    'qwen': ('<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are _ helpful assistant.', '<|im_end|>\n<|im_start|>user\n', '<|im_end|>\n<|im_start|>assistant\n'),
    'ds': ('<｜begin▁of▁sentence｜>', '<｜User｜>', '</think>', '<｜Assistant｜><think>')
}


def read(dat):
    dat = f'hf/hub/{[i for i in listdir('hf/hub')if dat in i.lower()][0]}/snapshots/'
    dat += listdir(dat)[0]
    if 'data' in listdir(dat):
        dat += '/data'
    for rows in listdir(dat):
        rows = f'{dat}/{rows}'
        if rows[-6:] == '.jsonl':
            yield from map(loads, open(rows))
        elif rows[-8:] == '.parquet':
            rows = read_table(rows)
            for row in zip(*rows.columns):
                yield dict(zip(rows.column_names, row))


def write(dat, chat):
    files = {}
    for model, template in MODEL.items():
        try:
            open(f'{dat}-{model}.txt')
        except FileNotFoundError:
            files[open(f'{dat}-{model}.txt', 'w')] = template
    if not files:
        return
    for chat in chat:
        for file, template in files.items():
            file.write(template[0])
            for message in chat:
                if str(message['role']) == 'user':
                    file.write(template[1])
                elif str(message['role']) == 'assistant':
                    file.write(template[2])
                elif str(message['role']) == 'think':
                    if len(template) < 4:
                        continue
                    file.write(template[3])
                else:
                    raise KeyError(message['role'])
                file.write(str(message['content']))


def readwrite(dat, fn):
    write(dat, map(fn, read(dat)))


readwrite('magpie-qwen2-pro-200k-chinese', lambda row: [
    {'role': 'user', 'content': row["instruction"]},
    {'role': 'think', 'content': f'{row["intent"]}\n\n{row["quality_explanation"]}\n\n{sub("the models?", "I", str(row["knowledge"]), 0, 2)}'},
    {'role': 'assistant', 'content': row['response']}
])
readwrite('reflection-chinese', lambda row: [
    {'role': 'user', 'content': row['prompt']},
    {'role': 'think', 'content': (t := [sub('</?[^>]*>', '', i)for i in split('<output>|<输出>', row['response'], 1)])[0]},
    {'role': 'assistant', 'content': t[1]}
])
readwrite('chinese-deepseek-r1-distill-data-110k', lambda row: [
    {'role': 'user', 'content': row['input']},
    {'role': 'think', 'content': row['reasoning_content']},
    {'role': 'assistant', 'content': row['content']}
])
readwrite('ultrachat_200k', lambda row: [i for i in row['messages']for i in ([i]if i['role'] == 'user'else [{'role': 'think', 'content': ''}, i])])
