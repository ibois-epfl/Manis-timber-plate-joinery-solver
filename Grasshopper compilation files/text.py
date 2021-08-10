"""Export a text file."""

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
import os
import datetime

__author__ = "Nicolas Rogeau"
__laboratory__ = "IBOIS, Laboratory for Timber Construction" 
__university__ = "EPFL, Ecole Polytechnique Federale de Lausanne"
__funding__ = "NCCR Digital Fabrication, ETH Zurich"
__version__ = "2020.01"

class MyComponent(component):
    def __new__(cls):
        instance = Grasshopper.Kernel.GH_Component.__new__(cls,
            "Export Text File", "TextOut", """Export a text file.""", "Manis", "Utility")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("02ba4a11-7b1c-48b3-8376-55637e7a1ed2")
    
    def SetUpParam(self, p, name, nickname, description):
        p.Name = name
        p.NickName = nickname
        p.Description = description
        p.Optional = True
    
    def RegisterInputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_Boolean()
        self.SetUpParam(p, "run", "run", "Export file if True.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_String()
        self.SetUpParam(p, "text", "text", "Text to export.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_String()
        self.SetUpParam(p, "folder", "folder", "Folder path.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_String()
        self.SetUpParam(p, "name", "name", "File name.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_String()
        self.SetUpParam(p, "extension", "extension", "(Optional) Custom file extension.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Boolean()
        self.SetUpParam(p, "date", "date", "(Optional) Add the date of today to the file name.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Boolean()
        self.SetUpParam(p, "x", "incremental", "(Optional) Check for existing file with the same name and increment if necessary.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
    
    def RegisterOutputParams(self, pManager):
        pass    
    def SolveInstance(self, DA):
        p0 = self.marshal.GetInput(DA, 0)
        p1 = self.marshal.GetInput(DA, 1)
        p2 = self.marshal.GetInput(DA, 2)
        p3 = self.marshal.GetInput(DA, 3)
        p4 = self.marshal.GetInput(DA, 4)
        p5 = self.marshal.GetInput(DA, 5)
        p6 = self.marshal.GetInput(DA, 6)
        result = self.RunScript(p0, p1, p2, p3, p4, p5, p6)

        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAJOgAACToAYJjBRwAAACKSURBVEhL7c3RCoQwDETR/v9Pq7dOSoygFDrggweGrhM2aT+3Ta8NB6xH4oDtyAZeZbl+APxWbvJwOlnqLzReg33KUAcj0We5rwmp61Sf6jeie5pV9Mr7Acz2YHbk/UB0T7OKXrn+Od4w+w06pVO9BvuUIZfTyVK/jFZ7lsO6HNblsC6HdfkXtLYDh4phuyx2L58AAAAASUVORK5CYII="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))


    def RunScript(self, run, text, folder, name, extension, date, incremental):

        inc = incremental
        ext = extension

        if run is True:

            # gh doc path
            ghP = self.LocalScope.ghdoc.Path

            # folder and file name
            if name == None: name = 'this_script_has_no_name'
            if folder == None: folder = os.path.dirname(os.path.realpath(ghP))
            outputName = folder + '\\' + str(name) 

            # date
            if date is True:
                date = datetime.datetime.today()
                outputName += '_' + str(date.year) + '_' + str(date.month) + '_' + str(date.day)

            # extension
            if ext == None: ext = '.txt'

            # avoid overwrite
            if inc is True:
                i = 0
                iter = outputName + '_' + str(i) 
                while  os.path.exists(iter + str(ext)) and i<100: #safety
                        i += 1
                        iter = outputName + '_' + str(i)
                outputName = iter
            outputName += str(ext)

            # create file
            print outputName
            myFile = open(outputName,'w')

            # pass values to file
            if text != None: 
                for i in range(len(text)):
                    myFile.write(str(text[i]))
                    if i != len(text)-1:
                        myFile.write('\n')

            # close file
            myFile.close()

            # confirm file write
            if os.stat(outputName).st_size > 0:
                print 'File successfully written as ' + outputName
            else:
                print 'output file is empty - check your values'

        return 


import GhPython
import System

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Text File Output"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("bc9186be-9321-4eb3-ba5e-58a615f66a50")