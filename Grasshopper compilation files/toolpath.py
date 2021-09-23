"""Explode the model and distribute the plates as an array."""

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
            "Toolpath Generator", "Toolpath", """Offset the contour of each plate to get the toolpath for fabrication.""", "Manis", "Solver")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("b8273f2a-e122-467c-961d-67071bb5d5d1")
    
    def SetUpParam(self, p, name, nickname, description):
        p.Name = name
        p.NickName = nickname
        p.Description = description
        p.Optional = True
    
    def RegisterInputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_Boolean()
        self.SetUpParam(p, "run", "run", "Run the model if True.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "model", "model", "Plate model.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_String()
        self.SetUpParam(p, "plates_id", "plates_id", "(Optional) List of plates to only merge joints for those plates.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "contour_tool_radius", "contour_tool_radius", "Radius of tool used to cut the contour.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "holes_tool_radius", "holes_tool_radius", "Radius of tool used to cut the holes.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Boolean()
        self.SetUpParam(p, "notch", "notch", "Generate notches in corners for insertion.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Boolean()
        self.SetUpParam(p, "cylinder", "cylinder", "If notch is True, generate cylinders as joints_negatives for detailed vizualization of the notches.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "limit", "limit", "Limit the angle of the corners for which a notch should be created.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Boolean()
        self.SetUpParam(p, "tbone", "tbone", "Change notch style: Dog-bone if False, T-bone if True.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Integer()
        self.SetUpParam(p, "switch", "switch", "Switch the top and bottom planes.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)
        
    
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "model", "model", "Updated plate model.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "top_milling_contour", "top_milling_contour", "Top_contour for milling operations.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "bottom_milling_contour", "bottom_milling_contour", "Bottom_contour for milling operations.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "top_milling_holes", "top_milling_holes", "Top_holes for milling operations.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "bottom_milling_holes", "bottom_milling_holes", "Bottom_holes for milling operations.")
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
                self.marshal.SetOutput(result[4], DA, 4, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAJOgAACToAYJjBRwAAACMSURBVEhL7ZRLDoAgDEQ9k2fiTJzJM7nB1E4TrbXy3RheMgmh7QywYDFIHlTntnpgxexbwIqhOrfVAytmBljAyobq3FbPaSIMuQHJQmrU1Aos79A+l9u5nlarK91PrvlfgKxL5PIIWGMsEuZeEfNhARrTxBPmsjFNPGEuG3muEpmb/US/5UjNgA+FdACwXPThKHhjfAAAAABJRU5ErkJggg=="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, run, model, plates_id, contour_tool_radius, holes_tool_radius, notch, cylinder, limit, tbone, switch):

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

        if run is True or run == None: 
            if model:
                model = copy.deepcopy(model)
    
                model.get_fabrication_lines(plates_id, contour_tool_radius, holes_tool_radius, notch, cylinder, limit, tbone)
    
                model.switch_top_bottom(switch)
    
                top_milling_contour =  []
                bottom_milling_contour =  []
                top_milling_holes =  []
                bottom_milling_holes =  []
    
                for i in range(len(model.plates)):

                    # apply to all or some plates.
                    flag = True
                    if (plates_id != None) and (plates_id != []) and (plates_id != 'all'):
                        flag = False
                        for j in range(len(plates_id)):
                            if str(i) == plates_id[j]: flag = True

                    if flag == True:
                        top_milling_contour.append(model.plates[i].top_milling_contour)
                        bottom_milling_contour.append(model.plates[i].bottom_milling_contour)
                        top_milling_holes.append(model.plates[i].top_milling_holes)
                        bottom_milling_holes.append(model.plates[i].bottom_milling_holes)
                                       
                top_milling_holes = list_to_datatree(top_milling_holes)
                bottom_milling_holes = list_to_datatree(bottom_milling_holes)

            else: self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'Waiting to get a model as input.')

        else: self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'Set Run to True to generate toolpath.')

        return (model, top_milling_contour, bottom_milling_contour, top_milling_holes, bottom_milling_holes)


import GhPython
import System

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Toolpath Generator"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("dd2bd212-02eb-4b01-ba5c-1b9accc4cb5c")