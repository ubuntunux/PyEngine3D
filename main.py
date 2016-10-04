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

__version__ = 0.1
"""

from multiprocessing import Process

# core manager
from Core import CoreManager, CustomQueue, CustomPipe


def run():
    coreCmdQueue = None
    uiCmdQueue = None
    pipe1, pipe2 = None, None

    # process - QT
    editable = True
    if editable:
        coreCmdQueue = CustomQueue()
        uiCmdQueue = CustomQueue()
        pipe1, pipe2 = CustomPipe()

        # main UI
        from UI import run_editor
        pEditor = Process(target=run_editor, args=(uiCmdQueue, coreCmdQueue, pipe2))
        pEditor.start()
    else:
        pEditor = None

    # process - Main Frame
    coreManager = CoreManager.instance(coreCmdQueue, uiCmdQueue, pipe1)
    coreManager.initialize()
    coreManager.run()

    # QT process end
    if pEditor:
        pEditor.join()

if __name__ == "__main__":
    run()
