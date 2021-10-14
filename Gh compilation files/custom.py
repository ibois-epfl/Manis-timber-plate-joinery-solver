"""Create Custom Joints between plates with Side to Face connections"""

from ghpythonlib.componentbase import dotnetcompiledcomponent as component
import Grasshopper, GhPython
import System
import copy
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path

__author__ = "Nicolas Rogeau"
__laboratory__ = "IBOIS, Laboratory for Timber Construction" 
__university__ = "EPFL, Ecole Polytechnique Federale de Lausanne"
__funding__ = "NCCR Digital Fabrication, ETH Zurich"
__version__ = "2021.09"

class MyComponent(component):
    def __new__(cls):
        instance = Grasshopper.Kernel.GH_Component.__new__(cls,
            "Add Custom Joints", "Custom", """Create Custom Joints between plates with Side to Face connections""", "Manis", "Joints")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("2c7ef0b7-ad80-419f-a24b-a33ac91edaa1")
    
    def SetUpParam(self, p, name, nickname, description):
        p.Name = name
        p.NickName = nickname
        p.Description = description
        p.Optional = True
    
    def RegisterInputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "model", "model", "Plate model.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_String()
        self.SetUpParam(p, "plates_pairs", "plates_pairs", "(Optional) List of pair of plates (a,b) to only add joints between those plates.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Integer()
        self.SetUpParam(p, "joint_number", "joint_number", "The number of joints to create for each contact zones.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "joint_width", "joint_width", "The width of the joint. The tile will be scaled to fit that width.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "joint_space", "joint_space", "(Optional) the space between two joints.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "joint_shift", "joint_shift", "Script input joint_shift.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Geometry()
        self.SetUpParam(p, "joint_drawing", "joint_drawing", "The tile representing the joint as an open polyline.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Geometry()
        self.SetUpParam(p, "hole_sides", "hole_sides", "(Optional) The tile representing the sides of the hole as two polylines.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Boolean()
        self.SetUpParam(p, "mirror", "mirror", "(Optional) Mirror the tile.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Boolean()
        self.SetUpParam(p, "reverse", "reverse", "(Optional) Reverse the tile.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
    
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "model", "model", "Updated plate model.")
        self.Params.Output.Add(p)
               
        p = Grasshopper.Kernel.Parameters.Param_Brep()
        self.SetUpParam(p, "joints_positives", "joints_positives", "The joints to add to each plate.")
        self.Params.Output.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Brep()
        self.SetUpParam(p, "joints_negatives", "joints_negatives", "The joints to subtract from each plate.")
        self.Params.Output.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Brep()
        self.SetUpParam(p, "joints_keys", "joints_keys", "The keys to insert in each plate.")
        self.Params.Output.Add(p)
    
    def SolveInstance(self, DA):
        p0 = self.marshal.GetInput(DA, 0)
        p1 = self.marshal.GetInput(DA, 1)
        p2 = self.marshal.GetInput(DA, 2)
        p3 = self.marshal.GetInput(DA, 3)
        p4 = self.marshal.GetInput(DA, 4)
        p5 = self.marshal.GetInput(DA, 5)
        p6 = self.marshal.GetInput(DA, 6)
        p7 = self.marshal.GetInput(DA, 7)
        p8 = self.marshal.GetInput(DA, 8)
        p9 = self.marshal.GetInput(DA, 9)
        result = self.RunScript(p0, p1, p2, p3, p4, p5, p6, p7, p8, p9)

        if result is not None:
            if not hasattr(result, '__getitem__'):
                self.marshal.SetOutput(result, DA, 0, True)
            else:
                self.marshal.SetOutput(result[0], DA, 0, True)
                self.marshal.SetOutput(result[1], DA, 1, True)
                self.marshal.SetOutput(result[2], DA, 2, True)
                self.marshal.SetOutput(result[3], DA, 3, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAJOgAACToAYJjBRwAAAC4SURBVEhL7ZBdDoMwDINzJH6utBtttOxGO9NeOjmBrtBUQQXeaul7WO3YaDQ4F+6kDZi0ARN1gIgyajKcS3+Mkwudj8epNkcAb2JF8W2WG9y8FL/4oZ+e1QO4hYcudKKbsNrP/m/4d/UAblcfnfxvoHQPwnITtSkHeBMrKutZujhoUhiw+X4ewQJBbUDL7mkDJvcPIHgEbeAgprLyFXgSOSe1HMCTyDlxUaH8kgGoNHCZ0i9OMUT0A99vGqal8sudAAAAAElFTkSuQmCC"
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, model, plates_pairs, joint_number, joint_width, joint_space, joint_shift, joint_drawing, hole_sides, mirror, reverse):

        def list_to_datatree(raggedList):
            rl = raggedList
            result = DataTree[object]()
            for i in range(len(rl)):
                temp = []
                for j in range(len(rl[i])):
                    temp.append(rl[i][j])
                path = GH_Path(i)
                result.AddRange(temp, path)
            return result

        joints_positives = []
        joints_negatives = []
        joints_keys = []

        if model:
            model = copy.deepcopy(model)
            if joint_drawing:
                if hole_sides == None or len(hole_sides) == 2:
                    model.add_custom_FS_joints(plates_pairs, 
                        joint_number,
                        joint_width, 
                        joint_space,
                        joint_shift,
                        joint_drawing, 
                        hole_sides,
                        mirror,
                        reverse)
                    
                    for plate in model.plates:
                        joints_positives.append(plate.joints_positives)
                        joints_negatives.append(plate.joints_negatives)
                        joints_keys.append(plate.joints_keys)
                    joints_positives = list_to_datatree(joints_positives)
                    joints_negatives = list_to_datatree(joints_negatives)
                    joints_keys = list_to_datatree(joints_keys)

                else: self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'joint_holes list should count two elements.')
            else: self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'Waiting to get joint_drawing as input.')
        else: self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'Waiting to get a model as input.')

        return (model, joints_positives, joints_negatives, joints_keys)

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Add Custom Joint"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("b8b12d63-f047-41aa-95ea-b74fc2054eba")