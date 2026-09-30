#!/bin/env python3.12
import copy
import os
import yaml


class FlowDumper(yaml.SafeDumper):
    def represent_sequence(s, tag, sequence, flow_style=None):
        return super().represent_sequence(tag, sequence, True)


cfgs = [yaml.safe_load(open(f'user@192.168.10.{i}/cfg.yaml')) for i in range(4, 10)]
for f in os.listdir('label'):
    if not f.endswith('.yml'):
        continue
    stagepat, taskpat = f[:-4].split('.')
    unitpat, nozlepat, missionpat, stagepat = stagepat.split('-')
    f = yaml.safe_load(open(f'label/{f}'))
    b = False
    for cfg in cfgs:
        for floor in cfg.values():
            for unitid, unit in floor['unit'].items():
                if not unitpat in unitid.replace('-SCR', '').replace('-SCT', '').replace('-SDC', ''):
                    continue
                for area in unit['area'].values():
                    for cam in area['cam'].values():
                        for nozleid, nozle in cam['nozle'].items():
                            if not nozlepat in nozleid:
                                continue
                            for missionid, mission in nozle['mission'].items():
                                if not missionpat in missionid:
                                    continue
                                for stageid, stage in mission['stage'].items():
                                    if not stagepat in stageid:
                                        continue
                                    for taskid, task in stage.get('task', {}).items():
                                        if not taskpat in taskid:
                                            continue
                                        task.clear()
                                        task |= copy.deepcopy(f)
                                        b = True
    if not b:
        print(unitpat, nozlepat, missionpat, stagepat, taskpat)
for i, cfg in enumerate(cfgs, 4):
    yaml.dump_all((cfg,), open(f'user@192.168.10.{i}/cfg.yaml', 'w'), FlowDumper, sort_keys=False, width=999)
