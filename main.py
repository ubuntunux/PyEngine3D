#!/usr/bin/env python
# -*- coding: utf-8 -*-

""""
Copyright (c) 2015, ubuntunux
All rights reserved.

License:
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

__version__ = 0.9
"""

import sys
import os
import time
from multiprocessing import Process

import OpenGL
OpenGL.ERROR_CHECKING = True
OpenGL.ERROR_LOGGING = True
OpenGL.FULL_LOGGING = False
OpenGL.ALLOW_NUMPY_SCALARS = True

from PyEngine3D.Common import CustomQueue, CustomPipe
from PyEngine3D.App import CoreManager
from PyEngine3D.Utilities import AutoEnum, Config


class GUIEditor(AutoEnum):
    CLIENT_MODE = ()
    QT = ()
    TKINTER = ()


def run(editor=GUIEditor.QT, project_filename=""):
    appCmdQueue = None
    uiCmdQueue = None
    pipe1, pipe2 = None, None
    editor_process = None

    config = Config("config.ini")

    # load last project file
    if "" == project_filename and config.hasValue('Project', 'recent'):
        last_project = config.getValue('Project', 'recent')
        if os.path.exists(last_project):
            project_filename = last_project

    # other process - GUIEditor
    if editor != GUIEditor.CLIENT_MODE:
        appCmdQueue = CustomQueue()
        uiCmdQueue = CustomQueue()
        pipe1, pipe2 = CustomPipe()

        # Select GUI backend
        if editor == GUIEditor.QT:
            from PyEngine3D.UI.QT.MainWindow import run_editor
        elif editor == GUIEditor.TKINTER:
            from PyEngine3D.UI.TKInter.MainWindow import run_editor
        editor_process = Process(target=run_editor, args=(project_filename, uiCmdQueue, appCmdQueue, pipe2))
        editor_process.start()

    # Client process
    coreManager = CoreManager.instance()
    result = coreManager.initialize(appCmdQueue, uiCmdQueue, pipe1, project_filename)
    if result:
        coreManager.run()
        next_next_open_project_filename = coreManager.get_next_open_project_filename()
    else:
        next_next_open_project_filename = ""

    # GUI Editor process end
    if editor_process:
        editor_process.join()

    return next_next_open_project_filename  # reload or not


if __name__ == "__main__":
    editor = GUIEditor.TKINTER

    # run program!!
    project_filename = sys.argv[1] if len(sys.argv) > 1 else ""
    next_open_project_filename = run(editor, project_filename)
    if os.path.exists(next_open_project_filename):
        executable = sys.executable
        args = sys.argv[:]
        if len(args) > 1:
            args[1] = next_open_project_filename
        else:
            args.append(next_open_project_filename)
        args.insert(0, sys.executable)
        time.sleep(1)
        os.execvp(executable, args)
