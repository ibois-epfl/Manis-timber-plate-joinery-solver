"""Create Half-lap Joints between plates with Side to Face connections"""

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
            "Add Half-lap Joint", "Half-lap", """Create Half-lap Joints between intersecting plates""", "Manis", "Joints")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("4d18d5fa-0412-4fd9-9da7-b037a22e2688")
    
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
        self.SetUpParam(p, "plates_pairs", "plates_pairs", "(Optional) List of pair of plates (a,b) to only add joints between those plates.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "proportion", "proportion", "The proportion of the cut (default halflap = 0.5) between both pieces.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "tolerance", "tolerance", "Chamfer the halflap joint to add more tolerance for assembly.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "min_angle", "min_angle", "If joint with tolerance: minimum angle for the slope of the optional chamfer (usually around 45 degrees).")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "straight_height", "straight_height", "If joint with tolerance: size of the part of the notch without chamfer.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "fillet_height", "fillet_height", "If joint with tolerance: size of the rounded part of the notch.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Integer()
        self.SetUpParam(p, "segments", "segments", "If joint with tolerance: number of segments for the discretization of the opening curve.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

    
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "model", "model", "Updated plate model.")
        self.Params.Output.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Brep()
        self.SetUpParam(p, "joints_positives", "joints_positives", "The joints to add to each plate.")
        self.Params.Output.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Brep()
        self.SetUpParam(p, "joints_negatives", "joints_negatives", "The joints to subtract from each plate.")
        self.Params.Output.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Brep()
        self.SetUpParam(p, "joints_keys", "joints_keys", "The keys to insert in each plate.")
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
        result = self.RunScript(p0, p1, p2, p3, p4, p5, p6, p7)

        if result is not None:
            if not hasattr(result, '__getitem__'):
                self.marshal.SetOutput(result, DA, 0, True)
            else:
                self.marshal.SetOutput(result[0], DA, 0, True)
                self.marshal.SetOutput(result[1], DA, 1, True)
                self.marshal.SetOutput(result[2], DA, 2, True)
                self.marshal.SetOutput(result[3], DA, 3, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAACxIAAAsSAdLdfvwAAAD5SURBVEhLzZJZDsIwDERzJs7EmXomzsSPmUkyIYtLt1TC0kta134jIcJjWewuQgh2W0CUs7yPVylyljdwBSi/cpY3dBboGjl65wKw6/aiNRd65wKwOwTkXimz+Oc5HpB2o6vpsaGq5WR3QNq1KOCzenxRoTfAY5B5YL8JyJTCjAsPV9gDB++01MkZqm89PAaZBz0Ez2kxl97X4DHIPOCy9+sZb/1UBD0X7PxRgORkekAtJ3UAn3lIWoPd7QAKMLwVwP7xAE8usphV3nHvD9DiLzhTz/Uh8PgBe+Sin61DKCdNwBH5GgoZAmbIBV1NwEy5UAjLHZhBCME+DZvjoNSWlgYAAAAASUVORK5CYII="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, model, plates_pairs, proportion, tolerance, min_angle, straight_height, fillet_height, segments):

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

        joints_positives = []
        joints_negatives = []
        joints_keys = []

        if model:
            model = copy.deepcopy(model)

            model.add_halflap(plates_pairs, 
                proportion,
                tolerance,
                min_angle,
                straight_height,
                fillet_height,
                segments)

            for plate in model.plates:
                joints_positives.append(plate.joints_positives)
                joints_negatives.append(plate.joints_negatives)
                joints_keys.append(plate.joints_keys)
            joints_positives = list_to_datatree(joints_positives)
            joints_negatives = list_to_datatree(joints_negatives)
            joints_keys = list_to_datatree(joints_keys)

        else: 
            self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'Waiting to get a model as input.')
        return (model, joints_positives, joints_negatives, joints_keys)

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Add Half-lap Joint"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("492de82d-384b-422a-8354-a2c471afb4bd")