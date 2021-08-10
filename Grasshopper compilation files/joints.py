"""Get the joints as list of solids to add or subtract from each plate in the model."""

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
            "Plate Joints", "Joints", """Get the joints as list of solids to add or subtract from each plate in the model.""", "Manis", "Properties")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("59a294f7-65ef-4a3f-b164-b2934bfbca40")
    
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
        
    
    def RegisterOutputParams(self, pManager):
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
        result = self.RunScript(p0)

        if result is not None:
            if not hasattr(result, '__getitem__'):
                self.marshal.SetOutput(result, DA, 0, True)
            else:
                self.marshal.SetOutput(result[0], DA, 0, True)
                self.marshal.SetOutput(result[1], DA, 1, True)
                self.marshal.SetOutput(result[2], DA, 2, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAJOgAACToAYJjBRwAAACdSURBVEhLvdNRCsJAFEPRWZOL7XbHpsmgHSO0eaMHHkiJt19tN/TpluuPbTsOv/lorSUvGH+u3le9Cg2mPM1yaDDlaZZDgylPsxwaTHma5dBgytMshwZTL+PhcVVzb7/zB1Q19/7zgvermnv7nWiWQ4MpT7McGkx5muXQYMrTLIcGU55mOTSY8jTLocGUNwbVi3x8QKv9/gXTXdDaEzvnhakppXfnAAAAAElFTkSuQmCC"
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, model):

        def list_to_datatree(raggedList):
            rl = raggedList
            result = DataTree[object]()
            for i in range(len(rl)):
                temp = []
                for j in range(len(rl[i])):
                    temp.append(rl[i][j])
                #print(i, " - ",temp)
                path = GH_Path(i)
                result.AddRange(temp, path)
            return result
        
        joints_positives = None
        joints_negatives = None
        joints_keys = None

        if model:
            model = copy.deepcopy(model)
            joints_positives = []
            joints_negatives = []
            joints_keys = []

            for plate in model.plates:
                joints_positives.append(plate.joints_positives)
                joints_negatives.append(plate.joints_negatives)
                joints_keys.append(plate.joints_keys)
            joints_positives = list_to_datatree(joints_positives)
            joints_negatives = list_to_datatree(joints_negatives)
            joints_keys = list_to_datatree(joints_keys)
        else: 
            self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'Waiting to get a model as input.')
        return (joints_positives, joints_negatives, joints_keys)


import GhPython
import System

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Plate Joints"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("1d8f273e-bbb8-44d3-83d7-d2f0e987d120")