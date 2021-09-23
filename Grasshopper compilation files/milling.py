"""Get topologic connections between plates in the model."""

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
            "Milling Contours", "Milling Contours", """Get plates milling contours.""", "Manis", "Properties")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("cb94896a-05f9-4c60-ac97-776b168be089")
    
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
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "top_milling_contour", "top_milling_contour", "Top milling contour.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "bottom_milling_contour", "bottom_milling_contour", "Bottom milling contour.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "top_milling_holes", "top_milling_holes", "Top milling holes.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "bottom_milling_holes", "bottom_milling_holes", "Bottom milling holes.")
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
                self.marshal.SetOutput(result[3], DA, 3, True)
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAACxIAAAsSAdLdfvwAAABzSURBVEhL3Y1BCsAwCAT7pj7W7xoN3RBae4lGMMKAu4JzMXPnJmIL732/YAq6f5gemFh3dIoWQyAjjZ8UAf6agtU5VKAB1BRgEUIFIE/QQ6AAf/MEQlGBhqcoKsASLQCmwEuKAH/HAmMUvwLkN6v3zQLiBrLj/EVqYYT7AAAAAElFTkSuQmCC"
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, model):

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

        top_milling_contour =  None
        bottom_milling_contour =  None
        top_milling_holes =  None
        bottom_milling_holes =  None

        if model:
            top_milling_contour =  []
            bottom_milling_contour =  []
            top_milling_holes =  []
            bottom_milling_holes =  []

            for i in range(len(model.plates)):
                top_milling_contour.append(model.plates[i].top_milling_contour)
                bottom_milling_contour.append(model.plates[i].bottom_milling_contour)
                top_milling_holes.append(model.plates[i].top_milling_holes)
                bottom_milling_holes.append(model.plates[i].bottom_milling_holes)

            top_milling_holes = list_to_datatree(top_milling_holes)
            bottom_milling_holes = list_to_datatree(bottom_milling_holes)

        else: self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'Waiting to get a model as input.')

        return (top_milling_contour, bottom_milling_contour, top_milling_holes, bottom_milling_holes)


import GhPython
import System

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Milling contours"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("5ca541c1-cd94-460b-8cb8-17306182c878")