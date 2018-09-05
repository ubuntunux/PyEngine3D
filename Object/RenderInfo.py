import math
from Utilities import *


def always_pass(*args):
    return False


def cone_sphere_culling_actor(camera, actor):
    to_actor = actor.transform.pos - camera.transform.pos

    dist = magnitude(to_actor)
    if 0.0 < dist:
        to_actor /= dist

    rad = math.acos(np.dot(to_actor, -camera.transform.front)) - camera.half_cone
    projected_dist = dist * math.sin(rad)
    radius = actor.model.mesh.radius * max(actor.transform.scale)
    if 0.0 < rad and radius < projected_dist:
        return True
    elif HALF_PI < rad and radius < dist:
        return True
    return False


def view_frustum_culling_geometry(camera, light, actor, geometry):
    to_geometry = np.array([geometry.boundCenter[0], geometry.boundCenter[1], geometry.boundCenter[2], 1.0])
    to_geometry = np.dot(to_geometry, actor.transform.matrix)[0:3] - camera.transform.pos
    max_scale = max(actor.transform.scale)

    if 1 < actor.instance_count:
        # instancing
        radius = geometry.radius * max_scale * actor.instance_radius_scale
        radius += actor.instance_radius_offset * max_scale
    else:
        radius = geometry.radius * max_scale

    for i in range(4):
        d = np.dot(camera.frustum_vectors[i], to_geometry)
        if radius < d:
            return True
    return False


def shadow_view_frustum(camera, light, actor, geometry):
    lightPosMatrix = get_translate_matrix(*(-camera.transform.get_pos()))
    shadow_matrix = np.dot(actor.transform.matrix, np.dot(lightPosMatrix, light.transform.rotationMatrix.T))

    if 1 < actor.instance_count:
        # instancing
        scale = actor.instance_radius_scale
        offset = actor.instance_radius_offset
        boundMin = geometry.boundMin * scale - offset
        boundMax = geometry.boundMax * scale + offset
    else:
        boundMin = geometry.boundMin.copy()
        boundMax = geometry.boundMax.copy()

    boundMin = abs(np.dot(np.array([boundMin[0], boundMin[1], boundMin[2], 1.0], dtype=np.float32), shadow_matrix))
    boundMax = abs(np.dot(np.array([boundMax[0], boundMax[1], boundMax[2], 1.0], dtype=np.float32), shadow_matrix))

    shadow_distance = 50.0 / camera.meter_per_unit
    width, height = shadow_distance * 0.5, shadow_distance * 0.5

    orthogonal = ortho(-boundMin[0], boundMax[0], -boundMin[1], boundMax[1], -boundMin[2], boundMax[2])

    light.shadow_view_projection[...] = np.dot(np.dot(lightPosMatrix, light.transform.inverse_matrix), orthogonal)
    return True


def gather_render_infos(culling_func, camera, light, actor_list, solid_render_infos, translucent_render_infos):
    for actor in actor_list:
        for geometry in actor.get_geometries():
            if culling_func(camera, light, actor, geometry):
                continue

            material_instance = actor.get_material_instance(geometry.index)
            render_info = RenderInfo()
            render_info.actor = actor
            render_info.geometry = geometry
            render_info.material = material_instance.material if material_instance else None
            render_info.material_instance = material_instance
            if render_info.material_instance.is_translucent():
                if translucent_render_infos is not None:
                    translucent_render_infos.append(render_info)
            elif solid_render_infos is not None:
                    solid_render_infos.append(render_info)


class RenderInfo:
    def __init__(self):
        self.actor = None
        self.geometry = None
        self.material = None
        self.material_instance = None
