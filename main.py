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

__version__ = 0.5
"""

import sys
import os
import time
from multiprocessing import Process

from Core.Command import CustomQueue, CustomPipe
from Core.CoreManager import CoreManager
from Utilities import AutoEnum


class GUIEditor(AutoEnum):
    CLIENT_MODE = ()
    QT = ()
    KIVY = ()


def run(editor, project_filename=""):
    appCmdQueue = None
    uiCmdQueue = None
    pipe1, pipe2 = None, None
    editor_process = None

    # other process - GUIEditor ( QT, Kivy )
    if editor != GUIEditor.CLIENT_MODE:
        appCmdQueue = CustomQueue()
        uiCmdQueue = CustomQueue()
        pipe1, pipe2 = CustomPipe()

        # Select GUI backend
        if editor == GUIEditor.QT:
            from UI.QT.MainWindow import run_editor
            editor_process = Process(target=run_editor, args=(project_filename, uiCmdQueue, appCmdQueue, pipe2))
            editor_process.start()
        elif editor == GUIEditor.KIVY:
            from UI.Kivy.MainWindow import run_editor
            editor_process = Process(target=run_editor, args=(project_filename, uiCmdQueue, appCmdQueue, pipe2))
            editor_process.start()

    # Client process
    coreManager = CoreManager.instance(appCmdQueue, uiCmdQueue, pipe1)
    result = coreManager.initialize(project_filename)
    if result:
        coreManager.run()
        open_project_filename = coreManager.get_open_project_filename()
    else:
        open_project_filename = ""

    # GUI Editor process end
    if editor_process:
        editor_process.join()

    return open_project_filename  # reload or not


if __name__ == "__main__":
    editor = GUIEditor.QT

    # run program!!
    project_filename = sys.argv[1] if len(sys.argv) > 1 else ""
    open_project_filename = run(editor, project_filename)
    if open_project_filename:
        executable = sys.executable
        args = sys.argv[:]
        if len(args) > 1:
            args[1] = open_project_filename
        else:
            args.append(open_project_filename)
        args.insert(0, sys.executable)
        time.sleep(1)
        os.execvp(executable, args)
