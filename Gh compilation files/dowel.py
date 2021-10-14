"""Create Dowel Joints between plates with Face to Face connections"""

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
            "Add Dowel Joint", "Dowel", """Create Dowel Joints between plates with Face to Face connections""", "Manis", "Joints")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("f7337d23-a306-4630-a218-cb7208b3bbd0")
    
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
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "dowel_number", "dowel_number", "The number of dowels to create for each contact zones.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "dowel_radius", "dowel_radius", "The radius of the dowels.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "dowel_tolerance", "dowel_tolerance", "The distance between the border of the hole and the dowel ")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "dowel_retreat_1", "dowel_retreat_1", "The distance which separate the top of the surface of the first plate to one side of the dowel.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "dowel_retreat_2", "dowel_retreat_2", "The distance which separate the top of the surface of the second plate to the one side of the dowel.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "circle_radius", "circle_radius", "(In the case of several dowels) The radius of the circle on which the dowels are laying.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "circle_rotation", "circle_rotation", "(In the case of several dowels) The rotation of the circle on which the dowels are laying.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "dowel_angle_1", "dowel_angle_1", "The rotation of the dowel in the plane of the plate.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "dowel_angle_2", "dowel_angle_2", "The rotation of the dowel through the plate.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Boolean()
        self.SetUpParam(p, "parallel", "parallel", "Align all dowels if True. Otherwise, the inclination of the dowels is directed towards the center of the joint.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Curve()
        self.SetUpParam(p, "tile", "tile", "(Optional) Geometric tile as polyline to customize the shape of the dowel. Tile should be drawn scale and centered on the world origin.")
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
        p10 = self.marshal.GetInput(DA, 10)
        p11 = self.marshal.GetInput(DA, 11)
        p12 = self.marshal.GetInput(DA, 12)
        result = self.RunScript(p0, p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12)

        if result is not None:
            if not hasattr(result, '__getitem__'):
                self.marshal.SetOutput(result, DA, 0, True)
            else:
                self.marshal.SetOutput(result[0], DA, 0, True)
                self.marshal.SetOutput(result[1], DA, 1, True)
                self.marshal.SetOutput(result[2], DA, 2, True)
                self.marshal.SetOutput(result[3], DA, 3, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAJOgAACToAYJjBRwAAADISURBVEhL7Y9BDsIgFETZunbjLbTlSt5IC/VGnskNMh8maeHTVneavmSS8meYT83OzpRQaDPlxaaI5mXV9M6FLYrRXJ8WaD76KqYhO7hw8S6c3TC7DMVorv94wZiL7xLshpuce4dzmrGA4JtzZjBDXwVe3I1eQlhi/UP+Amfr05wFBN+cM4MZ+ipQuqbWgtJHnwbNVRHNW5BKeD2vM2FGNL8laVPQgrn+lxdMVfotxayKGv5Gua9CXnk6HkQ8l6K/pJjb+W+MeQOOdDulf6sO+wAAAABJRU5ErkJggg=="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, model, plates_pairs, dowel_number, dowel_radius, dowel_tolerance, dowel_retreat_1, dowel_retreat_2, circle_radius, circle_rotation, dowel_angle_1, dowel_angle_2, parallel, tile):
        
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
            model.add_dowels(plates_pairs, 
                dowel_number,
                dowel_radius, 
                dowel_tolerance, 
                dowel_retreat_1, 
                dowel_retreat_2, 
                circle_radius, 
                circle_rotation, 
                dowel_angle_1,
                dowel_angle_2,
                parallel,
                tile)

            for plate in model.plates:
                joints_positives.append(plate.joints_positives)
                joints_negatives.append(plate.joints_negatives)
                joints_keys.append(plate.joints_keys)
            joints_positives = list_to_datatree(joints_positives)
            joints_negatives = list_to_datatree(joints_negatives)
            joints_keys = list_to_datatree(joints_keys)

        else: 
            self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'Waiting to get a model as input.')
        return (model, joints_positives, joints_negatives, joints_keys)

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Add Dowel Joint"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("791715cb-89d3-4f3d-9cdc-cae46be64cb4")