![PyEngine3D](https://github.com/ubuntunux/PyEngine3D/blob/master/PyEngine3D.png)

### What is PyEngine3D
* An open source OpenGL 3D engine written in Python.
* Homepage : https://pyengine3d.blogspot.com
* Documents : https://pyengine3d.readthedocs.io

## Requirments
 - numpy
 - Pillow
 - pygame
 - pyglet
 - PyOpenGL
 - PyOpenGL-accelerate ( optional )
 - Windows, Linux, Mac(not tested)
 
## Installation and Run
```
  git clone https://github.com/ubuntunux/PyEngine3D
  cd PyEngine3D
  pip install -r requirements.txt
  python main.py
```
![How to install PyEngine3D video](https://www.youtube.com/watch?v=bVwdV695_zo)

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
    - Spot
    - Area light
    - Point light shadow using dual paraboloid mapping
* Object
    - Select, Move, Modify
    - Gizmo
    - VTF Skinning
    - Animation calculation in gpu
* Particle System
    - Emitter Rotation
    - Particle spawn on polygon surface
    - Bitonic Sorting
    - Memory Pool
    - Spawn Volume
    - Attractor
    - Projector
    - Velocity Type
        - Random
        - Spawn Direction
        - Tornado
        - Hurricane
    - Acceleration / Damping
    - Vector Field Tiling
    - Screen Space Collide
    - Noise
    - Path Tracking
    - Depth Biased Alpha
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
