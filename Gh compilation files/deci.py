"""Split a number into its integer and decimal part."""

from ghpythonlib.componentbase import dotnetcompiledcomponent as component
import Grasshopper, GhPython
import System

__author__ = "Nicolas Rogeau"
__laboratory__ = "IBOIS, Laboratory for Timber Construction" 
__university__ = "EPFL, Ecole Polytechnique Federale de Lausanne"
__funding__ = "NCCR Digital Fabrication, ETH Zurich"
__version__ = "2021.09"

class MyComponent(component):
    def __new__(cls):
        instance = Grasshopper.Kernel.GH_Component.__new__(cls,
            "Split decimals", "Deci", """Split a number into its integer and decimal part.""", "Manis", "Utility")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("89c43144-3dbe-484e-8027-a379dfd3aa3e")
    
    def SetUpParam(self, p, name, nickname, description):
        p.Name = name
        p.NickName = nickname
        p.Description = description
        p.Optional = True
    
    def RegisterInputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "num", "num", "Number to split.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)       
    
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "int", "int", "Integer part.")
        self.Params.Output.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "deci", "deci", "Decimal part.")
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
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAACxIAAAsSAdLdfvwAAACfSURBVEhL7Y1dCsMwDINzph62Z+qZ9uJZ2WScVGN9cAaDBj6aqPppZrYUKVYixUqkWIkUwbbvBppbHOkBj2OzmZw5BQDLvw2ocvKKiIFcfnWAHr8PGjxDYC4vHVDlgGH6MvPArOEd5ly4aqCD858DmXvgHghKB97fCIKfDSjoi9LM1QHwqbwH/H8YFT4AH88QBF52AjpPv9O8CinWYe0J/L6Y5R3RgGwAAAAASUVORK5CYII="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, num):

        integer = None
        deci = None
        if num:             
            st= str(num).split(".")
            integer = int(st[0])
            deci = float("0."+st[1])
        
        return (integer, deci)

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Split decimals"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return ""
    
    def get_Id(self):
        return System.Guid("152935fe-53f7-48d0-a32d-02850646f159")