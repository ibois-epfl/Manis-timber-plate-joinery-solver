"""Get the compatible vector of assembly of each plate in the model according to the sequence."""

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
            "Assembly Vectors", "Assembly", """Get the compatible vector of assembly of each plate in the model according to the sequence.""", "Manis", "Properties")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("e0d11629-ce08-4079-abbd-d04a3c8be866")
    
    def SetUpParam(self, p, name, nickname, description):
        p.Name = name
        p.NickName = nickname
        p.Description = description
        p.Optional = True
    
    def RegisterInputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "module", "module", "Plate module.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
    
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_Vector()
        self.SetUpParam(p, "assembly", "assembly", "Assembly vector of each plate in the module.")
        self.Params.Output.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "relatives", "relatives", "Neighbours concerned by the assembly.")
        self.Params.Output.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "spaces", "spaces", "Intersection of insertion spaces with relatives.")
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
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAJOgAACToAYJjBRwAAABgSURBVEhL7Y1BCoAwDAT7Jh/b71aDHjROui3UkxkYKKHslIP2sXhc6flYTQYkGZBkQDId2Gp9qMjAdY35QcAPKj0yYNAQSQwFDBq8GzEcMGjY7PEKKP04/QnEIzo/XtoOlgiQW/tjAjsAAAAASUVORK5CYII="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))


    def RunScript(self, module):

        assembly = None
        relatives = None
        spaces = None

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

        if module:
            assembly = module.assembly_vectors
            relatives = list_to_datatree(module.assembly_relatives)
            spaces = list_to_datatree(module.assembly_spaces)
        else: 
            self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'Waiting to get a module as input.')
        return (assembly, relatives, spaces)


import GhPython
import System

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Assembly Vectors"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("1237da5a-deaa-4f59-9a40-b5844136a364")