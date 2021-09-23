"""Gives a preview of the assembly sequence."""

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

__author__ = "Nicolas Rogeau"
__laboratory__ = "IBOIS, Laboratory for Timber Construction" 
__university__ = "EPFL, Ecole Polytechnique Federale de Lausanne"
__funding__ = "NCCR Digital Fabrication, ETH Zurich"
__version__ = "2020.01"

class MyComponent(component):
    def __new__(cls):
        instance = Grasshopper.Kernel.GH_Component.__new__(cls,
            "Merge constraints", "Constraints", """Merge custom constraints according to joints type (use this as input for the plate model).""", "Manis", "Assembly")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("cd1d2abe-32b8-4855-993a-a6dfaa5fc25f")
    
    def SetUpParam(self, p, name, nickname, description):
        p.Name = name
        p.NickName = nickname
        p.Description = description
        p.Optional = True
    
    def RegisterInputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "FF", "FF", "Constraint for face-to-face contacts.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "FS", "FS", "Constraint for face-to-side contacts.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "ES", "ES", "Constraint for edge-to-side contacts.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "SS", "SS", "Constraint for side-to-side contacts.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "IN", "IN", "Constraint for intersecting contacts.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "constraints", "constraints", "List of constraints for all contact types.")
        self.Params.Output.Add(p)     
    
    def SolveInstance(self, DA):
        p0 = self.marshal.GetInput(DA, 0)
        p1 = self.marshal.GetInput(DA, 1)
        p2 = self.marshal.GetInput(DA, 2)
        p3 = self.marshal.GetInput(DA, 3)
        p4 = self.marshal.GetInput(DA, 4)
        result = self.RunScript(p0, p1, p2, p3, p4)

        if result is not None:
            self.marshal.SetOutput(result, DA, 0, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAACxIAAAsSAdLdfvwAAACnSURBVEhL7Y7RDQIxDEOZiZmYqTMxEz8hhgR8qa9XPu4DqZVelSaO3YuZTeMH17sQc4Vs7rECDlkBu5BxReoZ2UzIyB73m6wDuQ90k5Zhlox6Qe/VNULMJtVsNHO2fptHiJQBmJ07fUAO1RLX9Z0194I+oIp5YVRXYvYNiIYUg5xXlBaQxu/B7xloGKVhQuf3ZACA7kft63wWT+Hamp3JCjjk3wOaPQFb8mU3QniiBQAAAABJRU5ErkJggg=="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, FF,FS,ES,SS,IN):

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

        constraints = [[], [], [], [], []]
        if FF: constraints[0] = [FF]
        if FS: constraints[1] = [FS]
        if ES: constraints[2] = [ES]
        if SS: constraints[3] = [SS]
        if IN: constraints[4] = [IN]
        constraints = list_to_datatree(constraints)
        return constraints


import GhPython
import System

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Merge constraints"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("62b9926b-9fca-4d8a-bd98-9ec62d84be28")