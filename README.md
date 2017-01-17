Welcome to the GuineaPig wiki!

### What is GuineaPig
* Opensource 3D engine was written in python
* Reference - http://learnopengl.com/
* Check smiliar project - http://glumpy.github.io/

## Dependency modules.
 - python 3.5.1
 - Anaconda3-2.4.1 ( https://www.continuum.io/downloads )
 - accelerate 2.0 ( anaconda accelerate library )
 - numpy 1.10.4
 - numba 0.23.1
 - pillow (3.1.1)
 - pyqt4
 - pyopengl 3.1
 - pyopengl_accelerate 3.1
 - libpng 1.6.17
 - pygame 1.9.2

----
### TODO
- Column Major <--> Row Major Matrix Swtich System ( Now, App use row major matrix, but glsl use column major matrix. )
- glsl buffer binding system
- implement UniformBuffer
- Object Uniform Struct
- Create Material from shader
- Material System
- Auto create material from shader
- Object Data
- Resource Create, Delete, Regist, Release System
- Scene Data
- Import .blend File
- Choose Resource System
- Resource Reload System
- View Mode
 - wire, solid, unlit, shading, texture
- profiler
    - time
    - memory
    - scope blcok
