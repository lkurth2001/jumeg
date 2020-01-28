#!/usr/bin/env python3
# coding: utf-8


import os,sys,argparse

import wx
import wx.lib.agw.customtreectrl as CT
from wx.lib.agw.customtreectrl import CustomTreeCtrl
#import wx.propgrid as wxpg

from jumeg_base_config import JuMEG_CONFIG_YAML_BASE

# from jumeg.gui.wxlib.utils.jumeg_gui_wxlib_utils_property_grid import JuMEG_wxPropertyGridPageBase,JuMEG_wxPropertyGridPageNotebookBase,JuMEG_wxPropertyGridSubProperty

import logging
from jumeg.base import jumeg_logger
logger = logging.getLogger('jumeg')

import getpass
import datetime
import platform
from ruamel.yaml import YAML

__version__="2019-11-22-001"


"""
#https://stackoverflow.com/questions/15751029/how-do-i-properly-use-check-boxes-with-wx-lib-agw-customtreectrl-customtreectrl

import wx, wx.lib.agw.customtreectrl

app = wx.App(False)

fr = wx.Frame(None)

myModule = wx.lib.agw.customtreectrl
myStyle = (myModule.TR_DEFAULT_STYLE|myModule.TR_MULTIPLE
           |myModule.TR_FULL_ROW_HIGHLIGHT|myModule.TR_AUTO_CHECK_CHILD
           |myModule.TR_AUTO_CHECK_PARENT|myModule.TR_AUTO_TOGGLE_CHILD)

tree = myModule.CustomTreeCtrl(fr, agwStyle=myStyle)
treeRoot = tree.AddRoot("PyRx Enzymes")
treeNodes =['Node A','Node B', 'Node C']
treeItems = ['1', '2', '3']
for i, _ in enumerate(treeNodes):
    iNode = tree.AppendItem(treeRoot, treeNodes[i], ct_type=1)
    for ii in treeItems:
        tree.AppendItem(iNode, "%s %s"%(treeNodes[i].replace('Node ',''), ii), ct_type=1)
tree.Expand(treeRoot)

fr.Show()

app.MainLoop()
"""

"""
https://wxpython.org/Phoenix/docs/html/wx.lib.agw.customtreectrl.CustomTreeCtrl.html

AppendItem
        parentId – an instance of GenericTreeItem representing the item’s parent;

        text (string) – the item text label;

        ct_type (integer) – the item type (see SetItemType for a list of valid item types);

        wnd – if not None, a non-toplevel window to show next to the item, any subclass of wx.Window;

        image (integer) – an index within the normal image list specifying the image to use for the item in unselected state;

        selImage (integer) – an index within the normal image list specifying the image to use for the item in selected state; if image > -1 and selImage is -1, the same image is used for both selected and unselected items;

        data (object) – associate the given Python object data with the item.

        on_the_right (bool) – True positions the window on the right of text, False on the left of text and overlapping the image.

"""

"""
ComboBox stuff used for later
text_size = len(max(l,key=len))
combo = wx.ComboBox(self, -1, choices=l, style=wx.CB_READONLY|wx.CB_DROPDOWN)
#--- https://wxpython.org/Phoenix/docs/html/wx.Control.html#wx.Control.GetSizeFromTe
sz = combo.GetSizeFromTextSize(combo.GetTextExtent("W" * text_size) )
combo.SetInitialSize(sz)
"""


class MyTreeCtrl(CustomTreeCtrl):
   def __init__(self,parent,**kwargs):
       style = (CT.TR_DEFAULT_STYLE|CT.TR_MULTIPLE
               |CT.TR_FULL_ROW_HIGHLIGHT|CT.TR_HAS_VARIABLE_ROW_HEIGHT
               |CT.TR_AUTO_CHECK_CHILD
               |CT.TR_AUTO_CHECK_PARENT|CT.TR_AUTO_TOGGLE_CHILD
               |CT.TR_ELLIPSIZE_LONG_ITEMS|CT.TR_TOOLTIP_ON_LONG_ITEMS
               |CT.TR_ALIGN_WINDOWS)
               #|CT.TR_ALIGN_WINDOWS_RIGHT)
       
       super().__init__(parent,agwStyle=style)
       
       self._sortedKeys="wx_keys"
       self._sortedDictKeys="sorted_keys"
       self._list_seperator=" "
       self._data=dict()
       self._wx_init(**kwargs)
       
       self._info=dict()
       self._used_dict=dict()
       
       
   def sort(self,keys):
       
       pass
    
   def _get_item_data(self,data,item_data):
      #item_data["info"]=self.update_info()
      self.__get_item_data(data,item_data)
   
   def __get_item_data(self,data,item_data):
        if data==None:
           logger.exception("data is None")
           return
        keys = list(data.keys())
        keys.sort()
        #print(keys)
       
        for k in keys:
           v = data[k]
           #child=None
           
           if isinstance(v,(dict)):
               item_data[k]=dict()
               self.__get_item_data(data[k],item_data[k])
           else:
               if (v.GetName()=="list"):
                   d=v.GetLineText(lineNo=0).split(self._list_seperator)
                   if (d):
                       item_data[k]=d
                   else:
                       item_data[k]=list()
               else:
                  #item_data[k]=self.GetItemData(data[k])
                  item_data[k]=v.GetValue()
        return item_data
        """elif (v.GetName()=="str"):
        d=v.GetLineText(lineNo=0)
        if (d):
        item_data[k]=d
        else:
        item_data[k]=str()
        elif (v.GetName()=="int"):
        d=v.GetValue()
        if (d):
        item_data[k]=d
        else:
        item_data[k]=int()
        elif (v.GetName()=="float"):
        d=v.GetValue()
        if (d):
        item_data[k]=d
        else:
        item_data[k]=float()
        elif (v.GetName()=="bool"):
        d=v.IsChecked()
        if (d):
        item_data[k]=d
        else:
        item_data[k]=bool()
        item_data["info"]=self.update_info()
        print(item_data["info"])"""
               
   
   def GetData(self):
       data=self._item_data
       item_data=dict()
       item_data["info"]=self.update_info()
       keys = list(data.keys())
       for k in keys:
           item_data[k]=dict()
           self._get_item_data(data[k],item_data[k])
           
           
       return item_data
       
   def _init_tree_ctrl(self,data=None,root=None,item_data=None):
       if data==None:
           logger.exception("data is None")
           return
       txt_size = 10
       keys = list(data.keys())
       keys.sort()
       
       if "sorted_keys" in keys:
           keys=list( data.get( self._sortedDictKeys, data.keys() ) )
           
       """print(data)
       cfg_global=data["global"]
       keys = list( cfg_global.get( self._sortedKeys, data.keys() ) )
       """
       if not root:
          root=self.root
        
       for k in keys:
           v = data[k]
           child=None
           ctrl=None
           item_data[k]=dict()
           #logger.info("key: {} value. {} type: {} ".format(k,v,type(v)))
        
           #--- type bool
           if isinstance(v,(dict)):
               #--- ToDo call recursive; do not expand only OnClick
               kk=list(v.keys())
               #kk.sort()
               """if k=="info":
                   continue
               else:"""
               if "sorted_keys" in kk:
                  kk=v.get("sorted_keys")
               child = self.AppendItem(root,"{}".format(k),ct_type=0)
               self.SetPyData(child,data[k])
               self._init_tree_ctrl(data=data[k],root=child,item_data=item_data[k])
               """child = self.AppendItem(child,"{}".format(kk[0]),ct_type=0)
               self.SetPyData(child,v[kk[0]])"""
               continue
           
           elif isinstance(v,(bool)):
               ctrl=wx.CheckBox(self,-1,label=k,name="bool")
               ctrl.SetValue(v)
               child = self.AppendItem(root,"{}".format(k),wnd=ctrl)
               self.SetItemBold(child,True)
        
           elif isinstance(v,(str)):
               style = wx.TE_LEFT
               ctrl = wx.TextCtrl(self,-1,style=style,value=v,name="str")
               sz = ctrl.GetSizeFromTextSize(ctrl.GetTextExtent("W" * txt_size))
               ctrl.SetInitialSize(sz)
            
               child = self.AppendItem(root,"{}".format(k),wnd=ctrl,ct_type=0)
        
           #--- type list => make TextCtrl + clickOn show List + add,delete like PropertyGrid
           elif isinstance(v,(list)):
               
               if k=="wx_keys" or k=="sorted_keys":
                   pass
               else:
               
                   l = [str(x) for x in v]  # make list.items to str
                   style= wx.TE_MULTILINE|wx.TE_RIGHT
                   style = wx.TE_LEFT
                   ctrl = wx.TextCtrl(self,-1,style=style,value=self._list_seperator.join(l),name="list")
                   sz = ctrl.GetSizeFromTextSize(ctrl.GetTextExtent("W" * txt_size))
                   ctrl.SetInitialSize(sz)
                   ctrl.SetToolTip(wx.ToolTip(self._list_seperator.join(l)))
                   
                   child = self.AppendItem(root,"{}".format(k),wnd=ctrl)
        
           elif isinstance(v,(int)):
               ctrl=wx.SpinCtrl(self,-1,"",(30,50),name="int")
               ctrl.SetRange(0,10000)
               ctrl.SetValue(v)
               child=self.AppendItem(root,"{}".format(k),wnd=ctrl)
               self.SetItemBold(child,True)
        
           elif isinstance(v,(float)):
               value2=str(v)
               ctrl=wx.SpinCtrlDouble(self,min=0.,max=10000.,value=value2,inc=0.1,name="float")
               child=self.AppendItem(root,"{}".format(k),wnd=ctrl)
               
           item_data[k]=ctrl
           self.SetPyData(child,data[k])
           
   def update_info(self):
       self._info["user"]=getpass.getuser()
       now=datetime.datetime.now()
       dt=now.strftime('%Y-%m-%d')+" "+now.strftime('%H:%M')
       self._info["time"]=dt
       self._info["version"]=platform.python_version()
       return self._info
       
   def update_used_dict(self):
      self._used_dict=self.GetData()
       
   def _wx_init(self,**kwargs):
       data = kwargs.get("data",{})
       #keys = list(data.keys())
       #keys.sort()
       #print(data)
       cfg_global=data["global"]
       keys = list( cfg_global.get( self._sortedKeys, data.keys() ) )
       #logger.info(data)
       
       self.root = self.AddRoot(kwargs.get("root","Tree Ctrl") )
       #keys= list(data.keys())
       #keys.sort()
       item_data=dict()
       item_data["info"]=data.get("info")
       self._info=data.get("info")
       keys.remove("info")
       for k in keys:
           """if (k=="info"):
               self._info=data.get(k)
               print(self._info)
               print(item_data["info"])
               keys.remove("info")
               print(keys)
               #keys.remove("info")
               pass
           else:"""
           d = data.get(k)
           if isinstance(d,(dict)):
               item_data[k]=dict()
               child = self.AppendItem(self.root,"{}".format(k))
           #self.SetPyData(child,data[k])
               self._init_tree_ctrl( data=d ,root=child,item_data=item_data[k])
       self._item_data=item_data
       self._item_data.pop("info",None)
        
       self.Expand(self.root)


class CtrlPanel(wx.Panel):
    def __init__(self,parent,**kwargs):
        super().__init__(parent)
        # self._CfgTreeCtrl = None
        self.SetName(kwargs.get("name","test"))
        self._CfgTreeCtrl = None
        self._wx_init(**kwargs)
        self._ApplyLayout()
    
    @property
    def cfg(self): return self._CFG
    
    @property
    def ConfigTreeCtrls(self): return self._CfgTreeCtrls
    
    """def get_parameter(self):
        cfg=dict()
        for k in keys:
           v = data[k]
           #logger.info("key: {} value. {} type: {} ".format(k,v,type(v)))
        
           #--- type bool
           if isinstance(v,(dict)):
               pass
           
           elif isinstance(v,(bool)):
               pass
        
           elif isinstance(v,(str)):
               pass
        
           #--- type list => make TextCtrl + clickOn show List + add,delete like PropertyGrid
           elif isinstance(v,(list)):
               pass
        
           elif isinstance(v,(int)):
               pass
        
           elif isinstance(v,(float)):
               pass
        return cfg"""
    
    def _wx_init(self,**kwargs):
        self.SetBackgroundColour(wx.GREEN)
        #--- load cfg
        self._CFG = JuMEG_CONFIG_YAML_BASE(**kwargs)
        self._CFG.update(**kwargs)
        
        #self.cfg.info()
       
       #--- init TreeCtrl
        #for k in self.cfg.GetDataDict().keys():
        #    root= k #"noise_reducer"
        #    self._CfgTreeCtrls.append( MyTreeCtrl(self,root=root, data=self.cfg.GetDataDict(key=root) ) )
        root = "JuMEG Config"  #"noise_reducer"
        print(self.cfg.GetDataDict())
        self._CfgTreeCtrl=MyTreeCtrl(self,root=root,data=self.cfg.GetDataDict())

        #--- init show button
        #fehlerhaft show button
        self._bt_open = wx.Button(self,label="Open",name=self.GetName()+".BT.OPEN")
        self._bt_info  = wx.Button(self,label="Show", name=self.GetName()+".BT.SHOW")
        self._bt_save  = wx.Button(self,label="Save", name=self.GetName()+".BT.SAVE")
        self._bt_update =wx.Button(self,label="Update", name=self.GetName()+".BT.UPDATE")
        self._bt_close = wx.Button(self,label="Close",name=self.GetName()+".BT.CLOSE")
        
        self.Bind(wx.EVT_BUTTON,self.ClickOnButton)
    
    def _ApplyLayout(self):
        LEA = wx.LEFT | wx.EXPAND | wx.ALL
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        #---
        st1 = wx.StaticLine(self)
        st1.SetBackgroundColour("GREY85")
        st2 = wx.StaticLine(self)
        st2.SetBackgroundColour("GREY80")
        
        vbox.Add(st1,0,LEA,1)
        
        #if self.ConfigTreeCtrl:
        #   vbox.Add(self.ConfigTreeCtrl,1,LEA,1)
        vbox.Add(self._CfgTreeCtrl,1,LEA,1)
        st = wx.StaticLine(self)
        st.SetBackgroundColour("GREY85")
        vbox.Add(st,0,LEA,1)
            
       #--- buttons
        hbox= wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self._bt_close,0,LEA,2)
        hbox.Add((0,0),1,LEA,2)
        hbox.Add(self._bt_update,0,LEA,2)
        hbox.Add(self._bt_info,0,LEA,2)
        vbox.Add(hbox,0,LEA,2)
        hbox.Add(self._bt_save,0,LEA,2)
        hbox.Add(self._bt_open,0,LEA,2)
      
        self.SetAutoLayout(True)
        self.SetSizer(vbox)
        self.Fit()
        self.Layout()
   
    def OnSaveAs(self, event=None):
        with wx.FileDialog(self, "Save yaml file", wildcard="yaml files (*.yaml)|*.yaml",
                          style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
             fileDialog.SetDirectory(os.path.dirname(self.cfg.filename))
             if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind
   
           # save the current contents in the file
             pathname = fileDialog.GetPath()
             if not pathname.endswith(".yaml"):
                pathname+=".yaml"
             try:
                 data = self._CfgTreeCtrl._used_dict
                 print(pathname)
                 self.cfg.save_cfg(fname=pathname,data=data)
             except IOError:
                 wx.LogError("Cannot save current data in file '%s'." % pathname)
                 
    def OnOpen(self, event=None):

       """if self.contentNotSaved:
           if wx.MessageBox("Current content has not been saved! Proceed?", "Please confirm",
                            wx.ICON_QUESTION | wx.YES_NO, self) == wx.NO:
               return"""
   
       # otherwise ask the user what new file to open
       with wx.FileDialog(self, "Open yaml file", wildcard="yaml files (*.yaml)|*.yaml",
                          style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
           
           #fileDialog.SetDirectory(os.path.dirname(self.cfg.filename))
           if fileDialog.ShowModal() == wx.ID_CANCEL:
               return     # the user changed their mind
   
           # Proceed loading the file chosen by the user
           pathname = fileDialog.GetPath()
           try:
               with open(pathname, 'r') as file:
                  if wx.MessageBox("Do you want to save?", "Please confirm",
                            wx.ICON_QUESTION | wx.YES_NO, self) == wx.YES:
                     self._CfgTreeCtrl.update_info()
                     self._CfgTreeCtrl.update_used_dict()
                     self.OnSaveAs()
           except IOError:
               wx.LogError("Cannot open file '%s'." % pathname)
    
    def ClickOnButton(self,evt):
        obj = evt.GetEventObject()
        if obj.GetName() == self.GetName()+".BT.SHOW":
            print(obj.GetName())
            print(self.GetName())
            self.cfg.info()
        elif obj.GetName().endswith('.BT.SAVE'):
            print("saved")
            #print(self._CfgTreeCtrl.GetData())
            self._CfgTreeCtrl.update_info()
            self._CfgTreeCtrl.update_used_dict()
            self.OnSaveAs()
            #print(yaml.dump(self._CfgTreeCtrl._used_dict,explicit_start=False))
            #print(yaml.safe_dump(self._CfgTreeCtrl._used_dict))
            
            
            #print(self._CfgTreeCtrl._info)
            #cfg=self.ConfigTreeCtrls.get_parameter()
            #print(cfg)
        elif obj.GetName().endswith(".BT.UPDATE"):
            print("updated")
            self._CfgTreeCtrl.update_used_dict()
        elif obj.GetName().endswith(".BT.OPEN"):
           self.OnOpen()
        else:
            evt.Skip()

class MainWindow(wx.Frame):
  def __init__(self, parent, title, **kwargs):
    wx.Frame.__init__(self, parent, -1,title=title)
    self._wx_init(**kwargs)
   
  def _update_from_kwargs(self,**kwargs):
      pass
  
  def _wx_init(self,**kwargs):
        w,h = wx.GetDisplaySize()
        self.SetSize(w/4.0,h/3.0)
        self.Center()
        
        self._update_from_kwargs(**kwargs)
      #--- init STB in a new CLS
        self._STB = self.CreateStatusBar()
        
        self._PNL = CtrlPanel(self,**kwargs)
        
        self.Bind(wx.EVT_BUTTON,self.ClickOnButton)
        self.Bind(wx.EVT_CLOSE,self.ClickOnClose)
      
  def ClickOnButton(self,evt):
      obj = evt.GetEventObject()
      if obj.GetName().endswith("CLOSE"):
        self.Close()
      else:
          evt.Skip()

  def ClickOnClose(self,evt):
      #--- place to clean your stuff
      evt.Skip()
     
#---
def run(opt):
    if opt.debug:
        opt.verbose = True
        opt.debug = True
        opt.path = "./config/"
        opt.config = "test_config.yaml"
    
    app = wx.App()
    
    if opt.path:
        cfg = os.path.join((opt).path,opt.config)
    else:
        cfg = opt.config
    
    frame = MainWindow(None,'JuMEG Config',config=cfg,verbose=opt.verbose,debug=opt.debug)
    frame.Show()
    
    app.MainLoop()

#----
def get_args(argv):
    info_global = """
     JuMEG Config GUI Start Parameter

     ---> view time series data FIF file
      jumeg_cfg_gui01.py --config=test_config.yaml --path=./config -v

    """
    
    parser = argparse.ArgumentParser(info_global)
    
    parser.add_argument("-p","--path",help="config file path")
    parser.add_argument("-cfg","--config",help="config file name")
    
    parser.add_argument("-v","--verbose",action="store_true",help="verbose mode")
    parser.add_argument("-d","--debug",action="store_true",help="debug mode")
    
    #--- init flags
    # ck if flag is set in argv as True
    # problem can not switch on/off flag via cmd call
    opt = parser.parse_args()
    for g in parser._action_groups:
        for obj in g._group_actions:
            if str(type(obj)).endswith('_StoreTrueAction\'>'):
                if vars(opt).get(obj.dest):
                    opt.__dict__[obj.dest] = False
                    for flg in argv:
                        if flg in obj.option_strings:
                            opt.__dict__[obj.dest] = True
                            break
    
    return opt,parser


#=========================================================================================
#==== MAIN
#=========================================================================================
if __name__ == "__main__":
    opt,parser = get_args(sys.argv)
    
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(-1)
    
    jumeg_logger.setup_script_logging(name=sys.argv[0],opt=opt,logger=logger)
    
    run(opt)

