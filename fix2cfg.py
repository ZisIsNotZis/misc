#!/bin/env python3.12
import copy
import yaml


class FlowDumper(yaml.SafeDumper):
    def represent_sequence(s, tag, sequence, flow_style=None):
        return super().represent_sequence(tag, sequence, True)


FAC = {
    'PRRIGHT': 5 / 65,
    'PRLEFT': 5 / 65,
    'DBMA-MGP': 5 / 86,
    'DBMA-ADR': 4 / 112,
    'DBMA-EBR': .5 / 8,
    'DSMA': 1
}

cfgs = [yaml.safe_load(open(f'user@192.168.10.{i}/cfg.yaml')) for i in range(4, 10)]
for cfg in cfgs:
    for floorid, floor in cfg.items():
        for unitid, unit in floor['unit'].items():
            for areaid, area in unit['area'].items():
                for camid, cam in area['cam'].items():
                    cam['orderFactor'] = fac = FAC[camid]
                    for nozleid, nozle in cam['nozle'].items():
                        for missionid, mission in nozle['mission'].items():
                            if areaid == 'DSMA' and nozleid == '_':
                                mission['stage']['WAITAFTER'] = {'time': 10}
                            for stageid, stage in mission['stage'].items():
                                if areaid == 'DSMA' and 'ADR' in nozleid and taskid == 'FLOW':
                                    stage['task']['FLOW2'] = stage['task'].pop('FLOW')
                                for taskid, task in stage.setdefault('task', {}).items():
                                    if areaid == 'PR':
                                        if taskid == 'SB':
                                            task['row'] = [3/fac, 5/fac]
                                        elif taskid == 'NOZLE':
                                            task['row'] = [-.4/fac, .4/fac]
                                            task['column'] = [-.4/fac, .4/fac]
                                            task['phi'] = [-1/180*3.14, 1/180*3.14]
                                        elif taskid == 'DIRT':
                                            task['area'] = [-999, 0.4/fac**2]
for i, cfg in enumerate(cfgs, 4):
    yaml.dump_all([cfg], open(f'user@192.168.10.{i}/cfg.yaml', 'w'), FlowDumper, sort_keys=False, width=999)
