### What is GuineaPig
* Opensource Opengl 3D engine was written in python.
* Reference - http://learnopengl.com/
* Check smiliar project
    - http://glumpy.github.io/
    - https://github.com/JoshuaSenouf/GLEngine
    - https://github.com/bartwronski/CSharpRenderer

## Dependency modules
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

## Features
* Material System
    - Material Template
    - Material Instance
    - TODO : Shader Cache
* Actor System
    - StaticMesh
    - TODO : SkeletalMesh
    - TODO : Tree, Foliage
    - TODO : Landscape
    - Camera
    - Light
    - TODO : SkyBox
* Object
    - Basic primitives Triangle, Quad, Cube, Shpere
    - Mesh object from external file ( obj, fbx, blend )
    - TODO : instancing
    - TODO : skinning
* Rendering
    - View Mode
        - Wire, Solid, Lighting, Color
    - Forward Renderer
    - TODO : Deferred Renderer
    - TODO : LightPrepass Renderer
    - TODO : PBR
* Particle System
    - TODO
* PostProcess
    - TODO : PostProcess Chain
    - TODO : SSAA, TAA, MSAA, SMAA
    - TODO : Motion Blur
    - TODO : HDR Tonemapping
    - TODO : SSAO, Temporal SSAO
    - TODO : Screen Space Reflection
    - TODO : Screen Space SSS
* Scene Manager
    - Object managing
* Resource Manager
    - Create/Remove/Regist/Release resources
    - TODO : resource reload system
* Import/Export
    - OBJ
    - TODO : FBX
    - TODO : Blender
    - Textures
* GUI Tool
    - QT backend
    - Kivy backend
* Debug
    - performance profiler
    - debug info print
    - TODO : render target viewer
