"""Build a plate model from a list of breps"""

from ghpythonlib.componentbase import dotnetcompiledcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
from ghpythonlib import components as gh
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper.Kernel.GH_Convert import ObjRefToGeometry, ToGHBrep
from Grasshopper.Kernel import GH_Conversion 
import scriptcontext
import math
import copy
import ast
from datetime import date

__author__ = "Nicolas Rogeau"
__laboratory__ = "IBOIS, Laboratory for Timber Construction" 
__university__ = "EPFL, Ecole Polytechnique Federale de Lausanne"
__funding__ = "NCCR Digital Fabrication, ETH Zurich"
__version__ = "2020.01"

class MyComponent(component):
    def __new__(cls):
        instance = Grasshopper.Kernel.GH_Component.__new__(cls,
            "Plate Model Builder", "Build", """Build a plate model from a list of breps.""", "Manis", "Solver")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("56e1ad4c-ad3d-4600-999b-b6d72f780afa")
    
    def SetUpParam(self, p, name, nickname, description):
        p.Name = name
        p.NickName = nickname
        p.Description = description
        p.Optional = True
    
    def RegisterInputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_Boolean()
        self.SetUpParam(p, "run", "run", "Run the model if True.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Brep()
        self.SetUpParam(p, "breps", "breps", "List of Breps ID to define a new sequence.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_String()
        self.SetUpParam(p, "sequence", "sequence", "(Optional) List of integers to change the sequence of assembly.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "constraints", "constraints", "(optional) Constrained insertion spaces associated to each contact type. ")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)
        
    
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "model", "model", "Plate model.")
        self.Params.Output.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Brep()
        self.SetUpParam(p, "breps", "breps", "List of Breps (re-ordered).")
        self.Params.Output.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "sequence", "sequence", "Updated sequence (re-ordered).")
        self.Params.Output.Add(p)
    
    def SolveInstance(self, DA):
        p0 = self.marshal.GetInput(DA, 0)
        p1 = self.marshal.GetInput(DA, 1)
        p2 = self.marshal.GetInput(DA, 2)
        p3 = self.marshal.GetInput(DA, 3)
        result = self.RunScript(p0, p1, p2, p3)

        if result is not None:
            if not hasattr(result, '__getitem__'):
                self.marshal.SetOutput(result, DA, 0, True)
            else:
                self.marshal.SetOutput(result[0], DA, 0, True)
                self.marshal.SetOutput(result[1], DA, 1, True)
                self.marshal.SetOutput(result[2], DA, 2, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAJOgAACToAYJjBRwAAAFFSURBVEhLrVKxbcNADHy4SxOkDAJkiaySFTKTG8+RAQK4yBoG1Agp3LuQTUp/1JH6f8lGDjjweTwebcNpI64rfBgW8rHfO0Jjj3AzLIADWavNhU0UQ6LGPc8xExaxWOAl9KxzZT3TwRlataUV+hE2QGVT7Nc0vKELvQBjMLlZ7R21vOfNka2ZkmfsJX1uLr9fxjx0RAAYtejL/RwA4MD3z/FTa+2gksNCMDg9EKKAJlTYt4rUmbJ0gA5VfxrF+OZ5JDzK0iHhHJCFUcyohkU9fnJ3IJCxCJrk9gEKh78KNvLCQo+fnI78C8aw58MBof5A13XvuZmE++ACKVj/kDupKQ3D8ASRuAbzamg8cD2fX6Q6OMMWcjB6rX+n05tUj/x13BLXmq41voVVuIVGgPXRJ9wEW+AAvLmHr+/7V6l3wwJWWEFKN+3n1K9qHyYeAAAAAElFTkSuQmCC"
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, run, breps, sequence, constraints):
        

        #Model -----------------------------------------------------------------------
        
        class PlateModel:

            def __init__(self, breps, sequence=0, constraints=[None,None,None,None,None]):

                    # INITIALIZATION -------------------------------------

                    self.temp = []
                    self.log = []
                    self.count = len(breps)
                    self.sequence = self.__set_sequence(sequence)
                    self.breps = self.__reorder_breps(breps)
                    self.sequence = self.__reorder_sequence(self.sequence)
                    self.plates = self.__get_plates_from_breps()

                    # TOPOLOGY -------------------------------------------

                    self.contact_ids = self.__get_contact_ids()
                    self.contact_pairs = self.__get_contact_pairs()
                    self.contact_breps = self.__get_contact_breps()
                    self.contact_zones= self.__get_contact_zones()
                    self.contact_types = self.__get_contact_types()
                    self.contact_strings = self.__get_contact_strings()
                    self.contact_centers= self.__get_contact_centers()
                    self.contact_normals = self.__get_contact_normals()
                    self.contact_planes= self.__get_contact_planes()
                    self.contact_spheres = self.__get_contact_spheres(constraints)
                    
                    # ASSEMBLY -------------------------------------------

                    self.contact_vectors = []
                    self.modules = self.__get_modules_from_sequence()
                    self.__get_assembly_vectors()


            # MODEL INITIALIZATION ---------------------------------------

            def __set_sequence(self, sequence):
                """return the default sequence if incorrect input is provided"""
                if sequence == 0 or sequence == [] or sequence == None:
                    self.log.append('Sequence set to default : '+ str(range(self.count)))
                    return str(range(self.count))
                else:
                    if type(sequence) is str:
                        Toolbox.Data.test_seq(sequence)
                        try: test = ast.literal_eval(sequence)
                        except: raise Exception(' An error occured when trying to convert sequence text to list of lists.')
                        self.log.append('Sequence set to custom : '+ str(sequence))
                        return sequence
                    else: raise Exception(' Sequence input should be expressed as a string.')

            def __reorder_breps(self, breps):
                seq = ast.literal_eval(self.sequence)
                return Toolbox.Data.sort_list_sync(breps, Toolbox.Data.flatten_integer_list(seq))

            def __reorder_sequence(self, sequence):
                new_sequence = Toolbox.Data.reorder_sequence(sequence)
                if new_sequence != sequence:
                    self.log.append('Breps and sequence have been reordered: '+ str(new_sequence))
                return new_sequence

            def __get_plates_from_breps(self):
                plates=[]
                for i in range(len(self.breps)):
                    # plate object creation
                    plates.append(Plate(self.breps[i], i)) 
                return plates

            def __get_modules_from_sequence(self):

                # create sub_sequence list
                seq = ast.literal_eval(self.sequence)
                steps = Toolbox.Data.seq_to_steps(seq)
                steps = Toolbox.Data.order_sequence(steps)
                sub_seq = []
                sub_steps = []

                for i in range(len(steps)):
                    if steps[i] in Toolbox.Data.deepest_steps(seq): pass
                    else:
                        sub_steps.append(steps[i])
                        sub_seq.append(Toolbox.Data.get_item_from_path(seq, steps[i]))
                sub_seq.append(seq)
                sub_steps.append(['Model'])

                # fill parent list
                parents = []
                for sub_step in sub_steps:
                    if sub_step == ['Model']: parents.append([])
                    elif len(sub_step) == 1 : parents.append(['Model'])
                    else: parents.append(sub_step[0:len(sub_step)-1])

                # fill children list
                children = Toolbox.Data.list_of_empty_lists(len(parents))
                for i in range(len(parents)):
                    for j in range(len(sub_steps)):
                        if parents[i] == sub_steps[j]: 
                            children[j].append(sub_steps[i])

                # module creation
                modules = []
                for i in range(len(sub_seq)):
                    modules.append(PlateModules(self, i, sub_steps[i], str(sub_seq[i]), parents[i], children[i]))
                return modules

            # MODEL TOPOLOGY ---------------------------------------------

            def __get_contact_ids(self):
                mylist = []
                for i in range(self.count):
                    sub = []
                    for j in range(self.count):
                        if i != j:
                            intersect = rs.IntersectBreps(self.breps[i],self.breps[j])
                            if intersect != None:
                                if len(intersect) == 1:
                                    if rs.IsCurveClosed(intersect) is True:
                                        if rs.IsCurvePlanar(intersect) is True:
                                            sub.append(j)
                                        else:
                                            # if plate contours are intersecting the surfaces of the other plate
                                            if rs.CurveBrepIntersect(self.plates[i].top_contour,self.plates[j].top_face) != None:
                                                if rs.CurveBrepIntersect(self.plates[i].top_contour,self.plates[j].bottom_face) != None: 
                                                    if rs.CurveBrepIntersect(self.plates[i].bottom_contour,self.plates[j].top_face) != None:
                                                        if rs.CurveBrepIntersect(self.plates[i].bottom_contour,self.plates[j].bottom_face) != None:
                                                            sub.append(j)
                    mylist.append(sub)
                return mylist

            def __get_contact_pairs(self):
                mylist = []
                for i in range(self.count):
                    sub = []
                    for j in range(len(self.contact_ids[i])):
                        brep_id = self.contact_ids[i][j]
                        sub.append( '(' + str(i) + ',' + str(brep_id) + ')' )
                    mylist.append(sub)
                return mylist

            def __get_contact_breps(self):
                mylist = []
                for i in range(self.count):
                    sub = []
                    for j in range(len(self.contact_ids[i])):
                        brep_id = self.contact_ids[i][j]
                        brep = rs.coercebrep(rs.CopyObject(self.breps[brep_id]))
                        sub.append(brep)
                    mylist.append(sub)
                return mylist
            
            def __get_contact_zones(self):
                mylist = []
                for i in range(self.count):
                    sub = []
                    for j in range(len(self.contact_ids[i])):
                            brep_id = self.contact_ids[i][j]
                            pi = copy.deepcopy(self.plates[i])
                            pj = copy.deepcopy(self.plates[brep_id])
                            intersect = rs.IntersectBreps(pi.brep,pj.brep)
                            if intersect !=  None:
                                if len(intersect) == 1: 
                                    if rs.IsCurveClosed(intersect) is True:
                                        if rs.IsCurvePlanar(intersect) is True:
                                            zone = rs.coercegeometry(rs.AddPlanarSrf(intersect)[0])
                                            sub.append(zone)
                                        # intersecting breps
                                        else:
                                            # if plate contours are intersecting the surfaces of the other plate
                                            if rs.CurveBrepIntersect(pi.top_contour, pj.top_face) != None:
                                                if rs.CurveBrepIntersect(pi.top_contour, pj.bottom_face) != None: 
                                                    if rs.CurveBrepIntersect(pi.bottom_contour, pj.top_face) != None:
                                                        if rs.CurveBrepIntersect(pi.bottom_contour, pj.bottom_face) != None:
                                                            volume = rg.Brep.CreateBooleanIntersection(pi.brep,pj.brep,0.1)[0]
                                                            edges = Toolbox.Breps.brep_edges(volume)
                                                            edges.sort(key=rs.CurveLength)
                                                            edges.reverse()
                                                            vec_dir = Toolbox.Vectors.round_vector(rs.VectorUnitize(Toolbox.Vectors.cross(pi.top_normal, pj.top_normal)),3)
                                                            four_edges = []
                                                            for edge in edges:
                                                                vec_line = Toolbox.Vectors.round_vector(rs.VectorUnitize(Toolbox.Vectors.line_to_vec(edge)),3) 
                                                                if vec_dir == vec_line or vec_dir == rs.VectorReverse(vec_line):
                                                                    four_edges.append(edge)
                                                                if len(four_edges) == 4: break
                                                            mids = [rs.CurveMidPoint(four_edges[k]) for k in range(4)]
                                                            center = Toolbox.Points.average_point(mids)
                                                            proj = rs.coerce3dpointlist([rs.EvaluateCurve(four_edges[l],rs.CurveClosestPoint(four_edges[l],center)) for l in range(4)])
                                                            poly = rs.AddPolyline(rs.PolylineVertices(gh.ConvexHull(proj, rs.PlaneFitFromPoints(proj))[0]))
                                                            zone = rs.coercegeometry(rs.AddPlanarSrf(poly)[0])
                                                            #orient surface normal
                                                            current_normal = rs.SurfaceNormal(zone,[0,0])
                                                            new_vec = Toolbox.Vectors.line_to_vec(four_edges[0],True)
                                                            test_point = rs.CurveStartPoint(four_edges[0])
                                                            test1 = rs.IsPointOnCurve(pi.top_contour, test_point)
                                                            test2 = rs.IsPointOnCurve(pi.bottom_contour, test_point)
                                                            if test1 is True or test2 is True:
                                                                new_vec =rs.VectorReverse(new_vec)
                                                            if rs.IsVectorParallelTo(current_normal, new_vec) == -1:
                                                                rs.FlipSurface(zone,True)
                                                            sub.append(zone)    
                    mylist.append(sub)
                return mylist

            def __get_contact_types(self):
                mylist = []
                for i in range(self.count):
                    
                    sub = []
                    for j in range(len(self.contact_ids[i])):
                        nb = self.contact_ids[i][j]
                        zone = self.contact_zones[i][j]
                        zone_normal = rs.SurfaceNormal(zone,[0,0])
                        plate1_normal = self.plates[i].top_normal
                        plate2_normal = self.plates[nb].top_normal
                        cross1 = Toolbox.Vectors.cross(zone_normal,plate1_normal)
                        cross2 = Toolbox.Vectors.cross(zone_normal,plate2_normal)

                        if Toolbox.Vectors.isvectornull(cross1) is False and Toolbox.Vectors.isvectornull(cross2) is False :
                            intersect = rs.IntersectBreps(self.breps[i],self.breps[nb])
                            if rs.IsCurvePlanar(intersect) is True: sub.append('SS')
                            else: sub.append('IN')

                        elif Toolbox.Vectors.isvectornull(cross1) is True and Toolbox.Vectors.isvectornull(cross2) is True :
                            sub.append('FF')

                        else:
                            #edge test:
                            top_top = Toolbox.Curves.sharingEdge(self.plates[i].top_contour, self.plates[nb].top_contour)
                            top_bottom = Toolbox.Curves.sharingEdge(self.plates[i].top_contour, self.plates[nb].bottom_contour)
                            bottom_top = Toolbox.Curves.sharingEdge(self.plates[i].bottom_contour, self.plates[nb].top_contour)
                            bottom_bottom = Toolbox.Curves.sharingEdge(self.plates[i].bottom_contour, self.plates[nb].bottom_contour)
                            if Toolbox.Vectors.isvectornull(cross1) is True and Toolbox.Vectors.isvectornull(cross2) is False :
                                if top_top == None and top_bottom == None and bottom_top == None and bottom_bottom == None:
                                    sub.append('FS')
                                else: sub.append('ES')
                            elif Toolbox.Vectors.isvectornull(cross1) is False and Toolbox.Vectors.isvectornull(cross2) is True :
                                if top_top == None and top_bottom == None and bottom_top == None and bottom_bottom == None:
                                    sub.append('SF')
                                else: sub.append('SE')

                    mylist.append(sub)
                return mylist

            def __get_contact_strings(self):
                mylist = []
                for i in range(self.count):
                    sub = []
                    for j in range(len(self.contact_ids[i])):
                        brep_id = self.contact_ids[i][j]
                        ptype = self.contact_types[i][j]

                        if ptype == 'SS':
                            sub.append('Side of plate '+str(i)+' is connected to Side of plate '+str(brep_id))
                        elif ptype == 'FS':
                            sub.append('Face of plate '+str(i)+' is connected to Side of plate '+str(brep_id))
                        elif ptype == 'ES':
                            sub.append('Edge of plate '+str(i)+' is connected to Side of plate '+str(brep_id))
                        elif ptype == 'SF':
                            sub.append('Side of plate '+str(i)+' is connected to Face of plate '+str(brep_id))
                        elif ptype == 'SE':
                            sub.append('Side of plate '+str(i)+' is connected to Edge of plate '+str(brep_id))
                        elif ptype == 'FF':
                            sub.append('Face of plate '+str(i)+' is connected to Face of plate '+str(brep_id))
                        elif ptype == 'IN':
                            sub.append('Volume of plate '+str(i)+' is intersecting volume of plate '+str(brep_id))   
                    mylist.append(sub)
                return mylist

            def __get_contact_centers(self):
                mylist = []
                for i in range(self.count):
                    sub = []
                    for j in range(len(self.contact_ids[i])):
                        center = Toolbox.Surfaces.surface_centroid(self.contact_zones[i][j])
                        sub.append(rs.coerce3dpoint(center))
                    mylist.append(sub)
                return mylist

            def __get_contact_normals(self):
                mylist = []
                for i in range(self.count):
                    sub = []
                    for j in range(len(self.contact_ids[i])):
                        brep_id = self.contact_ids[i][j]
                        zone = self.contact_zones[i][j]
                        vec = rs.VectorUnitize(rs.SurfaceNormal(zone,[0,0]))
                        plate_center = self.plates[i].plate_center
                        zone_center = Toolbox.Surfaces.surface_centroid(zone)
                        if self.contact_types[i][j] != "IN":
                            if Toolbox.Vectors.is_vector_outward(plate_center, zone_center, copy.deepcopy(vec)) is False:
                                vec=rs.VectorReverse(copy.deepcopy(vec))
                        sub.append(rs.coerce3dvector(vec))
                    mylist.append(sub)
                return mylist

            def __get_contact_planes(self):
                mylist = []
                for i in range(self.count):
                    sub = []
                    for j in range(len(self.contact_ids[i])):
                        nb = self.contact_ids[i][j]
                        origin = self.contact_centers[i][j]
                        zone = Toolbox.Surfaces.get_face_largest_contour(self.contact_zones[i][j])
                        sides = rs.ExplodeCurves(rs.CopyObject(zone)) 
                        longest_side = Toolbox.Curves.sort_curves_by_length(sides)[-1][0]
                        x_axis = rs.VectorCreate(rs.CurveStartPoint(longest_side), rs.CurveEndPoint(longest_side))
                        plane = rs.PlaneFromNormal(origin, self.contact_normals[i][j], x_axis)
                        if self.contact_types[i][j] == 'ES':
                            if Toolbox.Vectors.is_vector_outward(self.plates[i].mid_plane.Origin, self.contact_centers[i][j], plane.YAxis) is False:
                                plane = rs.PlaneFromNormal(origin, self.contact_normals[i][j], -x_axis)
                        if self.contact_types[i][j] == 'SE':
                            if Toolbox.Vectors.is_vector_outward(self.plates[nb].mid_plane.Origin, self.contact_centers[i][j], plane.YAxis) is False:
                                plane = rs.PlaneFromNormal(origin, self.contact_normals[i][j], -x_axis)
                        sub.append(rs.coerceplane(plane))
                    mylist.append(sub)
                return mylist

            def __get_contact_spheres(self, constraints):

                # Create canonic insertion space
                sphere =  rs.AddSphere((0,0,0),1)
                cutter0 = rs.AddPlanarSrf(rs.AddPolyline([(1,1,0),(1,-1,0),(-1,-1,0),(-1,1,0),(1,1,0)]))
                hemisphere = rs.SplitBrep(sphere,cutter0)[1]
                cutter1 = rs.AddPlanarSrf(rs.AddPolyline([(1,0,1),(1,0,-1),(-1,0,-1),(-1,0,1),(1,0,1)]))
                quartersphere = rs.SplitBrep(hemisphere,cutter1)[1]
                hemicircle = rs.RotateObject(rs.AddArc(rs.WorldZXPlane(),1,180),(0,0,0),-90,(0,1,0))
                normal_point= rs.AddPoint(0,0,1)

                # Orient hemisphere on each conctact zone
                mylist = []
                for i in range(self.count):
                    sub = []
                    for j in range(len(self.contact_types[i])):
                        #face-to-face
                        
                        if self.contact_types[i][j] == 'FF':
                            if constraints[0] != None:
                                insertion_space = constraints[0]
                            else: insertion_space = hemisphere
                        #face-to-side
                        elif (self.contact_types[i][j] == 'FS' or self.contact_types[i][j]  == 'SF'):
                            if constraints[1] != None:
                                insertion_space = constraints[1]
                            else: insertion_space = hemicircle
                        #edge-to-side
                        elif (self.contact_types[i][j] == 'ES' or self.contact_types[i][j]  == 'SE'):
                            if constraints[2] != None:
                                insertion_space = constraints[2]
                            else: insertion_space = quartersphere
                        #side-to-side
                        elif self.contact_types[i][j] == 'SS':
                            if constraints[3] != None:
                                insertion_space = constraints[3]
                            else: insertion_space = hemicircle
                        #intersecting
                        elif self.contact_types[i][j] == 'IN':
                            if constraints[4] != None:
                                insertion_space = constraints[4]
                            else: insertion_space = normal_point
                        
                        matrix = rg.Transform.PlaneToPlane(rs.WorldXYPlane(), self.contact_planes[i][j])
                        insertion_space = rs.TransformObject(insertion_space, matrix,True)
                        sub.append(insertion_space)
                    mylist.append(sub)
                return mylist
            
            # MODULES ASSEMBLY -------------------------------------------

            def __get_assembly_vectors(self):
                
                adj = self.contact_ids
                seq = ast.literal_eval(self.sequence)
                steps = Toolbox.Data.seq_to_steps(seq)
                steps = Toolbox.Data.order_sequence(steps)

                sub_seq = []
                for i in range(len(steps)):
                    if steps[i] in Toolbox.Data.deepest_steps(seq): pass
                    else: sub_seq.append(Toolbox.Data.get_item_from_path(seq, steps[i]))
                sub_seq.append(seq)

                # Assembly vectors following modules list
                iv = copy.deepcopy(sub_seq)
                space = copy.deepcopy(sub_seq)
                rel = copy.deepcopy(sub_seq)
                gravity = rs.VectorCreate((0,0,-1),(0,0,0))
                for i in range(len(sub_seq)):
                    for j in range(len(sub_seq[i])):
                        # first element in subsequence
                        if j == 0:
                            iv[i][j] = gravity
                            rel[i][j] = []
                            space[i][j] = []

                        else:
                            # look for all connection between the plate (or a plate of the module) to insert and the plates in place
                            rel_list = [] #
                            is_list = [] #insertion spaces
                            # element in subsequence is a module
                            if type(sub_seq[i][j]) is list:
                                plates = Toolbox.Data.flatten_integer_list(sub_seq[i][j])
                                for plate in plates:
                                    neighbours = adj[plate]
                                    prequel = sub_seq[i][:j]
                                    # find all corespondance between the neighbour group and the prequel group
                                    for k in range(len(neighbours)):
                                        for l in range(len(prequel)):
                                            # element in prequel is a module
                                            if type(prequel[l]) is list:
                                                prequel[l] = Toolbox.Data.flatten_integer_list(prequel[l])
                                                for m in range(len(prequel[l])):
                                                    if prequel[l][m] == neighbours[k]:
                                                        to_zero = rs.VectorCreate((0,0,0),self.contact_centers[plate][k])
                                                        sphere = rs.CopyObject(self.contact_spheres[plate][k],to_zero)
                                                        is_list.append(sphere)
                                                        rel_list.append(neighbours[k])  
                                            # element in prequel is a plate
                                            else:
                                                if prequel[l] == neighbours[k]:
                                                    to_zero = rs.VectorCreate((0,0,0),self.contact_centers[plate][k])
                                                    sphere = rs.CopyObject(self.contact_spheres[plate][k],to_zero)
                                                    is_list.append(sphere)
                                                    rel_list.append(neighbours[k])

                            # element in subsequence is a plate
                            else: 
                                plate = sub_seq[i][j]
                                neighbours = adj[plate]
                                prequel = sub_seq[i][:j]
                                # find the first corespondance between the neighbour group and the prequel group
                                for k in range(len(neighbours)):
                                    for l in range(len(prequel)):
                                        # element in prequel is a module
                                        if type(prequel[l]) is list:
                                            for m in range(len(prequel[l])):
                                                if prequel[l][m] == neighbours[k]:
                                                    to_zero = rs.VectorCreate((0,0,0),self.contact_centers[plate][k])
                                                    sphere = rs.CopyObject(self.contact_spheres[plate][k],to_zero)
                                                    is_list.append(sphere)
                                                    rel_list.append(neighbours[k])
                                        # element in prequel is a plate
                                        else:
                                            if prequel[l] == neighbours[k]:
                                                to_zero = rs.VectorCreate((0,0,0),self.contact_centers[plate][k])
                                                sphere = rs.CopyObject(self.contact_spheres[plate][k],to_zero)
                                                is_list.append(sphere)
                                                rel_list.append(neighbours[k])

                            # If plate/module has no contact, add a default vector and a support
                            if is_list == []:
                                iv[i][j] = gravity
                                space[i][j] = []
                                rel[i][j] = []
                                self.modules[i].needed_supports += 1
                            
                            # If plate/module has contacts, intersect insertion spheres and take average candidate
                            else:

                                try:
                                    inter = self.intersect_insertion_spaces(is_list)

                                    iv[i][j] = inter[0] #average vector
                                    space[i][j] = inter[1] #candidates
                                    rel[i][j] = rel_list

                                except:
                                    iv[i][j] = gravity
                                    space[i][j] = []
                                    rel[i][j] = rel_list
                                    raise Exception('Insertion space intersection returns no compatible vector for plate(s) '+str(sub_seq[i][j])+' with plates '+str(rel[i][j]))

                                # if average vector failed or was null, take gravity instead
                                if iv[i][j] == None: iv[i][j] = gravity

                # Update modules attributes
                for i in range(len(self.modules)):
                    self.modules[i].assembly_vectors = iv[i]
                    self.modules[i].assembly_relatives = rel[i]
                    self.modules[i].assembly_spaces = space[i]
                
                # Assembly vectors following contact list
                iv2 = copy.deepcopy(self.contact_planes)
                rel2 = copy.deepcopy(self.contact_planes)
                # Compare each contact zone...
                for i in range(self.count):
                    for j in range(len(adj[i])):
                        
                        # ... with each module sequence.
                        search = True
                        for k in range(len(self.modules)):
                            # to retrieve the associated assembly vector
                            if search is True:
                                mod_seq = ast.literal_eval(self.modules[k].sequence)
                                plates_in_sequence = Toolbox.Data.flatten_integer_list(mod_seq)
                                if (i in plates_in_sequence) and (adj[i][j] in plates_in_sequence):
                                    for l in  range(len(mod_seq)):
                                        corresponding_vector = copy.deepcopy(self.modules[k].assembly_vectors[l])
                                        if type(mod_seq[l]) is list:
                                            plates_in_sub_sequence = Toolbox.Data.flatten_integer_list(mod_seq[l])
                                            if i < adj[i][j] and adj[i][j] in plates_in_sub_sequence:
                                                iv2[i][j] = corresponding_vector
                                                rel2[i][j] = adj[i][j]
                                                search = False
                                    
                                            elif i > adj[i][j] and i in plates_in_sub_sequence:
                                                iv2[i][j] = rs.VectorReverse(corresponding_vector)
                                                rel2[i][j] = adj[i][j]
                                                search = False

                                        else:
                                            if i < adj[i][j] and mod_seq[l] == adj[i][j]:
                                                iv2[i][j] = corresponding_vector
                                                rel2[i][j] = adj[i][j]
                                                search = False

                                            elif i > adj[i][j] and mod_seq[l] == i:
                                                iv2[i][j] = rs.VectorReverse(corresponding_vector)
                                                rel2[i][j] = adj[i][j]
                                                search = False
                self.assembly_relatives = rel2
                self.contact_vectors = iv2

                #coerce geometry of contact spheres to avoid guid instance problem.
                for i in range(len(self.contact_spheres)):
                    for j in range(len(self.contact_spheres[i])):
                        self.contact_spheres[i][j]=rs.coercegeometry(self.contact_spheres[i][j])

            def intersect_insertion_spaces(self, insertion_spaces):
                """
                Hypothesis:
                    insertion spaces are points, curves and surfaces
                    pts, crvs and srfs are parts of a sphere of radius 1
                    crvs are geodesics on that sphere
                    crvs are smaller than the hemisphere (L = pi.r)
                    srfs have convex perimeters and no holes
                    srfs are smaller than the hemisphere (A = 2.pi.r^2)
                Method:
                    we start from the most constraining (point to surface)
                    we avoid surface intersection using geodesic points
                """

                # Sort insertion_spaces
                pts,crvs,srfs = [],[],[]
                for space in insertion_spaces:
                    if rs.IsPoint(space) is True:
                        pts.append(space)
                    elif rs.IsCurve(space) is True:
                        crvs.append(space)        
                    elif rs.IsBrep(space) is True:
                        srfs.append(space)
                geodesic_cloud = Toolbox.Points.geodesic_sphere_points()

                tol = 0.001 # intersection tolerance
                dso = 2 # design space order
                candidates = []
                
                # Intersection functions:
                
                def pt_pt(pt1, pt2, tol):
                    if rs.Distance(pt1,pt2) > tol:
                        raise Exception('No pt-pt intersection was found')
                
                def pt_crv(pt,crv):
                    if rs.IsPointOnCurve(crv, pt) is False:
                        raise Exception('No pt-crv intersection was found')
                
                def pts_crv(pts, crv, warning=True):
                    new_pts = []
                    for pt in pts:
                        if rs.IsPointOnCurve(crv, pt) is True:
                            new_pts.append(pt)
                    if new_pts == [] and warning == True:
                        raise Exception('No pts-crv intersection was found')
                    else: return new_pts
                
                def pt_srf(pt,srf):
                    if rs.IsPointOnSurface(srf, pt) is False:
                        raise Exception('No pt-srf intersection was found')
                
                def pts_srf(pts, srf, tol, warning=True):
                    new_pts = []
                    for pt in pts:
                        srf_pt = rs.BrepClosestPoint(srf,pt)[0]
                        if rs.Distance(pt,srf_pt) < tol:
                            new_pts.append(pt)
                    if new_pts == [] and warning==True:
                        raise Exception('No pts-srf intersection was found')
                    else: return new_pts
                
                def crv_crv(crv1, crv2, warning=True):
                    inter = rs.CurveCurveIntersection(crv1,crv2)
                    if inter == None and warning == True:
                        raise Exception('No crv-crv intersection was found')
                    else: return inter
                
                def crv_srf():
                    pass
                
                def srf_srf():
                    pass
                
                def dist_to_srf(srf,pt):
                    srf_pt = rs.BrepClosestPoint(srf,pt)[0]
                    return rs.Distance(srf_pt,pt)
                
                def dist_to_crv(crv,pt):
                    t = rs.CurveClosestPoint(crv,pt)
                    return rs.Distance(rs.EvaluateCurve(crv,t),pt)
                
                def crv_to_pts(crv):
                    segments = rs.CurveLength(crv) /0.01
                    pts = rs.DivideCurve(crv,segments)
                    return pts
                
                def srf_to_pts(srf,geodesic_cloud,edge=True):
                    pts=[]
                    border = rs.DuplicateSurfaceBorder(srf,1)
                    if edge is True:
                        border_pts = crv_to_pts(border)
                        for pt in border_pts:
                            pts.append(pt)
                    for pt in geodesic_cloud:
                        pt = rs.AddPoint(pt)
                        srf_pt = rs.BrepClosestPoint(srf,pt)[0]
                        if rs.Distance(srf_pt,pt) < tol:
                            t =rs.CurveClosestPoint(border,pt)
                            border_pt = rs.EvaluateCurve(border,t)
                            if rs.Distance(border_pt,pt) > tol:
                                pts.append(pt)
                    return pts
                
                # Start from points
                if len(pts) != 0:
                    dso = 0
                    candidates.append(pts[0])
                    #check points
                    for i in range(len(pts)-1):
                        pt_pt(candidates[0],pts[i+1],tol)
                    # check curves
                    for crv in crvs:
                        pt_crv(candidates[0],crv)
                    # check surfaces
                    for srf in srfs:
                        pt_srf(candidates[0],srf)
                
                # Start from curves
                elif len(crvs) != 0:
                    dso = 1
                    candidates = crv_to_pts(crvs[0])
                    base_crv = crvs[0]
                    #check curves
                    for i in range(len(crvs)-1):
                        if dso == 1:
                            inter = crv_crv(base_crv,crvs[i+1])[0]
                            #intersection
                            if inter[0] == 1:
                                candidates = [inter[1]]
                                dso = 0
                            #overlap
                            else:
                                candidates = pts_crv(candidates,crvs[i+1])
                                new_start=rs.CurveClosestPoint(base_crv,candidates[0])
                                new_end=rs.CurveClosestPoint(base_crv,candidates[-1])
                                base_crv=rs.AddSubCrv(base_crv,new_start,new_end)
                        else: candidates = pt_crv(candidates[0],crvs[i+1])
                    # check surfaces
                    for srf in srfs:
                        candidates = pts_srf(candidates,srf,tol)
                
                # Start from surfaces
                elif len(srfs) != 0:
                    dso = 2
                    candidates = srf_to_pts(srfs[0],geodesic_cloud,edge=True)
                    # check surfaces
                    for i in range(len(srfs)-1):
                        candidates = pts_srf(candidates,srfs[i+1],tol,False)
                        #complete border
                        border_i = rs.DuplicateSurfaceBorder(srfs[i+1])
                        border_points = crv_to_pts(border_i)
                        for j in range(i+1):
                            border_points = pts_srf(border_points,srfs[j],tol,False)
                        candidates = candidates + border_points
                        if candidates == []: raise Exception('No srf-srf intersection was found')
                
                else: raise Exception('Please provide at least one point/curve/surface')

                
                if len(candidates) == 1:
                    chosen = candidates[0]
                elif len(candidates) > 1:
                    l = len(candidates)
                    x = 0
                    y = 0
                    z = 0
                    for i in range(len(candidates)):
                        if rs.IsPoint(candidates[i]) is False:
                            candidates[i] = rs.AddPoint(candidates[i])
                        coord = rs.PointCoordinates(candidates[i])
                        candidates[i] = rs.coercegeometry(candidates[i])
                        x += coord[0]
                        y += coord[1]
                        z += coord[2]
                    x = x/l
                    y = y/l
                    z = z/l
                    chosen = rs.AddPoint(x,y,z)
                vector = rs.VectorUnitize(rs.VectorCreate(chosen,(0,0,0)))
                return (vector, candidates)
                
            # Decorator -----------------------------------

            def __skip_nones(fun):
                """
                Decorator to use default value if parameter is null or is an empty list.
                """
                def _(*args, **kwargs):
                    for a, v in zip(fun.__code__.co_varnames, args):
                        if v is not None and v!=[]:
                            kwargs[a] = v 
                    return fun(**kwargs)
                return _
            
            # PLATE JOINERY ----------------------------------------------

            @__skip_nones
            def add_dowels(self, 
                plates_pairs='all', 
                dowel_number=1.0, 
                dowel_radius=0.5, 
                dowel_tolerance=0.0, 
                dowel_retreat_1=0.0, 
                dowel_retreat_2=0.0, 
                circle_radius=3.0, 
                circle_rotation=0.0, 
                dowel_angle_1=0.0, 
                dowel_angle_2=0.0, 
                parallel=False, 
                tile=False):

                """Add dowels on Face-to-Face contact zones."""

                #cast plate_pairs to string
                if plates_pairs != 'all':
                    for i in range(len(plates_pairs)):
                        plates_pairs[i] = str(plates_pairs[i])
                
                #conditional loop
                for i in range(self.count):
                    types = self.contact_types[i]
                    for j in range(len(types)):
                        nb = self.contact_ids[i][j]

                        #specific selection function
                        if ((plates_pairs == 'all') 
                            or ('('+str(i)+','+str(nb)+')' == plates_pairs) 
                            or ('('+str(i)+','+str(nb)+')' in plates_pairs)): 
                                i_want_a_dowel = True
                        else: i_want_a_dowel = False

                        #for all specified Face-to-Face connection
                        if (types[j] == 'FF') and (nb > i) and (i_want_a_dowel is True):

                            #prerequisite
                            if dowel_radius <= 0 : raise Exception(' Dowel_radius must be greater than 0')
                            if dowel_number <= 0 : raise Exception(' Dowel_number must be greater than 0')
                            if dowel_tolerance < 0 : raise Exception(' Dowel_tolerance must be greater than 0')
                            if dowel_retreat_1 >= self.plates[i].thickness : raise Exception(' Dowel_retreat_1 must be smaller than plate '+str(i)+' thickness')
                            if dowel_retreat_2 >= self.plates[nb].thickness : raise Exception(' Dowel_retreat_2 must be smaller than plate '+str(nb)+' thickness')
                            if circle_radius <= 0 : raise Exception(' Circle_radius must be greater than 0')
                            if not (-180.0 <= dowel_angle_1 <= 180.0) : raise Exception(' Dowel_angle_1 must be between -180 and 180')
                            if not (-45.0 <= dowel_angle_2 <= 45.0) : raise Exception(' Dowel_angle_1 must be between -45 and 45')


                            #location
                            plane = self.contact_planes[i][j]
                            location=[]
                            if dowel_number == 1:
                                location.append(plane)
                            elif dowel_number > 1:
                                polygon = Toolbox.Curves.create_polygon(plane, circle_radius, dowel_number)
                                polygon = rs.RotateObject(polygon, plane.Origin, circle_rotation, plane.ZAxis)
                                vertices = rs.PolylineVertices(polygon)
                                for k in range(len(vertices)-1):
                                    x_axis = rs.VectorCreate(plane.Origin,vertices[k])
                                    new_plane = rs.PlaneFromNormal(vertices[k], plane.ZAxis, x_axis)
                                    location.append(new_plane)

                            if tile != False :
                                tile = scriptcontext.doc.Objects.Add(tile)    

                            for k in range(len(location)):
                                
                                #construction lines
                                base_circle = tile
                                if tile == False :
                                    base_circle = rs.AddCircle(location[k],float(dowel_radius))
                                
                                else : 
                                    x_target = rs.CopyObject(location[k].Origin, location[k].XAxis)
                                    y_target = rs.CopyObject(location[k].Origin, location[k].YAxis)
                                    base_circle = Toolbox.Planes.orient(tile, rs.WorldXYPlane(), rs.RotatePlane(location[k], 90, location[k].ZAxis))
                                
                                top_circle = rs.CopyObject(base_circle, self.contact_normals[i][j] * (self.plates[nb].thickness - dowel_retreat_2))
                                bottom_circle = rs.CopyObject(base_circle, -self.contact_normals[i][j] * (self.plates[i].thickness - dowel_retreat_1))
                                
                                #inclination
                                if (-180 <= dowel_angle_1 <= 180) and (-45 <= dowel_angle_2 <= 45) :
                                    if parallel is True :
                                        ref = rs.PlaneFromFrame(plane.Origin,plane.XAxis,plane.YAxis)
                                        ref = rs.RotatePlane(ref, dowel_angle_1, ref.ZAxis)
                                    else :
                                        x_axis = rs.VectorCreate(plane.Origin, location[k].Origin)
                                        ref = rs.PlaneFromNormal(location[k].Origin, plane.ZAxis, x_axis)
                                    top_move = (self.plates[nb].thickness - dowel_retreat_2) * math.tan(math.radians(dowel_angle_2)) * ref.XAxis
                                    bottom_move = (self.plates[i].thickness - dowel_retreat_1) * math.tan(math.radians(dowel_angle_2)) * -ref.XAxis
                                    rs.MoveObject(top_circle,top_move)
                                    rs.MoveObject(bottom_circle,bottom_move)

                                #keys geometry
                                rail = rs.AddLine(rs.CurveAreaCentroid(bottom_circle)[0],rs.CurveAreaCentroid(top_circle)[0])
                                cylinder = rs.ExtrudeCurve(bottom_circle, rail)
                                rs.CapPlanarHoles(cylinder)
                                self.plates[nb].joints_keys.append(rs.coercebrep(cylinder))

                                #solid
                                base_circle_bool = Toolbox.Curves.offset(base_circle, - dowel_tolerance)
                                rail_top = rs.AddLine(rs.CurveAreaCentroid(base_circle)[0],rs.CurveAreaCentroid(top_circle)[0])
                                cylinder_top = rs.ExtrudeCurve(base_circle_bool, rail_top)
                                rail_bottom = rs.AddLine(rs.CurveAreaCentroid(base_circle)[0],rs.CurveAreaCentroid(bottom_circle)[0])
                                cylinder_bottom = rs.ExtrudeCurve(base_circle_bool, rail_bottom)
                                rs.CapPlanarHoles(cylinder_top)
                                rs.CapPlanarHoles(cylinder_bottom)
                                self.plates[i].joints_negatives.append(rs.coercebrep(cylinder_bottom))
                                self.plates[nb].joints_negatives.append(rs.coercebrep(cylinder_top))

                                #fabrication lines
                                top_poly = rs.ConvertCurveToPolyline(top_circle, 10)
                                bottom_poly = rs.ConvertCurveToPolyline(bottom_circle, 10)
                                base_poly = rs.ConvertCurveToPolyline(base_circle, 10)

                                if dowel_retreat_1 == 0 :
                                    self.plates[i].top_holes.append(rs.coercecurve(base_poly))
                                    self.plates[i].bottom_holes.append(rs.coercecurve(bottom_poly))   
                                else:
                                    self.plates[i].top_holes.append(rs.coercecurve(base_poly))
                                    self.plates[i].bottom_holes.append(rs.coercecurve(bottom_poly))   
                                if dowel_retreat_2 == 0 :
                                    self.plates[nb].top_holes.append(rs.coercecurve(top_poly))
                                    self.plates[nb].bottom_holes.append(rs.coercecurve(base_poly))  
                                else:
                                    self.plates[nb].top_holes.append(rs.coercecurve(top_poly))
                                    self.plates[nb].bottom_holes.append(rs.coercecurve(base_poly))  

                            self.log.append('Dowel joint added bewteen plates '+ str(i)+ ' and '+str(nb))

            @__skip_nones
            def add_tenons(self, 
                plates_pairs='all', 
                tenon_number=1.0, 
                tenon_length='default', 
                tenon_width=1.0, 
                tenon_space=1.0,
                tenon_shift=0.0,
                tenon_angle=0.0,
                assembly=True,
                specific_vector=None):

                """Add tenon and mortise on Side-to-Face or Face-to-Side contact zones."""
                
                #cast plate_pairs to string
                if plates_pairs != 'all':
                    for i in range(len(plates_pairs)):
                        plates_pairs[i] = str(plates_pairs[i])
                
                #conditional loop
                for i in range(self.count):
                    types = self.contact_types[i]
                    for j in range(len(types)):
                        nb = self.contact_ids[i][j]

                        #specific selection function
                        if ((plates_pairs == 'all') 
                            or ('('+str(i)+','+str(nb)+')' == plates_pairs) 
                            or ('('+str(i)+','+str(nb)+')' in plates_pairs)
                            or ('('+str(nb)+','+str(i)+')' == plates_pairs) 
                            or ('('+str(nb)+','+str(i)+')' in plates_pairs)): 
                                i_want_a_tenon = True
                        else: i_want_a_tenon = False
                        
                        #for all specified Side-to-Face connection
                        if (types[j] in 'SFS') and (nb > i) and i_want_a_tenon is True:
                            
                            #prerequisite
                            if tenon_number <= 0 : raise Exception(' Tenon_number must be greater than 0')
                            if tenon_width <= 0 : raise Exception(' Tenon_width must be greater than 0')

                            #male-female parameters
                            if types[j] == 'SF':
                                male = i
                                female = nb
                                plane_zone = rs.PlaneFromFrame(self.contact_planes[i][j].Origin, self.contact_planes[i][j].XAxis, self.contact_planes[i][j].YAxis)
                            if types[j] == 'FS':
                                male = nb
                                female = i
                                plane_zone = rs.PlaneFromFrame(self.contact_planes[i][j].Origin, self.contact_planes[i][j].YAxis, self.contact_planes[i][j].XAxis)
                            plane_male = self.plates[male].top_plane
                            plane_female = self.plates[female].top_plane
                            thickness_female = self.plates[female].thickness
                            top_contour_male = copy.deepcopy(self.plates[male].top_contour)
                            bottom_contour_male = copy.deepcopy(self.plates[male].bottom_contour)
                            top_contour_mstart = rs.CurveStartPoint(top_contour_male)
                            bottom_contour_mstart= rs.CurveStartPoint(bottom_contour_male)
                            
                            #joint location
                            zone = self.contact_zones[i][j]
                            rectangle = Toolbox.Curves.trapeze_to_rectangle(rs.JoinCurves(rs.DuplicateEdgeCurves(zone)))
                            if Toolbox.Curves.rectangle_dimensions(rectangle)[0] < (tenon_width*tenon_number + tenon_space*(tenon_number) + tenon_shift*2):
                                excess = (tenon_width*tenon_number + tenon_space*(tenon_number) + tenon_shift*2) / (Toolbox.Curves.rectangle_dimensions(rectangle)[0]) * 100
                                raise Exception(' Joint is to large ('+ str(int(excess)) +' %) for contact area between plate '+str(i)+' and plate '+str(nb))
                            center = rs.CurveAreaCentroid(rectangle)[0]
                            default_direction = Toolbox.Vectors.project_vector_to_plane(plane_zone.ZAxis, plane_male)
                            joint_plane = rs.PlaneFromNormal(center, plane_male.ZAxis, default_direction)

                            #force direction for assembly
                            #if assembly is True:
                            if types[j] == 'FS': direction = self.contact_vectors[i][j]
                            if types[j] == 'SF': direction = -self.contact_vectors[i][j]

                            #tenon rotation
                            #else: 
                            #    direction = rs.VectorRotate(default_direction, tenon_angle, joint_plane[3])
                            #    self.contact_vectors[nb] = direction

                            if specific_vector != None: 
                                direction = specific_vector
                            
                            #default length
                            if (tenon_length == 'default') or (tenon_length == 0) :
                                alpha = rs.VectorAngle(direction, plane_female[3])
                                new_tenon_length = abs(thickness_female / math.cos(math.radians(alpha)))
                            else: new_tenon_length = tenon_length
                            
                            #tenon location
                            if tenon_number > 1 :
                                dist = (float(tenon_number-1) /2) * (tenon_width + tenon_space)
                                pointA = rs.CopyObject(joint_plane.Origin, joint_plane.YAxis * dist)
                                pointB = rs.CopyObject(joint_plane.Origin, -joint_plane.YAxis * dist)
                                line = rs.AddLine(pointA, pointB)
                                shifted_line = rs.CopyObject(line, joint_plane.YAxis * tenon_shift)
                                location = rs.DivideCurve(shifted_line, tenon_number-1)
                            else: location = [rs.CopyObject(joint_plane.Origin, joint_plane.YAxis * tenon_shift)]

                            #solid
                            for k in range(len(location)):

                                #tenon box
                                point1 = rs.CopyObject(location[k], joint_plane.YAxis * tenon_width/2)
                                point4 = rs.CopyObject(location[k], -joint_plane.YAxis * tenon_width/2)
                                point2 = rs.CopyObject(point1, direction * new_tenon_length)
                                point3 = rs.CopyObject(point4, direction * new_tenon_length)
                                polyline = rs.AddPolyline([point1, point2, point3, point4, point1])
                                top_point = Toolbox.Curves.curve_closest_point(top_contour_male, joint_plane.Origin)
                                top_poly = rs.CopyObject(polyline, rs.VectorCreate(top_point, joint_plane.Origin))
                                bottom_point = Toolbox.Curves.curve_closest_point(bottom_contour_male, joint_plane.Origin)
                                bottom_poly = rs.CopyObject(polyline, rs.VectorCreate(bottom_point, joint_plane.Origin))
                                tenon_box = rs.coercebrep(Toolbox.Breps.box_from_2_poly(top_poly, bottom_poly))

                                #slice joint if forced assembly
                                if assembly is True: 
                                    top_plane = rs.coerceplane(self.plates[i].top_plane)
                                    bottom_plane =  rs.coerceplane(self.plates[i].bottom_plane)
                                    tenon_box = Toolbox.Breps.slice_2_planes(tenon_box, top_plane, bottom_plane)

                                #append
                                self.plates[male].joints_positives.append(rs.coercebrep(rs.CopyObject(tenon_box)))
                                self.plates[female].joints_negatives.append(rs.coercebrep(rs.CopyObject(tenon_box)))

                            # update contour lines
                            for k in range(len(location)):

                                # male part
                                point1 = rs.CopyObject(location[k], joint_plane.YAxis * (tenon_width/2 + tenon_space/2))
                                point2 = rs.CopyObject(location[k], joint_plane.YAxis * tenon_width/2)
                                point5 = rs.CopyObject(location[k], -joint_plane.YAxis * tenon_width/2)
                                point6 = rs.CopyObject(location[k], -joint_plane.YAxis * (tenon_width/2 + tenon_space/2))
                                point3 = rs.CopyObject(point2, direction * new_tenon_length)
                                point4 = rs.CopyObject(point5, direction * new_tenon_length)
                                polyline = rs.AddPolyline([point1, point2, point3, point4, point5, point6])
                                top_point = Toolbox.Curves.curve_closest_point(top_contour_male, joint_plane.Origin)
                                top_poly = rs.CopyObject(polyline, rs.VectorCreate(top_point, joint_plane.Origin))
                                bottom_point = Toolbox.Curves.curve_closest_point(bottom_contour_male, joint_plane.Origin)
                                bottom_poly = rs.CopyObject(polyline, rs.VectorCreate(bottom_point, joint_plane.Origin))
                                self.plates[male].top_contour = Toolbox.Curves.insert_curves(self.plates[male].top_contour, [top_poly], top_contour_mstart)
                                self.plates[male].bottom_contour = Toolbox.Curves.insert_curves(self.plates[male].bottom_contour, [bottom_poly], bottom_contour_mstart)

                                # female part
                                mod = 0
                                if tenon_space < 0.0001 : mod = -1
                                point1 = rs.PolylineVertices(top_poly)[1 + mod]
                                point2 = rs.PolylineVertices(top_poly)[4 + mod]
                                point3 = rs.PolylineVertices(bottom_poly)[4 + mod]
                                point4 = rs.PolylineVertices(bottom_poly)[1 + mod]
                                point5 = rs.PolylineVertices(top_poly)[2 + mod]
                                point6 = rs.PolylineVertices(top_poly)[3 + mod]
                                point7 = rs.PolylineVertices(bottom_poly)[3 + mod]
                                point8 = rs.PolylineVertices(bottom_poly)[2 + mod]
                                top_poly = rs.AddPolyline([point1, point2, point3, point4, point1])
                                bottom_poly = rs.AddPolyline([point5, point6, point7, point8, point5])
                                self.plates[female].top_holes.append(rs.coercecurve(top_poly))
                                self.plates[female].bottom_holes.append(rs.coercecurve(bottom_poly))                
                            
                            self.log.append('Tenon joint added bewteen plates '+str(i)+ ' and '+ str(nb))

                            pass

            @__skip_nones
            def add_chamfered_tenons(self, 
                plates_pairs='all', 
                tenon_number=2.0, 
                tenon_length='default', 
                tenon_width=10.0, 
                tenon_space=10.0,
                tenon_shift=0.0,
                side_tolerance=0.0,
                top_tolerance=0.0,
                bottom_tolerance=0.0):

                """Add tenon and mortise on Side-to-Face or Face-to-Side contact zones."""

                #cast plate_pairs to string
                if plates_pairs != 'all':
                    for i in range(len(plates_pairs)):
                        plates_pairs[i] = str(plates_pairs[i])
                
                #conditional loop
                for i in range(self.count):
                    types = self.contact_types[i]
                    for j in range(len(types)):
                        nb = self.contact_ids[i][j]

                        #specific selection function
                        if ((plates_pairs == 'all') 
                            or ('('+str(i)+','+str(nb)+')' == plates_pairs) 
                            or ('('+str(i)+','+str(nb)+')' in plates_pairs)
                            or ('('+str(nb)+','+str(i)+')' == plates_pairs) 
                            or ('('+str(nb)+','+str(i)+')' in plates_pairs)): 
                                i_want_a_tenon = True
                        else: i_want_a_tenon = False
                        
                        #for all specified Side-to-Face connection
                        if (types[j] in 'SFS') and (nb > i) and i_want_a_tenon is True:
                            
                            #prerequisite
                            if tenon_number <= 0 : raise Exception('tenon_number must be greater than 0')
                            if tenon_width <= 0 : raise Exception('tenon_width must be greater than 0')

                            #male-female parameters
                            if types[j] == 'SF':
                                male = i
                                female = nb
                                plane_zone = rs.PlaneFromFrame(self.contact_planes[i][j].Origin, self.contact_planes[i][j].XAxis, self.contact_planes[i][j].YAxis)
                            if types[j] == 'FS':
                                male = nb
                                female = i
                                plane_zone = rs.PlaneFromFrame(self.contact_planes[i][j].Origin, self.contact_planes[i][j].YAxis, self.contact_planes[i][j].XAxis)
                            plane_male = self.plates[male].top_plane
                            plane_female = self.plates[female].top_plane
                            thickness_female = self.plates[female].thickness
                            top_contour_male = copy.deepcopy(self.plates[male].top_contour)
                            bottom_contour_male = copy.deepcopy(self.plates[male].bottom_contour)
                            
                            #joint location
                            zone = self.contact_zones[i][j]
                            rectangle = Toolbox.Curves.trapeze_to_rectangle(rs.JoinCurves(rs.DuplicateEdgeCurves(zone)))
                            if Toolbox.Curves.rectangle_dimensions(rectangle)[0] < (tenon_width*tenon_number + tenon_space*(tenon_number) + tenon_shift*2):
                                excess = (tenon_width*tenon_number + tenon_space*(tenon_number) + tenon_shift*2) / (Toolbox.Curves.rectangle_dimensions(rectangle)[0]) * 100
                                raise Exception(' Joint is to large ('+ str(int(excess)) +' %) for contact area between plate '+str(i)+' and plate '+str(nb))
                            center = rs.CurveAreaCentroid(rectangle)[0]
                            default_direction = Toolbox.Vectors.project_vector_to_plane(plane_zone.ZAxis, plane_male)
                            joint_plane = rs.PlaneFromNormal(center, plane_male.ZAxis, default_direction)

                            #direction of assembly
                            if types[j] == 'FS': direction = self.contact_vectors[nb]
                            if types[j] == 'SF': direction = -self.contact_vectors[nb]
                            
                            #default length
                            if (tenon_length == 'default') or (tenon_length == 0) :
                                alpha = rs.VectorAngle(direction, plane_female[3])
                                new_tenon_length = abs(thickness_female / math.cos(math.radians(alpha)))
                            else: new_tenon_length = tenon_length
                            
                            #tenon location
                            if tenon_number > 1 :
                                dist = (float(tenon_number-1) /2) * (tenon_width + tenon_space)
                                pointA = rs.CopyObject(joint_plane.Origin, joint_plane.YAxis * dist)
                                pointB = rs.CopyObject(joint_plane.Origin, -joint_plane.YAxis * dist)
                                line = rs.AddLine(pointA, pointB)
                                shifted_line = rs.CopyObject(line, joint_plane.YAxis * tenon_shift)
                                location = rs.DivideCurve(shifted_line, tenon_number-1)
                            else: location = [rs.CopyObject(joint_plane.Origin, joint_plane.YAxis * tenon_shift)]

                            #solid
                            for k in range(len(location)):

                                #tenon box
                                if side_tolerance >= tenon_width/2 :
                                    raise Exception(' Side chamfer should be reduced for the joint between plate '+str(i)+' and plate '+str(nb))
                                point1 = rs.CopyObject(location[k], joint_plane.YAxis * tenon_width/2)
                                point4 = rs.CopyObject(location[k], -joint_plane.YAxis * tenon_width/2)
                                point2 = rs.CopyObject(point1, (direction * new_tenon_length) + (side_tolerance * -joint_plane.YAxis))
                                point3 = rs.CopyObject(point4, (direction * new_tenon_length) + (side_tolerance * joint_plane.YAxis))
                                polyline = rs.AddPolyline([point1, point2, point3, point4, point1])
                                top_point = Toolbox.Curves.curve_closest_point(top_contour_male, joint_plane.Origin)
                                top_poly = rs.CopyObject(polyline, rs.VectorCreate(top_point, joint_plane.Origin))
                                bottom_point = Toolbox.Curves.curve_closest_point(bottom_contour_male, joint_plane.Origin)
                                bottom_poly = rs.CopyObject(polyline, rs.VectorCreate(bottom_point, joint_plane.Origin))
                                tenon_box = rs.coercebrep(Toolbox.Breps.box_from_2_poly(top_poly, bottom_poly))
                                
                                #slice joint for top and bottom tolerance
                                top_pointa = rs.CopyObject(rs.PolylineVertices(top_poly)[0])
                                bottom_pointa = rs.CopyObject(rs.PolylineVertices(bottom_poly)[0])
                                top_pointb = rs.CopyObject(rs.PolylineVertices(top_poly)[1])
                                bottom_pointb = rs.CopyObject(rs.PolylineVertices(bottom_poly)[1])
                                tb_vector = rs.VectorUnitize(rs.VectorCreate(top_pointb, bottom_pointb))
                                top_pointc = rs.CopyObject(rs.PolylineVertices(top_poly)[1], -top_tolerance*tb_vector)
                                bottom_pointc = rs.CopyObject(rs.PolylineVertices(bottom_poly)[1], bottom_tolerance*tb_vector)
                                top_vector = rs.VectorUnitize(rs.VectorCreate(top_pointc, top_pointa))
                                bottom_vector = rs.VectorUnitize(rs.VectorCreate(bottom_pointc, bottom_pointa))
                                top_chamfer_origin = Toolbox.Curves.curve_closest_point(top_contour_male, joint_plane.Origin)
                                top_chamfer_plane = rs.PlaneFromFrame(top_chamfer_origin, top_vector, joint_plane.YAxis)
                                bottom_chamfer_origin = Toolbox.Curves.curve_closest_point(bottom_contour_male, joint_plane.Origin)
                                bottom_chamfer_plane = rs.PlaneFromFrame(bottom_chamfer_origin, joint_plane.YAxis,bottom_vector )
                                if (bottom_tolerance + top_tolerance) > self.plates[male].thickness:
                                    raise Exception(' Top and/or bottom chamfer should be reduced for the joint between plate '+str(i)+' and plate '+str(nb))
                                tenon_box = Toolbox.Breps.slice_2_planes(tenon_box, top_chamfer_plane, bottom_chamfer_plane)
                                
                                #slice joint if tenon goes out of plate plane
                                top_plane = rs.coerceplane(self.plates[i].top_plane)
                                bottom_plane =  rs.coerceplane(self.plates[i].bottom_plane)
                                tenon_box = Toolbox.Breps.slice_2_planes(tenon_box, top_plane, bottom_plane)
                                
                                #append
                                self.plates[male].joints_positives.append(rs.coercebrep(rs.CopyObject(tenon_box)))
                                self.plates[female].joints_negatives.append(rs.coercebrep(rs.CopyObject(tenon_box)))

                            # update contour lines
                            for k in range(len(location)):

                                # male part
                                mpoint1 = rs.CopyObject(location[k], joint_plane.YAxis * (tenon_width/2 + tenon_space/2))
                                mpoint2 = rs.CopyObject(location[k], joint_plane.YAxis * tenon_width/2)
                                mpoint5 = rs.CopyObject(location[k], -joint_plane.YAxis * tenon_width/2)
                                mpoint6 = rs.CopyObject(location[k], -joint_plane.YAxis * (tenon_width/2 + tenon_space/2))
                                mpoint3 = rs.CopyObject(mpoint2, direction * (new_tenon_length) + (side_tolerance * -joint_plane.YAxis))
                                mpoint4 = rs.CopyObject(mpoint5, direction * (new_tenon_length) + (side_tolerance * joint_plane.YAxis))
                                
                                #projection if tenon goes out of plate plane
                                mpoint3p = Toolbox.Points.project_point_to_plane(mpoint3, self.plates[male].mid_plane, -self.contact_planes[i][j].YAxis)
                                mpoint4p = Toolbox.Points.project_point_to_plane(mpoint4, self.plates[male].mid_plane, -self.contact_planes[i][j].YAxis)

                                #polyline reconstruction
                                top_point = Toolbox.Curves.curve_closest_point(top_contour_male, joint_plane.Origin)
                                bottom_point = Toolbox.Curves.curve_closest_point(bottom_contour_male, joint_plane.Origin)
                                mpolyline = rs.AddPolyline([mpoint1, mpoint2, mpoint3, mpoint4, mpoint5, mpoint6]) #original poly
                                mpolylinep = rs.AddPolyline([mpoint1, mpoint2, mpoint3p, mpoint4p, mpoint5, mpoint6]) #reduced poly
                                mtop_poly = rs.CopyObject(mpolyline, rs.VectorCreate(top_point, joint_plane.Origin))
                                mtop_polyp = rs.CopyObject(mpolylinep, rs.VectorCreate(top_point, joint_plane.Origin))
                                mbottom_poly = rs.CopyObject(mpolyline, rs.VectorCreate(bottom_point, joint_plane.Origin))                            
                                mbottom_polyp = rs.CopyObject(mpolylinep, rs.VectorCreate(bottom_point, joint_plane.Origin))

                                # modifier for null space
                                # if space is null, tenon polyline is made out of 4 points instead of 6 (indices need to change)    
                                mod = 0
                                if tenon_space < 0.0001 : mod = -1

                                #change poly with top and bottom chamfer
                                top_vertices = rs.PolylineVertices(mtop_poly)
                                top_vertices[2+mod] = rs.CopyObject(top_vertices[2+mod], -top_tolerance*tb_vector)
                                top_vertices[3+mod] = rs.CopyObject(top_vertices[3+mod], -top_tolerance*tb_vector)
                                mtop_poly = rs.AddPolyline(top_vertices)
                                bottom_vertices = rs.PolylineVertices(mbottom_poly)
                                bottom_vertices[2+mod] = rs.CopyObject(bottom_vertices[2+mod], bottom_tolerance*tb_vector)
                                bottom_vertices[3+mod] = rs.CopyObject(bottom_vertices[3+mod], bottom_tolerance*tb_vector)
                                mbottom_poly = rs.AddPolyline(bottom_vertices)

                                #append
                                self.plates[male].top_contour = Toolbox.Curves.insert_curves(self.plates[male].top_contour, [mtop_polyp])
                                self.plates[male].bottom_contour = Toolbox.Curves.insert_curves(self.plates[male].bottom_contour, [mbottom_polyp])
                                
                                # female part
                                fpoint1 = rs.PolylineVertices(mtop_polyp)[1 + mod]
                                fpoint2 = rs.PolylineVertices(mtop_polyp)[4 + mod]
                                fpoint3 = rs.PolylineVertices(mbottom_polyp)[4 + mod]
                                fpoint4 = rs.PolylineVertices(mbottom_polyp)[1 + mod]
                                midpointtest = Toolbox.Points.average_point([rs.PolylineVertices(mtop_poly)[2 + mod], rs.PolylineVertices(mbottom_poly)[2 + mod]])
                                d1 = rs.Distance(midpointtest, rs.PolylineVertices(mbottom_polyp)[2 + mod])
                                d2 = rs.Distance(midpointtest, rs.PolylineVertices(mtop_polyp)[2 + mod])
                                if d1 < d2 : #checking which points to use for reduced holes
                                    fpoint5 = rs.PolylineVertices(mtop_poly)[2 + mod]
                                    fpoint6 = rs.PolylineVertices(mtop_poly)[3 + mod]
                                    fpoint7 = rs.PolylineVertices(mbottom_polyp)[3 + mod]
                                    fpoint8 = rs.PolylineVertices(mbottom_polyp)[2 + mod]
                                else:
                                    fpoint5 = rs.PolylineVertices(mtop_polyp)[2 + mod]
                                    fpoint6 = rs.PolylineVertices(mtop_polyp)[3 + mod]
                                    fpoint7 = rs.PolylineVertices(mbottom_poly)[3 + mod]
                                    fpoint8 = rs.PolylineVertices(mbottom_poly)[2 + mod]
                                ftop_poly = rs.AddPolyline([fpoint1, fpoint2, fpoint3, fpoint4, fpoint1])
                                fbottom_poly = rs.AddPolyline([fpoint5, fpoint6, fpoint7, fpoint8, fpoint5])
                                self.plates[female].top_holes.append(rs.coercecurve(ftop_poly))
                                self.plates[female].bottom_holes.append(rs.coercecurve(fbottom_poly))                

                                #holes lines for chamfer on tenon due to out of plane
                                if round(d1,6) != round(d2,6) :
                                    if d1 < d2 :
                                        cpoly = mtop_poly
                                        cplane = self.plates[male].top_plane
                                    else : 
                                        cpoly = mbottom_poly
                                        cplane = self.plates[male].bottom_plane
                                    cpoint1 = rs.PolylineVertices(cpoly)[1 + mod]
                                    cpoint2 = rs.PolylineVertices(cpoly)[2 + mod]
                                    cpoint3 = rs.PolylineVertices(cpoly)[3 + mod]
                                    cpoint4 = rs.PolylineVertices(cpoly)[4 + mod]     
                                    cpoly_down = rs.AddPolyline([cpoint1, cpoint2, cpoint3, cpoint4, cpoint1])
                                    vec = rs.VectorRotate(direction, -90, joint_plane.YAxis)
                                    vecp = rs.VectorCreate(Toolbox.Points.project_point_to_plane(cpoint2, cplane, vec), cpoint2)
                                    cpoly_up = rs.CopyObject(cpoly_down, vecp)
                                    self.plates[male].top_holes.append(rs.coercecurve(cpoly_up))
                                    self.plates[male].bottom_holes.append(rs.coercecurve(cpoly_down))

                                """
                                #holes lines for chamfer on tenon due to out of plane
                                if top_tolerance > 0: 
                                    point1 = 
                                    point2 = 
                                    point3 = rs.PlaneClosestPoint(top_chamfer_plane, )
                                    point4 = rs.PlaneClosestPoint(top_chamfer_plane, )
                                """
                            self.log.append('Tenon joint added bewteen plates '+str(i)+ ' and '+ str(nb))

                            pass

          
            @__skip_nones                   
            def add_sunrise(self,
                plates_pairs='all', 
                tenon_number=2, 
                tenon_width=1.0,
                tenon_space=1.0,
                spread_angle=0.0,
                custom_insertion=None,
                flip=True):
                """ Add a sunrise dovetail on Edgewise contact zones."""
                
                #builder functions
                
                def create_joint_curves(origin, x, y, z, phi_offset, width, l, thickness, spacing, angle, n, vi):
                    ######## Creation of the construction parameters ########
                    lj = n * (width + spacing) - spacing  # Length of the joint
                    ys_k = Basics.get_yks(vi, y, angle, n)  # y vector of each finger plate to orient the plane
                    
                    # projection of the x axis on the yk, vi plane with respect to the y axis
                    xs_k = tuple([Basics.project(yk, vi, x, y) for yk in ys_k])
                    # Unitize the vector along the x direction
                    xs_k = tuple([tuple([comp / Basics.dot(xk, x) for comp in xk]) for xk in xs_k])
                    
                    # projection of the z axis on the yk, vi plane with respect to the y axis
                    zs_k = tuple([Basics.project(yk, vi, z, y) for yk in ys_k])
                    # Unitize the vector along the y direction
                    zs_k = tuple([tuple([comp / Basics.dot(zk, z) for comp in zk]) for zk in zs_k])

                    ######## Construction of the points of the joint ########
                    # Start points of the fingers at the center of the joint
                    pts_top_4k = [tuple([oi + ((width + spacing) * k - 0.5 * lj) * yi + 0.5 * thickness * zi - .5 * phi_offset * x_i
                                        for yi, oi, zi, x_i in zip(y, origin, z, x)])
                                for k in range(n)]

                    # Top curve points creation from middle start points
                    # pts_top_4k = [tuple([pti + thickness * (z_ki - 0.5 * zi) for pti, z_ki, zi in zip(pt, z_k, z)])
                    #              for pt, z_k in zip(pts_mid_4k, zs_k)]
                    pts_top_4k1 = [tuple([pti + l * x_ki for pti, x_ki in zip(pt, x_k)])
                                for pt, x_k in zip(pts_top_4k, xs_k)]
                    pts_top_4k2 = [tuple([pti + width * yi for pti, yi in zip(pt, y)])
                                for pt in pts_top_4k1]
                    pts_top_4k3 = [tuple([pti + width * yi for pti, yi in zip(pt, y)])
                                for pt in pts_top_4k]
                    # Merging lists of points correctly
                    pts_top = tuple(zip(pts_top_4k, pts_top_4k1, pts_top_4k2, pts_top_4k3))

                    # Create bottom curve by translating the top curve
                    pts_bottom = [[pti + 1 * phi_offset * x_ki - thickness * z_ki for pti, z_ki, x_ki in zip(pt, zs_k[i], xs_k[i])]
                                for i, pts in enumerate(pts_top) for pt in pts]

                    # Moving top curve to center origin on the joint
                    pts_top = [[pti - .0 * phi_offset * x_ki for pti, x_ki in zip(pt, xs_k[i])]
                            for i, pts in enumerate(pts_top) for pt in pts]

                    return (pts_bottom,
                            pts_top,[rg.Point3d(*point) for point in pts_top_4k])

                def create_plate1_curve(plane, top_curve, bottom_curve, w, l, o, phi_offset, t):
                    # Get plate axis
                    x, y, z = plane.XAxis, plane.YAxis, plane.ZAxis

                    # Center of the joint on the top edge
                    top_center = tuple([o_i - x_i * .5 * phi_offset + .5 * t * z_i for o_i, x_i, z_i in zip(o, x, z)])

                    # Add plates points
                    top_curve.append([pt_i + y_i * .5 * w for pt_i, y_i in zip(top_center, y)])
                    top_curve.append([pt_i - x_i * l for pt_i, x_i in zip(top_curve[-1], x)])
                    top_curve.append([pt_i - y_i * w for pt_i, y_i in zip(top_curve[-1], y)])
                    top_curve.append([pt_i + x_i * l for pt_i, x_i in zip(top_curve[-1], x)])
                    top_curve.append(top_curve[0])

                    # Center of the joint on the bottom edge
                    bottom_center = tuple([o_i + x_i * .5 * phi_offset - .5 * t * z_i for o_i, x_i, z_i in zip(o, x, z)])

                    # Add plates points
                    bottom_curve.append([pt_i + y_i * .5 * w for pt_i, y_i in zip(bottom_center, y)])
                    bottom_curve.append([pt_i - x_i * (l + phi_offset) for pt_i, x_i in zip(bottom_curve[-1], x)])
                    bottom_curve.append([pt_i - y_i * w for pt_i, y_i in zip(bottom_curve[-1], y)])
                    bottom_curve.append([pt_i + x_i * (l + phi_offset) for pt_i, x_i in zip(bottom_curve[-1], x)])
                    bottom_curve.append(bottom_curve[0])

                    # Return curves as PolylineCurve
                    return (rg.PolylineCurve([rg.Point3d(*pt) for pt in bottom_curve]),
                            rg.PolylineCurve([rg.Point3d(*pt) for pt in top_curve]),)

                def create_plate2_curve(plate1, plate2, top_curve, bottom_curve, width, lenght, thickness, origin, phi_offset, phi,
                                        finger_length):
                    # Get plates axes
                    x1, y1, z1 = plate1.XAxis, plate1.YAxis, plate1.ZAxis
                    x2, y2, z2 = plate2.XAxis, plate2.YAxis, plate2.ZAxis

                    # Center of the joint on top
                    top_center = tuple(
                        [o_i - .5 * phi_offset * x_i + .5 * thickness * z_i for o_i, x_i, z_i in zip(origin, x1, z1)])

                    # Center of the joint on top and dl the offset to create perpendicular edge to the plate
                    if phi not in [0, pi, 2. * pi]:
                        bottom_center = tuple([o_i + finger_length * x_i for o_i, x_i in zip(top_center, x1)])
                        dl = finger_length * cos(pi - phi)
                    else:  # Specific cases for aligned plates
                        bottom_center = tuple([o_i - thickness * z_i for o_i, z_i in zip(top_center, z1)])
                        dl = 0

                    # Add plates points
                    top_curve.append([pt_i - y_i * .5 * width for pt_i, y_i in zip(top_center, y2)])
                    top_curve.append([pt_i - x_i * (lenght + dl) for pt_i, x_i in zip(top_curve[-1], x2)])
                    top_curve.append([pt_i + y_i * width for pt_i, y_i in zip(top_curve[-1], y2)])
                    top_curve.append([pt_i + x_i * (lenght + dl) for pt_i, x_i in zip(top_curve[-1], x2)])
                    top_curve.append(top_curve[0])

                    # Add plates points
                    bottom_curve.append([pt_i - y_i * .5 * width for pt_i, y_i in zip(bottom_center, y2)])
                    bottom_curve.append([pt_i - x_i * (lenght) for pt_i, x_i in zip(bottom_curve[-1], x2)])
                    bottom_curve.append([pt_i + y_i * width for pt_i, y_i in zip(bottom_curve[-1], y2)])
                    bottom_curve.append([pt_i + x_i * (lenght) for pt_i, x_i in zip(bottom_curve[-1], x2)])
                    bottom_curve.append(bottom_curve[0])

                    return (rg.PolylineCurve([rg.Point3d(*pt) for pt in bottom_curve]),
                            rg.PolylineCurve([rg.Point3d(*pt) for pt in top_curve]),)

                def create_plate_brep(crv_top, crv_bottom):
                    # Convert curves to Polyline in order to get its points
                    top_pts = crv_top.ToPolyline()
                    bottom_pts = crv_bottom.ToPolyline()

                    # List of faces of the brep
                    faces = []

                    # Create side faces
                    for i in range(len(top_pts) - 1):
                        # Side faces points
                        _ = rg.PolylineCurve((top_pts[i], bottom_pts[i], bottom_pts[i + 1], top_pts[i + 1], top_pts[i]))
                        # Face creations
                        faces += rg.Brep.CreatePlanarBreps(_, 1e-3)

                    # Add top and bottom faces
                    faces += rg.Brep.CreatePlanarBreps(rg.PolylineCurve(bottom_pts), 1e-3)
                    faces += rg.Brep.CreatePlanarBreps(rg.PolylineCurve(top_pts), 1e-3)

                    return rg.Brep.CreateSolid(faces, 1e-3)

                #cast plate_pairs to string
                if plates_pairs != 'all':
                    for i in range(len(plates_pairs)):
                        plates_pairs[i] = str(plates_pairs[i])
                
                spread_angle = (spread_angle/360)*2*math.pi

                #conditional loop
                for i in range(self.count):
                    types = self.contact_types[i]
                    for j in range(len(types)):
                        nb = self.contact_ids[i][j]

                        # Specific selection function
                        if ((plates_pairs == 'all') 
                            or ('('+str(i)+','+str(nb)+')' == plates_pairs) 
                            or ('('+str(i)+','+str(nb)+')' in plates_pairs)
                            or ('('+str(nb)+','+str(i)+')' == plates_pairs) 
                            or ('('+str(nb)+','+str(i)+')' in plates_pairs)): 
                                i_want_a_tenon = True
                        else: i_want_a_tenon = False

                        # For all specified Edgewise connection
                        if (types[j] in 'SES') and (nb > i) and i_want_a_tenon is True:
                            
                            # Prerequisite
                            if tenon_number < 2 : raise Exception('tenon_number must be greater than 1')
                            if tenon_width <= 0 : raise Exception('tenon_width must be greater than 0')
                            if tenon_space <= 0 : raise Exception('tenon_space must be greater than 0')

                            # Male-female parameters
                            if types[j] == 'SE':
                                male = i
                                female = nb
                            if types[j] == 'ES':
                                male = nb
                                female = i
                            plane_male = self.plates[male].top_plane
                            plane_female = self.plates[female].top_plane
                            thickness_male = self.plates[male].thickness
                            thickness_female = self.plates[female].thickness
                            
                            # Joint location
                            zone = self.contact_zones[i][j]
                            center = self.contact_centers[i][j]
                            cp = self.contact_planes[i][j]

                            # Construction planes
                            z2=cp.ZAxis
                            x2 = cp.YAxis
                            testx2 = rs.CopyObject(center, 2*self.plates[female].thickness * rs.VectorUnitize(x2))
                            if rg.Brep.IsPointInside(self.plates[female].brep, rs.coerce3dpoint(testx2), 0.1, False): 
                                x2 = -x2
                            y2 = rs.VectorCrossProduct(z2,x2)
                            y1 = -y2
                            z1 = plane_male.ZAxis
                            x1 = rs.VectorCrossProduct(y1,z1)
                            testx1 = rs.CopyObject(center, 2*self.plates[female].thickness * rs.VectorUnitize(x1))
                            if rg.Brep.IsPointInside(self.plates[male].brep, rs.coerce3dpoint(testx1), 0.1, False): 
                                x1 = -x1
                                z1 = -z1
                            p1 = rs.PlaneFromFrame(center, x1,-y1)
                            p2 = rs.PlaneFromFrame(center, x2,-y2)

                            # insertion vector
                            vi = self.contact_vectors[i][j]
                            if custom_insertion != None: vi = custom_insertion
                            
                            # Alex parameters
                            l = thickness_female
                            x, y, z = (tuple(p1.XAxis), tuple(p1.YAxis), tuple(p1.ZAxis))
                            o = center  # Center of the joint
                            vi = Basics.unitize(tuple(vi))  # Ensure vi is unit length
                            phi = Basics.angle(x, tuple(p2.XAxis), z)  # Angle between the two plates
                            phi_lim = 0  # Limit to avoid near 0 angle problem

                            # Offset in x direction due to angle in contact face
                            pi = math.pi
                            if phi_lim < phi < pi - phi_lim:
                                if phi <= .5 * pi:
                                    phi_offset = -(thickness_male ** 2. * (math.sin(phi) ** -2. - 1)) ** .5
                                else:
                                    phi_offset = (thickness_male ** 2. * (math.sin(phi) ** -2. - 1)) ** .5
                                l = thickness_female / math.sin(phi)
                            else:
                                l = thickness_female
                                phi_offset = 0.

                            # Joint contour
                            pts_bottom, pts_top, m = create_joint_curves(o, x, y, z, phi_offset, tenon_width, l, thickness_male, tenon_space, spread_angle, tenon_number, vi)
                            if phi_lim < phi < pi - phi_lim:
                                pts_bottom_flip, pts_top_flip = Basics.flip_crv(pts_top, pts_bottom)
                            else:
                                pts_bottom_flip, pts_top_flip = list(pts_bottom), list(pts_top) 
                            
                            # flip top and bottom polylines if necessary
                            if rs.CurveCurveIntersection(self.plates[male].top_contour, rs.AddPolyline(pts_top),0.1) == None:
                                pts_top, pts_bottom = pts_bottom, pts_top
                            if rs.CurveCurveIntersection(self.plates[female].top_contour, rs.AddPolyline(pts_top_flip),0.1) == None:
                                pts_top_flip, pts_bottom_flip = pts_bottom_flip, pts_top_flip

                            # insert top and bottom polyines inside male and female contours
                            self.plates[male].top_contour = Toolbox.Curves.insert_curves(self.plates[male].top_contour, [rs.AddPolyline(pts_top)])
                            self.plates[male].bottom_contour = Toolbox.Curves.insert_curves(self.plates[male].bottom_contour, [rs.AddPolyline(pts_bottom)])
                            self.plates[female].top_contour = Toolbox.Curves.insert_curves(self.plates[female].top_contour, [rs.AddPolyline(pts_top_flip)])
                            self.plates[female].bottom_contour = Toolbox.Curves.insert_curves(self.plates[female].bottom_contour, [rs.AddPolyline(pts_bottom_flip)])

                            #joint solid
                            
                            for k in range(tenon_number):
                                box = Toolbox.Breps.box_from_2_poly(rs.AddPolyline(pts_top[4*k:4*k+4]), rs.AddPolyline(pts_bottom[4*k:4*k+4]))
                                self.plates[male].joints_positives.append(rs.coercebrep(box))
                                self.plates[female].joints_negatives.append(rs.coercebrep(box))
                            

            @__skip_nones
            def add_custom_FS_joints(self, 
                plates_pairs='all', 
                joint_number=2.0, 
                joint_width=10.0, 
                joint_space=10.0,
                joint_shift=0.0,
                joint_drawing=None,
                hole_sides=[],
                flip_1=False,
                flip_2=False):

                """Add Custom joint based on drawn polyline on Side-to-Face or Face-to-Side contact zones."""

                # Tile scale
                if joint_drawing is None : raise Exception('Please first provide a drawing for the joint')
                tile_start = rs.CurveStartPoint(joint_drawing)
                tile_end = rs.CurveEndPoint(joint_drawing)
                tile_mid = Toolbox.Points.average_point([tile_end, tile_start])
                tile_width = rs.Distance(tile_end, tile_start)
                tile_scale = joint_width/tile_width
                tile = rs.ScaleObject(joint_drawing, tile_mid, (tile_scale, tile_scale, tile_scale), True)
                if len(hole_sides) == 2 :
                    for i in range(len(hole_sides)):
                        hole_sides[i] = rs.ScaleObject(hole_sides[i], tile_mid, (tile_scale, tile_scale, tile_scale), True)

                # Tile plane
                tile_normal = rs.CurvePlane(tile).ZAxis
                if tile_normal[2] < 0 : 
                    tile_normal = rs.VectorReverse(tile_normal)
                tile_y = rs.VectorCreate(tile_end, tile_start)
                tile_x = rs.VectorCrossProduct(tile_normal, tile_y)
                tile_plane = rs.PlaneFromFrame(tile_mid, tile_x, tile_y)
                tile_zones = Toolbox.Curves.polyline_half_zones(tile)
                tile_positives = tile_zones[0]
                tile_negatives = tile_zones[1]

                # Tile flip
                if flip_1 is True: 
                    tile_plane = rs.RotatePlane(tile_plane, 180, tile_x)
                if flip_2 is True: 
                    tile_plane = rs.RotatePlane(tile_plane, 180, tile_y)
                    tile_positives = tile_zones[1]
                    tile_negatives = tile_zones[0]

                # Cast plate_pairs to string
                if plates_pairs != 'all':
                    for i in range(len(plates_pairs)):
                        plates_pairs[i] = str(plates_pairs[i])
                
                # Conditional loop for joint generation
                for i in range(self.count):
                    types = self.contact_types[i]
                    for j in range(len(types)):
                        nb = self.contact_ids[i][j]

                        # Specific selection function
                        if ((plates_pairs == 'all') 
                            or ('('+str(i)+','+str(nb)+')' == plates_pairs) 
                            or ('('+str(i)+','+str(nb)+')' in plates_pairs)): 
                                i_want_a_joint = True
                        else: i_want_a_joint = False
                        
                        # For all specified Side-to-Face connection
                        if (types[j] in 'SFS') and (nb > i) and i_want_a_joint is True:
                            
                            # Prerequisite
                            if joint_number <= 0 : raise Exception('joint_number must be greater than 0')
                            if joint_width <= 0 : raise Exception('joint_width must be greater than 0')

                            # Male-female parameters
                            if types[j] == 'SF':
                                male = i
                                female = nb
                                plane_zone = rs.PlaneFromFrame(self.contact_planes[i][j].Origin, self.contact_planes[i][j].XAxis, self.contact_planes[i][j].YAxis)
                            if types[j] == 'FS':
                                male = nb
                                female = i
                                plane_zone = rs.PlaneFromFrame(self.contact_planes[i][j].Origin, self.contact_planes[i][j].YAxis, self.contact_planes[i][j].XAxis)
                            plane_male = self.plates[male].top_plane
                            plane_female = self.plates[female].top_plane
                            thickness_female = self.plates[female].thickness
                            top_contour_male = self.plates[male].top_contour
                            bottom_contour_male = self.plates[male].bottom_contour
                            
                            # Joint location
                            zone = self.contact_zones[i][j]
                            rectangle = Toolbox.Curves.trapeze_to_rectangle(rs.JoinCurves(rs.DuplicateEdgeCurves(zone)))
                            if Toolbox.Curves.rectangle_dimensions(rectangle)[0] < (joint_width*joint_number + joint_space*(joint_number) + joint_shift*2):
                                excess = (joint_width*joint_number + joint_space*(joint_number) + joint_shift*2) / (Toolbox.Curves.rectangle_dimensions(rectangle)[0]) * 100
                                raise Exception(' Joint is to large ('+ str(int(excess)) +' %) for contact area between plate '+str(i)+' and plate '+str(nb))
                            center = rs.CurveAreaCentroid(rectangle)[0]
                            default_direction = Toolbox.Vectors.project_vector_to_plane(plane_zone.ZAxis, plane_male)
                            joint_plane = rs.PlaneFromNormal(center, plane_male.ZAxis, default_direction)
                            if joint_number > 1 :
                                dist = (float(joint_number-1) /2) * (joint_width + joint_space)
                                pointA = rs.CopyObject(joint_plane.Origin, joint_plane.YAxis * dist)
                                pointB = rs.CopyObject(joint_plane.Origin, -joint_plane.YAxis * dist)
                                line = rs.AddLine(pointA, pointB)
                                shifted_line = rs.CopyObject(line, joint_plane.YAxis * joint_shift)
                                location = rs.DivideCurve(shifted_line, joint_number-1)
                            else: location = [rs.CopyObject(joint_plane.Origin, joint_plane.YAxis * joint_shift)]
                            
                            # Solid
                            for k in range(len(location)):

                                # Get transformation matrix for top and bottom poly (male)
                                top_point = Toolbox.Curves.curve_closest_point(top_contour_male, joint_plane.Origin)
                                bottom_point = Toolbox.Curves.curve_closest_point(bottom_contour_male, joint_plane.Origin)
                                top_loc = rs.CopyObject(location[k], rs.VectorCreate(top_point, joint_plane.Origin))
                                bottom_loc = rs.CopyObject(location[k], rs.VectorCreate(bottom_point, joint_plane.Origin))
                                top_target_plane = rs.PlaneFromFrame(top_loc, joint_plane.XAxis, joint_plane.YAxis)
                                bottom_target_plane = rs.PlaneFromFrame(bottom_loc, joint_plane.XAxis, joint_plane.YAxis)
                                top_matrix = rg.Transform.PlaneToPlane(tile_plane, top_target_plane)
                                bottom_matrix = rg.Transform.PlaneToPlane(tile_plane, bottom_target_plane)

                                # Orient joint positives and negatives on male plate
                                if len(tile_positives) != 0:
                                    for l in range(len(tile_positives)):
                                        top_poly = rs.coercegeometry(rs.TransformObject(tile_positives[l], top_matrix, True))
                                        bottom_poly = rs.coercegeometry(rs.TransformObject(tile_positives[l], bottom_matrix, True))
                                        brep = Toolbox.Breps.brep_from_2_poly(top_poly, bottom_poly)
                                        self.plates[male].joints_positives.append(brep)
                                if len(tile_negatives) != 0:
                                    for l in range(len(tile_negatives)):
                                        top_poly = rs.coercegeometry(rs.TransformObject(tile_negatives[l], top_matrix, True))
                                        bottom_poly = rs.coercegeometry(rs.TransformObject(tile_negatives[l], bottom_matrix, True))
                                        brep = Toolbox.Breps.brep_from_2_poly(top_poly, bottom_poly)
                                        self.plates[male].joints_negatives.append(brep)
                                
                                # Insert tile in male contour
                                top_poly = rs.coercegeometry(rs.TransformObject(tile, top_matrix, True))
                                bottom_poly = rs.coercegeometry(rs.TransformObject(tile, bottom_matrix, True))
                                self.plates[male].top_contour = Toolbox.Curves.insert_curves(self.plates[male].top_contour, [top_poly])
                                self.plates[male].bottom_contour = Toolbox.Curves.insert_curves(self.plates[male].bottom_contour, [bottom_poly])

                                # Orient female part
                                if len(hole_sides) == 2:
                                    link_1 = rs.AddLine(rs.CurveStartPoint(hole_sides[0]), rs.CurveStartPoint(hole_sides[1]))
                                    link_2 = rs.AddLine(rs.CurveEndPoint(hole_sides[0]), rs.CurveEndPoint(hole_sides[1]))
                                    female_tile = rs.JoinCurves(hole_sides + [link_1, link_2])[0]
                                    top_poly = rs.coercegeometry(rs.TransformObject(female_tile, top_matrix, True))
                                    bottom_poly = rs.coercegeometry(rs.TransformObject(female_tile, bottom_matrix, True))
                                    brep = Toolbox.Breps.brep_from_2_poly(top_poly, bottom_poly)
                                    self.plates[female].joints_negatives.append(brep)

                                    # Get holes from female drawing
                                    vertices_1 = rs.PolylineVertices(hole_sides[0])
                                    vertices_2 = rs.PolylineVertices(hole_sides[1])
                                    if len(vertices_1) == len(vertices_2):
                                        for l in range(len(vertices_1)-1):
                                            line_1 = rs.AddLine(vertices_1[l], vertices_2[l])
                                            line_2 = rs.AddLine(vertices_1[l+1], vertices_2[l+1])
                                            top_line_1 = rs.coercegeometry(rs.TransformObject(line_1, top_matrix, True))
                                            bottom_line_1 = rs.coercegeometry(rs.TransformObject(line_1, bottom_matrix, True))
                                            top_line_2 = rs.coercegeometry(rs.TransformObject(line_2, top_matrix, True))
                                            bottom_line_2 = rs.coercegeometry(rs.TransformObject(line_2, bottom_matrix, True))
                                            link = rs.AddLine(rs.CurveStartPoint(top_line_1), rs.CurveStartPoint(bottom_line_1))
                                            pol_1 = rs.AddPolyline([rs.CurveStartPoint(top_line_1), rs.CurveEndPoint(top_line_1), rs.CurveEndPoint(bottom_line_1), rs.CurveStartPoint(bottom_line_1), rs.CurveStartPoint(top_line_1)])
                                            pol_2 = rs.AddPolyline([rs.CurveStartPoint(top_line_2), rs.CurveEndPoint(top_line_2), rs.CurveEndPoint(bottom_line_2), rs.CurveStartPoint(bottom_line_2), rs.CurveStartPoint(top_line_2)])
                                            # discard holes contour which are co-planar
                                            if Toolbox.Planes.is_plane_in_plane(rs.CurvePlane(pol_1), rs.CurvePlane(pol_2)) == False:
                                                # check the closest between top and bottom faces
                                                d1 = rs.Distance(rs.CurvePlane(pol_1).Origin, self.plates[female].top_center)
                                                d2 = rs.Distance(rs.CurvePlane(pol_2).Origin, self.plates[female].top_center)
                                                if d1 < d2:
                                                    self.plates[female].top_holes.append(rs.coercecurve(pol_1))
                                                    self.plates[female].bottom_holes.append(rs.coercecurve(pol_2))
                                                else:
                                                    self.plates[female].top_holes.append(rs.coercecurve(pol_2))
                                                    self.plates[female].bottom_holes.append(rs.coercecurve(pol_1))
                                    else: raise Exception('holes_sides should have the same number of vertices')

                            self.log.append('Custom joint added bewteen plates '+str(i)+ ' and '+ str(nb))

                            pass

            @__skip_nones
            def add_fingers(self, 
                plates_pairs='all',
                finger_number_1=2.0,
                finger_length_1='default',
                finger_width_1=1.0,
                finger_number_2=2.0,
                finger_length_2='default',
                finger_width_2=1.0,
                finger_spacing=0.0,
                finger_shift=0.0,
                mirror=False):

                """Add finger joints on Side-to-Side contact zones."""

                #cast plate_pairs to string
                if plates_pairs != 'all':
                    for i in range(len(plates_pairs)):
                        plates_pairs[i] = str(plates_pairs[i])
                
                #conditional loop
                for i in range(self.count):
                    types = self.contact_types[i]
                    for j in range(len(types)):
                        nb = self.contact_ids[i][j]

                        #specific selection function
                        if ((plates_pairs == 'all') 
                            or ('('+str(i)+','+str(nb)+')' == plates_pairs) 
                            or ('('+str(i)+','+str(nb)+')' in plates_pairs)): 
                                i_want_a_finger = True
                        else: i_want_a_finger = False
                        
                        #for all specified Side-to-Side connection
                        if (types[j] == 'SS') and (nb > i) and (i_want_a_finger is True):

                            #prerequisite
                            if finger_length_1 < 0 : raise Exception('finger_length_1 must be greater than 0')
                            if finger_length_2 < 0 : raise Exception('finger_length_2 must be greater than 0')

                            #joint location
                            zone = self.contact_zones[i][j]
                            rectangle = Toolbox.Curves.trapeze_to_rectangle(rs.JoinCurves(rs.DuplicateEdgeCurves(zone)))
                            if Toolbox.Curves.rectangle_dimensions(rectangle)[0] < (finger_width_1*finger_number_1 + finger_width_2*finger_number_2 + finger_spacing*(finger_number_1+finger_number_2) + finger_shift*2):
                                excess = (finger_width_1*finger_number_1 + finger_width_2*finger_number_2 + finger_spacing*(finger_number_1+finger_number_2) + finger_shift*2) / (Toolbox.Curves.rectangle_dimensions(rectangle)[0]) * 100
                                raise Exception(' Joint is to large ('+ str(int(excess)) +' %) for contact area between plate '+str(i)+' and plate '+str(nb))
                            plane_male = self.plates[i].top_plane
                            plane_female = self.plates[nb].top_plane
                            center = self.contact_centers[i][j]
                            joint_plane = rs.PlaneFromNormal(center, self.contact_planes[i][j].YAxis, self.contact_planes[i][j].XAxis)
                            
                            #default length 1
                            if (finger_length_1 == 'default') or (finger_length_1 == 0) :
                                if abs(rs.IsVectorParallelTo(plane_male.ZAxis, plane_female.ZAxis)) == 0 and rs.IsVectorPerpendicularTo(plane_male.ZAxis, plane_female.ZAxis) is False:
                                        alpha = rs.VectorAngle(plane_male.ZAxis, plane_female.ZAxis)
                                        thickness_female = self.plates[nb].thickness
                                        new_finger_length_1 = abs(thickness_female / math.sin(math.radians(180-alpha)))
                                else: new_finger_length_1 = self.plates[nb].thickness
                            else: new_finger_length_1 = finger_length_1

                            #default length 2
                            if (finger_length_2 == 'default') or (finger_length_2 == 0) :
                                if abs(rs.IsVectorParallelTo(plane_male.ZAxis, plane_female.ZAxis)) == 0 and rs.IsVectorPerpendicularTo(plane_male.ZAxis, plane_female.ZAxis) is False:
                                        alpha = rs.VectorAngle(plane_male.ZAxis, plane_female.ZAxis)
                                        thickness_male = self.plates[i].thickness
                                        new_finger_length_2 = abs(thickness_male / math.sin(math.radians(180-alpha)))
                                else: new_finger_length_2 = self.plates[i].thickness
                            else: new_finger_length_2 = finger_length_2

                            #correct length projection
                            if abs(rs.IsVectorParallelTo(plane_male.ZAxis, joint_plane.ZAxis)) == 0:
                                beta = rs.VectorAngle(plane_male.ZAxis, joint_plane.ZAxis)
                                new_finger_length_1 = new_finger_length_1 * abs(math.cos(math.radians(beta)))
                            if abs(rs.IsVectorParallelTo(plane_female.ZAxis, joint_plane.ZAxis)) == 0:
                                beta = rs.VectorAngle(plane_female.ZAxis, joint_plane.ZAxis)
                                new_finger_length_2 = new_finger_length_2*abs(math.cos(math.radians(beta)))
                            
                            #configuration (alternate or centered)
                            if (finger_number_1 + finger_number_2) % 2 == 0:
                                #alternate
                                if mirror is False:
                                    center_1 = rs.CopyObject(joint_plane.Origin, joint_plane.XAxis * (finger_spacing/2 + finger_width_2) /2)
                                    center_2 = rs.CopyObject(joint_plane.Origin, -joint_plane.XAxis * (finger_spacing/2 + finger_width_1) /2)
                                else: 
                                    center_1 = rs.CopyObject(joint_plane.Origin, -joint_plane.XAxis * (finger_spacing/2 + finger_width_2) /2)
                                    center_2 = rs.CopyObject(joint_plane.Origin, joint_plane.XAxis * (finger_spacing/2 + finger_width_1) /2)
                            else: 
                                #centered
                                center_1 = joint_plane.Origin
                                center_2 = joint_plane.Origin
                            
                            #finger location - first side
                            if finger_number_1 > 1 :
                                dist = (float(finger_number_1 -1) /2) * (finger_width_1 + finger_width_2 + finger_spacing)
                                pointA = rs.CopyObject(center_1, joint_plane.XAxis * dist)
                                pointB = rs.CopyObject(center_1, -joint_plane.XAxis * dist)
                                line = rs.AddLine(pointA, pointB)
                                shifted_line = rs.CopyObject(line, joint_plane.XAxis * finger_shift)
                                location_1 = rs.DivideCurve(shifted_line, finger_number_1 -1)
                            else: location_1 = [rs.CopyObject(center_1, joint_plane.XAxis * finger_shift)]
                            
                            #finger location - second side
                            if finger_number_2 > 1 :
                                dist = (float(finger_number_2 -1) /2) * (finger_width_1 + finger_width_2 + finger_spacing)
                                pointA = rs.CopyObject(center_2, joint_plane.XAxis * dist)
                                pointB = rs.CopyObject(center_2, -joint_plane.XAxis * dist)
                                line = rs.AddLine(pointA, pointB)
                                shifted_line = rs.CopyObject(line, joint_plane.XAxis * finger_shift)
                                location_2 = rs.DivideCurve(shifted_line, finger_number_2 -1)
                            else: location_2 = [rs.CopyObject(center_2, joint_plane.XAxis * finger_shift)]

                            #solid - first side
                            for k in range(len(location_2)):
                                #base polyline
                                point1 = rs.coerce3dpoint(rs.CopyObject(location_2[k], joint_plane.XAxis * finger_width_2/2))
                                point4 = rs.coerce3dpoint(rs.CopyObject(location_2[k], -joint_plane.XAxis * finger_width_2/2))
                                point2 = rs.coerce3dpoint(rs.CopyObject(point1, joint_plane.YAxis * new_finger_length_2))
                                point3 = rs.coerce3dpoint(rs.CopyObject(point4, joint_plane.YAxis  * new_finger_length_2))
                                polyline = [point1, point2, point3, point4, point1]

                                #projection for joint negative
                                proj_top_n = rg.Polyline(copy.deepcopy(polyline))
                                proj_top_n.Transform(rg.Transform.ProjectAlong(self.plates[i].top_plane, joint_plane.ZAxis))                               
                                proj_top_n =proj_top_n.ToArray()
                                proj_bottom_n = rg.Polyline(copy.deepcopy(polyline))
                                proj_bottom_n.Transform(rg.Transform.ProjectAlong(self.plates[i].bottom_plane, joint_plane.ZAxis))
                                proj_bottom_n = proj_bottom_n.ToArray()
                                finger_box_n = box = rg.Brep.CreateFromBox(proj_top_n[0:4] + proj_bottom_n[0:4])
                                self.plates[i].joints_negatives.append(finger_box_n)
                                
                                #projection for joint positive
                                proj_top_p = rg.Polyline(copy.deepcopy(polyline))
                                proj_top_p.Transform(rg.Transform.ProjectAlong(self.plates[nb].top_plane, joint_plane.ZAxis))
                                proj_top_p =proj_top_p.ToArray()
                                proj_bottom_p = rg.Polyline(copy.deepcopy(polyline))
                                proj_bottom_p.Transform(rg.Transform.ProjectAlong(self.plates[nb].bottom_plane, joint_plane.ZAxis))
                                proj_bottom_p = proj_bottom_p.ToArray()
                                finger_box_p = box = rg.Brep.CreateFromBox(proj_top_p[0:4] + proj_bottom_p[0:4])   
                                #if (finger_length_2 == 'default') or (finger_length_2 == 0) :
                                top_plane = rs.coerceplane(self.plates[i].top_plane)
                                bottom_plane =  rs.coerceplane(self.plates[i].bottom_plane)
                                finger_box_p = Toolbox.Breps.slice_2_planes(finger_box_p, top_plane, bottom_plane)                  
                                self.plates[nb].joints_positives.append(finger_box_p)
                                

                                # contour
                                top_poly_n = rs.AddPolyline([proj_top_n[0],proj_top_n[1], proj_top_n[2], proj_top_n[3]])
                                bottom_poly_n = rs.AddPolyline([proj_bottom_n[0],proj_bottom_n[1], proj_bottom_n[2], proj_bottom_n[3]])
                                top_poly_p = rs.AddPolyline([proj_top_p[0],proj_top_p[1], proj_top_p[2], proj_top_p[3]])
                                bottom_poly_p = rs.AddPolyline([proj_bottom_p[0],proj_bottom_p[1], proj_bottom_p[2], proj_bottom_p[3]])
                                
                                self.plates[nb].top_contour = Toolbox.Curves.insert_curves(self.plates[nb].top_contour, [top_poly_p])
                                self.plates[nb].bottom_contour = Toolbox.Curves.insert_curves(self.plates[nb].bottom_contour, [bottom_poly_p])
                                self.plates[i].top_contour = Toolbox.Curves.insert_curves(self.plates[i].top_contour, [top_poly_n])
                                self.plates[i].bottom_contour = Toolbox.Curves.insert_curves(self.plates[i].bottom_contour, [bottom_poly_n])   

                            #solid - second side
                            for k in range(len(location_1)):
                                #base polyline
                                point1 = rs.coerce3dpoint(rs.CopyObject(location_1[k], joint_plane.XAxis * finger_width_1/2))
                                point4 = rs.coerce3dpoint(rs.CopyObject(location_1[k], -joint_plane.XAxis * finger_width_1/2))
                                point2 = rs.coerce3dpoint(rs.CopyObject(point1, -joint_plane.YAxis * new_finger_length_1))
                                point3 = rs.coerce3dpoint(rs.CopyObject(point4, -joint_plane.YAxis * new_finger_length_1))
                                polyline = [point1, point2, point3, point4, point1]
                                
                                #projection for joint negative
                                proj_top_n = rg.Polyline(copy.deepcopy(polyline))
                                proj_top_n.Transform(rg.Transform.ProjectAlong(self.plates[nb].top_plane, joint_plane.ZAxis))
                                proj_top_n =proj_top_n.ToArray()
                                proj_bottom_n = rg.Polyline(copy.deepcopy(polyline))
                                proj_bottom_n.Transform(rg.Transform.ProjectAlong(self.plates[nb].bottom_plane, joint_plane.ZAxis))
                                proj_bottom_n = proj_bottom_n.ToArray()
                                finger_box_n = box = rg.Brep.CreateFromBox(proj_top_n[0:4] + proj_bottom_n[0:4])
                                self.plates[nb].joints_negatives.append(finger_box_n)
                                
                                #projection for joint positive
                                proj_top_p = rg.Polyline(copy.deepcopy(polyline))
                                proj_top_p.Transform(rg.Transform.ProjectAlong(self.plates[i].top_plane, joint_plane.ZAxis))
                                proj_top_p =proj_top_p.ToArray()
                                proj_bottom_p = rg.Polyline(copy.deepcopy(polyline))
                                proj_bottom_p.Transform(rg.Transform.ProjectAlong(self.plates[i].bottom_plane, joint_plane.ZAxis))
                                proj_bottom_p = proj_bottom_p.ToArray()
                                finger_box_p = box = rg.Brep.CreateFromBox(proj_top_p[0:4] + proj_bottom_p[0:4])
                                #if (finger_length_1 == 'default') or (finger_length_1 == 0) :
                                top_plane = rs.coerceplane(self.plates[nb].top_plane)
                                bottom_plane =  rs.coerceplane(self.plates[nb].bottom_plane)
                                finger_box_p = Toolbox.Breps.slice_2_planes(finger_box_p, top_plane, bottom_plane)
                                self.plates[i].joints_positives.append(finger_box_p)

                                # contour
                                top_poly_n = rs.AddPolyline([proj_top_n[0],proj_top_n[1], proj_top_n[2], proj_top_n[3]])
                                bottom_poly_n = rs.AddPolyline([proj_bottom_n[0],proj_bottom_n[1], proj_bottom_n[2], proj_bottom_n[3]])
                                top_poly_p = rs.AddPolyline([proj_top_p[0],proj_top_p[1], proj_top_p[2], proj_top_p[3]])
                                bottom_poly_p = rs.AddPolyline([proj_bottom_p[0],proj_bottom_p[1], proj_bottom_p[2], proj_bottom_p[3]])

                                self.plates[i].top_contour = Toolbox.Curves.insert_curves(self.plates[i].top_contour, [top_poly_p])
                                self.plates[i].bottom_contour = Toolbox.Curves.insert_curves(self.plates[i].bottom_contour, [bottom_poly_p])
                                self.plates[nb].top_contour = Toolbox.Curves.insert_curves(self.plates[nb].top_contour, [top_poly_n])
                                self.plates[nb].bottom_contour = Toolbox.Curves.insert_curves(self.plates[nb].bottom_contour, [bottom_poly_n])

            @__skip_nones
            def add_halflap(self,
                plates_pairs='all',
                proportion = 0.5,
                tolerance = 0.0,
                min_angle = 45.0,
                straight_height = 0.0,
                fillet_height = 0.0,
                segments = 1):

                """Add half-lap joints on Intersecting Plates."""

                #cast plate_pairs to string
                if plates_pairs != 'all':
                    for i in range(len(plates_pairs)):
                        plates_pairs[i] = str(plates_pairs[i])
                
                #conditional loop
                for i in range(self.count):
                    types = self.contact_types[i]
                    for j in range(len(types)):
                        nb = self.contact_ids[i][j]

                        #specific selection function
                        if ((plates_pairs == 'all') 
                            or ('('+str(i)+','+str(nb)+')' == plates_pairs) 
                            or ('('+str(i)+','+str(nb)+')' in plates_pairs)): 
                                i_want_a_halflap = True
                        else: i_want_a_halflap = False
                        
                        #for all specified Side-to-Side connection
                        if (types[j] == 'IN') and (nb > i) and (i_want_a_halflap is True):

                            #prerequisite
                            if proportion < 0.01 or proportion > 0.99: raise Exception(' Proportion should remain strictly between 0.01 and 0.99.')
                            if tolerance < 0 : raise Exception(' Tolerance should be higher than 0.0.')
                            if segments < 1: segments =1

                            # Solids
                            zone = self.contact_zones[i][j]
                            volume = rg.Brep.CreateBooleanIntersection(self.plates[i].brep,self.plates[nb].brep, 0.001)[0]
                            edges = Toolbox.Breps.brep_edges(volume)
                            edges.sort(key=rs.CurveLength)
                            edges.reverse()
                            vec_dir = Toolbox.Vectors.round_vector(rs.VectorUnitize(Toolbox.Vectors.cross(self.plates[i].top_normal, self.plates[nb].top_normal)),3)
                            four_edges = []
                            for edge in edges:
                                vec_line = Toolbox.Vectors.round_vector(rs.VectorUnitize(Toolbox.Vectors.line_to_vec(edge)),3) 
                                if vec_dir == vec_line:
                                    four_edges.append(edge)
                                elif vec_dir == rs.VectorReverse(vec_line):
                                    rg.Curve.Reverse(edge)
                                    four_edges.append(edge)
                                if len(four_edges) == 4: break

                            # Mid plane
                            mids = [rs.CurveMidPoint(four_edges[k]) for k in range(4)]
                            center = Toolbox.Points.average_point(mids)
                            proj = rs.coerce3dpointlist([rs.EvaluateCurve(four_edges[l],rs.CurveClosestPoint(four_edges[l],center)) for l in range(4)])

                            # Proportion parameter
                            d1 = rs.Distance(rs.CurveStartPoint(four_edges[0]), proj[0])
                            d2 = rs.Distance(rs.CurveStartPoint(four_edges[1]), proj[1]) 
                            d3 = rs.Distance(rs.CurveStartPoint(four_edges[2]), proj[2]) 
                            d4 = rs.Distance(rs.CurveStartPoint(four_edges[3]), proj[3])
                            min1 = min(d1,d2,d3,d4)
                            d5 = rs.Distance(rs.CurveEndPoint(four_edges[0]), proj[0])
                            d6 = rs.Distance(rs.CurveEndPoint(four_edges[1]), proj[1]) 
                            d7 = rs.Distance(rs.CurveEndPoint(four_edges[2]), proj[2]) 
                            d8 = rs.Distance(rs.CurveEndPoint(four_edges[3]), proj[3])
                            min2 = min(d5,d6,d7,d8)
                            poly = rs.AddPolyline(rs.PolylineVertices(gh.ConvexHull(proj, rs.PlaneFitFromPoints(proj))[0]))
                            vec1 = rs.VectorUnitize(rs.VectorCreate(rs.CurveStartPoint(four_edges[0]), proj[0]))
                            polyAt0 = rs.CopyObject(poly, min1*vec1)
                            poly = rs.CopyObject(polyAt0, proportion*(min1+min2)*rs.VectorUnitize(-vec1))
                            # Cutting volume in pieces
                            cutter = rs.coercebrep(rs.AddPlanarSrf(poly))
                            pieces = rs.SplitBrep(volume, cutter)                            
                            
                            for piece in pieces: piece = rs.CapPlanarHoles(piece)
                            int_i = rs.CurveBrepIntersect(self.plates[i].top_contour, pieces[0])
                            int_nb = rs.CurveBrepIntersect(self.plates[nb].top_contour, pieces[0])
                            if int_i != None:
                                if int_nb != None: 
                                    if rs.CurveLength(int_i[0]) < rs.CurveLength(int_nb[0]):
                                        pieces.reverse()
                            else: pieces.reverse()
                            
                            # Fabrication lines
                            piece_i_top = Toolbox.Curves.curve_difference(rs.IntersectBreps(pieces[0], self.plates[i].top_face)[0], self.plates[i].top_contour)
                            piece_i_bottom = Toolbox.Curves.curve_difference(rs.IntersectBreps(pieces[0], self.plates[i].bottom_face)[0], self.plates[i].bottom_contour)
                            piece_nb_top = Toolbox.Curves.curve_difference(rs.IntersectBreps(pieces[1], self.plates[nb].top_face)[0], self.plates[nb].top_contour)
                            piece_nb_bottom = Toolbox.Curves.curve_difference(rs.IntersectBreps(pieces[1], self.plates[nb].bottom_face)[0], self.plates[nb].bottom_contour)

                            # Chamfer
                            if tolerance != 0:
                                
                                if not 0 < min_angle < 90 : raise Exception(' The angle of the slope should remain strictly between 0 and 90.')
                                
                                radius = fillet_height/math.sin(math.radians(90-min_angle))
                                fillet_width = radius - math.sqrt((radius*radius)-(fillet_height*fillet_height))
                                
                                if fillet_width > tolerance: raise Exception(' Fillet height is to big according to the tolerance you specified.')
                                
                                #polyline vertices without chamfer   
                                pv_i_top = rs.CullDuplicatePoints(rs.PolylineVertices(piece_i_top),0.01)
                                pv_i_bottom = rs.CullDuplicatePoints(rs.PolylineVertices(piece_i_bottom),0.01)
                                pv_nb_top = rs.CullDuplicatePoints(rs.PolylineVertices(piece_nb_top),0.01)
                                pv_nb_bottom = rs.CullDuplicatePoints(rs.PolylineVertices(piece_nb_bottom),0.01)

                                #chamfer planes
                                chamfer_planes = []
                                chamfer_planes.append(rs.PlaneFromPoints(pv_i_top[1],pv_i_top[2],pv_i_top[0]))
                                chamfer_planes.append(rs.PlaneFromPoints(pv_i_top[2],pv_i_top[1],pv_i_top[3]))
                                chamfer_planes.append(rs.PlaneFromPoints(pv_i_bottom[2],pv_i_bottom[1],pv_i_bottom[3]))
                                chamfer_planes.append(rs.PlaneFromPoints(pv_i_bottom[1],pv_i_bottom[2],pv_i_bottom[0]))
                                chamfer_planes.append(rs.PlaneFromPoints(pv_nb_top[1],pv_nb_top[2],pv_nb_top[0]))
                                chamfer_planes.append(rs.PlaneFromPoints(pv_nb_top[2],pv_nb_top[1],pv_nb_top[3]))
                                chamfer_planes.append(rs.PlaneFromPoints(pv_nb_bottom[2],pv_nb_bottom[1],pv_nb_bottom[3]))
                                chamfer_planes.append(rs.PlaneFromPoints(pv_nb_bottom[1],pv_nb_bottom[2],pv_nb_bottom[0]))
                                contours = [self.plates[i].top_contour, self.plates[i].bottom_contour, self.plates[nb].top_contour, self.plates[nb].bottom_contour]
                                
                                #chamfer geometry
                                chamfer_sides = []
                                chamfer_faces = []
                                int_contour = []
                                for k in range(len(chamfer_planes)):
                                    cp = chamfer_planes[k]
                                    #new joint polyline
                                    point_A = cp.Origin #origin
                                    point_B = rs.CopyObject(point_A, straight_height * cp.YAxis) #before fillet
                                    point_C = rs.CopyObject(point_B, rs.VectorAdd(fillet_height * cp.YAxis, -fillet_width * cp.XAxis)) #after fillet
                                    point_D = rs.CopyObject(point_C, rs.VectorAdd( (tolerance - fillet_width) * math.tan(math.radians(min_angle)) * cp.YAxis,  -(tolerance - fillet_width) * cp.XAxis))
                                    point_E = rs.CopyObject(point_D, 100*cp.YAxis)
                                    chamfer_side = [point_A]
                                    if fillet_height > 0:
                                        fillet = Toolbox.Curves.fillet_curves(rs.AddLine(point_A,point_B), rs.AddLine(point_C,point_D), radius, False)
                                        discreet = rs.DivideCurve(fillet, segments)
                                        for point in discreet:
                                            chamfer_side.append(point)
                                    else:
                                        chamfer_side.append(rg.Point3d(rs.PointCoordinates(point_C)))
                                    chamfer_side.append(rg.Point3d(rs.PointCoordinates(point_D)))
                                    chamfer_side.append(rg.Point3d(rs.PointCoordinates(point_E)))
                                    chamfer_sides.append(rs.AddPolyline(chamfer_side))

                                    #new joint brep
                                    if k%2 == 1:
                                        chamfer_faces.append(Toolbox.Curves.connect_curves(chamfer_sides[k-1],chamfer_sides[k]))

                                chamfer_brep_1 = Toolbox.Breps.brep_from_2_poly(chamfer_faces[0], chamfer_faces[1])
                                chamfer_brep_2 = Toolbox.Breps.brep_from_2_poly(chamfer_faces[2], chamfer_faces[3])
                                pieces[0] = chamfer_brep_1
                                pieces[1] = chamfer_brep_2
                                
                                #chamfer contour
                                to_insert=[]
                                for k in range(len(contours)):
                                    c1 = Toolbox.Curves.trim_curve_with_curve(rs.coercecurve(chamfer_sides[2*k]), contours[k])
                                    c2 = Toolbox.Curves.trim_curve_with_curve(rs.coercecurve(chamfer_sides[2*k+1]), contours[k])
                                    line = rs.AddLine(rs.CurveStartPoint(c1),rs.CurveStartPoint(c2))
                                    to_insert.append(rs.coercecurve(rs.JoinCurves([c1, line, c2])))
                                piece_i_top, piece_i_bottom, piece_nb_top, piece_nb_bottom = to_insert[0], to_insert[1], to_insert[2], to_insert[3]
                            
                            #append final attributes
                            self.plates[i].joints_negatives.append(pieces[0])
                            self.plates[nb].joints_negatives.append(pieces[1])
                            self.plates[i].top_contour = Toolbox.Curves.insert_curves(self.plates[i].top_contour, [piece_i_top])
                            self.plates[i].bottom_contour = Toolbox.Curves.insert_curves(self.plates[i].bottom_contour, [piece_i_bottom])
                            self.plates[nb].top_contour = Toolbox.Curves.insert_curves(self.plates[nb].top_contour, [piece_nb_top])
                            self.plates[nb].bottom_contour = Toolbox.Curves.insert_curves(self.plates[nb].bottom_contour, [piece_nb_bottom])

                            
            # Operations ----------------------------------

            @__skip_nones
            def get_fabrication_lines(self,
                plates='all',
                contour_tool_radius = 1.0, 
                holes_tool_radius = 1.0, 
                notch=False, 
                cylinder=False,
                limit = 1,
                tbone = False):

                for i in range(self.count):
                    # apply to all or some plates.
                    flag = True
                    if (plates != None) and (plates != 'all'):
                        flag = False
                        for j in range(len(plates)):
                            if str(i) == plates[j]: flag = True
                            
                    if flag == True:

                        # match seam and direction
                        new_seam = rg.Curve.ClosestPoint(self.plates[i].bottom_contour , self.plates[i].top_contour.PointAtStart)[1]
                        self.plates[i].bottom_contour.ChangeClosedCurveSeam(new_seam)
                        self.plates[i].bottom_contour.RemoveShortSegments(0.001)
                        self.plates[i].bottom_contour  = Toolbox.Curves.align_curve_direction(self.plates[i].top_contour, self.plates[i].bottom_contour)
                        self.plates[i].bottom_contour  = rs.coercecurve(rs.AddPolyline(rs.PolylineVertices(self.plates[i].bottom_contour)))

                        # offset contour outside + create notches
                        tmc = Toolbox.Curves.offset_with_notch3(self.plates[i].top_contour, contour_tool_radius, notch, limit, tbone)
                        bmc = Toolbox.Curves.offset_with_notch3(self.plates[i].bottom_contour, contour_tool_radius, notch, limit, tbone)

                        self.temp.append(bmc)
                        #match seams
                        tmc, bmc = Toolbox.Curves.match_seams(tmc,bmc, False)
                        self.plates[i].top_milling_contour = rs.coercecurve(tmc)
                        self.plates[i].bottom_milling_contour = rs.coercecurve(bmc)

                        #cylinder planes
                        tmc_cylinder_points = Toolbox.Curves.get_spikes(tmc)
                        bmc_cylinder_points = Toolbox.Curves.get_spikes(bmc)
                        tmc_cylinder_planes = [rs.PlaneFromFrame(point, self.plates[i].top_plane.XAxis, self.plates[i].top_plane.YAxis) for point in tmc_cylinder_points]
                        bmc_cylinder_planes = [rs.PlaneFromFrame(point, self.plates[i].bottom_plane.XAxis, self.plates[i].bottom_plane.YAxis) for point in bmc_cylinder_points]

                        # create cylinder on contour notches for optional boolean operation
                        if (tmc_cylinder_planes != []) and (cylinder is True) and (notch is True):
                            for j in range(len(tmc_cylinder_planes)):
                                path = rs.AddLine(tmc_cylinder_planes[j].Origin, bmc_cylinder_planes[j].Origin)
                                cyl = rs.ExtrudeCurve(rs.AddCircle(tmc_cylinder_planes[j], contour_tool_radius), path)
                                rs.CapPlanarHoles(cyl)
                                self.plates[i].joints_negatives.append(rs.coercebrep(cyl))
                        
                        # offset holes inside + create notches
                        if self.plates[i].top_holes != [] :
                            for j in range(len(self.plates[i].top_holes)):

                                # offset holes inside + create notches        
                                tmh = Toolbox.Curves.offset_with_notch3(self.plates[i].top_holes[j], -holes_tool_radius, notch, limit, tbone)
                                bmh = Toolbox.Curves.offset_with_notch3(self.plates[i].bottom_holes[j], -holes_tool_radius, notch, limit, tbone)
                                
                                #match seams
                                tmh, bmh = Toolbox.Curves.match_seams(tmh,bmh, False)
                                self.plates[i].top_milling_holes.append(rs.coercecurve(tmh))
                                self.plates[i].bottom_milling_holes.append(rs.coercecurve(bmh))
                                
                                #cylinder planes
                                tmh_cylinder_points = Toolbox.Curves.get_spikes(tmh)
                                bmh_cylinder_points = Toolbox.Curves.get_spikes(bmh)
                                tmh_cylinder_planes = [rs.PlaneFromFrame(point, self.plates[i].top_plane.XAxis, self.plates[i].top_plane.YAxis) for point in tmh_cylinder_points]
                                bmh_cylinder_planes = [rs.PlaneFromFrame(point, self.plates[i].bottom_plane.XAxis, self.plates[i].bottom_plane.YAxis) for point in bmh_cylinder_points]

                                # create cylinder on holes notches for optional boolean operation
                                if (tmh_cylinder_planes != []) and (cylinder is True) and (notch is True):

                                    for j in range(len(tmh_cylinder_planes)):
                                        path = rs.AddLine(tmh_cylinder_planes[j].Origin, bmh_cylinder_planes[j].Origin)
                                        cyl = rs.ExtrudeCurve(rs.AddCircle(tmh_cylinder_planes[j], holes_tool_radius), path)
                                        rs.CapPlanarHoles(cyl)
                                        self.plates[i].joints_negatives.append(rs.coercebrep(cyl))

            @__skip_nones
            def perform_boolean_operations(self, plates='all', bool_tol=0.1, merge_tol=0.01):

                # Boolean union
                for i in range(self.count):
                    flag = True
                    if (plates != None) and (plates != 'all'):
                        flag = False
                        for j in range(len(plates)):
                            if str(i) == plates[j]: flag = True
                    if flag == True:
                        if len(self.plates[i].joints_positives) != 0 :
                            try:
                                # rhino_common methods (more reliable)
                                brep = rs.coercebrep(rs.CopyObject(self.plates[i].brep))
                                rhino_joined = rg.Brep.JoinBreps([brep]+self.plates[i].joints_positives, bool_tol)
                                rhino_unified = rg.Brep.CreateBooleanUnion(rhino_joined, bool_tol)[0]
                                rhino_unified.MergeCoplanarFaces(merge_tol, merge_tol)
                                # back to grasshopper
                                scriptcontext.doc.Objects.Add(rhino_unified)
                                self.plates[i].brep = rhino_unified
                            except:
                                print("boolean addition failed on plate " + str(i))
                                brep = rs.coercebrep(rs.CopyObject(self.plates[i].brep))
                                rhino_joined = rg.Brep.JoinBreps([brep]+self.plates[i].joints_positives, bool_tol)
                                rhino_unified = rg.Brep.CreateBooleanUnion(rhino_joined, bool_tol)

                # Boolean difference
                for i in range(self.count):
                    if str(i) in plates or plates == 'all':
                        if len(self.plates[i].joints_negatives) != 0 :
                            try:
                                for j in range(len(self.plates[i].joints_negatives)):
                                    #check orientation
                                    self.plates[i].joints_negatives[j] = rs.coercebrep(self.plates[i].joints_negatives[j])
                                    if(self.plates[i].joints_negatives[j].SolidOrientation == rg.BrepSolidOrientation.Inward):
                                        rg.Brep.Flip(self.plates[i].joints_negatives[j])
                                    try:
                                        self.plates[i].brep = rg.Brep.CreateBooleanDifference(self.plates[i].brep, self.plates[i].joints_negatives[j], bool_tol)[0]
                                    except: 
                                        print('Boolean difference failed on plate '+str(i)+' with joint '+str(j))
                                #try merge faces
                                try: 
                                    rg.Brep.MergeCoplanarFaces(self.plates[i].brep, merge_tol, merge_tol)
                                except:
                                    print("couldn't merge faces further on plate "+ str(i))
                                #back to grasshopper
                                scriptcontext.doc.Objects.Add(self.plates[i].brep)
                            except: print("boolean difference failed on plate " + str(i))

            @__skip_nones
            def transform(self, 
                mode = 'Array', 
                origin = rs.PlaneFromFrame((0,0,0), (1,0,0), (0,1,0)), 
                step = (1,0,0), 
                flip = None, 
                custom = [],
                scale = 1.0,
                target = rs.PlaneFromFrame((0,0,0), (1,0,0), (0,1,0))):
                
                #array parameters
                if mode == 1 : mode = 'Array'
                if mode == 2 : mode = 'Stack'
                if mode == 3 : mode = 'Custom'
                if mode == 4 : mode = 'Scale'
                if mode == 5 : mode = 'Orient'
                if len(origin) == 3: origin = rs.PlaneFromFrame(origin, (1,0,0), (0,1,0))
                center = origin.Origin 
                step = rs.VectorCreate(step, (0,0,0))

                #compute total stack height
                if mode == 'Stack':
                    stack_height = 0
                    for i in range(self.count):
                        stack_height += self.plates[i].thickness

                #get transformation for each plate
                for i in range(self.count):

                    #list of all attributes to be transformed
                    attributes=[self.breps[i],
                    self.contact_zones[i],
                    self.contact_vectors[i],
                    self.contact_spheres[i],
                    self.contact_breps[i],
                    self.contact_centers[i],
                    self.contact_planes[i],
                    self.contact_normals[i],
                    self.plates[i].brep,
                    self.plates[i].top_face,
                    self.plates[i].bottom_face,
                    self.plates[i].top_contour,
                    self.plates[i].bottom_contour,
                    self.plates[i].top_holes,
                    self.plates[i].bottom_holes,
                    self.plates[i].top_center,
                    self.plates[i].plate_center,
                    self.plates[i].bottom_center,
                    self.plates[i].top_normal,
                    self.plates[i].bottom_normal,
                    self.plates[i].top_plane,
                    self.plates[i].mid_plane,
                    self.plates[i].bottom_plane,
                    self.plates[i].top_milling_contour,
                    self.plates[i].bottom_milling_contour,
                    self.plates[i].top_milling_holes,
                    self.plates[i].bottom_milling_holes,
                    self.plates[i].joints_positives,
                    self.plates[i].joints_negatives,
                    self.plates[i].joints_keys]                  
                    
                    # stack transform
                    if mode == 'Stack':
                        stack_height -= self.plates[i].thickness
                        plate_height = stack_height + (self.plates[i].thickness /2 )
                        point = rs.CopyObject(center, (0, 0, plate_height))
                    
                    # array transform
                    if mode == 'Array':
                        point = rs.CopyObject(center, step * i)
                    
                    # custom transform
                    if mode == 'Custom':
                        if custom != None and custom != []: 
                            for j in range(len(custom)):
                                point = custom[i % len(custom)]
                        else: 
                            point = center

                    # flip option
                    if mode == 'Custom' or mode == 'Array' or mode == 'Stack':
                        mid_plane = self.plates[i].mid_plane
                        flat_plane = rs.PlaneFromFrame(point, origin.XAxis, origin.YAxis)
                        if flip != None:
                            if str(i) in flip:
                                self.log.append('plate '+ str(i) + ' was flipped')
                                flat_plane = rs.PlaneFromFrame(point, origin.XAxis, -origin.YAxis)

                        # Matrix from Plane to plane orientation
                        matrix = rg.Transform.PlaneToPlane(mid_plane, flat_plane)

                    # Scaling transformation
                    if mode == 'Scale':
                        if scale <= 0 : 
                            scale = 1.0
                            raise Exception('scaling factor should be greater than 0')
                        self.plates[i].thickness = self.plates[i].thickness * scale
                        matrix = rg.Transform.Scale(center, scale)
                    
                    # Orient (Move/rotate) transformation 
                    if mode == 'Orient':
                        ref = origin

                        matrix = rg.Transform.PlaneToPlane(ref, target)

                    # Transforming each attribute
                    if mode == 'Custom' or mode == 'Array' or mode == 'Stack' or mode == 'Scale' or mode == 'Orient':
                        for j in range(len(attributes)):
                            #dealing with attributes as lists of lists
                            if isinstance(attributes[j], list) is True:
                                for k in range(len(attributes[j])):
                                    try:
                                        attributes[j][k] = rs.coercegeometry(rs.TransformObject(attributes[j][k], matrix))
                                    except:
                                        try:
                                            rg.Vector3d.Transform(attributes[j][k], matrix)
                                            rg.Vector3d.Unitize(attributes[j][k])
                                        except:
                                            try: 
                                                rg.Plane.Transform(attributes[j][k], matrix)
                                            except:
                                                print(attributes[j][k], j, k)

                            #dealing with attributes as simple lists
                            else: 
                                    try:
                                        attributes[j] = rs.coercegeometry(rs.TransformObject(attributes[j], matrix))
                                    except:
                                        try:
                                            rg.Vector3d.Transform(attributes[j], matrix)
                                            rg.Vector3d.Unitize(attributes[j])
                                        except:
                                            try: 
                                                rg.Plane.Transform(attributes[j], matrix)
                                            except:
                                                print(attributes[j], j)

            @__skip_nones
            def switch_top_bottom(self, plates=[]):
                
                for i in range(self.count):
                    flag = False
                    if plates == 'all' : flag = True
                    if plates != [] and plates != None:
                        for j in range(len(plates)):
                            if plates[j] == i: flag = True
                    if flag == True:
                        pl = self.plates[i]
                        pl.top_face, pl.bottom_face = pl.bottom_face, pl.top_face
                        pl.top_contour, pl.bottom_contour = pl.bottom_contour, pl.top_contour
                        pl.top_holes, pl.bottom_holes = pl.bottom_holes, pl.top_holes
                        pl.top_center, pl.bottom_center = pl.bottom_center, pl.top_center
                        pl.top_normal, pl.bottom_normal = pl.bottom_normal, pl.top_normal
                        pl.top_plane, pl.bottom_plane = pl.bottom_plane, pl.top_plane
                        pl.top_milling_contour, pl.bottom_milling_contour = pl.bottom_milling_contour, pl.top_milling_contour
                        pl.top_milling_holes, pl.bottom_milling_holes = pl.bottom_milling_holes, pl.top_milling_holes

        #Modules -----------------------------------------------------------------------

        class PlateModules(PlateModel):

            def __init__(self, model, index, step, sub_sequence, parent, children):
                
                # INITIALIZATION -------------------------------------
                
                self.temp = []
                self.model = model #inherit model attributes
                self.index = index
                self.plate_ids = Toolbox.Data.flatten_integer_list(ast.literal_eval(sub_sequence))
                self.plates = [self.model.plates[integer] for integer in self.plate_ids]
                self.breps = [plate.brep for plate in self.plates]
                self.count = len(ast.literal_eval(sub_sequence))
                self.count_all = len(self.breps)
                self.step = step
                self.sequence = sub_sequence
                self.parent = parent
                self.children = children
                self.assembly_spaces = [None]
                self.assembly_vectors = [None]
                self.assembly_relatives = [None]
                self.needed_supports = 1

                # TOPOLOGY -------------------------------------------
                """
                self.contact_ids = [self.model.contact_ids[integer] for integer in self.plate_ids]
                self.contact_pairs = [self.model.contact_pairs[integer] for integer in self.plate_ids]
                self.contact_breps = [self.model.contact_breps[integer] for integer in self.plate_ids]
                self.contact_zones= [self.model.contact_zones[integer] for integer in self.plate_ids]
                self.contact_types = [self.model.contact_types[integer] for integer in self.plate_ids]
                self.contact_strings = [self.model.contact_strings[integer] for integer in self.plate_ids]
                self.contact_centers = [self.model.contact_centers[integer] for integer in self.plate_ids]
                self.contact_normals = [self.model.contact_normals[integer] for integer in self.plate_ids]
                self.contact_planes = [self.model.contact_planes[integer] for integer in self.plate_ids]
                self.contact_vectors = [self.model.contact_vectors[integer] for integer in self.plate_ids]
                
                self.contact_ids_in = self.__get_contact_inside_module(self.contact_ids)
                self.contact_pairs_in = self.__get_contact_inside_module(self.contact_pairs)
                self.contact_breps_in = self.__get_contact_inside_module(self.contact_breps)
                self.contact_zones_in= self.__get_contact_inside_module(self.contact_zones)
                self.contact_types_in = self.__get_contact_inside_module(self.contact_types)
                self.contact_strings_in = self.__get_contact_inside_module(self.contact_strings)
                self.contact_centers_in = self.__get_contact_inside_module(self.contact_centers)
                self.contact_normals_in = self.__get_contact_inside_module(self.contact_normals)
                self.contact_planes_in = self.__get_contact_inside_module(self.contact_planes)
                self.contact_vectors_in = self.__get_contact_inside_module(self.contact_vectors)

                self.contact_ids_out = self.__get_contact_outside_module(self.contact_ids)
                self.contact_pairs_out = self.__get_contact_outside_module(self.contact_pairs)
                self.contact_breps_out = self.__get_contact_outside_module(self.contact_breps)
                self.contact_zones_out= self.__get_contact_outside_module(self.contact_zones)
                self.contact_types_out = self.__get_contact_outside_module(self.contact_types)
                self.contact_strings_out = self.__get_contact_outside_module(self.contact_strings)
                self.contact_centers_out = self.__get_contact_outside_module(self.contact_centers)
                self.contact_normals_out = self.__get_contact_outside_module(self.contact_normals)
                self.contact_planes_out = self.__get_contact_outside_module(self.contact_planes)
                self.contact_vectors_out = self.__get_contact_outside_module(self.contact_vectors)
                
            def __get_contact_inside_module(self, mylist):
                inlist = []
                for i in range(len(self.contact_ids)):
                    sub_list = []
                    for j in range(len(self.contact_ids[i])):
                        if self.contact_ids[i][j] in self.plate_ids: 
                            sub_list.append(mylist[i][j])
                    inlist.append(sub_list)
                return inlist

            def __get_contact_outside_module(self, mylist):
                outlist = []
                for i in range(len(self.contact_ids)):
                    sub_list = []
                    for j in range(len(self.contact_ids[i])):
                        if self.contact_ids[i][j] in self.plate_ids: pass
                        else: sub_list.append(mylist[i][j])
                    outlist.append(sub_list)
                return outlist
                """
            pass

        #Plates -----------------------------------------------------------------------

        class Plate:

            def __init__(self, brep, index):

                # INITIALIZATION  -------------------------------------

                self.temp = []
                self.index = index
                self.brep = copy.deepcopy(brep)
                self.top_face = self.__get_top_face()
                self.bottom_face = self.__get_bottom_face()
                self.top_contour = self.__get_top_contour()
                self.bottom_contour = self.__get_bottom_contour()
                self.top_holes = self.__get_top_holes()
                self.bottom_holes = self.__get_bottom_holes()
                self.top_center = self.__get_top_center()
                self.bottom_center = self.__get_bottom_center()
                self.plate_center =self.__get_plate_center()
                self.top_normal = self.__get_top_normal()
                self.bottom_normal = self.__get_bottom_normal()
                self.top_plane = self.__get_top_plane()
                self.bottom_plane = self.__get_bottom_plane()
                self.mid_plane = self.__get_mid_plane()
                self.thickness = self.__get_thickness()

                # JOINERY --------------------------------------------

                self.joints_positives = []
                self.joints_negatives = []
                self.joints_keys = []

                # FABRICATION ----------------------------------------

                self.top_milling_contour = []
                self.bottom_milling_contour = []
                self.top_milling_holes = []
                self.bottom_milling_holes = []


            def __get_top_face(self):
                faces = self.brep.Faces
                sortedfaces = Toolbox.Surfaces.sort_surfaces_by_area(faces)
                sortedfaces.reverse()
                top_and_bottom = [sortedfaces[0][0],sortedfaces[1][0]]
                top_face = Toolbox.Surfaces.sort_surfaces_by_altitude(top_and_bottom)[1][0]
                return top_face

            def __get_bottom_face(self):
                faces = self.brep.Faces
                sortedfaces = Toolbox.Surfaces.sort_surfaces_by_area(faces)
                sortedfaces.reverse()
                top_and_bottom = [sortedfaces[0][0],sortedfaces[1][0]]
                bottom_face = Toolbox.Surfaces.sort_surfaces_by_altitude(top_and_bottom)[0][0]
                return bottom_face

            def __get_top_contour(self):
                largest_contour = Toolbox.Surfaces.get_face_largest_contour(self.top_face)
                if type(largest_contour) != rg.PolylineCurve: largest_contour=largest_contour.ToPolyline(0.01,0.01,0.01,10000)
                largest_contour = scriptcontext.doc.Objects.Add(largest_contour)
                Toolbox.Curves.resimplify_Curve(largest_contour)
                largest_contour = rs.coercecurve(largest_contour)
                return largest_contour

            def __get_bottom_contour(self):
                perimeter = Toolbox.Surfaces.get_face_largest_contour(self.bottom_face)
                #adjust seam
                new_seam = rg.Curve.ClosestPoint(perimeter, self.top_contour.PointAtStart)[1]
                perimeter.ChangeClosedCurveSeam(new_seam)
                #adjust direction
                new_perimeter = Toolbox.Curves.align_curve_direction(self.top_contour,perimeter)
                if type(new_perimeter) != rg.PolylineCurve: new_perimeter=new_perimeter.ToPolyline(0.01,0.01,0.01,10000)
                new_perimeter = scriptcontext.doc.Objects.Add(new_perimeter)
                Toolbox.Curves.resimplify_Curve(new_perimeter)
                new_perimeter = rs.coercecurve(new_perimeter)
                return new_perimeter

            def __get_top_holes(self):
                return Toolbox.Surfaces.get_face_other_contours(self.top_face)

            def __get_bottom_holes(self):
                perimeters = Toolbox.Surfaces.get_face_other_contours(self.bottom_face)
                if perimeters != [] :
                    for i in range(len(perimeters)):
                        #adjust seamtop_contour
                        new_seam = rg.Curve.ClosestPoint(perimeters[i], self.top_holes[i].PointAtStart)[1]
                        perimeters[i].ChangeClosedCurveSeam(new_seam)
                        #adjust direction
                        perimeters[i] = Toolbox.Curves.align_curve_direction(self.top_holes[i],perimeters[i],n = 10)
                return perimeters

            def __get_top_center(self):
                return rs.CurveAreaCentroid(self.top_contour)[0]

            def __get_bottom_center(self):
                return rs.CurveAreaCentroid(self.bottom_contour)[0]

            def __get_plate_center(self):
                return (self.top_center + self.bottom_center) /2

            def __get_top_normal(self):
                normal = rs.SurfaceNormal(self.top_face,[0,0])
                if Toolbox.Vectors.is_vector_outward(self.plate_center, self.top_center, normal) is True:
                    return normal
                else: return -normal

            def __get_bottom_normal(self):
                normal = rs.SurfaceNormal(self.bottom_face,[0,0])
                if Toolbox.Vectors.is_vector_outward(self.plate_center, self.bottom_center, normal) is True:
                    return normal
                else: return -normal

            def __get_top_plane(self):
                origin = self.top_center
                sides = rs.ExplodeCurves(rs.CopyObject(self.top_contour)) 
                longest_side = Toolbox.Curves.sort_curves_by_length(sides)[-1][0]
                x_axis = rs.VectorCreate(rs.CurveStartPoint(longest_side), rs.CurveEndPoint(longest_side))
                return rs.PlaneFromNormal(origin, self.top_normal, x_axis)

            def __get_bottom_plane(self):
                return rs.CreatePlane(self.bottom_center,self.top_plane.YAxis,self.top_plane.XAxis)

            def __get_mid_plane(self):
                return rs.CreatePlane(self.plate_center,self.top_plane.XAxis,self.top_plane.YAxis)

            def __get_thickness(self):
                pointA = self.top_center
                pointB = rg.Brep.ClosestPoint(self.bottom_face, pointA)
                t = rg.Point3d.DistanceTo(pointA,pointB)
                return t

            pass

        #Toolbox -----------------------------------------------------------------------
        
        class Toolbox:
            """Class of geometrical functions extending the rhinocommon library"""

            class Breps:

                @staticmethod #wip
                def is_plate():
                    pass
                    
                @staticmethod
                def brep_edges(brep):
                    array = rg.Brep.DuplicateEdgeCurves(brep)
                    edges = []
                    for curve in array:
                        edges.append(curve)
                    return edges

                @staticmethod
                def brep_faces(brep):
                    brep = rs.coercebrep(brep)
                    faces = []
                    for face in brep.faces:
                        faces.append(face)
                    return faces

                @staticmethod
                def brep_vertices(brep):
                    array = rg.Brep.DuplicateVertices(brep)
                    vertices = []
                    for point in array:
                        vertices.append(point)
                    return vertices

                @staticmethod
                def brep_centroid(brep):
                    brep = rs.coercebrep(brep)
                    return rg.AreaMassProperties.Compute(brep).Centroid
                
                @staticmethod
                def slice_2_planes(brep, top_plane, bottom_plane):
                    #top plane
                    tbrep = copy.deepcopy(brep)
                    tbrep = rg.Brep.Trim(tbrep, top_plane, 0.1)
                    if len(tbrep) > 0: 
                        tbrep = tbrep[0]
                        tbrep = rg.Brep.CapPlanarHoles(tbrep, 0.1)
                    else: tbrep = copy.deepcopy(brep)
                    #bottom plane
                    bbrep = copy.deepcopy(tbrep)
                    bbrep = rg.Brep.Trim(bbrep, bottom_plane, 0.1)
                    if len(bbrep) > 0: 
                        bbrep = bbrep[0]
                        bbrep = rg.Brep.CapPlanarHoles(bbrep, 0.1)
                    else: bbrep = copy.deepcopy(tbrep)
                    #back to grasshopper
                    brep = bbrep
                    scriptcontext.doc.Objects.Add(brep)
                    return brep

                @staticmethod
                def brep_from_2_poly(poly1, poly2):
                    poly2 = Toolbox.Curves.align_curve_direction(rs.coercegeometry(poly1), rs.coercegeometry(poly2))
                    poly2 = rs.AddPolyline(rs.PolylineVertices(poly2)+[rs.PolylineVertices(poly2)[0]])
                    poly1, poly2 = Toolbox.Curves.match_seams(poly1,poly2)
                    points_a = rs.PolylineVertices(poly1)
                    points_b = rs.PolylineVertices(poly2)
                    faces = []
                    if len(points_a) == len(points_b):
                        for i in range(len(points_a)-1):
                            poly = rs.AddPolyline([(points_a[i]), (points_a[i+1]), (points_b[i+1]), (points_b[i]), (points_a[i])])
                            faces.append(rs.AddPlanarSrf(poly)[0])
                    brep = rs.JoinSurfaces(faces)
                    rs.CapPlanarHoles(brep)
                    return rs.coercebrep(brep)

                @staticmethod
                def box_from_2_poly(poly1, poly2):
                    box = rs.AddBox(rs.PolylineVertices(poly1)[0:4]+rs.PolylineVertices(poly2)[0:4])
                    #box = rg.Brep.CreateFromBox(poly1[0:4] + poly2[0:4])
                    return box


            class Surfaces:

                @staticmethod
                def surface_centroid(surface):
                    surface = rs.coercesurface(surface)
                    return rg.AreaMassProperties.Compute(surface).Centroid

                @staticmethod
                def sort_surfaces_by_altitude(planar_surfaces):
                    faces = planar_surfaces
                    faces_tuples = []
                    for i in range(len(faces)):
                        face_centroid = Toolbox.Surfaces.surface_centroid(faces[i])
                        faces_tuples.append([faces[i],face_centroid[2]])
                    sortedfaces = sorted(faces_tuples, key=lambda faces: faces[1])
                    return sortedfaces

                @staticmethod
                def sort_surfaces_by_area(planar_surfaces):
                    faces = planar_surfaces
                    faces_tuples = []
                    for face in faces:
                        #test_planar = rg.Surface.IsPlanar(face)
                        #if test_planar is True:
                        face = rg.BrepFace.DuplicateFace(face, False)
                        face_area = rg.Brep.GetArea(face)
                        faces_tuples.append([face,face_area])
                        #else:
                        #    raise Exception(' Brep faces must be planar') 
                        #    break

                    sortedfaces = sorted(faces_tuples, key=lambda faces: faces[1])
                    return sortedfaces

                @staticmethod
                def get_face_largest_contour(face):
                    if str(face.ObjectType) == 'Surface':
                        face = rg.Brep.CreateFromSurface(face)
                    curves = rg.Brep.DuplicateEdgeCurves(face)
                    borders = rg.Curve.JoinCurves(curves)
                    curves_tuples = []
                    for i in range(len(borders)):
                        surface = rg.Brep.CreatePlanarBreps(borders[i])
                        area = rg.AreaMassProperties.Compute(surface).Area
                        curves_tuples.append([borders[i], area])
                    sortedcurves = sorted(curves_tuples, key=lambda curves: curves[1])
                    sortedcurves.reverse()
                    perimeter = sortedcurves[0][0]
                    return perimeter

                @staticmethod
                def get_face_other_contours(face):
                    if str(face.ObjectType) == 'Surface':
                        face = rg.Brep.CreateFromSurface(face)
                    curves = rg.Brep.DuplicateEdgeCurves(face)
                    borders = rg.Curve.JoinCurves(curves)
                    curves_tuples = []
                    for i in range(len(borders)):
                        surface = rg.Brep.CreatePlanarBreps(borders[i])
                        area = rg.AreaMassProperties.Compute(surface).Area
                        curves_tuples.append([borders[i], area])
                    sortedcurves = sorted(curves_tuples, key=lambda curves: curves[1])
                    sortedcurves.reverse()
                    perimeters = []
                    if len(sortedcurves)>0:
                        for i in range(len(sortedcurves)-1):
                            perimeters.append(sortedcurves[i+1][0])
                    return perimeters


            class Curves:
                
                @staticmethod
                def rectangle_dimensions(rectangle):
                    "get length and width from a rectangle"
                    curves = rs.ExplodeCurves(rectangle)
                    l1 = rs.CurveLength(curves[0])
                    l2 = rs.CurveLength(curves[1])
                    if l1 > l2:
                        return (l1, l2)
                    else: 
                        return (l2, l1)

                @staticmethod
                def offset_with_notch1(curve, distance, notch=False, limit=1, pair=0, custom_offset=None):

                    # placeholder for notch plane
                    notch_planes = None

                    curve = rs.coercecurve(curve)

                    if distance == 0 : return [curve, notch_planes]

                    else: 
                        normal = rs.CurveNormal(curve)
                        center = rs.CurveAreaCentroid(curve)[0]
                        plane = rs.PlaneFromNormal(center, normal)

                        # gives the option to use a custom offset curve 
                        # (e.g. using Clipper library instead of Rhino default definition)
                        if custom_offset == None :
                            offset = rs.OffsetCurve(rs.CopyObject(curve), center, -distance, normal, style=1)[0]
                        else: offset = custom_offset

                        if offset == None: 
                            raise Exception('Offset failed, tool radius is probably to big')

                        else:
                            #notch generation
                            if notch is True:
                                if distance < 0: con = 1 #convex corner for inside milling
                                else: con = -1 #concave corners for outside
                                corner = Toolbox.Curves.corner_analysis(offset, con)
                                points = corner[0]
                                bisectors = corner[1]
                                angles = corner[2]
                                ids = corner[3]
                                modifier = []
                                lines = []
                                new_poly = []
                                notch_planes = []

                                # insert notch in offset
                                pieces = rs.ExplodeCurves(offset)
                                vertices = rs.PolylineVertices(offset)
                                new_vertices = [rs.CurveStartPoint(offset)]
                                del vertices[0]
                                
                                # option to pair notches direction
                                for i in range(len(vertices)):
                                    for j in range(len(ids)):
                                        if i == ids[j]:
                                            if pair == 1 or pair == 2:
                                                factor = ((distance / math.sin(math.radians(angles[j]/2))) - distance ) * -con 
                                                if ((ids[j]%2 == pair-1) and ((ids[j]+1)%len(vertices) in ids)):
                                                    dir_1 = -rs.VectorCreate(vertices[ids[j]], vertices[(ids[j]+1)%len(vertices)])
                                                    modifier.append(distance / (math.tan(math.radians(angles[j]/2)) * factor))
                                                    bisectors[j] =  rs.VectorUnitize(dir_1)
                                                elif ((ids[j]%2 == -pair+2) and ((ids[j]-1)%len(vertices) in ids)):
                                                    dir_2 = -rs.VectorCreate(vertices[ids[j]], vertices[(ids[j]-1)%len(vertices)])
                                                    modifier.append(distance / (math.tan(math.radians(angles[j]/2)) * factor))
                                                    bisectors[j] = rs.VectorUnitize(dir_2)
                                                else : 
                                                    modifier.append(1)
                                            else: modifier.append(1)

                                # insert notch in offset
                                for i in range(len(pieces)):
                                    for j in range(len(ids)):
                                        if i == ids[j]:
                                            # limit angles where notch should be placed
                                            if angles[j]>limit and angles[j]<(180-limit):
                                                factor = ((distance / math.sin(math.radians(angles[j]/2))) - distance ) * -con * modifier[j]
                                                notch_point = rs.coerce3dpoint(rs.CopyObject((points[j]), rs.VectorScale(bisectors[j], factor)))
                                                #notch_planes.append(rs.PlaneFromFrame(notch_point, plane.XAxis, plane.YAxis))
                                                new_vertices.append(rs.CurveEndPoint(pieces[i]))
                                                new_vertices.append(notch_point)
                                    new_vertices.append(rs.CurveEndPoint(pieces[i]))
                                offset = rs.AddPolyline(new_vertices)
                    return offset

                @staticmethod
                def offset_with_notch2(curve, distance, notch=False, limit=1, pair=0, custom_offset=None):

                    # placeholder for notch plane
                    notch_planes = None

                    curve = rs.coercecurve(curve)

                    if distance == 0 : return [curve, notch_planes]

                    else: 
                        normal = rs.CurveNormal(curve)
                        center = rs.CurveAreaCentroid(curve)[0]
                        plane = rs.PlaneFromNormal(center, normal)

                        # gives the option to use a custom offset curve 
                        # (e.g. using Clipper library instead of Rhino default definition)
                        if custom_offset == None :
                            offset = rs.OffsetCurve(rs.CopyObject(curve), center, -distance, normal, style=1)[0]
                        else: offset = custom_offset

                        if offset == None: 
                            raise Exception('Offset failed, tool radius is probably to big')

                        else:
                            #notch generation
                            if notch is True:
                                if distance < 0: con = 1 #convex corner for inside milling
                                else: con = -1 #concave corners for outside
                                corner = Toolbox.Curves.corner_analysis(offset, con)
                                points = corner[0]
                                bisectors = corner[1]
                                angles = corner[2]
                                ids = corner[3]
                                modifier = []
                                lines = []
                                new_poly = []
                                notch_planes = []

                                # insert notch in offset
                                
                                pieces = rs.ExplodeCurves(offset)
                                vertices = rs.PolylineVertices(offset)
                                new_vertices = [rs.CurveStartPoint(offset)]
                                del vertices[0]
                                
                                # option to pair notches direction
                                for i in range(len(vertices)):
                                    for j in range(len(ids)):
                                        if i == ids[j]:
                                            if pair == 1 or pair == 2:
                                                factor = ((distance / math.sin(math.radians(angles[j]/2))) - distance ) * -con 
                                                if (((pair == 1) and ((ids[j]+1)%len(vertices) in ids))
                                                    or ((pair == 2) and ((ids[j]-1)%len(vertices) in ids))):
                                                    #print('a. point ',i,' from ', (ids[j]+1)%len(vertices), ' to ', ids[j])
                                                    dir_1 = rs.VectorCreate(vertices[(ids[j]+1)%len(vertices)], vertices[ids[j]%len(vertices)])
                                                    modifier.append(distance / (math.tan(math.radians(angles[j]/2)) * factor))
                                                    bisectors[j] =  rs.VectorUnitize(dir_1)
                                                elif (((pair == 1) and ((ids[j]-1)%len(vertices) in ids))
                                                    or ((pair == 2) and ((ids[j]+1)%len(vertices) in ids))):
                                                    #print('b.  point ',i,' from ', (ids[j]+1)%len(vertices), ' to ', ids[j])
                                                    dir_2 = rs.VectorCreate(vertices[ids[j]], vertices[(ids[j]+1)%len(vertices)])
                                                    modifier.append(distance / (math.tan(math.radians(angles[j]/2)) * factor))
                                                    bisectors[j] = rs.VectorUnitize(dir_2)
                                                else : 
                                                    modifier.append(1)
                                            else: modifier.append(1)

                                # insert notch in offset
                                for i in range(len(pieces)):
                                    for j in range(len(ids)):
                                        if i == ids[j]:
                                            # limit angles where notch should be placed
                                            if angles[j]>limit and angles[j]<(180-limit):
                                                factor = ((distance / math.sin(math.radians(angles[j]/2))) - distance ) * -con * modifier[j]
                                                notch_point = rs.coerce3dpoint(rs.CopyObject((points[j]), rs.VectorScale(bisectors[j], factor)))
                                                #notch_planes.append(rs.PlaneFromFrame(notch_point, plane.XAxis, plane.YAxis))
                                                new_vertices.append(rs.CurveEndPoint(pieces[i]))
                                                new_vertices.append(notch_point)
                                    new_vertices.append(rs.CurveEndPoint(pieces[i]))
                                offset = rs.AddPolyline(new_vertices)
                    return offset

                @staticmethod
                def offset_with_notch3(curve, distance, notch=False, limit=1, tbone=False):

                    # placeholder for notch plane
                    notch_planes = None

                    curve = rs.coercecurve(curve)

                    if distance == 0 : return curve

                    else: 
                        try:
                            normal = rs.CurveNormal(curve)
                            center = rs.CurveAreaCentroid(curve)[0]
                            plane = rs.PlaneFromNormal(center, normal)
                            offset = rs.OffsetCurve(rs.CopyObject(curve), center, -distance, normal, style=1)[0]

                            if offset == None: 
                                raise Exception('Offset failed, tool radius is probably to big')

                            else:
                                #notch generation
                                if notch is True:
                                    if distance < 0: con = 1 #convex corner for inside milling
                                    else: con = -1 #concave corners for outside
                                    corner = Toolbox.Curves.corner_analysis(offset, con)
                                    points = corner[0]
                                    bisectors = corner[1]
                                    angles = corner[2]
                                    ids = corner[3]
                                    modifier = []
                                    lines = []
                                    new_poly = []
                                    notch_planes = []

                                    # insert notch in offset
                                    pieces = rs.ExplodeCurves(offset)
                                    vertices = rs.PolylineVertices(offset)
                                    new_vertices = [rs.CurveStartPoint(offset)]
                                    del vertices[0]
                                    
                                    # option to use t-bone notches
                                    for i in range(len(vertices)):
                                        for j in range(len(ids)):
                                            if i == ids[j]:
                                                if tbone is True:
                                                    factor = ((distance / math.sin(math.radians(angles[j]/2))) - distance ) * -con 
                                                    if rs.Distance(vertices[i], vertices[(i+1)%len(vertices)]) > rs.Distance(vertices[i], vertices[(i-1)%len(vertices)]):
                                                        #print('a. point ',i,' from ', (i-1)%len(vertices), ' to ', i)
                                                        dir_1 = rs.VectorCreate(vertices[(i-1)%len(vertices)], vertices[i])
                                                        modifier.append(-abs(distance) / (math.tan(math.radians(angles[j]/2)) * factor))
                                                        bisectors[j] =  rs.VectorUnitize(dir_1)
                                                    elif rs.Distance(vertices[i], vertices[(i+1)%len(vertices)]) < rs.Distance(vertices[i], vertices[(i-1)%len(vertices)]):
                                                        #print('b.  point ',i,' from ', (i+1)%len(vertices), ' to ', i)
                                                        dir_2 = rs.VectorCreate(vertices[(i+1)%len(vertices)], vertices[i])
                                                        modifier.append(-abs(distance) / (math.tan(math.radians(angles[j]/2)) * factor))
                                                        bisectors[j] = rs.VectorUnitize(dir_2)
                                                    else : 
                                                        modifier.append(1)
                                                else: modifier.append(1)

                                    # insert notch in offset
                                    for i in range(len(pieces)):
                                        for j in range(len(ids)):
                                            if i == ids[j]:
                                                # limit angles where notch should be placed
                                                if angles[j]>limit and angles[j]<(180-limit):
                                                    factor = ((distance / math.sin(math.radians(angles[j]/2))) - distance ) * -con * modifier[j]
                                                    notch_point = rs.coerce3dpoint(rs.CopyObject((points[j]), rs.VectorScale(bisectors[j], factor)))
                                                    new_vertices.append(rs.CurveEndPoint(pieces[i]))
                                                    new_vertices.append(notch_point)
                                        new_vertices.append(rs.CurveEndPoint(pieces[i]))
                                    offset = rs.AddPolyline(new_vertices)
                                return offset
                        except:
                            print("toolpath failed")
                            return curve
                    

                @staticmethod
                def curve_concave_points(curve):

                    concave_points = []

                    seg = rs.ExplodeCurves(curve)
                    vec = []
                    normal = rs.CurveNormal(curve)

                    for i in range(len(seg)):
                        vec.append(rs.VectorCreate(rs.CurveEndPoint(seg[i]), rs.CurveStartPoint(seg[i])))

                    for i in range(len(vec)):
                        cross = rs.VectorCrossProduct(vec[i], vec[(i+1) % len(vec)])
                        dot = rs.VectorDotProduct(cross, normal)
                        if dot < -0.0000001 :
                            concave_points.append(rs.CurveEndPoint(seg[i]))

                    return concave_points

                @staticmethod
                def curve_convex_points(curve):

                    convex_points = []

                    seg = rs.ExplodeCurves(curve)
                    vec = []
                    normal = rs.CurveNormal(curve)

                    for i in range(len(seg)):
                        vec.append(rs.VectorCreate(rs.CurveEndPoint(seg[i]), rs.CurveStartPoint(seg[i])))

                    for i in range(len(vec)):
                        cross = rs.VectorCrossProduct(vec[i], vec[(i+1) % len(vec)])
                        dot = rs.VectorDotProduct(cross, normal)
                        if dot > 0.0000001 :
                            concave_points.append(rs.CurveEndPoint(seg[i]))

                    return convex_points

                @staticmethod
                def corner_analysis(curve, mode = 0):
                    """mode : -1 = concave, 1 = convex, 0 = both"""
                    tol = 0.0000001
                    normal = rs.CurveNormal(curve)
                    seg = rs.ExplodeCurves(curve)
                    vec = []
                    points = []
                    bisectors = []
                    angles = []
                    ids = []

                    # if product < 0 : then the corner is concave
                    for i in range(len(seg)):
                        v = rs.VectorCreate(rs.CurveEndPoint(seg[i]), rs.CurveStartPoint(seg[i]))
                        vec.append(rs.VectorUnitize(v))
                    for i in range(len(vec)):
                        cross = rs.VectorCrossProduct(vec[i], vec[(i+1) % len(vec)])
                        dot = rs.VectorDotProduct(cross, normal)

                        # keep concave or convex points or both
                        flag = False
                        if mode == -1 :
                            if (dot < -tol) : flag = True
                        elif mode == 1 : 
                            if (dot > tol) : flag = True
                        else: 
                            if (dot < -tol or dot > tol) : flag = True
                        if flag:
                            points.append(rs.CurveEndPoint(seg[i]))
                            bisectors.append(rs.VectorUnitize(rs.VectorAdd(vec[i], - vec[(i+1) % len(vec)])))
                            angle_1 = rs.VectorAngle(vec[i], -vec[(i+1) % len(vec)])
                            angle_2 = 360-angle_1
                            angles.append(min(abs(angle_1), abs(angle_2)))
                            ids.append(i)

                    return [points, bisectors, angles, ids]

                @staticmethod
                def insert_curves(base_curve, curves_to_insert, seam=None, tolerance = 0.1):
                    
                    base_curve = copy.deepcopy(base_curve)
                    curves_to_insert = copy.deepcopy(curves_to_insert)

                    # shatter points
                    points = []
                    for i in range(len(curves_to_insert)):
                        points.append(rs.CurveClosestPoint(base_curve, rs.CurveStartPoint(curves_to_insert[i])))
                        points.append(rs.CurveClosestPoint(base_curve, rs.CurveEndPoint(curves_to_insert[i])))
                    sorted(points)

                    # split curve
                    base_curve = rs.coercecurve(base_curve)
                    split = rg.Curve.Split(base_curve, points)

                    # 2 possible ways of trimming the curve
                    trim_A =  []
                    trim_B = []
                    for j in range(len(split)):
                        # cull pattern (keep only even or odd indices)
                        if j%2 == 0 : trim_A.append(split[j])
                        if j%2 == 1 : trim_B.append(split[j])

                    # join curve
                    for j in range(len(curves_to_insert)):
                        curves_to_insert[j] = rs.coercecurve(curves_to_insert[j])
                    result_A = rg.Curve.JoinCurves(curves_to_insert + trim_A, tolerance)
                    result_B = rg.Curve.JoinCurves(curves_to_insert + trim_B, tolerance)

                    # case with multiple curves to insert
                    if len(curves_to_insert) > 1 :
                        # best result is the best unified polyline
                        if len(result_A) < len(result_B) : result = result_A
                        else: result = result_B
                    
                    # case with only one curve to insert
                    else:
                        # best result is the longest curve
                        if rg.Curve.GetLength(result_A[0]) > rg.Curve.GetLength(result_B[0]) : result = result_A
                        else: result = result_B
                    if len(result) > 1 : 
                        raise Exception('joining curves failed to output a single polyline')
                        return curves_to_insert[0]
                    else : 
                        final_curve = result[0]
                        final_curve = scriptcontext.doc.Objects.Add(final_curve)
                        if seam != None:
                            Toolbox.Curves.curve_seam(final_curve, seam)
                            final_curve = Toolbox.Curves.resimplify_Curve(final_curve)
                        else: final_curve = rs.coercecurve(final_curve)
                        return final_curve

                @staticmethod
                def curve_seam(curve, point):
                    return rs.CurveSeam(curve, rs.CurveClosestPoint(curve, point))

                @staticmethod
                def curve_difference(base_curve, trim_curve):
                    # trim a curve using a surface
                    base_surface = rs.coercebrep(rs.AddPlanarSrf(base_curve))
                    base_curve = rs.coercecurve(base_curve)
                    line = rg.Intersect.Intersection.CurveBrep(trim_curve, base_surface, 0.001)[1][0]
                    p1 = line.PointAtStart
                    p2 = line.PointAtEnd
                    param1 = round(rg.Curve.ClosestPoint(base_curve,p1)[1],3)
                    param2 = round(rg.Curve.ClosestPoint(base_curve,p2)[1],3)
                    trim1 = rg.Curve.Trim(copy.deepcopy(base_curve), param1, param2)
                    trim2 = rg.Curve.Trim(copy.deepcopy(base_curve), param2, param1)               
                    mid = rs.coerce3dpoint(Toolbox.Points.average_point([p1,p2]))
                    d1 = rg.Curve.PointAt(trim1,rg.Curve.ClosestPoint(trim1,mid)[1]) 
                    d2 = rg.Curve.PointAt(trim2,rg.Curve.ClosestPoint(trim2,mid)[1]) 
                    dist1 = rs.Distance(d1, mid)
                    dist2 = rs.Distance(d2, mid)
                    if dist1 > dist2: result = trim1
                    else: result = trim2
                    return result

                @staticmethod
                def curve_closest_point(curve, point):
                    return rs.EvaluateCurve(curve, rs.CurveClosestPoint(curve, point))

                @staticmethod
                def offset(closed_curve, distance):
                    if distance != 0 :
                        return rs.OffsetCurve(closed_curve, rs.CurveAreaCentroid(closed_curve)[0], distance)[0]
                    else : return closed_curve

                @staticmethod #WIP
                def fill(closed_curve, distance, border=False):
                    if distance > 0 :
                        if border is True:
                            closed_curve = Toolbox.Curves.offset(closed_curve, -distance)
                        curves = []
                        for i in range(7) :
                            try:
                                curve = Toolbox.Curves.offset(closed_curve, distance*(i+1))
                                curve = Toolbox.Curves.open_closed_curve(curve)
                                if i > 0:
                                    if rs.CurveLength(curve) > rs.CurveLength(curves[i-1]): break
                                    link = rs.AddLine(rs.CurveEndPoint(curves[i-1]),rs.CurveStartPoint(curve))
                                    curves.append(rs.JoinCurves([curve, link])[0])
                                else: curves.append(curve)
                            except: break
                        if len(curves) > 1 :
                            return rs.JoinCurves(curves)[0]
                        else : return curves[0]
                    else : return closed_curve

                @staticmethod
                def open_closed_curve(curve):
                    tol = 0.000001 / rs.CurveLength(curve)
                    p = rs.CurveParameter(curve,1-tol)
                    return rs.AddSubCrv(curve, 0, p)
                
                @staticmethod
                def close_open_curve(curve):
                    if rs.IsCurveClosed(curve) is False:
                        line = rs.AddLine(rs.CurveStartPoint(curve), rs.CurveEndPoint(curve))
                        return rg.Curve.JoinCurves([rs.coercecurve(line),rs.coercecurve(curve)])[0]
                    else: return curve

                @staticmethod
                def sort_curves_by_length(curves):
                    curves_tuples = []
                    for i in range(len(curves)):
                        curve_length = rs.CurveLength(curves[i])
                        curves_tuples.append([curves[i],curve_length])
                    sortedcurves = sorted(curves_tuples, key=lambda curves: curves[1])
                    return sortedcurves
               
                @staticmethod
                def align_curve_direction(guide, curve):
                    if rs.CurveDirectionsMatch(curve, guide) == False: 
                        try: rg.Curve.Reverse(curve)
                        except: rs.ReverseCurve(curve)
                    return curve
                    
                @staticmethod
                def align_curve_direction_2(guide, curve, n = 10):
                    '''Flip curve comparing the angular difference between n tangent on both curves'''
                    x = guide
                    y = curve
                    r = rg.Curve.Duplicate(y)
                    rg.Curve.Reverse(r)
                    px = rg.Curve.DivideByCount(x,n,True)
                    py = rg.Curve.DivideByCount(y,n,True)
                    
                    pr = rg.Curve.DivideByCount(r,n,True)
                    tot1 = 0
                    tot2 = 0
                    for i in range(n):
                        tx = rg.Curve.TangentAt(x, px[i])
                        ty = rg.Curve.TangentAt(y, py[i])
                        tr = rg.Curve.TangentAt(r, pr[i])
                        tot1 += rg.Vector3d.VectorAngle(tx,ty)
                        tot2 += rg.Vector3d.VectorAngle(tx,tr)
                    if tot1 > tot2 :
                        rg.Curve.Reverse(y)
                    return y
               
                @staticmethod
                def resimplify_Curve(curve):
                    """Simplify and change curve seam if it's not already a vertice"""

                    rs.SimplifyCurve(curve)
                    nextstart = rs.PolylineVertices(curve)[0]
                    rs.CurveSeam(curve,rs.CurveClosestPoint(curve, nextstart))
                    rs.SimplifyCurve(curve)
                    nextstart = rs.PolylineVertices(curve)[1]
                    rs.CurveSeam(curve,rs.CurveClosestPoint(curve, nextstart))
                    rs.SimplifyCurve(curve)
                    nextstart = rs.PolylineVertices(curve)[-1]
                    rs.CurveSeam(curve,rs.CurveClosestPoint(curve, nextstart))
                    vertices = rs.PolylineVertices(curve)
                    vertices = rs.CullDuplicatePoints(vertices, 0.0001)
                    curve = rs.AddPolyline(vertices)
                    curve = Toolbox.Curves.close_open_curve(curve)

                    return curve

                @staticmethod
                def match_seams(curve1,curve2, simplify=True):
                    """Match the seams of two curves"""
                    if simplify is True:
                        Toolbox.Curves.resimplify_Curve(curve1)
                        Toolbox.Curves.resimplify_Curve(curve2)
                    Toolbox.Curves.align_curve_direction(rs.coercecurve(curve1),rs.coercecurve(curve2))
                    vcurve2 = rs.PolylineVertices(curve2)
                    del vcurve2[-1]
                    vcurve1 = rs.PolylineVertices(curve1)
                    del vcurve1[-1]
                    best_score = None
                    for i in range(len(vcurve2)):
                        totlen = 0
                        test = rs.CopyObject(curve2)
                        rs.CurveSeam(test, rs.CurveClosestPoint(test, vcurve2[i]))
                        vt = rs.PolylineVertices(test)
                        del vt[-1]
                        for j in range(min(len(vt), len(vcurve1))):
                            totlen += rs.Distance(vt[j],vcurve1[j])
                        if best_score == None: 
                            curve2 = rs.CopyObject(test)
                            best_score = totlen
                        if totlen < best_score:
                            curve2 = rs.CopyObject(test)
                            best_score = totlen
                    return [curve1, curve2]

                @staticmethod
                def get_spikes(curve, tolerance=0.0001):
                    spikes = []
                    vertices = rs.PolylineVertices(curve)
                    del vertices[0]
                    for i in range(len(vertices)):
                        if rs.Distance(vertices[i-1],vertices[(i+1)%len(vertices)]) < tolerance:
                            spikes.append(vertices[i])
                    return spikes

                @staticmethod
                def create_polygon(plane, radius, sides=3):
                    if sides == 2:
                        a = rs.CopyObject(plane[0], -plane[1] * radius)
                        b = rs.CopyObject(plane[0], plane[1] * radius)
                        return rs.AddPolyline([a, b, plane[0]])
                    elif sides >2:
                        circle = rg.Circle(plane, radius)
                        rh_polygon = rg.Polyline.CreateInscribedPolygon(circle,sides)
                        gh_polygon=[]
                        for i in range(len(rh_polygon)-1):
                            gh_polygon.append(rs.AddLine(rh_polygon[i],rh_polygon[i+1]))
                        return rs.JoinCurves(gh_polygon)[0]

                @staticmethod
                def trapeze_to_rectangle(trapeze):
                    """bases of the trapeze have to be longer than sides"""

                    
                    sorted_sides = Toolbox.Curves.sort_curves_by_length(rs.ExplodeCurves(trapeze))
                    longest_side = sorted_sides[-1][0]
                    second_side = sorted_sides[-2][0]

                    #exception sides not parallel
                    if rs.IsVectorParallelTo(Toolbox.Vectors.line_to_vec(longest_side),Toolbox.Vectors.line_to_vec(second_side)) == 0: 
                        raise Exception('Longest sides are not parallel')

                    #start with the extremities of the second longest side
                    point1 = rs.CurveStartPoint(second_side)
                    point2 = rs.CurveEndPoint(second_side)

                    #create a plane at one extremity
                    plane1 = rs.PlaneFromNormal(rs.CurveStartPoint(second_side),rs.VectorCreate(point2,point1))
                    #test if the plane is intersecting the other side
                    if rs.PlaneCurveIntersection(plane1,longest_side):
                        pointA = point1
                        pointB = rs.PlaneCurveIntersection(plane1,longest_side)[0][1]
                    else:
                        point3 = rs.CurveEndPoint(longest_side)
                        point4 = rs.CurveStartPoint(longest_side)
                        plane3 = rs.PlaneFromNormal(rs.CurveEndPoint(longest_side),rs.VectorCreate(point2,point1))
                        plane4 = rs.PlaneFromNormal(rs.CurveStartPoint(longest_side),rs.VectorCreate(point2,point1))
                        pointA = point3
                        pointB = rs.PlaneCurveIntersection(plane3,second_side)[0][1]

                    plane2 = rs.PlaneFromNormal(rs.CurveEndPoint(second_side),rs.VectorCreate(point2,point1))
                    if rs.PlaneCurveIntersection(plane2,longest_side):
                        pointC = point2
                        pointD = rs.PlaneCurveIntersection(plane2,longest_side)[0][1]
                    else:
                        point3 = rs.CurveStartPoint(longest_side)
                        point4 = rs.CurveEndPoint(longest_side)
                        plane3 = rs.PlaneFromNormal(rs.CurveStartPoint(longest_side),rs.VectorCreate(point2,point1))
                        plane4 = rs.PlaneFromNormal(rs.CurveEndPoint(longest_side),rs.VectorCreate(point2,point1))
                        pointC = point3
                        pointD = rs.PlaneCurveIntersection(plane3,second_side)[0][1]
                    #solve crossing polyline exception
                    polyline = rs.AddPolyline([pointA,pointB,pointC,pointD, pointA])
                    polyline_bis = rs.AddPolyline([pointA,pointB,pointD,pointC, pointA])
                    if  rs.CurveLength(polyline_bis) < rs.CurveLength(polyline):
                        polyline = polyline_bis
                    return polyline
                
                @staticmethod
                def insert_crossing_point(poly1, poly2):
                    """intersect two polylines and add intersection points to the first polyline."""

                    tolerance = 0.000001
                    params = []
                    points = rs.PolylineVertices(poly1)
                    inter = rs.CurveCurveIntersection(poly1, poly2)
                    
                    #get curve parameter
                    for i in range(len(points)):
                        params.append(rs.CurveClosestPoint(poly1, points[i]))

                    for i in range(len(inter)):
                        #check that this point is not already in the sequence
                        flag = True
                        for j in range(len(points)):
                            if rs.Distance(points[j], inter[i][1]) < tolerance:
                                flag = False
                        #find curve parameter
                        if flag is True:
                            params.append(rs.CurveClosestPoint(poly1, inter[i][1]))
                    
                    #sort parameters
                    params = sorted(params)
                    points = []
                    for i in range(len(params)):
                        points.append(rs.EvaluateCurve(poly1, params[i]))
                    return rs.AddPolyline(points)

                @staticmethod
                def polyline_half_zones(poly):
                    """
                    Divide a polyline in two using the axis linking endpoints. 
                    Each pieces is closed to shape a new polyline.
                    The new polylines are split in two list depending on their position to the axis.
                    """

                    # Axis creation
                    line = rs.AddLine(rs.CurveEndPoint(poly), rs.CurveStartPoint(poly))
                    # Add vertices at the intersection between the axis and the polyline
                    poly = Toolbox.Curves.insert_crossing_point(poly, line)

                    # Data
                    base_vec = rs.VectorCreate(rs.CurveEndPoint(poly), rs.CurveStartPoint(poly))
                    points = rs.PolylineVertices(poly)
                    normal = rs.CurveNormal(poly)
                    if normal[2] < 0 : normal = rs.VectorReverse(normal)
                    positive = []
                    negative = []
                    positive_points = []
                    negative_points = []
                    temp = []
                    temp.append(rs.CurveStartPoint(poly))
                    flag = 'Null'


                    for i in range(len(points)-1):
                        
                        # Use cross product to determine the position of the point in relation to the axis
                        test_vec = rs.VectorCreate(points[i+1], rs.CurveStartPoint(poly))
                        angle = rs.VectorAngle(base_vec, test_vec)
                        if angle > 0.01:
                            cross = rs.VectorUnitize(rs.VectorCrossProduct(base_vec, test_vec))
                        else: cross = None

                        # When the point is on the axis, close the polyline and initialize a new one
                        if cross == None:
                            temp.append(points[i+1])
                            temp.append(temp[0])
                            if flag == 'Pos': positive_points.append(temp)
                            if flag == 'Neg': negative_points.append(temp)
                            temp = []
                            flag = 'Null'
                        
                        # Change the flag value depending of the crossproduct result
                        elif rs.IsVectorParallelTo(cross, normal) == 1 :
                            flag = 'Pos'
                        elif rs.IsVectorParallelTo(cross, normal) == -1 :
                            flag = 'Neg'
                        else: raise Exception('Cross Product in Polyline half-zone got an unexpected result')

                        # Add this point to the temporary list
                        temp.append(points[i+1])

                    # Create polylines
                    if positive_points != []: 
                        for i in range(len(positive_points)):
                            positive.append(rs.AddPolyline(positive_points[i]))
                    if negative_points != []: 
                        for i in range(len(negative_points)):
                            negative.append(rs.AddPolyline(negative_points[i]))

                    return positive, negative
        
                @staticmethod
                def fillet_curves(c1, c2, radius, join=True):

                    c1 = rs.coercecurve(c1)
                    c2= rs.coercecurve(c2)
                    d1 = rs.Distance(rs.CurveStartPoint(c1), rs.CurveStartPoint(c2))
                    d2 = rs.Distance(rs.CurveEndPoint(c1), rs.CurveStartPoint(c2))
                    d3 = rs.Distance(rs.CurveEndPoint(c1), rs.CurveEndPoint(c2))
                    d4 = rs.Distance(rs.CurveStartPoint(c1), rs.CurveEndPoint(c2))
                    p1, p2 = rs.CurveStartPoint(c1), rs.CurveStartPoint(c2)
                    if d2 < d1: p1, p2 = rs.CurveEndPoint(c1), rs.CurveStartPoint(c2)
                    if d3 < d2 and d3 < d1: p1, p2 = rs.CurveEndPoint(c1), rs.CurveEndPoint(c2)
                    if d4 < d3 and d4 < d2 and d4 < d1:  p1, p2 = rs.CurveStartPoint(c1), rs.CurveEndPoint(c2)
                    
                    
                    return rg.Curve.CreateFilletCurves(c1, p1, c2, p2, radius, join,join, join, 0.001,0.001)[0]
                
                @staticmethod
                def connect_curves(c1,c2):
                    d1 = rs.Distance(rs.CurveStartPoint(c1), rs.CurveStartPoint(c2))
                    d2 = rs.Distance(rs.CurveStartPoint(c1), rs.CurveEndPoint(c2))
                    if d1 < d2:
                        l1 = rs.AddLine(rs.CurveStartPoint(c1), rs.CurveStartPoint(c2))
                        l2 = rs.AddLine(rs.CurveEndPoint(c1), rs.CurveEndPoint(c2))
                    else:
                        l1 = rs.AddLine(rs.CurveStartPoint(c1), rs.CurveEndPoint(c2))
                        l2 = rs.AddLine(rs.CurveEndPoint(c1), rs.CurveStartPoint(c2))
                    return rs.JoinCurves([c1,l1,c2,l2])[0]
        
                @staticmethod
                def trim_curve_with_curve(curve,cutter):
                    
                    param = rg.Intersect.Intersection.CurveCurve(curve,cutter,0.001,0.001).Item[0].ParameterA
                    return rg.Curve.Split(curve,param)[0]

                @staticmethod
                def sharingEdge(curve1, curve2):
                    curve1 = rs.coercecurve(curve1)
                    curve2 = rs.coercecurve(curve2)
                    srf1 = rg.Brep.CreatePlanarBreps(curve1)[0]
                    intbool, line1, points = rg.Intersect.Intersection.CurveBrep(curve2,srf1,0.1)
                    srf2 = rg.Brep.CreatePlanarBreps(curve2)[0]
                    intbool, line2, points = rg.Intersect.Intersection.CurveBrep(curve1,srf2,0.1)
                    if len(line1) == 1 and len(line2) == 1:
                        return line2
                    else: return None


            class Planes:

                @staticmethod
                def is_plane_in_plane(plane1, plane2):
                    """check if planes are parallel and in each other planes"""
                    
                    flag = False
                    # normal should be parallel
                    if abs(rs.IsVectorParallelTo(plane1.ZAxis, plane2.ZAxis)) == 1:
                        # trivial case where origins are the same
                        if rs.Distance(plane1.Origin, plane2.Origin) < 0.00001 : flag = True
                        # check if the translation from frame to frame is in the plane
                        else:
                            vec = rs.VectorUnitize(rs.VectorCreate(plane2.Origin, plane1.Origin))
                            test = rs.VectorCrossProduct(vec, plane1.XAxis)
                            if abs(rs.IsVectorParallelTo(test, plane1.ZAxis)) == 1 or str(Toolbox.Vectors.round_vector(test,6)) == '0,0,0' : flag = True
                            
                    return flag

                @staticmethod
                def orient(object, ref, target):
                    transform = rg.Transform.PlaneToPlane(ref, target)
                    return scriptcontext.doc.Objects.Transform(object, transform, False)
            

            class Vectors:
                
                @staticmethod
                def average_vector(vectors, cull_dup=False):
                    """average a list of vectors"""
                    
                    if cull_dup == True:
                        vectors = Toolbox.Vectors.cull_dup(vectors)

                    l = len(vectors)
                    x = 0
                    y = 0
                    z = 0
                    for i in range(l):
                        x += vectors[i][0]
                        y += vectors[i][1]
                        z += vectors[i][2]
                    x = x/l
                    y = y/l
                    z = z/l
                    return rs.VectorCreate((x,y,z),(0,0,0))
                
                @staticmethod
                def cull_dup(vectors):  
                    """cull duplicate vectors in a list"""            
                    unique_vec = []
                    for i in range(len(vectors)):
                        add = True
                        for j in range(i):
                            v1 = Toolbox.Vectors.round_vector(vectors[i], n=3)
                            v2 = Toolbox.Vectors.round_vector(vectors[j], n=3)
                            if v1 == v2: add=False
                        if add == True: unique_vec.append(vectors[i])
                    return unique_vec

                @staticmethod
                def project_vector_to_plane(vector,plane):
                    """project a vector to a plane by projecting a line on a disk"""
                    center = plane.Origin
                    line = rs.AddLine(center,rs.CopyObject(center,vector))
                    disk = rs.AddPlanarSrf(rs.AddCircle(plane,2*rs.VectorLength(vector)))
                    direction = -rs.SurfaceNormal(disk,[0,0])
                    rounded_vec = Toolbox.Vectors.round_vector(vector)
                    rounded_dir = Toolbox.Vectors.round_vector(direction)
                    if rounded_vec != rounded_dir and rounded_vec != -rounded_dir:
                        projection = rs.ProjectCurveToSurface(line,disk,direction)
                        new_vector=rs.VectorUnitize(rs.VectorCreate(rs.CurveEndPoint(projection),rs.CurveStartPoint(projection)))
                        return new_vector
                    else: return vector

                @staticmethod
                def line_to_vec(line, unitize=False):
                    """get a vector from a line"""
                    vec = rs.VectorCreate(rs.CurveEndPoint(line),rs.CurveStartPoint(line))
                    if unitize is True:
                        vec = rs.VectorUnitize(vec)
                    return vec

                @staticmethod
                def is_vector_outward(center, vector_location, vector):
                    """ check if a vector points toward a center point or outward """
                    testpoint = rs.CopyObject(vector_location,rs.VectorUnitize(vector)*0.01)
                    if rs.Distance(center,testpoint) < rs.Distance(center,vector_location):
                        return False
                    if rs.Distance(center,testpoint) > rs.Distance(center,vector_location):
                        return True 
                    else: raise Exception("is_vector_outward cannot compute because vector is tangent to circle")

                @staticmethod
                def round_vector(vector, n=3):
                    """round x,y,z components of a vector to n decimals"""
                    vec = copy.deepcopy(vector)
                    for i in range(len(vec)):
                        vec[i] = round(vec[i],n)
                    return vec

                @staticmethod
                def cross(a, b):
                    """simple cross product between two vectors"""
                    c = [a[1]*b[2] - a[2]*b[1],
                        a[2]*b[0] - a[0]*b[2],
                        a[0]*b[1] - a[1]*b[0]]
                    return c

                @staticmethod
                def isvectornull(vector):
                    """check if a vector is null or close to (0,0,0)"""
                    state = True
                    for i in range(len(vector)):
                        if Toolbox.Numbers.isclose(vector[i],0, rel_tol=1e-06, abs_tol=1e-06) is False:
                            state = False
                    return state


            class Points:

                @staticmethod
                def average_point(points):
                    """average a list of points"""
                    l = len(points)
                    x = 0
                    y = 0
                    z = 0
                    for i in range(l):
                        x += points[i][0]
                        y += points[i][1]
                        z += points[i][2]
                    x = x/l
                    y = y/l
                    z = z/l
                    return rs.AddPoint(x,y,z)
                
                @staticmethod
                def project_point_to_plane(point, plane, direction):
                    """project a point to a plane"""
                    line = [rs.CopyObject(point, direction), point]
                    intersect = rs.LinePlaneIntersection(line, plane)
                    return intersect

                @staticmethod
                def geodesic_sphere_points():
                    points = [[-0.850650787354,-0.525731086731,0.0],
                        [0.850650787354,-0.525731086731,0.0],
                        [-0.850650787354,0.525731086731,0.0],
                        [0.850650787354,0.525731086731,0.0],
                        [0.0,-0.850650787354,-0.525731086731],
                        [0.0,0.850650787354,-0.525731086731],
                        [0.0,-0.850650787354,0.525731086731],
                        [0.0,0.850650787354,0.525731086731],
                        [-0.525731086731,0.0,-0.850650787354],
                        [-0.525731086731,0.0,0.850650787354],
                        [0.525731086731,0.0,-0.850650787354],
                        [0.525731086731,0.0,0.850650787354],
                        [-0.5,-0.809017002583,0.309017002583],
                        [0.0,-1.0,0.0],
                        [-0.5,-0.809017002583,-0.309017002583],
                        [-0.309017002583,-0.5,0.809017002583],
                        [-0.5,-0.809017002583,0.309017002583],
                        [-0.809017002583,-0.309017002583,0.5],
                        [-0.309017002583,-0.5,0.809017002583],
                        [0.0,0.0,1.0],
                        [0.309017002583,-0.5,0.809017002583],
                        [0.309017002583,-0.5,0.809017002583],
                        [0.809017002583,-0.309017002583,0.5],
                        [0.5,-0.809017002583,0.309017002583],
                        [0.5,-0.809017002583,-0.309017002583],
                        [0.0,-1.0,0.0],
                        [0.5,-0.809017002583,0.309017002583],
                        [-0.5,-0.809017002583,-0.309017002583],
                        [-0.309017002583,-0.5,-0.809017002583],
                        [-0.809017002583,-0.309017002583,-0.5],
                        [0.5,-0.809017002583,-0.309017002583],
                        [0.809017002583,-0.309017002583,-0.5],
                        [0.309017002583,-0.5,-0.809017002583],
                        [0.0,0.0,-1.0],
                        [-0.309017002583,-0.5,-0.809017002583],
                        [0.309017002583,-0.5,-0.809017002583],
                        [-1.0,0.0,0.0],
                        [-0.809017002583,0.309017002583,-0.5],
                        [-0.809017002583,-0.309017002583,-0.5],
                        [-0.5,0.809017002583,-0.309017002583],
                        [-0.309017002583,0.5,-0.809017002583],
                        [-0.809017002583,0.309017002583,-0.5],
                        [0.0,0.0,-1.0],
                        [-0.309017002583,0.5,-0.809017002583],
                        [0.309017002583,0.5,-0.809017002583],
                        [0.309017002583,0.5,-0.809017002583],
                        [0.5,0.809017002583,-0.309017002583],
                        [0.809017002583,0.309017002583,-0.5],
                        [0.5,0.809017002583,-0.309017002583],
                        [0.0,1.0,0.0],
                        [0.5,0.809017002583,0.309017002583],
                        [0.5,0.809017002583,0.309017002583],
                        [0.309017002583,0.5,0.809017002583],
                        [0.809017002583,0.309017002583,0.5],
                        [1.0,0.0,0.0],
                        [0.809017002583,0.309017002583,0.5],
                        [0.809017002583,-0.309017002583,0.5],
                        [-0.809017002583,0.309017002583,0.5],
                        [-1.0,0.0,0.0],
                        [-0.809017002583,-0.309017002583,0.5],
                        [-0.309017002583,0.5,0.809017002583],
                        [-0.5,0.809017002583,0.309017002583],
                        [-0.809017002583,0.309017002583,0.5],
                        [-0.309017002583,0.5,0.809017002583],
                        [0.0,0.0,1.0],
                        [0.309017002583,0.5,0.809017002583],
                        [-0.5,0.809017002583,-0.309017002583],
                        [-0.5,0.809017002583,0.309017002583],
                        [0.0,1.0,0.0],
                        [0.809017002583,0.309017002583,-0.5],
                        [1.0,0.0,0.0],
                        [0.809017002583,-0.309017002583,-0.5],
                        [-0.71656692028,-0.681718349457,0.147620901465],
                        [-0.525731086731,-0.850650787354,0.0],
                        [-0.71656692028,-0.681718349457,-0.147620901465],
                        [-0.238855645061,-0.864187836647,0.442862719297],
                        [0.0,-0.955422580242,0.295241802931],
                        [-0.262865543365,-0.951056540012,0.162459850311],
                        [-0.262865543365,-0.951056540012,-0.162459850311],
                        [0.0,-0.955422580242,-0.295241802931],
                        [-0.238855645061,-0.864187836647,-0.442862719297],
                        [-0.262865543365,-0.951056540012,0.162459850311],
                        [-0.262865543365,-0.951056540012,-0.162459850311],
                        [-0.525731086731,-0.850650787354,0.0],
                        [-0.442862719297,-0.238855645061,0.864187836647],
                        [-0.587785243988,-0.425325393677,0.688190937042],
                        [-0.681718349457,-0.147620901465,0.71656692028],
                        [-0.147620901465,-0.71656692028,0.681718349457],
                        [-0.238855645061,-0.864187836647,0.442862719297],
                        [-0.425325393677,-0.688190937042,0.587785243988],
                        [-0.688190937042,-0.587785243988,0.425325393677],
                        [-0.71656692028,-0.681718349457,0.147620901465],
                        [-0.864187836647,-0.442862719297,0.238855645061],
                        [-0.425325393677,-0.688190937042,0.587785243988],
                        [-0.688190937042,-0.587785243988,0.425325393677],
                        [-0.587785243988,-0.425325393677,0.688190937042],
                        [-0.147620901465,-0.71656692028,0.681718349457],
                        [0.0,-0.525731086731,0.850650787354],
                        [0.147620901465,-0.71656692028,0.681718349457],
                        [-0.442862719297,-0.238855645061,0.864187836647],
                        [-0.295241802931,0.0,0.955422580242],
                        [-0.162459850311,-0.262865543365,0.951056540012],
                        [0.162459850311,-0.262865543365,0.951056540012],
                        [0.295241802931,0.0,0.955422580242],
                        [0.442862719297,-0.238855645061,0.864187836647],
                        [-0.162459850311,-0.262865543365,0.951056540012],
                        [0.162459850311,-0.262865543365,0.951056540012],
                        [0.0,-0.525731086731,0.850650787354],
                        [0.147620901465,-0.71656692028,0.681718349457],
                        [0.425325393677,-0.688190937042,0.587785243988],
                        [0.238855645061,-0.864187836647,0.442862719297],
                        [0.442862719297,-0.238855645061,0.864187836647],
                        [0.681718349457,-0.147620901465,0.71656692028],
                        [0.587785243988,-0.425325393677,0.688190937042],
                        [0.688190937042,-0.587785243988,0.425325393677],
                        [0.864187836647,-0.442862719297,0.238855645061],
                        [0.71656692028,-0.681718349457,0.147620901465],
                        [0.587785243988,-0.425325393677,0.688190937042],
                        [0.688190937042,-0.587785243988,0.425325393677],
                        [0.425325393677,-0.688190937042,0.587785243988],
                        [0.71656692028,-0.681718349457,-0.147620901465],
                        [0.525731086731,-0.850650787354,0.0],
                        [0.71656692028,-0.681718349457,0.147620901465],
                        [0.238855645061,-0.864187836647,-0.442862719297],
                        [0.0,-0.955422580242,-0.295241802931],
                        [0.262865543365,-0.951056540012,-0.162459850311],
                        [0.262865543365,-0.951056540012,0.162459850311],
                        [0.0,-0.955422580242,0.295241802931],
                        [0.238855645061,-0.864187836647,0.442862719297],
                        [0.262865543365,-0.951056540012,-0.162459850311],
                        [0.262865543365,-0.951056540012,0.162459850311],
                        [0.525731086731,-0.850650787354,0.0],
                        [-0.71656692028,-0.681718349457,-0.147620901465],
                        [-0.688190937042,-0.587785243988,-0.425325393677],
                        [-0.864187836647,-0.442862719297,-0.238855645061],
                        [-0.238855645061,-0.864187836647,-0.442862719297],
                        [-0.147620901465,-0.71656692028,-0.681718349457],
                        [-0.425325393677,-0.688190937042,-0.587785243988],
                        [-0.587785243988,-0.425325393677,-0.688190937042],
                        [-0.442862719297,-0.238855645061,-0.864187836647],
                        [-0.681718349457,-0.147620901465,-0.71656692028],
                        [-0.425325393677,-0.688190937042,-0.587785243988],
                        [-0.587785243988,-0.425325393677,-0.688190937042],
                        [-0.688190937042,-0.587785243988,-0.425325393677],
                        [0.238855645061,-0.864187836647,-0.442862719297],
                        [0.425325393677,-0.688190937042,-0.587785243988],
                        [0.147620901465,-0.71656692028,-0.681718349457],
                        [0.71656692028,-0.681718349457,-0.147620901465],
                        [0.864187836647,-0.442862719297,-0.238855645061],
                        [0.688190937042,-0.587785243988,-0.425325393677],
                        [0.587785243988,-0.425325393677,-0.688190937042],
                        [0.681718349457,-0.147620901465,-0.71656692028],
                        [0.442862719297,-0.238855645061,-0.864187836647],
                        [0.688190937042,-0.587785243988,-0.425325393677],
                        [0.587785243988,-0.425325393677,-0.688190937042],
                        [0.425325393677,-0.688190937042,-0.587785243988],
                        [0.295241802931,0.0,-0.955422580242],
                        [0.162459850311,-0.262865543365,-0.951056540012],
                        [0.442862719297,-0.238855645061,-0.864187836647],
                        [-0.295241802931,0.0,-0.955422580242],
                        [-0.442862719297,-0.238855645061,-0.864187836647],
                        [-0.162459850311,-0.262865543365,-0.951056540012],
                        [0.0,-0.525731086731,-0.850650787354],
                        [-0.147620901465,-0.71656692028,-0.681718349457],
                        [0.147620901465,-0.71656692028,-0.681718349457],
                        [-0.162459850311,-0.262865543365,-0.951056540012],
                        [0.0,-0.525731086731,-0.850650787354],
                        [0.162459850311,-0.262865543365,-0.951056540012],
                        [-0.955422580242,-0.295241802931,0.0],
                        [-0.951056540012,-0.162459850311,-0.262865543365],
                        [-0.864187836647,-0.442862719297,-0.238855645061],
                        [-0.955422580242,0.295241802931,0.0],
                        [-0.864187836647,0.442862719297,-0.238855645061],
                        [-0.951056540012,0.162459850311,-0.262865543365],
                        [-0.850650787354,0.0,-0.525731086731],
                        [-0.681718349457,0.147620901465,-0.71656692028],
                        [-0.681718349457,-0.147620901465,-0.71656692028],
                        [-0.951056540012,0.162459850311,-0.262865543365],
                        [-0.850650787354,0.0,-0.525731086731],
                        [-0.951056540012,-0.162459850311,-0.262865543365],
                        [-0.71656692028,0.681718349457,-0.147620901465],
                        [-0.688190937042,0.587785243988,-0.425325393677],
                        [-0.864187836647,0.442862719297,-0.238855645061],
                        [-0.238855645061,0.864187836647,-0.442862719297],
                        [-0.147620901465,0.71656692028,-0.681718349457],
                        [-0.425325393677,0.688190937042,-0.587785243988],
                        [-0.587785243988,0.425325393677,-0.688190937042],
                        [-0.442862719297,0.238855645061,-0.864187836647],
                        [-0.681718349457,0.147620901465,-0.71656692028],
                        [-0.425325393677,0.688190937042,-0.587785243988],
                        [-0.587785243988,0.425325393677,-0.688190937042],
                        [-0.688190937042,0.587785243988,-0.425325393677],
                        [0.295241802931,0.0,-0.955422580242],
                        [0.162459850311,0.262865543365,-0.951056540012],
                        [0.442862719297,0.238855645061,-0.864187836647],
                        [-0.295241802931,0.0,-0.955422580242],
                        [-0.442862719297,0.238855645061,-0.864187836647],
                        [-0.162459850311,0.262865543365,-0.951056540012],
                        [0.0,0.525731086731,-0.850650787354],
                        [-0.147620901465,0.71656692028,-0.681718349457],
                        [0.147620901465,0.71656692028,-0.681718349457],
                        [-0.162459850311,0.262865543365,-0.951056540012],
                        [0.0,0.525731086731,-0.850650787354],
                        [0.162459850311,0.262865543365,-0.951056540012],
                        [0.442862719297,0.238855645061,-0.864187836647],
                        [0.587785243988,0.425325393677,-0.688190937042],
                        [0.681718349457,0.147620901465,-0.71656692028],
                        [0.147620901465,0.71656692028,-0.681718349457],
                        [0.238855645061,0.864187836647,-0.442862719297],
                        [0.425325393677,0.688190937042,-0.587785243988],
                        [0.688190937042,0.587785243988,-0.425325393677],
                        [0.71656692028,0.681718349457,-0.147620901465],
                        [0.864187836647,0.442862719297,-0.238855645061],
                        [0.425325393677,0.688190937042,-0.587785243988],
                        [0.688190937042,0.587785243988,-0.425325393677],
                        [0.587785243988,0.425325393677,-0.688190937042],
                        [0.71656692028,0.681718349457,-0.147620901465],
                        [0.525731086731,0.850650787354,0.0],
                        [0.71656692028,0.681718349457,0.147620901465],
                        [0.238855645061,0.864187836647,-0.442862719297],
                        [0.0,0.955422580242,-0.295241802931],
                        [0.262865543365,0.951056540012,-0.162459850311],
                        [0.262865543365,0.951056540012,0.162459850311],
                        [0.0,0.955422580242,0.295241802931],
                        [0.238855645061,0.864187836647,0.442862719297],
                        [0.262865543365,0.951056540012,-0.162459850311],
                        [0.262865543365,0.951056540012,0.162459850311],
                        [0.525731086731,0.850650787354,0.0],
                        [0.71656692028,0.681718349457,0.147620901465],
                        [0.688190937042,0.587785243988,0.425325393677],
                        [0.864187836647,0.442862719297,0.238855645061],
                        [0.238855645061,0.864187836647,0.442862719297],
                        [0.147620901465,0.71656692028,0.681718349457],
                        [0.425325393677,0.688190937042,0.587785243988],
                        [0.587785243988,0.425325393677,0.688190937042],
                        [0.442862719297,0.238855645061,0.864187836647],
                        [0.681718349457,0.147620901465,0.71656692028],
                        [0.425325393677,0.688190937042,0.587785243988],
                        [0.587785243988,0.425325393677,0.688190937042],
                        [0.688190937042,0.587785243988,0.425325393677],
                        [0.955422580242,-0.295241802931,0.0],
                        [0.951056540012,-0.162459850311,0.262865543365],
                        [0.864187836647,-0.442862719297,0.238855645061],
                        [0.955422580242,0.295241802931,0.0],
                        [0.864187836647,0.442862719297,0.238855645061],
                        [0.951056540012,0.162459850311,0.262865543365],
                        [0.850650787354,0.0,0.525731086731],
                        [0.681718349457,0.147620901465,0.71656692028],
                        [0.681718349457,-0.147620901465,0.71656692028],
                        [0.951056540012,0.162459850311,0.262865543365],
                        [0.850650787354,0.0,0.525731086731],
                        [0.951056540012,-0.162459850311,0.262865543365],
                        [-0.681718349457,0.147620901465,0.71656692028],
                        [-0.850650787354,0.0,0.525731086731],
                        [-0.681718349457,-0.147620901465,0.71656692028],
                        [-0.864187836647,0.442862719297,0.238855645061],
                        [-0.955422580242,0.295241802931,0.0],
                        [-0.951056540012,0.162459850311,0.262865543365],
                        [-0.951056540012,-0.162459850311,0.262865543365],
                        [-0.955422580242,-0.295241802931,0.0],
                        [-0.864187836647,-0.442862719297,0.238855645061],
                        [-0.951056540012,0.162459850311,0.262865543365],
                        [-0.951056540012,-0.162459850311,0.262865543365],
                        [-0.850650787354,0.0,0.525731086731],
                        [-0.442862719297,0.238855645061,0.864187836647],
                        [-0.587785243988,0.425325393677,0.688190937042],
                        [-0.681718349457,0.147620901465,0.71656692028],
                        [-0.147620901465,0.71656692028,0.681718349457],
                        [-0.238855645061,0.864187836647,0.442862719297],
                        [-0.425325393677,0.688190937042,0.587785243988],
                        [-0.688190937042,0.587785243988,0.425325393677],
                        [-0.71656692028,0.681718349457,0.147620901465],
                        [-0.864187836647,0.442862719297,0.238855645061],
                        [-0.425325393677,0.688190937042,0.587785243988],
                        [-0.688190937042,0.587785243988,0.425325393677],
                        [-0.587785243988,0.425325393677,0.688190937042],
                        [-0.147620901465,0.71656692028,0.681718349457],
                        [0.0,0.525731086731,0.850650787354],
                        [0.147620901465,0.71656692028,0.681718349457],
                        [-0.442862719297,0.238855645061,0.864187836647],
                        [-0.295241802931,0.0,0.955422580242],
                        [-0.162459850311,0.262865543365,0.951056540012],
                        [0.162459850311,0.262865543365,0.951056540012],
                        [0.295241802931,0.0,0.955422580242],
                        [0.442862719297,0.238855645061,0.864187836647],
                        [-0.162459850311,0.262865543365,0.951056540012],
                        [0.162459850311,0.262865543365,0.951056540012],
                        [0.0,0.525731086731,0.850650787354],
                        [-0.238855645061,0.864187836647,-0.442862719297],
                        [-0.262865543365,0.951056540012,-0.162459850311],
                        [0.0,0.955422580242,-0.295241802931],
                        [-0.71656692028,0.681718349457,-0.147620901465],
                        [-0.71656692028,0.681718349457,0.147620901465],
                        [-0.525731086731,0.850650787354,0.0],
                        [-0.262865543365,0.951056540012,0.162459850311],
                        [-0.238855645061,0.864187836647,0.442862719297],
                        [0.0,0.955422580242,0.295241802931],
                        [-0.525731086731,0.850650787354,0.0],
                        [-0.262865543365,0.951056540012,0.162459850311],
                        [-0.262865543365,0.951056540012,-0.162459850311],
                        [0.681718349457,0.147620901465,-0.71656692028],
                        [0.850650787354,0.0,-0.525731086731],
                        [0.681718349457,-0.147620901465,-0.71656692028],
                        [0.864187836647,0.442862719297,-0.238855645061],
                        [0.955422580242,0.295241802931,0.0],
                        [0.951056540012,0.162459850311,-0.262865543365],
                        [0.951056540012,-0.162459850311,-0.262865543365],
                        [0.955422580242,-0.295241802931,0.0],
                        [0.864187836647,-0.442862719297,-0.238855645061],
                        [0.951056540012,0.162459850311,-0.262865543365],
                        [0.951056540012,-0.162459850311,-0.262865543365],
                        [0.850650787354,0.0,-0.525731086731],
                        [-0.793863236904,-0.604043483734,0.070090636611],
                        [-0.724504590034,-0.689269959927,0.0],
                        [-0.793863236904,-0.604043483734,-0.070090636611],
                        [-0.617670714855,-0.752343893051,0.229044884443],
                        [-0.518927633762,-0.839642524719,0.16035746038],
                        [-0.632596552372,-0.770524084568,0.0781932324171],
                        [-0.632596552372,-0.770524084568,-0.0781932324171],
                        [-0.518927633762,-0.839642524719,-0.16035746038],
                        [-0.617670714855,-0.752343893051,-0.229044884443],
                        [-0.632596552372,-0.770524084568,0.0781932324171],
                        [-0.632596552372,-0.770524084568,-0.0781932324171],
                        [-0.724504590034,-0.689269959927,0.0],
                        [-0.370602428913,-0.846715569496,0.381741464138],
                        [-0.253038614988,-0.915502369404,0.312772929668],
                        [-0.389195710421,-0.889195740223,0.240536183119],
                        [-0.113409027457,-0.863953828812,0.490634441376],
                        [0.0,-0.907272219658,0.420543789864],
                        [-0.120750762522,-0.919883430004,0.373140364885],
                        [-0.126519307494,-0.963828444481,0.234579697251],
                        [0.0,-0.988273143768,0.152696594596],
                        [-0.129731908441,-0.988302052021,0.0801787301898],
                        [-0.120750762522,-0.919883430004,0.373140364885],
                        [-0.126519307494,-0.963828444481,0.234579697251],
                        [-0.253038614988,-0.915502369404,0.312772929668],
                        [-0.389195710421,-0.889195740223,-0.240536183119],
                        [-0.253038614988,-0.915502369404,-0.312772929668],
                        [-0.370602428913,-0.846715569496,-0.381741464138],
                        [-0.129731908441,-0.988302052021,-0.0801787301898],
                        [0.0,-0.988273143768,-0.152696594596],
                        [-0.126519307494,-0.963828444481,-0.234579697251],
                        [-0.120750762522,-0.919883430004,-0.373140364885],
                        [0.0,-0.907272219658,-0.420543789864],
                        [-0.113409027457,-0.863953828812,-0.490634441376],
                        [-0.126519307494,-0.963828444481,-0.234579697251],
                        [-0.120750762522,-0.919883430004,-0.373140364885],
                        [-0.253038614988,-0.915502369404,-0.312772929668],
                        [-0.389195710421,-0.889195740223,0.240536183119],
                        [-0.39960706234,-0.912982463837,0.0823235809803],
                        [-0.518927633762,-0.839642524719,0.16035746038],
                        [-0.129731908441,-0.988302052021,0.0801787301898],
                        [-0.129731908441,-0.988302052021,-0.0801787301898],
                        [-0.266404688358,-0.96386128664,0.0],
                        [-0.39960706234,-0.912982463837,-0.0823235809803],
                        [-0.389195710421,-0.889195740223,-0.240536183119],
                        [-0.518927633762,-0.839642524719,-0.16035746038],
                        [-0.266404688358,-0.96386128664,0.0],
                        [-0.39960706234,-0.912982463837,-0.0823235809803],
                        [-0.39960706234,-0.912982463837,0.0823235809803],
                        [-0.490634441376,-0.113409027457,0.863953828812],
                        [-0.568519234657,-0.19537883997,0.79913264513],
                        [-0.604043483734,-0.070090636611,0.793863236904],
                        [-0.381741464138,-0.370602428913,0.846715569496],
                        [-0.450446814299,-0.469374448061,0.759463787079],
                        [-0.517485499382,-0.331231862307,0.788983047009],
                        [-0.644004821777,-0.28290578723,0.71078979969],
                        [-0.70991063118,-0.370268076658,0.599106371403],
                        [-0.752343893051,-0.229044884443,0.617670714855],
                        [-0.517485499382,-0.331231862307,0.788983047009],
                        [-0.644004821777,-0.28290578723,0.71078979969],
                        [-0.568519234657,-0.19537883997,0.79913264513],
                        [-0.229044884443,-0.617670714855,0.752343893051],
                        [-0.28290578723,-0.71078979969,0.644004821777],
                        [-0.370268076658,-0.599106371403,0.70991063118],
                        [-0.070090636611,-0.793863236904,0.604043483734],
                        [-0.113409027457,-0.863953828812,0.490634441376],
                        [-0.19537883997,-0.79913264513,0.568519234657],
                        [-0.331231862307,-0.788983047009,0.517485499382],
                        [-0.370602428913,-0.846715569496,0.381741464138],
                        [-0.469374448061,-0.759463787079,0.450446814299],
                        [-0.19537883997,-0.79913264513,0.568519234657],
                        [-0.331231862307,-0.788983047009,0.517485499382],
                        [-0.28290578723,-0.71078979969,0.644004821777],
                        [-0.759463787079,-0.450446814299,0.469374448061],
                        [-0.788983047009,-0.517485499382,0.331231862307],
                        [-0.846715569496,-0.381741464138,0.370602428913],
                        [-0.599106371403,-0.70991063118,0.370268076658],
                        [-0.617670714855,-0.752343893051,0.229044884443],
                        [-0.71078979969,-0.644004821777,0.28290578723],
                        [-0.79913264513,-0.568519234657,0.19537883997],
                        [-0.793863236904,-0.604043483734,0.070090636611],
                        [-0.863953828812,-0.490634441376,0.113409027457],
                        [-0.71078979969,-0.644004821777,0.28290578723],
                        [-0.79913264513,-0.568519234657,0.19537883997],
                        [-0.788983047009,-0.517485499382,0.331231862307],
                        [-0.370268076658,-0.599106371403,0.70991063118],
                        [-0.513375461102,-0.5642542243,0.646577775478],
                        [-0.450446814299,-0.469374448061,0.759463787079],
                        [-0.469374448061,-0.759463787079,0.450446814299],
                        [-0.599106371403,-0.70991063118,0.370268076658],
                        [-0.5642542243,-0.646577775478,0.513375461102],
                        [-0.646577775478,-0.513375461102,0.5642542243],
                        [-0.759463787079,-0.450446814299,0.469374448061],
                        [-0.70991063118,-0.370268076658,0.599106371403],
                        [-0.5642542243,-0.646577775478,0.513375461102],
                        [-0.646577775478,-0.513375461102,0.5642542243],
                        [-0.513375461102,-0.5642542243,0.646577775478],
                        [-0.070090636611,-0.793863236904,0.604043483734],
                        [0.0,-0.724504590034,0.689269959927],
                        [0.070090636611,-0.793863236904,0.604043483734],
                        [-0.229044884443,-0.617670714855,0.752343893051],
                        [-0.16035746038,-0.518927633762,0.839642524719],
                        [-0.0781932324171,-0.632596552372,0.770524084568],
                        [0.0781932324171,-0.632596552372,0.770524084568],
                        [0.16035746038,-0.518927633762,0.839642524719],
                        [0.229044884443,-0.617670714855,0.752343893051],
                        [-0.0781932324171,-0.632596552372,0.770524084568],
                        [0.0781932324171,-0.632596552372,0.770524084568],
                        [0.0,-0.724504590034,0.689269959927],
                        [-0.381741464138,-0.370602428913,0.846715569496],
                        [-0.312772929668,-0.253038614988,0.915502369404],
                        [-0.240536183119,-0.389195710421,0.889195740223],
                        [-0.490634441376,-0.113409027457,0.863953828812],
                        [-0.420543789864,0.0,0.907272219658],
                        [-0.373140364885,-0.120750762522,0.919883430004],
                        [-0.234579697251,-0.126519307494,0.963828444481],
                        [-0.152696594596,0.0,0.988273143768],
                        [-0.0801787301898,-0.129731908441,0.988302052021],
                        [-0.373140364885,-0.120750762522,0.919883430004],
                        [-0.234579697251,-0.126519307494,0.963828444481],
                        [-0.312772929668,-0.253038614988,0.915502369404],
                        [0.240536183119,-0.389195710421,0.889195740223],
                        [0.312772929668,-0.253038614988,0.915502369404],
                        [0.381741464138,-0.370602428913,0.846715569496],
                        [0.0801787301898,-0.129731908441,0.988302052021],
                        [0.152696594596,0.0,0.988273143768],
                        [0.234579697251,-0.126519307494,0.963828444481],
                        [0.373140364885,-0.120750762522,0.919883430004],
                        [0.420543789864,0.0,0.907272219658],
                        [0.490634441376,-0.113409027457,0.863953828812],
                        [0.234579697251,-0.126519307494,0.963828444481],
                        [0.373140364885,-0.120750762522,0.919883430004],
                        [0.312772929668,-0.253038614988,0.915502369404],
                        [-0.240536183119,-0.389195710421,0.889195740223],
                        [-0.0823235809803,-0.39960706234,0.912982463837],
                        [-0.16035746038,-0.518927633762,0.839642524719],
                        [-0.0801787301898,-0.129731908441,0.988302052021],
                        [0.0801787301898,-0.129731908441,0.988302052021],
                        [0.0,-0.266404688358,0.96386128664],
                        [0.0823235809803,-0.39960706234,0.912982463837],
                        [0.240536183119,-0.389195710421,0.889195740223],
                        [0.16035746038,-0.518927633762,0.839642524719],
                        [0.0,-0.266404688358,0.96386128664],
                        [0.0823235809803,-0.39960706234,0.912982463837],
                        [-0.0823235809803,-0.39960706234,0.912982463837],
                        [0.070090636611,-0.793863236904,0.604043483734],
                        [0.19537883997,-0.79913264513,0.568519234657],
                        [0.113409027457,-0.863953828812,0.490634441376],
                        [0.229044884443,-0.617670714855,0.752343893051],
                        [0.370268076658,-0.599106371403,0.70991063118],
                        [0.28290578723,-0.71078979969,0.644004821777],
                        [0.331231862307,-0.788983047009,0.517485499382],
                        [0.469374448061,-0.759463787079,0.450446814299],
                        [0.370602428913,-0.846715569496,0.381741464138],
                        [0.28290578723,-0.71078979969,0.644004821777],
                        [0.331231862307,-0.788983047009,0.517485499382],
                        [0.19537883997,-0.79913264513,0.568519234657],
                        [0.381741464138,-0.370602428913,0.846715569496],
                        [0.517485499382,-0.331231862307,0.788983047009],
                        [0.450446814299,-0.469374448061,0.759463787079],
                        [0.490634441376,-0.113409027457,0.863953828812],
                        [0.604043483734,-0.070090636611,0.793863236904],
                        [0.568519234657,-0.19537883997,0.79913264513],
                        [0.644004821777,-0.28290578723,0.71078979969],
                        [0.752343893051,-0.229044884443,0.617670714855],
                        [0.70991063118,-0.370268076658,0.599106371403],
                        [0.568519234657,-0.19537883997,0.79913264513],
                        [0.644004821777,-0.28290578723,0.71078979969],
                        [0.517485499382,-0.331231862307,0.788983047009],
                        [0.599106371403,-0.70991063118,0.370268076658],
                        [0.71078979969,-0.644004821777,0.28290578723],
                        [0.617670714855,-0.752343893051,0.229044884443],
                        [0.759463787079,-0.450446814299,0.469374448061],
                        [0.846715569496,-0.381741464138,0.370602428913],
                        [0.788983047009,-0.517485499382,0.331231862307],
                        [0.79913264513,-0.568519234657,0.19537883997],
                        [0.863953828812,-0.490634441376,0.113409027457],
                        [0.793863236904,-0.604043483734,0.070090636611],
                        [0.788983047009,-0.517485499382,0.331231862307],
                        [0.79913264513,-0.568519234657,0.19537883997],
                        [0.71078979969,-0.644004821777,0.28290578723],
                        [0.450446814299,-0.469374448061,0.759463787079],
                        [0.513375461102,-0.5642542243,0.646577775478],
                        [0.370268076658,-0.599106371403,0.70991063118],
                        [0.70991063118,-0.370268076658,0.599106371403],
                        [0.759463787079,-0.450446814299,0.469374448061],
                        [0.646577775478,-0.513375461102,0.5642542243],
                        [0.5642542243,-0.646577775478,0.513375461102],
                        [0.599106371403,-0.70991063118,0.370268076658],
                        [0.469374448061,-0.759463787079,0.450446814299],
                        [0.646577775478,-0.513375461102,0.5642542243],
                        [0.5642542243,-0.646577775478,0.513375461102],
                        [0.513375461102,-0.5642542243,0.646577775478],
                        [0.793863236904,-0.604043483734,-0.070090636611],
                        [0.724504590034,-0.689269959927,0.0],
                        [0.793863236904,-0.604043483734,0.070090636611],
                        [0.617670714855,-0.752343893051,-0.229044884443],
                        [0.518927633762,-0.839642524719,-0.16035746038],
                        [0.632596552372,-0.770524084568,-0.0781932324171],
                        [0.632596552372,-0.770524084568,0.0781932324171],
                        [0.518927633762,-0.839642524719,0.16035746038],
                        [0.617670714855,-0.752343893051,0.229044884443],
                        [0.632596552372,-0.770524084568,-0.0781932324171],
                        [0.632596552372,-0.770524084568,0.0781932324171],
                        [0.724504590034,-0.689269959927,0.0],
                        [0.370602428913,-0.846715569496,-0.381741464138],
                        [0.253038614988,-0.915502369404,-0.312772929668],
                        [0.389195710421,-0.889195740223,-0.240536183119],
                        [0.113409027457,-0.863953828812,-0.490634441376],
                        [0.0,-0.907272219658,-0.420543789864],
                        [0.120750762522,-0.919883430004,-0.373140364885],
                        [0.126519307494,-0.963828444481,-0.234579697251],
                        [0.0,-0.988273143768,-0.152696594596],
                        [0.129731908441,-0.988302052021,-0.0801787301898],
                        [0.120750762522,-0.919883430004,-0.373140364885],
                        [0.126519307494,-0.963828444481,-0.234579697251],
                        [0.253038614988,-0.915502369404,-0.312772929668],
                        [0.389195710421,-0.889195740223,0.240536183119],
                        [0.253038614988,-0.915502369404,0.312772929668],
                        [0.370602428913,-0.846715569496,0.381741464138],
                        [0.129731908441,-0.988302052021,0.0801787301898],
                        [0.0,-0.988273143768,0.152696594596],
                        [0.126519307494,-0.963828444481,0.234579697251],
                        [0.120750762522,-0.919883430004,0.373140364885],
                        [0.0,-0.907272219658,0.420543789864],
                        [0.113409027457,-0.863953828812,0.490634441376],
                        [0.126519307494,-0.963828444481,0.234579697251],
                        [0.120750762522,-0.919883430004,0.373140364885],
                        [0.253038614988,-0.915502369404,0.312772929668],
                        [0.389195710421,-0.889195740223,-0.240536183119],
                        [0.39960706234,-0.912982463837,-0.0823235809803],
                        [0.518927633762,-0.839642524719,-0.16035746038],
                        [0.129731908441,-0.988302052021,-0.0801787301898],
                        [0.129731908441,-0.988302052021,0.0801787301898],
                        [0.266404688358,-0.96386128664,0.0],
                        [0.39960706234,-0.912982463837,0.0823235809803],
                        [0.389195710421,-0.889195740223,0.240536183119],
                        [0.518927633762,-0.839642524719,0.16035746038],
                        [0.266404688358,-0.96386128664,0.0],
                        [0.39960706234,-0.912982463837,0.0823235809803],
                        [0.39960706234,-0.912982463837,-0.0823235809803],
                        [-0.793863236904,-0.604043483734,-0.070090636611],
                        [-0.79913264513,-0.568519234657,-0.19537883997],
                        [-0.863953828812,-0.490634441376,-0.113409027457],
                        [-0.617670714855,-0.752343893051,-0.229044884443],
                        [-0.599106371403,-0.70991063118,-0.370268076658],
                        [-0.71078979969,-0.644004821777,-0.28290578723],
                        [-0.788983047009,-0.517485499382,-0.331231862307],
                        [-0.759463787079,-0.450446814299,-0.469374448061],
                        [-0.846715569496,-0.381741464138,-0.370602428913],
                        [-0.71078979969,-0.644004821777,-0.28290578723],
                        [-0.788983047009,-0.517485499382,-0.331231862307],
                        [-0.79913264513,-0.568519234657,-0.19537883997],
                        [-0.370602428913,-0.846715569496,-0.381741464138],
                        [-0.331231862307,-0.788983047009,-0.517485499382],
                        [-0.469374448061,-0.759463787079,-0.450446814299],
                        [-0.113409027457,-0.863953828812,-0.490634441376],
                        [-0.070090636611,-0.793863236904,-0.604043483734],
                        [-0.19537883997,-0.79913264513,-0.568519234657],
                        [-0.28290578723,-0.71078979969,-0.644004821777],
                        [-0.229044884443,-0.617670714855,-0.752343893051],
                        [-0.370268076658,-0.599106371403,-0.70991063118],
                        [-0.19537883997,-0.79913264513,-0.568519234657],
                        [-0.28290578723,-0.71078979969,-0.644004821777],
                        [-0.331231862307,-0.788983047009,-0.517485499382],
                        [-0.70991063118,-0.370268076658,-0.599106371403],
                        [-0.644004821777,-0.28290578723,-0.71078979969],
                        [-0.752343893051,-0.229044884443,-0.617670714855],
                        [-0.450446814299,-0.469374448061,-0.759463787079],
                        [-0.381741464138,-0.370602428913,-0.846715569496],
                        [-0.517485499382,-0.331231862307,-0.788983047009],
                        [-0.568519234657,-0.19537883997,-0.79913264513],
                        [-0.490634441376,-0.113409027457,-0.863953828812],
                        [-0.604043483734,-0.070090636611,-0.793863236904],
                        [-0.517485499382,-0.331231862307,-0.788983047009],
                        [-0.568519234657,-0.19537883997,-0.79913264513],
                        [-0.644004821777,-0.28290578723,-0.71078979969],
                        [-0.469374448061,-0.759463787079,-0.450446814299],
                        [-0.5642542243,-0.646577775478,-0.513375461102],
                        [-0.599106371403,-0.70991063118,-0.370268076658],
                        [-0.370268076658,-0.599106371403,-0.70991063118],
                        [-0.450446814299,-0.469374448061,-0.759463787079],
                        [-0.513375461102,-0.5642542243,-0.646577775478],
                        [-0.646577775478,-0.513375461102,-0.5642542243],
                        [-0.70991063118,-0.370268076658,-0.599106371403],
                        [-0.759463787079,-0.450446814299,-0.469374448061],
                        [-0.513375461102,-0.5642542243,-0.646577775478],
                        [-0.646577775478,-0.513375461102,-0.5642542243],
                        [-0.5642542243,-0.646577775478,-0.513375461102],
                        [0.113409027457,-0.863953828812,-0.490634441376],
                        [0.19537883997,-0.79913264513,-0.568519234657],
                        [0.070090636611,-0.793863236904,-0.604043483734],
                        [0.370602428913,-0.846715569496,-0.381741464138],
                        [0.469374448061,-0.759463787079,-0.450446814299],
                        [0.331231862307,-0.788983047009,-0.517485499382],
                        [0.28290578723,-0.71078979969,-0.644004821777],
                        [0.370268076658,-0.599106371403,-0.70991063118],
                        [0.229044884443,-0.617670714855,-0.752343893051],
                        [0.331231862307,-0.788983047009,-0.517485499382],
                        [0.28290578723,-0.71078979969,-0.644004821777],
                        [0.19537883997,-0.79913264513,-0.568519234657],
                        [0.617670714855,-0.752343893051,-0.229044884443],
                        [0.71078979969,-0.644004821777,-0.28290578723],
                        [0.599106371403,-0.70991063118,-0.370268076658],
                        [0.793863236904,-0.604043483734,-0.070090636611],
                        [0.863953828812,-0.490634441376,-0.113409027457],
                        [0.79913264513,-0.568519234657,-0.19537883997],
                        [0.788983047009,-0.517485499382,-0.331231862307],
                        [0.846715569496,-0.381741464138,-0.370602428913],
                        [0.759463787079,-0.450446814299,-0.469374448061],
                        [0.79913264513,-0.568519234657,-0.19537883997],
                        [0.788983047009,-0.517485499382,-0.331231862307],
                        [0.71078979969,-0.644004821777,-0.28290578723],
                        [0.450446814299,-0.469374448061,-0.759463787079],
                        [0.517485499382,-0.331231862307,-0.788983047009],
                        [0.381741464138,-0.370602428913,-0.846715569496],
                        [0.70991063118,-0.370268076658,-0.599106371403],
                        [0.752343893051,-0.229044884443,-0.617670714855],
                        [0.644004821777,-0.28290578723,-0.71078979969],
                        [0.568519234657,-0.19537883997,-0.79913264513],
                        [0.604043483734,-0.070090636611,-0.793863236904],
                        [0.490634441376,-0.113409027457,-0.863953828812],
                        [0.644004821777,-0.28290578723,-0.71078979969],
                        [0.568519234657,-0.19537883997,-0.79913264513],
                        [0.517485499382,-0.331231862307,-0.788983047009],
                        [0.599106371403,-0.70991063118,-0.370268076658],
                        [0.5642542243,-0.646577775478,-0.513375461102],
                        [0.469374448061,-0.759463787079,-0.450446814299],
                        [0.759463787079,-0.450446814299,-0.469374448061],
                        [0.70991063118,-0.370268076658,-0.599106371403],
                        [0.646577775478,-0.513375461102,-0.5642542243],
                        [0.513375461102,-0.5642542243,-0.646577775478],
                        [0.450446814299,-0.469374448061,-0.759463787079],
                        [0.370268076658,-0.599106371403,-0.70991063118],
                        [0.646577775478,-0.513375461102,-0.5642542243],
                        [0.513375461102,-0.5642542243,-0.646577775478],
                        [0.5642542243,-0.646577775478,-0.513375461102],
                        [0.420543789864,0.0,-0.907272219658],
                        [0.373140364885,-0.120750762522,-0.919883430004],
                        [0.490634441376,-0.113409027457,-0.863953828812],
                        [0.152696594596,0.0,-0.988273143768],
                        [0.0801787301898,-0.129731908441,-0.988302052021],
                        [0.234579697251,-0.126519307494,-0.963828444481],
                        [0.312772929668,-0.253038614988,-0.915502369404],
                        [0.240536183119,-0.389195710421,-0.889195740223],
                        [0.381741464138,-0.370602428913,-0.846715569496],
                        [0.234579697251,-0.126519307494,-0.963828444481],
                        [0.312772929668,-0.253038614988,-0.915502369404],
                        [0.373140364885,-0.120750762522,-0.919883430004],
                        [-0.152696594596,0.0,-0.988273143768],
                        [-0.234579697251,-0.126519307494,-0.963828444481],
                        [-0.0801787301898,-0.129731908441,-0.988302052021],
                        [-0.420543789864,0.0,-0.907272219658],
                        [-0.490634441376,-0.113409027457,-0.863953828812],
                        [-0.373140364885,-0.120750762522,-0.919883430004],
                        [-0.312772929668,-0.253038614988,-0.915502369404],
                        [-0.381741464138,-0.370602428913,-0.846715569496],
                        [-0.240536183119,-0.389195710421,-0.889195740223],
                        [-0.373140364885,-0.120750762522,-0.919883430004],
                        [-0.312772929668,-0.253038614988,-0.915502369404],
                        [-0.234579697251,-0.126519307494,-0.963828444481],
                        [0.16035746038,-0.518927633762,-0.839642524719],
                        [0.0781932324171,-0.632596552372,-0.770524084568],
                        [0.229044884443,-0.617670714855,-0.752343893051],
                        [-0.16035746038,-0.518927633762,-0.839642524719],
                        [-0.229044884443,-0.617670714855,-0.752343893051],
                        [-0.0781932324171,-0.632596552372,-0.770524084568],
                        [0.0,-0.724504590034,-0.689269959927],
                        [-0.070090636611,-0.793863236904,-0.604043483734],
                        [0.070090636611,-0.793863236904,-0.604043483734],
                        [-0.0781932324171,-0.632596552372,-0.770524084568],
                        [0.0,-0.724504590034,-0.689269959927],
                        [0.0781932324171,-0.632596552372,-0.770524084568],
                        [-0.0801787301898,-0.129731908441,-0.988302052021],
                        [0.0,-0.266404688358,-0.96386128664],
                        [0.0801787301898,-0.129731908441,-0.988302052021],
                        [-0.240536183119,-0.389195710421,-0.889195740223],
                        [-0.16035746038,-0.518927633762,-0.839642524719],
                        [-0.0823235809803,-0.39960706234,-0.912982463837],
                        [0.0823235809803,-0.39960706234,-0.912982463837],
                        [0.16035746038,-0.518927633762,-0.839642524719],
                        [0.240536183119,-0.389195710421,-0.889195740223],
                        [-0.0823235809803,-0.39960706234,-0.912982463837],
                        [0.0823235809803,-0.39960706234,-0.912982463837],
                        [0.0,-0.266404688358,-0.96386128664],
                        [-0.907272219658,-0.420543789864,0.0],
                        [-0.919883430004,-0.373140364885,-0.120750762522],
                        [-0.863953828812,-0.490634441376,-0.113409027457],
                        [-0.988273143768,-0.152696594596,0.0],
                        [-0.988302052021,-0.0801787301898,-0.129731908441],
                        [-0.963828444481,-0.234579697251,-0.126519307494],
                        [-0.915502369404,-0.312772929668,-0.253038614988],
                        [-0.889195740223,-0.240536183119,-0.389195710421],
                        [-0.846715569496,-0.381741464138,-0.370602428913],
                        [-0.963828444481,-0.234579697251,-0.126519307494],
                        [-0.915502369404,-0.312772929668,-0.253038614988],
                        [-0.919883430004,-0.373140364885,-0.120750762522],
                        [-0.988273143768,0.152696594596,0.0],
                        [-0.963828444481,0.234579697251,-0.126519307494],
                        [-0.988302052021,0.0801787301898,-0.129731908441],
                        [-0.907272219658,0.420543789864,0.0],
                        [-0.863953828812,0.490634441376,-0.113409027457],
                        [-0.919883430004,0.373140364885,-0.120750762522],
                        [-0.915502369404,0.312772929668,-0.253038614988],
                        [-0.846715569496,0.381741464138,-0.370602428913],
                        [-0.889195740223,0.240536183119,-0.389195710421],
                        [-0.919883430004,0.373140364885,-0.120750762522],
                        [-0.915502369404,0.312772929668,-0.253038614988],
                        [-0.963828444481,0.234579697251,-0.126519307494],
                        [-0.839642524719,-0.16035746038,-0.518927633762],
                        [-0.770524084568,-0.0781932324171,-0.632596552372],
                        [-0.752343893051,-0.229044884443,-0.617670714855],
                        [-0.839642524719,0.16035746038,-0.518927633762],
                        [-0.752343893051,0.229044884443,-0.617670714855],
                        [-0.770524084568,0.0781932324171,-0.632596552372],
                        [-0.689269959927,0.0,-0.724504590034],
                        [-0.604043483734,0.070090636611,-0.793863236904],
                        [-0.604043483734,-0.070090636611,-0.793863236904],
                        [-0.770524084568,0.0781932324171,-0.632596552372],
                        [-0.689269959927,0.0,-0.724504590034],
                        [-0.770524084568,-0.0781932324171,-0.632596552372],
                        [-0.988302052021,0.0801787301898,-0.129731908441],
                        [-0.96386128664,0.0,-0.266404688358],
                        [-0.988302052021,-0.0801787301898,-0.129731908441],
                        [-0.889195740223,0.240536183119,-0.389195710421],
                        [-0.839642524719,0.16035746038,-0.518927633762],
                        [-0.912982463837,0.0823235809803,-0.39960706234],
                        [-0.912982463837,-0.0823235809803,-0.39960706234],
                        [-0.839642524719,-0.16035746038,-0.518927633762],
                        [-0.889195740223,-0.240536183119,-0.389195710421],
                        [-0.912982463837,0.0823235809803,-0.39960706234],
                        [-0.912982463837,-0.0823235809803,-0.39960706234],
                        [-0.96386128664,0.0,-0.266404688358],
                        [-0.793863236904,0.604043483734,-0.070090636611],
                        [-0.79913264513,0.568519234657,-0.19537883997],
                        [-0.863953828812,0.490634441376,-0.113409027457],
                        [-0.617670714855,0.752343893051,-0.229044884443],
                        [-0.599106371403,0.70991063118,-0.370268076658],
                        [-0.71078979969,0.644004821777,-0.28290578723],
                        [-0.788983047009,0.517485499382,-0.331231862307],
                        [-0.759463787079,0.450446814299,-0.469374448061],
                        [-0.846715569496,0.381741464138,-0.370602428913],
                        [-0.71078979969,0.644004821777,-0.28290578723],
                        [-0.788983047009,0.517485499382,-0.331231862307],
                        [-0.79913264513,0.568519234657,-0.19537883997],
                        [-0.370602428913,0.846715569496,-0.381741464138],
                        [-0.331231862307,0.788983047009,-0.517485499382],
                        [-0.469374448061,0.759463787079,-0.450446814299],
                        [-0.113409027457,0.863953828812,-0.490634441376],
                        [-0.070090636611,0.793863236904,-0.604043483734],
                        [-0.19537883997,0.79913264513,-0.568519234657],
                        [-0.28290578723,0.71078979969,-0.644004821777],
                        [-0.229044884443,0.617670714855,-0.752343893051],
                        [-0.370268076658,0.599106371403,-0.70991063118],
                        [-0.19537883997,0.79913264513,-0.568519234657],
                        [-0.28290578723,0.71078979969,-0.644004821777],
                        [-0.331231862307,0.788983047009,-0.517485499382],
                        [-0.70991063118,0.370268076658,-0.599106371403],
                        [-0.644004821777,0.28290578723,-0.71078979969],
                        [-0.752343893051,0.229044884443,-0.617670714855],
                        [-0.450446814299,0.469374448061,-0.759463787079],
                        [-0.381741464138,0.370602428913,-0.846715569496],
                        [-0.517485499382,0.331231862307,-0.788983047009],
                        [-0.568519234657,0.19537883997,-0.79913264513],
                        [-0.490634441376,0.113409027457,-0.863953828812],
                        [-0.604043483734,0.070090636611,-0.793863236904],
                        [-0.517485499382,0.331231862307,-0.788983047009],
                        [-0.568519234657,0.19537883997,-0.79913264513],
                        [-0.644004821777,0.28290578723,-0.71078979969],
                        [-0.469374448061,0.759463787079,-0.450446814299],
                        [-0.5642542243,0.646577775478,-0.513375461102],
                        [-0.599106371403,0.70991063118,-0.370268076658],
                        [-0.370268076658,0.599106371403,-0.70991063118],
                        [-0.450446814299,0.469374448061,-0.759463787079],
                        [-0.513375461102,0.5642542243,-0.646577775478],
                        [-0.646577775478,0.513375461102,-0.5642542243],
                        [-0.70991063118,0.370268076658,-0.599106371403],
                        [-0.759463787079,0.450446814299,-0.469374448061],
                        [-0.513375461102,0.5642542243,-0.646577775478],
                        [-0.646577775478,0.513375461102,-0.5642542243],
                        [-0.5642542243,0.646577775478,-0.513375461102],
                        [0.420543789864,0.0,-0.907272219658],
                        [0.373140364885,0.120750762522,-0.919883430004],
                        [0.490634441376,0.113409027457,-0.863953828812],
                        [0.152696594596,0.0,-0.988273143768],
                        [0.0801787301898,0.129731908441,-0.988302052021],
                        [0.234579697251,0.126519307494,-0.963828444481],
                        [0.312772929668,0.253038614988,-0.915502369404],
                        [0.240536183119,0.389195710421,-0.889195740223],
                        [0.381741464138,0.370602428913,-0.846715569496],
                        [0.234579697251,0.126519307494,-0.963828444481],
                        [0.312772929668,0.253038614988,-0.915502369404],
                        [0.373140364885,0.120750762522,-0.919883430004],
                        [-0.152696594596,0.0,-0.988273143768],
                        [-0.234579697251,0.126519307494,-0.963828444481],
                        [-0.0801787301898,0.129731908441,-0.988302052021],
                        [-0.420543789864,0.0,-0.907272219658],
                        [-0.490634441376,0.113409027457,-0.863953828812],
                        [-0.373140364885,0.120750762522,-0.919883430004],
                        [-0.312772929668,0.253038614988,-0.915502369404],
                        [-0.381741464138,0.370602428913,-0.846715569496],
                        [-0.240536183119,0.389195710421,-0.889195740223],
                        [-0.373140364885,0.120750762522,-0.919883430004],
                        [-0.312772929668,0.253038614988,-0.915502369404],
                        [-0.234579697251,0.126519307494,-0.963828444481],
                        [0.16035746038,0.518927633762,-0.839642524719],
                        [0.0781932324171,0.632596552372,-0.770524084568],
                        [0.229044884443,0.617670714855,-0.752343893051],
                        [-0.16035746038,0.518927633762,-0.839642524719],
                        [-0.229044884443,0.617670714855,-0.752343893051],
                        [-0.0781932324171,0.632596552372,-0.770524084568],
                        [0.0,0.724504590034,-0.689269959927],
                        [-0.070090636611,0.793863236904,-0.604043483734],
                        [0.070090636611,0.793863236904,-0.604043483734],
                        [-0.0781932324171,0.632596552372,-0.770524084568],
                        [0.0,0.724504590034,-0.689269959927],
                        [0.0781932324171,0.632596552372,-0.770524084568],
                        [-0.0801787301898,0.129731908441,-0.988302052021],
                        [0.0,0.266404688358,-0.96386128664],
                        [0.0801787301898,0.129731908441,-0.988302052021],
                        [-0.240536183119,0.389195710421,-0.889195740223],
                        [-0.16035746038,0.518927633762,-0.839642524719],
                        [-0.0823235809803,0.39960706234,-0.912982463837],
                        [0.0823235809803,0.39960706234,-0.912982463837],
                        [0.16035746038,0.518927633762,-0.839642524719],
                        [0.240536183119,0.389195710421,-0.889195740223],
                        [-0.0823235809803,0.39960706234,-0.912982463837],
                        [0.0823235809803,0.39960706234,-0.912982463837],
                        [0.0,0.266404688358,-0.96386128664],
                        [0.490634441376,0.113409027457,-0.863953828812],
                        [0.568519234657,0.19537883997,-0.79913264513],
                        [0.604043483734,0.070090636611,-0.793863236904],
                        [0.381741464138,0.370602428913,-0.846715569496],
                        [0.450446814299,0.469374448061,-0.759463787079],
                        [0.517485499382,0.331231862307,-0.788983047009],
                        [0.644004821777,0.28290578723,-0.71078979969],
                        [0.70991063118,0.370268076658,-0.599106371403],
                        [0.752343893051,0.229044884443,-0.617670714855],
                        [0.517485499382,0.331231862307,-0.788983047009],
                        [0.644004821777,0.28290578723,-0.71078979969],
                        [0.568519234657,0.19537883997,-0.79913264513],
                        [0.229044884443,0.617670714855,-0.752343893051],
                        [0.28290578723,0.71078979969,-0.644004821777],
                        [0.370268076658,0.599106371403,-0.70991063118],
                        [0.070090636611,0.793863236904,-0.604043483734],
                        [0.113409027457,0.863953828812,-0.490634441376],
                        [0.19537883997,0.79913264513,-0.568519234657],
                        [0.331231862307,0.788983047009,-0.517485499382],
                        [0.370602428913,0.846715569496,-0.381741464138],
                        [0.469374448061,0.759463787079,-0.450446814299],
                        [0.19537883997,0.79913264513,-0.568519234657],
                        [0.331231862307,0.788983047009,-0.517485499382],
                        [0.28290578723,0.71078979969,-0.644004821777],
                        [0.759463787079,0.450446814299,-0.469374448061],
                        [0.788983047009,0.517485499382,-0.331231862307],
                        [0.846715569496,0.381741464138,-0.370602428913],
                        [0.599106371403,0.70991063118,-0.370268076658],
                        [0.617670714855,0.752343893051,-0.229044884443],
                        [0.71078979969,0.644004821777,-0.28290578723],
                        [0.79913264513,0.568519234657,-0.19537883997],
                        [0.793863236904,0.604043483734,-0.070090636611],
                        [0.863953828812,0.490634441376,-0.113409027457],
                        [0.71078979969,0.644004821777,-0.28290578723],
                        [0.79913264513,0.568519234657,-0.19537883997],
                        [0.788983047009,0.517485499382,-0.331231862307],
                        [0.370268076658,0.599106371403,-0.70991063118],
                        [0.513375461102,0.5642542243,-0.646577775478],
                        [0.450446814299,0.469374448061,-0.759463787079],
                        [0.469374448061,0.759463787079,-0.450446814299],
                        [0.599106371403,0.70991063118,-0.370268076658],
                        [0.5642542243,0.646577775478,-0.513375461102],
                        [0.646577775478,0.513375461102,-0.5642542243],
                        [0.759463787079,0.450446814299,-0.469374448061],
                        [0.70991063118,0.370268076658,-0.599106371403],
                        [0.5642542243,0.646577775478,-0.513375461102],
                        [0.646577775478,0.513375461102,-0.5642542243],
                        [0.513375461102,0.5642542243,-0.646577775478],
                        [0.793863236904,0.604043483734,-0.070090636611],
                        [0.724504590034,0.689269959927,0.0],
                        [0.793863236904,0.604043483734,0.070090636611],
                        [0.617670714855,0.752343893051,-0.229044884443],
                        [0.518927633762,0.839642524719,-0.16035746038],
                        [0.632596552372,0.770524084568,-0.0781932324171],
                        [0.632596552372,0.770524084568,0.0781932324171],
                        [0.518927633762,0.839642524719,0.16035746038],
                        [0.617670714855,0.752343893051,0.229044884443],
                        [0.632596552372,0.770524084568,-0.0781932324171],
                        [0.632596552372,0.770524084568,0.0781932324171],
                        [0.724504590034,0.689269959927,0.0],
                        [0.370602428913,0.846715569496,-0.381741464138],
                        [0.253038614988,0.915502369404,-0.312772929668],
                        [0.389195710421,0.889195740223,-0.240536183119],
                        [0.113409027457,0.863953828812,-0.490634441376],
                        [0.0,0.907272219658,-0.420543789864],
                        [0.120750762522,0.919883430004,-0.373140364885],
                        [0.126519307494,0.963828444481,-0.234579697251],
                        [0.0,0.988273143768,-0.152696594596],
                        [0.129731908441,0.988302052021,-0.0801787301898],
                        [0.120750762522,0.919883430004,-0.373140364885],
                        [0.126519307494,0.963828444481,-0.234579697251],
                        [0.253038614988,0.915502369404,-0.312772929668],
                        [0.389195710421,0.889195740223,0.240536183119],
                        [0.253038614988,0.915502369404,0.312772929668],
                        [0.370602428913,0.846715569496,0.381741464138],
                        [0.129731908441,0.988302052021,0.0801787301898],
                        [0.0,0.988273143768,0.152696594596],
                        [0.126519307494,0.963828444481,0.234579697251],
                        [0.120750762522,0.919883430004,0.373140364885],
                        [0.0,0.907272219658,0.420543789864],
                        [0.113409027457,0.863953828812,0.490634441376],
                        [0.126519307494,0.963828444481,0.234579697251],
                        [0.120750762522,0.919883430004,0.373140364885],
                        [0.253038614988,0.915502369404,0.312772929668],
                        [0.389195710421,0.889195740223,-0.240536183119],
                        [0.39960706234,0.912982463837,-0.0823235809803],
                        [0.518927633762,0.839642524719,-0.16035746038],
                        [0.129731908441,0.988302052021,-0.0801787301898],
                        [0.129731908441,0.988302052021,0.0801787301898],
                        [0.266404688358,0.96386128664,0.0],
                        [0.39960706234,0.912982463837,0.0823235809803],
                        [0.389195710421,0.889195740223,0.240536183119],
                        [0.518927633762,0.839642524719,0.16035746038],
                        [0.266404688358,0.96386128664,0.0],
                        [0.39960706234,0.912982463837,0.0823235809803],
                        [0.39960706234,0.912982463837,-0.0823235809803],
                        [0.793863236904,0.604043483734,0.070090636611],
                        [0.79913264513,0.568519234657,0.19537883997],
                        [0.863953828812,0.490634441376,0.113409027457],
                        [0.617670714855,0.752343893051,0.229044884443],
                        [0.599106371403,0.70991063118,0.370268076658],
                        [0.71078979969,0.644004821777,0.28290578723],
                        [0.788983047009,0.517485499382,0.331231862307],
                        [0.759463787079,0.450446814299,0.469374448061],
                        [0.846715569496,0.381741464138,0.370602428913],
                        [0.71078979969,0.644004821777,0.28290578723],
                        [0.788983047009,0.517485499382,0.331231862307],
                        [0.79913264513,0.568519234657,0.19537883997],
                        [0.370602428913,0.846715569496,0.381741464138],
                        [0.331231862307,0.788983047009,0.517485499382],
                        [0.469374448061,0.759463787079,0.450446814299],
                        [0.113409027457,0.863953828812,0.490634441376],
                        [0.070090636611,0.793863236904,0.604043483734],
                        [0.19537883997,0.79913264513,0.568519234657],
                        [0.28290578723,0.71078979969,0.644004821777],
                        [0.229044884443,0.617670714855,0.752343893051],
                        [0.370268076658,0.599106371403,0.70991063118],
                        [0.19537883997,0.79913264513,0.568519234657],
                        [0.28290578723,0.71078979969,0.644004821777],
                        [0.331231862307,0.788983047009,0.517485499382],
                        [0.70991063118,0.370268076658,0.599106371403],
                        [0.644004821777,0.28290578723,0.71078979969],
                        [0.752343893051,0.229044884443,0.617670714855],
                        [0.450446814299,0.469374448061,0.759463787079],
                        [0.381741464138,0.370602428913,0.846715569496],
                        [0.517485499382,0.331231862307,0.788983047009],
                        [0.568519234657,0.19537883997,0.79913264513],
                        [0.490634441376,0.113409027457,0.863953828812],
                        [0.604043483734,0.070090636611,0.793863236904],
                        [0.517485499382,0.331231862307,0.788983047009],
                        [0.568519234657,0.19537883997,0.79913264513],
                        [0.644004821777,0.28290578723,0.71078979969],
                        [0.469374448061,0.759463787079,0.450446814299],
                        [0.5642542243,0.646577775478,0.513375461102],
                        [0.599106371403,0.70991063118,0.370268076658],
                        [0.370268076658,0.599106371403,0.70991063118],
                        [0.450446814299,0.469374448061,0.759463787079],
                        [0.513375461102,0.5642542243,0.646577775478],
                        [0.646577775478,0.513375461102,0.5642542243],
                        [0.70991063118,0.370268076658,0.599106371403],
                        [0.759463787079,0.450446814299,0.469374448061],
                        [0.513375461102,0.5642542243,0.646577775478],
                        [0.646577775478,0.513375461102,0.5642542243],
                        [0.5642542243,0.646577775478,0.513375461102],
                        [0.907272219658,-0.420543789864,0.0],
                        [0.919883430004,-0.373140364885,0.120750762522],
                        [0.863953828812,-0.490634441376,0.113409027457],
                        [0.988273143768,-0.152696594596,0.0],
                        [0.988302052021,-0.0801787301898,0.129731908441],
                        [0.963828444481,-0.234579697251,0.126519307494],
                        [0.915502369404,-0.312772929668,0.253038614988],
                        [0.889195740223,-0.240536183119,0.389195710421],
                        [0.846715569496,-0.381741464138,0.370602428913],
                        [0.963828444481,-0.234579697251,0.126519307494],
                        [0.915502369404,-0.312772929668,0.253038614988],
                        [0.919883430004,-0.373140364885,0.120750762522],
                        [0.988273143768,0.152696594596,0.0],
                        [0.963828444481,0.234579697251,0.126519307494],
                        [0.988302052021,0.0801787301898,0.129731908441],
                        [0.907272219658,0.420543789864,0.0],
                        [0.863953828812,0.490634441376,0.113409027457],
                        [0.919883430004,0.373140364885,0.120750762522],
                        [0.915502369404,0.312772929668,0.253038614988],
                        [0.846715569496,0.381741464138,0.370602428913],
                        [0.889195740223,0.240536183119,0.389195710421],
                        [0.919883430004,0.373140364885,0.120750762522],
                        [0.915502369404,0.312772929668,0.253038614988],
                        [0.963828444481,0.234579697251,0.126519307494],
                        [0.839642524719,-0.16035746038,0.518927633762],
                        [0.770524084568,-0.0781932324171,0.632596552372],
                        [0.752343893051,-0.229044884443,0.617670714855],
                        [0.839642524719,0.16035746038,0.518927633762],
                        [0.752343893051,0.229044884443,0.617670714855],
                        [0.770524084568,0.0781932324171,0.632596552372],
                        [0.689269959927,0.0,0.724504590034],
                        [0.604043483734,0.070090636611,0.793863236904],
                        [0.604043483734,-0.070090636611,0.793863236904],
                        [0.770524084568,0.0781932324171,0.632596552372],
                        [0.689269959927,0.0,0.724504590034],
                        [0.770524084568,-0.0781932324171,0.632596552372],
                        [0.988302052021,0.0801787301898,0.129731908441],
                        [0.96386128664,0.0,0.266404688358],
                        [0.988302052021,-0.0801787301898,0.129731908441],
                        [0.889195740223,0.240536183119,0.389195710421],
                        [0.839642524719,0.16035746038,0.518927633762],
                        [0.912982463837,0.0823235809803,0.39960706234],
                        [0.912982463837,-0.0823235809803,0.39960706234],
                        [0.839642524719,-0.16035746038,0.518927633762],
                        [0.889195740223,-0.240536183119,0.389195710421],
                        [0.912982463837,0.0823235809803,0.39960706234],
                        [0.912982463837,-0.0823235809803,0.39960706234],
                        [0.96386128664,0.0,0.266404688358],
                        [-0.604043483734,0.070090636611,0.793863236904],
                        [-0.689269959927,0.0,0.724504590034],
                        [-0.604043483734,-0.070090636611,0.793863236904],
                        [-0.752343893051,0.229044884443,0.617670714855],
                        [-0.839642524719,0.16035746038,0.518927633762],
                        [-0.770524084568,0.0781932324171,0.632596552372],
                        [-0.770524084568,-0.0781932324171,0.632596552372],
                        [-0.839642524719,-0.16035746038,0.518927633762],
                        [-0.752343893051,-0.229044884443,0.617670714855],
                        [-0.770524084568,0.0781932324171,0.632596552372],
                        [-0.770524084568,-0.0781932324171,0.632596552372],
                        [-0.689269959927,0.0,0.724504590034],
                        [-0.846715569496,0.381741464138,0.370602428913],
                        [-0.915502369404,0.312772929668,0.253038614988],
                        [-0.889195740223,0.240536183119,0.389195710421],
                        [-0.863953828812,0.490634441376,0.113409027457],
                        [-0.907272219658,0.420543789864,0.0],
                        [-0.919883430004,0.373140364885,0.120750762522],
                        [-0.963828444481,0.234579697251,0.126519307494],
                        [-0.988273143768,0.152696594596,0.0],
                        [-0.988302052021,0.0801787301898,0.129731908441],
                        [-0.919883430004,0.373140364885,0.120750762522],
                        [-0.963828444481,0.234579697251,0.126519307494],
                        [-0.915502369404,0.312772929668,0.253038614988],
                        [-0.889195740223,-0.240536183119,0.389195710421],
                        [-0.915502369404,-0.312772929668,0.253038614988],
                        [-0.846715569496,-0.381741464138,0.370602428913],
                        [-0.988302052021,-0.0801787301898,0.129731908441],
                        [-0.988273143768,-0.152696594596,0.0],
                        [-0.963828444481,-0.234579697251,0.126519307494],
                        [-0.919883430004,-0.373140364885,0.120750762522],
                        [-0.907272219658,-0.420543789864,0.0],
                        [-0.863953828812,-0.490634441376,0.113409027457],
                        [-0.963828444481,-0.234579697251,0.126519307494],
                        [-0.919883430004,-0.373140364885,0.120750762522],
                        [-0.915502369404,-0.312772929668,0.253038614988],
                        [-0.889195740223,0.240536183119,0.389195710421],
                        [-0.912982463837,0.0823235809803,0.39960706234],
                        [-0.839642524719,0.16035746038,0.518927633762],
                        [-0.988302052021,0.0801787301898,0.129731908441],
                        [-0.988302052021,-0.0801787301898,0.129731908441],
                        [-0.96386128664,0.0,0.266404688358],
                        [-0.912982463837,-0.0823235809803,0.39960706234],
                        [-0.889195740223,-0.240536183119,0.389195710421],
                        [-0.839642524719,-0.16035746038,0.518927633762],
                        [-0.96386128664,0.0,0.266404688358],
                        [-0.912982463837,-0.0823235809803,0.39960706234],
                        [-0.912982463837,0.0823235809803,0.39960706234],
                        [-0.490634441376,0.113409027457,0.863953828812],
                        [-0.568519234657,0.19537883997,0.79913264513],
                        [-0.604043483734,0.070090636611,0.793863236904],
                        [-0.381741464138,0.370602428913,0.846715569496],
                        [-0.450446814299,0.469374448061,0.759463787079],
                        [-0.517485499382,0.331231862307,0.788983047009],
                        [-0.644004821777,0.28290578723,0.71078979969],
                        [-0.70991063118,0.370268076658,0.599106371403],
                        [-0.752343893051,0.229044884443,0.617670714855],
                        [-0.517485499382,0.331231862307,0.788983047009],
                        [-0.644004821777,0.28290578723,0.71078979969],
                        [-0.568519234657,0.19537883997,0.79913264513],
                        [-0.229044884443,0.617670714855,0.752343893051],
                        [-0.28290578723,0.71078979969,0.644004821777],
                        [-0.370268076658,0.599106371403,0.70991063118],
                        [-0.070090636611,0.793863236904,0.604043483734],
                        [-0.113409027457,0.863953828812,0.490634441376],
                        [-0.19537883997,0.79913264513,0.568519234657],
                        [-0.331231862307,0.788983047009,0.517485499382],
                        [-0.370602428913,0.846715569496,0.381741464138],
                        [-0.469374448061,0.759463787079,0.450446814299],
                        [-0.19537883997,0.79913264513,0.568519234657],
                        [-0.331231862307,0.788983047009,0.517485499382],
                        [-0.28290578723,0.71078979969,0.644004821777],
                        [-0.759463787079,0.450446814299,0.469374448061],
                        [-0.788983047009,0.517485499382,0.331231862307],
                        [-0.846715569496,0.381741464138,0.370602428913],
                        [-0.599106371403,0.70991063118,0.370268076658],
                        [-0.617670714855,0.752343893051,0.229044884443],
                        [-0.71078979969,0.644004821777,0.28290578723],
                        [-0.79913264513,0.568519234657,0.19537883997],
                        [-0.793863236904,0.604043483734,0.070090636611],
                        [-0.863953828812,0.490634441376,0.113409027457],
                        [-0.71078979969,0.644004821777,0.28290578723],
                        [-0.79913264513,0.568519234657,0.19537883997],
                        [-0.788983047009,0.517485499382,0.331231862307],
                        [-0.370268076658,0.599106371403,0.70991063118],
                        [-0.513375461102,0.5642542243,0.646577775478],
                        [-0.450446814299,0.469374448061,0.759463787079],
                        [-0.469374448061,0.759463787079,0.450446814299],
                        [-0.599106371403,0.70991063118,0.370268076658],
                        [-0.5642542243,0.646577775478,0.513375461102],
                        [-0.646577775478,0.513375461102,0.5642542243],
                        [-0.759463787079,0.450446814299,0.469374448061],
                        [-0.70991063118,0.370268076658,0.599106371403],
                        [-0.5642542243,0.646577775478,0.513375461102],
                        [-0.646577775478,0.513375461102,0.5642542243],
                        [-0.513375461102,0.5642542243,0.646577775478],
                        [-0.070090636611,0.793863236904,0.604043483734],
                        [0.0,0.724504590034,0.689269959927],
                        [0.070090636611,0.793863236904,0.604043483734],
                        [-0.229044884443,0.617670714855,0.752343893051],
                        [-0.16035746038,0.518927633762,0.839642524719],
                        [-0.0781932324171,0.632596552372,0.770524084568],
                        [0.0781932324171,0.632596552372,0.770524084568],
                        [0.16035746038,0.518927633762,0.839642524719],
                        [0.229044884443,0.617670714855,0.752343893051],
                        [-0.0781932324171,0.632596552372,0.770524084568],
                        [0.0781932324171,0.632596552372,0.770524084568],
                        [0.0,0.724504590034,0.689269959927],
                        [-0.381741464138,0.370602428913,0.846715569496],
                        [-0.312772929668,0.253038614988,0.915502369404],
                        [-0.240536183119,0.389195710421,0.889195740223],
                        [-0.490634441376,0.113409027457,0.863953828812],
                        [-0.420543789864,0.0,0.907272219658],
                        [-0.373140364885,0.120750762522,0.919883430004],
                        [-0.234579697251,0.126519307494,0.963828444481],
                        [-0.152696594596,0.0,0.988273143768],
                        [-0.0801787301898,0.129731908441,0.988302052021],
                        [-0.373140364885,0.120750762522,0.919883430004],
                        [-0.234579697251,0.126519307494,0.963828444481],
                        [-0.312772929668,0.253038614988,0.915502369404],
                        [0.240536183119,0.389195710421,0.889195740223],
                        [0.312772929668,0.253038614988,0.915502369404],
                        [0.381741464138,0.370602428913,0.846715569496],
                        [0.0801787301898,0.129731908441,0.988302052021],
                        [0.152696594596,0.0,0.988273143768],
                        [0.234579697251,0.126519307494,0.963828444481],
                        [0.373140364885,0.120750762522,0.919883430004],
                        [0.420543789864,0.0,0.907272219658],
                        [0.490634441376,0.113409027457,0.863953828812],
                        [0.234579697251,0.126519307494,0.963828444481],
                        [0.373140364885,0.120750762522,0.919883430004],
                        [0.312772929668,0.253038614988,0.915502369404],
                        [-0.240536183119,0.389195710421,0.889195740223],
                        [-0.0823235809803,0.39960706234,0.912982463837],
                        [-0.16035746038,0.518927633762,0.839642524719],
                        [-0.0801787301898,0.129731908441,0.988302052021],
                        [0.0801787301898,0.129731908441,0.988302052021],
                        [0.0,0.266404688358,0.96386128664],
                        [0.0823235809803,0.39960706234,0.912982463837],
                        [0.240536183119,0.389195710421,0.889195740223],
                        [0.16035746038,0.518927633762,0.839642524719],
                        [0.0,0.266404688358,0.96386128664],
                        [0.0823235809803,0.39960706234,0.912982463837],
                        [-0.0823235809803,0.39960706234,0.912982463837],
                        [-0.113409027457,0.863953828812,-0.490634441376],
                        [-0.120750762522,0.919883430004,-0.373140364885],
                        [0.0,0.907272219658,-0.420543789864],
                        [-0.370602428913,0.846715569496,-0.381741464138],
                        [-0.389195710421,0.889195740223,-0.240536183119],
                        [-0.253038614988,0.915502369404,-0.312772929668],
                        [-0.126519307494,0.963828444481,-0.234579697251],
                        [-0.129731908441,0.988302052021,-0.0801787301898],
                        [0.0,0.988273143768,-0.152696594596],
                        [-0.253038614988,0.915502369404,-0.312772929668],
                        [-0.126519307494,0.963828444481,-0.234579697251],
                        [-0.120750762522,0.919883430004,-0.373140364885],
                        [-0.617670714855,0.752343893051,-0.229044884443],
                        [-0.632596552372,0.770524084568,-0.0781932324171],
                        [-0.518927633762,0.839642524719,-0.16035746038],
                        [-0.793863236904,0.604043483734,-0.070090636611],
                        [-0.793863236904,0.604043483734,0.070090636611],
                        [-0.724504590034,0.689269959927,0.0],
                        [-0.632596552372,0.770524084568,0.0781932324171],
                        [-0.617670714855,0.752343893051,0.229044884443],
                        [-0.518927633762,0.839642524719,0.16035746038],
                        [-0.724504590034,0.689269959927,0.0],
                        [-0.632596552372,0.770524084568,0.0781932324171],
                        [-0.632596552372,0.770524084568,-0.0781932324171],
                        [-0.129731908441,0.988302052021,0.0801787301898],
                        [-0.126519307494,0.963828444481,0.234579697251],
                        [0.0,0.988273143768,0.152696594596],
                        [-0.389195710421,0.889195740223,0.240536183119],
                        [-0.370602428913,0.846715569496,0.381741464138],
                        [-0.253038614988,0.915502369404,0.312772929668],
                        [-0.120750762522,0.919883430004,0.373140364885],
                        [-0.113409027457,0.863953828812,0.490634441376],
                        [0.0,0.907272219658,0.420543789864],
                        [-0.253038614988,0.915502369404,0.312772929668],
                        [-0.120750762522,0.919883430004,0.373140364885],
                        [-0.126519307494,0.963828444481,0.234579697251],
                        [-0.518927633762,0.839642524719,-0.16035746038],
                        [-0.39960706234,0.912982463837,-0.0823235809803],
                        [-0.389195710421,0.889195740223,-0.240536183119],
                        [-0.518927633762,0.839642524719,0.16035746038],
                        [-0.389195710421,0.889195740223,0.240536183119],
                        [-0.39960706234,0.912982463837,0.0823235809803],
                        [-0.266404688358,0.96386128664,0.0],
                        [-0.129731908441,0.988302052021,0.0801787301898],
                        [-0.129731908441,0.988302052021,-0.0801787301898],
                        [-0.39960706234,0.912982463837,0.0823235809803],
                        [-0.266404688358,0.96386128664,0.0],
                        [-0.39960706234,0.912982463837,-0.0823235809803],
                        [0.604043483734,0.070090636611,-0.793863236904],
                        [0.689269959927,0.0,-0.724504590034],
                        [0.604043483734,-0.070090636611,-0.793863236904],
                        [0.752343893051,0.229044884443,-0.617670714855],
                        [0.839642524719,0.16035746038,-0.518927633762],
                        [0.770524084568,0.0781932324171,-0.632596552372],
                        [0.770524084568,-0.0781932324171,-0.632596552372],
                        [0.839642524719,-0.16035746038,-0.518927633762],
                        [0.752343893051,-0.229044884443,-0.617670714855],
                        [0.770524084568,0.0781932324171,-0.632596552372],
                        [0.770524084568,-0.0781932324171,-0.632596552372],
                        [0.689269959927,0.0,-0.724504590034],
                        [0.846715569496,0.381741464138,-0.370602428913],
                        [0.915502369404,0.312772929668,-0.253038614988],
                        [0.889195740223,0.240536183119,-0.389195710421],
                        [0.863953828812,0.490634441376,-0.113409027457],
                        [0.907272219658,0.420543789864,0.0],
                        [0.919883430004,0.373140364885,-0.120750762522],
                        [0.963828444481,0.234579697251,-0.126519307494],
                        [0.988273143768,0.152696594596,0.0],
                        [0.988302052021,0.0801787301898,-0.129731908441],
                        [0.919883430004,0.373140364885,-0.120750762522],
                        [0.963828444481,0.234579697251,-0.126519307494],
                        [0.915502369404,0.312772929668,-0.253038614988],
                        [0.889195740223,-0.240536183119,-0.389195710421],
                        [0.915502369404,-0.312772929668,-0.253038614988],
                        [0.846715569496,-0.381741464138,-0.370602428913],
                        [0.988302052021,-0.0801787301898,-0.129731908441],
                        [0.988273143768,-0.152696594596,0.0],
                        [0.963828444481,-0.234579697251,-0.126519307494],
                        [0.919883430004,-0.373140364885,-0.120750762522],
                        [0.907272219658,-0.420543789864,0.0],
                        [0.863953828812,-0.490634441376,-0.113409027457],
                        [0.963828444481,-0.234579697251,-0.126519307494],
                        [0.919883430004,-0.373140364885,-0.120750762522],
                        [0.915502369404,-0.312772929668,-0.253038614988],
                        [0.889195740223,0.240536183119,-0.389195710421],
                        [0.912982463837,0.0823235809803,-0.39960706234],
                        [0.839642524719,0.16035746038,-0.518927633762],
                        [0.988302052021,0.0801787301898,-0.129731908441],
                        [0.988302052021,-0.0801787301898,-0.129731908441],
                        [0.96386128664,0.0,-0.266404688358],
                        [0.912982463837,-0.0823235809803,-0.39960706234],
                        [0.889195740223,-0.240536183119,-0.389195710421],
                        [0.839642524719,-0.16035746038,-0.518927633762],
                        [0.96386128664,0.0,-0.266404688358],
                        [0.912982463837,-0.0823235809803,-0.39960706234],
                        [0.912982463837,0.0823235809803,-0.39960706234],
                        [-0.82464236021,-0.564633131027,0.0339771322906],
                        [-0.79582041502,-0.605532705784,0.0],
                        [-0.82464236021,-0.564633131027,-0.0339771322906],
                        [-0.757922053337,-0.643326640129,0.108097285032],
                        [-0.722495436668,-0.687358558178,0.0744211226702],
                        [-0.761889100075,-0.646693944931,0.0362210273743],
                        [-0.761889100075,-0.646693944931,-0.0362210273743],
                        [-0.722495436668,-0.687358558178,-0.0744211226702],
                        [-0.757922053337,-0.643326640129,-0.108097285032],
                        [-0.761889100075,-0.646693944931,0.0362210273743],
                        [-0.761889100075,-0.646693944931,-0.0362210273743],
                        [-0.79582041502,-0.605532705784,0.0],
                        [-0.669747889042,-0.718357801437,0.188148602843],
                        [-0.62687343359,-0.763553202152,0.154971644282],
                        [-0.677466154099,-0.726636230946,0.114190116525],
                        [-0.560828924179,-0.782811582088,0.269586592913],
                        [-0.510783493519,-0.826465010643,0.236761152744],
                        [-0.571085453033,-0.797127783298,0.196083456278],
                        [-0.578244268894,-0.807120084763,0.119124859571],
                        [-0.524005174637,-0.847858190536,0.0809632539749],
                        [-0.581926107407,-0.81225925684,0.0399611219764],
                        [-0.571085453033,-0.797127783298,0.196083456278],
                        [-0.578244268894,-0.807120084763,0.119124859571],
                        [-0.62687343359,-0.763553202152,0.154971644282],
                        [-0.677466154099,-0.726636230946,-0.114190116525],
                        [-0.62687343359,-0.763553202152,-0.154971644282],
                        [-0.669747889042,-0.718357801437,-0.188148602843],
                        [-0.581926107407,-0.81225925684,-0.0399611219764],
                        [-0.524005174637,-0.847858190536,-0.0809632539749],
                        [-0.578244268894,-0.807120084763,-0.119124859571],
                        [-0.571085453033,-0.797127783298,-0.196083456278],
                        [-0.510783493519,-0.826465010643,-0.236761152744],
                        [-0.560828924179,-0.782811582088,-0.269586592913],
                        [-0.578244268894,-0.807120084763,-0.119124859571],
                        [-0.571085453033,-0.797127783298,-0.196083456278],
                        [-0.62687343359,-0.763553202152,-0.154971644282],
                        [-0.677466154099,-0.726636230946,0.114190116525],
                        [-0.68142670393,-0.730884253979,0.0382858961821],
                        [-0.722495436668,-0.687358558178,0.0744211226702],
                        [-0.581926107407,-0.81225925684,0.0399611219764],
                        [-0.581926107407,-0.81225925684,-0.0399611219764],
                        [-0.634539365768,-0.772890508175,0.0],
                        [-0.68142670393,-0.730884253979,-0.0382858961821],
                        [-0.677466154099,-0.726636230946,-0.114190116525],
                        [-0.722495436668,-0.687358558178,-0.0744211226702],
                        [-0.634539365768,-0.772890508175,0.0],
                        [-0.68142670393,-0.730884253979,-0.0382858961821],
                        [-0.68142670393,-0.730884253979,0.0382858961821],
                        [-0.436200261116,-0.830415487289,0.346611320972],
                        [-0.380723625422,-0.869839549065,0.313733518124],
                        [-0.446935534477,-0.85085272789,0.276221334934],
                        [-0.3044308424,-0.857896447182,0.413926929235],
                        [-0.246351331472,-0.891307473183,0.380633711815],
                        [-0.313436716795,-0.883275330067,0.348686188459],
                        [-0.321246802807,-0.905284404755,0.277958005667],
                        [-0.258633822203,-0.935745954514,0.239766731858],
                        [-0.327503234148,-0.922915279865,0.202408134937],
                        [-0.313436716795,-0.883275330067,0.348686188459],
                        [-0.321246802807,-0.905284404755,0.277958005667],
                        [-0.380723625422,-0.869839549065,0.313733518124],
                        [-0.174905076623,-0.866019308567,0.468421578407],
                        [-0.117213711143,-0.892938017845,0.434652328491],
                        [-0.180623859167,-0.894335091114,0.409316182137],
                        [-0.0549761541188,-0.858619451523,0.509656965733],
                        [0.0,-0.8796184659,0.475679844618],
                        [-0.0568443164229,-0.887796461582,0.456712335348],
                        [-0.0586068555713,-0.915323853493,0.398431301117],
                        [0.0,-0.932827115059,0.360324263573],
                        [-0.0602079555392,-0.940329909325,0.334895044565],
                        [-0.0568443164229,-0.887796461582,0.456712335348],
                        [-0.0586068555713,-0.915323853493,0.398431301117],
                        [-0.117213711143,-0.892938017845,0.434652328491],
                        [-0.193975359201,-0.960443258286,0.199805602431],
                        [-0.128498718143,-0.978907585144,0.158833146095],
                        [-0.196501940489,-0.97295331955,0.121444880962],
                        [-0.0615878328681,-0.961880862713,0.266443610191],
                        [0.0,-0.974178731441,0.225778326392],
                        [-0.0626873448491,-0.979053080082,0.193714544177],
                        [-0.0634539350867,-0.991025745869,0.117650069296],
                        [0.0,-0.997029185295,0.0770247355103],
                        [-0.0638479366899,-0.997179210186,0.0394601933658],
                        [-0.0626873448491,-0.979053080082,0.193714544177],
                        [-0.0634539350867,-0.991025745869,0.117650069296],
                        [-0.128498718143,-0.978907585144,0.158833146095],
                        [-0.180623859167,-0.894335091114,0.409316182137],
                        [-0.185843646526,-0.920180141926,0.34457308054],
                        [-0.246351331472,-0.891307473183,0.380633711815],
                        [-0.0602079555392,-0.940329909325,0.334895044565],
                        [-0.0615878328681,-0.961880862713,0.266443610191],
                        [-0.123895764351,-0.943842172623,0.306287169456],
                        [-0.190361812711,-0.942551255226,0.274516820908],
                        [-0.193975359201,-0.960443258286,0.199805602431],
                        [-0.258633822203,-0.935745954514,0.239766731858],
                        [-0.123895764351,-0.943842172623,0.306287169456],
                        [-0.190361812711,-0.942551255226,0.274516820908],
                        [-0.185843646526,-0.920180141926,0.34457308054],
                        [-0.446935534477,-0.85085272789,-0.276221334934],
                        [-0.380723625422,-0.869839549065,-0.313733518124],
                        [-0.436200261116,-0.830415487289,-0.346611320972],
                        [-0.327503234148,-0.922915279865,-0.202408134937],
                        [-0.258633822203,-0.935745954514,-0.239766731858],
                        [-0.321246802807,-0.905284404755,-0.277958005667],
                        [-0.313436716795,-0.883275330067,-0.348686188459],
                        [-0.246351331472,-0.891307473183,-0.380633711815],
                        [-0.3044308424,-0.857896447182,-0.413926929235],
                        [-0.321246802807,-0.905284404755,-0.277958005667],
                        [-0.313436716795,-0.883275330067,-0.348686188459],
                        [-0.380723625422,-0.869839549065,-0.313733518124],
                        [-0.196501940489,-0.97295331955,-0.121444880962],
                        [-0.128498718143,-0.978907585144,-0.158833146095],
                        [-0.193975359201,-0.960443258286,-0.199805602431],
                        [-0.0638479366899,-0.997179210186,-0.0394601933658],
                        [0.0,-0.997029185295,-0.0770247355103],
                        [-0.0634539350867,-0.991025745869,-0.117650069296],
                        [-0.0626873448491,-0.979053080082,-0.193714544177],
                        [0.0,-0.974178731441,-0.225778326392],
                        [-0.0615878328681,-0.961880862713,-0.266443610191],
                        [-0.0634539350867,-0.991025745869,-0.117650069296],
                        [-0.0626873448491,-0.979053080082,-0.193714544177],
                        [-0.128498718143,-0.978907585144,-0.158833146095],
                        [-0.180623859167,-0.894335091114,-0.409316182137],
                        [-0.117213711143,-0.892938017845,-0.434652328491],
                        [-0.174905076623,-0.866019308567,-0.468421578407],
                        [-0.0602079555392,-0.940329909325,-0.334895044565],
                        [0.0,-0.932827115059,-0.360324263573],
                        [-0.0586068555713,-0.915323853493,-0.398431301117],
                        [-0.0568443164229,-0.887796461582,-0.456712335348],
                        [0.0,-0.8796184659,-0.475679844618],
                        [-0.0549761541188,-0.858619451523,-0.509656965733],
                        [-0.0586068555713,-0.915323853493,-0.398431301117],
                        [-0.0568443164229,-0.887796461582,-0.456712335348],
                        [-0.117213711143,-0.892938017845,-0.434652328491],
                        [-0.193975359201,-0.960443258286,-0.199805602431],
                        [-0.190361812711,-0.942551255226,-0.274516820908],
                        [-0.258633822203,-0.935745954514,-0.239766731858],
                        [-0.0615878328681,-0.961880862713,-0.266443610191],
                        [-0.0602079555392,-0.940329909325,-0.334895044565],
                        [-0.123895764351,-0.943842172623,-0.306287169456],
                        [-0.185843646526,-0.920180141926,-0.34457308054],
                        [-0.180623859167,-0.894335091114,-0.409316182137],
                        [-0.246351331472,-0.891307473183,-0.380633711815],
                        [-0.123895764351,-0.943842172623,-0.306287169456],
                        [-0.185843646526,-0.920180141926,-0.34457308054],
                        [-0.190361812711,-0.942551255226,-0.274516820908],
                        [-0.446935534477,-0.85085272789,0.276221334934],
                        [-0.455528259277,-0.867211103439,0.20109423995],
                        [-0.510783493519,-0.826465010643,0.236761152744],
                        [-0.327503234148,-0.922915279865,0.202408134937],
                        [-0.33188316226,-0.935258030891,0.123069040477],
                        [-0.395605653524,-0.903840482235,0.162998497486],
                        [-0.461539924145,-0.878655850887,0.122248865664],
                        [-0.464636415243,-0.88455080986,0.0410230122507],
                        [-0.524005174637,-0.847858190536,0.0809632539749],
                        [-0.395605653524,-0.903840482235,0.162998497486],
                        [-0.461539924145,-0.878655850887,0.122248865664],
                        [-0.455528259277,-0.867211103439,0.20109423995],
                        [-0.196501940489,-0.97295331955,0.121444880962],
                        [-0.197802826762,-0.979394435883,0.0407496243715],
                        [-0.265506535769,-0.960611641407,0.0820460245013],
                        [-0.0638479366899,-0.997179210186,0.0394601933658],
                        [-0.0638479366899,-0.997179210186,-0.0394601933658],
                        [-0.130150929093,-0.991494178772,0.0],
                        [-0.197802826762,-0.979394435883,-0.0407496243715],
                        [-0.196501940489,-0.97295331955,-0.121444880962],
                        [-0.265506535769,-0.960611641407,-0.0820460245013],
                        [-0.130150929093,-0.991494178772,0.0],
                        [-0.197802826762,-0.979394435883,-0.0407496243715],
                        [-0.197802826762,-0.979394435883,0.0407496243715],
                        [-0.464636415243,-0.88455080986,-0.0410230122507],
                        [-0.461539924145,-0.878655850887,-0.122248865664],
                        [-0.524005174637,-0.847858190536,-0.0809632539749],
                        [-0.33188316226,-0.935258030891,-0.123069040477],
                        [-0.327503234148,-0.922915279865,-0.202408134937],
                        [-0.395605653524,-0.903840482235,-0.162998497486],
                        [-0.455528259277,-0.867211103439,-0.20109423995],
                        [-0.446935534477,-0.85085272789,-0.276221334934],
                        [-0.510783493519,-0.826465010643,-0.236761152744],
                        [-0.395605653524,-0.903840482235,-0.162998497486],
                        [-0.455528259277,-0.867211103439,-0.20109423995],
                        [-0.461539924145,-0.878655850887,-0.122248865664],
                        [-0.265506535769,-0.960611641407,0.0820460245013],
                        [-0.334140062332,-0.941618084908,0.04130198434],
                        [-0.33188316226,-0.935258030891,0.123069040477],
                        [-0.265506535769,-0.960611641407,-0.0820460245013],
                        [-0.33188316226,-0.935258030891,-0.123069040477],
                        [-0.334140062332,-0.941618084908,-0.04130198434],
                        [-0.400968074799,-0.916092038155,0.0],
                        [-0.464636415243,-0.88455080986,-0.0410230122507],
                        [-0.464636415243,-0.88455080986,0.0410230122507],
                        [-0.334140062332,-0.941618084908,-0.04130198434],
                        [-0.400968074799,-0.916092038155,0.0],
                        [-0.334140062332,-0.941618084908,0.04130198434],
                        [-0.509656965733,-0.0549761541188,0.858619451523],
                        [-0.548688352108,-0.091976031661,0.830952167511],
                        [-0.564633131027,-0.0339771322906,0.82464236021],
                        [-0.468421578407,-0.174905076623,0.866019308567],
                        [-0.506734728813,-0.217834427953,0.834127128124],
                        [-0.529480218887,-0.153434738517,0.834331154823],
                        [-0.588087081909,-0.131048902869,0.798110127449],
                        [-0.627150595188,-0.171839639544,0.759706020355],
                        [-0.643326640129,-0.108097285032,0.757922053337],
                        [-0.529480218887,-0.153434738517,0.834331154823],
                        [-0.588087081909,-0.131048902869,0.798110127449],
                        [-0.548688352108,-0.091976031661,0.830952167511],
                        [-0.413926929235,-0.3044308424,0.857896447182],
                        [-0.450116455555,-0.352179646492,0.820587992668],
                        [-0.480284929276,-0.284414708614,0.829719662666],
                        [-0.346611320972,-0.436200261116,0.830415487289],
                        [-0.379529476166,-0.486395716667,0.787004828453],
                        [-0.416404157877,-0.419940322638,0.806385576725],
                        [-0.485873311758,-0.400663375854,0.776785671711],
                        [-0.520354926586,-0.44894811511,0.726413309574],
                        [-0.553625464439,-0.378517180681,0.74177056551],
                        [-0.416404157877,-0.419940322638,0.806385576725],
                        [-0.485873311758,-0.400663375854,0.776785671711],
                        [-0.450116455555,-0.352179646492,0.820587992668],
                        [-0.665048420429,-0.213841319084,0.715529501438],
                        [-0.700865805149,-0.256401896477,0.665616393089],
                        [-0.718357801437,-0.188148602843,0.669747889042],
                        [-0.618283927441,-0.353819847107,0.701809465885],
                        [-0.65135627985,-0.398910075426,0.645450055599],
                        [-0.678621411324,-0.327040165663,0.657660841942],
                        [-0.733673810959,-0.298754066229,0.610302150249],
                        [-0.762617051601,-0.340069264174,0.550243675709],
                        [-0.782811582088,-0.269586592913,0.560828924179],
                        [-0.678621411324,-0.327040165663,0.657660841942],
                        [-0.733673810959,-0.298754066229,0.610302150249],
                        [-0.700865805149,-0.256401896477,0.665616393089],
                        [-0.480284929276,-0.284414708614,0.829719662666],
                        [-0.545040607452,-0.26241543889,0.796284377575],
                        [-0.506734728813,-0.217834427953,0.834127128124],
                        [-0.553625464439,-0.378517180681,0.74177056551],
                        [-0.618283927441,-0.353819847107,0.701809465885],
                        [-0.582528710365,-0.308011889458,0.752189457417],
                        [-0.606988489628,-0.238753452897,0.757998526096],
                        [-0.665048420429,-0.213841319084,0.715529501438],
                        [-0.627150595188,-0.171839639544,0.759706020355],
                        [-0.582528710365,-0.308011889458,0.752189457417],
                        [-0.606988489628,-0.238753452897,0.757998526096],
                        [-0.545040607452,-0.26241543889,0.796284377575],
                        [-0.269586592913,-0.560828924179,0.782811582088],
                        [-0.298754066229,-0.610302150249,0.733673810959],
                        [-0.340069264174,-0.550243675709,0.762617051601],
                        [-0.188148602843,-0.669747889042,0.718357801437],
                        [-0.213841319084,-0.715529501438,0.665048420429],
                        [-0.256401896477,-0.665616393089,0.700865805149],
                        [-0.327040165663,-0.657660841942,0.678621411324],
                        [-0.353819847107,-0.701809465885,0.618283927441],
                        [-0.398910075426,-0.645450055599,0.65135627985],
                        [-0.256401896477,-0.665616393089,0.700865805149],
                        [-0.327040165663,-0.657660841942,0.678621411324],
                        [-0.298754066229,-0.610302150249,0.733673810959],
                        [-0.108097285032,-0.757922053337,0.643326640129],
                        [-0.131048902869,-0.798110127449,0.588087081909],
                        [-0.171839639544,-0.759706020355,0.627150595188],
                        [-0.0339771322906,-0.82464236021,0.564633131027],
                        [-0.0549761541188,-0.858619451523,0.509656965733],
                        [-0.091976031661,-0.830952167511,0.548688352108],
                        [-0.153434738517,-0.834331154823,0.529480218887],
                        [-0.174905076623,-0.866019308567,0.468421578407],
                        [-0.217834427953,-0.834127128124,0.506734728813],
                        [-0.091976031661,-0.830952167511,0.548688352108],
                        [-0.153434738517,-0.834331154823,0.529480218887],
                        [-0.131048902869,-0.798110127449,0.588087081909],
                        [-0.378517180681,-0.74177056551,0.553625464439],
                        [-0.400663375854,-0.776785671711,0.485873311758],
                        [-0.44894811511,-0.726413309574,0.520354926586],
                        [-0.284414708614,-0.829719662666,0.480284929276],
                        [-0.3044308424,-0.857896447182,0.413926929235],
                        [-0.352179646492,-0.820587992668,0.450116455555],
                        [-0.419940322638,-0.806385576725,0.416404157877],
                        [-0.436200261116,-0.830415487289,0.346611320972],
                        [-0.486395716667,-0.787004828453,0.379529476166],
                        [-0.352179646492,-0.820587992668,0.450116455555],
                        [-0.419940322638,-0.806385576725,0.416404157877],
                        [-0.400663375854,-0.776785671711,0.485873311758],
                        [-0.171839639544,-0.759706020355,0.627150595188],
                        [-0.238753452897,-0.757998526096,0.606988489628],
                        [-0.213841319084,-0.715529501438,0.665048420429],
                        [-0.217834427953,-0.834127128124,0.506734728813],
                        [-0.284414708614,-0.829719662666,0.480284929276],
                        [-0.26241543889,-0.796284377575,0.545040607452],
                        [-0.308011889458,-0.752189457417,0.582528710365],
                        [-0.378517180681,-0.74177056551,0.553625464439],
                        [-0.353819847107,-0.701809465885,0.618283927441],
                        [-0.26241543889,-0.796284377575,0.545040607452],
                        [-0.308011889458,-0.752189457417,0.582528710365],
                        [-0.238753452897,-0.757998526096,0.606988489628],
                        [-0.787004828453,-0.379529476166,0.486395716667],
                        [-0.806385576725,-0.416404157877,0.419940322638],
                        [-0.830415487289,-0.346611320972,0.436200261116],
                        [-0.726413309574,-0.520354926586,0.44894811511],
                        [-0.74177056551,-0.553625464439,0.378517180681],
                        [-0.776785671711,-0.485873311758,0.400663375854],
                        [-0.820587992668,-0.450116455555,0.352179646492],
                        [-0.829719662666,-0.480284929276,0.284414708614],
                        [-0.857896447182,-0.413926929235,0.3044308424],
                        [-0.776785671711,-0.485873311758,0.400663375854],
                        [-0.820587992668,-0.450116455555,0.352179646492],
                        [-0.806385576725,-0.416404157877,0.419940322638],
                        [-0.645450055599,-0.65135627985,0.398910075426],
                        [-0.657660841942,-0.678621411324,0.327040165663],
                        [-0.701809465885,-0.618283927441,0.353819847107],
                        [-0.550243675709,-0.762617051601,0.340069264174],
                        [-0.560828924179,-0.782811582088,0.269586592913],
                        [-0.610302150249,-0.733673810959,0.298754066229],
                        [-0.665616393089,-0.700865805149,0.256401896477],
                        [-0.669747889042,-0.718357801437,0.188148602843],
                        [-0.715529501438,-0.665048420429,0.213841319084],
                        [-0.610302150249,-0.733673810959,0.298754066229],
                        [-0.665616393089,-0.700865805149,0.256401896477],
                        [-0.657660841942,-0.678621411324,0.327040165663],
                        [-0.834127128124,-0.506734728813,0.217834427953],
                        [-0.834331154823,-0.529480218887,0.153434738517],
                        [-0.866019308567,-0.468421578407,0.174905076623],
                        [-0.759706020355,-0.627150595188,0.171839639544],
                        [-0.757922053337,-0.643326640129,0.108097285032],
                        [-0.798110127449,-0.588087081909,0.131048902869],
                        [-0.830952167511,-0.548688352108,0.091976031661],
                        [-0.82464236021,-0.564633131027,0.0339771322906],
                        [-0.858619451523,-0.509656965733,0.0549761541188],
                        [-0.798110127449,-0.588087081909,0.131048902869],
                        [-0.830952167511,-0.548688352108,0.091976031661],
                        [-0.834331154823,-0.529480218887,0.153434738517],
                        [-0.701809465885,-0.618283927441,0.353819847107],
                        [-0.752189457417,-0.582528710365,0.308011889458],
                        [-0.74177056551,-0.553625464439,0.378517180681],
                        [-0.715529501438,-0.665048420429,0.213841319084],
                        [-0.759706020355,-0.627150595188,0.171839639544],
                        [-0.757998526096,-0.606988489628,0.238753452897],
                        [-0.796284377575,-0.545040607452,0.26241543889],
                        [-0.834127128124,-0.506734728813,0.217834427953],
                        [-0.829719662666,-0.480284929276,0.284414708614],
                        [-0.757998526096,-0.606988489628,0.238753452897],
                        [-0.796284377575,-0.545040607452,0.26241543889],
                        [-0.752189457417,-0.582528710365,0.308011889458],
                        [-0.340069264174,-0.550243675709,0.762617051601],
                        [-0.411682873964,-0.535965919495,0.737060189247],
                        [-0.379529476166,-0.486395716667,0.787004828453],
                        [-0.398910075426,-0.645450055599,0.65135627985],
                        [-0.470621615648,-0.628728508949,0.619044244289],
                        [-0.44230055809,-0.58378881216,0.680853009224],
                        [-0.483050197363,-0.517854511738,0.706037700176],
                        [-0.552667617798,-0.495975226164,0.669751524925],
                        [-0.520354926586,-0.44894811511,0.726413309574],
                        [-0.44230055809,-0.58378881216,0.680853009224],
                        [-0.483050197363,-0.517854511738,0.706037700176],
                        [-0.411682873964,-0.535965919495,0.737060189247],
                        [-0.44894811511,-0.726413309574,0.520354926586],
                        [-0.517854511738,-0.706037700176,0.483050197363],
                        [-0.495975226164,-0.669751524925,0.552667617798],
                        [-0.486395716667,-0.787004828453,0.379529476166],
                        [-0.550243675709,-0.762617051601,0.340069264174],
                        [-0.535965919495,-0.737060189247,0.411682873964],
                        [-0.58378881216,-0.680853009224,0.44230055809],
                        [-0.645450055599,-0.65135627985,0.398910075426],
                        [-0.628728508949,-0.619044244289,0.470621615648],
                        [-0.535965919495,-0.737060189247,0.411682873964],
                        [-0.58378881216,-0.680853009224,0.44230055809],
                        [-0.517854511738,-0.706037700176,0.483050197363],
                        [-0.619044244289,-0.470621615648,0.628728508949],
                        [-0.680853009224,-0.44230055809,0.58378881216],
                        [-0.65135627985,-0.398910075426,0.645450055599],
                        [-0.669751524925,-0.552667617798,0.495975226164],
                        [-0.726413309574,-0.520354926586,0.44894811511],
                        [-0.706037700176,-0.483050197363,0.517854511738],
                        [-0.737060189247,-0.411682873964,0.535965919495],
                        [-0.787004828453,-0.379529476166,0.486395716667],
                        [-0.762617051601,-0.340069264174,0.550243675709],
                        [-0.706037700176,-0.483050197363,0.517854511738],
                        [-0.737060189247,-0.411682873964,0.535965919495],
                        [-0.680853009224,-0.44230055809,0.58378881216],
                        [-0.495975226164,-0.669751524925,0.552667617798],
                        [-0.540649950504,-0.607478022575,0.581951975822],
                        [-0.470621615648,-0.628728508949,0.619044244289],
                        [-0.628728508949,-0.619044244289,0.470621615648],
                        [-0.669751524925,-0.552667617798,0.495975226164],
                        [-0.607478022575,-0.581951975822,0.540649950504],
                        [-0.581951975822,-0.540649950504,0.607478022575],
                        [-0.619044244289,-0.470621615648,0.628728508949],
                        [-0.552667617798,-0.495975226164,0.669751524925],
                        [-0.607478022575,-0.581951975822,0.540649950504],
                        [-0.581951975822,-0.540649950504,0.607478022575],
                        [-0.540649950504,-0.607478022575,0.581951975822],
                        [-0.0339771322906,-0.82464236021,0.564633131027],
                        [0.0,-0.79582041502,0.605532705784],
                        [0.0339771322906,-0.82464236021,0.564633131027],
                        [-0.108097285032,-0.757922053337,0.643326640129],
                        [-0.0744211226702,-0.722495436668,0.687358558178],
                        [-0.0362210273743,-0.761889100075,0.646693944931],
                        [0.0362210273743,-0.761889100075,0.646693944931],
                        [0.0744211226702,-0.722495436668,0.687358558178],
                        [0.108097285032,-0.757922053337,0.643326640129],
                        [-0.0362210273743,-0.761889100075,0.646693944931],
                        [0.0362210273743,-0.761889100075,0.646693944931],
                        [0.0,-0.79582041502,0.605532705784],
                        [-0.188148602843,-0.669747889042,0.718357801437],
                        [-0.154971644282,-0.62687343359,0.763553202152],
                        [-0.114190116525,-0.677466154099,0.726636230946],
                        [-0.269586592913,-0.560828924179,0.782811582088],
                        [-0.236761152744,-0.510783493519,0.826465010643],
                        [-0.196083456278,-0.571085453033,0.797127783298],
                        [-0.119124859571,-0.578244268894,0.807120084763],
                        [-0.0809632539749,-0.524005174637,0.847858190536],
                        [-0.0399611219764,-0.581926107407,0.81225925684],
                        [-0.196083456278,-0.571085453033,0.797127783298],
                        [-0.119124859571,-0.578244268894,0.807120084763],
                        [-0.154971644282,-0.62687343359,0.763553202152],
                        [0.114190116525,-0.677466154099,0.726636230946],
                        [0.154971644282,-0.62687343359,0.763553202152],
                        [0.188148602843,-0.669747889042,0.718357801437],
                        [0.0399611219764,-0.581926107407,0.81225925684],
                        [0.0809632539749,-0.524005174637,0.847858190536],
                        [0.119124859571,-0.578244268894,0.807120084763],
                        [0.196083456278,-0.571085453033,0.797127783298],
                        [0.236761152744,-0.510783493519,0.826465010643],
                        [0.269586592913,-0.560828924179,0.782811582088],
                        [0.119124859571,-0.578244268894,0.807120084763],
                        [0.196083456278,-0.571085453033,0.797127783298],
                        [0.154971644282,-0.62687343359,0.763553202152],
                        [-0.114190116525,-0.677466154099,0.726636230946],
                        [-0.0382858961821,-0.68142670393,0.730884253979],
                        [-0.0744211226702,-0.722495436668,0.687358558178],
                        [-0.0399611219764,-0.581926107407,0.81225925684],
                        [0.0399611219764,-0.581926107407,0.81225925684],
                        [0.0,-0.634539365768,0.772890508175],
                        [0.0382858961821,-0.68142670393,0.730884253979],
                        [0.114190116525,-0.677466154099,0.726636230946],
                        [0.0744211226702,-0.722495436668,0.687358558178],
                        [0.0,-0.634539365768,0.772890508175],
                        [0.0382858961821,-0.68142670393,0.730884253979],
                        [-0.0382858961821,-0.68142670393,0.730884253979],
                        [-0.346611320972,-0.436200261116,0.830415487289],
                        [-0.313733518124,-0.380723625422,0.869839549065],
                        [-0.276221334934,-0.446935534477,0.85085272789],
                        [-0.413926929235,-0.3044308424,0.857896447182],
                        [-0.380633711815,-0.246351331472,0.891307473183],
                        [-0.348686188459,-0.313436716795,0.883275330067],
                        [-0.277958005667,-0.321246802807,0.905284404755],
                        [-0.239766731858,-0.258633822203,0.935745954514],
                        [-0.202408134937,-0.327503234148,0.922915279865],
                        [-0.348686188459,-0.313436716795,0.883275330067],
                        [-0.277958005667,-0.321246802807,0.905284404755],
                        [-0.313733518124,-0.380723625422,0.869839549065],
                        [-0.468421578407,-0.174905076623,0.866019308567],
                        [-0.434652328491,-0.117213711143,0.892938017845],
                        [-0.409316182137,-0.180623859167,0.894335091114],
                        [-0.509656965733,-0.0549761541188,0.858619451523],
                        [-0.475679844618,0.0,0.8796184659],
                        [-0.456712335348,-0.0568443164229,0.887796461582],
                        [-0.398431301117,-0.0586068555713,0.915323853493],
                        [-0.360324263573,0.0,0.932827115059],
                        [-0.334895044565,-0.0602079555392,0.940329909325],
                        [-0.456712335348,-0.0568443164229,0.887796461582],
                        [-0.398431301117,-0.0586068555713,0.915323853493],
                        [-0.434652328491,-0.117213711143,0.892938017845],
                        [-0.199805602431,-0.193975359201,0.960443258286],
                        [-0.158833146095,-0.128498718143,0.978907585144],
                        [-0.121444880962,-0.196501940489,0.97295331955],
                        [-0.266443610191,-0.0615878328681,0.961880862713],
                        [-0.225778326392,0.0,0.974178731441],
                        [-0.193714544177,-0.0626873448491,0.979053080082],
                        [-0.117650069296,-0.0634539350867,0.991025745869],
                        [-0.0770247355103,0.0,0.997029185295],
                        [-0.0394601933658,-0.0638479366899,0.997179210186],
                        [-0.193714544177,-0.0626873448491,0.979053080082],
                        [-0.117650069296,-0.0634539350867,0.991025745869],
                        [-0.158833146095,-0.128498718143,0.978907585144],
                        [-0.409316182137,-0.180623859167,0.894335091114],
                        [-0.34457308054,-0.185843646526,0.920180141926],
                        [-0.380633711815,-0.246351331472,0.891307473183],
                        [-0.334895044565,-0.0602079555392,0.940329909325],
                        [-0.266443610191,-0.0615878328681,0.961880862713],
                        [-0.306287169456,-0.123895764351,0.943842172623],
                        [-0.274516820908,-0.190361812711,0.942551255226],
                        [-0.199805602431,-0.193975359201,0.960443258286],
                        [-0.239766731858,-0.258633822203,0.935745954514],
                        [-0.306287169456,-0.123895764351,0.943842172623],
                        [-0.274516820908,-0.190361812711,0.942551255226],
                        [-0.34457308054,-0.185843646526,0.920180141926],
                        [0.276221334934,-0.446935534477,0.85085272789],
                        [0.313733518124,-0.380723625422,0.869839549065],
                        [0.346611320972,-0.436200261116,0.830415487289],
                        [0.202408134937,-0.327503234148,0.922915279865],
                        [0.239766731858,-0.258633822203,0.935745954514],
                        [0.277958005667,-0.321246802807,0.905284404755],
                        [0.348686188459,-0.313436716795,0.883275330067],
                        [0.380633711815,-0.246351331472,0.891307473183],
                        [0.413926929235,-0.3044308424,0.857896447182],
                        [0.277958005667,-0.321246802807,0.905284404755],
                        [0.348686188459,-0.313436716795,0.883275330067],
                        [0.313733518124,-0.380723625422,0.869839549065],
                        [0.121444880962,-0.196501940489,0.97295331955],
                        [0.158833146095,-0.128498718143,0.978907585144],
                        [0.199805602431,-0.193975359201,0.960443258286],
                        [0.0394601933658,-0.0638479366899,0.997179210186],
                        [0.0770247355103,0.0,0.997029185295],
                        [0.117650069296,-0.0634539350867,0.991025745869],
                        [0.193714544177,-0.0626873448491,0.979053080082],
                        [0.225778326392,0.0,0.974178731441],
                        [0.266443610191,-0.0615878328681,0.961880862713],
                        [0.117650069296,-0.0634539350867,0.991025745869],
                        [0.193714544177,-0.0626873448491,0.979053080082],
                        [0.158833146095,-0.128498718143,0.978907585144],
                        [0.409316182137,-0.180623859167,0.894335091114],
                        [0.434652328491,-0.117213711143,0.892938017845],
                        [0.468421578407,-0.174905076623,0.866019308567],
                        [0.334895044565,-0.0602079555392,0.940329909325],
                        [0.360324263573,0.0,0.932827115059],
                        [0.398431301117,-0.0586068555713,0.915323853493],
                        [0.456712335348,-0.0568443164229,0.887796461582],
                        [0.475679844618,0.0,0.8796184659],
                        [0.509656965733,-0.0549761541188,0.858619451523],
                        [0.398431301117,-0.0586068555713,0.915323853493],
                        [0.456712335348,-0.0568443164229,0.887796461582],
                        [0.434652328491,-0.117213711143,0.892938017845],
                        [0.199805602431,-0.193975359201,0.960443258286],
                        [0.274516820908,-0.190361812711,0.942551255226],
                        [0.239766731858,-0.258633822203,0.935745954514],
                        [0.266443610191,-0.0615878328681,0.961880862713],
                        [0.334895044565,-0.0602079555392,0.940329909325],
                        [0.306287169456,-0.123895764351,0.943842172623],
                        [0.34457308054,-0.185843646526,0.920180141926],
                        [0.409316182137,-0.180623859167,0.894335091114],
                        [0.380633711815,-0.246351331472,0.891307473183],
                        [0.306287169456,-0.123895764351,0.943842172623],
                        [0.34457308054,-0.185843646526,0.920180141926],
                        [0.274516820908,-0.190361812711,0.942551255226],
                        [-0.276221334934,-0.446935534477,0.85085272789],
                        [-0.20109423995,-0.455528259277,0.867211103439],
                        [-0.236761152744,-0.510783493519,0.826465010643],
                        [-0.202408134937,-0.327503234148,0.922915279865],
                        [-0.123069040477,-0.33188316226,0.935258030891],
                        [-0.162998497486,-0.395605653524,0.903840482235],
                        [-0.122248865664,-0.461539924145,0.878655850887],
                        [-0.0410230122507,-0.464636415243,0.88455080986],
                        [-0.0809632539749,-0.524005174637,0.847858190536],
                        [-0.162998497486,-0.395605653524,0.903840482235],
                        [-0.122248865664,-0.461539924145,0.878655850887],
                        [-0.20109423995,-0.455528259277,0.867211103439],
                        [-0.121444880962,-0.196501940489,0.97295331955],
                        [-0.0407496243715,-0.197802826762,0.979394435883],
                        [-0.0820460245013,-0.265506535769,0.960611641407],
                        [-0.0394601933658,-0.0638479366899,0.997179210186],
                        [0.0394601933658,-0.0638479366899,0.997179210186],
                        [0.0,-0.130150929093,0.991494178772],
                        [0.0407496243715,-0.197802826762,0.979394435883],
                        [0.121444880962,-0.196501940489,0.97295331955],
                        [0.0820460245013,-0.265506535769,0.960611641407],
                        [0.0,-0.130150929093,0.991494178772],
                        [0.0407496243715,-0.197802826762,0.979394435883],
                        [-0.0407496243715,-0.197802826762,0.979394435883],
                        [0.0410230122507,-0.464636415243,0.88455080986],
                        [0.122248865664,-0.461539924145,0.878655850887],
                        [0.0809632539749,-0.524005174637,0.847858190536],
                        [0.123069040477,-0.33188316226,0.935258030891],
                        [0.202408134937,-0.327503234148,0.922915279865],
                        [0.162998497486,-0.395605653524,0.903840482235],
                        [0.20109423995,-0.455528259277,0.867211103439],
                        [0.276221334934,-0.446935534477,0.85085272789],
                        [0.236761152744,-0.510783493519,0.826465010643],
                        [0.162998497486,-0.395605653524,0.903840482235],
                        [0.20109423995,-0.455528259277,0.867211103439],
                        [0.122248865664,-0.461539924145,0.878655850887],
                        [-0.0820460245013,-0.265506535769,0.960611641407],
                        [-0.04130198434,-0.334140062332,0.941618084908],
                        [-0.123069040477,-0.33188316226,0.935258030891],
                        [0.0820460245013,-0.265506535769,0.960611641407],
                        [0.123069040477,-0.33188316226,0.935258030891],
                        [0.04130198434,-0.334140062332,0.941618084908],
                        [0.0,-0.400968074799,0.916092038155],
                        [0.0410230122507,-0.464636415243,0.88455080986],
                        [-0.0410230122507,-0.464636415243,0.88455080986],
                        [0.04130198434,-0.334140062332,0.941618084908],
                        [0.0,-0.400968074799,0.916092038155],
                        [-0.04130198434,-0.334140062332,0.941618084908],
                        [0.0339771322906,-0.82464236021,0.564633131027],
                        [0.091976031661,-0.830952167511,0.548688352108],
                        [0.0549761541188,-0.858619451523,0.509656965733],
                        [0.108097285032,-0.757922053337,0.643326640129],
                        [0.171839639544,-0.759706020355,0.627150595188],
                        [0.131048902869,-0.798110127449,0.588087081909],
                        [0.153434738517,-0.834331154823,0.529480218887],
                        [0.217834427953,-0.834127128124,0.506734728813],
                        [0.174905076623,-0.866019308567,0.468421578407],
                        [0.131048902869,-0.798110127449,0.588087081909],
                        [0.153434738517,-0.834331154823,0.529480218887],
                        [0.091976031661,-0.830952167511,0.548688352108],
                        [0.188148602843,-0.669747889042,0.718357801437],
                        [0.256401896477,-0.665616393089,0.700865805149],
                        [0.213841319084,-0.715529501438,0.665048420429],
                        [0.269586592913,-0.560828924179,0.782811582088],
                        [0.340069264174,-0.550243675709,0.762617051601],
                        [0.298754066229,-0.610302150249,0.733673810959],
                        [0.327040165663,-0.657660841942,0.678621411324],
                        [0.398910075426,-0.645450055599,0.65135627985],
                        [0.353819847107,-0.701809465885,0.618283927441],
                        [0.298754066229,-0.610302150249,0.733673810959],
                        [0.327040165663,-0.657660841942,0.678621411324],
                        [0.256401896477,-0.665616393089,0.700865805149],
                        [0.284414708614,-0.829719662666,0.480284929276],
                        [0.352179646492,-0.820587992668,0.450116455555],
                        [0.3044308424,-0.857896447182,0.413926929235],
                        [0.378517180681,-0.74177056551,0.553625464439],
                        [0.44894811511,-0.726413309574,0.520354926586],
                        [0.400663375854,-0.776785671711,0.485873311758],
                        [0.419940322638,-0.806385576725,0.416404157877],
                        [0.486395716667,-0.787004828453,0.379529476166],
                        [0.436200261116,-0.830415487289,0.346611320972],
                        [0.400663375854,-0.776785671711,0.485873311758],
                        [0.419940322638,-0.806385576725,0.416404157877],
                        [0.352179646492,-0.820587992668,0.450116455555],
                        [0.213841319084,-0.715529501438,0.665048420429],
                        [0.238753452897,-0.757998526096,0.606988489628],
                        [0.171839639544,-0.759706020355,0.627150595188],
                        [0.353819847107,-0.701809465885,0.618283927441],
                        [0.378517180681,-0.74177056551,0.553625464439],
                        [0.308011889458,-0.752189457417,0.582528710365],
                        [0.26241543889,-0.796284377575,0.545040607452],
                        [0.284414708614,-0.829719662666,0.480284929276],
                        [0.217834427953,-0.834127128124,0.506734728813],
                        [0.308011889458,-0.752189457417,0.582528710365],
                        [0.26241543889,-0.796284377575,0.545040607452],
                        [0.238753452897,-0.757998526096,0.606988489628],
                        [0.346611320972,-0.436200261116,0.830415487289],
                        [0.416404157877,-0.419940322638,0.806385576725],
                        [0.379529476166,-0.486395716667,0.787004828453],
                        [0.413926929235,-0.3044308424,0.857896447182],
                        [0.480284929276,-0.284414708614,0.829719662666],
                        [0.450116455555,-0.352179646492,0.820587992668],
                        [0.485873311758,-0.400663375854,0.776785671711],
                        [0.553625464439,-0.378517180681,0.74177056551],
                        [0.520354926586,-0.44894811511,0.726413309574],
                        [0.450116455555,-0.352179646492,0.820587992668],
                        [0.485873311758,-0.400663375854,0.776785671711],
                        [0.416404157877,-0.419940322638,0.806385576725],
                        [0.468421578407,-0.174905076623,0.866019308567],
                        [0.529480218887,-0.153434738517,0.834331154823],
                        [0.506734728813,-0.217834427953,0.834127128124],
                        [0.509656965733,-0.0549761541188,0.858619451523],
                        [0.564633131027,-0.0339771322906,0.82464236021],
                        [0.548688352108,-0.091976031661,0.830952167511],
                        [0.588087081909,-0.131048902869,0.798110127449],
                        [0.643326640129,-0.108097285032,0.757922053337],
                        [0.627150595188,-0.171839639544,0.759706020355],
                        [0.548688352108,-0.091976031661,0.830952167511],
                        [0.588087081909,-0.131048902869,0.798110127449],
                        [0.529480218887,-0.153434738517,0.834331154823],
                        [0.618283927441,-0.353819847107,0.701809465885],
                        [0.678621411324,-0.327040165663,0.657660841942],
                        [0.65135627985,-0.398910075426,0.645450055599],
                        [0.665048420429,-0.213841319084,0.715529501438],
                        [0.718357801437,-0.188148602843,0.669747889042],
                        [0.700865805149,-0.256401896477,0.665616393089],
                        [0.733673810959,-0.298754066229,0.610302150249],
                        [0.782811582088,-0.269586592913,0.560828924179],
                        [0.762617051601,-0.340069264174,0.550243675709],
                        [0.700865805149,-0.256401896477,0.665616393089],
                        [0.733673810959,-0.298754066229,0.610302150249],
                        [0.678621411324,-0.327040165663,0.657660841942],
                        [0.506734728813,-0.217834427953,0.834127128124],
                        [0.545040607452,-0.26241543889,0.796284377575],
                        [0.480284929276,-0.284414708614,0.829719662666],
                        [0.627150595188,-0.171839639544,0.759706020355],
                        [0.665048420429,-0.213841319084,0.715529501438],
                        [0.606988489628,-0.238753452897,0.757998526096],
                        [0.582528710365,-0.308011889458,0.752189457417],
                        [0.618283927441,-0.353819847107,0.701809465885],
                        [0.553625464439,-0.378517180681,0.74177056551],
                        [0.606988489628,-0.238753452897,0.757998526096],
                        [0.582528710365,-0.308011889458,0.752189457417],
                        [0.545040607452,-0.26241543889,0.796284377575],
                        [0.550243675709,-0.762617051601,0.340069264174],
                        [0.610302150249,-0.733673810959,0.298754066229],
                        [0.560828924179,-0.782811582088,0.269586592913],
                        [0.645450055599,-0.65135627985,0.398910075426],
                        [0.701809465885,-0.618283927441,0.353819847107],
                        [0.657660841942,-0.678621411324,0.327040165663],
                        [0.665616393089,-0.700865805149,0.256401896477],
                        [0.715529501438,-0.665048420429,0.213841319084],
                        [0.669747889042,-0.718357801437,0.188148602843],
                        [0.657660841942,-0.678621411324,0.327040165663],
                        [0.665616393089,-0.700865805149,0.256401896477],
                        [0.610302150249,-0.733673810959,0.298754066229],
                        [0.726413309574,-0.520354926586,0.44894811511],
                        [0.776785671711,-0.485873311758,0.400663375854],
                        [0.74177056551,-0.553625464439,0.378517180681],
                        [0.787004828453,-0.379529476166,0.486395716667],
                        [0.830415487289,-0.346611320972,0.436200261116],
                        [0.806385576725,-0.416404157877,0.419940322638],
                        [0.820587992668,-0.450116455555,0.352179646492],
                        [0.857896447182,-0.413926929235,0.3044308424],
                        [0.829719662666,-0.480284929276,0.284414708614],
                        [0.806385576725,-0.416404157877,0.419940322638],
                        [0.820587992668,-0.450116455555,0.352179646492],
                        [0.776785671711,-0.485873311758,0.400663375854],
                        [0.759706020355,-0.627150595188,0.171839639544],
                        [0.798110127449,-0.588087081909,0.131048902869],
                        [0.757922053337,-0.643326640129,0.108097285032],
                        [0.834127128124,-0.506734728813,0.217834427953],
                        [0.866019308567,-0.468421578407,0.174905076623],
                        [0.834331154823,-0.529480218887,0.153434738517],
                        [0.830952167511,-0.548688352108,0.091976031661],
                        [0.858619451523,-0.509656965733,0.0549761541188],
                        [0.82464236021,-0.564633131027,0.0339771322906],
                        [0.834331154823,-0.529480218887,0.153434738517],
                        [0.830952167511,-0.548688352108,0.091976031661],
                        [0.798110127449,-0.588087081909,0.131048902869],
                        [0.74177056551,-0.553625464439,0.378517180681],
                        [0.752189457417,-0.582528710365,0.308011889458],
                        [0.701809465885,-0.618283927441,0.353819847107],
                        [0.829719662666,-0.480284929276,0.284414708614],
                        [0.834127128124,-0.506734728813,0.217834427953],
                        [0.796284377575,-0.545040607452,0.26241543889],
                        [0.757998526096,-0.606988489628,0.238753452897],
                        [0.759706020355,-0.627150595188,0.171839639544],
                        [0.715529501438,-0.665048420429,0.213841319084],
                        [0.796284377575,-0.545040607452,0.26241543889],
                        [0.757998526096,-0.606988489628,0.238753452897],
                        [0.752189457417,-0.582528710365,0.308011889458],
                        [0.379529476166,-0.486395716667,0.787004828453],
                        [0.411682873964,-0.535965919495,0.737060189247],
                        [0.340069264174,-0.550243675709,0.762617051601],
                        [0.520354926586,-0.44894811511,0.726413309574],
                        [0.552667617798,-0.495975226164,0.669751524925],
                        [0.483050197363,-0.517854511738,0.706037700176],
                        [0.44230055809,-0.58378881216,0.680853009224],
                        [0.470621615648,-0.628728508949,0.619044244289],
                        [0.398910075426,-0.645450055599,0.65135627985],
                        [0.483050197363,-0.517854511738,0.706037700176],
                        [0.44230055809,-0.58378881216,0.680853009224],
                        [0.411682873964,-0.535965919495,0.737060189247],
                        [0.65135627985,-0.398910075426,0.645450055599],
                        [0.680853009224,-0.44230055809,0.58378881216],
                        [0.619044244289,-0.470621615648,0.628728508949],
                        [0.762617051601,-0.340069264174,0.550243675709],
                        [0.787004828453,-0.379529476166,0.486395716667],
                        [0.737060189247,-0.411682873964,0.535965919495],
                        [0.706037700176,-0.483050197363,0.517854511738],
                        [0.726413309574,-0.520354926586,0.44894811511],
                        [0.669751524925,-0.552667617798,0.495975226164],
                        [0.737060189247,-0.411682873964,0.535965919495],
                        [0.706037700176,-0.483050197363,0.517854511738],
                        [0.680853009224,-0.44230055809,0.58378881216],
                        [0.495975226164,-0.669751524925,0.552667617798],
                        [0.517854511738,-0.706037700176,0.483050197363],
                        [0.44894811511,-0.726413309574,0.520354926586],
                        [0.628728508949,-0.619044244289,0.470621615648],
                        [0.645450055599,-0.65135627985,0.398910075426],
                        [0.58378881216,-0.680853009224,0.44230055809],
                        [0.535965919495,-0.737060189247,0.411682873964],
                        [0.550243675709,-0.762617051601,0.340069264174],
                        [0.486395716667,-0.787004828453,0.379529476166],
                        [0.58378881216,-0.680853009224,0.44230055809],
                        [0.535965919495,-0.737060189247,0.411682873964],
                        [0.517854511738,-0.706037700176,0.483050197363],
                        [0.619044244289,-0.470621615648,0.628728508949],
                        [0.581951975822,-0.540649950504,0.607478022575],
                        [0.552667617798,-0.495975226164,0.669751524925],
                        [0.669751524925,-0.552667617798,0.495975226164],
                        [0.628728508949,-0.619044244289,0.470621615648],
                        [0.607478022575,-0.581951975822,0.540649950504],
                        [0.540649950504,-0.607478022575,0.581951975822],
                        [0.495975226164,-0.669751524925,0.552667617798],
                        [0.470621615648,-0.628728508949,0.619044244289],
                        [0.607478022575,-0.581951975822,0.540649950504],
                        [0.540649950504,-0.607478022575,0.581951975822],
                        [0.581951975822,-0.540649950504,0.607478022575],
                        [0.82464236021,-0.564633131027,-0.0339771322906],
                        [0.79582041502,-0.605532705784,0.0],
                        [0.82464236021,-0.564633131027,0.0339771322906],
                        [0.757922053337,-0.643326640129,-0.108097285032],
                        [0.722495436668,-0.687358558178,-0.0744211226702],
                        [0.761889100075,-0.646693944931,-0.0362210273743],
                        [0.761889100075,-0.646693944931,0.0362210273743],
                        [0.722495436668,-0.687358558178,0.0744211226702],
                        [0.757922053337,-0.643326640129,0.108097285032],
                        [0.761889100075,-0.646693944931,-0.0362210273743],
                        [0.761889100075,-0.646693944931,0.0362210273743],
                        [0.79582041502,-0.605532705784,0.0],
                        [0.669747889042,-0.718357801437,-0.188148602843],
                        [0.62687343359,-0.763553202152,-0.154971644282],
                        [0.677466154099,-0.726636230946,-0.114190116525],
                        [0.560828924179,-0.782811582088,-0.269586592913],
                        [0.510783493519,-0.826465010643,-0.236761152744],
                        [0.571085453033,-0.797127783298,-0.196083456278],
                        [0.578244268894,-0.807120084763,-0.119124859571],
                        [0.524005174637,-0.847858190536,-0.0809632539749],
                        [0.581926107407,-0.81225925684,-0.0399611219764],
                        [0.571085453033,-0.797127783298,-0.196083456278],
                        [0.578244268894,-0.807120084763,-0.119124859571],
                        [0.62687343359,-0.763553202152,-0.154971644282],
                        [0.677466154099,-0.726636230946,0.114190116525],
                        [0.62687343359,-0.763553202152,0.154971644282],
                        [0.669747889042,-0.718357801437,0.188148602843],
                        [0.581926107407,-0.81225925684,0.0399611219764],
                        [0.524005174637,-0.847858190536,0.0809632539749],
                        [0.578244268894,-0.807120084763,0.119124859571],
                        [0.571085453033,-0.797127783298,0.196083456278],
                        [0.510783493519,-0.826465010643,0.236761152744],
                        [0.560828924179,-0.782811582088,0.269586592913],
                        [0.578244268894,-0.807120084763,0.119124859571],
                        [0.571085453033,-0.797127783298,0.196083456278],
                        [0.62687343359,-0.763553202152,0.154971644282],
                        [0.677466154099,-0.726636230946,-0.114190116525],
                        [0.68142670393,-0.730884253979,-0.0382858961821],
                        [0.722495436668,-0.687358558178,-0.0744211226702],
                        [0.581926107407,-0.81225925684,-0.0399611219764],
                        [0.581926107407,-0.81225925684,0.0399611219764],
                        [0.634539365768,-0.772890508175,0.0],
                        [0.68142670393,-0.730884253979,0.0382858961821],
                        [0.677466154099,-0.726636230946,0.114190116525],
                        [0.722495436668,-0.687358558178,0.0744211226702],
                        [0.634539365768,-0.772890508175,0.0],
                        [0.68142670393,-0.730884253979,0.0382858961821],
                        [0.68142670393,-0.730884253979,-0.0382858961821],
                        [0.436200261116,-0.830415487289,-0.346611320972],
                        [0.380723625422,-0.869839549065,-0.313733518124],
                        [0.446935534477,-0.85085272789,-0.276221334934],
                        [0.3044308424,-0.857896447182,-0.413926929235],
                        [0.246351331472,-0.891307473183,-0.380633711815],
                        [0.313436716795,-0.883275330067,-0.348686188459],
                        [0.321246802807,-0.905284404755,-0.277958005667],
                        [0.258633822203,-0.935745954514,-0.239766731858],
                        [0.327503234148,-0.922915279865,-0.202408134937],
                        [0.313436716795,-0.883275330067,-0.348686188459],
                        [0.321246802807,-0.905284404755,-0.277958005667],
                        [0.380723625422,-0.869839549065,-0.313733518124],
                        [0.174905076623,-0.866019308567,-0.468421578407],
                        [0.117213711143,-0.892938017845,-0.434652328491],
                        [0.180623859167,-0.894335091114,-0.409316182137],
                        [0.0549761541188,-0.858619451523,-0.509656965733],
                        [0.0,-0.8796184659,-0.475679844618],
                        [0.0568443164229,-0.887796461582,-0.456712335348],
                        [0.0586068555713,-0.915323853493,-0.398431301117],
                        [0.0,-0.932827115059,-0.360324263573],
                        [0.0602079555392,-0.940329909325,-0.334895044565],
                        [0.0568443164229,-0.887796461582,-0.456712335348],
                        [0.0586068555713,-0.915323853493,-0.398431301117],
                        [0.117213711143,-0.892938017845,-0.434652328491],
                        [0.193975359201,-0.960443258286,-0.199805602431],
                        [0.128498718143,-0.978907585144,-0.158833146095],
                        [0.196501940489,-0.97295331955,-0.121444880962],
                        [0.0615878328681,-0.961880862713,-0.266443610191],
                        [0.0,-0.974178731441,-0.225778326392],
                        [0.0626873448491,-0.979053080082,-0.193714544177],
                        [0.0634539350867,-0.991025745869,-0.117650069296],
                        [0.0,-0.997029185295,-0.0770247355103],
                        [0.0638479366899,-0.997179210186,-0.0394601933658],
                        [0.0626873448491,-0.979053080082,-0.193714544177],
                        [0.0634539350867,-0.991025745869,-0.117650069296],
                        [0.128498718143,-0.978907585144,-0.158833146095],
                        [0.180623859167,-0.894335091114,-0.409316182137],
                        [0.185843646526,-0.920180141926,-0.34457308054],
                        [0.246351331472,-0.891307473183,-0.380633711815],
                        [0.0602079555392,-0.940329909325,-0.334895044565],
                        [0.0615878328681,-0.961880862713,-0.266443610191],
                        [0.123895764351,-0.943842172623,-0.306287169456],
                        [0.190361812711,-0.942551255226,-0.274516820908],
                        [0.193975359201,-0.960443258286,-0.199805602431],
                        [0.258633822203,-0.935745954514,-0.239766731858],
                        [0.123895764351,-0.943842172623,-0.306287169456],
                        [0.190361812711,-0.942551255226,-0.274516820908],
                        [0.185843646526,-0.920180141926,-0.34457308054],
                        [0.446935534477,-0.85085272789,0.276221334934],
                        [0.380723625422,-0.869839549065,0.313733518124],
                        [0.436200261116,-0.830415487289,0.346611320972],
                        [0.327503234148,-0.922915279865,0.202408134937],
                        [0.258633822203,-0.935745954514,0.239766731858],
                        [0.321246802807,-0.905284404755,0.277958005667],
                        [0.313436716795,-0.883275330067,0.348686188459],
                        [0.246351331472,-0.891307473183,0.380633711815],
                        [0.3044308424,-0.857896447182,0.413926929235],
                        [0.321246802807,-0.905284404755,0.277958005667],
                        [0.313436716795,-0.883275330067,0.348686188459],
                        [0.380723625422,-0.869839549065,0.313733518124],
                        [0.196501940489,-0.97295331955,0.121444880962],
                        [0.128498718143,-0.978907585144,0.158833146095],
                        [0.193975359201,-0.960443258286,0.199805602431],
                        [0.0638479366899,-0.997179210186,0.0394601933658],
                        [0.0,-0.997029185295,0.0770247355103],
                        [0.0634539350867,-0.991025745869,0.117650069296],
                        [0.0626873448491,-0.979053080082,0.193714544177],
                        [0.0,-0.974178731441,0.225778326392],
                        [0.0615878328681,-0.961880862713,0.266443610191],
                        [0.0634539350867,-0.991025745869,0.117650069296],
                        [0.0626873448491,-0.979053080082,0.193714544177],
                        [0.128498718143,-0.978907585144,0.158833146095],
                        [0.180623859167,-0.894335091114,0.409316182137],
                        [0.117213711143,-0.892938017845,0.434652328491],
                        [0.174905076623,-0.866019308567,0.468421578407],
                        [0.0602079555392,-0.940329909325,0.334895044565],
                        [0.0,-0.932827115059,0.360324263573],
                        [0.0586068555713,-0.915323853493,0.398431301117],
                        [0.0568443164229,-0.887796461582,0.456712335348],
                        [0.0,-0.8796184659,0.475679844618],
                        [0.0549761541188,-0.858619451523,0.509656965733],
                        [0.0586068555713,-0.915323853493,0.398431301117],
                        [0.0568443164229,-0.887796461582,0.456712335348],
                        [0.117213711143,-0.892938017845,0.434652328491],
                        [0.193975359201,-0.960443258286,0.199805602431],
                        [0.190361812711,-0.942551255226,0.274516820908],
                        [0.258633822203,-0.935745954514,0.239766731858],
                        [0.0615878328681,-0.961880862713,0.266443610191],
                        [0.0602079555392,-0.940329909325,0.334895044565],
                        [0.123895764351,-0.943842172623,0.306287169456],
                        [0.185843646526,-0.920180141926,0.34457308054],
                        [0.180623859167,-0.894335091114,0.409316182137],
                        [0.246351331472,-0.891307473183,0.380633711815],
                        [0.123895764351,-0.943842172623,0.306287169456],
                        [0.185843646526,-0.920180141926,0.34457308054],
                        [0.190361812711,-0.942551255226,0.274516820908],
                        [0.446935534477,-0.85085272789,-0.276221334934],
                        [0.455528259277,-0.867211103439,-0.20109423995],
                        [0.510783493519,-0.826465010643,-0.236761152744],
                        [0.327503234148,-0.922915279865,-0.202408134937],
                        [0.33188316226,-0.935258030891,-0.123069040477],
                        [0.395605653524,-0.903840482235,-0.162998497486],
                        [0.461539924145,-0.878655850887,-0.122248865664],
                        [0.464636415243,-0.88455080986,-0.0410230122507],
                        [0.524005174637,-0.847858190536,-0.0809632539749],
                        [0.395605653524,-0.903840482235,-0.162998497486],
                        [0.461539924145,-0.878655850887,-0.122248865664],
                        [0.455528259277,-0.867211103439,-0.20109423995],
                        [0.196501940489,-0.97295331955,-0.121444880962],
                        [0.197802826762,-0.979394435883,-0.0407496243715],
                        [0.265506535769,-0.960611641407,-0.0820460245013],
                        [0.0638479366899,-0.997179210186,-0.0394601933658],
                        [0.0638479366899,-0.997179210186,0.0394601933658],
                        [0.130150929093,-0.991494178772,0.0],
                        [0.197802826762,-0.979394435883,0.0407496243715],
                        [0.196501940489,-0.97295331955,0.121444880962],
                        [0.265506535769,-0.960611641407,0.0820460245013],
                        [0.130150929093,-0.991494178772,0.0],
                        [0.197802826762,-0.979394435883,0.0407496243715],
                        [0.197802826762,-0.979394435883,-0.0407496243715],
                        [0.464636415243,-0.88455080986,0.0410230122507],
                        [0.461539924145,-0.878655850887,0.122248865664],
                        [0.524005174637,-0.847858190536,0.0809632539749],
                        [0.33188316226,-0.935258030891,0.123069040477],
                        [0.327503234148,-0.922915279865,0.202408134937],
                        [0.395605653524,-0.903840482235,0.162998497486],
                        [0.455528259277,-0.867211103439,0.20109423995],
                        [0.446935534477,-0.85085272789,0.276221334934],
                        [0.510783493519,-0.826465010643,0.236761152744],
                        [0.395605653524,-0.903840482235,0.162998497486],
                        [0.455528259277,-0.867211103439,0.20109423995],
                        [0.461539924145,-0.878655850887,0.122248865664],
                        [0.265506535769,-0.960611641407,-0.0820460245013],
                        [0.334140062332,-0.941618084908,-0.04130198434],
                        [0.33188316226,-0.935258030891,-0.123069040477],
                        [0.265506535769,-0.960611641407,0.0820460245013],
                        [0.33188316226,-0.935258030891,0.123069040477],
                        [0.334140062332,-0.941618084908,0.04130198434],
                        [0.400968074799,-0.916092038155,0.0],
                        [0.464636415243,-0.88455080986,0.0410230122507],
                        [0.464636415243,-0.88455080986,-0.0410230122507],
                        [0.334140062332,-0.941618084908,0.04130198434],
                        [0.400968074799,-0.916092038155,0.0],
                        [0.334140062332,-0.941618084908,-0.04130198434],
                        [-0.82464236021,-0.564633131027,-0.0339771322906],
                        [-0.830952167511,-0.548688352108,-0.091976031661],
                        [-0.858619451523,-0.509656965733,-0.0549761541188],
                        [-0.757922053337,-0.643326640129,-0.108097285032],
                        [-0.759706020355,-0.627150595188,-0.171839639544],
                        [-0.798110127449,-0.588087081909,-0.131048902869],
                        [-0.834331154823,-0.529480218887,-0.153434738517],
                        [-0.834127128124,-0.506734728813,-0.217834427953],
                        [-0.866019308567,-0.468421578407,-0.174905076623],
                        [-0.798110127449,-0.588087081909,-0.131048902869],
                        [-0.834331154823,-0.529480218887,-0.153434738517],
                        [-0.830952167511,-0.548688352108,-0.091976031661],
                        [-0.669747889042,-0.718357801437,-0.188148602843],
                        [-0.665616393089,-0.700865805149,-0.256401896477],
                        [-0.715529501438,-0.665048420429,-0.213841319084],
                        [-0.560828924179,-0.782811582088,-0.269586592913],
                        [-0.550243675709,-0.762617051601,-0.340069264174],
                        [-0.610302150249,-0.733673810959,-0.298754066229],
                        [-0.657660841942,-0.678621411324,-0.327040165663],
                        [-0.645450055599,-0.65135627985,-0.398910075426],
                        [-0.701809465885,-0.618283927441,-0.353819847107],
                        [-0.610302150249,-0.733673810959,-0.298754066229],
                        [-0.657660841942,-0.678621411324,-0.327040165663],
                        [-0.665616393089,-0.700865805149,-0.256401896477],
                        [-0.829719662666,-0.480284929276,-0.284414708614],
                        [-0.820587992668,-0.450116455555,-0.352179646492],
                        [-0.857896447182,-0.413926929235,-0.3044308424],
                        [-0.74177056551,-0.553625464439,-0.378517180681],
                        [-0.726413309574,-0.520354926586,-0.44894811511],
                        [-0.776785671711,-0.485873311758,-0.400663375854],
                        [-0.806385576725,-0.416404157877,-0.419940322638],
                        [-0.787004828453,-0.379529476166,-0.486395716667],
                        [-0.830415487289,-0.346611320972,-0.436200261116],
                        [-0.776785671711,-0.485873311758,-0.400663375854],
                        [-0.806385576725,-0.416404157877,-0.419940322638],
                        [-0.820587992668,-0.450116455555,-0.352179646492],
                        [-0.715529501438,-0.665048420429,-0.213841319084],
                        [-0.757998526096,-0.606988489628,-0.238753452897],
                        [-0.759706020355,-0.627150595188,-0.171839639544],
                        [-0.701809465885,-0.618283927441,-0.353819847107],
                        [-0.74177056551,-0.553625464439,-0.378517180681],
                        [-0.752189457417,-0.582528710365,-0.308011889458],
                        [-0.796284377575,-0.545040607452,-0.26241543889],
                        [-0.829719662666,-0.480284929276,-0.284414708614],
                        [-0.834127128124,-0.506734728813,-0.217834427953],
                        [-0.752189457417,-0.582528710365,-0.308011889458],
                        [-0.796284377575,-0.545040607452,-0.26241543889],
                        [-0.757998526096,-0.606988489628,-0.238753452897],
                        [-0.436200261116,-0.830415487289,-0.346611320972],
                        [-0.419940322638,-0.806385576725,-0.416404157877],
                        [-0.486395716667,-0.787004828453,-0.379529476166],
                        [-0.3044308424,-0.857896447182,-0.413926929235],
                        [-0.284414708614,-0.829719662666,-0.480284929276],
                        [-0.352179646492,-0.820587992668,-0.450116455555],
                        [-0.400663375854,-0.776785671711,-0.485873311758],
                        [-0.378517180681,-0.74177056551,-0.553625464439],
                        [-0.44894811511,-0.726413309574,-0.520354926586],
                        [-0.352179646492,-0.820587992668,-0.450116455555],
                        [-0.400663375854,-0.776785671711,-0.485873311758],
                        [-0.419940322638,-0.806385576725,-0.416404157877],
                        [-0.174905076623,-0.866019308567,-0.468421578407],
                        [-0.153434738517,-0.834331154823,-0.529480218887],
                        [-0.217834427953,-0.834127128124,-0.506734728813],
                        [-0.0549761541188,-0.858619451523,-0.509656965733],
                        [-0.0339771322906,-0.82464236021,-0.564633131027],
                        [-0.091976031661,-0.830952167511,-0.548688352108],
                        [-0.131048902869,-0.798110127449,-0.588087081909],
                        [-0.108097285032,-0.757922053337,-0.643326640129],
                        [-0.171839639544,-0.759706020355,-0.627150595188],
                        [-0.091976031661,-0.830952167511,-0.548688352108],
                        [-0.131048902869,-0.798110127449,-0.588087081909],
                        [-0.153434738517,-0.834331154823,-0.529480218887],
                        [-0.353819847107,-0.701809465885,-0.618283927441],
                        [-0.327040165663,-0.657660841942,-0.678621411324],
                        [-0.398910075426,-0.645450055599,-0.65135627985],
                        [-0.213841319084,-0.715529501438,-0.665048420429],
                        [-0.188148602843,-0.669747889042,-0.718357801437],
                        [-0.256401896477,-0.665616393089,-0.700865805149],
                        [-0.298754066229,-0.610302150249,-0.733673810959],
                        [-0.269586592913,-0.560828924179,-0.782811582088],
                        [-0.340069264174,-0.550243675709,-0.762617051601],
                        [-0.256401896477,-0.665616393089,-0.700865805149],
                        [-0.298754066229,-0.610302150249,-0.733673810959],
                        [-0.327040165663,-0.657660841942,-0.678621411324],
                        [-0.217834427953,-0.834127128124,-0.506734728813],
                        [-0.26241543889,-0.796284377575,-0.545040607452],
                        [-0.284414708614,-0.829719662666,-0.480284929276],
                        [-0.171839639544,-0.759706020355,-0.627150595188],
                        [-0.213841319084,-0.715529501438,-0.665048420429],
                        [-0.238753452897,-0.757998526096,-0.606988489628],
                        [-0.308011889458,-0.752189457417,-0.582528710365],
                        [-0.353819847107,-0.701809465885,-0.618283927441],
                        [-0.378517180681,-0.74177056551,-0.553625464439],
                        [-0.238753452897,-0.757998526096,-0.606988489628],
                        [-0.308011889458,-0.752189457417,-0.582528710365],
                        [-0.26241543889,-0.796284377575,-0.545040607452],
                        [-0.762617051601,-0.340069264174,-0.550243675709],
                        [-0.733673810959,-0.298754066229,-0.610302150249],
                        [-0.782811582088,-0.269586592913,-0.560828924179],
                        [-0.65135627985,-0.398910075426,-0.645450055599],
                        [-0.618283927441,-0.353819847107,-0.701809465885],
                        [-0.678621411324,-0.327040165663,-0.657660841942],
                        [-0.700865805149,-0.256401896477,-0.665616393089],
                        [-0.665048420429,-0.213841319084,-0.715529501438],
                        [-0.718357801437,-0.188148602843,-0.669747889042],
                        [-0.678621411324,-0.327040165663,-0.657660841942],
                        [-0.700865805149,-0.256401896477,-0.665616393089],
                        [-0.733673810959,-0.298754066229,-0.610302150249],
                        [-0.520354926586,-0.44894811511,-0.726413309574],
                        [-0.485873311758,-0.400663375854,-0.776785671711],
                        [-0.553625464439,-0.378517180681,-0.74177056551],
                        [-0.379529476166,-0.486395716667,-0.787004828453],
                        [-0.346611320972,-0.436200261116,-0.830415487289],
                        [-0.416404157877,-0.419940322638,-0.806385576725],
                        [-0.450116455555,-0.352179646492,-0.820587992668],
                        [-0.413926929235,-0.3044308424,-0.857896447182],
                        [-0.480284929276,-0.284414708614,-0.829719662666],
                        [-0.416404157877,-0.419940322638,-0.806385576725],
                        [-0.450116455555,-0.352179646492,-0.820587992668],
                        [-0.485873311758,-0.400663375854,-0.776785671711],
                        [-0.627150595188,-0.171839639544,-0.759706020355],
                        [-0.588087081909,-0.131048902869,-0.798110127449],
                        [-0.643326640129,-0.108097285032,-0.757922053337],
                        [-0.506734728813,-0.217834427953,-0.834127128124],
                        [-0.468421578407,-0.174905076623,-0.866019308567],
                        [-0.529480218887,-0.153434738517,-0.834331154823],
                        [-0.548688352108,-0.091976031661,-0.830952167511],
                        [-0.509656965733,-0.0549761541188,-0.858619451523],
                        [-0.564633131027,-0.0339771322906,-0.82464236021],
                        [-0.529480218887,-0.153434738517,-0.834331154823],
                        [-0.548688352108,-0.091976031661,-0.830952167511],
                        [-0.588087081909,-0.131048902869,-0.798110127449],
                        [-0.553625464439,-0.378517180681,-0.74177056551],
                        [-0.582528710365,-0.308011889458,-0.752189457417],
                        [-0.618283927441,-0.353819847107,-0.701809465885],
                        [-0.480284929276,-0.284414708614,-0.829719662666],
                        [-0.506734728813,-0.217834427953,-0.834127128124],
                        [-0.545040607452,-0.26241543889,-0.796284377575],
                        [-0.606988489628,-0.238753452897,-0.757998526096],
                        [-0.627150595188,-0.171839639544,-0.759706020355],
                        [-0.665048420429,-0.213841319084,-0.715529501438],
                        [-0.545040607452,-0.26241543889,-0.796284377575],
                        [-0.606988489628,-0.238753452897,-0.757998526096],
                        [-0.582528710365,-0.308011889458,-0.752189457417],
                        [-0.486395716667,-0.787004828453,-0.379529476166],
                        [-0.535965919495,-0.737060189247,-0.411682873964],
                        [-0.550243675709,-0.762617051601,-0.340069264174],
                        [-0.44894811511,-0.726413309574,-0.520354926586],
                        [-0.495975226164,-0.669751524925,-0.552667617798],
                        [-0.517854511738,-0.706037700176,-0.483050197363],
                        [-0.58378881216,-0.680853009224,-0.44230055809],
                        [-0.628728508949,-0.619044244289,-0.470621615648],
                        [-0.645450055599,-0.65135627985,-0.398910075426],
                        [-0.517854511738,-0.706037700176,-0.483050197363],
                        [-0.58378881216,-0.680853009224,-0.44230055809],
                        [-0.535965919495,-0.737060189247,-0.411682873964],
                        [-0.398910075426,-0.645450055599,-0.65135627985],
                        [-0.44230055809,-0.58378881216,-0.680853009224],
                        [-0.470621615648,-0.628728508949,-0.619044244289],
                        [-0.340069264174,-0.550243675709,-0.762617051601],
                        [-0.379529476166,-0.486395716667,-0.787004828453],
                        [-0.411682873964,-0.535965919495,-0.737060189247],
                        [-0.483050197363,-0.517854511738,-0.706037700176],
                        [-0.520354926586,-0.44894811511,-0.726413309574],
                        [-0.552667617798,-0.495975226164,-0.669751524925],
                        [-0.411682873964,-0.535965919495,-0.737060189247],
                        [-0.483050197363,-0.517854511738,-0.706037700176],
                        [-0.44230055809,-0.58378881216,-0.680853009224],
                        [-0.669751524925,-0.552667617798,-0.495975226164],
                        [-0.706037700176,-0.483050197363,-0.517854511738],
                        [-0.726413309574,-0.520354926586,-0.44894811511],
                        [-0.619044244289,-0.470621615648,-0.628728508949],
                        [-0.65135627985,-0.398910075426,-0.645450055599],
                        [-0.680853009224,-0.44230055809,-0.58378881216],
                        [-0.737060189247,-0.411682873964,-0.535965919495],
                        [-0.762617051601,-0.340069264174,-0.550243675709],
                        [-0.787004828453,-0.379529476166,-0.486395716667],
                        [-0.680853009224,-0.44230055809,-0.58378881216],
                        [-0.737060189247,-0.411682873964,-0.535965919495],
                        [-0.706037700176,-0.483050197363,-0.517854511738],
                        [-0.470621615648,-0.628728508949,-0.619044244289],
                        [-0.540649950504,-0.607478022575,-0.581951975822],
                        [-0.495975226164,-0.669751524925,-0.552667617798],
                        [-0.552667617798,-0.495975226164,-0.669751524925],
                        [-0.619044244289,-0.470621615648,-0.628728508949],
                        [-0.581951975822,-0.540649950504,-0.607478022575],
                        [-0.607478022575,-0.581951975822,-0.540649950504],
                        [-0.669751524925,-0.552667617798,-0.495975226164],
                        [-0.628728508949,-0.619044244289,-0.470621615648],
                        [-0.581951975822,-0.540649950504,-0.607478022575],
                        [-0.607478022575,-0.581951975822,-0.540649950504],
                        [-0.540649950504,-0.607478022575,-0.581951975822],
                        [0.0549761541188,-0.858619451523,-0.509656965733],
                        [0.091976031661,-0.830952167511,-0.548688352108],
                        [0.0339771322906,-0.82464236021,-0.564633131027],
                        [0.174905076623,-0.866019308567,-0.468421578407],
                        [0.217834427953,-0.834127128124,-0.506734728813],
                        [0.153434738517,-0.834331154823,-0.529480218887],
                        [0.131048902869,-0.798110127449,-0.588087081909],
                        [0.171839639544,-0.759706020355,-0.627150595188],
                        [0.108097285032,-0.757922053337,-0.643326640129],
                        [0.153434738517,-0.834331154823,-0.529480218887],
                        [0.131048902869,-0.798110127449,-0.588087081909],
                        [0.091976031661,-0.830952167511,-0.548688352108],
                        [0.3044308424,-0.857896447182,-0.413926929235],
                        [0.352179646492,-0.820587992668,-0.450116455555],
                        [0.284414708614,-0.829719662666,-0.480284929276],
                        [0.436200261116,-0.830415487289,-0.346611320972],
                        [0.486395716667,-0.787004828453,-0.379529476166],
                        [0.419940322638,-0.806385576725,-0.416404157877],
                        [0.400663375854,-0.776785671711,-0.485873311758],
                        [0.44894811511,-0.726413309574,-0.520354926586],
                        [0.378517180681,-0.74177056551,-0.553625464439],
                        [0.419940322638,-0.806385576725,-0.416404157877],
                        [0.400663375854,-0.776785671711,-0.485873311758],
                        [0.352179646492,-0.820587992668,-0.450116455555],
                        [0.213841319084,-0.715529501438,-0.665048420429],
                        [0.256401896477,-0.665616393089,-0.700865805149],
                        [0.188148602843,-0.669747889042,-0.718357801437],
                        [0.353819847107,-0.701809465885,-0.618283927441],
                        [0.398910075426,-0.645450055599,-0.65135627985],
                        [0.327040165663,-0.657660841942,-0.678621411324],
                        [0.298754066229,-0.610302150249,-0.733673810959],
                        [0.340069264174,-0.550243675709,-0.762617051601],
                        [0.269586592913,-0.560828924179,-0.782811582088],
                        [0.327040165663,-0.657660841942,-0.678621411324],
                        [0.298754066229,-0.610302150249,-0.733673810959],
                        [0.256401896477,-0.665616393089,-0.700865805149],
                        [0.284414708614,-0.829719662666,-0.480284929276],
                        [0.26241543889,-0.796284377575,-0.545040607452],
                        [0.217834427953,-0.834127128124,-0.506734728813],
                        [0.378517180681,-0.74177056551,-0.553625464439],
                        [0.353819847107,-0.701809465885,-0.618283927441],
                        [0.308011889458,-0.752189457417,-0.582528710365],
                        [0.238753452897,-0.757998526096,-0.606988489628],
                        [0.213841319084,-0.715529501438,-0.665048420429],
                        [0.171839639544,-0.759706020355,-0.627150595188],
                        [0.308011889458,-0.752189457417,-0.582528710365],
                        [0.238753452897,-0.757998526096,-0.606988489628],
                        [0.26241543889,-0.796284377575,-0.545040607452],
                        [0.560828924179,-0.782811582088,-0.269586592913],
                        [0.610302150249,-0.733673810959,-0.298754066229],
                        [0.550243675709,-0.762617051601,-0.340069264174],
                        [0.669747889042,-0.718357801437,-0.188148602843],
                        [0.715529501438,-0.665048420429,-0.213841319084],
                        [0.665616393089,-0.700865805149,-0.256401896477],
                        [0.657660841942,-0.678621411324,-0.327040165663],
                        [0.701809465885,-0.618283927441,-0.353819847107],
                        [0.645450055599,-0.65135627985,-0.398910075426],
                        [0.665616393089,-0.700865805149,-0.256401896477],
                        [0.657660841942,-0.678621411324,-0.327040165663],
                        [0.610302150249,-0.733673810959,-0.298754066229],
                        [0.757922053337,-0.643326640129,-0.108097285032],
                        [0.798110127449,-0.588087081909,-0.131048902869],
                        [0.759706020355,-0.627150595188,-0.171839639544],
                        [0.82464236021,-0.564633131027,-0.0339771322906],
                        [0.858619451523,-0.509656965733,-0.0549761541188],
                        [0.830952167511,-0.548688352108,-0.091976031661],
                        [0.834331154823,-0.529480218887,-0.153434738517],
                        [0.866019308567,-0.468421578407,-0.174905076623],
                        [0.834127128124,-0.506734728813,-0.217834427953],
                        [0.830952167511,-0.548688352108,-0.091976031661],
                        [0.834331154823,-0.529480218887,-0.153434738517],
                        [0.798110127449,-0.588087081909,-0.131048902869],
                        [0.74177056551,-0.553625464439,-0.378517180681],
                        [0.776785671711,-0.485873311758,-0.400663375854],
                        [0.726413309574,-0.520354926586,-0.44894811511],
                        [0.829719662666,-0.480284929276,-0.284414708614],
                        [0.857896447182,-0.413926929235,-0.3044308424],
                        [0.820587992668,-0.450116455555,-0.352179646492],
                        [0.806385576725,-0.416404157877,-0.419940322638],
                        [0.830415487289,-0.346611320972,-0.436200261116],
                        [0.787004828453,-0.379529476166,-0.486395716667],
                        [0.820587992668,-0.450116455555,-0.352179646492],
                        [0.806385576725,-0.416404157877,-0.419940322638],
                        [0.776785671711,-0.485873311758,-0.400663375854],
                        [0.759706020355,-0.627150595188,-0.171839639544],
                        [0.757998526096,-0.606988489628,-0.238753452897],
                        [0.715529501438,-0.665048420429,-0.213841319084],
                        [0.834127128124,-0.506734728813,-0.217834427953],
                        [0.829719662666,-0.480284929276,-0.284414708614],
                        [0.796284377575,-0.545040607452,-0.26241543889],
                        [0.752189457417,-0.582528710365,-0.308011889458],
                        [0.74177056551,-0.553625464439,-0.378517180681],
                        [0.701809465885,-0.618283927441,-0.353819847107],
                        [0.796284377575,-0.545040607452,-0.26241543889],
                        [0.752189457417,-0.582528710365,-0.308011889458],
                        [0.757998526096,-0.606988489628,-0.238753452897],
                        [0.379529476166,-0.486395716667,-0.787004828453],
                        [0.416404157877,-0.419940322638,-0.806385576725],
                        [0.346611320972,-0.436200261116,-0.830415487289],
                        [0.520354926586,-0.44894811511,-0.726413309574],
                        [0.553625464439,-0.378517180681,-0.74177056551],
                        [0.485873311758,-0.400663375854,-0.776785671711],
                        [0.450116455555,-0.352179646492,-0.820587992668],
                        [0.480284929276,-0.284414708614,-0.829719662666],
                        [0.413926929235,-0.3044308424,-0.857896447182],
                        [0.485873311758,-0.400663375854,-0.776785671711],
                        [0.450116455555,-0.352179646492,-0.820587992668],
                        [0.416404157877,-0.419940322638,-0.806385576725],
                        [0.65135627985,-0.398910075426,-0.645450055599],
                        [0.678621411324,-0.327040165663,-0.657660841942],
                        [0.618283927441,-0.353819847107,-0.701809465885],
                        [0.762617051601,-0.340069264174,-0.550243675709],
                        [0.782811582088,-0.269586592913,-0.560828924179],
                        [0.733673810959,-0.298754066229,-0.610302150249],
                        [0.700865805149,-0.256401896477,-0.665616393089],
                        [0.718357801437,-0.188148602843,-0.669747889042],
                        [0.665048420429,-0.213841319084,-0.715529501438],
                        [0.733673810959,-0.298754066229,-0.610302150249],
                        [0.700865805149,-0.256401896477,-0.665616393089],
                        [0.678621411324,-0.327040165663,-0.657660841942],
                        [0.506734728813,-0.217834427953,-0.834127128124],
                        [0.529480218887,-0.153434738517,-0.834331154823],
                        [0.468421578407,-0.174905076623,-0.866019308567],
                        [0.627150595188,-0.171839639544,-0.759706020355],
                        [0.643326640129,-0.108097285032,-0.757922053337],
                        [0.588087081909,-0.131048902869,-0.798110127449],
                        [0.548688352108,-0.091976031661,-0.830952167511],
                        [0.564633131027,-0.0339771322906,-0.82464236021],
                        [0.509656965733,-0.0549761541188,-0.858619451523],
                        [0.588087081909,-0.131048902869,-0.798110127449],
                        [0.548688352108,-0.091976031661,-0.830952167511],
                        [0.529480218887,-0.153434738517,-0.834331154823],
                        [0.618283927441,-0.353819847107,-0.701809465885],
                        [0.582528710365,-0.308011889458,-0.752189457417],
                        [0.553625464439,-0.378517180681,-0.74177056551],
                        [0.665048420429,-0.213841319084,-0.715529501438],
                        [0.627150595188,-0.171839639544,-0.759706020355],
                        [0.606988489628,-0.238753452897,-0.757998526096],
                        [0.545040607452,-0.26241543889,-0.796284377575],
                        [0.506734728813,-0.217834427953,-0.834127128124],
                        [0.480284929276,-0.284414708614,-0.829719662666],
                        [0.606988489628,-0.238753452897,-0.757998526096],
                        [0.545040607452,-0.26241543889,-0.796284377575],
                        [0.582528710365,-0.308011889458,-0.752189457417],
                        [0.550243675709,-0.762617051601,-0.340069264174],
                        [0.535965919495,-0.737060189247,-0.411682873964],
                        [0.486395716667,-0.787004828453,-0.379529476166],
                        [0.645450055599,-0.65135627985,-0.398910075426],
                        [0.628728508949,-0.619044244289,-0.470621615648],
                        [0.58378881216,-0.680853009224,-0.44230055809],
                        [0.517854511738,-0.706037700176,-0.483050197363],
                        [0.495975226164,-0.669751524925,-0.552667617798],
                        [0.44894811511,-0.726413309574,-0.520354926586],
                        [0.58378881216,-0.680853009224,-0.44230055809],
                        [0.517854511738,-0.706037700176,-0.483050197363],
                        [0.535965919495,-0.737060189247,-0.411682873964],
                        [0.726413309574,-0.520354926586,-0.44894811511],
                        [0.706037700176,-0.483050197363,-0.517854511738],
                        [0.669751524925,-0.552667617798,-0.495975226164],
                        [0.787004828453,-0.379529476166,-0.486395716667],
                        [0.762617051601,-0.340069264174,-0.550243675709],
                        [0.737060189247,-0.411682873964,-0.535965919495],
                        [0.680853009224,-0.44230055809,-0.58378881216],
                        [0.65135627985,-0.398910075426,-0.645450055599],
                        [0.619044244289,-0.470621615648,-0.628728508949],
                        [0.737060189247,-0.411682873964,-0.535965919495],
                        [0.680853009224,-0.44230055809,-0.58378881216],
                        [0.706037700176,-0.483050197363,-0.517854511738],
                        [0.470621615648,-0.628728508949,-0.619044244289],
                        [0.44230055809,-0.58378881216,-0.680853009224],
                        [0.398910075426,-0.645450055599,-0.65135627985],
                        [0.552667617798,-0.495975226164,-0.669751524925],
                        [0.520354926586,-0.44894811511,-0.726413309574],
                        [0.483050197363,-0.517854511738,-0.706037700176],
                        [0.411682873964,-0.535965919495,-0.737060189247],
                        [0.379529476166,-0.486395716667,-0.787004828453],
                        [0.340069264174,-0.550243675709,-0.762617051601],
                        [0.483050197363,-0.517854511738,-0.706037700176],
                        [0.411682873964,-0.535965919495,-0.737060189247],
                        [0.44230055809,-0.58378881216,-0.680853009224],
                        [0.669751524925,-0.552667617798,-0.495975226164],
                        [0.607478022575,-0.581951975822,-0.540649950504],
                        [0.628728508949,-0.619044244289,-0.470621615648],
                        [0.619044244289,-0.470621615648,-0.628728508949],
                        [0.552667617798,-0.495975226164,-0.669751524925],
                        [0.581951975822,-0.540649950504,-0.607478022575],
                        [0.540649950504,-0.607478022575,-0.581951975822],
                        [0.470621615648,-0.628728508949,-0.619044244289],
                        [0.495975226164,-0.669751524925,-0.552667617798],
                        [0.581951975822,-0.540649950504,-0.607478022575],
                        [0.540649950504,-0.607478022575,-0.581951975822],
                        [0.607478022575,-0.581951975822,-0.540649950504],
                        [0.475679844618,0.0,-0.8796184659],
                        [0.456712335348,-0.0568443164229,-0.887796461582],
                        [0.509656965733,-0.0549761541188,-0.858619451523],
                        [0.360324263573,0.0,-0.932827115059],
                        [0.334895044565,-0.0602079555392,-0.940329909325],
                        [0.398431301117,-0.0586068555713,-0.915323853493],
                        [0.434652328491,-0.117213711143,-0.892938017845],
                        [0.409316182137,-0.180623859167,-0.894335091114],
                        [0.468421578407,-0.174905076623,-0.866019308567],
                        [0.398431301117,-0.0586068555713,-0.915323853493],
                        [0.434652328491,-0.117213711143,-0.892938017845],
                        [0.456712335348,-0.0568443164229,-0.887796461582],
                        [0.225778326392,0.0,-0.974178731441],
                        [0.193714544177,-0.0626873448491,-0.979053080082],
                        [0.266443610191,-0.0615878328681,-0.961880862713],
                        [0.0770247355103,0.0,-0.997029185295],
                        [0.0394601933658,-0.0638479366899,-0.997179210186],
                        [0.117650069296,-0.0634539350867,-0.991025745869],
                        [0.158833146095,-0.128498718143,-0.978907585144],
                        [0.121444880962,-0.196501940489,-0.97295331955],
                        [0.199805602431,-0.193975359201,-0.960443258286],
                        [0.117650069296,-0.0634539350867,-0.991025745869],
                        [0.158833146095,-0.128498718143,-0.978907585144],
                        [0.193714544177,-0.0626873448491,-0.979053080082],
                        [0.380633711815,-0.246351331472,-0.891307473183],
                        [0.348686188459,-0.313436716795,-0.883275330067],
                        [0.413926929235,-0.3044308424,-0.857896447182],
                        [0.239766731858,-0.258633822203,-0.935745954514],
                        [0.202408134937,-0.327503234148,-0.922915279865],
                        [0.277958005667,-0.321246802807,-0.905284404755],
                        [0.313733518124,-0.380723625422,-0.869839549065],
                        [0.276221334934,-0.446935534477,-0.85085272789],
                        [0.346611320972,-0.436200261116,-0.830415487289],
                        [0.277958005667,-0.321246802807,-0.905284404755],
                        [0.313733518124,-0.380723625422,-0.869839549065],
                        [0.348686188459,-0.313436716795,-0.883275330067],
                        [0.266443610191,-0.0615878328681,-0.961880862713],
                        [0.306287169456,-0.123895764351,-0.943842172623],
                        [0.334895044565,-0.0602079555392,-0.940329909325],
                        [0.199805602431,-0.193975359201,-0.960443258286],
                        [0.239766731858,-0.258633822203,-0.935745954514],
                        [0.274516820908,-0.190361812711,-0.942551255226],
                        [0.34457308054,-0.185843646526,-0.920180141926],
                        [0.380633711815,-0.246351331472,-0.891307473183],
                        [0.409316182137,-0.180623859167,-0.894335091114],
                        [0.274516820908,-0.190361812711,-0.942551255226],
                        [0.34457308054,-0.185843646526,-0.920180141926],
                        [0.306287169456,-0.123895764351,-0.943842172623],
                        [-0.0770247355103,0.0,-0.997029185295],
                        [-0.117650069296,-0.0634539350867,-0.991025745869],
                        [-0.0394601933658,-0.0638479366899,-0.997179210186],
                        [-0.225778326392,0.0,-0.974178731441],
                        [-0.266443610191,-0.0615878328681,-0.961880862713],
                        [-0.193714544177,-0.0626873448491,-0.979053080082],
                        [-0.158833146095,-0.128498718143,-0.978907585144],
                        [-0.199805602431,-0.193975359201,-0.960443258286],
                        [-0.121444880962,-0.196501940489,-0.97295331955],
                        [-0.193714544177,-0.0626873448491,-0.979053080082],
                        [-0.158833146095,-0.128498718143,-0.978907585144],
                        [-0.117650069296,-0.0634539350867,-0.991025745869],
                        [-0.360324263573,0.0,-0.932827115059],
                        [-0.398431301117,-0.0586068555713,-0.915323853493],
                        [-0.334895044565,-0.0602079555392,-0.940329909325],
                        [-0.475679844618,0.0,-0.8796184659],
                        [-0.509656965733,-0.0549761541188,-0.858619451523],
                        [-0.456712335348,-0.0568443164229,-0.887796461582],
                        [-0.434652328491,-0.117213711143,-0.892938017845],
                        [-0.468421578407,-0.174905076623,-0.866019308567],
                        [-0.409316182137,-0.180623859167,-0.894335091114],
                        [-0.456712335348,-0.0568443164229,-0.887796461582],
                        [-0.434652328491,-0.117213711143,-0.892938017845],
                        [-0.398431301117,-0.0586068555713,-0.915323853493],
                        [-0.239766731858,-0.258633822203,-0.935745954514],
                        [-0.277958005667,-0.321246802807,-0.905284404755],
                        [-0.202408134937,-0.327503234148,-0.922915279865],
                        [-0.380633711815,-0.246351331472,-0.891307473183],
                        [-0.413926929235,-0.3044308424,-0.857896447182],
                        [-0.348686188459,-0.313436716795,-0.883275330067],
                        [-0.313733518124,-0.380723625422,-0.869839549065],
                        [-0.346611320972,-0.436200261116,-0.830415487289],
                        [-0.276221334934,-0.446935534477,-0.85085272789],
                        [-0.348686188459,-0.313436716795,-0.883275330067],
                        [-0.313733518124,-0.380723625422,-0.869839549065],
                        [-0.277958005667,-0.321246802807,-0.905284404755],
                        [-0.334895044565,-0.0602079555392,-0.940329909325],
                        [-0.306287169456,-0.123895764351,-0.943842172623],
                        [-0.266443610191,-0.0615878328681,-0.961880862713],
                        [-0.409316182137,-0.180623859167,-0.894335091114],
                        [-0.380633711815,-0.246351331472,-0.891307473183],
                        [-0.34457308054,-0.185843646526,-0.920180141926],
                        [-0.274516820908,-0.190361812711,-0.942551255226],
                        [-0.239766731858,-0.258633822203,-0.935745954514],
                        [-0.199805602431,-0.193975359201,-0.960443258286],
                        [-0.34457308054,-0.185843646526,-0.920180141926],
                        [-0.274516820908,-0.190361812711,-0.942551255226],
                        [-0.306287169456,-0.123895764351,-0.943842172623],
                        [0.236761152744,-0.510783493519,-0.826465010643],
                        [0.196083456278,-0.571085453033,-0.797127783298],
                        [0.269586592913,-0.560828924179,-0.782811582088],
                        [0.0809632539749,-0.524005174637,-0.847858190536],
                        [0.0399611219764,-0.581926107407,-0.81225925684],
                        [0.119124859571,-0.578244268894,-0.807120084763],
                        [0.154971644282,-0.62687343359,-0.763553202152],
                        [0.114190116525,-0.677466154099,-0.726636230946],
                        [0.188148602843,-0.669747889042,-0.718357801437],
                        [0.119124859571,-0.578244268894,-0.807120084763],
                        [0.154971644282,-0.62687343359,-0.763553202152],
                        [0.196083456278,-0.571085453033,-0.797127783298],
                        [-0.0809632539749,-0.524005174637,-0.847858190536],
                        [-0.119124859571,-0.578244268894,-0.807120084763],
                        [-0.0399611219764,-0.581926107407,-0.81225925684],
                        [-0.236761152744,-0.510783493519,-0.826465010643],
                        [-0.269586592913,-0.560828924179,-0.782811582088],
                        [-0.196083456278,-0.571085453033,-0.797127783298],
                        [-0.154971644282,-0.62687343359,-0.763553202152],
                        [-0.188148602843,-0.669747889042,-0.718357801437],
                        [-0.114190116525,-0.677466154099,-0.726636230946],
                        [-0.196083456278,-0.571085453033,-0.797127783298],
                        [-0.154971644282,-0.62687343359,-0.763553202152],
                        [-0.119124859571,-0.578244268894,-0.807120084763],
                        [0.0744211226702,-0.722495436668,-0.687358558178],
                        [0.0362210273743,-0.761889100075,-0.646693944931],
                        [0.108097285032,-0.757922053337,-0.643326640129],
                        [-0.0744211226702,-0.722495436668,-0.687358558178],
                        [-0.108097285032,-0.757922053337,-0.643326640129],
                        [-0.0362210273743,-0.761889100075,-0.646693944931],
                        [0.0,-0.79582041502,-0.605532705784],
                        [-0.0339771322906,-0.82464236021,-0.564633131027],
                        [0.0339771322906,-0.82464236021,-0.564633131027],
                        [-0.0362210273743,-0.761889100075,-0.646693944931],
                        [0.0,-0.79582041502,-0.605532705784],
                        [0.0362210273743,-0.761889100075,-0.646693944931],
                        [-0.0399611219764,-0.581926107407,-0.81225925684],
                        [0.0,-0.634539365768,-0.772890508175],
                        [0.0399611219764,-0.581926107407,-0.81225925684],
                        [-0.114190116525,-0.677466154099,-0.726636230946],
                        [-0.0744211226702,-0.722495436668,-0.687358558178],
                        [-0.0382858961821,-0.68142670393,-0.730884253979],
                        [0.0382858961821,-0.68142670393,-0.730884253979],
                        [0.0744211226702,-0.722495436668,-0.687358558178],
                        [0.114190116525,-0.677466154099,-0.726636230946],
                        [-0.0382858961821,-0.68142670393,-0.730884253979],
                        [0.0382858961821,-0.68142670393,-0.730884253979],
                        [0.0,-0.634539365768,-0.772890508175],
                        [-0.0394601933658,-0.0638479366899,-0.997179210186],
                        [0.0,-0.130150929093,-0.991494178772],
                        [0.0394601933658,-0.0638479366899,-0.997179210186],
                        [-0.121444880962,-0.196501940489,-0.97295331955],
                        [-0.0820460245013,-0.265506535769,-0.960611641407],
                        [-0.0407496243715,-0.197802826762,-0.979394435883],
                        [0.0407496243715,-0.197802826762,-0.979394435883],
                        [0.0820460245013,-0.265506535769,-0.960611641407],
                        [0.121444880962,-0.196501940489,-0.97295331955],
                        [-0.0407496243715,-0.197802826762,-0.979394435883],
                        [0.0407496243715,-0.197802826762,-0.979394435883],
                        [0.0,-0.130150929093,-0.991494178772],
                        [-0.202408134937,-0.327503234148,-0.922915279865],
                        [-0.162998497486,-0.395605653524,-0.903840482235],
                        [-0.123069040477,-0.33188316226,-0.935258030891],
                        [-0.276221334934,-0.446935534477,-0.85085272789],
                        [-0.236761152744,-0.510783493519,-0.826465010643],
                        [-0.20109423995,-0.455528259277,-0.867211103439],
                        [-0.122248865664,-0.461539924145,-0.878655850887],
                        [-0.0809632539749,-0.524005174637,-0.847858190536],
                        [-0.0410230122507,-0.464636415243,-0.88455080986],
                        [-0.20109423995,-0.455528259277,-0.867211103439],
                        [-0.122248865664,-0.461539924145,-0.878655850887],
                        [-0.162998497486,-0.395605653524,-0.903840482235],
                        [0.123069040477,-0.33188316226,-0.935258030891],
                        [0.162998497486,-0.395605653524,-0.903840482235],
                        [0.202408134937,-0.327503234148,-0.922915279865],
                        [0.0410230122507,-0.464636415243,-0.88455080986],
                        [0.0809632539749,-0.524005174637,-0.847858190536],
                        [0.122248865664,-0.461539924145,-0.878655850887],
                        [0.20109423995,-0.455528259277,-0.867211103439],
                        [0.236761152744,-0.510783493519,-0.826465010643],
                        [0.276221334934,-0.446935534477,-0.85085272789],
                        [0.122248865664,-0.461539924145,-0.878655850887],
                        [0.20109423995,-0.455528259277,-0.867211103439],
                        [0.162998497486,-0.395605653524,-0.903840482235],
                        [-0.123069040477,-0.33188316226,-0.935258030891],
                        [-0.04130198434,-0.334140062332,-0.941618084908],
                        [-0.0820460245013,-0.265506535769,-0.960611641407],
                        [-0.0410230122507,-0.464636415243,-0.88455080986],
                        [0.0410230122507,-0.464636415243,-0.88455080986],
                        [0.0,-0.400968074799,-0.916092038155],
                        [0.04130198434,-0.334140062332,-0.941618084908],
                        [0.123069040477,-0.33188316226,-0.935258030891],
                        [0.0820460245013,-0.265506535769,-0.960611641407],
                        [0.0,-0.400968074799,-0.916092038155],
                        [0.04130198434,-0.334140062332,-0.941618084908],
                        [-0.04130198434,-0.334140062332,-0.941618084908],
                        [-0.8796184659,-0.475679844618,0.0],
                        [-0.887796461582,-0.456712335348,-0.0568443164229],
                        [-0.858619451523,-0.509656965733,-0.0549761541188],
                        [-0.932827115059,-0.360324263573,0.0],
                        [-0.940329909325,-0.334895044565,-0.0602079555392],
                        [-0.915323853493,-0.398431301117,-0.0586068555713],
                        [-0.892938017845,-0.434652328491,-0.117213711143],
                        [-0.894335091114,-0.409316182137,-0.180623859167],
                        [-0.866019308567,-0.468421578407,-0.174905076623],
                        [-0.915323853493,-0.398431301117,-0.0586068555713],
                        [-0.892938017845,-0.434652328491,-0.117213711143],
                        [-0.887796461582,-0.456712335348,-0.0568443164229],
                        [-0.974178731441,-0.225778326392,0.0],
                        [-0.979053080082,-0.193714544177,-0.0626873448491],
                        [-0.961880862713,-0.266443610191,-0.0615878328681],
                        [-0.997029185295,-0.0770247355103,0.0],
                        [-0.997179210186,-0.0394601933658,-0.0638479366899],
                        [-0.991025745869,-0.117650069296,-0.0634539350867],
                        [-0.978907585144,-0.158833146095,-0.128498718143],
                        [-0.97295331955,-0.121444880962,-0.196501940489],
                        [-0.960443258286,-0.199805602431,-0.193975359201],
                        [-0.991025745869,-0.117650069296,-0.0634539350867],
                        [-0.978907585144,-0.158833146095,-0.128498718143],
                        [-0.979053080082,-0.193714544177,-0.0626873448491],
                        [-0.891307473183,-0.380633711815,-0.246351331472],
                        [-0.883275330067,-0.348686188459,-0.313436716795],
                        [-0.857896447182,-0.413926929235,-0.3044308424],
                        [-0.935745954514,-0.239766731858,-0.258633822203],
                        [-0.922915279865,-0.202408134937,-0.327503234148],
                        [-0.905284404755,-0.277958005667,-0.321246802807],
                        [-0.869839549065,-0.313733518124,-0.380723625422],
                        [-0.85085272789,-0.276221334934,-0.446935534477],
                        [-0.830415487289,-0.346611320972,-0.436200261116],
                        [-0.905284404755,-0.277958005667,-0.321246802807],
                        [-0.869839549065,-0.313733518124,-0.380723625422],
                        [-0.883275330067,-0.348686188459,-0.313436716795],
                        [-0.961880862713,-0.266443610191,-0.0615878328681],
                        [-0.943842172623,-0.306287169456,-0.123895764351],
                        [-0.940329909325,-0.334895044565,-0.0602079555392],
                        [-0.960443258286,-0.199805602431,-0.193975359201],
                        [-0.935745954514,-0.239766731858,-0.258633822203],
                        [-0.942551255226,-0.274516820908,-0.190361812711],
                        [-0.920180141926,-0.34457308054,-0.185843646526],
                        [-0.891307473183,-0.380633711815,-0.246351331472],
                        [-0.894335091114,-0.409316182137,-0.180623859167],
                        [-0.942551255226,-0.274516820908,-0.190361812711],
                        [-0.920180141926,-0.34457308054,-0.185843646526],
                        [-0.943842172623,-0.306287169456,-0.123895764351],
                        [-0.997029185295,0.0770247355103,0.0],
                        [-0.991025745869,0.117650069296,-0.0634539350867],
                        [-0.997179210186,0.0394601933658,-0.0638479366899],
                        [-0.974178731441,0.225778326392,0.0],
                        [-0.961880862713,0.266443610191,-0.0615878328681],
                        [-0.979053080082,0.193714544177,-0.0626873448491],
                        [-0.978907585144,0.158833146095,-0.128498718143],
                        [-0.960443258286,0.199805602431,-0.193975359201],
                        [-0.97295331955,0.121444880962,-0.196501940489],
                        [-0.979053080082,0.193714544177,-0.0626873448491],
                        [-0.978907585144,0.158833146095,-0.128498718143],
                        [-0.991025745869,0.117650069296,-0.0634539350867],
                        [-0.932827115059,0.360324263573,0.0],
                        [-0.915323853493,0.398431301117,-0.0586068555713],
                        [-0.940329909325,0.334895044565,-0.0602079555392],
                        [-0.8796184659,0.475679844618,0.0],
                        [-0.858619451523,0.509656965733,-0.0549761541188],
                        [-0.887796461582,0.456712335348,-0.0568443164229],
                        [-0.892938017845,0.434652328491,-0.117213711143],
                        [-0.866019308567,0.468421578407,-0.174905076623],
                        [-0.894335091114,0.409316182137,-0.180623859167],
                        [-0.887796461582,0.456712335348,-0.0568443164229],
                        [-0.892938017845,0.434652328491,-0.117213711143],
                        [-0.915323853493,0.398431301117,-0.0586068555713],
                        [-0.935745954514,0.239766731858,-0.258633822203],
                        [-0.905284404755,0.277958005667,-0.321246802807],
                        [-0.922915279865,0.202408134937,-0.327503234148],
                        [-0.891307473183,0.380633711815,-0.246351331472],
                        [-0.857896447182,0.413926929235,-0.3044308424],
                        [-0.883275330067,0.348686188459,-0.313436716795],
                        [-0.869839549065,0.313733518124,-0.380723625422],
                        [-0.830415487289,0.346611320972,-0.436200261116],
                        [-0.85085272789,0.276221334934,-0.446935534477],
                        [-0.883275330067,0.348686188459,-0.313436716795],
                        [-0.869839549065,0.313733518124,-0.380723625422],
                        [-0.905284404755,0.277958005667,-0.321246802807],
                        [-0.940329909325,0.334895044565,-0.0602079555392],
                        [-0.943842172623,0.306287169456,-0.123895764351],
                        [-0.961880862713,0.266443610191,-0.0615878328681],
                        [-0.894335091114,0.409316182137,-0.180623859167],
                        [-0.891307473183,0.380633711815,-0.246351331472],
                        [-0.920180141926,0.34457308054,-0.185843646526],
                        [-0.942551255226,0.274516820908,-0.190361812711],
                        [-0.935745954514,0.239766731858,-0.258633822203],
                        [-0.960443258286,0.199805602431,-0.193975359201],
                        [-0.920180141926,0.34457308054,-0.185843646526],
                        [-0.942551255226,0.274516820908,-0.190361812711],
                        [-0.943842172623,0.306287169456,-0.123895764351],
                        [-0.826465010643,-0.236761152744,-0.510783493519],
                        [-0.797127783298,-0.196083456278,-0.571085453033],
                        [-0.782811582088,-0.269586592913,-0.560828924179],
                        [-0.847858190536,-0.0809632539749,-0.524005174637],
                        [-0.81225925684,-0.0399611219764,-0.581926107407],
                        [-0.807120084763,-0.119124859571,-0.578244268894],
                        [-0.763553202152,-0.154971644282,-0.62687343359],
                        [-0.726636230946,-0.114190116525,-0.677466154099],
                        [-0.718357801437,-0.188148602843,-0.669747889042],
                        [-0.807120084763,-0.119124859571,-0.578244268894],
                        [-0.763553202152,-0.154971644282,-0.62687343359],
                        [-0.797127783298,-0.196083456278,-0.571085453033],
                        [-0.847858190536,0.0809632539749,-0.524005174637],
                        [-0.807120084763,0.119124859571,-0.578244268894],
                        [-0.81225925684,0.0399611219764,-0.581926107407],
                        [-0.826465010643,0.236761152744,-0.510783493519],
                        [-0.782811582088,0.269586592913,-0.560828924179],
                        [-0.797127783298,0.196083456278,-0.571085453033],
                        [-0.763553202152,0.154971644282,-0.62687343359],
                        [-0.718357801437,0.188148602843,-0.669747889042],
                        [-0.726636230946,0.114190116525,-0.677466154099],
                        [-0.797127783298,0.196083456278,-0.571085453033],
                        [-0.763553202152,0.154971644282,-0.62687343359],
                        [-0.807120084763,0.119124859571,-0.578244268894],
                        [-0.687358558178,-0.0744211226702,-0.722495436668],
                        [-0.646693944931,-0.0362210273743,-0.761889100075],
                        [-0.643326640129,-0.108097285032,-0.757922053337],
                        [-0.687358558178,0.0744211226702,-0.722495436668],
                        [-0.643326640129,0.108097285032,-0.757922053337],
                        [-0.646693944931,0.0362210273743,-0.761889100075],
                        [-0.605532705784,0.0,-0.79582041502],
                        [-0.564633131027,0.0339771322906,-0.82464236021],
                        [-0.564633131027,-0.0339771322906,-0.82464236021],
                        [-0.646693944931,0.0362210273743,-0.761889100075],
                        [-0.605532705784,0.0,-0.79582041502],
                        [-0.646693944931,-0.0362210273743,-0.761889100075],
                        [-0.81225925684,0.0399611219764,-0.581926107407],
                        [-0.772890508175,0.0,-0.634539365768],
                        [-0.81225925684,-0.0399611219764,-0.581926107407],
                        [-0.726636230946,0.114190116525,-0.677466154099],
                        [-0.687358558178,0.0744211226702,-0.722495436668],
                        [-0.730884253979,0.0382858961821,-0.68142670393],
                        [-0.730884253979,-0.0382858961821,-0.68142670393],
                        [-0.687358558178,-0.0744211226702,-0.722495436668],
                        [-0.726636230946,-0.114190116525,-0.677466154099],
                        [-0.730884253979,0.0382858961821,-0.68142670393],
                        [-0.730884253979,-0.0382858961821,-0.68142670393],
                        [-0.772890508175,0.0,-0.634539365768],
                        [-0.997179210186,0.0394601933658,-0.0638479366899],
                        [-0.991494178772,0.0,-0.130150929093],
                        [-0.997179210186,-0.0394601933658,-0.0638479366899],
                        [-0.97295331955,0.121444880962,-0.196501940489],
                        [-0.960611641407,0.0820460245013,-0.265506535769],
                        [-0.979394435883,0.0407496243715,-0.197802826762],
                        [-0.979394435883,-0.0407496243715,-0.197802826762],
                        [-0.960611641407,-0.0820460245013,-0.265506535769],
                        [-0.97295331955,-0.121444880962,-0.196501940489],
                        [-0.979394435883,0.0407496243715,-0.197802826762],
                        [-0.979394435883,-0.0407496243715,-0.197802826762],
                        [-0.991494178772,0.0,-0.130150929093],
                        [-0.922915279865,0.202408134937,-0.327503234148],
                        [-0.903840482235,0.162998497486,-0.395605653524],
                        [-0.935258030891,0.123069040477,-0.33188316226],
                        [-0.85085272789,0.276221334934,-0.446935534477],
                        [-0.826465010643,0.236761152744,-0.510783493519],
                        [-0.867211103439,0.20109423995,-0.455528259277],
                        [-0.878655850887,0.122248865664,-0.461539924145],
                        [-0.847858190536,0.0809632539749,-0.524005174637],
                        [-0.88455080986,0.0410230122507,-0.464636415243],
                        [-0.867211103439,0.20109423995,-0.455528259277],
                        [-0.878655850887,0.122248865664,-0.461539924145],
                        [-0.903840482235,0.162998497486,-0.395605653524],
                        [-0.935258030891,-0.123069040477,-0.33188316226],
                        [-0.903840482235,-0.162998497486,-0.395605653524],
                        [-0.922915279865,-0.202408134937,-0.327503234148],
                        [-0.88455080986,-0.0410230122507,-0.464636415243],
                        [-0.847858190536,-0.0809632539749,-0.524005174637],
                        [-0.878655850887,-0.122248865664,-0.461539924145],
                        [-0.867211103439,-0.20109423995,-0.455528259277],
                        [-0.826465010643,-0.236761152744,-0.510783493519],
                        [-0.85085272789,-0.276221334934,-0.446935534477],
                        [-0.878655850887,-0.122248865664,-0.461539924145],
                        [-0.867211103439,-0.20109423995,-0.455528259277],
                        [-0.903840482235,-0.162998497486,-0.395605653524],
                        [-0.935258030891,0.123069040477,-0.33188316226],
                        [-0.941618084908,0.04130198434,-0.334140062332],
                        [-0.960611641407,0.0820460245013,-0.265506535769],
                        [-0.88455080986,0.0410230122507,-0.464636415243],
                        [-0.88455080986,-0.0410230122507,-0.464636415243],
                        [-0.916092038155,0.0,-0.400968074799],
                        [-0.941618084908,-0.04130198434,-0.334140062332],
                        [-0.935258030891,-0.123069040477,-0.33188316226],
                        [-0.960611641407,-0.0820460245013,-0.265506535769],
                        [-0.916092038155,0.0,-0.400968074799],
                        [-0.941618084908,-0.04130198434,-0.334140062332],
                        [-0.941618084908,0.04130198434,-0.334140062332],
                        [-0.82464236021,0.564633131027,-0.0339771322906],
                        [-0.830952167511,0.548688352108,-0.091976031661],
                        [-0.858619451523,0.509656965733,-0.0549761541188],
                        [-0.757922053337,0.643326640129,-0.108097285032],
                        [-0.759706020355,0.627150595188,-0.171839639544],
                        [-0.798110127449,0.588087081909,-0.131048902869],
                        [-0.834331154823,0.529480218887,-0.153434738517],
                        [-0.834127128124,0.506734728813,-0.217834427953],
                        [-0.866019308567,0.468421578407,-0.174905076623],
                        [-0.798110127449,0.588087081909,-0.131048902869],
                        [-0.834331154823,0.529480218887,-0.153434738517],
                        [-0.830952167511,0.548688352108,-0.091976031661],
                        [-0.669747889042,0.718357801437,-0.188148602843],
                        [-0.665616393089,0.700865805149,-0.256401896477],
                        [-0.715529501438,0.665048420429,-0.213841319084],
                        [-0.560828924179,0.782811582088,-0.269586592913],
                        [-0.550243675709,0.762617051601,-0.340069264174],
                        [-0.610302150249,0.733673810959,-0.298754066229],
                        [-0.657660841942,0.678621411324,-0.327040165663],
                        [-0.645450055599,0.65135627985,-0.398910075426],
                        [-0.701809465885,0.618283927441,-0.353819847107],
                        [-0.610302150249,0.733673810959,-0.298754066229],
                        [-0.657660841942,0.678621411324,-0.327040165663],
                        [-0.665616393089,0.700865805149,-0.256401896477],
                        [-0.829719662666,0.480284929276,-0.284414708614],
                        [-0.820587992668,0.450116455555,-0.352179646492],
                        [-0.857896447182,0.413926929235,-0.3044308424],
                        [-0.74177056551,0.553625464439,-0.378517180681],
                        [-0.726413309574,0.520354926586,-0.44894811511],
                        [-0.776785671711,0.485873311758,-0.400663375854],
                        [-0.806385576725,0.416404157877,-0.419940322638],
                        [-0.787004828453,0.379529476166,-0.486395716667],
                        [-0.830415487289,0.346611320972,-0.436200261116],
                        [-0.776785671711,0.485873311758,-0.400663375854],
                        [-0.806385576725,0.416404157877,-0.419940322638],
                        [-0.820587992668,0.450116455555,-0.352179646492],
                        [-0.715529501438,0.665048420429,-0.213841319084],
                        [-0.757998526096,0.606988489628,-0.238753452897],
                        [-0.759706020355,0.627150595188,-0.171839639544],
                        [-0.701809465885,0.618283927441,-0.353819847107],
                        [-0.74177056551,0.553625464439,-0.378517180681],
                        [-0.752189457417,0.582528710365,-0.308011889458],
                        [-0.796284377575,0.545040607452,-0.26241543889],
                        [-0.829719662666,0.480284929276,-0.284414708614],
                        [-0.834127128124,0.506734728813,-0.217834427953],
                        [-0.752189457417,0.582528710365,-0.308011889458],
                        [-0.796284377575,0.545040607452,-0.26241543889],
                        [-0.757998526096,0.606988489628,-0.238753452897],
                        [-0.436200261116,0.830415487289,-0.346611320972],
                        [-0.419940322638,0.806385576725,-0.416404157877],
                        [-0.486395716667,0.787004828453,-0.379529476166],
                        [-0.3044308424,0.857896447182,-0.413926929235],
                        [-0.284414708614,0.829719662666,-0.480284929276],
                        [-0.352179646492,0.820587992668,-0.450116455555],
                        [-0.400663375854,0.776785671711,-0.485873311758],
                        [-0.378517180681,0.74177056551,-0.553625464439],
                        [-0.44894811511,0.726413309574,-0.520354926586],
                        [-0.352179646492,0.820587992668,-0.450116455555],
                        [-0.400663375854,0.776785671711,-0.485873311758],
                        [-0.419940322638,0.806385576725,-0.416404157877],
                        [-0.174905076623,0.866019308567,-0.468421578407],
                        [-0.153434738517,0.834331154823,-0.529480218887],
                        [-0.217834427953,0.834127128124,-0.506734728813],
                        [-0.0549761541188,0.858619451523,-0.509656965733],
                        [-0.0339771322906,0.82464236021,-0.564633131027],
                        [-0.091976031661,0.830952167511,-0.548688352108],
                        [-0.131048902869,0.798110127449,-0.588087081909],
                        [-0.108097285032,0.757922053337,-0.643326640129],
                        [-0.171839639544,0.759706020355,-0.627150595188],
                        [-0.091976031661,0.830952167511,-0.548688352108],
                        [-0.131048902869,0.798110127449,-0.588087081909],
                        [-0.153434738517,0.834331154823,-0.529480218887],
                        [-0.353819847107,0.701809465885,-0.618283927441],
                        [-0.327040165663,0.657660841942,-0.678621411324],
                        [-0.398910075426,0.645450055599,-0.65135627985],
                        [-0.213841319084,0.715529501438,-0.665048420429],
                        [-0.188148602843,0.669747889042,-0.718357801437],
                        [-0.256401896477,0.665616393089,-0.700865805149],
                        [-0.298754066229,0.610302150249,-0.733673810959],
                        [-0.269586592913,0.560828924179,-0.782811582088],
                        [-0.340069264174,0.550243675709,-0.762617051601],
                        [-0.256401896477,0.665616393089,-0.700865805149],
                        [-0.298754066229,0.610302150249,-0.733673810959],
                        [-0.327040165663,0.657660841942,-0.678621411324],
                        [-0.217834427953,0.834127128124,-0.506734728813],
                        [-0.26241543889,0.796284377575,-0.545040607452],
                        [-0.284414708614,0.829719662666,-0.480284929276],
                        [-0.171839639544,0.759706020355,-0.627150595188],
                        [-0.213841319084,0.715529501438,-0.665048420429],
                        [-0.238753452897,0.757998526096,-0.606988489628],
                        [-0.308011889458,0.752189457417,-0.582528710365],
                        [-0.353819847107,0.701809465885,-0.618283927441],
                        [-0.378517180681,0.74177056551,-0.553625464439],
                        [-0.238753452897,0.757998526096,-0.606988489628],
                        [-0.308011889458,0.752189457417,-0.582528710365],
                        [-0.26241543889,0.796284377575,-0.545040607452],
                        [-0.762617051601,0.340069264174,-0.550243675709],
                        [-0.733673810959,0.298754066229,-0.610302150249],
                        [-0.782811582088,0.269586592913,-0.560828924179],
                        [-0.65135627985,0.398910075426,-0.645450055599],
                        [-0.618283927441,0.353819847107,-0.701809465885],
                        [-0.678621411324,0.327040165663,-0.657660841942],
                        [-0.700865805149,0.256401896477,-0.665616393089],
                        [-0.665048420429,0.213841319084,-0.715529501438],
                        [-0.718357801437,0.188148602843,-0.669747889042],
                        [-0.678621411324,0.327040165663,-0.657660841942],
                        [-0.700865805149,0.256401896477,-0.665616393089],
                        [-0.733673810959,0.298754066229,-0.610302150249],
                        [-0.520354926586,0.44894811511,-0.726413309574],
                        [-0.485873311758,0.400663375854,-0.776785671711],
                        [-0.553625464439,0.378517180681,-0.74177056551],
                        [-0.379529476166,0.486395716667,-0.787004828453],
                        [-0.346611320972,0.436200261116,-0.830415487289],
                        [-0.416404157877,0.419940322638,-0.806385576725],
                        [-0.450116455555,0.352179646492,-0.820587992668],
                        [-0.413926929235,0.3044308424,-0.857896447182],
                        [-0.480284929276,0.284414708614,-0.829719662666],
                        [-0.416404157877,0.419940322638,-0.806385576725],
                        [-0.450116455555,0.352179646492,-0.820587992668],
                        [-0.485873311758,0.400663375854,-0.776785671711],
                        [-0.627150595188,0.171839639544,-0.759706020355],
                        [-0.588087081909,0.131048902869,-0.798110127449],
                        [-0.643326640129,0.108097285032,-0.757922053337],
                        [-0.506734728813,0.217834427953,-0.834127128124],
                        [-0.468421578407,0.174905076623,-0.866019308567],
                        [-0.529480218887,0.153434738517,-0.834331154823],
                        [-0.548688352108,0.091976031661,-0.830952167511],
                        [-0.509656965733,0.0549761541188,-0.858619451523],
                        [-0.564633131027,0.0339771322906,-0.82464236021],
                        [-0.529480218887,0.153434738517,-0.834331154823],
                        [-0.548688352108,0.091976031661,-0.830952167511],
                        [-0.588087081909,0.131048902869,-0.798110127449],
                        [-0.553625464439,0.378517180681,-0.74177056551],
                        [-0.582528710365,0.308011889458,-0.752189457417],
                        [-0.618283927441,0.353819847107,-0.701809465885],
                        [-0.480284929276,0.284414708614,-0.829719662666],
                        [-0.506734728813,0.217834427953,-0.834127128124],
                        [-0.545040607452,0.26241543889,-0.796284377575],
                        [-0.606988489628,0.238753452897,-0.757998526096],
                        [-0.627150595188,0.171839639544,-0.759706020355],
                        [-0.665048420429,0.213841319084,-0.715529501438],
                        [-0.545040607452,0.26241543889,-0.796284377575],
                        [-0.606988489628,0.238753452897,-0.757998526096],
                        [-0.582528710365,0.308011889458,-0.752189457417],
                        [-0.486395716667,0.787004828453,-0.379529476166],
                        [-0.535965919495,0.737060189247,-0.411682873964],
                        [-0.550243675709,0.762617051601,-0.340069264174],
                        [-0.44894811511,0.726413309574,-0.520354926586],
                        [-0.495975226164,0.669751524925,-0.552667617798],
                        [-0.517854511738,0.706037700176,-0.483050197363],
                        [-0.58378881216,0.680853009224,-0.44230055809],
                        [-0.628728508949,0.619044244289,-0.470621615648],
                        [-0.645450055599,0.65135627985,-0.398910075426],
                        [-0.517854511738,0.706037700176,-0.483050197363],
                        [-0.58378881216,0.680853009224,-0.44230055809],
                        [-0.535965919495,0.737060189247,-0.411682873964],
                        [-0.398910075426,0.645450055599,-0.65135627985],
                        [-0.44230055809,0.58378881216,-0.680853009224],
                        [-0.470621615648,0.628728508949,-0.619044244289],
                        [-0.340069264174,0.550243675709,-0.762617051601],
                        [-0.379529476166,0.486395716667,-0.787004828453],
                        [-0.411682873964,0.535965919495,-0.737060189247],
                        [-0.483050197363,0.517854511738,-0.706037700176],
                        [-0.520354926586,0.44894811511,-0.726413309574],
                        [-0.552667617798,0.495975226164,-0.669751524925],
                        [-0.411682873964,0.535965919495,-0.737060189247],
                        [-0.483050197363,0.517854511738,-0.706037700176],
                        [-0.44230055809,0.58378881216,-0.680853009224],
                        [-0.669751524925,0.552667617798,-0.495975226164],
                        [-0.706037700176,0.483050197363,-0.517854511738],
                        [-0.726413309574,0.520354926586,-0.44894811511],
                        [-0.619044244289,0.470621615648,-0.628728508949],
                        [-0.65135627985,0.398910075426,-0.645450055599],
                        [-0.680853009224,0.44230055809,-0.58378881216],
                        [-0.737060189247,0.411682873964,-0.535965919495],
                        [-0.762617051601,0.340069264174,-0.550243675709],
                        [-0.787004828453,0.379529476166,-0.486395716667],
                        [-0.680853009224,0.44230055809,-0.58378881216],
                        [-0.737060189247,0.411682873964,-0.535965919495],
                        [-0.706037700176,0.483050197363,-0.517854511738],
                        [-0.470621615648,0.628728508949,-0.619044244289],
                        [-0.540649950504,0.607478022575,-0.581951975822],
                        [-0.495975226164,0.669751524925,-0.552667617798],
                        [-0.552667617798,0.495975226164,-0.669751524925],
                        [-0.619044244289,0.470621615648,-0.628728508949],
                        [-0.581951975822,0.540649950504,-0.607478022575],
                        [-0.607478022575,0.581951975822,-0.540649950504],
                        [-0.669751524925,0.552667617798,-0.495975226164],
                        [-0.628728508949,0.619044244289,-0.470621615648],
                        [-0.581951975822,0.540649950504,-0.607478022575],
                        [-0.607478022575,0.581951975822,-0.540649950504],
                        [-0.540649950504,0.607478022575,-0.581951975822],
                        [0.475679844618,0.0,-0.8796184659],
                        [0.456712335348,0.0568443164229,-0.887796461582],
                        [0.509656965733,0.0549761541188,-0.858619451523],
                        [0.360324263573,0.0,-0.932827115059],
                        [0.334895044565,0.0602079555392,-0.940329909325],
                        [0.398431301117,0.0586068555713,-0.915323853493],
                        [0.434652328491,0.117213711143,-0.892938017845],
                        [0.409316182137,0.180623859167,-0.894335091114],
                        [0.468421578407,0.174905076623,-0.866019308567],
                        [0.398431301117,0.0586068555713,-0.915323853493],
                        [0.434652328491,0.117213711143,-0.892938017845],
                        [0.456712335348,0.0568443164229,-0.887796461582],
                        [0.225778326392,0.0,-0.974178731441],
                        [0.193714544177,0.0626873448491,-0.979053080082],
                        [0.266443610191,0.0615878328681,-0.961880862713],
                        [0.0770247355103,0.0,-0.997029185295],
                        [0.0394601933658,0.0638479366899,-0.997179210186],
                        [0.117650069296,0.0634539350867,-0.991025745869],
                        [0.158833146095,0.128498718143,-0.978907585144],
                        [0.121444880962,0.196501940489,-0.97295331955],
                        [0.199805602431,0.193975359201,-0.960443258286],
                        [0.117650069296,0.0634539350867,-0.991025745869],
                        [0.158833146095,0.128498718143,-0.978907585144],
                        [0.193714544177,0.0626873448491,-0.979053080082],
                        [0.380633711815,0.246351331472,-0.891307473183],
                        [0.348686188459,0.313436716795,-0.883275330067],
                        [0.413926929235,0.3044308424,-0.857896447182],
                        [0.239766731858,0.258633822203,-0.935745954514],
                        [0.202408134937,0.327503234148,-0.922915279865],
                        [0.277958005667,0.321246802807,-0.905284404755],
                        [0.313733518124,0.380723625422,-0.869839549065],
                        [0.276221334934,0.446935534477,-0.85085272789],
                        [0.346611320972,0.436200261116,-0.830415487289],
                        [0.277958005667,0.321246802807,-0.905284404755],
                        [0.313733518124,0.380723625422,-0.869839549065],
                        [0.348686188459,0.313436716795,-0.883275330067],
                        [0.266443610191,0.0615878328681,-0.961880862713],
                        [0.306287169456,0.123895764351,-0.943842172623],
                        [0.334895044565,0.0602079555392,-0.940329909325],
                        [0.199805602431,0.193975359201,-0.960443258286],
                        [0.239766731858,0.258633822203,-0.935745954514],
                        [0.274516820908,0.190361812711,-0.942551255226],
                        [0.34457308054,0.185843646526,-0.920180141926],
                        [0.380633711815,0.246351331472,-0.891307473183],
                        [0.409316182137,0.180623859167,-0.894335091114],
                        [0.274516820908,0.190361812711,-0.942551255226],
                        [0.34457308054,0.185843646526,-0.920180141926],
                        [0.306287169456,0.123895764351,-0.943842172623],
                        [-0.0770247355103,0.0,-0.997029185295],
                        [-0.117650069296,0.0634539350867,-0.991025745869],
                        [-0.0394601933658,0.0638479366899,-0.997179210186],
                        [-0.225778326392,0.0,-0.974178731441],
                        [-0.266443610191,0.0615878328681,-0.961880862713],
                        [-0.193714544177,0.0626873448491,-0.979053080082],
                        [-0.158833146095,0.128498718143,-0.978907585144],
                        [-0.199805602431,0.193975359201,-0.960443258286],
                        [-0.121444880962,0.196501940489,-0.97295331955],
                        [-0.193714544177,0.0626873448491,-0.979053080082],
                        [-0.158833146095,0.128498718143,-0.978907585144],
                        [-0.117650069296,0.0634539350867,-0.991025745869],
                        [-0.360324263573,0.0,-0.932827115059],
                        [-0.398431301117,0.0586068555713,-0.915323853493],
                        [-0.334895044565,0.0602079555392,-0.940329909325],
                        [-0.475679844618,0.0,-0.8796184659],
                        [-0.509656965733,0.0549761541188,-0.858619451523],
                        [-0.456712335348,0.0568443164229,-0.887796461582],
                        [-0.434652328491,0.117213711143,-0.892938017845],
                        [-0.468421578407,0.174905076623,-0.866019308567],
                        [-0.409316182137,0.180623859167,-0.894335091114],
                        [-0.456712335348,0.0568443164229,-0.887796461582],
                        [-0.434652328491,0.117213711143,-0.892938017845],
                        [-0.398431301117,0.0586068555713,-0.915323853493],
                        [-0.239766731858,0.258633822203,-0.935745954514],
                        [-0.277958005667,0.321246802807,-0.905284404755],
                        [-0.202408134937,0.327503234148,-0.922915279865],
                        [-0.380633711815,0.246351331472,-0.891307473183],
                        [-0.413926929235,0.3044308424,-0.857896447182],
                        [-0.348686188459,0.313436716795,-0.883275330067],
                        [-0.313733518124,0.380723625422,-0.869839549065],
                        [-0.346611320972,0.436200261116,-0.830415487289],
                        [-0.276221334934,0.446935534477,-0.85085272789],
                        [-0.348686188459,0.313436716795,-0.883275330067],
                        [-0.313733518124,0.380723625422,-0.869839549065],
                        [-0.277958005667,0.321246802807,-0.905284404755],
                        [-0.334895044565,0.0602079555392,-0.940329909325],
                        [-0.306287169456,0.123895764351,-0.943842172623],
                        [-0.266443610191,0.0615878328681,-0.961880862713],
                        [-0.409316182137,0.180623859167,-0.894335091114],
                        [-0.380633711815,0.246351331472,-0.891307473183],
                        [-0.34457308054,0.185843646526,-0.920180141926],
                        [-0.274516820908,0.190361812711,-0.942551255226],
                        [-0.239766731858,0.258633822203,-0.935745954514],
                        [-0.199805602431,0.193975359201,-0.960443258286],
                        [-0.34457308054,0.185843646526,-0.920180141926],
                        [-0.274516820908,0.190361812711,-0.942551255226],
                        [-0.306287169456,0.123895764351,-0.943842172623],
                        [0.236761152744,0.510783493519,-0.826465010643],
                        [0.196083456278,0.571085453033,-0.797127783298],
                        [0.269586592913,0.560828924179,-0.782811582088],
                        [0.0809632539749,0.524005174637,-0.847858190536],
                        [0.0399611219764,0.581926107407,-0.81225925684],
                        [0.119124859571,0.578244268894,-0.807120084763],
                        [0.154971644282,0.62687343359,-0.763553202152],
                        [0.114190116525,0.677466154099,-0.726636230946],
                        [0.188148602843,0.669747889042,-0.718357801437],
                        [0.119124859571,0.578244268894,-0.807120084763],
                        [0.154971644282,0.62687343359,-0.763553202152],
                        [0.196083456278,0.571085453033,-0.797127783298],
                        [-0.0809632539749,0.524005174637,-0.847858190536],
                        [-0.119124859571,0.578244268894,-0.807120084763],
                        [-0.0399611219764,0.581926107407,-0.81225925684],
                        [-0.236761152744,0.510783493519,-0.826465010643],
                        [-0.269586592913,0.560828924179,-0.782811582088],
                        [-0.196083456278,0.571085453033,-0.797127783298],
                        [-0.154971644282,0.62687343359,-0.763553202152],
                        [-0.188148602843,0.669747889042,-0.718357801437],
                        [-0.114190116525,0.677466154099,-0.726636230946],
                        [-0.196083456278,0.571085453033,-0.797127783298],
                        [-0.154971644282,0.62687343359,-0.763553202152],
                        [-0.119124859571,0.578244268894,-0.807120084763],
                        [0.0744211226702,0.722495436668,-0.687358558178],
                        [0.0362210273743,0.761889100075,-0.646693944931],
                        [0.108097285032,0.757922053337,-0.643326640129],
                        [-0.0744211226702,0.722495436668,-0.687358558178],
                        [-0.108097285032,0.757922053337,-0.643326640129],
                        [-0.0362210273743,0.761889100075,-0.646693944931],
                        [0.0,0.79582041502,-0.605532705784],
                        [-0.0339771322906,0.82464236021,-0.564633131027],
                        [0.0339771322906,0.82464236021,-0.564633131027],
                        [-0.0362210273743,0.761889100075,-0.646693944931],
                        [0.0,0.79582041502,-0.605532705784],
                        [0.0362210273743,0.761889100075,-0.646693944931],
                        [-0.0399611219764,0.581926107407,-0.81225925684],
                        [0.0,0.634539365768,-0.772890508175],
                        [0.0399611219764,0.581926107407,-0.81225925684],
                        [-0.114190116525,0.677466154099,-0.726636230946],
                        [-0.0744211226702,0.722495436668,-0.687358558178],
                        [-0.0382858961821,0.68142670393,-0.730884253979],
                        [0.0382858961821,0.68142670393,-0.730884253979],
                        [0.0744211226702,0.722495436668,-0.687358558178],
                        [0.114190116525,0.677466154099,-0.726636230946],
                        [-0.0382858961821,0.68142670393,-0.730884253979],
                        [0.0382858961821,0.68142670393,-0.730884253979],
                        [0.0,0.634539365768,-0.772890508175],
                        [-0.0394601933658,0.0638479366899,-0.997179210186],
                        [0.0,0.130150929093,-0.991494178772],
                        [0.0394601933658,0.0638479366899,-0.997179210186],
                        [-0.121444880962,0.196501940489,-0.97295331955],
                        [-0.0820460245013,0.265506535769,-0.960611641407],
                        [-0.0407496243715,0.197802826762,-0.979394435883],
                        [0.0407496243715,0.197802826762,-0.979394435883],
                        [0.0820460245013,0.265506535769,-0.960611641407],
                        [0.121444880962,0.196501940489,-0.97295331955],
                        [-0.0407496243715,0.197802826762,-0.979394435883],
                        [0.0407496243715,0.197802826762,-0.979394435883],
                        [0.0,0.130150929093,-0.991494178772],
                        [-0.202408134937,0.327503234148,-0.922915279865],
                        [-0.162998497486,0.395605653524,-0.903840482235],
                        [-0.123069040477,0.33188316226,-0.935258030891],
                        [-0.276221334934,0.446935534477,-0.85085272789],
                        [-0.236761152744,0.510783493519,-0.826465010643],
                        [-0.20109423995,0.455528259277,-0.867211103439],
                        [-0.122248865664,0.461539924145,-0.878655850887],
                        [-0.0809632539749,0.524005174637,-0.847858190536],
                        [-0.0410230122507,0.464636415243,-0.88455080986],
                        [-0.20109423995,0.455528259277,-0.867211103439],
                        [-0.122248865664,0.461539924145,-0.878655850887],
                        [-0.162998497486,0.395605653524,-0.903840482235],
                        [0.123069040477,0.33188316226,-0.935258030891],
                        [0.162998497486,0.395605653524,-0.903840482235],
                        [0.202408134937,0.327503234148,-0.922915279865],
                        [0.0410230122507,0.464636415243,-0.88455080986],
                        [0.0809632539749,0.524005174637,-0.847858190536],
                        [0.122248865664,0.461539924145,-0.878655850887],
                        [0.20109423995,0.455528259277,-0.867211103439],
                        [0.236761152744,0.510783493519,-0.826465010643],
                        [0.276221334934,0.446935534477,-0.85085272789],
                        [0.122248865664,0.461539924145,-0.878655850887],
                        [0.20109423995,0.455528259277,-0.867211103439],
                        [0.162998497486,0.395605653524,-0.903840482235],
                        [-0.123069040477,0.33188316226,-0.935258030891],
                        [-0.04130198434,0.334140062332,-0.941618084908],
                        [-0.0820460245013,0.265506535769,-0.960611641407],
                        [-0.0410230122507,0.464636415243,-0.88455080986],
                        [0.0410230122507,0.464636415243,-0.88455080986],
                        [0.0,0.400968074799,-0.916092038155],
                        [0.04130198434,0.334140062332,-0.941618084908],
                        [0.123069040477,0.33188316226,-0.935258030891],
                        [0.0820460245013,0.265506535769,-0.960611641407],
                        [0.0,0.400968074799,-0.916092038155],
                        [0.04130198434,0.334140062332,-0.941618084908],
                        [-0.04130198434,0.334140062332,-0.941618084908],
                        [0.509656965733,0.0549761541188,-0.858619451523],
                        [0.548688352108,0.091976031661,-0.830952167511],
                        [0.564633131027,0.0339771322906,-0.82464236021],
                        [0.468421578407,0.174905076623,-0.866019308567],
                        [0.506734728813,0.217834427953,-0.834127128124],
                        [0.529480218887,0.153434738517,-0.834331154823],
                        [0.588087081909,0.131048902869,-0.798110127449],
                        [0.627150595188,0.171839639544,-0.759706020355],
                        [0.643326640129,0.108097285032,-0.757922053337],
                        [0.529480218887,0.153434738517,-0.834331154823],
                        [0.588087081909,0.131048902869,-0.798110127449],
                        [0.548688352108,0.091976031661,-0.830952167511],
                        [0.413926929235,0.3044308424,-0.857896447182],
                        [0.450116455555,0.352179646492,-0.820587992668],
                        [0.480284929276,0.284414708614,-0.829719662666],
                        [0.346611320972,0.436200261116,-0.830415487289],
                        [0.379529476166,0.486395716667,-0.787004828453],
                        [0.416404157877,0.419940322638,-0.806385576725],
                        [0.485873311758,0.400663375854,-0.776785671711],
                        [0.520354926586,0.44894811511,-0.726413309574],
                        [0.553625464439,0.378517180681,-0.74177056551],
                        [0.416404157877,0.419940322638,-0.806385576725],
                        [0.485873311758,0.400663375854,-0.776785671711],
                        [0.450116455555,0.352179646492,-0.820587992668],
                        [0.665048420429,0.213841319084,-0.715529501438],
                        [0.700865805149,0.256401896477,-0.665616393089],
                        [0.718357801437,0.188148602843,-0.669747889042],
                        [0.618283927441,0.353819847107,-0.701809465885],
                        [0.65135627985,0.398910075426,-0.645450055599],
                        [0.678621411324,0.327040165663,-0.657660841942],
                        [0.733673810959,0.298754066229,-0.610302150249],
                        [0.762617051601,0.340069264174,-0.550243675709],
                        [0.782811582088,0.269586592913,-0.560828924179],
                        [0.678621411324,0.327040165663,-0.657660841942],
                        [0.733673810959,0.298754066229,-0.610302150249],
                        [0.700865805149,0.256401896477,-0.665616393089],
                        [0.480284929276,0.284414708614,-0.829719662666],
                        [0.545040607452,0.26241543889,-0.796284377575],
                        [0.506734728813,0.217834427953,-0.834127128124],
                        [0.553625464439,0.378517180681,-0.74177056551],
                        [0.618283927441,0.353819847107,-0.701809465885],
                        [0.582528710365,0.308011889458,-0.752189457417],
                        [0.606988489628,0.238753452897,-0.757998526096],
                        [0.665048420429,0.213841319084,-0.715529501438],
                        [0.627150595188,0.171839639544,-0.759706020355],
                        [0.582528710365,0.308011889458,-0.752189457417],
                        [0.606988489628,0.238753452897,-0.757998526096],
                        [0.545040607452,0.26241543889,-0.796284377575],
                        [0.269586592913,0.560828924179,-0.782811582088],
                        [0.298754066229,0.610302150249,-0.733673810959],
                        [0.340069264174,0.550243675709,-0.762617051601],
                        [0.188148602843,0.669747889042,-0.718357801437],
                        [0.213841319084,0.715529501438,-0.665048420429],
                        [0.256401896477,0.665616393089,-0.700865805149],
                        [0.327040165663,0.657660841942,-0.678621411324],
                        [0.353819847107,0.701809465885,-0.618283927441],
                        [0.398910075426,0.645450055599,-0.65135627985],
                        [0.256401896477,0.665616393089,-0.700865805149],
                        [0.327040165663,0.657660841942,-0.678621411324],
                        [0.298754066229,0.610302150249,-0.733673810959],
                        [0.108097285032,0.757922053337,-0.643326640129],
                        [0.131048902869,0.798110127449,-0.588087081909],
                        [0.171839639544,0.759706020355,-0.627150595188],
                        [0.0339771322906,0.82464236021,-0.564633131027],
                        [0.0549761541188,0.858619451523,-0.509656965733],
                        [0.091976031661,0.830952167511,-0.548688352108],
                        [0.153434738517,0.834331154823,-0.529480218887],
                        [0.174905076623,0.866019308567,-0.468421578407],
                        [0.217834427953,0.834127128124,-0.506734728813],
                        [0.091976031661,0.830952167511,-0.548688352108],
                        [0.153434738517,0.834331154823,-0.529480218887],
                        [0.131048902869,0.798110127449,-0.588087081909],
                        [0.378517180681,0.74177056551,-0.553625464439],
                        [0.400663375854,0.776785671711,-0.485873311758],
                        [0.44894811511,0.726413309574,-0.520354926586],
                        [0.284414708614,0.829719662666,-0.480284929276],
                        [0.3044308424,0.857896447182,-0.413926929235],
                        [0.352179646492,0.820587992668,-0.450116455555],
                        [0.419940322638,0.806385576725,-0.416404157877],
                        [0.436200261116,0.830415487289,-0.346611320972],
                        [0.486395716667,0.787004828453,-0.379529476166],
                        [0.352179646492,0.820587992668,-0.450116455555],
                        [0.419940322638,0.806385576725,-0.416404157877],
                        [0.400663375854,0.776785671711,-0.485873311758],
                        [0.171839639544,0.759706020355,-0.627150595188],
                        [0.238753452897,0.757998526096,-0.606988489628],
                        [0.213841319084,0.715529501438,-0.665048420429],
                        [0.217834427953,0.834127128124,-0.506734728813],
                        [0.284414708614,0.829719662666,-0.480284929276],
                        [0.26241543889,0.796284377575,-0.545040607452],
                        [0.308011889458,0.752189457417,-0.582528710365],
                        [0.378517180681,0.74177056551,-0.553625464439],
                        [0.353819847107,0.701809465885,-0.618283927441],
                        [0.26241543889,0.796284377575,-0.545040607452],
                        [0.308011889458,0.752189457417,-0.582528710365],
                        [0.238753452897,0.757998526096,-0.606988489628],
                        [0.787004828453,0.379529476166,-0.486395716667],
                        [0.806385576725,0.416404157877,-0.419940322638],
                        [0.830415487289,0.346611320972,-0.436200261116],
                        [0.726413309574,0.520354926586,-0.44894811511],
                        [0.74177056551,0.553625464439,-0.378517180681],
                        [0.776785671711,0.485873311758,-0.400663375854],
                        [0.820587992668,0.450116455555,-0.352179646492],
                        [0.829719662666,0.480284929276,-0.284414708614],
                        [0.857896447182,0.413926929235,-0.3044308424],
                        [0.776785671711,0.485873311758,-0.400663375854],
                        [0.820587992668,0.450116455555,-0.352179646492],
                        [0.806385576725,0.416404157877,-0.419940322638],
                        [0.645450055599,0.65135627985,-0.398910075426],
                        [0.657660841942,0.678621411324,-0.327040165663],
                        [0.701809465885,0.618283927441,-0.353819847107],
                        [0.550243675709,0.762617051601,-0.340069264174],
                        [0.560828924179,0.782811582088,-0.269586592913],
                        [0.610302150249,0.733673810959,-0.298754066229],
                        [0.665616393089,0.700865805149,-0.256401896477],
                        [0.669747889042,0.718357801437,-0.188148602843],
                        [0.715529501438,0.665048420429,-0.213841319084],
                        [0.610302150249,0.733673810959,-0.298754066229],
                        [0.665616393089,0.700865805149,-0.256401896477],
                        [0.657660841942,0.678621411324,-0.327040165663],
                        [0.834127128124,0.506734728813,-0.217834427953],
                        [0.834331154823,0.529480218887,-0.153434738517],
                        [0.866019308567,0.468421578407,-0.174905076623],
                        [0.759706020355,0.627150595188,-0.171839639544],
                        [0.757922053337,0.643326640129,-0.108097285032],
                        [0.798110127449,0.588087081909,-0.131048902869],
                        [0.830952167511,0.548688352108,-0.091976031661],
                        [0.82464236021,0.564633131027,-0.0339771322906],
                        [0.858619451523,0.509656965733,-0.0549761541188],
                        [0.798110127449,0.588087081909,-0.131048902869],
                        [0.830952167511,0.548688352108,-0.091976031661],
                        [0.834331154823,0.529480218887,-0.153434738517],
                        [0.701809465885,0.618283927441,-0.353819847107],
                        [0.752189457417,0.582528710365,-0.308011889458],
                        [0.74177056551,0.553625464439,-0.378517180681],
                        [0.715529501438,0.665048420429,-0.213841319084],
                        [0.759706020355,0.627150595188,-0.171839639544],
                        [0.757998526096,0.606988489628,-0.238753452897],
                        [0.796284377575,0.545040607452,-0.26241543889],
                        [0.834127128124,0.506734728813,-0.217834427953],
                        [0.829719662666,0.480284929276,-0.284414708614],
                        [0.757998526096,0.606988489628,-0.238753452897],
                        [0.796284377575,0.545040607452,-0.26241543889],
                        [0.752189457417,0.582528710365,-0.308011889458],
                        [0.340069264174,0.550243675709,-0.762617051601],
                        [0.411682873964,0.535965919495,-0.737060189247],
                        [0.379529476166,0.486395716667,-0.787004828453],
                        [0.398910075426,0.645450055599,-0.65135627985],
                        [0.470621615648,0.628728508949,-0.619044244289],
                        [0.44230055809,0.58378881216,-0.680853009224],
                        [0.483050197363,0.517854511738,-0.706037700176],
                        [0.552667617798,0.495975226164,-0.669751524925],
                        [0.520354926586,0.44894811511,-0.726413309574],
                        [0.44230055809,0.58378881216,-0.680853009224],
                        [0.483050197363,0.517854511738,-0.706037700176],
                        [0.411682873964,0.535965919495,-0.737060189247],
                        [0.44894811511,0.726413309574,-0.520354926586],
                        [0.517854511738,0.706037700176,-0.483050197363],
                        [0.495975226164,0.669751524925,-0.552667617798],
                        [0.486395716667,0.787004828453,-0.379529476166],
                        [0.550243675709,0.762617051601,-0.340069264174],
                        [0.535965919495,0.737060189247,-0.411682873964],
                        [0.58378881216,0.680853009224,-0.44230055809],
                        [0.645450055599,0.65135627985,-0.398910075426],
                        [0.628728508949,0.619044244289,-0.470621615648],
                        [0.535965919495,0.737060189247,-0.411682873964],
                        [0.58378881216,0.680853009224,-0.44230055809],
                        [0.517854511738,0.706037700176,-0.483050197363],
                        [0.619044244289,0.470621615648,-0.628728508949],
                        [0.680853009224,0.44230055809,-0.58378881216],
                        [0.65135627985,0.398910075426,-0.645450055599],
                        [0.669751524925,0.552667617798,-0.495975226164],
                        [0.726413309574,0.520354926586,-0.44894811511],
                        [0.706037700176,0.483050197363,-0.517854511738],
                        [0.737060189247,0.411682873964,-0.535965919495],
                        [0.787004828453,0.379529476166,-0.486395716667],
                        [0.762617051601,0.340069264174,-0.550243675709],
                        [0.706037700176,0.483050197363,-0.517854511738],
                        [0.737060189247,0.411682873964,-0.535965919495],
                        [0.680853009224,0.44230055809,-0.58378881216],
                        [0.495975226164,0.669751524925,-0.552667617798],
                        [0.540649950504,0.607478022575,-0.581951975822],
                        [0.470621615648,0.628728508949,-0.619044244289],
                        [0.628728508949,0.619044244289,-0.470621615648],
                        [0.669751524925,0.552667617798,-0.495975226164],
                        [0.607478022575,0.581951975822,-0.540649950504],
                        [0.581951975822,0.540649950504,-0.607478022575],
                        [0.619044244289,0.470621615648,-0.628728508949],
                        [0.552667617798,0.495975226164,-0.669751524925],
                        [0.607478022575,0.581951975822,-0.540649950504],
                        [0.581951975822,0.540649950504,-0.607478022575],
                        [0.540649950504,0.607478022575,-0.581951975822],
                        [0.82464236021,0.564633131027,-0.0339771322906],
                        [0.79582041502,0.605532705784,0.0],
                        [0.82464236021,0.564633131027,0.0339771322906],
                        [0.757922053337,0.643326640129,-0.108097285032],
                        [0.722495436668,0.687358558178,-0.0744211226702],
                        [0.761889100075,0.646693944931,-0.0362210273743],
                        [0.761889100075,0.646693944931,0.0362210273743],
                        [0.722495436668,0.687358558178,0.0744211226702],
                        [0.757922053337,0.643326640129,0.108097285032],
                        [0.761889100075,0.646693944931,-0.0362210273743],
                        [0.761889100075,0.646693944931,0.0362210273743],
                        [0.79582041502,0.605532705784,0.0],
                        [0.669747889042,0.718357801437,-0.188148602843],
                        [0.62687343359,0.763553202152,-0.154971644282],
                        [0.677466154099,0.726636230946,-0.114190116525],
                        [0.560828924179,0.782811582088,-0.269586592913],
                        [0.510783493519,0.826465010643,-0.236761152744],
                        [0.571085453033,0.797127783298,-0.196083456278],
                        [0.578244268894,0.807120084763,-0.119124859571],
                        [0.524005174637,0.847858190536,-0.0809632539749],
                        [0.581926107407,0.81225925684,-0.0399611219764],
                        [0.571085453033,0.797127783298,-0.196083456278],
                        [0.578244268894,0.807120084763,-0.119124859571],
                        [0.62687343359,0.763553202152,-0.154971644282],
                        [0.677466154099,0.726636230946,0.114190116525],
                        [0.62687343359,0.763553202152,0.154971644282],
                        [0.669747889042,0.718357801437,0.188148602843],
                        [0.581926107407,0.81225925684,0.0399611219764],
                        [0.524005174637,0.847858190536,0.0809632539749],
                        [0.578244268894,0.807120084763,0.119124859571],
                        [0.571085453033,0.797127783298,0.196083456278],
                        [0.510783493519,0.826465010643,0.236761152744],
                        [0.560828924179,0.782811582088,0.269586592913],
                        [0.578244268894,0.807120084763,0.119124859571],
                        [0.571085453033,0.797127783298,0.196083456278],
                        [0.62687343359,0.763553202152,0.154971644282],
                        [0.677466154099,0.726636230946,-0.114190116525],
                        [0.68142670393,0.730884253979,-0.0382858961821],
                        [0.722495436668,0.687358558178,-0.0744211226702],
                        [0.581926107407,0.81225925684,-0.0399611219764],
                        [0.581926107407,0.81225925684,0.0399611219764],
                        [0.634539365768,0.772890508175,0.0],
                        [0.68142670393,0.730884253979,0.0382858961821],
                        [0.677466154099,0.726636230946,0.114190116525],
                        [0.722495436668,0.687358558178,0.0744211226702],
                        [0.634539365768,0.772890508175,0.0],
                        [0.68142670393,0.730884253979,0.0382858961821],
                        [0.68142670393,0.730884253979,-0.0382858961821],
                        [0.436200261116,0.830415487289,-0.346611320972],
                        [0.380723625422,0.869839549065,-0.313733518124],
                        [0.446935534477,0.85085272789,-0.276221334934],
                        [0.3044308424,0.857896447182,-0.413926929235],
                        [0.246351331472,0.891307473183,-0.380633711815],
                        [0.313436716795,0.883275330067,-0.348686188459],
                        [0.321246802807,0.905284404755,-0.277958005667],
                        [0.258633822203,0.935745954514,-0.239766731858],
                        [0.327503234148,0.922915279865,-0.202408134937],
                        [0.313436716795,0.883275330067,-0.348686188459],
                        [0.321246802807,0.905284404755,-0.277958005667],
                        [0.380723625422,0.869839549065,-0.313733518124],
                        [0.174905076623,0.866019308567,-0.468421578407],
                        [0.117213711143,0.892938017845,-0.434652328491],
                        [0.180623859167,0.894335091114,-0.409316182137],
                        [0.0549761541188,0.858619451523,-0.509656965733],
                        [0.0,0.8796184659,-0.475679844618],
                        [0.0568443164229,0.887796461582,-0.456712335348],
                        [0.0586068555713,0.915323853493,-0.398431301117],
                        [0.0,0.932827115059,-0.360324263573],
                        [0.0602079555392,0.940329909325,-0.334895044565],
                        [0.0568443164229,0.887796461582,-0.456712335348],
                        [0.0586068555713,0.915323853493,-0.398431301117],
                        [0.117213711143,0.892938017845,-0.434652328491],
                        [0.193975359201,0.960443258286,-0.199805602431],
                        [0.128498718143,0.978907585144,-0.158833146095],
                        [0.196501940489,0.97295331955,-0.121444880962],
                        [0.0615878328681,0.961880862713,-0.266443610191],
                        [0.0,0.974178731441,-0.225778326392],
                        [0.0626873448491,0.979053080082,-0.193714544177],
                        [0.0634539350867,0.991025745869,-0.117650069296],
                        [0.0,0.997029185295,-0.0770247355103],
                        [0.0638479366899,0.997179210186,-0.0394601933658],
                        [0.0626873448491,0.979053080082,-0.193714544177],
                        [0.0634539350867,0.991025745869,-0.117650069296],
                        [0.128498718143,0.978907585144,-0.158833146095],
                        [0.180623859167,0.894335091114,-0.409316182137],
                        [0.185843646526,0.920180141926,-0.34457308054],
                        [0.246351331472,0.891307473183,-0.380633711815],
                        [0.0602079555392,0.940329909325,-0.334895044565],
                        [0.0615878328681,0.961880862713,-0.266443610191],
                        [0.123895764351,0.943842172623,-0.306287169456],
                        [0.190361812711,0.942551255226,-0.274516820908],
                        [0.193975359201,0.960443258286,-0.199805602431],
                        [0.258633822203,0.935745954514,-0.239766731858],
                        [0.123895764351,0.943842172623,-0.306287169456],
                        [0.190361812711,0.942551255226,-0.274516820908],
                        [0.185843646526,0.920180141926,-0.34457308054],
                        [0.446935534477,0.85085272789,0.276221334934],
                        [0.380723625422,0.869839549065,0.313733518124],
                        [0.436200261116,0.830415487289,0.346611320972],
                        [0.327503234148,0.922915279865,0.202408134937],
                        [0.258633822203,0.935745954514,0.239766731858],
                        [0.321246802807,0.905284404755,0.277958005667],
                        [0.313436716795,0.883275330067,0.348686188459],
                        [0.246351331472,0.891307473183,0.380633711815],
                        [0.3044308424,0.857896447182,0.413926929235],
                        [0.321246802807,0.905284404755,0.277958005667],
                        [0.313436716795,0.883275330067,0.348686188459],
                        [0.380723625422,0.869839549065,0.313733518124],
                        [0.196501940489,0.97295331955,0.121444880962],
                        [0.128498718143,0.978907585144,0.158833146095],
                        [0.193975359201,0.960443258286,0.199805602431],
                        [0.0638479366899,0.997179210186,0.0394601933658],
                        [0.0,0.997029185295,0.0770247355103],
                        [0.0634539350867,0.991025745869,0.117650069296],
                        [0.0626873448491,0.979053080082,0.193714544177],
                        [0.0,0.974178731441,0.225778326392],
                        [0.0615878328681,0.961880862713,0.266443610191],
                        [0.0634539350867,0.991025745869,0.117650069296],
                        [0.0626873448491,0.979053080082,0.193714544177],
                        [0.128498718143,0.978907585144,0.158833146095],
                        [0.180623859167,0.894335091114,0.409316182137],
                        [0.117213711143,0.892938017845,0.434652328491],
                        [0.174905076623,0.866019308567,0.468421578407],
                        [0.0602079555392,0.940329909325,0.334895044565],
                        [0.0,0.932827115059,0.360324263573],
                        [0.0586068555713,0.915323853493,0.398431301117],
                        [0.0568443164229,0.887796461582,0.456712335348],
                        [0.0,0.8796184659,0.475679844618],
                        [0.0549761541188,0.858619451523,0.509656965733],
                        [0.0586068555713,0.915323853493,0.398431301117],
                        [0.0568443164229,0.887796461582,0.456712335348],
                        [0.117213711143,0.892938017845,0.434652328491],
                        [0.193975359201,0.960443258286,0.199805602431],
                        [0.190361812711,0.942551255226,0.274516820908],
                        [0.258633822203,0.935745954514,0.239766731858],
                        [0.0615878328681,0.961880862713,0.266443610191],
                        [0.0602079555392,0.940329909325,0.334895044565],
                        [0.123895764351,0.943842172623,0.306287169456],
                        [0.185843646526,0.920180141926,0.34457308054],
                        [0.180623859167,0.894335091114,0.409316182137],
                        [0.246351331472,0.891307473183,0.380633711815],
                        [0.123895764351,0.943842172623,0.306287169456],
                        [0.185843646526,0.920180141926,0.34457308054],
                        [0.190361812711,0.942551255226,0.274516820908],
                        [0.446935534477,0.85085272789,-0.276221334934],
                        [0.455528259277,0.867211103439,-0.20109423995],
                        [0.510783493519,0.826465010643,-0.236761152744],
                        [0.327503234148,0.922915279865,-0.202408134937],
                        [0.33188316226,0.935258030891,-0.123069040477],
                        [0.395605653524,0.903840482235,-0.162998497486],
                        [0.461539924145,0.878655850887,-0.122248865664],
                        [0.464636415243,0.88455080986,-0.0410230122507],
                        [0.524005174637,0.847858190536,-0.0809632539749],
                        [0.395605653524,0.903840482235,-0.162998497486],
                        [0.461539924145,0.878655850887,-0.122248865664],
                        [0.455528259277,0.867211103439,-0.20109423995],
                        [0.196501940489,0.97295331955,-0.121444880962],
                        [0.197802826762,0.979394435883,-0.0407496243715],
                        [0.265506535769,0.960611641407,-0.0820460245013],
                        [0.0638479366899,0.997179210186,-0.0394601933658],
                        [0.0638479366899,0.997179210186,0.0394601933658],
                        [0.130150929093,0.991494178772,0.0],
                        [0.197802826762,0.979394435883,0.0407496243715],
                        [0.196501940489,0.97295331955,0.121444880962],
                        [0.265506535769,0.960611641407,0.0820460245013],
                        [0.130150929093,0.991494178772,0.0],
                        [0.197802826762,0.979394435883,0.0407496243715],
                        [0.197802826762,0.979394435883,-0.0407496243715],
                        [0.464636415243,0.88455080986,0.0410230122507],
                        [0.461539924145,0.878655850887,0.122248865664],
                        [0.524005174637,0.847858190536,0.0809632539749],
                        [0.33188316226,0.935258030891,0.123069040477],
                        [0.327503234148,0.922915279865,0.202408134937],
                        [0.395605653524,0.903840482235,0.162998497486],
                        [0.455528259277,0.867211103439,0.20109423995],
                        [0.446935534477,0.85085272789,0.276221334934],
                        [0.510783493519,0.826465010643,0.236761152744],
                        [0.395605653524,0.903840482235,0.162998497486],
                        [0.455528259277,0.867211103439,0.20109423995],
                        [0.461539924145,0.878655850887,0.122248865664],
                        [0.265506535769,0.960611641407,-0.0820460245013],
                        [0.334140062332,0.941618084908,-0.04130198434],
                        [0.33188316226,0.935258030891,-0.123069040477],
                        [0.265506535769,0.960611641407,0.0820460245013],
                        [0.33188316226,0.935258030891,0.123069040477],
                        [0.334140062332,0.941618084908,0.04130198434],
                        [0.400968074799,0.916092038155,0.0],
                        [0.464636415243,0.88455080986,0.0410230122507],
                        [0.464636415243,0.88455080986,-0.0410230122507],
                        [0.334140062332,0.941618084908,0.04130198434],
                        [0.400968074799,0.916092038155,0.0],
                        [0.334140062332,0.941618084908,-0.04130198434],
                        [0.82464236021,0.564633131027,0.0339771322906],
                        [0.830952167511,0.548688352108,0.091976031661],
                        [0.858619451523,0.509656965733,0.0549761541188],
                        [0.757922053337,0.643326640129,0.108097285032],
                        [0.759706020355,0.627150595188,0.171839639544],
                        [0.798110127449,0.588087081909,0.131048902869],
                        [0.834331154823,0.529480218887,0.153434738517],
                        [0.834127128124,0.506734728813,0.217834427953],
                        [0.866019308567,0.468421578407,0.174905076623],
                        [0.798110127449,0.588087081909,0.131048902869],
                        [0.834331154823,0.529480218887,0.153434738517],
                        [0.830952167511,0.548688352108,0.091976031661],
                        [0.669747889042,0.718357801437,0.188148602843],
                        [0.665616393089,0.700865805149,0.256401896477],
                        [0.715529501438,0.665048420429,0.213841319084],
                        [0.560828924179,0.782811582088,0.269586592913],
                        [0.550243675709,0.762617051601,0.340069264174],
                        [0.610302150249,0.733673810959,0.298754066229],
                        [0.657660841942,0.678621411324,0.327040165663],
                        [0.645450055599,0.65135627985,0.398910075426],
                        [0.701809465885,0.618283927441,0.353819847107],
                        [0.610302150249,0.733673810959,0.298754066229],
                        [0.657660841942,0.678621411324,0.327040165663],
                        [0.665616393089,0.700865805149,0.256401896477],
                        [0.829719662666,0.480284929276,0.284414708614],
                        [0.820587992668,0.450116455555,0.352179646492],
                        [0.857896447182,0.413926929235,0.3044308424],
                        [0.74177056551,0.553625464439,0.378517180681],
                        [0.726413309574,0.520354926586,0.44894811511],
                        [0.776785671711,0.485873311758,0.400663375854],
                        [0.806385576725,0.416404157877,0.419940322638],
                        [0.787004828453,0.379529476166,0.486395716667],
                        [0.830415487289,0.346611320972,0.436200261116],
                        [0.776785671711,0.485873311758,0.400663375854],
                        [0.806385576725,0.416404157877,0.419940322638],
                        [0.820587992668,0.450116455555,0.352179646492],
                        [0.715529501438,0.665048420429,0.213841319084],
                        [0.757998526096,0.606988489628,0.238753452897],
                        [0.759706020355,0.627150595188,0.171839639544],
                        [0.701809465885,0.618283927441,0.353819847107],
                        [0.74177056551,0.553625464439,0.378517180681],
                        [0.752189457417,0.582528710365,0.308011889458],
                        [0.796284377575,0.545040607452,0.26241543889],
                        [0.829719662666,0.480284929276,0.284414708614],
                        [0.834127128124,0.506734728813,0.217834427953],
                        [0.752189457417,0.582528710365,0.308011889458],
                        [0.796284377575,0.545040607452,0.26241543889],
                        [0.757998526096,0.606988489628,0.238753452897],
                        [0.436200261116,0.830415487289,0.346611320972],
                        [0.419940322638,0.806385576725,0.416404157877],
                        [0.486395716667,0.787004828453,0.379529476166],
                        [0.3044308424,0.857896447182,0.413926929235],
                        [0.284414708614,0.829719662666,0.480284929276],
                        [0.352179646492,0.820587992668,0.450116455555],
                        [0.400663375854,0.776785671711,0.485873311758],
                        [0.378517180681,0.74177056551,0.553625464439],
                        [0.44894811511,0.726413309574,0.520354926586],
                        [0.352179646492,0.820587992668,0.450116455555],
                        [0.400663375854,0.776785671711,0.485873311758],
                        [0.419940322638,0.806385576725,0.416404157877],
                        [0.174905076623,0.866019308567,0.468421578407],
                        [0.153434738517,0.834331154823,0.529480218887],
                        [0.217834427953,0.834127128124,0.506734728813],
                        [0.0549761541188,0.858619451523,0.509656965733],
                        [0.0339771322906,0.82464236021,0.564633131027],
                        [0.091976031661,0.830952167511,0.548688352108],
                        [0.131048902869,0.798110127449,0.588087081909],
                        [0.108097285032,0.757922053337,0.643326640129],
                        [0.171839639544,0.759706020355,0.627150595188],
                        [0.091976031661,0.830952167511,0.548688352108],
                        [0.131048902869,0.798110127449,0.588087081909],
                        [0.153434738517,0.834331154823,0.529480218887],
                        [0.353819847107,0.701809465885,0.618283927441],
                        [0.327040165663,0.657660841942,0.678621411324],
                        [0.398910075426,0.645450055599,0.65135627985],
                        [0.213841319084,0.715529501438,0.665048420429],
                        [0.188148602843,0.669747889042,0.718357801437],
                        [0.256401896477,0.665616393089,0.700865805149],
                        [0.298754066229,0.610302150249,0.733673810959],
                        [0.269586592913,0.560828924179,0.782811582088],
                        [0.340069264174,0.550243675709,0.762617051601],
                        [0.256401896477,0.665616393089,0.700865805149],
                        [0.298754066229,0.610302150249,0.733673810959],
                        [0.327040165663,0.657660841942,0.678621411324],
                        [0.217834427953,0.834127128124,0.506734728813],
                        [0.26241543889,0.796284377575,0.545040607452],
                        [0.284414708614,0.829719662666,0.480284929276],
                        [0.171839639544,0.759706020355,0.627150595188],
                        [0.213841319084,0.715529501438,0.665048420429],
                        [0.238753452897,0.757998526096,0.606988489628],
                        [0.308011889458,0.752189457417,0.582528710365],
                        [0.353819847107,0.701809465885,0.618283927441],
                        [0.378517180681,0.74177056551,0.553625464439],
                        [0.238753452897,0.757998526096,0.606988489628],
                        [0.308011889458,0.752189457417,0.582528710365],
                        [0.26241543889,0.796284377575,0.545040607452],
                        [0.762617051601,0.340069264174,0.550243675709],
                        [0.733673810959,0.298754066229,0.610302150249],
                        [0.782811582088,0.269586592913,0.560828924179],
                        [0.65135627985,0.398910075426,0.645450055599],
                        [0.618283927441,0.353819847107,0.701809465885],
                        [0.678621411324,0.327040165663,0.657660841942],
                        [0.700865805149,0.256401896477,0.665616393089],
                        [0.665048420429,0.213841319084,0.715529501438],
                        [0.718357801437,0.188148602843,0.669747889042],
                        [0.678621411324,0.327040165663,0.657660841942],
                        [0.700865805149,0.256401896477,0.665616393089],
                        [0.733673810959,0.298754066229,0.610302150249],
                        [0.520354926586,0.44894811511,0.726413309574],
                        [0.485873311758,0.400663375854,0.776785671711],
                        [0.553625464439,0.378517180681,0.74177056551],
                        [0.379529476166,0.486395716667,0.787004828453],
                        [0.346611320972,0.436200261116,0.830415487289],
                        [0.416404157877,0.419940322638,0.806385576725],
                        [0.450116455555,0.352179646492,0.820587992668],
                        [0.413926929235,0.3044308424,0.857896447182],
                        [0.480284929276,0.284414708614,0.829719662666],
                        [0.416404157877,0.419940322638,0.806385576725],
                        [0.450116455555,0.352179646492,0.820587992668],
                        [0.485873311758,0.400663375854,0.776785671711],
                        [0.627150595188,0.171839639544,0.759706020355],
                        [0.588087081909,0.131048902869,0.798110127449],
                        [0.643326640129,0.108097285032,0.757922053337],
                        [0.506734728813,0.217834427953,0.834127128124],
                        [0.468421578407,0.174905076623,0.866019308567],
                        [0.529480218887,0.153434738517,0.834331154823],
                        [0.548688352108,0.091976031661,0.830952167511],
                        [0.509656965733,0.0549761541188,0.858619451523],
                        [0.564633131027,0.0339771322906,0.82464236021],
                        [0.529480218887,0.153434738517,0.834331154823],
                        [0.548688352108,0.091976031661,0.830952167511],
                        [0.588087081909,0.131048902869,0.798110127449],
                        [0.553625464439,0.378517180681,0.74177056551],
                        [0.582528710365,0.308011889458,0.752189457417],
                        [0.618283927441,0.353819847107,0.701809465885],
                        [0.480284929276,0.284414708614,0.829719662666],
                        [0.506734728813,0.217834427953,0.834127128124],
                        [0.545040607452,0.26241543889,0.796284377575],
                        [0.606988489628,0.238753452897,0.757998526096],
                        [0.627150595188,0.171839639544,0.759706020355],
                        [0.665048420429,0.213841319084,0.715529501438],
                        [0.545040607452,0.26241543889,0.796284377575],
                        [0.606988489628,0.238753452897,0.757998526096],
                        [0.582528710365,0.308011889458,0.752189457417],
                        [0.486395716667,0.787004828453,0.379529476166],
                        [0.535965919495,0.737060189247,0.411682873964],
                        [0.550243675709,0.762617051601,0.340069264174],
                        [0.44894811511,0.726413309574,0.520354926586],
                        [0.495975226164,0.669751524925,0.552667617798],
                        [0.517854511738,0.706037700176,0.483050197363],
                        [0.58378881216,0.680853009224,0.44230055809],
                        [0.628728508949,0.619044244289,0.470621615648],
                        [0.645450055599,0.65135627985,0.398910075426],
                        [0.517854511738,0.706037700176,0.483050197363],
                        [0.58378881216,0.680853009224,0.44230055809],
                        [0.535965919495,0.737060189247,0.411682873964],
                        [0.398910075426,0.645450055599,0.65135627985],
                        [0.44230055809,0.58378881216,0.680853009224],
                        [0.470621615648,0.628728508949,0.619044244289],
                        [0.340069264174,0.550243675709,0.762617051601],
                        [0.379529476166,0.486395716667,0.787004828453],
                        [0.411682873964,0.535965919495,0.737060189247],
                        [0.483050197363,0.517854511738,0.706037700176],
                        [0.520354926586,0.44894811511,0.726413309574],
                        [0.552667617798,0.495975226164,0.669751524925],
                        [0.411682873964,0.535965919495,0.737060189247],
                        [0.483050197363,0.517854511738,0.706037700176],
                        [0.44230055809,0.58378881216,0.680853009224],
                        [0.669751524925,0.552667617798,0.495975226164],
                        [0.706037700176,0.483050197363,0.517854511738],
                        [0.726413309574,0.520354926586,0.44894811511],
                        [0.619044244289,0.470621615648,0.628728508949],
                        [0.65135627985,0.398910075426,0.645450055599],
                        [0.680853009224,0.44230055809,0.58378881216],
                        [0.737060189247,0.411682873964,0.535965919495],
                        [0.762617051601,0.340069264174,0.550243675709],
                        [0.787004828453,0.379529476166,0.486395716667],
                        [0.680853009224,0.44230055809,0.58378881216],
                        [0.737060189247,0.411682873964,0.535965919495],
                        [0.706037700176,0.483050197363,0.517854511738],
                        [0.470621615648,0.628728508949,0.619044244289],
                        [0.540649950504,0.607478022575,0.581951975822],
                        [0.495975226164,0.669751524925,0.552667617798],
                        [0.552667617798,0.495975226164,0.669751524925],
                        [0.619044244289,0.470621615648,0.628728508949],
                        [0.581951975822,0.540649950504,0.607478022575],
                        [0.607478022575,0.581951975822,0.540649950504],
                        [0.669751524925,0.552667617798,0.495975226164],
                        [0.628728508949,0.619044244289,0.470621615648],
                        [0.581951975822,0.540649950504,0.607478022575],
                        [0.607478022575,0.581951975822,0.540649950504],
                        [0.540649950504,0.607478022575,0.581951975822],
                        [0.8796184659,-0.475679844618,0.0],
                        [0.887796461582,-0.456712335348,0.0568443164229],
                        [0.858619451523,-0.509656965733,0.0549761541188],
                        [0.932827115059,-0.360324263573,0.0],
                        [0.940329909325,-0.334895044565,0.0602079555392],
                        [0.915323853493,-0.398431301117,0.0586068555713],
                        [0.892938017845,-0.434652328491,0.117213711143],
                        [0.894335091114,-0.409316182137,0.180623859167],
                        [0.866019308567,-0.468421578407,0.174905076623],
                        [0.915323853493,-0.398431301117,0.0586068555713],
                        [0.892938017845,-0.434652328491,0.117213711143],
                        [0.887796461582,-0.456712335348,0.0568443164229],
                        [0.974178731441,-0.225778326392,0.0],
                        [0.979053080082,-0.193714544177,0.0626873448491],
                        [0.961880862713,-0.266443610191,0.0615878328681],
                        [0.997029185295,-0.0770247355103,0.0],
                        [0.997179210186,-0.0394601933658,0.0638479366899],
                        [0.991025745869,-0.117650069296,0.0634539350867],
                        [0.978907585144,-0.158833146095,0.128498718143],
                        [0.97295331955,-0.121444880962,0.196501940489],
                        [0.960443258286,-0.199805602431,0.193975359201],
                        [0.991025745869,-0.117650069296,0.0634539350867],
                        [0.978907585144,-0.158833146095,0.128498718143],
                        [0.979053080082,-0.193714544177,0.0626873448491],
                        [0.891307473183,-0.380633711815,0.246351331472],
                        [0.883275330067,-0.348686188459,0.313436716795],
                        [0.857896447182,-0.413926929235,0.3044308424],
                        [0.935745954514,-0.239766731858,0.258633822203],
                        [0.922915279865,-0.202408134937,0.327503234148],
                        [0.905284404755,-0.277958005667,0.321246802807],
                        [0.869839549065,-0.313733518124,0.380723625422],
                        [0.85085272789,-0.276221334934,0.446935534477],
                        [0.830415487289,-0.346611320972,0.436200261116],
                        [0.905284404755,-0.277958005667,0.321246802807],
                        [0.869839549065,-0.313733518124,0.380723625422],
                        [0.883275330067,-0.348686188459,0.313436716795],
                        [0.961880862713,-0.266443610191,0.0615878328681],
                        [0.943842172623,-0.306287169456,0.123895764351],
                        [0.940329909325,-0.334895044565,0.0602079555392],
                        [0.960443258286,-0.199805602431,0.193975359201],
                        [0.935745954514,-0.239766731858,0.258633822203],
                        [0.942551255226,-0.274516820908,0.190361812711],
                        [0.920180141926,-0.34457308054,0.185843646526],
                        [0.891307473183,-0.380633711815,0.246351331472],
                        [0.894335091114,-0.409316182137,0.180623859167],
                        [0.942551255226,-0.274516820908,0.190361812711],
                        [0.920180141926,-0.34457308054,0.185843646526],
                        [0.943842172623,-0.306287169456,0.123895764351],
                        [0.997029185295,0.0770247355103,0.0],
                        [0.991025745869,0.117650069296,0.0634539350867],
                        [0.997179210186,0.0394601933658,0.0638479366899],
                        [0.974178731441,0.225778326392,0.0],
                        [0.961880862713,0.266443610191,0.0615878328681],
                        [0.979053080082,0.193714544177,0.0626873448491],
                        [0.978907585144,0.158833146095,0.128498718143],
                        [0.960443258286,0.199805602431,0.193975359201],
                        [0.97295331955,0.121444880962,0.196501940489],
                        [0.979053080082,0.193714544177,0.0626873448491],
                        [0.978907585144,0.158833146095,0.128498718143],
                        [0.991025745869,0.117650069296,0.0634539350867],
                        [0.932827115059,0.360324263573,0.0],
                        [0.915323853493,0.398431301117,0.0586068555713],
                        [0.940329909325,0.334895044565,0.0602079555392],
                        [0.8796184659,0.475679844618,0.0],
                        [0.858619451523,0.509656965733,0.0549761541188],
                        [0.887796461582,0.456712335348,0.0568443164229],
                        [0.892938017845,0.434652328491,0.117213711143],
                        [0.866019308567,0.468421578407,0.174905076623],
                        [0.894335091114,0.409316182137,0.180623859167],
                        [0.887796461582,0.456712335348,0.0568443164229],
                        [0.892938017845,0.434652328491,0.117213711143],
                        [0.915323853493,0.398431301117,0.0586068555713],
                        [0.935745954514,0.239766731858,0.258633822203],
                        [0.905284404755,0.277958005667,0.321246802807],
                        [0.922915279865,0.202408134937,0.327503234148],
                        [0.891307473183,0.380633711815,0.246351331472],
                        [0.857896447182,0.413926929235,0.3044308424],
                        [0.883275330067,0.348686188459,0.313436716795],
                        [0.869839549065,0.313733518124,0.380723625422],
                        [0.830415487289,0.346611320972,0.436200261116],
                        [0.85085272789,0.276221334934,0.446935534477],
                        [0.883275330067,0.348686188459,0.313436716795],
                        [0.869839549065,0.313733518124,0.380723625422],
                        [0.905284404755,0.277958005667,0.321246802807],
                        [0.940329909325,0.334895044565,0.0602079555392],
                        [0.943842172623,0.306287169456,0.123895764351],
                        [0.961880862713,0.266443610191,0.0615878328681],
                        [0.894335091114,0.409316182137,0.180623859167],
                        [0.891307473183,0.380633711815,0.246351331472],
                        [0.920180141926,0.34457308054,0.185843646526],
                        [0.942551255226,0.274516820908,0.190361812711],
                        [0.935745954514,0.239766731858,0.258633822203],
                        [0.960443258286,0.199805602431,0.193975359201],
                        [0.920180141926,0.34457308054,0.185843646526],
                        [0.942551255226,0.274516820908,0.190361812711],
                        [0.943842172623,0.306287169456,0.123895764351],
                        [0.826465010643,-0.236761152744,0.510783493519],
                        [0.797127783298,-0.196083456278,0.571085453033],
                        [0.782811582088,-0.269586592913,0.560828924179],
                        [0.847858190536,-0.0809632539749,0.524005174637],
                        [0.81225925684,-0.0399611219764,0.581926107407],
                        [0.807120084763,-0.119124859571,0.578244268894],
                        [0.763553202152,-0.154971644282,0.62687343359],
                        [0.726636230946,-0.114190116525,0.677466154099],
                        [0.718357801437,-0.188148602843,0.669747889042],
                        [0.807120084763,-0.119124859571,0.578244268894],
                        [0.763553202152,-0.154971644282,0.62687343359],
                        [0.797127783298,-0.196083456278,0.571085453033],
                        [0.847858190536,0.0809632539749,0.524005174637],
                        [0.807120084763,0.119124859571,0.578244268894],
                        [0.81225925684,0.0399611219764,0.581926107407],
                        [0.826465010643,0.236761152744,0.510783493519],
                        [0.782811582088,0.269586592913,0.560828924179],
                        [0.797127783298,0.196083456278,0.571085453033],
                        [0.763553202152,0.154971644282,0.62687343359],
                        [0.718357801437,0.188148602843,0.669747889042],
                        [0.726636230946,0.114190116525,0.677466154099],
                        [0.797127783298,0.196083456278,0.571085453033],
                        [0.763553202152,0.154971644282,0.62687343359],
                        [0.807120084763,0.119124859571,0.578244268894],
                        [0.687358558178,-0.0744211226702,0.722495436668],
                        [0.646693944931,-0.0362210273743,0.761889100075],
                        [0.643326640129,-0.108097285032,0.757922053337],
                        [0.687358558178,0.0744211226702,0.722495436668],
                        [0.643326640129,0.108097285032,0.757922053337],
                        [0.646693944931,0.0362210273743,0.761889100075],
                        [0.605532705784,0.0,0.79582041502],
                        [0.564633131027,0.0339771322906,0.82464236021],
                        [0.564633131027,-0.0339771322906,0.82464236021],
                        [0.646693944931,0.0362210273743,0.761889100075],
                        [0.605532705784,0.0,0.79582041502],
                        [0.646693944931,-0.0362210273743,0.761889100075],
                        [0.81225925684,0.0399611219764,0.581926107407],
                        [0.772890508175,0.0,0.634539365768],
                        [0.81225925684,-0.0399611219764,0.581926107407],
                        [0.726636230946,0.114190116525,0.677466154099],
                        [0.687358558178,0.0744211226702,0.722495436668],
                        [0.730884253979,0.0382858961821,0.68142670393],
                        [0.730884253979,-0.0382858961821,0.68142670393],
                        [0.687358558178,-0.0744211226702,0.722495436668],
                        [0.726636230946,-0.114190116525,0.677466154099],
                        [0.730884253979,0.0382858961821,0.68142670393],
                        [0.730884253979,-0.0382858961821,0.68142670393],
                        [0.772890508175,0.0,0.634539365768],
                        [0.997179210186,0.0394601933658,0.0638479366899],
                        [0.991494178772,0.0,0.130150929093],
                        [0.997179210186,-0.0394601933658,0.0638479366899],
                        [0.97295331955,0.121444880962,0.196501940489],
                        [0.960611641407,0.0820460245013,0.265506535769],
                        [0.979394435883,0.0407496243715,0.197802826762],
                        [0.979394435883,-0.0407496243715,0.197802826762],
                        [0.960611641407,-0.0820460245013,0.265506535769],
                        [0.97295331955,-0.121444880962,0.196501940489],
                        [0.979394435883,0.0407496243715,0.197802826762],
                        [0.979394435883,-0.0407496243715,0.197802826762],
                        [0.991494178772,0.0,0.130150929093],
                        [0.922915279865,0.202408134937,0.327503234148],
                        [0.903840482235,0.162998497486,0.395605653524],
                        [0.935258030891,0.123069040477,0.33188316226],
                        [0.85085272789,0.276221334934,0.446935534477],
                        [0.826465010643,0.236761152744,0.510783493519],
                        [0.867211103439,0.20109423995,0.455528259277],
                        [0.878655850887,0.122248865664,0.461539924145],
                        [0.847858190536,0.0809632539749,0.524005174637],
                        [0.88455080986,0.0410230122507,0.464636415243],
                        [0.867211103439,0.20109423995,0.455528259277],
                        [0.878655850887,0.122248865664,0.461539924145],
                        [0.903840482235,0.162998497486,0.395605653524],
                        [0.935258030891,-0.123069040477,0.33188316226],
                        [0.903840482235,-0.162998497486,0.395605653524],
                        [0.922915279865,-0.202408134937,0.327503234148],
                        [0.88455080986,-0.0410230122507,0.464636415243],
                        [0.847858190536,-0.0809632539749,0.524005174637],
                        [0.878655850887,-0.122248865664,0.461539924145],
                        [0.867211103439,-0.20109423995,0.455528259277],
                        [0.826465010643,-0.236761152744,0.510783493519],
                        [0.85085272789,-0.276221334934,0.446935534477],
                        [0.878655850887,-0.122248865664,0.461539924145],
                        [0.867211103439,-0.20109423995,0.455528259277],
                        [0.903840482235,-0.162998497486,0.395605653524],
                        [0.935258030891,0.123069040477,0.33188316226],
                        [0.941618084908,0.04130198434,0.334140062332],
                        [0.960611641407,0.0820460245013,0.265506535769],
                        [0.88455080986,0.0410230122507,0.464636415243],
                        [0.88455080986,-0.0410230122507,0.464636415243],
                        [0.916092038155,0.0,0.400968074799],
                        [0.941618084908,-0.04130198434,0.334140062332],
                        [0.935258030891,-0.123069040477,0.33188316226],
                        [0.960611641407,-0.0820460245013,0.265506535769],
                        [0.916092038155,0.0,0.400968074799],
                        [0.941618084908,-0.04130198434,0.334140062332],
                        [0.941618084908,0.04130198434,0.334140062332],
                        [-0.564633131027,0.0339771322906,0.82464236021],
                        [-0.605532705784,0.0,0.79582041502],
                        [-0.564633131027,-0.0339771322906,0.82464236021],
                        [-0.643326640129,0.108097285032,0.757922053337],
                        [-0.687358558178,0.0744211226702,0.722495436668],
                        [-0.646693944931,0.0362210273743,0.761889100075],
                        [-0.646693944931,-0.0362210273743,0.761889100075],
                        [-0.687358558178,-0.0744211226702,0.722495436668],
                        [-0.643326640129,-0.108097285032,0.757922053337],
                        [-0.646693944931,0.0362210273743,0.761889100075],
                        [-0.646693944931,-0.0362210273743,0.761889100075],
                        [-0.605532705784,0.0,0.79582041502],
                        [-0.718357801437,0.188148602843,0.669747889042],
                        [-0.763553202152,0.154971644282,0.62687343359],
                        [-0.726636230946,0.114190116525,0.677466154099],
                        [-0.782811582088,0.269586592913,0.560828924179],
                        [-0.826465010643,0.236761152744,0.510783493519],
                        [-0.797127783298,0.196083456278,0.571085453033],
                        [-0.807120084763,0.119124859571,0.578244268894],
                        [-0.847858190536,0.0809632539749,0.524005174637],
                        [-0.81225925684,0.0399611219764,0.581926107407],
                        [-0.797127783298,0.196083456278,0.571085453033],
                        [-0.807120084763,0.119124859571,0.578244268894],
                        [-0.763553202152,0.154971644282,0.62687343359],
                        [-0.726636230946,-0.114190116525,0.677466154099],
                        [-0.763553202152,-0.154971644282,0.62687343359],
                        [-0.718357801437,-0.188148602843,0.669747889042],
                        [-0.81225925684,-0.0399611219764,0.581926107407],
                        [-0.847858190536,-0.0809632539749,0.524005174637],
                        [-0.807120084763,-0.119124859571,0.578244268894],
                        [-0.797127783298,-0.196083456278,0.571085453033],
                        [-0.826465010643,-0.236761152744,0.510783493519],
                        [-0.782811582088,-0.269586592913,0.560828924179],
                        [-0.807120084763,-0.119124859571,0.578244268894],
                        [-0.797127783298,-0.196083456278,0.571085453033],
                        [-0.763553202152,-0.154971644282,0.62687343359],
                        [-0.726636230946,0.114190116525,0.677466154099],
                        [-0.730884253979,0.0382858961821,0.68142670393],
                        [-0.687358558178,0.0744211226702,0.722495436668],
                        [-0.81225925684,0.0399611219764,0.581926107407],
                        [-0.81225925684,-0.0399611219764,0.581926107407],
                        [-0.772890508175,0.0,0.634539365768],
                        [-0.730884253979,-0.0382858961821,0.68142670393],
                        [-0.726636230946,-0.114190116525,0.677466154099],
                        [-0.687358558178,-0.0744211226702,0.722495436668],
                        [-0.772890508175,0.0,0.634539365768],
                        [-0.730884253979,-0.0382858961821,0.68142670393],
                        [-0.730884253979,0.0382858961821,0.68142670393],
                        [-0.830415487289,0.346611320972,0.436200261116],
                        [-0.869839549065,0.313733518124,0.380723625422],
                        [-0.85085272789,0.276221334934,0.446935534477],
                        [-0.857896447182,0.413926929235,0.3044308424],
                        [-0.891307473183,0.380633711815,0.246351331472],
                        [-0.883275330067,0.348686188459,0.313436716795],
                        [-0.905284404755,0.277958005667,0.321246802807],
                        [-0.935745954514,0.239766731858,0.258633822203],
                        [-0.922915279865,0.202408134937,0.327503234148],
                        [-0.883275330067,0.348686188459,0.313436716795],
                        [-0.905284404755,0.277958005667,0.321246802807],
                        [-0.869839549065,0.313733518124,0.380723625422],
                        [-0.866019308567,0.468421578407,0.174905076623],
                        [-0.892938017845,0.434652328491,0.117213711143],
                        [-0.894335091114,0.409316182137,0.180623859167],
                        [-0.858619451523,0.509656965733,0.0549761541188],
                        [-0.8796184659,0.475679844618,0.0],
                        [-0.887796461582,0.456712335348,0.0568443164229],
                        [-0.915323853493,0.398431301117,0.0586068555713],
                        [-0.932827115059,0.360324263573,0.0],
                        [-0.940329909325,0.334895044565,0.0602079555392],
                        [-0.887796461582,0.456712335348,0.0568443164229],
                        [-0.915323853493,0.398431301117,0.0586068555713],
                        [-0.892938017845,0.434652328491,0.117213711143],
                        [-0.960443258286,0.199805602431,0.193975359201],
                        [-0.978907585144,0.158833146095,0.128498718143],
                        [-0.97295331955,0.121444880962,0.196501940489],
                        [-0.961880862713,0.266443610191,0.0615878328681],
                        [-0.974178731441,0.225778326392,0.0],
                        [-0.979053080082,0.193714544177,0.0626873448491],
                        [-0.991025745869,0.117650069296,0.0634539350867],
                        [-0.997029185295,0.0770247355103,0.0],
                        [-0.997179210186,0.0394601933658,0.0638479366899],
                        [-0.979053080082,0.193714544177,0.0626873448491],
                        [-0.991025745869,0.117650069296,0.0634539350867],
                        [-0.978907585144,0.158833146095,0.128498718143],
                        [-0.894335091114,0.409316182137,0.180623859167],
                        [-0.920180141926,0.34457308054,0.185843646526],
                        [-0.891307473183,0.380633711815,0.246351331472],
                        [-0.940329909325,0.334895044565,0.0602079555392],
                        [-0.961880862713,0.266443610191,0.0615878328681],
                        [-0.943842172623,0.306287169456,0.123895764351],
                        [-0.942551255226,0.274516820908,0.190361812711],
                        [-0.960443258286,0.199805602431,0.193975359201],
                        [-0.935745954514,0.239766731858,0.258633822203],
                        [-0.943842172623,0.306287169456,0.123895764351],
                        [-0.942551255226,0.274516820908,0.190361812711],
                        [-0.920180141926,0.34457308054,0.185843646526],
                        [-0.85085272789,-0.276221334934,0.446935534477],
                        [-0.869839549065,-0.313733518124,0.380723625422],
                        [-0.830415487289,-0.346611320972,0.436200261116],
                        [-0.922915279865,-0.202408134937,0.327503234148],
                        [-0.935745954514,-0.239766731858,0.258633822203],
                        [-0.905284404755,-0.277958005667,0.321246802807],
                        [-0.883275330067,-0.348686188459,0.313436716795],
                        [-0.891307473183,-0.380633711815,0.246351331472],
                        [-0.857896447182,-0.413926929235,0.3044308424],
                        [-0.905284404755,-0.277958005667,0.321246802807],
                        [-0.883275330067,-0.348686188459,0.313436716795],
                        [-0.869839549065,-0.313733518124,0.380723625422],
                        [-0.97295331955,-0.121444880962,0.196501940489],
                        [-0.978907585144,-0.158833146095,0.128498718143],
                        [-0.960443258286,-0.199805602431,0.193975359201],
                        [-0.997179210186,-0.0394601933658,0.0638479366899],
                        [-0.997029185295,-0.0770247355103,0.0],
                        [-0.991025745869,-0.117650069296,0.0634539350867],
                        [-0.979053080082,-0.193714544177,0.0626873448491],
                        [-0.974178731441,-0.225778326392,0.0],
                        [-0.961880862713,-0.266443610191,0.0615878328681],
                        [-0.991025745869,-0.117650069296,0.0634539350867],
                        [-0.979053080082,-0.193714544177,0.0626873448491],
                        [-0.978907585144,-0.158833146095,0.128498718143],
                        [-0.894335091114,-0.409316182137,0.180623859167],
                        [-0.892938017845,-0.434652328491,0.117213711143],
                        [-0.866019308567,-0.468421578407,0.174905076623],
                        [-0.940329909325,-0.334895044565,0.0602079555392],
                        [-0.932827115059,-0.360324263573,0.0],
                        [-0.915323853493,-0.398431301117,0.0586068555713],
                        [-0.887796461582,-0.456712335348,0.0568443164229],
                        [-0.8796184659,-0.475679844618,0.0],
                        [-0.858619451523,-0.509656965733,0.0549761541188],
                        [-0.915323853493,-0.398431301117,0.0586068555713],
                        [-0.887796461582,-0.456712335348,0.0568443164229],
                        [-0.892938017845,-0.434652328491,0.117213711143],
                        [-0.960443258286,-0.199805602431,0.193975359201],
                        [-0.942551255226,-0.274516820908,0.190361812711],
                        [-0.935745954514,-0.239766731858,0.258633822203],
                        [-0.961880862713,-0.266443610191,0.0615878328681],
                        [-0.940329909325,-0.334895044565,0.0602079555392],
                        [-0.943842172623,-0.306287169456,0.123895764351],
                        [-0.920180141926,-0.34457308054,0.185843646526],
                        [-0.894335091114,-0.409316182137,0.180623859167],
                        [-0.891307473183,-0.380633711815,0.246351331472],
                        [-0.943842172623,-0.306287169456,0.123895764351],
                        [-0.920180141926,-0.34457308054,0.185843646526],
                        [-0.942551255226,-0.274516820908,0.190361812711],
                        [-0.85085272789,0.276221334934,0.446935534477],
                        [-0.867211103439,0.20109423995,0.455528259277],
                        [-0.826465010643,0.236761152744,0.510783493519],
                        [-0.922915279865,0.202408134937,0.327503234148],
                        [-0.935258030891,0.123069040477,0.33188316226],
                        [-0.903840482235,0.162998497486,0.395605653524],
                        [-0.878655850887,0.122248865664,0.461539924145],
                        [-0.88455080986,0.0410230122507,0.464636415243],
                        [-0.847858190536,0.0809632539749,0.524005174637],
                        [-0.903840482235,0.162998497486,0.395605653524],
                        [-0.878655850887,0.122248865664,0.461539924145],
                        [-0.867211103439,0.20109423995,0.455528259277],
                        [-0.97295331955,0.121444880962,0.196501940489],
                        [-0.979394435883,0.0407496243715,0.197802826762],
                        [-0.960611641407,0.0820460245013,0.265506535769],
                        [-0.997179210186,0.0394601933658,0.0638479366899],
                        [-0.997179210186,-0.0394601933658,0.0638479366899],
                        [-0.991494178772,0.0,0.130150929093],
                        [-0.979394435883,-0.0407496243715,0.197802826762],
                        [-0.97295331955,-0.121444880962,0.196501940489],
                        [-0.960611641407,-0.0820460245013,0.265506535769],
                        [-0.991494178772,0.0,0.130150929093],
                        [-0.979394435883,-0.0407496243715,0.197802826762],
                        [-0.979394435883,0.0407496243715,0.197802826762],
                        [-0.88455080986,-0.0410230122507,0.464636415243],
                        [-0.878655850887,-0.122248865664,0.461539924145],
                        [-0.847858190536,-0.0809632539749,0.524005174637],
                        [-0.935258030891,-0.123069040477,0.33188316226],
                        [-0.922915279865,-0.202408134937,0.327503234148],
                        [-0.903840482235,-0.162998497486,0.395605653524],
                        [-0.867211103439,-0.20109423995,0.455528259277],
                        [-0.85085272789,-0.276221334934,0.446935534477],
                        [-0.826465010643,-0.236761152744,0.510783493519],
                        [-0.903840482235,-0.162998497486,0.395605653524],
                        [-0.867211103439,-0.20109423995,0.455528259277],
                        [-0.878655850887,-0.122248865664,0.461539924145],
                        [-0.960611641407,0.0820460245013,0.265506535769],
                        [-0.941618084908,0.04130198434,0.334140062332],
                        [-0.935258030891,0.123069040477,0.33188316226],
                        [-0.960611641407,-0.0820460245013,0.265506535769],
                        [-0.935258030891,-0.123069040477,0.33188316226],
                        [-0.941618084908,-0.04130198434,0.334140062332],
                        [-0.916092038155,0.0,0.400968074799],
                        [-0.88455080986,-0.0410230122507,0.464636415243],
                        [-0.88455080986,0.0410230122507,0.464636415243],
                        [-0.941618084908,-0.04130198434,0.334140062332],
                        [-0.916092038155,0.0,0.400968074799],
                        [-0.941618084908,0.04130198434,0.334140062332],
                        [-0.509656965733,0.0549761541188,0.858619451523],
                        [-0.548688352108,0.091976031661,0.830952167511],
                        [-0.564633131027,0.0339771322906,0.82464236021],
                        [-0.468421578407,0.174905076623,0.866019308567],
                        [-0.506734728813,0.217834427953,0.834127128124],
                        [-0.529480218887,0.153434738517,0.834331154823],
                        [-0.588087081909,0.131048902869,0.798110127449],
                        [-0.627150595188,0.171839639544,0.759706020355],
                        [-0.643326640129,0.108097285032,0.757922053337],
                        [-0.529480218887,0.153434738517,0.834331154823],
                        [-0.588087081909,0.131048902869,0.798110127449],
                        [-0.548688352108,0.091976031661,0.830952167511],
                        [-0.413926929235,0.3044308424,0.857896447182],
                        [-0.450116455555,0.352179646492,0.820587992668],
                        [-0.480284929276,0.284414708614,0.829719662666],
                        [-0.346611320972,0.436200261116,0.830415487289],
                        [-0.379529476166,0.486395716667,0.787004828453],
                        [-0.416404157877,0.419940322638,0.806385576725],
                        [-0.485873311758,0.400663375854,0.776785671711],
                        [-0.520354926586,0.44894811511,0.726413309574],
                        [-0.553625464439,0.378517180681,0.74177056551],
                        [-0.416404157877,0.419940322638,0.806385576725],
                        [-0.485873311758,0.400663375854,0.776785671711],
                        [-0.450116455555,0.352179646492,0.820587992668],
                        [-0.665048420429,0.213841319084,0.715529501438],
                        [-0.700865805149,0.256401896477,0.665616393089],
                        [-0.718357801437,0.188148602843,0.669747889042],
                        [-0.618283927441,0.353819847107,0.701809465885],
                        [-0.65135627985,0.398910075426,0.645450055599],
                        [-0.678621411324,0.327040165663,0.657660841942],
                        [-0.733673810959,0.298754066229,0.610302150249],
                        [-0.762617051601,0.340069264174,0.550243675709],
                        [-0.782811582088,0.269586592913,0.560828924179],
                        [-0.678621411324,0.327040165663,0.657660841942],
                        [-0.733673810959,0.298754066229,0.610302150249],
                        [-0.700865805149,0.256401896477,0.665616393089],
                        [-0.480284929276,0.284414708614,0.829719662666],
                        [-0.545040607452,0.26241543889,0.796284377575],
                        [-0.506734728813,0.217834427953,0.834127128124],
                        [-0.553625464439,0.378517180681,0.74177056551],
                        [-0.618283927441,0.353819847107,0.701809465885],
                        [-0.582528710365,0.308011889458,0.752189457417],
                        [-0.606988489628,0.238753452897,0.757998526096],
                        [-0.665048420429,0.213841319084,0.715529501438],
                        [-0.627150595188,0.171839639544,0.759706020355],
                        [-0.582528710365,0.308011889458,0.752189457417],
                        [-0.606988489628,0.238753452897,0.757998526096],
                        [-0.545040607452,0.26241543889,0.796284377575],
                        [-0.269586592913,0.560828924179,0.782811582088],
                        [-0.298754066229,0.610302150249,0.733673810959],
                        [-0.340069264174,0.550243675709,0.762617051601],
                        [-0.188148602843,0.669747889042,0.718357801437],
                        [-0.213841319084,0.715529501438,0.665048420429],
                        [-0.256401896477,0.665616393089,0.700865805149],
                        [-0.327040165663,0.657660841942,0.678621411324],
                        [-0.353819847107,0.701809465885,0.618283927441],
                        [-0.398910075426,0.645450055599,0.65135627985],
                        [-0.256401896477,0.665616393089,0.700865805149],
                        [-0.327040165663,0.657660841942,0.678621411324],
                        [-0.298754066229,0.610302150249,0.733673810959],
                        [-0.108097285032,0.757922053337,0.643326640129],
                        [-0.131048902869,0.798110127449,0.588087081909],
                        [-0.171839639544,0.759706020355,0.627150595188],
                        [-0.0339771322906,0.82464236021,0.564633131027],
                        [-0.0549761541188,0.858619451523,0.509656965733],
                        [-0.091976031661,0.830952167511,0.548688352108],
                        [-0.153434738517,0.834331154823,0.529480218887],
                        [-0.174905076623,0.866019308567,0.468421578407],
                        [-0.217834427953,0.834127128124,0.506734728813],
                        [-0.091976031661,0.830952167511,0.548688352108],
                        [-0.153434738517,0.834331154823,0.529480218887],
                        [-0.131048902869,0.798110127449,0.588087081909],
                        [-0.378517180681,0.74177056551,0.553625464439],
                        [-0.400663375854,0.776785671711,0.485873311758],
                        [-0.44894811511,0.726413309574,0.520354926586],
                        [-0.284414708614,0.829719662666,0.480284929276],
                        [-0.3044308424,0.857896447182,0.413926929235],
                        [-0.352179646492,0.820587992668,0.450116455555],
                        [-0.419940322638,0.806385576725,0.416404157877],
                        [-0.436200261116,0.830415487289,0.346611320972],
                        [-0.486395716667,0.787004828453,0.379529476166],
                        [-0.352179646492,0.820587992668,0.450116455555],
                        [-0.419940322638,0.806385576725,0.416404157877],
                        [-0.400663375854,0.776785671711,0.485873311758],
                        [-0.171839639544,0.759706020355,0.627150595188],
                        [-0.238753452897,0.757998526096,0.606988489628],
                        [-0.213841319084,0.715529501438,0.665048420429],
                        [-0.217834427953,0.834127128124,0.506734728813],
                        [-0.284414708614,0.829719662666,0.480284929276],
                        [-0.26241543889,0.796284377575,0.545040607452],
                        [-0.308011889458,0.752189457417,0.582528710365],
                        [-0.378517180681,0.74177056551,0.553625464439],
                        [-0.353819847107,0.701809465885,0.618283927441],
                        [-0.26241543889,0.796284377575,0.545040607452],
                        [-0.308011889458,0.752189457417,0.582528710365],
                        [-0.238753452897,0.757998526096,0.606988489628],
                        [-0.787004828453,0.379529476166,0.486395716667],
                        [-0.806385576725,0.416404157877,0.419940322638],
                        [-0.830415487289,0.346611320972,0.436200261116],
                        [-0.726413309574,0.520354926586,0.44894811511],
                        [-0.74177056551,0.553625464439,0.378517180681],
                        [-0.776785671711,0.485873311758,0.400663375854],
                        [-0.820587992668,0.450116455555,0.352179646492],
                        [-0.829719662666,0.480284929276,0.284414708614],
                        [-0.857896447182,0.413926929235,0.3044308424],
                        [-0.776785671711,0.485873311758,0.400663375854],
                        [-0.820587992668,0.450116455555,0.352179646492],
                        [-0.806385576725,0.416404157877,0.419940322638],
                        [-0.645450055599,0.65135627985,0.398910075426],
                        [-0.657660841942,0.678621411324,0.327040165663],
                        [-0.701809465885,0.618283927441,0.353819847107],
                        [-0.550243675709,0.762617051601,0.340069264174],
                        [-0.560828924179,0.782811582088,0.269586592913],
                        [-0.610302150249,0.733673810959,0.298754066229],
                        [-0.665616393089,0.700865805149,0.256401896477],
                        [-0.669747889042,0.718357801437,0.188148602843],
                        [-0.715529501438,0.665048420429,0.213841319084],
                        [-0.610302150249,0.733673810959,0.298754066229],
                        [-0.665616393089,0.700865805149,0.256401896477],
                        [-0.657660841942,0.678621411324,0.327040165663],
                        [-0.834127128124,0.506734728813,0.217834427953],
                        [-0.834331154823,0.529480218887,0.153434738517],
                        [-0.866019308567,0.468421578407,0.174905076623],
                        [-0.759706020355,0.627150595188,0.171839639544],
                        [-0.757922053337,0.643326640129,0.108097285032],
                        [-0.798110127449,0.588087081909,0.131048902869],
                        [-0.830952167511,0.548688352108,0.091976031661],
                        [-0.82464236021,0.564633131027,0.0339771322906],
                        [-0.858619451523,0.509656965733,0.0549761541188],
                        [-0.798110127449,0.588087081909,0.131048902869],
                        [-0.830952167511,0.548688352108,0.091976031661],
                        [-0.834331154823,0.529480218887,0.153434738517],
                        [-0.701809465885,0.618283927441,0.353819847107],
                        [-0.752189457417,0.582528710365,0.308011889458],
                        [-0.74177056551,0.553625464439,0.378517180681],
                        [-0.715529501438,0.665048420429,0.213841319084],
                        [-0.759706020355,0.627150595188,0.171839639544],
                        [-0.757998526096,0.606988489628,0.238753452897],
                        [-0.796284377575,0.545040607452,0.26241543889],
                        [-0.834127128124,0.506734728813,0.217834427953],
                        [-0.829719662666,0.480284929276,0.284414708614],
                        [-0.757998526096,0.606988489628,0.238753452897],
                        [-0.796284377575,0.545040607452,0.26241543889],
                        [-0.752189457417,0.582528710365,0.308011889458],
                        [-0.340069264174,0.550243675709,0.762617051601],
                        [-0.411682873964,0.535965919495,0.737060189247],
                        [-0.379529476166,0.486395716667,0.787004828453],
                        [-0.398910075426,0.645450055599,0.65135627985],
                        [-0.470621615648,0.628728508949,0.619044244289],
                        [-0.44230055809,0.58378881216,0.680853009224],
                        [-0.483050197363,0.517854511738,0.706037700176],
                        [-0.552667617798,0.495975226164,0.669751524925],
                        [-0.520354926586,0.44894811511,0.726413309574],
                        [-0.44230055809,0.58378881216,0.680853009224],
                        [-0.483050197363,0.517854511738,0.706037700176],
                        [-0.411682873964,0.535965919495,0.737060189247],
                        [-0.44894811511,0.726413309574,0.520354926586],
                        [-0.517854511738,0.706037700176,0.483050197363],
                        [-0.495975226164,0.669751524925,0.552667617798],
                        [-0.486395716667,0.787004828453,0.379529476166],
                        [-0.550243675709,0.762617051601,0.340069264174],
                        [-0.535965919495,0.737060189247,0.411682873964],
                        [-0.58378881216,0.680853009224,0.44230055809],
                        [-0.645450055599,0.65135627985,0.398910075426],
                        [-0.628728508949,0.619044244289,0.470621615648],
                        [-0.535965919495,0.737060189247,0.411682873964],
                        [-0.58378881216,0.680853009224,0.44230055809],
                        [-0.517854511738,0.706037700176,0.483050197363],
                        [-0.619044244289,0.470621615648,0.628728508949],
                        [-0.680853009224,0.44230055809,0.58378881216],
                        [-0.65135627985,0.398910075426,0.645450055599],
                        [-0.669751524925,0.552667617798,0.495975226164],
                        [-0.726413309574,0.520354926586,0.44894811511],
                        [-0.706037700176,0.483050197363,0.517854511738],
                        [-0.737060189247,0.411682873964,0.535965919495],
                        [-0.787004828453,0.379529476166,0.486395716667],
                        [-0.762617051601,0.340069264174,0.550243675709],
                        [-0.706037700176,0.483050197363,0.517854511738],
                        [-0.737060189247,0.411682873964,0.535965919495],
                        [-0.680853009224,0.44230055809,0.58378881216],
                        [-0.495975226164,0.669751524925,0.552667617798],
                        [-0.540649950504,0.607478022575,0.581951975822],
                        [-0.470621615648,0.628728508949,0.619044244289],
                        [-0.628728508949,0.619044244289,0.470621615648],
                        [-0.669751524925,0.552667617798,0.495975226164],
                        [-0.607478022575,0.581951975822,0.540649950504],
                        [-0.581951975822,0.540649950504,0.607478022575],
                        [-0.619044244289,0.470621615648,0.628728508949],
                        [-0.552667617798,0.495975226164,0.669751524925],
                        [-0.607478022575,0.581951975822,0.540649950504],
                        [-0.581951975822,0.540649950504,0.607478022575],
                        [-0.540649950504,0.607478022575,0.581951975822],
                        [-0.0339771322906,0.82464236021,0.564633131027],
                        [0.0,0.79582041502,0.605532705784],
                        [0.0339771322906,0.82464236021,0.564633131027],
                        [-0.108097285032,0.757922053337,0.643326640129],
                        [-0.0744211226702,0.722495436668,0.687358558178],
                        [-0.0362210273743,0.761889100075,0.646693944931],
                        [0.0362210273743,0.761889100075,0.646693944931],
                        [0.0744211226702,0.722495436668,0.687358558178],
                        [0.108097285032,0.757922053337,0.643326640129],
                        [-0.0362210273743,0.761889100075,0.646693944931],
                        [0.0362210273743,0.761889100075,0.646693944931],
                        [0.0,0.79582041502,0.605532705784],
                        [-0.188148602843,0.669747889042,0.718357801437],
                        [-0.154971644282,0.62687343359,0.763553202152],
                        [-0.114190116525,0.677466154099,0.726636230946],
                        [-0.269586592913,0.560828924179,0.782811582088],
                        [-0.236761152744,0.510783493519,0.826465010643],
                        [-0.196083456278,0.571085453033,0.797127783298],
                        [-0.119124859571,0.578244268894,0.807120084763],
                        [-0.0809632539749,0.524005174637,0.847858190536],
                        [-0.0399611219764,0.581926107407,0.81225925684],
                        [-0.196083456278,0.571085453033,0.797127783298],
                        [-0.119124859571,0.578244268894,0.807120084763],
                        [-0.154971644282,0.62687343359,0.763553202152],
                        [0.114190116525,0.677466154099,0.726636230946],
                        [0.154971644282,0.62687343359,0.763553202152],
                        [0.188148602843,0.669747889042,0.718357801437],
                        [0.0399611219764,0.581926107407,0.81225925684],
                        [0.0809632539749,0.524005174637,0.847858190536],
                        [0.119124859571,0.578244268894,0.807120084763],
                        [0.196083456278,0.571085453033,0.797127783298],
                        [0.236761152744,0.510783493519,0.826465010643],
                        [0.269586592913,0.560828924179,0.782811582088],
                        [0.119124859571,0.578244268894,0.807120084763],
                        [0.196083456278,0.571085453033,0.797127783298],
                        [0.154971644282,0.62687343359,0.763553202152],
                        [-0.114190116525,0.677466154099,0.726636230946],
                        [-0.0382858961821,0.68142670393,0.730884253979],
                        [-0.0744211226702,0.722495436668,0.687358558178],
                        [-0.0399611219764,0.581926107407,0.81225925684],
                        [0.0399611219764,0.581926107407,0.81225925684],
                        [0.0,0.634539365768,0.772890508175],
                        [0.0382858961821,0.68142670393,0.730884253979],
                        [0.114190116525,0.677466154099,0.726636230946],
                        [0.0744211226702,0.722495436668,0.687358558178],
                        [0.0,0.634539365768,0.772890508175],
                        [0.0382858961821,0.68142670393,0.730884253979],
                        [-0.0382858961821,0.68142670393,0.730884253979],
                        [-0.346611320972,0.436200261116,0.830415487289],
                        [-0.313733518124,0.380723625422,0.869839549065],
                        [-0.276221334934,0.446935534477,0.85085272789],
                        [-0.413926929235,0.3044308424,0.857896447182],
                        [-0.380633711815,0.246351331472,0.891307473183],
                        [-0.348686188459,0.313436716795,0.883275330067],
                        [-0.277958005667,0.321246802807,0.905284404755],
                        [-0.239766731858,0.258633822203,0.935745954514],
                        [-0.202408134937,0.327503234148,0.922915279865],
                        [-0.348686188459,0.313436716795,0.883275330067],
                        [-0.277958005667,0.321246802807,0.905284404755],
                        [-0.313733518124,0.380723625422,0.869839549065],
                        [-0.468421578407,0.174905076623,0.866019308567],
                        [-0.434652328491,0.117213711143,0.892938017845],
                        [-0.409316182137,0.180623859167,0.894335091114],
                        [-0.509656965733,0.0549761541188,0.858619451523],
                        [-0.475679844618,0.0,0.8796184659],
                        [-0.456712335348,0.0568443164229,0.887796461582],
                        [-0.398431301117,0.0586068555713,0.915323853493],
                        [-0.360324263573,0.0,0.932827115059],
                        [-0.334895044565,0.0602079555392,0.940329909325],
                        [-0.456712335348,0.0568443164229,0.887796461582],
                        [-0.398431301117,0.0586068555713,0.915323853493],
                        [-0.434652328491,0.117213711143,0.892938017845],
                        [-0.199805602431,0.193975359201,0.960443258286],
                        [-0.158833146095,0.128498718143,0.978907585144],
                        [-0.121444880962,0.196501940489,0.97295331955],
                        [-0.266443610191,0.0615878328681,0.961880862713],
                        [-0.225778326392,0.0,0.974178731441],
                        [-0.193714544177,0.0626873448491,0.979053080082],
                        [-0.117650069296,0.0634539350867,0.991025745869],
                        [-0.0770247355103,0.0,0.997029185295],
                        [-0.0394601933658,0.0638479366899,0.997179210186],
                        [-0.193714544177,0.0626873448491,0.979053080082],
                        [-0.117650069296,0.0634539350867,0.991025745869],
                        [-0.158833146095,0.128498718143,0.978907585144],
                        [-0.409316182137,0.180623859167,0.894335091114],
                        [-0.34457308054,0.185843646526,0.920180141926],
                        [-0.380633711815,0.246351331472,0.891307473183],
                        [-0.334895044565,0.0602079555392,0.940329909325],
                        [-0.266443610191,0.0615878328681,0.961880862713],
                        [-0.306287169456,0.123895764351,0.943842172623],
                        [-0.274516820908,0.190361812711,0.942551255226],
                        [-0.199805602431,0.193975359201,0.960443258286],
                        [-0.239766731858,0.258633822203,0.935745954514],
                        [-0.306287169456,0.123895764351,0.943842172623],
                        [-0.274516820908,0.190361812711,0.942551255226],
                        [-0.34457308054,0.185843646526,0.920180141926],
                        [0.276221334934,0.446935534477,0.85085272789],
                        [0.313733518124,0.380723625422,0.869839549065],
                        [0.346611320972,0.436200261116,0.830415487289],
                        [0.202408134937,0.327503234148,0.922915279865],
                        [0.239766731858,0.258633822203,0.935745954514],
                        [0.277958005667,0.321246802807,0.905284404755],
                        [0.348686188459,0.313436716795,0.883275330067],
                        [0.380633711815,0.246351331472,0.891307473183],
                        [0.413926929235,0.3044308424,0.857896447182],
                        [0.277958005667,0.321246802807,0.905284404755],
                        [0.348686188459,0.313436716795,0.883275330067],
                        [0.313733518124,0.380723625422,0.869839549065],
                        [0.121444880962,0.196501940489,0.97295331955],
                        [0.158833146095,0.128498718143,0.978907585144],
                        [0.199805602431,0.193975359201,0.960443258286],
                        [0.0394601933658,0.0638479366899,0.997179210186],
                        [0.0770247355103,0.0,0.997029185295],
                        [0.117650069296,0.0634539350867,0.991025745869],
                        [0.193714544177,0.0626873448491,0.979053080082],
                        [0.225778326392,0.0,0.974178731441],
                        [0.266443610191,0.0615878328681,0.961880862713],
                        [0.117650069296,0.0634539350867,0.991025745869],
                        [0.193714544177,0.0626873448491,0.979053080082],
                        [0.158833146095,0.128498718143,0.978907585144],
                        [0.409316182137,0.180623859167,0.894335091114],
                        [0.434652328491,0.117213711143,0.892938017845],
                        [0.468421578407,0.174905076623,0.866019308567],
                        [0.334895044565,0.0602079555392,0.940329909325],
                        [0.360324263573,0.0,0.932827115059],
                        [0.398431301117,0.0586068555713,0.915323853493],
                        [0.456712335348,0.0568443164229,0.887796461582],
                        [0.475679844618,0.0,0.8796184659],
                        [0.509656965733,0.0549761541188,0.858619451523],
                        [0.398431301117,0.0586068555713,0.915323853493],
                        [0.456712335348,0.0568443164229,0.887796461582],
                        [0.434652328491,0.117213711143,0.892938017845],
                        [0.199805602431,0.193975359201,0.960443258286],
                        [0.274516820908,0.190361812711,0.942551255226],
                        [0.239766731858,0.258633822203,0.935745954514],
                        [0.266443610191,0.0615878328681,0.961880862713],
                        [0.334895044565,0.0602079555392,0.940329909325],
                        [0.306287169456,0.123895764351,0.943842172623],
                        [0.34457308054,0.185843646526,0.920180141926],
                        [0.409316182137,0.180623859167,0.894335091114],
                        [0.380633711815,0.246351331472,0.891307473183],
                        [0.306287169456,0.123895764351,0.943842172623],
                        [0.34457308054,0.185843646526,0.920180141926],
                        [0.274516820908,0.190361812711,0.942551255226],
                        [-0.276221334934,0.446935534477,0.85085272789],
                        [-0.20109423995,0.455528259277,0.867211103439],
                        [-0.236761152744,0.510783493519,0.826465010643],
                        [-0.202408134937,0.327503234148,0.922915279865],
                        [-0.123069040477,0.33188316226,0.935258030891],
                        [-0.162998497486,0.395605653524,0.903840482235],
                        [-0.122248865664,0.461539924145,0.878655850887],
                        [-0.0410230122507,0.464636415243,0.88455080986],
                        [-0.0809632539749,0.524005174637,0.847858190536],
                        [-0.162998497486,0.395605653524,0.903840482235],
                        [-0.122248865664,0.461539924145,0.878655850887],
                        [-0.20109423995,0.455528259277,0.867211103439],
                        [-0.121444880962,0.196501940489,0.97295331955],
                        [-0.0407496243715,0.197802826762,0.979394435883],
                        [-0.0820460245013,0.265506535769,0.960611641407],
                        [-0.0394601933658,0.0638479366899,0.997179210186],
                        [0.0394601933658,0.0638479366899,0.997179210186],
                        [0.0,0.130150929093,0.991494178772],
                        [0.0407496243715,0.197802826762,0.979394435883],
                        [0.121444880962,0.196501940489,0.97295331955],
                        [0.0820460245013,0.265506535769,0.960611641407],
                        [0.0,0.130150929093,0.991494178772],
                        [0.0407496243715,0.197802826762,0.979394435883],
                        [-0.0407496243715,0.197802826762,0.979394435883],
                        [0.0410230122507,0.464636415243,0.88455080986],
                        [0.122248865664,0.461539924145,0.878655850887],
                        [0.0809632539749,0.524005174637,0.847858190536],
                        [0.123069040477,0.33188316226,0.935258030891],
                        [0.202408134937,0.327503234148,0.922915279865],
                        [0.162998497486,0.395605653524,0.903840482235],
                        [0.20109423995,0.455528259277,0.867211103439],
                        [0.276221334934,0.446935534477,0.85085272789],
                        [0.236761152744,0.510783493519,0.826465010643],
                        [0.162998497486,0.395605653524,0.903840482235],
                        [0.20109423995,0.455528259277,0.867211103439],
                        [0.122248865664,0.461539924145,0.878655850887],
                        [-0.0820460245013,0.265506535769,0.960611641407],
                        [-0.04130198434,0.334140062332,0.941618084908],
                        [-0.123069040477,0.33188316226,0.935258030891],
                        [0.0820460245013,0.265506535769,0.960611641407],
                        [0.123069040477,0.33188316226,0.935258030891],
                        [0.04130198434,0.334140062332,0.941618084908],
                        [0.0,0.400968074799,0.916092038155],
                        [0.0410230122507,0.464636415243,0.88455080986],
                        [-0.0410230122507,0.464636415243,0.88455080986],
                        [0.04130198434,0.334140062332,0.941618084908],
                        [0.0,0.400968074799,0.916092038155],
                        [-0.04130198434,0.334140062332,0.941618084908],
                        [-0.0549761541188,0.858619451523,-0.509656965733],
                        [-0.0568443164229,0.887796461582,-0.456712335348],
                        [0.0,0.8796184659,-0.475679844618],
                        [-0.174905076623,0.866019308567,-0.468421578407],
                        [-0.180623859167,0.894335091114,-0.409316182137],
                        [-0.117213711143,0.892938017845,-0.434652328491],
                        [-0.0586068555713,0.915323853493,-0.398431301117],
                        [-0.0602079555392,0.940329909325,-0.334895044565],
                        [0.0,0.932827115059,-0.360324263573],
                        [-0.117213711143,0.892938017845,-0.434652328491],
                        [-0.0586068555713,0.915323853493,-0.398431301117],
                        [-0.0568443164229,0.887796461582,-0.456712335348],
                        [-0.3044308424,0.857896447182,-0.413926929235],
                        [-0.313436716795,0.883275330067,-0.348686188459],
                        [-0.246351331472,0.891307473183,-0.380633711815],
                        [-0.436200261116,0.830415487289,-0.346611320972],
                        [-0.446935534477,0.85085272789,-0.276221334934],
                        [-0.380723625422,0.869839549065,-0.313733518124],
                        [-0.321246802807,0.905284404755,-0.277958005667],
                        [-0.327503234148,0.922915279865,-0.202408134937],
                        [-0.258633822203,0.935745954514,-0.239766731858],
                        [-0.380723625422,0.869839549065,-0.313733518124],
                        [-0.321246802807,0.905284404755,-0.277958005667],
                        [-0.313436716795,0.883275330067,-0.348686188459],
                        [-0.0615878328681,0.961880862713,-0.266443610191],
                        [-0.0626873448491,0.979053080082,-0.193714544177],
                        [0.0,0.974178731441,-0.225778326392],
                        [-0.193975359201,0.960443258286,-0.199805602431],
                        [-0.196501940489,0.97295331955,-0.121444880962],
                        [-0.128498718143,0.978907585144,-0.158833146095],
                        [-0.0634539350867,0.991025745869,-0.117650069296],
                        [-0.0638479366899,0.997179210186,-0.0394601933658],
                        [0.0,0.997029185295,-0.0770247355103],
                        [-0.128498718143,0.978907585144,-0.158833146095],
                        [-0.0634539350867,0.991025745869,-0.117650069296],
                        [-0.0626873448491,0.979053080082,-0.193714544177],
                        [-0.246351331472,0.891307473183,-0.380633711815],
                        [-0.185843646526,0.920180141926,-0.34457308054],
                        [-0.180623859167,0.894335091114,-0.409316182137],
                        [-0.258633822203,0.935745954514,-0.239766731858],
                        [-0.193975359201,0.960443258286,-0.199805602431],
                        [-0.190361812711,0.942551255226,-0.274516820908],
                        [-0.123895764351,0.943842172623,-0.306287169456],
                        [-0.0615878328681,0.961880862713,-0.266443610191],
                        [-0.0602079555392,0.940329909325,-0.334895044565],
                        [-0.190361812711,0.942551255226,-0.274516820908],
                        [-0.123895764351,0.943842172623,-0.306287169456],
                        [-0.185843646526,0.920180141926,-0.34457308054],
                        [-0.560828924179,0.782811582088,-0.269586592913],
                        [-0.571085453033,0.797127783298,-0.196083456278],
                        [-0.510783493519,0.826465010643,-0.236761152744],
                        [-0.669747889042,0.718357801437,-0.188148602843],
                        [-0.677466154099,0.726636230946,-0.114190116525],
                        [-0.62687343359,0.763553202152,-0.154971644282],
                        [-0.578244268894,0.807120084763,-0.119124859571],
                        [-0.581926107407,0.81225925684,-0.0399611219764],
                        [-0.524005174637,0.847858190536,-0.0809632539749],
                        [-0.62687343359,0.763553202152,-0.154971644282],
                        [-0.578244268894,0.807120084763,-0.119124859571],
                        [-0.571085453033,0.797127783298,-0.196083456278],
                        [-0.757922053337,0.643326640129,-0.108097285032],
                        [-0.761889100075,0.646693944931,-0.0362210273743],
                        [-0.722495436668,0.687358558178,-0.0744211226702],
                        [-0.82464236021,0.564633131027,-0.0339771322906],
                        [-0.82464236021,0.564633131027,0.0339771322906],
                        [-0.79582041502,0.605532705784,0.0],
                        [-0.761889100075,0.646693944931,0.0362210273743],
                        [-0.757922053337,0.643326640129,0.108097285032],
                        [-0.722495436668,0.687358558178,0.0744211226702],
                        [-0.79582041502,0.605532705784,0.0],
                        [-0.761889100075,0.646693944931,0.0362210273743],
                        [-0.761889100075,0.646693944931,-0.0362210273743],
                        [-0.581926107407,0.81225925684,0.0399611219764],
                        [-0.578244268894,0.807120084763,0.119124859571],
                        [-0.524005174637,0.847858190536,0.0809632539749],
                        [-0.677466154099,0.726636230946,0.114190116525],
                        [-0.669747889042,0.718357801437,0.188148602843],
                        [-0.62687343359,0.763553202152,0.154971644282],
                        [-0.571085453033,0.797127783298,0.196083456278],
                        [-0.560828924179,0.782811582088,0.269586592913],
                        [-0.510783493519,0.826465010643,0.236761152744],
                        [-0.62687343359,0.763553202152,0.154971644282],
                        [-0.571085453033,0.797127783298,0.196083456278],
                        [-0.578244268894,0.807120084763,0.119124859571],
                        [-0.722495436668,0.687358558178,-0.0744211226702],
                        [-0.68142670393,0.730884253979,-0.0382858961821],
                        [-0.677466154099,0.726636230946,-0.114190116525],
                        [-0.722495436668,0.687358558178,0.0744211226702],
                        [-0.677466154099,0.726636230946,0.114190116525],
                        [-0.68142670393,0.730884253979,0.0382858961821],
                        [-0.634539365768,0.772890508175,0.0],
                        [-0.581926107407,0.81225925684,0.0399611219764],
                        [-0.581926107407,0.81225925684,-0.0399611219764],
                        [-0.68142670393,0.730884253979,0.0382858961821],
                        [-0.634539365768,0.772890508175,0.0],
                        [-0.68142670393,0.730884253979,-0.0382858961821],
                        [-0.0638479366899,0.997179210186,0.0394601933658],
                        [-0.0634539350867,0.991025745869,0.117650069296],
                        [0.0,0.997029185295,0.0770247355103],
                        [-0.196501940489,0.97295331955,0.121444880962],
                        [-0.193975359201,0.960443258286,0.199805602431],
                        [-0.128498718143,0.978907585144,0.158833146095],
                        [-0.0626873448491,0.979053080082,0.193714544177],
                        [-0.0615878328681,0.961880862713,0.266443610191],
                        [0.0,0.974178731441,0.225778326392],
                        [-0.128498718143,0.978907585144,0.158833146095],
                        [-0.0626873448491,0.979053080082,0.193714544177],
                        [-0.0634539350867,0.991025745869,0.117650069296],
                        [-0.327503234148,0.922915279865,0.202408134937],
                        [-0.321246802807,0.905284404755,0.277958005667],
                        [-0.258633822203,0.935745954514,0.239766731858],
                        [-0.446935534477,0.85085272789,0.276221334934],
                        [-0.436200261116,0.830415487289,0.346611320972],
                        [-0.380723625422,0.869839549065,0.313733518124],
                        [-0.313436716795,0.883275330067,0.348686188459],
                        [-0.3044308424,0.857896447182,0.413926929235],
                        [-0.246351331472,0.891307473183,0.380633711815],
                        [-0.380723625422,0.869839549065,0.313733518124],
                        [-0.313436716795,0.883275330067,0.348686188459],
                        [-0.321246802807,0.905284404755,0.277958005667],
                        [-0.0602079555392,0.940329909325,0.334895044565],
                        [-0.0586068555713,0.915323853493,0.398431301117],
                        [0.0,0.932827115059,0.360324263573],
                        [-0.180623859167,0.894335091114,0.409316182137],
                        [-0.174905076623,0.866019308567,0.468421578407],
                        [-0.117213711143,0.892938017845,0.434652328491],
                        [-0.0568443164229,0.887796461582,0.456712335348],
                        [-0.0549761541188,0.858619451523,0.509656965733],
                        [0.0,0.8796184659,0.475679844618],
                        [-0.117213711143,0.892938017845,0.434652328491],
                        [-0.0568443164229,0.887796461582,0.456712335348],
                        [-0.0586068555713,0.915323853493,0.398431301117],
                        [-0.258633822203,0.935745954514,0.239766731858],
                        [-0.190361812711,0.942551255226,0.274516820908],
                        [-0.193975359201,0.960443258286,0.199805602431],
                        [-0.246351331472,0.891307473183,0.380633711815],
                        [-0.180623859167,0.894335091114,0.409316182137],
                        [-0.185843646526,0.920180141926,0.34457308054],
                        [-0.123895764351,0.943842172623,0.306287169456],
                        [-0.0602079555392,0.940329909325,0.334895044565],
                        [-0.0615878328681,0.961880862713,0.266443610191],
                        [-0.185843646526,0.920180141926,0.34457308054],
                        [-0.123895764351,0.943842172623,0.306287169456],
                        [-0.190361812711,0.942551255226,0.274516820908],
                        [-0.510783493519,0.826465010643,-0.236761152744],
                        [-0.455528259277,0.867211103439,-0.20109423995],
                        [-0.446935534477,0.85085272789,-0.276221334934],
                        [-0.524005174637,0.847858190536,-0.0809632539749],
                        [-0.464636415243,0.88455080986,-0.0410230122507],
                        [-0.461539924145,0.878655850887,-0.122248865664],
                        [-0.395605653524,0.903840482235,-0.162998497486],
                        [-0.33188316226,0.935258030891,-0.123069040477],
                        [-0.327503234148,0.922915279865,-0.202408134937],
                        [-0.461539924145,0.878655850887,-0.122248865664],
                        [-0.395605653524,0.903840482235,-0.162998497486],
                        [-0.455528259277,0.867211103439,-0.20109423995],
                        [-0.524005174637,0.847858190536,0.0809632539749],
                        [-0.461539924145,0.878655850887,0.122248865664],
                        [-0.464636415243,0.88455080986,0.0410230122507],
                        [-0.510783493519,0.826465010643,0.236761152744],
                        [-0.446935534477,0.85085272789,0.276221334934],
                        [-0.455528259277,0.867211103439,0.20109423995],
                        [-0.395605653524,0.903840482235,0.162998497486],
                        [-0.327503234148,0.922915279865,0.202408134937],
                        [-0.33188316226,0.935258030891,0.123069040477],
                        [-0.455528259277,0.867211103439,0.20109423995],
                        [-0.395605653524,0.903840482235,0.162998497486],
                        [-0.461539924145,0.878655850887,0.122248865664],
                        [-0.265506535769,0.960611641407,-0.0820460245013],
                        [-0.197802826762,0.979394435883,-0.0407496243715],
                        [-0.196501940489,0.97295331955,-0.121444880962],
                        [-0.265506535769,0.960611641407,0.0820460245013],
                        [-0.196501940489,0.97295331955,0.121444880962],
                        [-0.197802826762,0.979394435883,0.0407496243715],
                        [-0.130150929093,0.991494178772,0.0],
                        [-0.0638479366899,0.997179210186,0.0394601933658],
                        [-0.0638479366899,0.997179210186,-0.0394601933658],
                        [-0.197802826762,0.979394435883,0.0407496243715],
                        [-0.130150929093,0.991494178772,0.0],
                        [-0.197802826762,0.979394435883,-0.0407496243715],
                        [-0.464636415243,0.88455080986,0.0410230122507],
                        [-0.400968074799,0.916092038155,0.0],
                        [-0.464636415243,0.88455080986,-0.0410230122507],
                        [-0.33188316226,0.935258030891,0.123069040477],
                        [-0.265506535769,0.960611641407,0.0820460245013],
                        [-0.334140062332,0.941618084908,0.04130198434],
                        [-0.334140062332,0.941618084908,-0.04130198434],
                        [-0.265506535769,0.960611641407,-0.0820460245013],
                        [-0.33188316226,0.935258030891,-0.123069040477],
                        [-0.334140062332,0.941618084908,0.04130198434],
                        [-0.334140062332,0.941618084908,-0.04130198434],
                        [-0.400968074799,0.916092038155,0.0],
                        [0.564633131027,0.0339771322906,-0.82464236021],
                        [0.605532705784,0.0,-0.79582041502],
                        [0.564633131027,-0.0339771322906,-0.82464236021],
                        [0.643326640129,0.108097285032,-0.757922053337],
                        [0.687358558178,0.0744211226702,-0.722495436668],
                        [0.646693944931,0.0362210273743,-0.761889100075],
                        [0.646693944931,-0.0362210273743,-0.761889100075],
                        [0.687358558178,-0.0744211226702,-0.722495436668],
                        [0.643326640129,-0.108097285032,-0.757922053337],
                        [0.646693944931,0.0362210273743,-0.761889100075],
                        [0.646693944931,-0.0362210273743,-0.761889100075],
                        [0.605532705784,0.0,-0.79582041502],
                        [0.718357801437,0.188148602843,-0.669747889042],
                        [0.763553202152,0.154971644282,-0.62687343359],
                        [0.726636230946,0.114190116525,-0.677466154099],
                        [0.782811582088,0.269586592913,-0.560828924179],
                        [0.826465010643,0.236761152744,-0.510783493519],
                        [0.797127783298,0.196083456278,-0.571085453033],
                        [0.807120084763,0.119124859571,-0.578244268894],
                        [0.847858190536,0.0809632539749,-0.524005174637],
                        [0.81225925684,0.0399611219764,-0.581926107407],
                        [0.797127783298,0.196083456278,-0.571085453033],
                        [0.807120084763,0.119124859571,-0.578244268894],
                        [0.763553202152,0.154971644282,-0.62687343359],
                        [0.726636230946,-0.114190116525,-0.677466154099],
                        [0.763553202152,-0.154971644282,-0.62687343359],
                        [0.718357801437,-0.188148602843,-0.669747889042],
                        [0.81225925684,-0.0399611219764,-0.581926107407],
                        [0.847858190536,-0.0809632539749,-0.524005174637],
                        [0.807120084763,-0.119124859571,-0.578244268894],
                        [0.797127783298,-0.196083456278,-0.571085453033],
                        [0.826465010643,-0.236761152744,-0.510783493519],
                        [0.782811582088,-0.269586592913,-0.560828924179],
                        [0.807120084763,-0.119124859571,-0.578244268894],
                        [0.797127783298,-0.196083456278,-0.571085453033],
                        [0.763553202152,-0.154971644282,-0.62687343359],
                        [0.726636230946,0.114190116525,-0.677466154099],
                        [0.730884253979,0.0382858961821,-0.68142670393],
                        [0.687358558178,0.0744211226702,-0.722495436668],
                        [0.81225925684,0.0399611219764,-0.581926107407],
                        [0.81225925684,-0.0399611219764,-0.581926107407],
                        [0.772890508175,0.0,-0.634539365768],
                        [0.730884253979,-0.0382858961821,-0.68142670393],
                        [0.726636230946,-0.114190116525,-0.677466154099],
                        [0.687358558178,-0.0744211226702,-0.722495436668],
                        [0.772890508175,0.0,-0.634539365768],
                        [0.730884253979,-0.0382858961821,-0.68142670393],
                        [0.730884253979,0.0382858961821,-0.68142670393],
                        [0.830415487289,0.346611320972,-0.436200261116],
                        [0.869839549065,0.313733518124,-0.380723625422],
                        [0.85085272789,0.276221334934,-0.446935534477],
                        [0.857896447182,0.413926929235,-0.3044308424],
                        [0.891307473183,0.380633711815,-0.246351331472],
                        [0.883275330067,0.348686188459,-0.313436716795],
                        [0.905284404755,0.277958005667,-0.321246802807],
                        [0.935745954514,0.239766731858,-0.258633822203],
                        [0.922915279865,0.202408134937,-0.327503234148],
                        [0.883275330067,0.348686188459,-0.313436716795],
                        [0.905284404755,0.277958005667,-0.321246802807],
                        [0.869839549065,0.313733518124,-0.380723625422],
                        [0.866019308567,0.468421578407,-0.174905076623],
                        [0.892938017845,0.434652328491,-0.117213711143],
                        [0.894335091114,0.409316182137,-0.180623859167],
                        [0.858619451523,0.509656965733,-0.0549761541188],
                        [0.8796184659,0.475679844618,0.0],
                        [0.887796461582,0.456712335348,-0.0568443164229],
                        [0.915323853493,0.398431301117,-0.0586068555713],
                        [0.932827115059,0.360324263573,0.0],
                        [0.940329909325,0.334895044565,-0.0602079555392],
                        [0.887796461582,0.456712335348,-0.0568443164229],
                        [0.915323853493,0.398431301117,-0.0586068555713],
                        [0.892938017845,0.434652328491,-0.117213711143],
                        [0.960443258286,0.199805602431,-0.193975359201],
                        [0.978907585144,0.158833146095,-0.128498718143],
                        [0.97295331955,0.121444880962,-0.196501940489],
                        [0.961880862713,0.266443610191,-0.0615878328681],
                        [0.974178731441,0.225778326392,0.0],
                        [0.979053080082,0.193714544177,-0.0626873448491],
                        [0.991025745869,0.117650069296,-0.0634539350867],
                        [0.997029185295,0.0770247355103,0.0],
                        [0.997179210186,0.0394601933658,-0.0638479366899],
                        [0.979053080082,0.193714544177,-0.0626873448491],
                        [0.991025745869,0.117650069296,-0.0634539350867],
                        [0.978907585144,0.158833146095,-0.128498718143],
                        [0.894335091114,0.409316182137,-0.180623859167],
                        [0.920180141926,0.34457308054,-0.185843646526],
                        [0.891307473183,0.380633711815,-0.246351331472],
                        [0.940329909325,0.334895044565,-0.0602079555392],
                        [0.961880862713,0.266443610191,-0.0615878328681],
                        [0.943842172623,0.306287169456,-0.123895764351],
                        [0.942551255226,0.274516820908,-0.190361812711],
                        [0.960443258286,0.199805602431,-0.193975359201],
                        [0.935745954514,0.239766731858,-0.258633822203],
                        [0.943842172623,0.306287169456,-0.123895764351],
                        [0.942551255226,0.274516820908,-0.190361812711],
                        [0.920180141926,0.34457308054,-0.185843646526],
                        [0.85085272789,-0.276221334934,-0.446935534477],
                        [0.869839549065,-0.313733518124,-0.380723625422],
                        [0.830415487289,-0.346611320972,-0.436200261116],
                        [0.922915279865,-0.202408134937,-0.327503234148],
                        [0.935745954514,-0.239766731858,-0.258633822203],
                        [0.905284404755,-0.277958005667,-0.321246802807],
                        [0.883275330067,-0.348686188459,-0.313436716795],
                        [0.891307473183,-0.380633711815,-0.246351331472],
                        [0.857896447182,-0.413926929235,-0.3044308424],
                        [0.905284404755,-0.277958005667,-0.321246802807],
                        [0.883275330067,-0.348686188459,-0.313436716795],
                        [0.869839549065,-0.313733518124,-0.380723625422],
                        [0.97295331955,-0.121444880962,-0.196501940489],
                        [0.978907585144,-0.158833146095,-0.128498718143],
                        [0.960443258286,-0.199805602431,-0.193975359201],
                        [0.997179210186,-0.0394601933658,-0.0638479366899],
                        [0.997029185295,-0.0770247355103,0.0],
                        [0.991025745869,-0.117650069296,-0.0634539350867],
                        [0.979053080082,-0.193714544177,-0.0626873448491],
                        [0.974178731441,-0.225778326392,0.0],
                        [0.961880862713,-0.266443610191,-0.0615878328681],
                        [0.991025745869,-0.117650069296,-0.0634539350867],
                        [0.979053080082,-0.193714544177,-0.0626873448491],
                        [0.978907585144,-0.158833146095,-0.128498718143],
                        [0.894335091114,-0.409316182137,-0.180623859167],
                        [0.892938017845,-0.434652328491,-0.117213711143],
                        [0.866019308567,-0.468421578407,-0.174905076623],
                        [0.940329909325,-0.334895044565,-0.0602079555392],
                        [0.932827115059,-0.360324263573,0.0],
                        [0.915323853493,-0.398431301117,-0.0586068555713],
                        [0.887796461582,-0.456712335348,-0.0568443164229],
                        [0.8796184659,-0.475679844618,0.0],
                        [0.858619451523,-0.509656965733,-0.0549761541188],
                        [0.915323853493,-0.398431301117,-0.0586068555713],
                        [0.887796461582,-0.456712335348,-0.0568443164229],
                        [0.892938017845,-0.434652328491,-0.117213711143],
                        [0.960443258286,-0.199805602431,-0.193975359201],
                        [0.942551255226,-0.274516820908,-0.190361812711],
                        [0.935745954514,-0.239766731858,-0.258633822203],
                        [0.961880862713,-0.266443610191,-0.0615878328681],
                        [0.940329909325,-0.334895044565,-0.0602079555392],
                        [0.943842172623,-0.306287169456,-0.123895764351],
                        [0.920180141926,-0.34457308054,-0.185843646526],
                        [0.894335091114,-0.409316182137,-0.180623859167],
                        [0.891307473183,-0.380633711815,-0.246351331472],
                        [0.943842172623,-0.306287169456,-0.123895764351],
                        [0.920180141926,-0.34457308054,-0.185843646526],
                        [0.942551255226,-0.274516820908,-0.190361812711],
                        [0.85085272789,0.276221334934,-0.446935534477],
                        [0.867211103439,0.20109423995,-0.455528259277],
                        [0.826465010643,0.236761152744,-0.510783493519],
                        [0.922915279865,0.202408134937,-0.327503234148],
                        [0.935258030891,0.123069040477,-0.33188316226],
                        [0.903840482235,0.162998497486,-0.395605653524],
                        [0.878655850887,0.122248865664,-0.461539924145],
                        [0.88455080986,0.0410230122507,-0.464636415243],
                        [0.847858190536,0.0809632539749,-0.524005174637],
                        [0.903840482235,0.162998497486,-0.395605653524],
                        [0.878655850887,0.122248865664,-0.461539924145],
                        [0.867211103439,0.20109423995,-0.455528259277],
                        [0.97295331955,0.121444880962,-0.196501940489],
                        [0.979394435883,0.0407496243715,-0.197802826762],
                        [0.960611641407,0.0820460245013,-0.265506535769],
                        [0.997179210186,0.0394601933658,-0.0638479366899],
                        [0.997179210186,-0.0394601933658,-0.0638479366899],
                        [0.991494178772,0.0,-0.130150929093],
                        [0.979394435883,-0.0407496243715,-0.197802826762],
                        [0.97295331955,-0.121444880962,-0.196501940489],
                        [0.960611641407,-0.0820460245013,-0.265506535769],
                        [0.991494178772,0.0,-0.130150929093],
                        [0.979394435883,-0.0407496243715,-0.197802826762],
                        [0.979394435883,0.0407496243715,-0.197802826762],
                        [0.88455080986,-0.0410230122507,-0.464636415243],
                        [0.878655850887,-0.122248865664,-0.461539924145],
                        [0.847858190536,-0.0809632539749,-0.524005174637],
                        [0.935258030891,-0.123069040477,-0.33188316226],
                        [0.922915279865,-0.202408134937,-0.327503234148],
                        [0.903840482235,-0.162998497486,-0.395605653524],
                        [0.867211103439,-0.20109423995,-0.455528259277],
                        [0.85085272789,-0.276221334934,-0.446935534477],
                        [0.826465010643,-0.236761152744,-0.510783493519],
                        [0.903840482235,-0.162998497486,-0.395605653524],
                        [0.867211103439,-0.20109423995,-0.455528259277],
                        [0.878655850887,-0.122248865664,-0.461539924145],
                        [0.960611641407,0.0820460245013,-0.265506535769],
                        [0.941618084908,0.04130198434,-0.334140062332],
                        [0.935258030891,0.123069040477,-0.33188316226],
                        [0.960611641407,-0.0820460245013,-0.265506535769],
                        [0.935258030891,-0.123069040477,-0.33188316226],
                        [0.941618084908,-0.04130198434,-0.334140062332],
                        [0.916092038155,0.0,-0.400968074799],
                        [0.88455080986,-0.0410230122507,-0.464636415243],
                        [0.88455080986,0.0410230122507,-0.464636415243],
                        [0.941618084908,-0.04130198434,-0.334140062332],
                        [0.916092038155,0.0,-0.400968074799],
                        [0.941618084908,0.04130198434,-0.334140062332]]
                    return points


            class Numbers:

                @staticmethod
                def isclose(a, b, rel_tol=1e-09, abs_tol=1e-09):
                    """check equality within tolerance"""
                    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


            class Data:

                @staticmethod
                def list_to_datatree(raggedList):
                    """Python to Grasshopper (from Chen Jingcheng)"""
                    rl = raggedList
                    result = DataTree[object]()
                    for i in range(len(rl)):
                        temp = []
                        for j in range(len(rl[i])):
                            temp.append(rl[i][j])
                        path = GH_Path(i)
                        result.AddRange(temp, path)
                    return result

                @staticmethod
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
                
                @staticmethod
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
            
                @staticmethod
                def flatten_list(list):
                    """Flatten a list of list (not higher degrees!)"""
                    flatlist = []
                    for sublist in list:
                        for item in sublist:
                            flatlist.append(item)
                    return flatlist

                @staticmethod
                def islistsimilar(list1,list2):
                    """check if two lists contain the same integers"""
                    state = False
                    if len(list1) == len(list2):
                        sort1=copy.deepcopy(list1)
                        sort2=copy.deepcopy(list2)
                        sort1.sort()
                        sort2.sort()
                        if sort1 == sort2:
                            state = True
                    return state

                @staticmethod
                def list_of_empty_lists(n):
                    """Generate a list of n empty lists"""
                    list=[]
                    for i in range(n):
                        list.append([])
                    return list

                @staticmethod
                def sort_list_sync(list_to_sort, key_list):
                    """Sort list synchroneously using keys"""
                    return [list_to_sort[i] for i in key_list]

                @staticmethod
                def break_list(alist):
                    """return list first item if parameter is a list"""
                    try : return alist[0]
                    except: return alist

                @staticmethod
                def seq_to_steps(seq):
                    step=[]
                    steps=[]
                    for i in range(len(str(seq))):
                        char = str(seq)[i]
                        if char == '[':
                            index = 0
                            step.append(index)
                        elif char == ']':
                            del step[-1]
                            index = 0
                        elif char == ' ':
                            pass
                        elif char == ',':
                            step[-1] += 1
                        if char == ',' or  char == '[':
                            steps.append(copy.deepcopy(step))
                    return(steps)
            
                @staticmethod
                def deepest_steps(seq):
                    step=[]
                    steps=[]
                    for i in range(len(str(seq))):
                        char = str(seq)[i]
                        if char == '[':
                            index = 0
                            step.append(index)
                        elif char == ']':
                            del step[-1]
                            index = 0
                        elif char == ' ':
                            pass
                        elif char == ',':
                            step[-1] += 1
                        else:
                            steps.append(copy.deepcopy(step))
                    return(steps)
                
                @staticmethod
                def get_item_from_path(l, path):
                    l = copy.deepcopy(l)
                    if type(path) == list:
                        for i in range(len(path)):
                            l = l[path[i]]
                        return l
                                    
                @staticmethod
                def order_sequence(steps):
                    #tree as a list of paths
                    #path as a list of indices
                    new_steps = []
                    for step in copy.deepcopy(steps):
                        depth = 0
                        ls = len(steps)
                        # compute current tree depth
                        for j in range(ls):
                            if len(steps[j])-1 > depth : depth = len(steps[j])-1
                        # append current first deepest item
                        for j in range(ls):
                            if len(steps[j])-1 == depth : 
                                new_steps.append(steps[j])
                                del(steps[j])
                                break
                    return new_steps

                @staticmethod
                def seq_to_tree(text):
                    #sequence as text
                    seq = ast.literal_eval(text)
                    steps = Toolbox.Data.seq_to_steps(seq)
                    deep = Toolbox.Data.deepest_steps(seq)
                    tree = DataTree[object]()
                    for i in range(len(deep)):
                        path = deep[i]
                        item = Toolbox.Data.get_item_from_path(seq, path)
                        temp = [item]
                        tree.Add(item, GH_Path(*path))
                    return tree

                @staticmethod
                def tree_to_seq(tree):

                    # get tree paths as list of int
                    paths = []
                    parents = []
                    all_parents = []
                    for i in range(tree.BranchCount):
                        path_string = tree.Path(i).ToString()
                        path = []
                        num = None
                        for char in path_string:
                            if char == '{' or char == ';' or char == '}':
                                if num != None :
                                    path.append(num)
                                    num = None
                            else : 
                                if num == None: num = int(char)
                                else: num = int(str(num) + char)
                        paths.append(path)
                        #parents
                        all_par=[]
                        if len(path) == 1 : 
                            parents.append('M')
                        else: 
                            parents.append(path[0:len(path)-1])
                            for j in range(len(path)-1):
                                all_par.append(path[0:len(path)-1-j])
                        all_par.append('M')
                        all_parents.append(all_par)

                    # create sequence from paths
                    seq_as_string = ''
                    for i in range(len(paths)):
                        path = paths[i]
                        #add coma
                        if i != 0 : seq_as_string += ','
                        #if parent doesn't exists before, add opening parenthesis
                        if (parents[i] in parents[0:i]) is False:
                            #add one parenthesis for each zero in path.
                            last_zeros = 0
                            for j in range(len(path)):
                                if path[j] == 0: last_zeros += 1
                                else: last_zeros = 0
                            seq_as_string += '[' * last_zeros 
                        #add number
                        seq_as_string += str(tree.AllData()[i])
                        #if parent doesn't exist after, add closing parenthesis
                        if (parents[i] in parents[i+1:len(parents)]) is False:
                            #last parenthesis of the sequence
                            if i+1 == len(paths):
                                seq_as_string += ']' * len(path)
                            else:
                                count = 0
                                search = True
                                for j in range(len(all_parents[i])):
                                    if search == True:
                                        for k in range(len(all_parents[i+1])):
                                            if search == True:
                                                if all_parents[i][j] == all_parents[i+1][k]:
                                                    count = j
                                                    search = False
                                seq_as_string += ']' * count
                    
                    return seq_as_string
                
                @staticmethod
                def test_seq(seq):
                    flag = False
                    if (type(seq) is str):
                        if len(seq) > 2:
                            if seq[0] == '[' and seq[-1] == ']':
                                comas=0
                                ophook=0
                                clhook=0
                                numbers=[]
                                num = ''
                                flag = True
                                for i in range(len(seq)):
                                    if seq[i] == '[' : ophook += 1
                                    elif seq[i] == ']' : clhook += 1
                                    elif seq[i] == ',' : comas += 1
                                    elif seq[i] == ' ': pass
                                    elif seq[i] in ['0','1','2','3','4','5','6','7','8','9'] :
                                        num += seq[i]
                                        if seq[i+1] not in ['0','1','2','3','4','5','6','7','8','9']: 
                                            numbers.append(int(num))
                                            num = ''
                                    else: raise Exception( 'Invalid character in sequence.')
                                if ophook != clhook : raise Exception( 'Missing hook(s) in sequence.')
                                if comas != len(numbers)-1 : raise Exception( 'Missing coma(s) in sequence.')
                                #if Toolbox.Data.islistsimilar(numbers, range(min(numbers), min(numbers)+len(numbers))) is False: raise Exception( 'Missing number(s) in sequence.')
                            else: raise Exception( 'Sequence should start and end with hooks.')
                    else: raise Exception( 'Sequence should be expressed as a string.')
                    if flag == False: raise Exception( 'Error is sequence input.')
                    return flag

                @staticmethod
                def reorder_sequence(seq):
                    seq = str(seq)
                    new_num = range(len(Toolbox.Data.flatten_integer_list(ast.literal_eval(seq))))
                    new_seq = ''
                    temp_num = None
                    count = 0
                    for i in range(len(seq)):
                        if seq[i] != '[' and seq[i] != ',' and seq[i] != ']' and seq[i] != ' ':
                            if temp_num == None: temp_num = seq[i]
                            else: temp_num += seq[i]
                            if seq[i+1] != '[' and seq[i+1] != ',' and seq[i+1] != ']' and seq[i+1] != ' ': pass
                            else: 
                                new_seq += str(new_num[count])
                                count += 1
                        else: new_seq += seq[i]
                    return new_seq


        class Basics:
            """Class of geometrical functions independant from the rhinocommon library"""

        
            @staticmethod
            def length(v):
                """ Compute vector length. """
                return Basics.dot(v, v) ** .5

            @staticmethod
            def angle(v1, v2, w):
                """ Compute angle beween two vectors. The angle is comprised within the [0;2pi] range. """

                _ = sum([coord ** 2 for coord in v1]) ** .5  # v1 magnitude
                v1 = [coord / _ for coord in v1]  # Unitize v1
                _ = sum([coord ** 2 for coord in v2]) ** .5  # v2 magnitude
                v2 = [coord / _ for coord in v2]  # Unitize v2

                dot = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
                det = (v1[1] * v2[2] - v1[2] * v2[1],
                    v1[2] * v2[0] - v1[0] * v2[2],
                    v1[0] * v2[1] - v1[1] * v2[0],)
                det = sum([det_i ** 2. for det_i in det]) ** .5

                angle = math.atan2(det, dot)
                try:
                    sign = sum([v_i * w_i for v_i, w_i in zip(v2, w)])
                    sign /= abs(sign)
                except:
                    sign = 1
                sign = 1
                
                return sign * angle

            @staticmethod
            def unitize(v):
                v_length = Basics.length(v)
                return tuple([vi / v_length for vi in v])

            @staticmethod
            def dot(v1, v2):
                """Dot product of two vectors"""
                return sum([a * b for a, b in zip(v1, v2)])

            @staticmethod
            def cross(v1, v2):
                n = (v1[1] * v2[2] - v1[2] * v2[1],
                    v1[2] * v2[0] - v1[0] * v2[2],
                    v1[0] * v2[1] - v1[1] * v2[0])
                return n

            @staticmethod
            def project(px, py, v, proj_dir):
                """Project a vector on a plate defined by two axis with respect
                to a projection vector"""
                n = Basics.cross(px, py)

                n_dot_proj_dir = Basics.dot(n, proj_dir)
                
                # If d is parallel to the plane, no projection is possible
                if n_dot_proj_dir == 0:
                    # But is ok is v in within the plane
                    if dot(v, n) == 0:
                        return v
                    return []

                # Position parameter of the projection
                q = - Basics.dot(v, n) / n_dot_proj_dir

                # v is already within the plane
                if q == 0:
                    return v

                return tuple([vi + q * di for vi, di in zip(v, proj_dir)])

            @staticmethod
            def get_yks(vi, y, a, n):
                ys_k = []

                for i in range(n):
                    ci = math.cos(0.5 * (math.pi - a) + a / (n - 1) * i)
                    si = math.sin(0.5 * (math.pi - a) + a / (n - 1) * i)

                    yix = (vi[0] ** 2 * (1 - ci) + ci) * y[0] + \
                        (vi[0] * vi[1] * (1 - ci) - vi[2] * si) * y[1] + \
                        (vi[0] * vi[2] * (1 - ci) + vi[1] * si) * y[2]

                    yiy = (vi[0] * vi[1] * (1 - ci) + vi[2] * si) * y[0] + \
                        (vi[1] ** 2 * (1 - ci) + ci) * y[1] + \
                        (vi[1] * vi[2] * (1 - ci) - vi[0] * si) * y[2]

                    yiz = (vi[0] * vi[2] * (1 - ci) - vi[1] * si) * y[0] + \
                        (vi[1] * vi[2] * (1 - ci) + vi[0] * si) * y[1] + \
                        (vi[2] ** 2 * (1 - ci) + ci) * y[2]

                    ys_k.append((yix, yiy, yiz))

                return tuple(ys_k[::-1])

            @staticmethod
            def flip_crv(top, bottom):
                top14 = [[top[4 * i], top[4 * i + 3]] for i in range(len(top) // 4)]
                top23 = [[top[4 * i + 1], top[4 * i + 2]] for i in range(len(top) // 4)]

                bottom14 = [[bottom[4 * i], bottom[4 * i + 3]] for i in range(len(bottom) // 4)]
                bottom23 = [[bottom[4 * i + 1], bottom[4 * i + 2]] for i in range(len(bottom) // 4)]

                return ([item for sublits in [tuple([t[0]] + b + [t[1]])
                                            for b, t in zip(bottom23, top23)] for item in sublits],
                        [item for sublist in [tuple([t[0]] + b + [t[1]])
                                            for b, t in zip(bottom14, top14)] for item in sublist])

        pass
    
        #Security ---------------------------------------------------------------------
    
        if date.today() < date(2022, 1, 1):
            model = None
            if breps :
                if run is True or run == None:
                    if len(constraints) != 5: constraints = [None,None,None,None,None]
                    if sequence is None:
                        model = PlateModel(breps,constraints=constraints)
                    else: model = PlateModel(breps, sequence, constraints=constraints)
                    breps = model.breps
                    sequence = model.sequence
                else: self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'Set Run to True to create a Plate Model.')
            else: self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'Waiting to get Breps as input.')
        else: self.AddRuntimeMessage(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, 'This demo version of the plugin has expired. Please contact me for more information about latest updates: nicolas.rogeau@gmail.com')

        return (model, breps, sequence)

import GhPython
import System

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Plate Model Builder"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("1200b47c-43d6-45a6-9620-46e03fffe5e2")