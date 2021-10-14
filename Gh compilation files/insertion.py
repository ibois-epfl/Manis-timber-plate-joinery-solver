"""Get possible insertion vectors between each pair of plates."""

from ghpythonlib.componentbase import dotnetcompiledcomponent as component
import Grasshopper, GhPython
import System
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path

__author__ = "Nicolas Rogeau"
__laboratory__ = "IBOIS, Laboratory for Timber Construction" 
__university__ = "EPFL, Ecole Polytechnique Federale de Lausanne"
__funding__ = "NCCR Digital Fabrication, ETH Zurich"
__version__ = "2021.09"

class MyComponent(component):
    def __new__(cls):
        instance = Grasshopper.Kernel.GH_Component.__new__(cls,
            "Insertion Vectors", "Insertion", """Get possible insertion vectors between each pair of plates.""", "Manis", "Adjacency")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("06866161-1783-48cd-b069-c2d25c8be31f")
    
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
        p = Grasshopper.Kernel.Parameters.Param_Vector()
        self.SetUpParam(p, "vectors", "insertion", "Insertion vectors.")
        self.Params.Output.Add(p)
        
    
    def SolveInstance(self, DA):
        p0 = self.marshal.GetInput(DA, 0)
        result = self.RunScript(p0)

        if result is not None:
            self.marshal.SetOutput(result, DA, 0, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAJOgAACToAYJjBRwAAACvSURBVEhL7ZUxDoMwEASJQ4HynLwpb+JNvInG+E6O2b2cdRQolVeawgueFUWUqSRfhDI/U77C9F7XHFF87sC+fULGQMgYCHEHyn3FnG1OSX0fxe0ZikHmdTYsqvew094RkRx6m19ZvU+dkdzG/wdwBDvoKa9lbpImM3LtOjKvo6T0YJEj1x5FRmjPFBwoRwXF7RmKe1QBxX5BjzEQMgZC5N2vIIIiA/JrFuS/wSflA+2MRFEms8f0AAAAAElFTkSuQmCC"
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, model):

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
        
        insertion = None

        if model:
            insertion = list_to_datatree(model.contact_vectors)
        else: 
            self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'Waiting to get a model as input.')
        return insertion

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Insertion Vectors"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("63d0b026-9906-45ca-bfcb-4648905dd290")