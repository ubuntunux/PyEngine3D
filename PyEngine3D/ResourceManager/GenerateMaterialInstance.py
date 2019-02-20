import numpy as np
from numpy import array, float32
import os
from collections import OrderedDict
import pprint

for filename in os.listdir():
  if os.path.splitext(filename)[-1] != ".matinst":
    continue
  f=open(filename, "r")
  m = eval(f.read())
  f.close()
  texture_name = os.path.splitext(filename)[0]
  texture_albedo = texture_name + "_albedo.texture"
  texture_material = texture_name + "_material.texture"
  texture_normal = texture_name + "_normal.texture"
  if os.path.exists(os.path.join("..", "..", "Textures", texture_albedo)):
    m['uniform_datas']['texture_diffuse'] = texture_albedo
  if os.path.exists(os.path.join("..", "..", "Textures", texture_normal)):
    m['uniform_datas']['texture_normal'] = texture_normal
  if os.path.exists(os.path.join("..", "..", "Textures", texture_material)):
    m['uniform_datas']['texture_material'] = texture_material
  f=open(filename, "w")
  pprint.pprint(m, f)
  f.close()
