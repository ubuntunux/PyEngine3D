![PyEngine3D](https://github.com/ubuntunux/PyEngine3D/blob/master/PyEngine3D.png)

## What is PyEngine3D
* An open source OpenGL 3D engine written in Python.
* Homepage : https://pyengine3d.blogspot.com
* Documents : https://pyengine3d.readthedocs.io
 
## How to install PyEngine3D
```
  git clone https://github.com/ubuntunux/PyEngine3D
  cd PyEngine3D
  pip install -r requirements.txt
  python main.py
```
* Video : https://www.youtube.com/watch?v=bVwdV695_zo


## Requirements
 - numpy
 - Pillow
 - pygame
 - pyglet
 - PyOpenGL
 - PyOpenGL-accelerate ( optional )
 - Windows, Linux, Mac(not tested)

## Features
* Optimize
    - Only dynamic shadows are updated on every frame, and static shadows are not updated every time.
    - SSR ray reuse in compute shader
    - Postprocessing in compute shader
    - FFT in compute shader
    - Precomputed atmosphere in compute shader 
* Blender3D plugin
    - transfer geometry, animation, scene datas
    - edit animation, scene, sequence, particles in blender
* Debug
    - 3D position font
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
    [o] Directional light & Shadow mapping    
    - Spot light
    - Area light
    - Point light
        - shadow map using dual paraboloid mapping
* Particle System
    - Particle spawn on polygon surface
    - Bitonic Sorting
    - Memory Pool
    - Attractor
    - Noise
    - Curl Noise
    - Depth Biased Alpha   
* Object
    - Select, Move, Modify
    - Gizmo
    - Skeleton Mesh
    - Static Mesh        
    - Tree, Foliage, Grass
    - Terrain
    - Atmoshpere & Sky
    - Road
    - Wind
    - Ocean
    - River 
* Rendering
    - View Mode
        - Wire, Solid, Lighting, Color
    - Culling
        - occlusion culling
        - distance culling
        - view frustum culling
    - VTF Skinning
    - Animation calculation in gpu
    - Font Distance Field
        - FontLoader.DistanceField
    - PBR
    - Screen Space Relfection
    - Temporal AA
    - SSAA
    - MSAA
    - Voxel Based GI
    - Screen Space Bevel
    - Screen Space SSS
    - Glare
    - Depth Of Field
        - Bokeh
    - Film Grain
    - Color Correction
    - Color Grading
    - Coarse Shading, Checkboard rendering
    - Paraboloid environment map
    - Light Shaft
    - Volumtric Scattering
    - Fur Rendering    
    - Motion Blur
        - Recursive Velocity
* Resource Manager
    - Load / Unload / Reload system
    - Duplicate resource
* Sound
    - Loader
    - Player
