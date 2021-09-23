"""Get possible insertion vectors between each pair of plates."""

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
            "Insertion Space", "Insertion", """The insertion space associated to each contact zone and represented as a piece of sphere""", "Manis", "Adjacency")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("d385adf7-e98c-4721-8240-397518bde84b")
    
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
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "scale", "scale", "Scale factor.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
    
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "spheres", "spheres", "Local insertion spaces represented as spheres centered on each contact zone.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "grouped", "grouped", "Local insertion spaces represented as spheres grouped at the origin.")
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
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAACxIAAAsSAdLdfvwAAADiSURBVEhL3ZVBDsIwDARL6AHxHN7Em/om3sQl1JY2rBzHsUAgQaVB1G5m4IBY9qtm2C95aazHUjMsl22rM0aB++06JQzMvgF2nhi4ARaDKABSAT7AMy/QJHSG5brz5DzDPAo0mRP5XmAkxy4TUKGJvBxgCQNPu2eJwGLevRXA0IqB7LIBAT59D4FgxUB2/xc4n9ZODLoAJKOIFyjl0IlVSHK9Z8lvByDyItmAlevMij4agAzwLArwGZbrjuUstHgB+4yVDwOAD0cBTwzCABgFPKFlP/v8lBFeQH7Ngvw3+JT6ACZIFPgP3z7FAAAAAElFTkSuQmCC"
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, model, scale):
        
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
        
        spheres = None
        grouped = None
        if scale is None: scale = 1
        if model:
            #model = copy.deepcopy(model)
            spheres = copy.deepcopy(model.contact_spheres)
            grouped = copy.deepcopy(model.contact_spheres)
            for i in range(len(model.contact_spheres)):
                for j in range(len(model.contact_spheres[i])):
                    spheres[i][j] = rs.ScaleObject(spheres[i][j],model.contact_centers[i][j],[scale,scale,scale])
                    grouped[i][j] = rs.CopyObject(model.contact_spheres[i][j],rs.VectorCreate((0,0,0),model.contact_centers[i][j]))
                    grouped[i][j] = rs.ScaleObject(grouped[i][j],(0,0,0),[scale,scale,scale])
            spheres = list_to_datatree(spheres)
            grouped = list_to_datatree(grouped)
        
        # return outputs if you have them; here I try it for you:
        return (spheres, grouped)


class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Contact Spheres"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return ""
    
    def get_Id(self):
        return System.Guid("c4c4c63d-f9a1-4100-92a5-aefddc4eed92")