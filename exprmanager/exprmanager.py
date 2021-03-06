# exprmanager/exprmanager.py

import os
import numpy as np
import itertools

from exprmanager import utils

class ExprManager():
    ''' manage the logistics between the main program
    and the experiment output folder.
    create a class instance for a single experiment (a folder).
    '''
    def __init__(self, base_dir='', expr_name='test', 
                 varied=None, config=None):
        # set up expr_subdir
        self.expr_name = expr_name
        self.expr_dir = os.path.join(base_dir, expr_name + '/')
        self.res_dir = os.path.join(self.expr_dir, 'res/')
        # os.makedirs(self.res_dir, exist_ok=True) # recursive mkdir
        
        if varied is not None:
            self.varied = varied
        
        self.config = config or dict() # if None, empty dict    
        self.config['expr_name'] = expr_name
        
    def save_varied_params(self):
        for param_name, param_values in self.varied.items():
            self.print_parameter_list(self.expr_dir + param_name + '.tsv', param_values)
        
    @staticmethod
    def print_parameter_list(filename, param_values, delimiter='\t'):
        ''' save parameter set into a tab-separted value (tsv) file
        where each row has an index and a value.
        params: expecting a list of values.
        '''
        header = ['idx', 'val']
        body = [[i, v] for i, v in enumerate(param_values)]
        utils.write_csv(filename, body, header=header, delimiter=delimiter)
    
    def load_parameter_list(self, param_name, delimiter='\t'):
        body, _ = utils.read_csv(self.expr_dir + param_name + '.tsv', 
                                      nheader=1,
                                      delimiter=delimiter)
        # idx = [int(row[0]) for row in body] # no need
        val = [float(row[1]) for row in body]
        return val
            
    def save_config(self):
        config_copy = self.treat_dict_before_export(self.config)
        utils.save_json(self.expr_dir + 'config.json', config_copy)
    
    def load_config(self):
        return utils.load_json(self.expr_dir + 'config.json')
    
    def treat_dict_before_export(self, full_dict, allow_only=None):
        # TODO: change to listing types that are *not* allowed
        if allow_only is None:
            allow_only=(int, float, str, np.ndarray, type(None))
        return utils.copy_nested_dict(full_dict,
                            allow_only=allow_only, replace_value='(dropped)')
        
    def set_filename(self, idx, prefix='sol', subdir=False):
        if subdir:
            prefix = prefix + '/' + prefix
        return utils._set_filename(idx, prefix=prefix, extension='')
        
    def save_result(self, obj, filename, return_path=False):
        ''' save to a BSDF file. '''
        filename = utils.ensure_extension(filename, ext='.bsdf')
        res_path = os.path.join(self.res_dir, filename) # full path to file
        # if `filename` includes subdirectories like 'sub/dir/file', make them
        os.makedirs(os.path.dirname(res_path), exist_ok=True)
        utils.save_bsdf(res_path, obj)
        if return_path:
            return res_path
        
    def load_result(self, filename):
        ''' load and return previous result if available as a file;
        if the file does not exist, return None.
        '''
        filename = utils.ensure_extension(filename, ext='.bsdf')
        res_path = os.path.join(self.res_dir, filename) # full path to file
        try:
            return utils.load_bsdf(res_path) # previous result
        except FileNotFoundError:
            return None
    
    def export_as_dict(self, obj, filename):
        ''' export a copy of the __dict__ of the given object;
        in this case a model or a solver,
        that stores parameter values as attributes.
        '''
        return export_dict(obj.__dict__)
        
    def export_dict(self, obj, filename):
        ''' export a copy of the dictionary object to a file.
        obj: dict (output data)
        filename: string (path to output file to be generated)
        '''
        out_dict = self.treat_dict_before_export(obj)
        out_dict['type'] = type(obj).__name__ # make a string
        self.save_result(out_dict, filename)
        return out_dict
        
    def call_with_file(self, solver, data=None, idx=None,
                    solver_kwargs=None, save_output=True,
                    prefix='sol', subdir=False,
                    force_recalculate=False, verbose=True):
        filename = self.set_filename(idx, prefix=prefix, subdir=subdir)
        # check for previously saved file
        if not force_recalculate:
            sol = self.load_result(filename)
            if sol is not None:
                if verbose:
                    print(' - {}: loaded from file'.format(filename))
                return sol
        if solver is None:
            raise FileNotFoundError('{}: check filename or generate.'.format(filename))
                
        # do the computation and save results to file
        if verbose:
            print(' - {}: running...'.format(filename))
        solver_kwargs = solver_kwargs or self.config.get('solver', dict())
        sol = solver(*data, **solver_kwargs)
        if save_output:
            _ = self.export_dict(sol, filename) # write to a BDSF file
        return sol
        
    def load_from_export(self, filename):
        # TODO: load previous exports, to create a new copy of object
        pass
        
    def varied_param_iterables(self):
        ''' prepare for iteration over multiple parameter loops.
        return iterable lists of K-tuples, where K is the param space dim.
        '''
        # expand
        val_aux = tuple(self.varied.values())
        idx_aux = tuple([np.arange(0, len(vv)) for vv in val_aux])
        idx_iter = itertools.product(*idx_aux)
        val_iter = itertools.product(*val_aux)
        return idx_iter, val_iter

    def run_expr_loop(self, data_input, func_prep_data, func_solve):
        ''' common template for parameter space sweep
        '''
        # print parameter lists and solver configs
        self.save_varied_params()
        self.save_config()
        
        # prepare (or generate) data for inference etc.
        data = func_prep_data(data_input)

        # iterate
        idx_iter, prm_iter = self.varied_param_iterables()
        for idx, prm in zip(idx_iter, prm_iter):
            func_solve(idx, prm, data)
        print('end of experiment.')
