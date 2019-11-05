import math

from PyEngine3D.Utilities import *


def always_pass(*args):
    return False


def cone_sphere_culling_actor(camera, actor):
    to_actor = actor.transform.pos - camera.transform.pos

    dist = length(to_actor)
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


def view_frustum_culling_geometry(camera, light, actor, geometry_bound_box):
    to_geometry = geometry_bound_box.bound_center - camera.transform.pos
    for i in range(4):
        d = np.dot(camera.frustum_vectors[i], to_geometry)
        if geometry_bound_box.radius < d:
            return True
    return False


def shadow_culling(camera, light, actor, geometry_bound_box):
    bound_min = np.dot(np.array([geometry_bound_box.bound_min[0], geometry_bound_box.bound_min[1], geometry_bound_box.bound_min[2], 1.0], dtype=np.float32), light.shadow_view_projection)[: 3]
    bound_max = np.dot(np.array([geometry_bound_box.bound_max[0], geometry_bound_box.bound_max[1], geometry_bound_box.bound_max[2], 1.0], dtype=np.float32), light.shadow_view_projection)[: 3]
    minimum = np.minimum(bound_min, bound_max)
    maximum = np.maximum(bound_min, bound_max)
    if any(x < -1.0 for x in maximum) or any(1.0 < x for x in minimum):
        return True
    return False


def gather_render_infos(culling_func, camera, light, actor_list, solid_render_infos, translucent_render_infos):
    for actor in actor_list:
        for i in range(actor.get_geometry_count()):
            if not actor.visible:
                continue

            if culling_func(camera, light, actor, actor.get_geometry_bound_box(i)):
                continue

            material_instance = actor.get_material_instance(i)
            render_info = RenderInfo()
            render_info.actor = actor
            render_info.geometry = actor.get_geometry(i)
            render_info.geometry_data = actor.get_geometry_data(i)
            render_info.gl_call_list = actor.get_gl_call_list(i)
            render_info.material = material_instance.material if material_instance else None
            render_info.material_instance = material_instance
            if render_info.material_instance is not None and render_info.material_instance.is_translucent():
                if translucent_render_infos is not None:
                    translucent_render_infos.append(render_info)
            elif solid_render_infos is not None:
                solid_render_infos.append(render_info)


class RenderInfo:
    def __init__(self):
        self.actor = None
        self.geometry = None
        self.geometry_data = None
        self.gl_call_list = None
        self.material = None
        self.material_instance = None
