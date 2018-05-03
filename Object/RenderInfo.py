import math
from Utilities import *


def always_pass(*args):
    return False


def cone_sphere_culling(camera, actor):
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


def view_frustum_culling(camera, actor):
    to_actor = actor.transform.pos - camera.transform.pos
    radius = actor.model.mesh.radius * max(actor.transform.scale)
    for i in range(6):
        d = np.dot(to_actor, camera.frustum_planes[i][0:3])
        if camera.frustum_planes[i][3] < d - radius:
            return True
    return False


def view_frustum_culling_geomtry(camera, actor, geometry):
    to_geometry = np.array([geometry.boundCenter[0], geometry.boundCenter[1], geometry.boundCenter[2], 1.0])
    to_geometry = np.dot(to_geometry, actor.transform.matrix)[0:3] - camera.transform.pos
    radius = geometry.radius * max(actor.transform.scale)
    for i in range(6):
        d = np.dot(to_geometry, camera.frustum_planes[i][0:3])
        if camera.frustum_planes[i][3] < d - radius:
            return True
    return False


class RenderInfo:
    def __init__(self):
        self.actor = None
        self.geometry = None
        self.material = None
        self.material_instance = None

    @staticmethod
    def gather_render_infos(culling_func, camera, actor_list, solid_render_infos, translucent_render_infos):
        for actor in actor_list:
            if culling_func(camera, actor):
                continue

            for geometry in actor.get_geometries():
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


class RenderInstanceInfo:
    def __init__(self):
        self.actor = None
        self.geometry = None
        self.material_instance = None
        self.model_instance_data = []
        self.model_instance_location = -1

    @staticmethod
    def gather_render_infos(culling_func, camera, actor_list, check_actor_change, model_instance_location,
                            solid_render_infos, translucent_render_infos):
        last_actor = None
        last_geometry = None
        last_material_instance = None

        render_info = None
        new_render_info = True
        for actor in actor_list:
            if culling_func(camera, actor):
                continue

            for geometry in actor.get_geometries():
                material_instance = actor.get_material_instance(geometry.index)
                if last_geometry != geometry:
                    new_render_info = True
                elif last_material_instance != material_instance:
                    new_render_info = True
                elif check_actor_change and last_actor != actor:
                    new_render_info = True

                if new_render_info and geometry  is not None and material_instance is not None:
                    # convert to numpy array.
                    if render_info is not None:
                        render_info.model_instance_data = np.array(render_info.model_instance_data, np.float32)

                    render_info = RenderInfo()
                    render_info.actor = actor
                    render_info.geometry = geometry
                    render_info.material_instance = material_instance
                    render_info.material = material_instance.material
                    render_info.model_instance_location = model_instance_location
                    if render_info.material_instance.is_translucent():
                        if translucent_render_infos is not None:
                            translucent_render_infos.append(render_info)
                    elif solid_render_infos is not None:
                            solid_render_infos.append(render_info)
                    new_render_info = False

                # append instance data
                if render_info is not None:
                    render_info.model_instance_data.append(actor.transform.matrix)

                last_actor = actor
                last_geometry = geometry
                last_material_instance = material_instance
        else:
            # At the end, you should convert to numpy.array unconditionally.
            if render_info:
                render_info.model_instance_data = np.array(render_info.model_instance_data, np.float32)
