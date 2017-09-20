![PyEngine3D](https://github.com/ubuntunux/PyEngine3D/blob/master/PyEngine3D.png)

### What is PyEngine3D
* An open source OpenGL 3D engine written in Python.
* Wiki : https://github.com/ubuntunux/PyEngine3D/wiki/main
* Reference
    - http://learnopengl.com/
    - http://www.opengl-tutorial.org/
    - https://github.com/neutralord/pyopengl-experiments
    - https://github.com/asylum2010/Asylum_Tutorials
* Check similar project
    - http://glumpy.github.io/
    - https://github.com/JoshuaSenouf/GLEngine
    - https://github.com/bartwronski/CSharpRenderer

## Dependency modules
 - python 3.5.1
 - Anaconda3-2.4.1 ( https://www.continuum.io/downloads )
 - accelerate 2.0 ( anaconda accelerate library )
 - numpy 1.10.4
 - numba 0.23.1
 - pillow 3.1.1
 - Wand 0.4.4
 - pyqt4
 - pybullet 1.2.1
 - kivy 1.9.1
 - pyopengl 3.1
 - pyopengl_accelerate 3.1
 - libpng 1.6.17
 - pygame 1.9.2

## TODO
* Actors
    - Tree, Foliage actor
    - Landscape
    - SkyBox
    - Wind
    - Ocean, River
    - Envirment Cube map
* Blender3D plugin
    - transfer geometry, animation, scene datas
    - edit animation, scene, sequence, particles in blender
* Debug
    - performance profiler
    - debug info print
    - render target viewer
* Editor
    - Tab based panel
    - Snap to window rect
* Import
    - FBX
    - Blender
    - Compressed Texture (ETC, DDS)
* InGame GUI
    - input / output
    - progress bar
    - button
* Light
    - Dominant Directional Light, Spot, point, area light
    - SkyLight, AmbientLight, Spherical Harmonic Light
* Object
    - instancing
    - select, move, modify
    - gizmo
* Particle System
    - runtime particles
* PostProcess
    - AntiAliasing
        - SSAA, TAA, MSAA, SMAA
    - Motion Blur
    - HDR Tonemapping
    - SSAO, Temporal SSAO
    - Screen Space Reflection
    - Screen Space SSS
    - God Ray
    - Glare
    - Depth Of Field
    - Film Grain
    - Color Correction
    - Color Grading
    - Vignetting
* Rendering
    - Blend mode
        - Additive, Multiply, Blending
    - Multisample texture - glTexImage2DMultisample
        - sampler2D/texture by sampler2DMS/texelFetch in the fragment shader
    - View Mode
        - Wire, Solid, Lighting, Color
    - Culling
        - view frustum culling
        - occlusion culling
        - distance culling
    - Forward Renderer
    - Deferred Renderer
    - LightPrepass Renderer
    - PBR
    - Fog
    - Volumtric Scattering
    - Atmospheric Scattering
    - Font Rendering
        - Console input/output
        - Shader based rendering
* Resource Manager
    - Load / Unload / Reload system
    - Duplicate resource
* Sound
    - Loader
    - Player