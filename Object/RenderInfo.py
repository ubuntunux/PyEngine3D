from Utilities import *


class RenderInfo:
    def __init__(self):
        self.actor = None
        self.geometry = None
        self.material = None
        self.material_instance = None

    @staticmethod
    def gather_render_infos(camera, actor_list, solid_render_infos, translucent_render_infos):
        # camera_pos = camera.transform.getPos()
        # view_front = -camera.transform.front

        for actor in actor_list:
            # to_actor = actor.transform.getPos() - camera_pos
            #
            # temp = camera.left_diagonal * np.dot(to_actor, camera.left_diagonal)
            # if dot(view_front, camera.left_diagonal) < dot(view_front, camera.left_diagonal):
            #     if magnitude(to_actor - temp) < actor.model.mesh.radius:
            #         continue

            for geometry in actor.get_geometries():
                material_instance = actor.get_material_instance(geometry.index)
                render_info = RenderInfo()
                render_info.actor = actor
                render_info.geometry = geometry
                render_info.material = material_instance.material if material_instance else None
                render_info.material_instance = material_instance
                if render_info.material_instance.is_translucent():
                    translucent_render_infos.append(render_info)
                else:
                    solid_render_infos.append(render_info)


class RenderInstanceInfo:
    def __init__(self):
        self.actor = None
        self.geometry = None
        self.material_instance = None
        self.model_instance_data = []
        self.model_instance_location = -1

    @staticmethod
    def gather_render_infos(camera, actor_list, check_actor_change, model_instance_location, solid_render_infos,
                            translucent_render_infos):
        last_actor = None
        last_geometry = None
        last_material_instance = None

        render_info = None
        new_render_info = True
        for actor in actor_list:
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
                        translucent_render_infos.append(render_info)
                    else:
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