"""Create a robot trajectory between for a plate module."""

from ghpythonlib.componentbase import dotnetcompiledcomponent as component
import Grasshopper, GhPython
import System
import rhinoscriptsyntax as rs

__author__ = "Nicolas Rogeau"
__laboratory__ = "IBOIS, Laboratory for Timber Construction" 
__university__ = "EPFL, Ecole Polytechnique Federale de Lausanne"
__funding__ = "NCCR Digital Fabrication, ETH Zurich"
__version__ = "2021.09"

class MyComponent(component):
    def __new__(cls):
        instance = Grasshopper.Kernel.GH_Component.__new__(cls,
            "Robot trajectory", "Robot trajectory", """Create a robot trajectory between for a plate module.""", "Manis", "Robotics")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("22f1e7f4-3036-42d8-a4e5-51a8ec2bd477")
    
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
        
        p = Grasshopper.Kernel.Parameters.Param_String()
        self.SetUpParam(p, "plates_id", "plates_id", "(Optional) List of plates to assemble with a robot.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Plane()
        self.SetUpParam(p, "safe_spot", "safe_spot", "A plane where the robot can safely move between the assembly of each plate.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "up_dist", "up_dist", "The distance above the assembly where the robot should travel.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "retreat_dist", "retreat_dist", "The distance that the robot should travel to retreat after the insertion of the plate.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_Plane()
        self.SetUpParam(p, "planes", "planes", "The list of planes for the robot trajectory.")
        self.Params.Output.Add(p)

    def SolveInstance(self, DA):
        p0 = self.marshal.GetInput(DA, 0)
        p1 = self.marshal.GetInput(DA, 1)
        p2 = self.marshal.GetInput(DA, 2)
        p3 = self.marshal.GetInput(DA, 3)
        p4 = self.marshal.GetInput(DA, 4)
        p5 = self.marshal.GetInput(DA, 5)
        result = self.RunScript(p0, p1, p2, p3, p4, p5)

        if result is not None:
            self.marshal.SetOutput(result, DA, 0, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAACxIAAAsSAdLdfvwAAAEVSURBVEhLrY7rDYMwDIT7sytU6hQMy7rUF3zpOXECSLH0EUzuwes4jkdcTBEEfVgSQcvFjAv8kgSRcjGdlyY6w6lC111N52uNcRFhoxtNLdj2/QCtcUkBw2sBsEUFBQ2nZgb8dgaCGQI88A40nJoM+nDajvflBZgSDOwbsU3MLqhGDadmwPm3Es6cYObgHWg4NQk1lGhGMNuUv3Awb+NDcQID03AwKijDO9UIXbh/DwQzxHjw1HBqnC4cer8LBHMzXYmbboeDWQEG5q+LNfBWOGj/7n8hY3sN5envna9lWFAuz4AaDGTv9BnTAkMDlUybMiuo4QTBHNtvMSqYhmPs2y2ygi7c0PtHtAVLw4EWLA/f9v31A49phgrTyfm7AAAAAElFTkSuQmCC"
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))


    def RunScript(self, stack_module, goal_module, plates_id, safe_spot, up_dist, retreat_dist):

        planes = None

        if goal_module and stack_module:

            #default param
            if safe_spot is None: safe_spot = rs.PlaneFromNormal((1230,-1350,2020),(0,0,1))
            if up_dist is None: up_dist = 100
            if retreat_dist is None: retreat_dist = 10

            # initialization
            planes = []
            bases = []
            goals = []
            normals = []
            foam_dist = 20 # foam height on Joulin

            #auto-flip plates in stack
            for i in range(goal_module.count):
                if stack_module.plates[i].top_center[2] < stack_module.plates[i].bottom_center[2] :
                    bases.append(stack_module.plates[i].bottom_plane)
                    goals.append(goal_module.plates[i].bottom_plane)
                    normals.append(goal_module.plates[i].bottom_normal)
                else :
                    bases.append(stack_module.plates[i].top_plane)
                    goals.append(goal_module.plates[i].top_plane)
                    normals.append(goal_module.plates[i].top_normal)

            if len(bases) != len(goals):
                self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Error, 'start and goal model should have the same number of plates') 

            # plane and text list
            else:
                for i in range(goal_module.count):
                    flag = True
                    if (plates_id != []) and (plates_id != 'all') and (plates_id != None):
                        flag = False
                        for j in range(len(plates_id)):
                            if str(i) == plates_id[j]: flag = True
                    if flag == True:

                        #-------------------- SAFE PART (World) --------------------
            
                        # safe_spot
                        planes.append(safe_spot)
            
                        #-------------------- BASE PART (model) --------------------
            
                        # above_base
                        above_base_point = rs.CopyObject(bases[i].Origin, (0,0,up_dist))
                        above_base_plane = rs.PlaneFromFrame(above_base_point, bases[i].XAxis, bases[i].YAxis)
                        planes.append(above_base_plane)
            
                        # near_base
                        near_base_point = rs.CopyObject(bases[i].Origin, (0,0,retreat_dist))
                        near_base_plane = rs.PlaneFromFrame(near_base_point, bases[i].XAxis, bases[i].YAxis)
                        planes.append(near_base_plane)
            
                        #------------------- BASE PART (picture) -------------------
            
                        # near_base
                        planes.append(near_base_plane)
            
                        # to_plate
                        to_plate_point = rs.CopyObject(bases[i].Origin, (0,0, foam_dist))
                        to_plate_plane = rs.PlaneFromFrame(to_plate_point, bases[i].XAxis, bases[i].YAxis)
                        planes.append(to_plate_plane)
            
                        # near_base
                        planes.append(near_base_plane)
            
                        # above_base
                        planes.append(above_base_plane)
            
                        #-------------------- SAFE PART (World) --------------------
            
                        # safe_spot
                        planes.append(safe_spot)
            
                        #------------------- GOAL PART (picture) -------------------
                       
                        # above_goal
            
                        if goal_module.assembly_vectors[i] == 'gravity': 
                            near_goal_point = rs.CopyObject(goals[i].Origin, -retreat_dist * rs.VectorCreate((0,0,-1),(0,0,0)))
                        else: near_goal_point = rs.CopyObject(goals[i].Origin, -retreat_dist * goal_module.assembly_vectors[i])
                        above_goal_point = rs.CopyObject(near_goal_point, (0,0,up_dist))
                        above_goal_plane = rs.PlaneFromFrame(above_goal_point, goals[i].XAxis,goals[i].YAxis)
                        planes.append(above_goal_plane)
            
                        # near_goal
                        near_goal_plane = rs.PlaneFromFrame(near_goal_point, goals[i].XAxis,goals[i].YAxis)
                        planes.append(near_goal_plane)
            
            
                        # to_insert
                        planes.append(goals[i])
            
                        # retreat
                        retreat_point = rs.CopyObject(goals[i].Origin, retreat_dist * normals[i])
                        retreat_plane = rs.PlaneFromFrame(retreat_point, goals[i].XAxis, goals[i].YAxis)
                        planes.append(retreat_plane)
            
                        # above_retreat
                        above_retreat = rs.CopyObject(retreat_point, (0,0,up_dist))
                        retreat_plane = rs.PlaneFromFrame(above_retreat, goals[i].XAxis, goals[i].YAxis)
                        planes.append(retreat_plane)

        return (planes)

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Robot trajectory"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("16004be3-3e5c-4683-a78d-d0b4b1611328")