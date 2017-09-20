![PyEngine3D](https://github.com/ubuntunux/PyEngine3D/blob/master/PyEngine3D.png)

### What is PyEngine3D
* Opensource Opengl 3D engine was written in python.
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
* Blender3D plugin
    - transfer geometry, animation, scene datas
    - edit animation, scene, sequence, particles in blender
* Resource Manager
    - Load / Unload / Reload system
    - Duplicate resource
* Import
    - FBX
    - Blender
    - Compressed Texture (ETC, DDS)
    - Done : Collada, Obj
* GUI Editor
    - Small Tab based panel
* Rendering
    - blend mode
        - Additive, Multiply, Blending
    - Multisample texture - glTexImage2DMultisample
        - sampler2D/texture by sampler2DMS/texelFetch in the fragment shader
* Light
    - Dominant Directional Light, Spot, point, area light
    - SkyLight, AmbientLight, Spherical Harmonic Light
* Actors
    - Static actor
    - Skeleton actor
    - Tree, Foliage actor
    - Landscape
    - SkyBox
    - Wind
    - Ocean, River
    - Envirment Cube map
* Object
    - instancing
    
* Rendering
    - OpenGL Context
    - View Mode
        - Wire, Solid, Lighting, Color
    - TODO : Culling
        - view frustum culling 
        - occlusion culling
        - distance culling
    - RenderBuffer object
    - Texture2D attach to framebuffer    
    - TODO : Multi render target
    - TODO : Copy Texture Interface
    - TODO : RenderTargets Resize when change resolution
    - Forward Renderer
    - TODO : Deferred Renderer
    - TODO : LightPrepass Renderer
    - TODO : PBR
    - TODO : Shadow
    - TODO : Fog
    - TODO : Volumtric Scattering
    - TODO : Atmospheric Scattering
* Particle System
* PostProcess
    - TODO : PostProcess Chain
    - TODO : SSAA, TAA, MSAA, SMAA
    - TODO : Motion Blur
    - TODO : HDR Tonemapping
    - TODO : SSAO, Temporal SSAO
    - TODO : Screen Space Reflection
    - TODO : Screen Space SSS
    - TODO : God Ray
    - TODO : Glare
    - TODO : Depth Of Field
    - TODO : Film Grain
    - TODO : Color Correction
    - TODO : Color Grading
    - TODO : Vignetting
* Font
    - TODO : Console input/output
    - TODO : Shader based rendering
* InGame GUI
    - TODO : input / output
    - TODO : progress bar
    - TODO : button
* GUI Edit Tool
    - QT backend
    - Kivy backend
* Debug
    - performance profiler
    - debug info print
    - TODO : render target viewer
