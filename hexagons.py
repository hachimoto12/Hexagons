"""
MIT License

Copyright (c) 2020 hachimoto12

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import numpy as np
import bpy
import bmesh
from bpy_extras.object_utils import AddObjectHelper


bl_info = {
    "name": "Hexagons",
    "author": "Hachimoto12",
    "version": (0, 0, 0),
    "blender": (2, 80, 0),
    "location": "3D Viewport > Add > Mesh",
    "description": "This addon creates hexagons mesh.",
    "wiki_url": "https://github.com/hachimoto12/Hexagons",
    "warning": "",
    "tracker_url": "",
    "category": "Add Mesh"
}


def base_hexagon(height):
    rad60 = np.deg2rad(60)
    degs = [rad60*i for i in range(6)]
    
    x = np.cos(degs)
    y = np.sin(degs)
    z = np.zeros(len(degs))
    verts = np.vstack((np.zeros((3)), np.vstack((x, y, z)).T))
    
    faces = np.array((
        (0, 1, 2),
        (0, 2, 3),
        (0, 3, 4),
        (0, 4, 5),
        (0, 5, 6),
        (0, 6, 1),
    ))

    if height > 0.0:
        tmp_verts = verts.copy()
        tmp_verts[:, 2] = -height
        verts = np.vstack((verts, tmp_verts))
        
        st_idx = len(degs)+1
        tmp_faces = faces.copy() + st_idx
        side_faces = (
            (1, st_idx+1, st_idx+2),
            (2, st_idx+2, 1),
            (2, st_idx+2, st_idx+3),
            (3, st_idx+3, 2),
            (3, st_idx+3, st_idx+4),
            (4, st_idx+4, 3),
            (4, st_idx+4, st_idx+5),
            (5, st_idx+5, 4),
            (5, st_idx+5, st_idx+6),
            (6, st_idx+6, 5),
            (6, st_idx+6, st_idx+1),
            (1, st_idx+1, 6),
        )
        faces = np.vstack((faces, tmp_faces))
        faces = np.vstack((faces, side_faces))

    return verts, faces


from bpy.props import (
    BoolProperty,
    BoolVectorProperty,
    EnumProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
)


class HexagonsMesh(bpy.types.Operator):
    bl_idname = "mesh.primitive_hexagons_mesh"
    bl_label = "Hexagons"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Create hexagons mesh."

    row: IntProperty(
        name="Row",
        description="Number of row",
        min=2,
        default=2,
    )
    column: IntProperty(
        name="Column",
        description="Number of column",
        min=2,
        default=2,
    )
    scale: FloatProperty(
        name="Scale",
        description="Scale",
        min=0.01, max=100.0,
        default=1.0
    )
    space: FloatProperty(
        name="Space",
        description="Hex Spacing",
        min=0, max=100.0,
        default=0.1
    )
    height: FloatProperty(
        name="Height",
        description="Hex Height",
        min=0,
        default=0
    )
    layers: BoolVectorProperty(
        name="Layers",
        description="Object Layers",
        size=20,
        options={"HIDDEN", "SKIP_SAVE"},
    )
    
    align_items = (
        ("WORLD", "World", "world"),
        ("VIEW", "View", "view"),
        ("CURSOR", "3D Cursor", "3D Cursor"),
    )
    align: EnumProperty(
        name="Align",
        items=align_items,
        default="WORLD",
        update=AddObjectHelper.align_update_callback,
    )
    location: FloatVectorProperty(
        name="Location",
        subtype="TRANSLATION",
    )
    rotation: FloatVectorProperty(
        name="Rotation",
        subtype="EULER",
    )

    def execute(self, context):
        verts, faces = base_hexagon(self.height)
    
        mesh = bpy.data.meshes.new('Hexagons')
        bm = bmesh.new()

        rad30 = np.deg2rad(30)
        edge_middle = self.get_edge_middle(
            np.zeros((3)),
            np.array((np.cos(rad30), np.sin(rad30), 0)),
            verts[1],
            verts[2]
        )

        y_max = np.sin(np.deg2rad(60))

        verts[:, 0:2] *= self.scale
        edge_middle *= self.scale
        y_max *= self.scale

        for c in range(self.column):
            c_space = self.space if c != 0 else 0
            for r in range(self.row):
                r_space = self.space if r != 0 else 0
                for vert in verts:
                    x = vert[0] + edge_middle[0]*2*r + r_space*r
                    y = vert[1] + (y_max*c) + c_space*c
                    if r % 2 == 0:
                        y += edge_middle[1]*2*c
                    else:
                        y += edge_middle[1]*2*(c+1) + self.space/2
                    bm.verts.new([x, y, vert[2]])

        bm.verts.ensure_lookup_table()
        for i in range(self.row*self.column):
            for face in faces:
                bm.faces.new([bm.verts[f+(len(verts)*i)] for f in face])
        mesh.

        bm.to_mesh(mesh)
        mesh.update()
        
        from bpy_extras import object_utils
        object_utils.object_data_add(context, mesh, operator=self)
        
        return {'FINISHED'}

    def get_edge_middle(self, p1, p2, p3, p4):
        det = (p1[0] - p2[0]) * (p4[1] - p3[1]) - (p4[0] - p3[0]) * (p1[1] - p2[1])
        t = ((p4[1] - p3[1]) * (p4[0] - p2[0]) + (p3[0] - p4[0]) * (p4[1] - p2[1])) / det
        x = t * p1[0] + (1.0 - t) * p2[0]
        y = t * p1[1] + (1.0 - t) * p2[1]
        return np.array([x, y, 0])


def menu_func(self, context):
    self.layout.operator(HexagonsMesh.bl_idname, icon="MESH_ICOSPHERE")


def register():
    bpy.utils.register_class(HexagonsMesh)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)
    
    
def unregister():
    bpy.utils.unregister_class(HexagonsMesh)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    

if __name__ == '__main__':
    register()
