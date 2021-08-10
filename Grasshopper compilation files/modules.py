from ghpythonlib.componentbase import dotnetcompiledcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import math
import copy
import ast
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper.Kernel.GH_Convert import ObjRefToGeometry, ToGHBrep
from Grasshopper.Kernel import GH_Conversion 
import scriptcontext

class MyComponent(component):
    def __new__(cls):
        instance = Grasshopper.Kernel.GH_Component.__new__(cls,
            "Get Modules", "Modules", """Get modules from model.""", "Manis", "Assembly")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("8b1633ef-c5f8-4fd7-b75c-d757d5131433")
    
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
        
        p = Grasshopper.Kernel.Parameters.Param_Integer()
        self.SetUpParam(p, "module_id", "module_id", "(Optional) ID of the module. If none is provided, all modules will be retrieved.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
    
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "module", "module", "Module(s) inheriting model functions.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_String()
        self.SetUpParam(p, "sequence", "sequence", "Sub-sequence of the module.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "step", "step", "Tag representing the position of the module in the full assembly sequence. 'M' stands for the final step of the Model.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Brep()
        self.SetUpParam(p, "breps", "breps", "Module breps.")
        self.Params.Output.Add(p)
        
    
    def SolveInstance(self, DA):
        p0 = self.marshal.GetInput(DA, 0)
        p1 = self.marshal.GetInput(DA, 1)
        result = self.RunScript(p0, p1)

        if result is not None:
            if not hasattr(result, '__getitem__'):
                self.marshal.SetOutput(result, DA, 0, True)
            else:
                self.marshal.SetOutput(result[0], DA, 0, True)
                self.marshal.SetOutput(result[1], DA, 1, True)
                self.marshal.SetOutput(result[2], DA, 2, True)
                self.marshal.SetOutput(result[3], DA, 3, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAACxIAAAsSAdLdfvwAAADESURBVEhLzZDREYMwDEOZqTN1JmbqTP0JloMhMbFB+ehVdw+TKLYCSynlMSI8OEaDItDw/bwphoMijlsxjAZFQHIrlHq7WnXP8J5uzGBDBK+LpxsM1oOqA/qv7DzIFhRMwMx/7YbcBuwKDZH3ngdERtrEnI2MpImDDXitKwUdQDMRANXbnetWF88WFFQANhisB1UHuK9tPcgWFEyAKTRE3vujgMhIm5izkZE21Xqs/dmG08QrEdDJne0VDXFNvw1ovZyybMNIxM83vg1XAAAAAElFTkSuQmCC"
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, model, module_id):
        
        def round_vector(vector, n=3):
            """round x,y,z components of a vector to n decimals"""
            vec = copy.deepcopy(vector)
            for i in range(len(vec)):
                vec[i] = round(vec[i],n)
            return vec

        def list_to_datatree(raggedList):
            """Python to Grasshopper (from Chen Jingcheng)"""
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

        module = None
        sequence = None
        step = None
        breps = None
        
        if model:
            model = copy.deepcopy(model)
        
            if module_id != None:
                module_id = module_id % len(model.modules)
                module = model.modules[module_id]
                breps = model.modules[module_id].breps
                step = str(model.modules[module_id].step)
                sequence = str(model.modules[module_id].sequence)
                assembly_vectors = []
                for i in range(len(model.modules[module_id].assembly_vectors)):
                    assembly_vectors.append(round_vector(model.modules[module_id].assembly_vectors[i]))
        
            else:
                module = []
                breps = []
                sequence = []
                step = []
                assembly_vectors = []
                for mod in model.modules:
                    module.append(mod)
                    breps.append(mod.breps)
                    sequence.append(str(mod.sequence))
                    step.append(str(mod.step))
                    assembly_vectors.append(mod.assembly_vectors)
                breps = list_to_datatree(breps)
                assembly_vectors = list_to_datatree(assembly_vectors)
        
        # return outputs if you have them; here I try it for you:
        return (module, sequence, step, breps)


import GhPython
import System

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Modules"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("8b84a228-8858-4a01-9624-9af6a0036530")