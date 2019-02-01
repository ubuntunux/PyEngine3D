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
 - pyglet or pygame
 - PyOpenGL
 - PyOpenGL-accelerate ( optional )
 - Windows, Linux, Mac(not tested)

## Features
* Import
    - [x] .fbx
    - [x] .obj
    - [x] .dae ( colada )
    - gltf
    - Blender
    - Compressed Texture (ETC, DDS)
* Light
    - [x] Directional light & Shadow mapping    
    - Spot light
    - Area light
    - [x] Point light
        - shadow map using dual paraboloid mapping
* Particle System
    - [x] CPU Based Particle
    - [x] GPU Based Particle
    - [x] Vector Field
    - Particle spawn on polygon surface
    - Bitonic Sorting
    - Memory Pool
    - Attractor
    - Noise
    - Curl Noise
* Object
    - Select, Move, Modify
    - Gizmo
    - [x] Skeleton Mesh
    - [x] Static Mesh        
    - Tree, Foliage, Grass
    - [x] Terrain
    - [x] Atmoshpere & Sky
    - Road
    - Wind
    - [x] Ocean
    - River 
* Rendering
    - Culling
        - occlusion culling
        - distance culling
        - [x] view frustum culling
    - VTF Skinning
    - Calculate the animation in gpu
    - Distance Field Font 
    - [x] PBR
    - [x] Screen Space Relfection
    - [x] Temporal AA
    - [x] SSAA
    - [x] MSAA
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
    - [x] Light Shaft
    - Volumtric Scattering
    - Fur Rendering    
    - [x] Motion Blur
        - Recursive Velocity
* Resource Manager
    - [x] Load / Save / Import / Export
    - Unload / Reload system
    - Duplicate resource
    - Sound Manager
    - [x] Script Manager
* Blender3D plugin
    - transfer geometry, animation, scene datas
    - edit animation, scene, sequence, particles in blender
* InGame GUI
    - input / output
    - progress bar
    - button
* Optimize
    - Only dynamic shadows are updated on every frame, and static shadows are not updated every time.
    - SSR ray reuse in compute shader
    - Postprocessing in compute shader
    - FFT in compute shader
    - Precomputed atmosphere in compute shader 

