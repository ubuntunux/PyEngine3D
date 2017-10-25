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
 - numpy 1.11
 - numba 0.35
 - pillow
 - pyqt4
 - pybullet
 - pyopengl
 - pyopengl_accelerate
 - pygame

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
    - Instancing
    - Select, Move, Modify
    - Gizmo
    - Culling
* Particle System
    - runtime particles
* PostProcess
    - AntiAliasing
        - TAA, FXAA
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
