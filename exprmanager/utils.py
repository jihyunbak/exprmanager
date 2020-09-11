# exprmanager/utils.py

import os
import time

import bsdf # note: install using pip - at this time conda doesn't work
import json
import csv

# --- file i/o ---

def write_csv(filename, body, header=None, quoting=None, delimiter=','):
    ''' write to a csv file.
    body and header should be iterables (expecting lists).
    '''
    quoting = quoting or csv.QUOTE_NONNUMERIC
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=quoting, delimiter=delimiter)
        if (header is not None) and (len(header) > 0):
            writer.writerow(header)
        writer.writerows(body)

def read_csv(filename, nheader=0, delimiter=','):
    ''' read from a csv file and return lists.
    optionally read the first n lines seperately as header (default is 0).
    '''
    body = []
    header = []
    with open(filename, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            if len(header) < nheader:
                header.append(row)
                continue
            body.append(row)
    if nheader>0:
        return body, header
    else:
        return body

def save_json(json_file, object, indent=4):
    with open(json_file, 'w') as fh:
        json.dump(object, fh, indent=4)

def load_json(json_file):
    with open(json_file, 'r') as fh:
        object = json.load(fh)
    return object

def save_bsdf(filename, object, encode=True):
    ''' save object to a BSDF file. optionally BSDF-encoded to bytes. '''
    if encode:
        object = bsdf.encode(object) # type: bytes
    bsdf.save(filename, object)

def load_bsdf(filename, decode=True):
    ''' load object from a BSDF file. automatically decode if in bytes. '''
    object = bsdf.load(filename)
    if decode and (type(object) is bytes):
        return bsdf.decode(object)
    else:
        return object
        
# --- other functions ---
        
def timer(old_time=None):
    new_time = time.time()
    if old_time is None:
        elapsed = 0
    else:
        elapsed = new_time - old_time
    return elapsed, new_time

def drop_key(obj, key, replace=None):
    ''' recursively search a dict object and drop specified key '''
    if replace is None:
        obj.pop(key, None)
    else:
        obj[key] = replace
    for k, v in obj.items():
        if isinstance(v, dict):
            drop_key(v, key, replace=replace)
            
def copy_nested_dict(old_dict, allow_only=None, replace_value=None):
    ''' manual deepcopy, optionally replacing values for certain types. '''
    new_dict = dict()
    for k, v in old_dict.items():
        if isinstance(v, dict):
            new_dict[k] = copy_nested_dict(v, allow_only=allow_only, replace_value=replace_value)
            continue
        if allow_only is None:
            # allow all types
            new_dict[k] = v
            continue
        if any([isinstance(v, tp) for tp in allow_only]):
            new_dict[k] = v
        else:
            new_dict[k] = replace_value
    return new_dict

def print_value_types(obj, return_unique=True):
    ''' recursively search a dict object and print all value types.
    if return_unique is True, return a set (non-repeated values)
    '''
    all_types = []
    for k, v in obj.items():
        all_types.append(type(v))
        if isinstance(v, dict):
            all_types.extend(print_value_types(v))
    if return_unique:
        return set(all_types)
    # otherwise return the raw list
    return all_types

def _set_filename(idx, keys='', prefix='result', extension='.bsdf', separator='_'):
    ''' set filenames by index when doing batch experiment '''
    if len(idx) == len(keys):
        _key = lambda i: keys[i]
    elif len(keys) == 1:
        _key = lambda i: keys[0]
    else:
        _key = lambda i: '' # empty
    filename = prefix
    for i, id in enumerate(idx):
        filename += separator + _key(i) + '{}'.format(id)
    filename += extension
    return filename
