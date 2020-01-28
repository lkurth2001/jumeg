#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 08.10.19
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------

"""
https://stackoverflow.com/questions/6866600/how-to-parse-read-a-yaml-file-into-a-python-object
"""
import os,os.path as op
import logging,pprint

from jumeg.base.jumeg_base import jumeg_base as jb
from jumeg.base            import jumeg_logger

import datetime
import getpass
from copy import copy
from ruamel.yaml import YAML

logger = logging.getLogger("jumeg")

__version__= "2019.10.08.001"

class _Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

class dict2obj(dict):
    def __init__(self, dict_):
        super(dict2obj, self).__init__(dict_)
        for key in self:
            item = self[key]
            if isinstance(item, list):
                for idx, it in enumerate(item):
                    if isinstance(it, dict):
                        item[idx] = dict2obj(it)
            elif isinstance(item, dict):
                self[key] = dict2obj(item)

    def __getattr__(self, key):
        # Enhanced to handle key not found.
        if self.has_key(key):
            return self[key]
        else:
            return None

class Struct(object):
    """
    https://stackoverflow.com/questions/1305532/convert-nested-python-dict-to-object
    Nr: 30
    """
    def __init__(self, data):
        for name, value in data.items():
            setattr(self, name, self._wrap(value))

    def _wrap(self, value):
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])
        else:
            return Struct(value) if isinstance(value, dict) else value
        

class JuMEG_CONFIG_Info():
    
    def __init__(self,user=None,date=None,version=None,comments=None):
        self._param={"user":None,"date":None,"version":version,"comments":comments}
        if user==None:
            user=getpass.getuser()
            self._param["user"]=user
        else:
            self._param["user"]=user
        if date!=None:
            self._param["date"]=date
        
    def reload_date(self):
        now=datetime.datetime.now()
        dt=now.strftime('%Y-%m-%d')+" "+now.strftime('%H:%M')
        return dt
        
    def printInfo(self):
        logger.info("user: {}".format(self.user))
        
    def get_param(self):
        d=copy(self._param)
        d["date"]=self.date
        return d
    
    def _get_param(self,key):
        return self._param[key]
    
    def _set_param(self,key,value):
        self._param[key]=value
        
    @property
    def user(self): return self._get_param("user")
    
    @property
    def date(self):
        if self._param["date"]==None:
            return self.reload_date()
        return self._get_param("date")
        
    @property
    def version(self): return self._get_param("version")
    
    @version.setter
    def version(self,v): self._set_param("version",v)
    
    @property
    def comments(self): return self._get_param("comments")
    
    @comments.setter
    def comments(self,v): self._set_param("comments",v)
        
        
class JuMEG_CONFIG_YAML_BASE(object):
    """
    load or get yaml config as dict
    convert to object
    
    Example:
    --------
     cfg["test"] => cfg.test
     cfg["test"]["A"] => cfg.test.A
    """
    def __init__(self,**kwargs):
        self._fname = None
        self._data  = None
        self._cfg   = None
        self._init(**kwargs)
        self._yaml=YAML()
    
    @property
    def data(self): return self._data
   
    @property
    def filename(self): return self._fname
    
    def _init(self,**kwargs):
        pass
    
    def info(self):
        """print config dict"""
        #logger.info("info")
        logger.info("---> config file: {}\n{}/n".format(self.filename,pprint.pformat(self._cfg,indent=4)))
        #logger.info("---> config file: {}\n{}/n".format(self.filename,yaml.dump(self._cfg,indent=4)))
    #def GetData(self,key=None):
    #    if key:
    #        return self._cfg.et(key)
    #    return self._cfg
    
    def GetDataDict(self,key=None):
        if key:
           return self._cfg.get(key)
        return self._cfg
    
    def _init(self,**kwargs):
        pass
    
    def load_cfg(self,fname=None,key=None):
        if fname:
           self._fname = jb.expandvars(fname)
        with open(self._fname) as f:
            self._cfg = self._yaml.load(f)
            if key:
                self._cfg = self._cfg.get(key)
            self._data = Struct( self._cfg )
            
        return self._data
    
    def update(self,**kwargs):
        """
        update config obj
        :param config: config dict or filename
        :param key: if <key> use part of config e.g.: config.get(key)
        :return:
        """
        self._cfg = kwargs.get("config",None)
        key = kwargs.get("key",None)
        
        if isinstance(self._cfg,(dict)):
           if key:
              self._cfg  = self._cfg.get(key)
           self._data  = Struct(self._cfg)
           self._fname = None
        else:
           self.load_cfg(fname=self._cfg,key=key)
           
           
    def save_cfg(self,fname=None,data=None):
         """
         """
         if data:
            self._cfg=data
         if fname:
            self._fname = jb.expandvars(fname)
         with open(self._fname, "w") as f:
            self._yaml.dump(self._cfg, f)
        
if __name__=='__main__':
    from jumeg.base.jumeg_logger import setup_script_logging
    logger=setup_script_logging(logger=logger,name="jumeg",opt=None)
    print('test:')
    info=JuMEG_CONFIG_Info(version=__version__)
    info.printInfo()
    print(info.get_param())
    """cfg=JuMEG_CONFIG_YAML_BASE()
    cfg.update(config="./test_config.yaml")
    cfg.info()"""
