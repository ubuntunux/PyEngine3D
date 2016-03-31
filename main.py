#!/usr/bin/env python
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (c) 2015, ubuntunux"
__license__ = """
Copyright (c) 2015, ubuntunux
All rights reserved.

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
"""
__version__ = '0.1'

import os
from multiprocessing import Process, Queue, Pipe

import sdl2
# use local sdl library file path
sdlpath = os.path.join(os.path.dirname(__file__), 'libs')
if os.path.exists(sdlpath):
    os.environ['PYSDL2_DLL_PATH'] = sdlpath

# core manager
import Core

# main UI
from UI import run_editor


if __name__ == "__main__":
    # sdl init
    if sdl2.SDL_Init(sdl2.SDL_INIT_EVERYTHING) == 0:
        coreCmdQueue = Queue()
        uiCmdQueue = Queue()
        pipe1, pipe2 = Pipe()

        # process - Main Frame
        pCoreProcess = Process(target = Core.run, args=(coreCmdQueue, uiCmdQueue, pipe1))
        pCoreProcess.start()

        # process - QT
        pEditor = Process(target=run_editor, args=(uiCmdQueue, coreCmdQueue, pipe2))
        pEditor.start()

        # end
        pCoreProcess.join()
        pEditor.join()

        # sdl2 quit
        sdl2.SDL_Quit()
    else:
        # sdl initialize error
        print(sdl2.SDL_GetError())