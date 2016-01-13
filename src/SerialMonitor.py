#!/usr/bin/python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------#
#                                                                       #
# This file is part of the web2board project                            #
#                                                                       #
# Copyright (C) 2015 Mundo Reader S.L.                                  #
#                                                                       #
# Date: August 2015                                                     #
# Author: Irene Sanz Nieto <irene.sanz@bq.com>                          #
#                                                                       #
# -----------------------------------------------------------------------#

import os
import sys
import time
import wx
import logging

import serial

from libs import utils
from libs.CompilerUploader import getCompilerUploader

log = logging.getLogger(__name__)
reload(sys)
sys.setdefaultencoding("utf-8")


class SerialConnection:
    def __init__(self, port):
        self.serial = serial.Serial()
        self.serial.port = port
        self.serial.baudrate = 9600
        self.serial.open()

    def getData(self):
        if self.serial.isOpen():
            out = ''
            try:
                while self.serial.inWaiting() > 0:
                    out += self.serial.read(1)
                if out != '':
                    return out
            except Exception as e:
                log.critical("error getting data {}".format(e), exc_info=1)

    def write(self, data):
        self.serial.write(data.encode())

    def changeBaudRate(self, value):
        self.serial.close()
        self.serial.baudrate = value
        self.serial.open()

    def close(self):
        self.serial.close()


class SerialMonitorUI(wx.Dialog):
    def __init__(self, parent, port=None):
        if port is None:
            getCompilerUploader().setBoard("uno")
            port = getCompilerUploader().getPort()

        style = wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX | wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX
        super(SerialMonitorUI, self).__init__(parent, title='bitbloq\'s Serial Monitor', size=(500, 500), style=style)
        self.serialConnection = SerialConnection(port)
        # Timer
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.timer)
        self.timer.Start(100)
        self.newLine = ''
        self.Pause = False
        self.lastPause = False
        self.charCounter = 0

        # Elements
        self.inputTextBox = wx.TextCtrl(self, size=(300, 10))
        self.response = wx.TextCtrl(self, size=(10, 250), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_AUTO_URL)
        # self.response.SetMaxLength(3)
        self.sendButton = wx.Button(self, label='Send', style=wx.ALIGN_RIGHT)
        self.pauseButton = wx.Button(self, label='Pause', style=wx.ALIGN_RIGHT)
        self.clearButton = wx.Button(self, label='Clear', style=wx.ALIGN_RIGHT)

        baudRates = ['300', '1200', '2400', '4800', '9600', '14400', '19200', '28800', '38400', '57600', '115200']
        self.dropdown = wx.ComboBox(self, 0, '9600', (0, 0), wx.DefaultSize, baudRates, wx.CB_DROPDOWN)

        # Events
        self.inputTextBox.Bind(wx.EVT_CHAR, self.onKeyPress)
        self.sendButton.Bind(wx.EVT_BUTTON, self.onSend)
        self.pauseButton.Bind(wx.EVT_BUTTON, self.onPause)
        self.clearButton.Bind(wx.EVT_BUTTON, self.onClear)
        self.dropdown.Bind(wx.EVT_COMBOBOX, self.onBaudRateChanged)

        # Layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.inputTextBox, 1, wx.ALL ^ wx.CENTER | wx.EXPAND, 12)
        hbox.Add(self.sendButton, 0, wx.ALL ^ wx.ALIGN_RIGHT, 12)
        vbox.Add(hbox, 0, wx.EXPAND, 12)
        vbox.Add(self.response, 1, wx.ALL ^ wx.CENTER | wx.EXPAND, 12)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.pauseButton, 0, wx.ALL ^ wx.ALIGN_LEFT, 12)
        hbox1.Add(self.clearButton, 0, wx.ALL ^ wx.CENTER | wx.EXPAND, 12)
        hbox1.Add((0, 0), 1, wx.EXPAND)
        hbox1.Add(self.dropdown, 0, wx.ALL ^ wx.ALIGN_RIGHT, 12)
        vbox.Add(hbox1, 0, wx.EXPAND, 12)
        self.SetSizer(vbox)
        # self.ShowModal()
        self.Bind( wx.EVT_CLOSE, self.ParentFrameOnClose)
        self.isClosed = False


    def ParentFrameOnClose(self, event):
        self.serialConnection.close()
        self.isClosed = True
        time.sleep(3.0)  # todo iter ports untill it is open again
        self.DestroyChildren()
        self.Destroy()

    def onKeyPress(self, event):
        if event.GetKeyCode() != wx.WXK_RETURN:
            event.Skip()
            return
        else:
            self.onSend(event)

    def logText(self, message):
        if message is not None:
            if '\n' in message:
                self.charCounter = 0
            else:
                self.charCounter += 1

            if self.response.GetNumberOfLines() >= 800 or self.charCounter > 300:
                self.response.SetValue(message)
                self.charCounter = 0
            else:
                self.response.AppendText(message)

    def update(self, event):
        if self.Pause and not self.lastPause:
            self.logText('\n*** SERIAL MONITOR PAUSED ***\n\n')
            self.lastPause = True
        elif not self.Pause:
            try:
                self.logText(self.serialConnection.getData())
            except:
                pass
            self.lastPause = False

    def onSend(self, event):
        message = self.inputTextBox.GetValue()
        # self.logText(message)
        self.serialConnection.write(message)
        self.inputTextBox.SetValue('')

    def onPause(self, event):
        if self.pauseButton.GetLabel() == 'Pause':
            self.pauseButton.SetLabel('Continue')
            self.Pause = True
        else:
            self.pauseButton.SetLabel('Pause')
            self.Pause = False

    def onClear(self, event):
        self.response.SetValue('')
        self.inputTextBox.SetValue('')
        self.charCounter = 0

    def onBaudRateChanged(self, event):
        self.serialConnection.changeBaudRate(self.dropdown.GetValue())




if __name__ == "__main__":
    # app = wx.App(redirect=True)
    app = wx.App()
    serialMonitor = SerialMonitorUI(None, port)
    serialMonitor.Show()
    app.MainLoop()
