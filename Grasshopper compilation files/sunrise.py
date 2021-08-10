"""Create Half-lap Joints between plates with Side to Face connections"""

from ghpythonlib.componentbase import dotnetcompiledcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import math
import copy
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper.Kernel.GH_Convert import ObjRefToGeometry, ToGHBrep
from Grasshopper.Kernel import GH_Conversion 
import scriptcontext

__author__ = "Nicolas Rogeau"
__laboratory__ = "IBOIS, Laboratory for Timber Construction" 
__university__ = "EPFL, Ecole Polytechnique Federale de Lausanne"
__funding__ = "NCCR Digital Fabrication, ETH Zurich"
__version__ = "2020.01"

class MyComponent(component):
    def __new__(cls):
        instance = Grasshopper.Kernel.GH_Component.__new__(cls,
            "Add Sunrise dovetail joint", "Sunrise", """Create Sunrise dovetail joints for edgewise connections.""", "Manis", "Joints")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("0c5d7435-92b0-4b19-99f5-cbff275e556a")
    
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
        self.SetUpParam(p, "tenon_number", "tenon_number", "The number of tenons to create for each contact zones.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "tenon_width", "tenon_width", "The width of each tenon.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "tenon_spacing", "tenon_spacing", "The space between two tenons (= the width of the tenons of the second plate).")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "spread_angle", "spread_angle", "Maximum angle between the most extreme tenons giving the sun-like pattern.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Vector()
        self.SetUpParam(p, "assembly_vector", "assembly_vector", "Optional vector of insertion to force assembly direction.")
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
        result = self.RunScript(p0, p1, p2, p3, p4, p5, p6)

        if result is not None:
            if not hasattr(result, '__getitem__'):
                self.marshal.SetOutput(result, DA, 0, True)
            else:
                self.marshal.SetOutput(result[0], DA, 0, True)
                self.marshal.SetOutput(result[1], DA, 1, True)
                self.marshal.SetOutput(result[2], DA, 2, True)
                self.marshal.SetOutput(result[3], DA, 3, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAACxIAAAsSAdLdfvwAAADpSURBVEhL7ZJBFoIwDES7de3GWwhyJU8kkuKNPJObyLTkGUooLIorFv/xOpnJ9AHuRsR7chSschSs8t+CpiOuPPGVuolpC8ggix1aHwr6cfEzCHXXjiaco5Yn+pBBFhp2xR09O7TWvf8N/CvcBOfGRz2HeMLtQ3a86LAT2v7f4HI+sabCKxtuhafW06CeLWWA+7zvDMRY04MbasNZz6wCPUcGWSmR2awARr0Az3S5kHqQNQsgYCAF2iBhi9QnBbpkUrD19QipD9n0NYWPnAvpmUXOj/PsLyqNY94XUyyJKZbEFEtiiuVg9wXnkWSiSKTDTAAAAABJRU5ErkJggg=="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, model, plates_pairs, tenon_number, tenon_width, tenon_spacing, spread_angle, forced_direction):

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

            model.add_sunrise(plates_pairs, 
                tenon_number,
                tenon_width, 
                tenon_spacing,
                spread_angle,
                forced_direction)

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



import GhPython
import System

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Add Sunrise Dovetail Joint"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("0c5d7435-92b0-4b19-99f5-cbff275e666a")