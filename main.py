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


def run(editor):
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
            editor_process = Process(target=run_editor, args=(uiCmdQueue, appCmdQueue, pipe2))
            editor_process.start()
        elif editor == GUIEditor.KIVY:
            from UI.Kivy.MainWindow import run_editor
            editor_process = Process(target=run_editor, args=(uiCmdQueue, appCmdQueue, pipe2))
            editor_process.start()

    # Client process
    coreManager = CoreManager.instance(appCmdQueue, uiCmdQueue, pipe1)
    coreManager.initialize()
    reload = coreManager.run()

    # GUI Editor process end
    if editor_process:
        editor_process.join()

    return reload  # reload or not


if __name__ == "__main__":
    editor = GUIEditor.QT

    select_editor = False
    if select_editor:
        enums = [editor for editor in dir(GUIEditor) if not editor.startswith("__")]
        enums = sorted(enums, key=lambda enum_str: getattr(GUIEditor, enum_str).value)
        nums = [str(i) for i in range(len(enums))]

        if len(sys.argv) > 1:
            for enum in enums:
                if sys.argv[1].upper() == enum:
                    editor = eval("GUIEditor." + enum)
                    break
        else:
            try:
                for i, enum in enumerate(enums):
                    print("%d. %s" % (i, enum))
                answer = input("Select GUI Editor :")
                if answer in nums:
                    editor = eval("GUIEditor." + enums[int(answer)])
                elif answer.upper() in enums:
                    editor = eval("GUIEditor.%s" % answer.upper())
            except:
                pass

    - New_Project => Copy all default resources to new project dircetory
    - Open Porject => Reload All! Load only resources of project directory

    while True:
        # run program!!
        reload = run(editor)
        if reload:
            executable = sys.executable
            args = sys.argv[:]
            args.insert(0, sys.executable)
            time.sleep(1)
            os.execvp(executable, args)
        else:
            break
