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
            "Create Constraint", "Constraint", """Create a new constrained insertion space.""", "Manis", "Assembly")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("46acbe0b-f549-435c-b685-c2e67e4359c2")
    
    def SetUpParam(self, p, name, nickname, description):
        p.Name = name
        p.NickName = nickname
        p.Description = description
        p.Optional = True
    
    def RegisterInputParams(self, pManager):      
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "alpha", "alpha", "Horizontal constraint angle.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "beta", "beta", "Vertical constraint angle.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "constraint", "constraint", "Constrained insertion space.")
        self.Params.Output.Add(p)
        p = Grasshopper.Kernel.Parameters.Param_Surface()
        self.SetUpParam(p, "boundaries", "boundaries", "Boundary surfaces constraining the insertion space.")
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
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAACxIAAAsSAdLdfvwAAAC6SURBVEhL7Y5RDgIxCEQ9k2fyTD2TZ/KHdQpYipO6JvTDRJLXbYdh2IuIbIWKlVCxEipWQsVKqFgJFSuhYuZZOBjUH6Gi40GP+43i/W4k84CLNshCGe7vgznrTfgiOMOWzA8z4MsCVthMn+3HaoEbY8AK877m+pEXeAMVtRjEUPv0kygdxjs0Rtc011kwUOvwmh+lg3ibODrB7EA+E+5Y6cWEoSazg9aZcGA1XfZxbU128l/wkV9f0OQApsqgOBWdkr0AAAAASUVORK5CYII="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, alpha, beta):
       
        constraint = None
        boundaries = None
        sphere =  rs.AddSphere((0,0,0),1)
        cutter = rs.AddPlanarSrf(rs.AddPolyline([(1,1,0),(1,-1,0),(-1,-1,0),(-1,1,0),(1,1,0)]))
        hemisphere = rs.SplitBrep(sphere,cutter)[1]

        if alpha is None: alpha = 180
        if beta is None: beta = 180

        boundaries = [cutter[0]]
        cutter2 = rs.RotateObject(cutter,(0,0,0),90+(alpha/2),(0,1,0),(True))
        cutter3 = rs.RotateObject(cutter,(0,0,0),90-(alpha/2),(0,1,0),(True))
        cutter4 = rs.RotateObject(cutter,(0,0,0),90+(beta/2),(1,0,0),(True))
        cutter5 = rs.RotateObject(cutter,(0,0,0),90-(beta/2),(1,0,0),(True))
        boundaries.append(cutter2)
        boundaries.append(cutter3)
        boundaries.append(cutter4)
        boundaries.append(cutter5)

        if alpha == 0:
            if beta == 0:
                constraint = rs.AddPoint(0,0,1)
            else:
                arc = rs.AddArc(rs.WorldYZPlane(),1,beta)
                constraint = rs.RotateObject(arc,(0,0,0),90-(beta/2),(1,0,0),(True))
        else:
            if beta == 0:
                arc = rs.AddArc(rs.WorldZXPlane(),1,alpha)
                constraint = rs.RotateObject(arc,(0,0,0),-(alpha/2),(0,1,0),(True))
            else:
                constraint = hemisphere
                if alpha<180:
                    constraint = rs.SplitBrep(constraint,cutter2)[0]
                    constraint = rs.SplitBrep(constraint,cutter3)[1]
                if beta<180:
                    constraint = rs.SplitBrep(constraint,cutter4)[0]
                    constraint = rs.SplitBrep(constraint,cutter5)[1]

        return (constraint,boundaries)


import GhPython
import System

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Animate Sequence"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("516e3730-d1f4-409b-9a7a-50182a323983")