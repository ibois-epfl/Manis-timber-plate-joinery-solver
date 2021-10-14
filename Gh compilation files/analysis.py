"""Run a structural analysis of the model using Abaqus solver through Compas framework."""

from ghpythonlib.componentbase import dotnetcompiledcomponent as component
import Grasshopper, GhPython
import System
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import datetime
import json

__author__ = "Nicolas Rogeau and Aryan Rezaei Rad"
__laboratory__ = "IBOIS, Laboratory for Timber Construction" 
__university__ = "EPFL, Ecole Polytechnique Federale de Lausanne"
__funding__ = "NCCR Digital Fabrication, ETH Zurich"
__version__ = "2021.09"

class MyComponent(component):
    def __new__(cls):
        instance = Grasshopper.Kernel.GH_Component.__new__(cls,
            "FEM analysis", "FEM Analysis", """Run a structural analysis of the model using Abaqus solver through Compas framework.""", "Manis", "FEM")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("a5d29a9e-1702-4ed8-8ccb-997c922f6911")
    
    def SetUpParam(self, p, name, nickname, description):
        p.Name = name
        p.NickName = nickname
        p.Description = description
        p.Optional = True

    def RegisterInputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_Boolean()
        self.SetUpParam(p, "run", "run", "Script input Boolean")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Mesh()
        self.SetUpParam(p, "meshes", "meshes", "Script input meshes.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Line()

        self.SetUpParam(p, "lines", "lines", "Script input lines.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Point()
        self.SetUpParam(p, "supports", "supports", "Script input supports.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Point()
        self.SetUpParam(p, "load_points", "load_points", "Script input load_points.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Boolean()
        self.SetUpParam(p, "fixed", "fixed", "Script input fixed.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "elasticity", "elasticity", "Script input elasticity.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "poisson", "poisson", "Script input poisson.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "density", "density", "Script input density.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "thickness", "thickness", "Script input thickness.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "width", "width", "Script input width.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "height", "height", "Script input height.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "uni_load", "uni_load", "Script input uni_load.")
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
        p7 = self.marshal.GetInput(DA, 7)
        p8 = self.marshal.GetInput(DA, 8)
        p9 = self.marshal.GetInput(DA, 9)
        p10 = self.marshal.GetInput(DA, 10)
        p11 = self.marshal.GetInput(DA, 11)
        p12 = self.marshal.GetInput(DA, 12)
        result = self.RunScript(p0, p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12)

    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAACxIAAAsSAdLdfvwAAAClSURBVEhL7ZLRDYAgDESZiWGZyZn8qS3JkVooaAz9sskzhfN6AU1EtJX6OI9MQi7lhrcPVr64ACW0o/E6cfEblbq2QMdaees86R8HYF8DXfsEN0B68CbA6vEB+CjK8AnMiwvAkVi0BZNXQ727orAA6TVcbYDVZvofsNS7gO2/6fYAHIlFWzB5NdS7KwoLkF7D1QZYbabHB+CjQADePlj54gL2QekC+ZuAi+2XxMIAAAAASUVORK5CYII="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    def RunScript(self, run, meshes, lines, supports, load_points, fixed, elasticity, poisson, density, thickness, width, height, uni_load):
                    
        def clear(layer_name):
            sc.doc = Rhino.RhinoDoc.ActiveDoc
            objects = sc.doc.Objects.FindByLayer(layer_name)
            if objects != None:
                for obj in objects: sc.doc.Objects.Delete(obj, True)
            sc.doc = GhPython.DocReplacement.GrasshopperDocument()

        def bake(objects, layer_name, color=(0,0,0,255)):
            for obj in objects:
                #create layer
                sc.doc = Rhino.RhinoDoc.ActiveDoc
                rs.AddLayer(layer_name, color, visible=True, locked=False, parent=None)

                #create object
                sc.doc = GhPython.DocReplacement.GrasshopperDocument()
                try: obj = sc.doc.Objects.Add(obj)
                except: obj = sc.doc.Objects.AddPoint(obj)
                obj_object = rs.coercerhinoobject(obj)
                obj_attributes = obj_object.Attributes
                obj_geometry = obj_object.Geometry

                #select layer to bake and add to the attributes
                sc.doc = Rhino.RhinoDoc.ActiveDoc
                layertable = sc.doc.Layers
                obj_attributes.LayerIndex = layertable.Find(layer_name,True)

                #bake object
                sc.doc.Objects.Add(obj_geometry, obj_attributes, None, True)
                sc.doc = GhPython.DocReplacement.GrasshopperDocument()

        try:
            from compas.geometry import cross_vectors
            from compas.geometry import normalize_vector
            from compas.geometry import subtract_vectors
            from compas_fea.cad import rhino
            from compas_fea.structure import ElasticIsotropic
            from compas_fea.structure import ElementProperties as Properties
            from compas_fea.structure import GeneralStep
            from compas_fea.structure import FixedDisplacement
            from compas_fea.structure import PinnedDisplacement
            from compas_fea.structure import RollerDisplacementX
            from compas_fea.structure import PointLoad
            from compas_fea.structure import ShellSection
            from compas_fea.structure import RectangularSection
            from compas_fea.structure import CircularSection
            from compas_fea.structure import Structure
        except: self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Error, 'Compas and compas_fea are both required to run the analysis. Please verify that both are installed and available in Rhino.')
        
        if run is True:

            meshes = [rs.coercemesh(mesh) for mesh in meshes]
            lines = [line.ToNurbsCurve() for line in lines]
            supports = rs.coerce3dpointlist(supports)
            load_points = rs.coerce3dpointlist(load_points)

            #Bake initial conditions in Rhino
            clear("elset_mesh")
            bake(meshes, "elset_mesh", color=(50,150,150,255))
            clear("elset_beams")
            bake(lines, "elset_beams", color=(250,200,50,255))
            clear("nset_support")
            bake(supports, "nset_support", color=(250,0,0,255))
            clear("nset_load")
            bake(load_points, "nset_load", color=(0,250,0,255))
        
            sc.doc = Rhino.RhinoDoc.ActiveDoc
        
            # Local Coordinate System per each element
            for i in rs.ObjectsByLayer('elset_beams'):
                ez = subtract_vectors(rs.CurveEndPoint(i), rs.CurveStartPoint(i))
                ex = normalize_vector(cross_vectors(ez, [0, 0, 1]))
                rs.ObjectName(i, '_{0}'.format(json.dumps({'ex': ex})))
        
            # Structure
            mdl = Structure(name=datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S"), path='C:/temp/')
        
            # Elements
            rhino.add_nodes_elements_from_layers(mdl, mesh_type='ShellElement', layers='elset_mesh')
            rhino.add_nodes_elements_from_layers(mdl, line_type='BeamElement', layers='elset_beams')

            # Sets
            rhino.add_sets_from_layers(mdl, layers=['nset_load', 'nset_support'])

            # Materials
            mdl.add(ElasticIsotropic(name='mat_elastic_plate', E=elasticity, v=poisson, p=density))
            mdl.add(ElasticIsotropic(name='mat_elastic_connections', E=elasticity, v=poisson, p=density))

            # Sections
            mdl.add(ShellSection(name='sec_plate', t=thickness))
            mdl.add(RectangularSection(name='sec_beam', b=width, h=height))
            
            
            # Properties
            mdl.add(Properties(name='ep_plate', material='mat_elastic_plate', section='sec_plate', elset='elset_mesh'))
            mdl.add(Properties(name='ep_beam', material='mat_elastic_connections', section='sec_beam', elset='elset_beams'))
            
            # Displacements
            if fixed is True: mdl.add([FixedDisplacement(name='disp', nodes='nset_support')])
            else: mdl.add([PinnedDisplacement(name='disp', nodes='nset_support')])
        
            # Loads
            mdl.add(PointLoad(name='load_point', nodes='nset_load', z=uni_load))

            # Steps
            mdl.add([
                GeneralStep(name='step_bc', displacements=['disp']),
                GeneralStep(name='step_load', loads=['load_point'], tolerance=1, iterations=500),
            ])
            mdl.steps_order = ['step_bc', 'step_load']
            
            # Summary
            mdl.summary()
            
            # Run
            mdl.analyse_and_extract(software='abaqus',
                fields=['u', 'sf', 'cf', 'rf', 's'],
                components=['ux', 'uy', 'uz', 'rfx', 'rfy', 'rfz', 'cfx', 'cfy', 'cfz', 'sxx', 'syy', 'smises'])
            
            # Output
            rhino.plot_data(mdl, step='step_load', field='uz', radius=10.0, scale=50.0)
            #rhino.plot_data(mdl, step='step_load', field='sxx', radius=10., scale=100.0)
            #rhino.plot_data(mdl, step='step_load', field='syy', radius=10., scale=100.0)
            rhino.plot_reaction_forces(mdl, step='step_load', scale=100.0)
            rhino.plot_concentrated_forces(mdl, step='step_load', scale=100.0)
            rhino.plot_data(mdl, step='step_load', field='smises', radius=100.)
            
            mdl.save_to_obj()
        
            sc.doc = GhPython.DocReplacement.GrasshopperDocument()

        return

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "FEM_analysis"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("6a7710df-9747-452c-a3a5-67114d94b67a")