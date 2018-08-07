![PyEngine3D](https://github.com/ubuntunux/PyEngine3D/blob/master/PyEngine3D.png)

### What is PyEngine3D
* An open source OpenGL 3D engine written in Python.
* Reference
    - http://learnopengl.com/
    - http://www.opengl-tutorial.org/
    - https://github.com/neutralord/pyopengl-experiments
    - https://github.com/asylum2010/Asylum_Tutorials
* Similar projects
    - http://glumpy.github.io/
    - https://github.com/JoshuaSenouf/GLEngine
    - https://github.com/bartwronski/CSharpRenderer

## Dependency modules
 - python 3
 - numpy
 - pillow
 - pyopengl
 - pyopengl_accelerate
 - pygame or pyglet

## TODO
* Optimize
    - Only dynamic shadows are updated on every frame, and static shadows are not updated every time.
    - SSR optimize, hierachical z ray marching
    - Particle uniform block
* Actors
    - Tree, Foliage actor
    - Landscape
    - Wind
    - River
* Blender3D plugin
    - transfer geometry, animation, scene datas
    - edit animation, scene, sequence, particles in blender
* Debug
    - performance profiler
* Import
    - FBX
    - Blender
    - Compressed Texture (ETC, DDS)
* InGame GUI
    - input / output
    - progress bar
    - button
* Light
    - Spot, area light
* Object
    - Select, Move, Modify
    - Gizmo
    - VTF Skinning
    - Animation calculation in gpu
* Particle System
    - Force field
* Rendering    
    - View Mode
        - Wire, Solid, Lighting, Color
    - Culling
        - occlusion culling
        - distance culling   
    - Volumtric Fog
    - Fur Rendering
    - Procedural Terrain
* Technique
    - FXAA
    - SSR Optimization
    - Hierachical-Z depth
    - Screen Space SSS
    - God Ray
    - Glare
    - Depth Of Field
    - Film Grain
    - Color Correction
    - Color Grading
    - Coarse Shading, Checkboard rendering
    - Paraboloid environment map    
* Resource Manager
    - Load / Unload / Reload system
    - Duplicate resource
* Sound
    - Loader
    - Player
