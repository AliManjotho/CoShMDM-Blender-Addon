# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "CoShMDM",
    "author": "Ali Asghar Manjotho",
    "description": "",
    "blender": (4, 3, 0),
    "version": (1, 0, 0),
    "location": "",
    "warning": "",
    "category": "View3D",
}


# IMPORTS  ######################################################
import bpy
from bpy_extras.io_utils import ImportHelper,ExportHelper
from mathutils import Vector, Quaternion
from bpy.props import ( BoolProperty, EnumProperty, FloatProperty, IntProperty, FloatVectorProperty, PointerProperty, StringProperty )
from bpy.types import ( Panel, PropertyGroup, Operator, AddonPreferences, PropertyGroup )                       

import json
from math import radians
import numpy as np
import os
import pickle
import math
from mathutils import Vector, Quaternion
import bmesh
# END IMPORTS  ##################################################









# CONSTANTS  ####################################################
BASE_PATH = "D:/RESEARCH/Code/Blender/t2m-obj-test"
ADDON_DIR = os.path.dirname(os.path.abspath(__file__))

# P1_OFFSET = (0.27, 0.8, 0)
# P2_OFFSET = (0, -0.8, 0)
background_color = "#FFFFFF"

class Paths:
    def get_P1_SMPL_OBJS_PATH():
        return os.path.join(BASE_PATH, "p1")
    
    def get_P2_SMPL_OBJS_PATH():
        return os.path.join(BASE_PATH, "p2")
    
    def get_DISK_FILE_PATH():
        return os.path.join(ADDON_DIR, "assets/disk.obj")
    
    def get_ARROW_FILE_PATH():
        return os.path.join(ADDON_DIR, "assets/arrow.obj")
    
    def get_STAGE_FILE_PATH():
        return os.path.join(ADDON_DIR, "assets/stage.obj")

   

class Normals:
    HEAD_INDEX = 335
    CHEST_INDEX = 3495
    MIDHIP_INDEX = 1807

P1_DRAW_SMPL = True
P2_DRAW_SMPL = True
P1_DRAW_DISK = True
P2_DRAW_DISK = True
P1_DRAW_MIDHIP_ARROW = True
P2_DRAW_MIDHIP_ARROW = True
P1_DRAW_CHEST_ARROW = True
P2_DRAW_CHEST_ARROW = True
P1_DRAW_HEAD_ARROW = True
P2_DRAW_HEAD_ARROW = True

# Z_STAGE = -1.09638
# Z_DISK = -1.093 + 0.007


# END CONSTANTS  #################################################







def clear_scene():

    if bpy.context.screen.is_animation_playing:
        bpy.ops.screen.animation_cancel()
        
    if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    for collection in bpy.data.collections:
        bpy.data.collections.remove(collection)
        
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
        
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
        
    for curve in bpy.data.curves:
        bpy.data.curves.remove(curve)

def setup_scene(scene, frame_start, num_frames, res="ultra"):
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.resolution_percentage = 100
    
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.data.scenes[0].render.engine = "CYCLES"
    bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"
    bpy.context.scene.cycles.device = "GPU"
    bpy.context.preferences.addons["cycles"].preferences.get_devices()

    bpy.context.scene.cycles.use_denoising = True
    bpy.context.scene.cycles.denoiser = 'OPTIX'
    bpy.context.scene.cycles.use_adaptive_sampling = True    
    bpy.context.scene.cycles.samples = 4098
    
    bpy.context.scene.view_settings.view_transform = 'Standard'
    bpy.context.scene.render.film_transparent = True
    bpy.context.scene.display_settings.display_device = 'sRGB'
    bpy.context.scene.view_settings.gamma = 1.2
    bpy.context.scene.view_settings.exposure = -0.75

    scene = bpy.data.scenes['Scene']
    assert res in ["ultra", "high", "med", "low"]

    if res == "high":
        scene.render.resolution_x = 1280
        scene.render.resolution_y = 1024
    elif res == "med":
        scene.render.resolution_x = 1280//2
        scene.render.resolution_y = 1024//2
    elif res == "low":
        scene.render.resolution_x = 1280//4
        scene.render.resolution_y = 1024//4
    elif res == "ultra":
        scene.render.resolution_x = 1920
        scene.render.resolution_y = 1080

    world = bpy.data.worlds['World']
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs[0].default_value[:3] = (1.0, 1.0, 1.0)
    bg.inputs[1].default_value = 1.0


    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'HIGH'
    scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
    scene.render.filepath = os.path.join("c:/temp", "anim.mp4")
    scene.render.fps = 24  # Set your desired frames per second
    scene.frame_start = frame_start  # Set the start frame
    scene.frame_end = frame_start + num_frames - 1  # Set the end frame

    # Area Light
    bpy.ops.object.light_add(type='AREA', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.ops.transform.translate(value=(0, 0, 2.01739), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    bpy.context.object.data.energy = 100
    bpy.ops.transform.resize(value=(8.15251, 8.15251, 8.15251), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)


    area_light = bpy.context.selected_objects[0]
    assets_collection = create_collection("Assets")
    assets_collection.objects.link(area_light)
    bpy.context.scene.collection.objects.unlink(area_light)


    # Sun Light
    bpy.ops.object.light_add(type='SUN', radius=1, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.object.data.energy = 5
    
    sun_light = bpy.context.selected_objects[0]
    assets_collection = create_collection("Assets")
    assets_collection.objects.link(sun_light)
    bpy.context.scene.collection.objects.unlink(sun_light)

    # Camera
    bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=(0, 0, 0), rotation=(1.36974, -2.11349e-07, -2.95226), scale=(1, 1, 1))

    camera = bpy.context.selected_objects[0]
    assets_collection = create_collection("Assets")
    assets_collection.objects.link(camera)
    bpy.context.scene.collection.objects.unlink(camera)
   
def read_npy_file(file_path):
    data = np.load(file_path, allow_pickle=True)
    data = data[None][0]

    motion = data['motion']
    motion = data['thetas']
    gender = "neutral" 
    root_translations = data['root_translation']
    root_translations = root_translations.transpose(1,0)
    num_frames = data['length']

    return motion, gender, root_translations, num_frames

def draw_obj(name, obj_file_path, scale=(0.8, 0.8, 0.8)):
    bpy.ops.wm.obj_import(filepath=obj_file_path)
    disk_obj = bpy.context.active_object
    disk_obj.name = name
    disk_obj.scale = scale

    return disk_obj

def get_smpl_center(smpl_mesh_obj):
    bpy.context.view_layer.objects.active = smpl_mesh_obj
    bbox_center = sum((Vector(b) for b in smpl_mesh_obj.bound_box), Vector()) / 8
    world_bbox_center = smpl_mesh_obj.matrix_world @ bbox_center

    return world_bbox_center

def rotate_z_obj(smpl_mesh_obj, obj, vertex_index):
    bpy.context.view_layer.objects.active = smpl_mesh_obj

    if smpl_mesh_obj.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')

    mesh = smpl_mesh_obj.data
    bm = bmesh.from_edit_mesh(mesh)
    bm.verts.ensure_lookup_table()
    vert = bm.verts[vertex_index]
    vert_normal = vert.normal
    world_vert_normal = smpl_mesh_obj.matrix_world.to_3x3() @ vert_normal
    world_vert_normal.normalize()
    
    if smpl_mesh_obj.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    rot_z = math.atan2(world_vert_normal[1], world_vert_normal[0])
    obj.rotation_euler[2] = rot_z

def translate_obj(obj, center, Z_STAGE):
    location = (center[0], center[1], Z_STAGE)
    obj.location = location

    return location

def get_min_max_bounds(smpl_mesh_objects):
    points = []
    for index, smpl_obj in enumerate(smpl_mesh_objects):
    
        bbox_corners = [Vector(corner) for corner in smpl_obj.bound_box]
        world_bbox_corners = [smpl_obj.matrix_world @ corner for corner in bbox_corners]

        min_z = min(corner.z for corner in world_bbox_corners)
        bottom_corners = [corner for corner in world_bbox_corners if corner.z == min_z] 

        points.extend(bottom_corners)

    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)
    min_z = min(point[2] for point in points)
    max_z = max(point[2] for point in points)

    return (min_x, min_y, min_z), (max_x, max_y, max_z)

def create_material(name, color, alpha = 1.0):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    else:
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        bsdf = material.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Metallic'].default_value = 0.125
        bsdf.inputs['Roughness'].default_value = 0.3
        bsdf.inputs['IOR'].default_value = 1.5
        bsdf.inputs['Alpha'].default_value = alpha
        return material

def assign_material(name, color, alpha=1.0, obj=None):
    if obj == None and name in bpy.data.materials:
        mat = bpy.data.materials[name]
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Alpha'].default_value = alpha
    else:
        mat = create_material(name, color, alpha)
        obj.data.materials.append(mat)

def create_collection(name):
    if name not in bpy.data.collections:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    else:
        collection = bpy.data.collections[name]
    return collection

def draw_curve(name, points):
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'

    spline = curve_data.splines.new(type='POLY')
    spline.points.add(count=len(points) - 1)

    for i, (x, y, z) in enumerate(points):
        spline.points[i].co = (x, y, z, 1)

    curve_object = bpy.data.objects.new(name=name, object_data=curve_data)
    bpy.context.collection.objects.link(curve_object)
    bpy.context.view_layer.objects.active = curve_object

    curve_object.data.bevel_depth = 0.02
    curve_object.data.use_fill_caps = True

    return curve_object

def toggle_obj_visibility(obj_name, state):
    obj = bpy.data.objects[obj_name]
    obj.hide_viewport = not state
    obj.hide_render = not state

def set_z_stage(self, context):
    z = context.scene.intergen_props.z_stage  
    bpy.data.objects["stage"].location[2] = z

def set_z_disk(self, context):
    z = context.scene.intergen_props.z_disk  
    bpy.data.objects["p1_disk"].location[2] = z
    bpy.data.objects["p2_disk"].location[2] = z

def toggle_p1_disk(self, context):
    toggle_obj_visibility("p1_disk", context.scene.intergen_props.show_p1_disk)

def toggle_p1_midhiparrow(self, context):
    toggle_obj_visibility("p1_midhip_arrow", context.scene.intergen_props.show_p1_midhiparrow)

def toggle_p1_chestarrow(self, context):
    toggle_obj_visibility("p1_chest_arrow", context.scene.intergen_props.show_p1_chestarrow)

def toggle_p1_headarrow(self, context):
    toggle_obj_visibility("p1_head_arrow", context.scene.intergen_props.show_p1_headarrow)

def toggle_p1_path(self, context):
    toggle_obj_visibility("p1_curve", context.scene.intergen_props.show_p1_path)

def toggle_p2_disk(self, context):
    toggle_obj_visibility("p2_disk", context.scene.intergen_props.show_p2_disk)

def toggle_p2_midhiparrow(self, context):
    toggle_obj_visibility("p2_midhip_arrow", context.scene.intergen_props.show_p2_midhiparrow)

def toggle_p2_chestarrow(self, context):
    toggle_obj_visibility("p2_chest_arrow", context.scene.intergen_props.show_p2_chestarrow)

def toggle_p2_headarrow(self, context):
    toggle_obj_visibility("p2_head_arrow", context.scene.intergen_props.show_p2_headarrow)

def toggle_p2_path(self, context):
    toggle_obj_visibility("p2_curve", context.scene.intergen_props.show_p2_path)
    
def offset_p1_smpl(self, context):
    for obj in bpy.data.objects:
        loc = context.scene.intergen_props.p1_offset
        if obj.name.startswith("p1_smpl"):            
            obj.location = loc
    
    bpy.data.objects["p1_disk"].location = (loc[0], loc[1], bpy.data.objects["p1_disk"].location[2])
    bpy.data.objects["p1_midhip_arrow"].location = (loc[0], loc[1], bpy.data.objects["p1_midhip_arrow"].location[2])
    bpy.data.objects["p1_chest_arrow"].location = (loc[0], loc[1], bpy.data.objects["p1_chest_arrow"].location[2])
    bpy.data.objects["p1_head_arrow"].location = (loc[0], loc[1], bpy.data.objects["p1_head_arrow"].location[2])
    bpy.data.objects["p1_curve"].location = (loc[0], loc[1], bpy.data.objects["p1_curve"].location[2])
   
def offset_p2_smpl(self, context):
    for obj in bpy.data.objects:
        loc = context.scene.intergen_props.p2_offset
        if obj.name.startswith("p2_smpl"):            
            obj.location = loc
    
    bpy.data.objects["p2_disk"].location = (loc[0], loc[1], bpy.data.objects["p2_disk"].location[2])
    bpy.data.objects["p2_midhip_arrow"].location = (loc[0], loc[1], bpy.data.objects["p2_midhip_arrow"].location[2])
    bpy.data.objects["p2_chest_arrow"].location = (loc[0], loc[1], bpy.data.objects["p2_chest_arrow"].location[2])
    bpy.data.objects["p2_head_arrow"].location = (loc[0], loc[1], bpy.data.objects["p2_head_arrow"].location[2])
    bpy.data.objects["p2_curve"].location = (loc[0], loc[1], bpy.data.objects["p2_curve"].location[2])


def change_p1_body_color(self, context):
    assign_material(name="P1_SMPL_BODY_MATERIAL", color=context.scene.intergen_props.p1_body_color)

def change_p1_disk_color(self, context):
    assign_material(name="P1_DISK_MATERIAL", color=context.scene.intergen_props.p1_disk_color)

def change_p1_midhiparrow_color(self, context):
    assign_material(name="P1_MIDHIP_NORMAL_MATERIAL", color=context.scene.intergen_props.p1_midhiparrow_color)

def change_p1_chestarrow_color(self, context):
    assign_material(name="P1_CHEST_NORMAL_MATERIAL", color=context.scene.intergen_props.p1_chestarrow_color)

def change_p1_headarrow_color(self, context):
    assign_material(name="P1_HEAD_NORMAL_MATERIAL", color=context.scene.intergen_props.p1_headarrow_color)

def change_p1_pathcurve_color(self, context):
    assign_material(name="P1_CURVE_MATERIAL", color=context.scene.intergen_props.p1_path_color)




def change_p2_body_color(self, context):
    assign_material(name="P2_SMPL_BODY_MATERIAL", color=context.scene.intergen_props.p2_body_color)

def change_p2_disk_color(self, context):
    assign_material(name="P2_DISK_MATERIAL", color=context.scene.intergen_props.p2_disk_color)

def change_p2_midhiparrow_color(self, context):
    assign_material(name="P2_MIDHIP_NORMAL_MATERIAL", color=context.scene.intergen_props.p2_midhiparrow_color)

def change_p2_chestarrow_color(self, context):
    assign_material(name="P2_CHEST_NORMAL_MATERIAL", color=context.scene.intergen_props.p2_chestarrow_color)

def change_p2_headarrow_color(self, context):
    assign_material(name="P2_HEAD_NORMAL_MATERIAL", color=context.scene.intergen_props.p2_headarrow_color)

def change_p2_pathcurve_color(self, context):
    assign_material(name="P2_CURVE_MATERIAL", color=context.scene.intergen_props.p2_path_color)






# ------------------------------------------------------------------------
#    Store properties in the active scene
# ------------------------------------------------------------------------
class InterGenProperties(PropertyGroup):

    z_stage: bpy.props.FloatProperty(
        name="z_stage",
        description="Z coordinate for stage object",
        default=-1.09638,
        update = lambda self, context: set_z_stage(self, context)
    )

    z_disk: bpy.props.FloatProperty(
            name="z_disk",
            description="Z coordinate for disk objects",
            default=-1.093 + 0.007,
            update = lambda self, context: set_z_disk(self, context)
        )

    show_p1_disk : BoolProperty(
        name="show_p1_disk",
        description="Show or Hide Disk for person 1",
        default = True,
        update = lambda self, context: toggle_p1_disk(self, context)
        )
    
    show_p1_midhiparrow : BoolProperty(
        name="show_p1_midhip arrow",
        description="Show or Hide midhip arrow for person 1",
        default = True,
        update = lambda self, context: toggle_p1_midhiparrow(self, context)
        )
    
    show_p1_chestarrow : BoolProperty(
        name="show_p1_chest arrow",
        description="Show or Hide chest arrow for person 1",
        default = True,
        update = lambda self, context: toggle_p1_chestarrow(self, context)
        )
    
    show_p1_headarrow : BoolProperty(
        name="show_p1_head arrow",
        description="Show or Hide head arrow for person 1",
        default = True,
        update = lambda self, context: toggle_p1_headarrow(self, context)
        )
    
    show_p1_path : BoolProperty(
        name="show_p1_path",
        description="Show or Hide path for person 1",
        default = True,
        update = lambda self, context: toggle_p1_path(self, context)
        )
    




    show_p2_disk : BoolProperty(
        name="show_p2_disk",
        description="Show or Hide Disk for person 2",
        default = True,
        update = lambda self, context: toggle_p2_disk(self, context)
        )
    
    show_p2_midhiparrow : BoolProperty(
        name="show_p2_midhip arrow",
        description="Show or Hide midhip arrow for person 2",
        default = True,
        update = lambda self, context: toggle_p2_midhiparrow(self, context)
        )
    
    show_p2_chestarrow : BoolProperty(
        name="show_p2_chest arrow",
        description="Show or Hide chest arrow for person 2",
        default = True,
        update = lambda self, context: toggle_p2_chestarrow(self, context)
        )
    
    show_p2_headarrow : BoolProperty(
        name="show_p2_head arrow",
        description="Show or Hide head arrow for person 2",
        default = True,
        update = lambda self, context: toggle_p2_headarrow(self, context)
        )
    
    show_p2_path : BoolProperty(
        name="show_p2_path",
        description="Show or Hide path for person 2",
        default = True,
        update = lambda self, context: toggle_p2_path(self, context)
        )
    

    p1_offset: bpy.props.FloatVectorProperty(
        name="p1_offset",
        default=(0.27, 0.8, 0),
        description="P1 Offset",
        update = lambda self, context: offset_p1_smpl(self, context)
    )

    p2_offset: bpy.props.FloatVectorProperty(
        name="p2_offset",
        default=(0, -0.8, 0),
        description="P2 Offset",
        update = lambda self, context: offset_p2_smpl(self, context)
    )




    p1_body_color: bpy.props.FloatVectorProperty(
        name="p1_body_color",
        subtype='COLOR',
        size=4,
        default=(0, 0.216, 0.651, 1),
        min=0.0, max=1.0,
        description="Color for person 1",
        update = lambda self, context: change_p1_body_color(self, context)
    )

    p1_disk_color: bpy.props.FloatVectorProperty(
        name="p1_disk_color",
        subtype='COLOR',
        size=4,
        default=(0, 0.216, 0.216, 1),
        min=0.0, max=1.0,
        description="Color for person 1 disk",
        update = lambda self, context: change_p1_disk_color(self, context)
    )

    p1_midhiparrow_color: bpy.props.FloatVectorProperty(
        name="p1_midhiparrow_color",
        subtype='COLOR',
        size=4,
        default=(0.591, 0.031, 0.031, 1),
        min=0.0, max=1.0,
        description="Color for person 1 midhip arrow",
        update = lambda self, context: change_p1_midhiparrow_color(self, context)
    )

    p1_chestarrow_color: bpy.props.FloatVectorProperty(
        name="p1_chestarrow_color",
        subtype='COLOR',
        size=4,
        default=(0.695, 0.366, 0, 1),
        min=0.0, max=1.0,
        description="Color for person 1 chest arrow",
        update = lambda self, context: change_p1_chestarrow_color(self, context)
    )

    p1_headarrow_color: bpy.props.FloatVectorProperty(
        name="p1_headarrow_color",
        subtype='COLOR',
        size=4,
        default=(0.130, 0.590, 0.166, 1),
        min=0.0, max=1.0,
        description="Color for person 1 head arrow",
        update = lambda self, context: change_p1_headarrow_color(self, context)
    )

    p1_path_color: bpy.props.FloatVectorProperty(
        name="p1_path_color",
        subtype='COLOR',
        size=4,
        default=(0, 0.216, 0.651, 1),
        min=0.0, max=1.0,
        description="Color for person 1 path arrow",
        update = lambda self, context: change_p1_pathcurve_color(self, context)
    )




    p2_body_color: bpy.props.FloatVectorProperty(
        name="p2_body_color",
        subtype='COLOR',
        size=4,
        default=(0.63, 0.153, 0, 1),
        min=0.0, max=1.0,
        description="Color for person 2",
        update = lambda self, context: change_p2_body_color(self, context),
    )


    p2_disk_color: bpy.props.FloatVectorProperty(
        name="p2_disk_color",
        subtype='COLOR',
        size=4,
        default=(0.120, 0.051, 0.171, 1),
        min=0.0, max=1.0,
        description="Color for person 2 disk",
        update = lambda self, context: change_p2_disk_color(self, context)
    )

    p2_midhiparrow_color: bpy.props.FloatVectorProperty(
        name="p2_midhiparrow_color",
        subtype='COLOR',
        size=4,
        default=(0.591, 0.031, 0.031, 1),
        min=0.0, max=1.0,
        description="Color for person 2 midhip arrow",
        update = lambda self, context: change_p2_midhiparrow_color(self, context)
    )

    p2_chestarrow_color: bpy.props.FloatVectorProperty(
        name="p2_chestarrow_color",
        subtype='COLOR',
        size=4,
        default=(0.695, 0.366, 0, 1),
        min=0.0, max=1.0,
        description="Color for person 2 chest arrow",
        update = lambda self, context: change_p2_chestarrow_color(self, context)
    )

    p2_headarrow_color: bpy.props.FloatVectorProperty(
        name="p2_headarrow_color",
        subtype='COLOR',
        size=4,
        default=(0.130, 0.590, 0.166, 1),
        min=0.0, max=1.0,
        description="Color for person 2 head arrow",
        update = lambda self, context: change_p2_headarrow_color(self, context)
    )

    p2_path_color: bpy.props.FloatVectorProperty(
        name="p2_path_color",
        subtype='COLOR',
        size=4,
        default=(0.63, 0.153, 0, 1),
        min=0.0, max=1.0,
        description="Color for person 2 path arrow",
        update = lambda self, context: change_p2_pathcurve_color(self, context)
    )
    
    




class ClearSceneOperator(bpy.types.Operator):
    bl_idname = "object.clear_scene"
    bl_label = "Clear Scene"
    
    def execute(self, context):
        clear_scene()
        self.report({'INFO'}, "Operator Executed!")
        return {'FINISHED'}



class SelectAnimationFolderOperator(bpy.types.Operator, ImportHelper):
    bl_idname = "object.select_folder"
    bl_label = "Select Animation Folder"
    
    def execute(self, context):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        # Open the folder selection dialog
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        global BASE_PATH
        BASE_PATH = self.filepath  # Store the selected folder path
        self.report({'INFO'}, f"Selected Folder: {BASE_PATH}")
        return {'FINISHED'}
    



class AddAnimationOperator(bpy.types.Operator):
    bl_idname = "object.add_animation"
    bl_label = "Add Animation"
    
    def execute(self, context):
        scene = context.scene
        intergen_props = scene.intergen_props

        P1_OFFSET = intergen_props.p1_offset
        P2_OFFSET = intergen_props.p2_offset
        Z_STAGE = intergen_props.z_stage
        Z_DISK = intergen_props.z_disk


        P1_SMPL_BODY_COLOR = intergen_props.p1_body_color
        P1_DISK_COLOR = intergen_props.p1_disk_color        
        P1_MIDHIP_NORMAL_COLOR = intergen_props.p1_midhiparrow_color        
        P1_CHEST_NORMAL_COLOR = intergen_props.p1_chestarrow_color        
        P1_HEAD_NORMAL_COLOR = intergen_props.p1_headarrow_color 
        P1_CURVE_COLOR = intergen_props.p1_path_color

        P2_SMPL_BODY_COLOR = intergen_props.p2_body_color
        P2_DISK_COLOR = intergen_props.p2_disk_color
        P2_MIDHIP_NORMAL_COLOR = intergen_props.p2_midhiparrow_color
        P2_CHEST_NORMAL_COLOR = intergen_props.p2_chestarrow_color
        P2_HEAD_NORMAL_COLOR = intergen_props.p2_headarrow_color
        P2_CURVE_COLOR = intergen_props.p2_path_color


        clear_scene()



        bpy.ops.wm.obj_import(filepath=Paths.get_STAGE_FILE_PATH())
        stage_obj = bpy.context.selected_objects[0]
        stage_obj.name = "stage"
        stage_obj.location = (0, 0, Z_STAGE)

        assets_collection = create_collection("Assets")
        assets_collection.objects.link(stage_obj)
        bpy.context.scene.collection.objects.unlink(stage_obj)


        p1_smpl_objs = sorted([f for f in os.listdir(Paths.get_P1_SMPL_OBJS_PATH()) if f.endswith(".obj")])
        p2_smpl_objs = sorted([f for f in os.listdir(Paths.get_P2_SMPL_OBJS_PATH()) if f.endswith(".obj")])

        frame_start = 0
        num_frames = len(p1_smpl_objs)
        setup_scene(bpy.context.scene, frame_start, num_frames)




        p1_smpls = []
        p2_smpls = []

        p1_points = []
        p2_points = []

        p1_disk_obj = draw_obj("p1_disk", Paths.get_DISK_FILE_PATH())
        p2_disk_obj = draw_obj("p2_disk", Paths.get_DISK_FILE_PATH())
        p1_chest_arrow_obj = draw_obj("p1_chest_arrow", Paths.get_ARROW_FILE_PATH())
        p2_chest_arrow_obj = draw_obj("p2_chest_arrow", Paths.get_ARROW_FILE_PATH())
        p1_head_arrow_obj = draw_obj("p1_head_arrow", Paths.get_ARROW_FILE_PATH())
        p2_head_arrow_obj = draw_obj("p2_head_arrow", Paths.get_ARROW_FILE_PATH())
        p1_midhip_arrow_obj = draw_obj("p1_midhip_arrow", Paths.get_ARROW_FILE_PATH())
        p2_midhip_arrow_obj = draw_obj("p2_midhip_arrow", Paths.get_ARROW_FILE_PATH())

        assign_material(name="P1_DISK_MATERIAL", color=P1_DISK_COLOR, obj=p1_disk_obj)
        assign_material(name="P2_DISK_MATERIAL", color=P2_DISK_COLOR, obj=p2_disk_obj)
        assign_material(name="P1_MIDHIP_NORMAL_MATERIAL", color=P1_MIDHIP_NORMAL_COLOR, obj=p1_midhip_arrow_obj)
        assign_material(name="P2_MIDHIP_NORMAL_MATERIAL", color=P2_MIDHIP_NORMAL_COLOR, obj=p2_midhip_arrow_obj)
        assign_material(name="P1_CHEST_NORMAL_MATERIAL", color=P1_CHEST_NORMAL_COLOR, obj=p1_chest_arrow_obj)
        assign_material(name="P2_CHEST_NORMAL_MATERIAL", color=P2_CHEST_NORMAL_COLOR, obj=p2_chest_arrow_obj)
        assign_material(name="P1_HEAD_NORMAL_MATERIAL", color=P1_HEAD_NORMAL_COLOR, obj=p1_head_arrow_obj)
        assign_material(name="P2_HEAD_NORMAL_MATERIAL", color=P2_HEAD_NORMAL_COLOR, obj=p2_head_arrow_obj)

        for index, (p1_smpl_obj, p2_smpl_obj) in enumerate(zip(p1_smpl_objs, p2_smpl_objs)):

            frame_collection = create_collection(f"Frame_{index}")

            if P1_DRAW_SMPL:
                # P1_SMPL
                bpy.ops.wm.obj_import(filepath=os.path.join(Paths.get_P1_SMPL_OBJS_PATH(), p1_smpl_obj))    
                p1_smpl = bpy.context.selected_objects[0]
                p1_smpl.name = f"p1_smpl_{index+1}"
                p1_smpls.append(p1_smpl)
                bpy.ops.object.shade_smooth()  
                frame_collection.objects.link(p1_smpl)
                bpy.context.scene.collection.objects.unlink(p1_smpl)
                p1_smpl.location = p1_smpl.location + Vector((P1_OFFSET))
                assign_material(name="P1_SMPL_BODY_MATERIAL", color=P1_SMPL_BODY_COLOR, obj=p1_smpl)


                # P1_DISK
                center = get_smpl_center(p1_smpl)
                center = translate_obj(p1_disk_obj, center + Vector((P1_OFFSET)), Z_DISK)
                p1_disk_obj.keyframe_insert(data_path="location", frame=index)
                p1_points.append(center)

                # P1_MIDHIP_ARROW
                translate_obj(p1_midhip_arrow_obj, center, Z_DISK - 0.002)
                rotate_z_obj(p1_smpl, p1_midhip_arrow_obj, Normals.MIDHIP_INDEX)
                p1_midhip_arrow_obj.keyframe_insert(data_path="location", frame=index)
                p1_midhip_arrow_obj.keyframe_insert(data_path="rotation_euler", frame=index)

                # P1_CHEST_ARROW
                translate_obj(p1_chest_arrow_obj, center, Z_DISK - 0.004)
                rotate_z_obj(p1_smpl, p1_chest_arrow_obj, Normals.CHEST_INDEX)
                p1_chest_arrow_obj.keyframe_insert(data_path="location", frame=index)
                p1_chest_arrow_obj.keyframe_insert(data_path="rotation_euler", frame=index)

                # P1_HEAD_ARROW
                translate_obj(p1_head_arrow_obj, center, Z_DISK - 0.006)
                rotate_z_obj(p1_smpl, p1_head_arrow_obj, Normals.HEAD_INDEX)
                p1_head_arrow_obj.keyframe_insert(data_path="location", frame=index)
                p1_head_arrow_obj.keyframe_insert(data_path="rotation_euler", frame=index)


            if P2_DRAW_SMPL:
                # P2_SMPL
                bpy.ops.wm.obj_import(filepath=os.path.join(Paths.get_P2_SMPL_OBJS_PATH(), p2_smpl_obj))    
                p2_smpl = bpy.context.selected_objects[0]
                p2_smpl.name = f"p2_smpl_{index+1}"
                p2_smpls.append(p2_smpl)
                bpy.ops.object.shade_smooth()  
                frame_collection.objects.link(p2_smpl)
                bpy.context.scene.collection.objects.unlink(p2_smpl)
                p2_smpl.location = p2_smpl.location + Vector((P2_OFFSET))
                assign_material(name="P2_SMPL_BODY_MATERIAL", color=P2_SMPL_BODY_COLOR, obj=p2_smpl)

                # P2_DISK
                center = get_smpl_center(p2_smpl)
                center = translate_obj(p2_disk_obj, center + Vector((P2_OFFSET)), Z_DISK - 0.001)
                p2_disk_obj.keyframe_insert(data_path="location", frame=index)
                p2_points.append(center)

                # P2_MIDHIP_ARROW
                translate_obj(p2_midhip_arrow_obj, center, Z_DISK - 0.003)
                rotate_z_obj(p2_smpl, p2_midhip_arrow_obj, Normals.MIDHIP_INDEX)
                p2_midhip_arrow_obj.keyframe_insert(data_path="location", frame=index)
                p2_midhip_arrow_obj.keyframe_insert(data_path="rotation_euler", frame=index)

                # P2_CHEST_ARROW
                translate_obj(p2_chest_arrow_obj, center, Z_DISK - 0.005)
                rotate_z_obj(p2_smpl, p2_chest_arrow_obj, Normals.CHEST_INDEX)
                p2_chest_arrow_obj.keyframe_insert(data_path="location", frame=index)
                p2_chest_arrow_obj.keyframe_insert(data_path="rotation_euler", frame=index)

                # P2_HEAD_ARROW
                translate_obj(p2_head_arrow_obj, center, Z_DISK - 0.007)
                rotate_z_obj(p2_smpl, p2_head_arrow_obj, Normals.HEAD_INDEX)
                p2_head_arrow_obj.keyframe_insert(data_path="location", frame=index)
                p2_head_arrow_obj.keyframe_insert(data_path="rotation_euler", frame=index)



        print("OBJ IMPORT DONE!!!")

        all_objs = []
        if P1_DRAW_SMPL:
            all_objs.append(p1_smpls)
        if P2_DRAW_SMPL:
            all_objs.append(p2_smpls)


        p1_curve = draw_curve("p1_curve", p1_points)
        assign_material(name="P1_CURVE_MATERIAL", color=P1_CURVE_COLOR, obj=p1_curve)


        p2_curve = draw_curve("p2_curve", p2_points)
        assign_material(name="P2_CURVE_MATERIAL", color=P2_CURVE_COLOR, obj=p2_curve)


        print("CURVES DRAWN!!!")

        # for index in range(num_frames):
        for index in range(num_frames):
            frame_number = index + 1

            for obj_type in all_objs:
                for obj in obj_type:
                    obj.hide_viewport = True
                    obj.hide_render = True
                    obj.keyframe_insert(data_path="hide_viewport", frame=index)
                    obj.keyframe_insert(data_path="hide_render", frame=index)

                obj_type[index].hide_viewport = False
                obj_type[index].hide_render = False
                obj_type[index].keyframe_insert(data_path="hide_viewport", frame=index)
                obj_type[index].keyframe_insert(data_path="hide_render", frame=index)

        print("ANIMATIONS DONE!!!")
        print("ALL DONE!!!")

        self.report({'INFO'}, "Operator Executed!")
        return {'FINISHED'}
    



class ResetSettingsOperator(bpy.types.Operator):
    bl_idname = "object.reset_settings"
    bl_label = "Reset Settings"
    
    def execute(self, context):
        scene = context.scene
        intergen_props = scene.intergen_props

        intergen_props.z_stage = -1.09638
        intergen_props.z_disk = -1.093 + 0.007

        intergen_props.show_p1_disk = True
        intergen_props.show_p1_midhiparrow = True
        intergen_props.show_p1_chestarrow = True
        intergen_props.show_p1_headarrow = True
        intergen_props.show_p1_path = True

        intergen_props.show_p2_disk = True
        intergen_props.show_p2_midhiparrow = True
        intergen_props.show_p2_chestarrow = True
        intergen_props.show_p2_headarrow = True
        intergen_props.show_p2_path = True

        intergen_props.p1_offset = (0.27, 0.8, 0)
        intergen_props.p2_offset = (0, -0.8, 0)

        intergen_props.p1_body_color = (0, 0.216, 0.651, 1)
        intergen_props.p1_disk_color = (0, 0.216, 0.216, 1)
        intergen_props.p1_midhiparrow_color = (0.591, 0.031, 0.031, 1)
        intergen_props.p1_chestarrow_color = (0.695, 0.366, 0, 1)
        intergen_props.p1_headarrow_color = (0.130, 0.590, 0.166, 1)
        intergen_props.p1_path_color = (0, 0.216, 0.651, 1)

        intergen_props.p2_body_color = (0.63, 0.153, 0, 1)
        intergen_props.p2_disk_color = (0.120, 0.051, 0.171, 1)
        intergen_props.p2_midhiparrow_color = (0.591, 0.031, 0.031, 1)
        intergen_props.p2_chestarrow_color = (0.695, 0.366, 0, 1)
        intergen_props.p2_headarrow_color = (0.130, 0.590, 0.166, 1)
        intergen_props.p2_path_color = (0.63, 0.153, 0, 1)


        self.report({'INFO'}, "Operator Executed!")
        return {'FINISHED'}






class GlobalPanel(bpy.types.Panel):
    bl_label = "Global Settings"
    bl_idname = "OBJECT_PT_global_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CoShMDM'
    
    def draw(self, context):
        layout = self.layout  

        scene = context.scene
        intergen_props = scene.intergen_props
        layout.prop(intergen_props, "z_stage", text="Z-Stage")
        layout.prop(intergen_props, "z_disk", text="Z-Disk")

        layout = self.layout
        layout.operator("object.reset_settings")

        

        

class Person1Panel(bpy.types.Panel):
    bl_label = "Person 1 Properties"
    bl_idname = "OBJECT_PT_p1_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CoShMDM'
    
    def draw(self, context):
        layout = self.layout  

        scene = context.scene
        intergen_props = scene.intergen_props

        layout.prop(intergen_props, "p1_body_color", text="Body Color")
        layout.prop(intergen_props, "p1_disk_color", text="Disk Color")
        layout.prop(intergen_props, "p1_midhiparrow_color", text="Midhip Arrow Color")
        layout.prop(intergen_props, "p1_chestarrow_color", text="Chest Arrow Color")
        layout.prop(intergen_props, "p1_headarrow_color", text="Head Arrow Color")
        layout.prop(intergen_props, "p1_path_color", text="Path Curve Color")

        layout.prop(intergen_props, "show_p1_disk", text="Show Disk")
        layout.prop(intergen_props, "show_p1_midhiparrow", text="Show MidHip Orientation")
        layout.prop(intergen_props, "show_p1_chestarrow", text="Show Chest Orientation")
        layout.prop(intergen_props, "show_p1_headarrow", text="Show Head Orientation")
        layout.prop(intergen_props, "show_p1_path", text="Show Path Curve")

        layout.prop(intergen_props, "p1_offset", text="Set Offset")


        

class Person2Panel(bpy.types.Panel):
    bl_label = "Person 2 Properties"
    bl_idname = "OBJECT_PT_p2_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CoShMDM' 
    
    def draw(self, context):
        layout = self.layout  

        scene = context.scene
        intergen_props = scene.intergen_props

        layout.prop(intergen_props, "p2_body_color", text="Body Color")
        layout.prop(intergen_props, "p2_disk_color", text="Disk Color")
        layout.prop(intergen_props, "p2_midhiparrow_color", text="Midhip Arrow Color")
        layout.prop(intergen_props, "p2_chestarrow_color", text="Chest Arrow Color")
        layout.prop(intergen_props, "p2_headarrow_color", text="Head Arrow Color")
        layout.prop(intergen_props, "p2_path_color", text="Path Curve Color")
        
        layout.prop(intergen_props, "show_p2_disk", text="Show Disk")
        layout.prop(intergen_props, "show_p2_midhiparrow", text="Show MidHip Orientation")
        layout.prop(intergen_props, "show_p2_chestarrow", text="Show Chest Orientation")
        layout.prop(intergen_props, "show_p2_headarrow", text="Show Head Orientation")
        layout.prop(intergen_props, "show_p2_path", text="Show Path Curve")

        layout.prop(intergen_props, "p2_offset", text="Set Offset")







class InterGenPanel(bpy.types.Panel):
    bl_label = "CoShMDM Animations"
    bl_idname = "OBJECT_PT_integen_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CoShMDM'
    
    def draw(self, context):
        layout = self.layout
        layout.operator("object.clear_scene")
        # layout.label(text="Select folder containing animation objs.")
        layout.operator("object.select_folder")
        
        if BASE_PATH:
            layout.label(text=f"{BASE_PATH}")
        else:
            layout.label(text="No folder selected yet.")
        
        layout.operator("object.add_animation")

     






classes = [   
    InterGenProperties,
    ResetSettingsOperator,
    GlobalPanel,
    Person1Panel,
    Person2Panel,
    InterGenPanel,
    ClearSceneOperator,
    AddAnimationOperator,
    SelectAnimationFolderOperator,  
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.intergen_props = PointerProperty(type=InterGenProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.intergen_props


if __name__ == "__main__":
    register()

