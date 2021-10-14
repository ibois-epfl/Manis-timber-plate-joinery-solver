"""Set user-specified attributes to the model. (Use carefully)"""

from ghpythonlib.componentbase import dotnetcompiledcomponent as component
import Grasshopper, GhPython
import System
import copy
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
            "Edit Model Attributes", "Edit", """Set user-specified attributes to the model. (Use carefully)""", "Manis", "Utility")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("49c2b057-624d-44d8-bff2-8d2497f4e186")
    
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
        
        p = Grasshopper.Kernel.Parameters.Param_String()
        self.SetUpParam(p, "attribute", "attribute", "Attribute to modify (e.g. 'top_face').")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "set", "set", "Set new values for the specified attribute.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.tree
        self.Params.Input.Add(p) 
    
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "model", "model", "Updated plate model.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "get", "get", "Get old or new values for the specified attribute.")
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
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAJOgAACToAYJjBRwAAAQWSURBVEhLYxhSINlfz7e3xqHY21rdASpEPTCnxmnFj7MZ//8/K/7/6lDy/7Zcm2aoFCqQ0tGxVImIKFCNjq5WjYzEitXj46vlXF1DoVoYJpfZz/1/L///12Mp/w/NDrzx51z6/yc74v/bWigbQZWAAZd6cvIq40mT/luuXPnfcvXq/5arVmHF1ps2/Tfu7f0P1CMysdCq7v/1nP9/rmT/78izrQCKsV5eHvb+/+3C/9EBZqVgk0FALS5uOchQkxkz/uuUl1/RLiw8rFVUdAQb1i0vPyIUk9qeH6JT9w3o2v+38/5PLLWfCDJnQb3rov938v7fWBf531hHXgNsuLSOjp4R0EUms2b9V/T0LAILEgDFHtIhb46k/P//sPD/3FrnpSCxyaWOE0GWfTuX8b86xRxhjrK3d47l8uX/tcvL70GF8IIoL03/BzvjwBG6vM1jB0isPce6BhRMoOBqz7buBCuEARl391ILoAWaJSUXoEI4gYuFiv31DVE//78q+b+x3+ckSKwywSz98ylgUAEjenq5w0ywQmQg4+ZWbLFs2X+t0tJLUCGsQFtBWv/c8vAP/1+X/t813f8mUIglM9ww6PmBpP//nxT9X1RrvxIoxgxWjAyIsYCdnV/x6Pzgp//flP0H0s+AQkJhrpp2t7fE/Pv/ouT/1i7XjQxGrnkGzS03ZF1d3SC6oIAIC0R3T/e/AQrzCysj3srJiSmZGchpXVoT8f3/q9L/Wyf6goKWXaOwZIfd9u3/VWNieiHaoICABXwber1O/X9Y8P/J7vi/PDyCNkAx0ZNLQt6CfLNvVuB9IF8CpFAnL2+v1Zo1/9ViYlpBfDjAZ0FngW3L/1t5//9fy/7/73zG/xVtHtt2TfO7CYqHE4tCXgsLC6tDlTJo5+XtJtUCpv0zA2/+v5v3f1K5467rayNe/b+VC0z7Bf8vrgr/aqEvYwZVBwYkW2Bnomj6bn/i/2e74v8EOmtOPrYw+BHI8Fubov8GOGqgRiQQkGzBjGqnvv83cv5/Opj4///VHHBSvLY+6k+Sn14EVAkKINmC6dVOc/8/LgIanv3/ytrI93Ob3KaD8gJUGgPgtEDO3b0MnJNLS89DhcBAXl5UYmaty6TeMsdKIFcKIoobaOXm7rBauxaUTNuhQhCg5OOTYbl06X/dyspHUCGygFZh4RmwDyIi6qFCECCiqKhm0N7+32z+/P/KoaGggooPiJlIwFyKPj5FxtOm/TOZOvW/jIWFPVAMFQBrscmgeDBbuPC/bm3tC92qqptAH90iiEHqamqemM6eDa6kVOPjN0CNxABMqlFREww6On6CLDJfsYJoDIo/w+7u/+qJiYuA5nBBjMMBRNjYVBX8/XNlIiKKZUJCCOOwsGLF4OBCaWlsqYuBAQDgfWJKIeZjuAAAAABJRU5ErkJggg=="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, model, attribute, set):

        def list_to_datatree(raggedList):
            """Python to Grasshopper"""
            rl = raggedList
            result = DataTree[object]()
            for i in range(len(rl)):
                temp = []
                for j in range(len(rl[i])):
                    temp.append(rl[i][j])
                path = GH_Path(i)
                result.AddRange(temp, path)
            return result

        def datatree_to_list(aTree):
            """Grasshopper to Python (from Chen Jingcheng)"""
            theList = []
            for i in range(aTree.BranchCount):
                thisListPart = []
                thisBranch = aTree.Branch(i)
                for j in range(len(thisBranch)):
                    thisListPart.append( thisBranch[j] )
                theList.append(thisListPart)
            return theList
        
        
        get=[]
        if set != []: set = datatree_to_list(set)
        if model:
            model = copy.deepcopy(model)
            new_items = set
            if attribute:
                try:
                    attr = getattr(model, attribute)
                    get=attr
                    if new_items:
                        if type(attr) != type(new_items):
                            raise Exception("You're trying to change attributes with the wrong data type!")
                        elif len(attr) != len(new_items):
                            raise Exception("The provided list of new_items does not match the length of the list of attributes!")
                        else: setattr(model, new_items)
                except:
                    try:
                        for i in range(model.count):
                            attr = getattr(model.plates[i], attribute)
                            get.append(attr)
                            if new_items:
                                if type(attr) != type(new_items[i]):
                                    raise Exception("You're trying to change attributes with the wrong data type!")
                                elif model.count != len(new_items):
                                    raise Exception("The provided list of new_items does not match the length of the list of attributes!")
                                else: 
                                    setattr(model.plates[i], attribute, new_items[i])
                    except ValueError: 
                        print("""This is the list of all plate attributes:
                            temp
                            id
                            brep
                            top_face
                            bottom_face
                            top_contour
                            mid_contour
                            bottom_contour
                            top_holes
                            bottom_holes
                            top_center
                            bottom_center
                            plate_center
                            top_normal
                            bottom_normal
                            top_plane
                            bottom_plane
                            mid_plane
                            thickness
                            joints_positives
                            joints_negatives
                            joints_keys
                            top_milling_contour
                            bottom_milling_contour
                            top_milling_holes
                            bottom_milling_holes""")
                        print("""This is the list of all model attributes:
                            temp
                            count
                            sequence
                            breps
                            plates
                            contact_ids
                            contact_pairs
                            contact_breps
                            contact_zones
                            contact_types
                            contact_strings
                            contact_centers
                            contact_normals
                            contact_planes
                            contact_vectors
                            needed_support
                            assembly_vectors
                            assembly_relatives
                            """)
        if get != []:
            if type(get[0]) == list:
                get = list_to_datatree(get)
        
        # return outputs if you have them; here I try it for you:
        return (model, get)

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Edit Model Attributes"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("eef830d2-c6c3-4832-9fe8-89b603206475")