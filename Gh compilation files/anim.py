"""Gives a preview of the assembly sequence."""

from ghpythonlib.componentbase import dotnetcompiledcomponent as component
import Grasshopper, GhPython
import System
import rhinoscriptsyntax as rs
import ast


__author__ = "Nicolas Rogeau"
__laboratory__ = "IBOIS, Laboratory for Timber Construction" 
__university__ = "EPFL, Ecole Polytechnique Federale de Lausanne"
__funding__ = "NCCR Digital Fabrication, ETH Zurich"
__version__ = "2021.09"

class MyComponent(component):
    def __new__(cls):
        instance = Grasshopper.Kernel.GH_Component.__new__(cls,
            "Animate Sequence", "Anim", """Gives a preview of the assembly sequence.""", "Manis", "Utility")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("dcc9f1d8-23dd-4869-b406-8b02b0765862")
    
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
        self.SetUpParam(p, "step", "step", "Animation progression from 0 to 1.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "retreat", "retreat", "Length of the insertion path.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
    
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_Brep()
        self.SetUpParam(p, "breps", "breps", "Show late in motion.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_String()
        self.SetUpParam(p, "status", "status", "Assembly progression.")
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
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAJOgAACToAYJjBRwAAAB4SURBVEhL7Y9BCsAgDATzpr6pb/JNfVMvtlJcUBLKHIJQOrCIMhvVbmpyrG6lpORDFyRnHeT2tS+N+H/gEoneOXEHujCvHsQdIAU8vEMKeHgq7TVzIogr6nnsSts/xy7EFaREXEFKxBWkRFxBSsQVpERcQUovrtkF47mRqvh38rQAAAAASUVORK5CYII="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, model, step, retreat):
       

        def flatten_integer_list(l):
            """Flatten a nested list of integers"""
            if type(l) is list:
                new_l=[]
                num = None
                for i in range(len(str(l))):
                    char = str(l)[i]
                    if char != '[' and char != ']' and char!= ' ' and char != ',':
                        if num == None: num = char
                        else: num += char
                    elif num != None: 
                        new_l.append(int(num))
                        num = None
                return(new_l)
            else: return l
       
        mod = model
        #init
        breps = None
        status = None
        if retreat == None: retreat = 1000
        if step == None: step = 1

        if mod:
            # If model as input, take last module for animation.
            if hasattr(mod, 'model') is False:
                mod = mod.modules[-1]

            #start of insertion
            if step == 0: 
                status = ('start of insertion sequence')
            else:
                vectors = mod.assembly_vectors
                count = mod.count
                seq = ast.literal_eval(mod.sequence)
                breps = []
                step = step * count
                deci = step - int(step)

                # animation
                for i in range(count):
                    if vectors[i] == "gravity": vectors[i] = rs.VectorCreate((0,0,-1),(0,0,0))
                    # standing plates
                    if i < int(step) :
                        plate_ids = flatten_integer_list(seq[i])
                        if type(plate_ids) is list:
                            for integer in plate_ids:
                                breps.append(rs.CopyObject(mod.model.plates[integer].brep))
                        else: breps.append(rs.CopyObject(mod.model.plates[plate_ids].brep))
                    # moving plates
                    if i == int(step) :
                        if type(seq[i]) is list:
                            plate_ids = flatten_integer_list(seq[i])
                            for integer in plate_ids:
                                breps.append(rs.CopyObject(mod.model.plates[integer].brep, -(1-deci)*retreat*vectors[i]))
                        else: breps.append(rs.CopyObject(mod.model.plates[seq[i]].brep, -(1-deci)*retreat*vectors[i]))

                # ongoing status
                perc = 100*(step - int(step))
                status = ('plate '+ str(int(step)) + ' inserted at ' + str(perc)+ ' %.')

                # end status
                if step == 1: status = ('end of insertion sequence')

            if breps is not None: 
                for i in range(len(breps)): breps[i]= rs.coercebrep(breps[i])
            
        else: self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'Waiting to get a model as input.')

        return (breps, status)

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
        return System.Guid("fd95287a-598b-49e7-a9a0-bff3ba219cf7")