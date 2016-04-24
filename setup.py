import os, sys
from distutils.core import setup
from Cython.Build import cythonize

ignorefiles = ["Shader.py", "GLFont.py", "MainWindow.py", "main.py", "setup.py"]

def clear():
    for dirname, directories, filenames in os.walk('.'):
        for filename in filenames:
            name, ext = os.path.splitext(filename)
            oldFilename = os.path.join(dirname, filename)
            if ext.lower() in (".c", ".so"):
                os.remove(oldFilename)
            elif ext.lower() == ".pyx":
                newFilename = os.path.join(dirname, name + ".py")
                os.rename(oldFilename, newFilename)

def build():
    ext_modules = []
    for dirname, directories, filenames in os.walk('.'):
        for filename in filenames:
            if filename in ignorefiles:
                continue
            name, ext = os.path.splitext(filename)
            if ".py" == ext.lower():
                oldFilename = os.path.join(dirname, filename)
                newFilename = os.path.jogit ain(dirname, name + ".pyx")
                os.rename(oldFilename, newFilename)
                ext_modules.append(newFilename)
    setup(ext_modules = cythonize(ext_modules))


if 'build_ext' in sys.argv:
    build()
else:
    clear()