"""Display plates according to robot moves."""

from ghpythonlib.componentbase import dotnetcompiledcomponent as component
import Grasshopper, GhPython
import System
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg

__author__ = "Nicolas Rogeau"
__laboratory__ = "IBOIS, Laboratory for Timber Construction" 
__university__ = "EPFL, Ecole Polytechnique Federale de Lausanne"
__funding__ = "NCCR Digital Fabrication, ETH Zurich"
__version__ = "2021.09"

class MyComponent(component):
    def __new__(cls):
        instance = Grasshopper.Kernel.GH_Component.__new__(cls,
            "Plate simulation", "Plate simulation", """Display plates according to robot moves.""", "Manis", "Robotics")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("172b904a-aafc-48d0-b5c4-552a0bf99ed2")
    
    def SetUpParam(self, p, name, nickname, description):
        p.Name = name
        p.NickName = nickname
        p.Description = description
        p.Optional = True
    
    def RegisterInputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "stack_module", "stack_module", "The plate module stacked in range of the robotic arm.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "goal_module", "goal_module", "The plate module to assemble in range of the robotic arm.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Plane()
        self.SetUpParam(p, "planes", "planes", "The list of planes describing the trajectory of the robotic arm.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Plane()
        self.SetUpParam(p, "tcp", "tcp", "The current TCP of the robot.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Integer()
        self.SetUpParam(p, "step", "step", "The current step for the assembly.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Integer()
        self.SetUpParam(p, "pick_step", "pick_step", "The step where the robot should pick the plate.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Integer()
        self.SetUpParam(p, "drop_step", "drop_step", "The step where the robot should drop the plate.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "breps", "breps", "Plates displayed according to robot movements.")
        self.Params.Output.Add(p)
        
    
    def SolveInstance(self, DA):
        p0 = self.marshal.GetInput(DA, 0)
        p1 = self.marshal.GetInput(DA, 1)
        p2 = self.marshal.GetInput(DA, 2)
        p3 = self.marshal.GetInput(DA, 3)
        p4 = self.marshal.GetInput(DA, 4)
        p5 = self.marshal.GetInput(DA, 5)
        p6 = self.marshal.GetInput(DA, 6)
        result = self.RunScript(p0, p1, p2, p3, p4, p5, p6)

        if result is not None:
            self.marshal.SetOutput(result, DA, 0, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAJOgAACToAYJjBRwAAAJ9SURBVEhLvdVrSFNhHMfxU2Y1yhpFFDnLS04XFBRhFwUhamlOcCgRDqo33RS7uFrGiCgiuqzCIicl9SJYBa7SEpJoXY1qXRCiF0VvKujmi14FQnT6/s/Okelmzlj94MPO8+zseZ49+z9nyn9LxdKsgpq180oqi7MX6F3JTfCo/WXv++3qlSP2p3pXchPylz1SezxqyO+4p3clN7eayrrUzzvUO82O23pXvKRiMtIxBRORWIwJrvnsz2lWYBU2YB98OIlTOIabeAO5txhDx5ig0b2kl6YMLFv1FjJwFmTlYyFZDbnvB75i6MIYMMFOhPAKstrjOIPzuIgOfMR91KAVmRg8xgQ3TpQ8oTkfGZA9ng4LpmESJmA0tkImlyzGdZi0VrwYE1BFsvJEE4Bsp2QNzkUu4yTU7OhSv3moovK7elciMeMhcrSWohzEnsjlgFz12bt/fXJTRSue6V2JRqooiBFaS1GaUBm5jErVssziqnLrturS7EK9azjZBdkq+SaX8QDLEROX/vo3kUr7gM2QcfbDgb6MgvGDDTdyqt/hEhqgYj22oC8jsTFyOazMxRccgGyVDCyHUxYbs+B1GIepWmvwyKHy4jR64IYkD/INDqMFcm60FMCJTdiN2RgssojXOIRSzEF0rPgOmaxfpNykAmLeiIrc8wIztFZs5JkVRr9KTJnpcrXYvN7WnNraTmt9fXBWXV1HtDyPpyPd6ZSTehZF2qdiMwbdqNZaUTHlNzT8LGxrUxcGAnEVtberGS6XPGv8SNE+FRvpf4xFkIo0KCtNFktXWn5+eHxublxpNls41Wzu5F6plD9lLy6gMUpkliRGxpP/DcO/jKL8BqAWy6+d88mZAAAAAElFTkSuQmCC"
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))


    def RunScript(self, stack_module, goal_module, planes, tcp, step, pick_step, drop_step):
        
        if step is None: step = 0
        if pick_step is None: pick_step = 6
        if drop_step is None: drop_step = 11
        
        display = []

        if goal_module:
            goal = []
            for i in range(goal_module.count):
                goal.append(goal_module.plates[i].brep)
        if stack_module:
            stack = []
            for i in range(stack_module.count):
                stack.append(stack_module.plates[i].brep)
        if stack_module and goal_module and planes and tcp:
            #number of moves
            n = int(len(planes)/len(stack))
            
            # beginning phase
            if step < pick_step :
                display = stack
            
            # on move phase
            elif (step % n >= pick_step) and (step % n <= drop_step):
                plate_on_move = (step - step % n) / n
                for i in range(len(stack)):
                    if i < plate_on_move: display.append(goal[i])
                    if i == plate_on_move:
                        start_plane = planes[step - step % n + pick_step-2]
                        matrix = rg.Transform.PlaneToPlane(start_plane, tcp)
                        obj = rs.TransformObject(rs.CopyObject(stack[i]), matrix)
                        display.append(obj)
                    if i > plate_on_move: display.append(stack[i])
            
            # stand still phase
            else:
                step = step - pick_step
                plate_on_move = (step - step % n) / n
                for i in range(len(stack)):
                    if i <= plate_on_move: display.append(goal[i])
                    if i > plate_on_move: display.append(stack[i])

        return (display)

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Plate simulation"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("16004be3-3e5c-4683-a78d-d0b4b1612804")