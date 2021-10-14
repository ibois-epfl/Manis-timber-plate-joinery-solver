"""Scale the plates while keeping faces planar."""

from ghpythonlib.componentbase import dotnetcompiledcomponent as component
import Grasshopper, GhPython
import System
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import math
import scriptcontext

__author__ = "Nicolas Rogeau"
__laboratory__ = "IBOIS, Laboratory for Timber Construction" 
__university__ = "EPFL, Ecole Polytechnique Federale de Lausanne"
__funding__ = "NCCR Digital Fabrication, ETH Zurich"
__version__ = "2021.09"


class MyComponent(component):
    def __new__(cls):
        instance = Grasshopper.Kernel.GH_Component.__new__(cls,
            "Thicken plates", "Thicken", """Scale the plates while keeping faces planar.""", "Manis", "Utility")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("73376a07-b918-43c0-8a29-1fab470a5cd0")
    
    def SetUpParam(self, p, name, nickname, description):
        p.Name = name
        p.NickName = nickname
        p.Description = description
        p.Optional = True
    
    def RegisterInputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_Brep()
        self.SetUpParam(p, "breps", "breps", "Plate breps to scale.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "new_thickness", "new_thickness", "New thickness for to the plates.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Number()
        self.SetUpParam(p, "proportion", "proportion", "(Optional) Change the direction of the scaling (from 0 to 1, default = 0.5).")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
    
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "breps", "breps", "Updated breps.")
        self.Params.Output.Add(p)
        
    
    def SolveInstance(self, DA):
        p0 = self.marshal.GetInput(DA, 0)
        p1 = self.marshal.GetInput(DA, 1)
        p2 = self.marshal.GetInput(DA, 2)
        result = self.RunScript(p0, p1, p2)

        if result is not None:
            self.marshal.SetOutput(result, DA, 0, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAACxIAAAsSAdLdfvwAAAC0SURBVEhL7ZJbCsMwDARzph4213UtURmxGT9qkp9SwQTtSmgx5CilPAqaPV7nWT7gnECTSMcdnfewsm/tm3HRejzQPdKt0YFqa9Lx5uueahczoiTAi/YzaCpRWwG2s0oE0GwAmshWQH3GckXAN/UPmNYPBFx+qwERQLMBaCJbAfaKVSJA/RFo9tgKiKckA7U1OSB83VPdGh1kHYcV3SPtYoYVHPei/QyaRD2aQ3CHQPM+yvEGLDPifQrgf5IAAAAASUVORK5CYII="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, breps, new_thickness, proportion):

        def surface_centroid(surface):
            surface = rs.coercesurface(surface)
            return rg.AreaMassProperties.Compute(surface).Centroid

        def sort_surfaces_by_altitude(planar_surfaces):
            faces = planar_surfaces
            faces_tuples = []
            for i in range(len(faces)):
                face_centroid = surface_centroid(faces[i])
                faces_tuples.append([faces[i],face_centroid[2]])
            sortedfaces = sorted(faces_tuples, key=lambda faces: faces[1])
            return sortedfaces

        def sort_surfaces_by_area(planar_surfaces):
            faces = planar_surfaces
            faces_tuples = []
            for face in faces:
                face = rg.BrepFace.DuplicateFace(face, False)
                face_area = rg.Brep.GetArea(face)
                faces_tuples.append([face,face_area])
            sortedfaces = sorted(faces_tuples, key=lambda faces: faces[1])
            return sortedfaces

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

        def resimplify_Curve(curve):
            """Simplify and change curve seam if it's not already a vertice"""

            curve=scriptcontext.doc.Objects.Add(curve)
            vertices = rs.PolylineVertices(curve)
            best_candidate=curve
            best_v_len = len(vertices)

            for i in range(len(vertices)):
                new_candidate = rs.CopyObject(curve)
                rs.CurveSeam(new_candidate, rs.CurveClosestPoint(new_candidate,vertices[i]))
                rs.SimplifyCurve(new_candidate)
                v_len = len(rs.PolylineVertices(new_candidate))
                if v_len < best_v_len:
                    best_candidate = rs.CopyObject(new_candidate)
                    best_v_len = v_len
            return rs.coercecurve(best_candidate)
        
        def align_curve_direction(guide, curve):
            if rs.CurveDirectionsMatch(curve, guide) == False: 
                try: rg.Curve.Reverse(curve)
                except: rs.ReverseCurve(curve)
            return curve

        def line_to_vec(line, unitize=False):
            """get a vector from a line"""
            vec = rs.VectorCreate(rs.CurveEndPoint(line),rs.CurveStartPoint(line))
            if unitize is True:
                vec = rs.VectorUnitize(vec)
            return vec

        def curve_seam(curve, point):
            return rs.CurveSeam(curve, rs.CurveClosestPoint(curve, point))

        def match_seams(curve1, curve2, simplify=True):
                            """match the seam of two curves that have parallel segments"""

                            if simplify is True:
                                curve1=resimplify_Curve(curve1)
                                curve2=resimplify_Curve(curve2)
                            curve2 = align_curve_direction(rs.coercecurve(curve1),rs.coercecurve(curve2))
                            curve1=scriptcontext.doc.Objects.Add(curve1)
                            curve2=scriptcontext.doc.Objects.Add(curve2)
                            seg1 = rs.ExplodeCurves(curve1)
                            seg2 = rs.ExplodeCurves(curve2)
                            shift = None

                            if len(seg1) == len(seg2):
                                for i in range(len(seg2)):
                                    flag = True
                                    for j in range(len(seg1)):
                                        vec1 = line_to_vec(seg2[(i+j)%len(seg2)])
                                        vec2 = line_to_vec(seg1[j])
                                        if rs.IsVectorParallelTo(vec1,vec2) != 1:
                                            flag = False
                                    if flag == True:
                                        shift = i
                                        break
                            else: raise Exception("polylines have a different number of segments")
                            if shift == None: raise Exception("polyline segments are not parallel")
                            else:
                                points = rs.PolylineVertices(curve2)

                                curve_seam(curve2, points[shift])
                                rs.coercecurve(curve2)
                            curve1 = rs.coercecurve(curve1)
                            curve2 = rs.coercecurve(curve2)
                            return [curve1,curve2]
                
        def brep_from_2_poly(poly1, poly2):
                            poly2 = align_curve_direction(rs.coercegeometry(poly1), rs.coercegeometry(poly2))
                            poly2 = rs.AddPolyline(rs.PolylineVertices(poly2)+[rs.PolylineVertices(poly2)[0]])
                            poly1, poly2 = match_seams(rs.coercecurve(poly1),rs.coercecurve(poly2))
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

        if proportion is None: proportion = 0.5
        new_breps = []
        for brep in breps:
            #faces
            faces= brep.Faces
            sortedfaces = sort_surfaces_by_area(faces)
            sortedfaces.reverse()
            top_and_bottom = [sortedfaces[0][0],sortedfaces[1][0]]
            bottom_face = sort_surfaces_by_altitude(top_and_bottom)[0][0]
            top_face = sort_surfaces_by_altitude(top_and_bottom)[1][0]
        
            #contour
            top_contour = get_face_largest_contour(top_face)
            if type(top_contour) != rg.PolylineCurve: top_contour=top_contour.ToPolyline(0.01,0.01,0.01,10000)
            top_contour = resimplify_Curve(top_contour)
            bottom_contour = get_face_largest_contour(bottom_face)
            bottom_contour = align_curve_direction(top_contour,bottom_contour)
            top_contour, bottom_contour = match_seams(top_contour, bottom_contour)
            top_center = rs.CurveAreaCentroid(top_contour)[0]
            thickness = rg.Point3d.DistanceTo(top_center, rg.Brep.ClosestPoint(bottom_face, top_center))
            if new_thickness != thickness and new_thickness != None : 
                normal = rs.CurveNormal(top_contour)
                top_vertices = rs.PolylineVertices(top_contour)
                bottom_vertices = rs.PolylineVertices(bottom_contour)
                for i in range(len(bottom_vertices)):
                    vec = rs.VectorCreate(top_vertices[i],bottom_vertices[i])
                    vec = rs.VectorUnitize(vec)
                    angle = rs.VectorAngle(normal, vec)
                    factor = (new_thickness - thickness)/math.cos(math.radians(angle))
                    top_vertices[i] = rs.MoveObject(top_vertices[i], factor*proportion*vec)
                    bottom_vertices[i] = rs.MoveObject(bottom_vertices[i], -factor*(1-proportion)*vec)
                top_contour=rs.coercecurve(rs.AddPolyline(top_vertices))
                bottom_contour=rs.coercecurve(rs.AddPolyline(bottom_vertices))
                new_breps.append(brep_from_2_poly(top_contour, bottom_contour))
        
        return new_breps

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Thicken plates"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return ""
    
    def get_Id(self):
        return System.Guid("76b95803-ad1b-46dc-bf51-173cd45e5198")