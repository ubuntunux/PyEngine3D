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
    - SSR ray reuse in compute shader
    - Postprocessing in compute shader
    - FFT in compute shader
    - Precomputed atmosphere in compute shader
* Actors
    - Tree, Foliage actor
    - Landscape
    - Road
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
    - Spot
    - Area light
    - Point light shadow using dual paraboloid mapping
* Object
    - Select, Move, Modify
    - Gizmo
    - VTF Skinning
    - Animation calculation in gpu
* Particle System
    - Particle spawn on polygon surface
* Rendering
    - View Mode
        - Wire, Solid, Lighting, Color
    - Culling
        - occlusion culling
        - distance culling
* Technique
    - Voxelization
    - Voxel Based GI
    - Screen Space Bevel
    - Screen Space LightShaft
    - Screen Space SSS
    - God Ray
    - Glare
    - Depth Of Field
    - Film Grain
    - Color Correction
    - Color Grading
    - Coarse Shading, Checkboard rendering
    - Paraboloid environment map
    - Volumtric Fog
    - Fur Rendering
* Resource Manager
    - Load / Unload / Reload system
    - Duplicate resource
* Sound
    - Loader
    - Player
