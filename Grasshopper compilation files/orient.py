"""Scale all the plates of the model with their attributes."""

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
            "Orient Plates", "Orient", """Move and/or rotate all the plates of the model with their attributes.""", "Manis", "Transform")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("3a60a4cd-58e1-4a48-b616-04651544e3d7")
    
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
        
        p = Grasshopper.Kernel.Parameters.Param_Plane()
        self.SetUpParam(p, "ref", "ref", "Plane of reference.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Plane()
        self.SetUpParam(p, "plane", "plane", "Target Plane")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
    
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "model", "model", "Transformed plate model.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "breps", "breps", "Transformed Breps.")
        self.Params.Output.Add(p)
        
    
    def SolveInstance(self, DA):
        p0 = self.marshal.GetInput(DA, 0)
        p1 = self.marshal.GetInput(DA, 1)
        p2 = self.marshal.GetInput(DA, 2)
        result = self.RunScript(p0, p1, p2)

        if result is not None:
            if not hasattr(result, '__getitem__'):
                self.marshal.SetOutput(result, DA, 0, True)
            else:
                self.marshal.SetOutput(result[0], DA, 0, True)
                self.marshal.SetOutput(result[1], DA, 1, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAACxIAAAsSAdLdfvwAAALrSURBVEhLvZRfSFNhGMbnmKzBTpSw4ZhBhCjm3JypdNOFJYqiiSXzUogwGOwqigLFKQiFYoqkgpDkwKkE/SGIKAbF2IXaLioIw0S66KZoOXSbRbw97/mTnjrHCUkP/OCc93u/5/m27/uOgYhU6CgPXAABUMMFWefAEelRR1kCbGAEvAYTYAiMAiM4b7fbv+Xm5n7C81mgrSwBj0AEWMW3bXVbLBZaWlqk+fk5MpvNPFE7RCfgNLgHPoJ+EAKKut1uNy0tLqJdUiwWI6fT+RVjzVLLDmFcK4B1E3DhJ+D/mtXt8bhpc3MTrWpxiPxLrkqtsjCmF2ACl0AtEMAsm39YWUGbtjjkeEkJm1wDklDXC1DEGzpXV1enufI/lVxfV0KuiLNR2y2AT9Fce7uPMpkMhomWl5cpEAiQ3++nzs5OCoVCYn2nuMflcrHZ9WwBx8BaX18fhiQlEgkKh8M0MDBARqORWlpa5JFtpdNpqq+vZ7PZbAEsm8lkivX09NDW1hZaiGZmZqigoIBaW1vJ5/OJNUVs3tbWxkZhIOwlgGUHa42NjTQ9PU2CIFAkEqFoNEpTU1OYJmljY4Nqa8+wyXNwB1j2GsDi/XhjtVopHo+jVa0VnK6ysjI2eAq+ACXI8Ba83wN8kX6AFw0NDZRKpWRraeWy+Q2QAM/Ad/AOGJL2mhpyNDXpIhQVkSEnhw1egoNg3ustp9XVVVpYWFDMuwB/Ui6Ck4ADnMCQLMUpqRgf18TR3EwWbKhRuqWPeYKsYGFhIfE3Cc9srsgD4oB/RQ4XkqW9vVQxNqbCMzREhysrRfPSYFArgMU39i64DW6BJ4BX/gDwnonSDMirqiKhuJjKh4fJOzqqF8C6DF4BXvVDcAqopArwDA5SXnU1HfJ6qXxkRKxlCcgqVQBvKKOY73vA0Y4OKunq+v2+7wFa7AzAsf/rcu7G/wlw9fdT5eSkLicmJv4p4LPZZksdcDj0yc9P4San0Xtfy0QfMvwCxQCYu1zKcmEAAAAASUVORK5CYII="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, model, ref, target):

        breps = None
        if ref == None : ref = rs.PlaneFromFrame((0,0,0), (1,0,0), (0,1,0))
        if target == None : target = rs.PlaneFromFrame((0,0,0), (1,0,0), (0,1,0))
        if model:
        
            model = copy.deepcopy(model)
            model.transform(mode = 'Orient', origin = ref, target = target)
        
            breps = []
            for i in range(model.count):
                breps.append(model.plates[i].brep)
        else: 
            self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'Waiting to get a model as input.')
        return (model, breps)


import GhPython
import System

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Orient Plates"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("93cc54b2-33ce-4877-b719-2a62c9f79a7f")
