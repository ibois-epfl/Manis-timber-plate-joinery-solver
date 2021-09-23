from ghpythonlib.componentbase import dotnetcompiledcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import math
import copy
import ast
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper.Kernel.GH_Convert import ObjRefToGeometry, ToGHBrep
from Grasshopper.Kernel import GH_Conversion 
import scriptcontext


class MyComponent(component):
    def __new__(cls):
        instance = Grasshopper.Kernel.GH_Component.__new__(cls,
            "Sequence Tree Converter", "Seq and Tree", """Convert a sequence (as text) to a datatree, or a datatree to a sequence. An optional list of data can also be sorted synchroneously.""", "Manis", "Utility")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("c25b2168-ece8-4318-b659-8106b6847c34")
    
    def SetUpParam(self, p, name, nickname, description):
        p.Name = name
        p.NickName = nickname
        p.Description = description
        p.Optional = True
    
    def RegisterInputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_String()
        self.SetUpParam(p, "sequence", "sequence", "Sequence to convert to datatree.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Integer()
        self.SetUpParam(p, "datatree", "datatree", "Datatree to convert to sequence.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.tree
        self.Params.Input.Add(p)
        
        p = GhPython.Assemblies.MarshalParam()
        self.SetUpParam(p, "data", "data", "List of data to organize according to the sequence (if a datatree is provided, the newly generated sequence will be used).")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.list
        self.Params.Input.Add(p)
        
    
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_Integer()
        self.SetUpParam(p, "datatree", "datatree", "Generated datatree from sequence.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_String()
        self.SetUpParam(p, "sequence", "sequence", "Generated sequence from datatree.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "match", "match", "Organized list matching sequence.")
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
                self.marshal.SetOutput(result[2], DA, 2, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAACxIAAAsSAdLdfvwAAADkSURBVEhLtY/REYMwDEPpSp2pMzFTZ+pPGuVQznFkQwvo7kFkOTYspZRbaY/nuhaifIbv9b434U28Z81e9EQz0vCoVzX6NIy84tQC1lSdRDPSUBFlly0AKj+1YM+rGn0a+hrxGYhmdGMve5/he72Xl64Ej1s1bbya9vi8X4XYEFT1jOcol55FGwDhIe+poZe5XUDBTI1QPeP1qNhs6K2gpwlntYDyl7mAstnwEZa+gAUhO2grDX/QhEwxLSBOduAwHL0Z4QJi1AcDFNiTsbsAGP00HBxaADbxD2SP4vAC8N+CsnwB5cS2jP4jXZUAAAAASUVORK5CYII="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    
    def RunScript(self, sequence, datatree, data):

        seq = sequence
        tree = datatree

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
                    #print step
                    steps.append(copy.deepcopy(step))
                    #print 'char= '+ char + '         index = ' + str(index) + '        step = ' + str(step)
            return(steps)
        
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
        
        def get_item_from_path(l, path):
            l = copy.deepcopy(l)
            if type(path) == list:
                for i in range(len(path)):
                    l = l[path[i]]
                return l

        def seq_to_tree(text):
            #sequence as text
            seq = ast.literal_eval(text)
            steps = seq_to_steps(seq)
            deep = deepest_steps(seq)
            print steps
            tree = DataTree[object]()
            for i in range(len(deep)):
                path = deep[i]
                item = get_item_from_path(seq, path)
                temp = [item]
                tree.Add(item, GH_Path(*path))
            return tree

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
                    else: raise Exception( 'Sequence should start and end with hooks.')
            else: raise Exception( 'Sequence should be expressed as a string.')
            if flag == False: raise Exception( 'Error is sequence input.')
            return flag

        def list_to_datatree(raggedList):
            """Python to Grasshopper"""
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

        if seq != None: 
            test_seq(seq)
            tree = seq_to_tree(seq)
        if tree != None: seq = tree_to_seq(tree) 
        
        dt= []
        count = 0
        sequence = copy.deepcopy(seq)
        if sequence and data: 
            sequence = ast.literal_eval(sequence)
            for i in range(len(sequence)):
                if type(sequence[i]) is list:
                    intlist = flatten_integer_list(sequence[i])
                else: intlist = [sequence[i]]
                sub = []
                for j in range(len(intlist)):
                    sub.append(data[count])
                    count += 1
                dt.append(sub)
            dt = list_to_datatree(dt)
        match = dt
        
        # return outputs if you have them; here I try it for you:
        return (tree, seq, match)


import GhPython
import System

class AssemblyInfo(GhPython.Assemblies.PythonAssemblyInfo):
    def get_AssemblyName(self):
        return "Sequence Tree Converter"
    
    def get_AssemblyDescription(self):
        return """"""

    def get_AssemblyVersion(self):
        return "0.1"

    def get_AuthorName(self):
        return "Nicolas Rogeau"
    
    def get_Id(self):
        return System.Guid("15a9cdcb-1504-48fb-a114-4a7956733e65")