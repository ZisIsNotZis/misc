#!/bin/env python
import copy
import os
import yaml
import glob

class FlowDumper(yaml.SafeDumper):
    def represent_sequence(s, tag, sequence, flow_style=None):
        return super().represent_sequence(tag, sequence, True)


def adj(task, op, mi, ma):
    if (val := task.get(op)) is None:
        return
    task[f'{op}_scale'] = scale = (ma-mi)/(val[1]-val[0]+1e-3)
    task[f'{op}_base'] = mi-val[0]*scale
    task[f'_{op}'] = val
    task[op] = mi, ma


FAC = {
    'PRRIGHT': 5 / 65,
    'PRLEFT': 5 / 65,
    'DBMA-MGP': 5 / 86,
    'DBMA-ADR': 4 / 112,
    'DBMA-EBR': .5 / 8,
    'DSMA': 1
}
cfgs = {i:yaml.safe_load(open(i)) for i in glob.iglob(f'*/cfg.yaml')}
for cfgfile,cfg in cfgs.items():
    for floor in cfg.values():
        for unitid, unit in floor['unit'].items():
            for area in unit.setdefault('area', {}).values():
                for cam in area['cam'].values():
                    for nozleid, nozle in cam['nozle'].items():
                        for missionid, mission in nozle['mission'].items():
                            if nozleid.startswith('RRC') and missionid.endswith('PROCESS'):
                                mission['stage'].setdefault('WAITAFTER', {'time': .5})
                                mission['stage'].setdefault('AFTER', {'time': .05, 'task': {'NOZLE': {}, 'DIRT': {}, 'SB': {}, 'FLOW': {}}})
                            if (nozleid.startswith('PR') or nozleid.startswith('RRC')) and missionid.endswith('PROCESS'):
                                tmp = {'DURING': mission['stage'].pop('DURING'), 'WAITAFTER': mission['stage'].pop('WAITAFTER'), 'AFTER': mission['stage'].pop('AFTER')}
                                mission['stage']['WAITDURING2'] = {'time': .1, 'task': {}}
                                mission['stage'] |= tmp
                            if nozleid.startswith('PR') and missionid.endswith('PROCESS'):
                                mission['stage']['WAITAFTER']['time'] = .9
                            for stageid, stage in mission['stage'].items():
                                for taskid, task in stage.get('task', {}).items():
                                    task.clear()
for f in os.listdir('label'):
    if not f.endswith('.yml'):
        continue
    stagepat, taskpat = f[:-4].split('.')
    unitpat, nozlepat, missionpat, stagepat = stagepat.replace('-NIGHT', '').split('-', 3)
    if os.getenv('NOZLEMISSWAP'):
        nozlepat, missionpat = missionpat, nozlepat
    f = {i: j for i, j in yaml.safe_load(open(f'label/{f}')).items()if i[0] != '_'}
    b = False
    for cfgfile,cfg in cfgs.items():
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
                                    b = False
                                    for taskid, task in stage.setdefault('task', {}).items():
                                        if not taskpat in taskid:
                                            continue
                                        task |= copy.deepcopy(f)
                                        b = True
                                    if not b:
                                        stage['task'][taskpat] = copy.deepcopy(f)
                                        b = True
    if not b:
        print(f'unit={unitpat} nozle={nozlepat} misions={missionpat} stage={stagepat} task={taskpat} no loc to insert')
for cfgfile,cfg in cfgs.items():
    for floorid, floor in cfg.items():
        for unitid, unit in floor['unit'].items():
            for areaid, area in unit['area'].items():
                for camid, cam in area['cam'].items():
                    cam['orderFactor'] = fac = FAC[camid]
                    for nozleid, nozle in cam['nozle'].items():
                        for missionid, mission in nozle['mission'].items():
                            for stageid, stage in mission['stage'].items():
                                for taskid, task in stage.setdefault('task',{}).items():
                                    if any('_base' in i for i in task):
                                        continue
                                    if areaid == 'PR':
                                        if stageid in 'BEFORE AFTER':
                                            if taskid == 'SB':
                                                adj(task, 'row', 3/fac, 5/fac)
                                            elif taskid == 'NOZLE':
                                                adj(task, 'row', -.4/fac, .4/fac)
                                                adj(task, 'column', -.4/fac, .4/fac)
                                                adj(task, 'phi', -1/180*3.14, 1/180*3.14)
                                                adj(task, 'area', 0, (.4/fac)**2)
                                            elif taskid == 'DIRT':
                                                adj(task, 'area', 0, (.4/fac)**2)
                                            elif taskid == 'FLOW':
                                                task['width'] = 0, .4/fac
                                        elif 'DURING' in stageid:
                                            if 'width' in task:
                                                task['width_avg'] = copy.deepcopy(task['width'])
                                    elif areaid == 'EBR':
                                        if taskid == 'NOZLE':
                                            adj(task, 'row', -.4/fac, .4/fac)
                                            adj(task, 'column', -.4/fac, .4/fac)
                                            adj(task, 'phi', -1/180*3.14, 1/180*3.14)
                                            adj(task, 'area', 0, (.2/fac)**2)
                                        elif taskid == 'DIRT':
                                            adj(task, 'area', 0, (.2/fac)**2)
                                    elif areaid == 'ADR':
                                        if taskid == 'SB':
                                            adj(task, 'row', 2/fac, 3/fac)
                                        elif taskid == 'NOZLE':
                                            adj(task, 'row', -.5/fac, .5/fac)
                                            adj(task, 'column', -.5/fac, .5/fac)
                                            adj(task, 'phi', -3/180*3.14, 3/180*3.14)
                                            adj(task, 'area', 0, (.5/fac)**2)
                                        elif taskid == 'DIRT':
                                            adj(task, 'area', 0, (.5/fac)**2)
                                        elif taskid == 'FLOW':
                                            adj(task, 'width', 0, .2/fac)
                                    elif areaid == 'MGP':
                                        if nozleid == 'SUBDIW':
                                            if taskid == 'SB':
                                                adj(task, 'row', 2/fac, 3/fac)
                                            elif taskid == 'NOZLE':
                                                adj(task, 'row', -.5/fac, .5/fac)
                                                adj(task, 'column', -.5/fac, .5/fac)
                                                adj(task, 'phi', -3/180*3.14, 3/180*3.14)
                                                adj(task, 'area', 0, (.5/fac)**2)
                                            elif taskid == 'DIRT':
                                                adj(task, 'area', 0, (.5/fac)**2)
                                            elif taskid == 'FLOW':
                                                adj(task, 'width', 0, .2/fac)
                                        elif nozleid == 'SUBDEV':
                                            if taskid == 'SB':
                                                adj(task, 'row', 2/fac, 3/fac)
                                            elif taskid == 'NOZLE':
                                                adj(task, 'row', -.5/fac, .5/fac)
                                                adj(task, 'column', -.5/fac, .5/fac)
                                                adj(task, 'phi', -3/180*3.14, 3/180*3.14)
                                                adj(task, 'area', 0, (.5/fac)**2)
                                            elif taskid == 'DIRT':
                                                adj(task, 'area', 0, (.5/fac)**2)
                                            elif taskid == 'FLOW':
                                                adj(task, 'width', 0, .2/fac)
                                        elif nozleid in 'MGPH MGPL':
                                            if taskid == 'SB':
                                                adj(task, 'row', 2/fac, 3/fac)
                                            elif taskid == 'NOZLE':
                                                adj(task, 'row', -.5/fac, .5/fac)
                                                adj(task, 'column', -.5/fac, .5/fac)
                                                adj(task, 'phi', -3/180*3.14, 3/180*3.14)
                                                adj(task, 'area', 0, (.5/fac)**2)
                                            elif taskid == 'DIRT':
                                                adj(task, 'area', 0, (.5/fac)**2)
                                            elif taskid == 'FLOW':
                                                adj(task, 'width', 0, .2/fac)
                                    elif areaid == 'DSMA':
                                        if taskid == 'FLOW':
                                            adj(task, 'width', 0, .2/fac)
                                        elif taskid == 'FLOW2':
                                            adj(task, 'width', 0, .1/fac)
for cfgfile,cfg in cfgs.items():
    yaml.dump_all((cfg,), open(cfgfile, 'w'), FlowDumper, sort_keys=False, width=999)
