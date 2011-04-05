#!/usr/bin/python
#
# File      :  XenBackupGui.py
# Project   :  XenServer Live VMs Backup
# Author    :  Emiliano Giovannetti
#
# Created   :  march'11
#
# Description:
#   Project's function library
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import XenBackupGui_xrc
import datetime, wx, XenBackup, thread
import wx.lib.masked as masked
from string import Template
import wx.xrc as xrc

"""
Possible status bar left messages 
"""
statusLeftText = {'taggedVM': ' tagged virtual machines will be backed up',
                    'singleVM': ' will be backed up',
                    'noVM': 'Select a virtual machine to backup',
                    'backupVMs': 'Backing up ', 
                }     
                

"""
Possible status bar rigth messages 
"""           
statusRightText = {'notConnected': 'Not connected',
                    'connected': 'Connected to '
                }

"""
Possible backup button labels 
"""
backupButtonLabel = {'backup': 'Backup!',
                        'abort': 'Abort'
                    }

"""
Possible backup button tool tips 
"""                    
backupButtonTooltip = {'backup': 'Start backup process',
                        'abort': 'Abort backup process'
                    }
                    
"""
Possible host button labels 
"""                    
hostButtonLabel = {'connect': 'Connect to Pool...',
                    'disconnect': 'Disconnect from Pool...'
                    }                    
                
"""
IpAddrCtrl's name and id
"""                
ipAddrCtrl = {'name': 'ipAddrCtrl',
                'id': -1
            }

class xrcmainFrameSub(XenBackupGui_xrc.xrcmainFrame):
    """ 
This class represents the main GUI frame
    """
    
    def __init__(self):
        """ 
    xrcmainFrameSub Constructor:
    
    1) create parent frame
    2) create XenServer object
    3) setup event handler for EVT_RESULT event and initialize members
    4) set IpAddrCtrl instead of simple TextCtrl
    5) set default status bar appereance
    6) set backup button mouse events
    7) show up
        """
        # 1)
        XenBackupGui_xrc.xrcmainFrame.__init__(self, parent = None)
        # 2)
        try:
            self.xen = XenBackup.XenServer('XenBackup.cfg', self)
        except Exception, e:
            wx.MessageBox('Error creating XenServer object:\n %s ' % str(e))
            raise        
        # 3)
        XenBackup.EVT_RESULT(self, self.OnTaskEvent)
        self.isLogged = False
        self.vmId = datetime.datetime.today().strftime("%a")
        self.vmList = None
        self.vmCount = 0
        self.vmLeft = 0
        self.exportTaskVM = ''
        self.statusBeforeBackup = ''
        # 4)        
        self.ipAddrCtrl = masked.IpAddrCtrl(self, id = ipAddrCtrl['id'], name = ipAddrCtrl['name'])
        XenBackupGui_xrc.get_resources().AttachUnknownControl('hostTextCtrl', self.ipAddrCtrl, self)
        self.Bind(wx.EVT_TEXT, self.OnText_hostTextCtrl, id = ipAddrCtrl['id'])
        # 5)
        xrc.XRCCTRL(self, 'mainStatus').SetStatusText(statusRightText['notConnected'], 1)
        xrc.XRCCTRL(self, 'mainStatus').SetStatusText(self.vmId + \
            statusLeftText['taggedVM'], 0)
        # 6)
        xrc.XRCCTRL(self, 'backupButton').Bind(wx.EVT_ENTER_WINDOW, self.OnBackupButtonMouseOver)
        xrc.XRCCTRL(self, 'backupButton').Bind(wx.EVT_LEAVE_WINDOW, self.OnBackupButtonMouseLeave)
        # 7)
        self.Show()
        
    def OnTaskEvent(self, evt):
        """ 
    EVT_RESULT event handler:
    
    1) if backup process has started:
        1.1) set virtual machines to do an done
        1.2) set backup button lable and tool tip
        1.3) disable all control except backup button 
        1.4) save mainStatus' left panel
    2) if backup process has finished:
        2.1) restore backup button label and tool tip
        2.2) enable all controls previously disabled
        2.3) restore mainStatus' left panel
    3) if single exporting task has started:
        3.1) save current exporting task reference
    4) if single exporting task has finished:
        4.1) decrement virtual machine to be done count
        4.2) reset current exporting task reference
    5) if single exporting task is in progress:
        5.1) calculate partial and total progress and show them on mainStatus' left panel 
        """        
        # 1)
        if evt.data['name'] == XenBackup.BACKUP_EVENTS['start_backup']:
            # 1.1)
            self.vmLeft = len(self.xen.config['vm'])
            self.vmCount = self.vmLeft
            # 1.2) 
            xrc.XRCCTRL(self, 'backupButton').SetLabel(backupButtonLabel['abort'])
            xrc.XRCCTRL(self, 'backupButton').SetToolTip(wx.ToolTip(backupButtonTooltip['abort']))
            # 1.3)
            self.toggleAllControlEnable(False)
            xrc.XRCCTRL(self, 'backupButton').Enable(True)
            # 1.4)
            self.statusBeforeBackup = xrc.XRCCTRL(self, 'mainStatus').GetStatusText(0)
        # 2)
        elif evt.data['name'] == XenBackup.BACKUP_EVENTS['end_backup']:
            # 2.1)
            xrc.XRCCTRL(self, 'backupButton').SetLabel(backupButtonLabel['backup'])
            xrc.XRCCTRL(self, 'backupButton').SetToolTip(wx.ToolTip(backupButtonTooltip['backup']))
            # 2.2)
            self.toggleAllControlEnable(True)
            xrc.XRCCTRL(self, 'backupButton').Enable(True)
            # 2.3)
            xrc.XRCCTRL(self, 'mainStatus').SetStatusText(self.statusBeforeBackup, 0)   
        # 3)
        elif evt.data['name'] == XenBackup.BACKUP_EVENTS['start_task']:
            # 3.1)
            self.exportTaskVM = evt.data['task_vm']            
        # 4)
        elif evt.data['name'] == XenBackup.BACKUP_EVENTS['end_task']:
            # 4.1)
            self.vmLeft -= 1
            # 4.2)
            self.exportTaskVM = None
        # 5)
        elif evt.data['name'] == XenBackup.BACKUP_EVENTS['progress_task']:
            # 5.1)
            partial = int(evt.data['progress'] * 100)
            total = int((evt.data['progress'] / self.vmLeft) + \
                ((self.vmCount - self.vmLeft) / self.vmCount)) * 100
            text = Template('[$status] $backupVMs$vmName: $partial% (Total: $total%)')
            status = text.safe_substitute(status = evt.data['status'], \
                                    backupVMs = statusLeftText['backupVMs'], \
                                    vmName = evt.data['original_vm'], \
                                    partial = str(partial), \
                                    total = str(total))                  
            xrc.XRCCTRL(self, 'mainStatus').SetStatusText(status, 0)

    def OnButton_hostButton(self, evt):
        """ 
    hostButton event handler:
    
    1) If not already logged:
        1.1) login to specified host and retreive SR list
        1.2) set controls appereance
    2) if already logged:
        2.1) logout
        2.2) set controls appereance
        """  
        # 1)
        if not self.isLogged:  
            wx.SafeYield()
            wx.BeginBusyCursor()                        
            # 1.1)
            try:
                self.isLogged = self.xen.login(self.ipAddrCtrl.GetAddress())
                xrc.XRCCTRL(self, 'srCombo').AppendItems(self.xen.get_sr_list())
            except Exception, e:
                wx.MessageBox('Error retreiving SR list:\n %s ' % str(e))
            finally:   
                wx.SafeYield()
                wx.EndBusyCursor()
                # 1.2)
                if self.isLogged:
                    try:
                        xrc.XRCCTRL(self, 'mainStatus').SetStatusText(statusRightText['connected'] \
                            + self.xen.get_pool_name(), 1)
                    except Exception, e:
                        wx.MessageBox('Error retreiving Pool name:\n %s ' % str(e))
                    xrc.XRCCTRL(self, 'srText').Enable(self.isLogged)
                    xrc.XRCCTRL(self, 'srCombo').Enable(self.isLogged)
                    xrc.XRCCTRL(self, 'vmEnableText').Enable(self.isLogged)
                    xrc.XRCCTRL(self, 'vmEnableCheck').Enable(self.isLogged)
                    xrc.XRCCTRL(self, 'hostButton').SetLabel(hostButtonLabel['disconnect'])
                    xrc.XRCCTRL(self, 'hostTextCtrl').Enable(not self.isLogged)
        # 2)
        else:            
            # 2.1)
            self.isLogged = not self.xen.logout()
            # 2.3)
            if not self.isLogged:
                xrc.XRCCTRL(self, 'mainStatus').SetStatusText(statusRightText['notConnected'], 1)
                xrc.XRCCTRL(self, 'srText').Enable(self.isLogged)
                xrc.XRCCTRL(self, 'srCombo').Clear()
                xrc.XRCCTRL(self, 'srCombo').Append('')
                xrc.XRCCTRL(self, 'srCombo').Select(0)
                xrc.XRCCTRL(self, 'srCombo').Enable(self.isLogged)
                self.OnCombobox_srCombo(wx.EVT_COMBOBOX)
                xrc.XRCCTRL(self, 'vmEnableText').Enable(self.isLogged)
                xrc.XRCCTRL(self, 'vmEnableCheck').SetValue(wx.CHK_UNCHECKED)
                xrc.XRCCTRL(self, 'vmEnableCheck').Enable(self.isLogged)
                self.OnCheckbox_vmEnableCheck(wx.EVT_CHECKBOX)
                xrc.XRCCTRL(self, 'hostButton').SetLabel(hostButtonLabel['connect'])
                xrc.XRCCTRL(self, 'hostTextCtrl').Enable(not self.isLogged)
                xrc.XRCCTRL(self, 'hostTextCtrl').Clear()
                xrc.XRCCTRL(self, 'backupButton').Enable(self.isLogged)
        
    def OnText_hostTextCtrl(self, evt):
        """ 
    hostTextCtrl event handler:
        """
        parts = self.ipAddrCtrl.GetAddress().split('.')
        for i in range(len(parts)): 
            isEmpty = len(parts[i]) == 0
            if isEmpty: 
                break
        xrc.XRCCTRL(self, 'hostButton').Enable(not isEmpty)
        
    def OnCombobox_srCombo(self, evt):
        """ 
    srCombo event handler:
        """        
        xrc.XRCCTRL(self, 'backupButton').Enable(self.enableBackupButton())
        
    def OnCheckbox_vmEnableCheck(self, evt):
        """ 
    vmEnableCheck event handler:
        """        
        try:
            isChecked = xrc.XRCCTRL(self, 'vmEnableCheck').GetValue()
            if not isChecked:
                xrc.XRCCTRL(self, 'vmTextCtrl').Clear()            
                xrc.XRCCTRL(self, 'mainStatus').SetStatusText(self.vmId + \
                    statusLeftText['taggedVM'], 0)
            else:
                xrc.XRCCTRL(self, 'mainStatus').SetStatusText(statusLeftText['noVM'], 0)                                    
            xrc.XRCCTRL(self, 'vmEnableText').Enable(isChecked)
            xrc.XRCCTRL(self, 'vmTextCtrl').Enable(isChecked)
            xrc.XRCCTRL(self, 'vmText').Enable(isChecked)
            xrc.XRCCTRL(self, 'vmButton').Enable(isChecked)
        finally:
            xrc.XRCCTRL(self, 'backupButton').Enable(self.enableBackupButton())
    
    def OnText_vmTextCtrl(self, evt):
        """ 
    vmTextCtrl event handler:
    
    1) if no virtual machine is specified:
        1.1) select all virtual machines tagged as current weekday
    2) if a virtual machine is specified select it for backup
        """      
        # 1)
        if len(xrc.XRCCTRL(self, 'vmTextCtrl').GetValue()) == 0:
            # 1.1)
            self.vmId = datetime.datetime.today().strftime("%a")
        # 2)
        else:
            self.vmId = xrc.XRCCTRL(self, 'vmTextCtrl').GetValue() 
            xrc.XRCCTRL(self, 'mainStatus').SetStatusText(self.vmId + \
                statusLeftText['singleVM'], 0)
    
    def OnButton_vmButton(self, evt):
        """ 
    vmButton event handler:
    
    1) get Pool's virtual machine list
    2) create virtual machines dialog
    3) add virtual machine list to the tree list control grouped by hostname
    4) enable backup button
        """         
        wx.SafeYield()
        wx.BeginBusyCursor()
        # 1)
        try:
            if self.vmList is None:
                self.vmList = self.xen.get_vm_list()
        except Exception, e:
            wx.MessageBox('Error retreiving VM list by host:\n %s ' % str(e))
        finally:
            wx.SafeYield()
            wx.EndBusyCursor()         
        # 2)
        vmDialog = xrcvmDialogSub(self)
        # 3)
        try:
            vmTree = xrc.XRCCTRL(vmDialog, 'vmTreeList')
            vmTree.AddRoot(self.xen.get_pool_name())
            for host, vms in self.vmList.iteritems():
                h = vmTree.AppendItem(vmTree.GetRootItem(), host)
                for vm in vms:
                    vmTree.AppendItem(h, vm)
            vmDialog.ShowModal()          
        finally:
            # 4)
            xrc.XRCCTRL(self, 'backupButton').Enable(self.enableBackupButton())
            vmDialog.Destroy()        
        
    def OnBackupButtonMouseOver(self, evt):
        """ 
    backupButton mouseover event handler:
        """         
        if xrc.XRCCTRL(self, 'backupButton').GetLabel() == backupButtonLabel['abort']:
            wx.SafeYield()
            wx.EndBusyCursor() 
        
    def OnBackupButtonMouseLeave(self, evt):
        """ 
    backupButton mouseleave event handler:
        """         
        if xrc.XRCCTRL(self, 'backupButton').GetLabel() == backupButtonLabel['abort']:
            wx.SafeYield()
            wx.BeginBusyCursor() 
        
    def OnButton_backupButton(self, evt):
        """ 
    backupButton event handler:
    
    1) if backup:
        1.1) start backup process on a different thread
        1.2) temporary disable backup button (waiting for EVT_RESULT)
    2) if abort:
        2.1) delete export task
        2.1) temporary disable backup button (waiting for EVT_RESULT)
        """          
        # 1)
        if xrc.XRCCTRL(self, 'backupButton').GetLabel() == backupButtonLabel['backup']:
            sr = xrc.XRCCTRL(self, 'srCombo').GetValue()
            # 1.1)
            thread.start_new_thread(self.xen.backup, (self.vmId, sr))
            # 1.2)
            xrc.XRCCTRL(self, 'backupButton').Enable(False)
        # 2)
        else:
            # 2.1)
            self.xen.delete_task(self.exportTaskVM)
            # 2.1)
            xrc.XRCCTRL(self, 'backupButton').Enable(False)
        
    def OnButton_quitButton(self, evt):
        """ 
    quitButton event handler:
        """         
        ret  = wx.MessageBox('Are you sure to quit?', 'Question', wx.YES_NO | wx.CENTRE | wx.NO_DEFAULT, self)
        if ret == wx.YES:
            if self.isLogged:
                self.xen.logout()
            self.Close()
        
    def toggleAllControlEnable(self, enable):
        """
    Disable all controls but one
        """        
        xrc.XRCCTRL(self, 'hostTextCtrl').Enable(enable)
        xrc.XRCCTRL(self, 'hostButton').Enable(enable)
        xrc.XRCCTRL(self, 'srCombo').Enable(enable)
        xrc.XRCCTRL(self, 'vmEnableCheck').Enable(enable)
        xrc.XRCCTRL(self, 'vmTextCtrl').Enable(enable)
        xrc.XRCCTRL(self, 'vmButton').Enable(enable)
        xrc.XRCCTRL(self, 'quitButton').Enable(enable)        
        wx.SafeYield()
        if enable:
            wx.EndBusyCursor()
        else:
            wx.BeginBusyCursor()            
        
    def enableBackupButton(self):
        """
    Return True if backup button can be enabled
        """
        isFullSR = (len(xrc.XRCCTRL(self, 'srCombo').GetValue()) != 0)
        isCheckedVM = xrc.XRCCTRL(self, 'vmEnableCheck').GetValue()
        isFullVM = (len(xrc.XRCCTRL(self, 'vmTextCtrl').GetValue()) != 0)
        if (isFullSR and isCheckedVM and isFullVM) or (isFullSR and (not(isCheckedVM)) and (not(isFullVM))):
            return True
        else:
            return False

class xrcvmDialogSub(XenBackupGui_xrc.xrcvmDialog):
    """ 
This class represents the virtual machines selection's dialog
    """
        
    def __init__(self, parent):
        """ 
    xrcvmDialogSub Constructor
        """        
        self.myParent = parent
        self.selection = None
        XenBackupGui_xrc.xrcvmDialog.__init__(self, parent)
        
    def OnTree_sel_changed_vmTreeList(self, evt):
        """ 
    vmTreeList selection change event handler:
        """         
        selection = evt.GetItem()
        isLeaf = not xrc.XRCCTRL(self, 'vmTreeList').ItemHasChildren(selection)
        xrc.XRCCTRL(self, 'OkButton').Enable(isLeaf)
        if isLeaf:
            self.selection = selection
        else:
            self.selection = None
            
    def OnButton_CancelButton(self, evt):
        """ 
    cancelButton event handler:
        """         
        self.EndModal(wx.ID_ABORT)
        
    def OnButton_OkButton(self, evt):
        """ 
    okButton event handler:
        """         
        if self.selection is not None:
            selectionText = xrc.XRCCTRL(self, 'vmTreeList').GetItemText(self.selection)
            xrc.XRCCTRL(self.myParent, 'vmTextCtrl').SetValue(selectionText)
            self.EndModal(wx.ID_OK)
        else:
            self.EndModal(wx.ID_ABORT)
    
if __name__ == "__main__":
    app = wx.App(False)
    frame = xrcmainFrameSub()
    app.MainLoop()
    