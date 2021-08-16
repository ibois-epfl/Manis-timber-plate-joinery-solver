# Manis -  A timber plate joinery solver

* [Introduction](#introduction)
* [For users](#for-users)
* [For developers](#for-developers)

## Introduction

### Tool purpose
Manis is a grasshopper plugin for creating joints between timber panels.
The tool allows:
* generating joints geometry according to topological constraints
* generating CNC cutting toolpath to automate the fabrication of the plates
* generating robotic trajectories to automate the assembly of the plates

### Reference
For research applications, please refer to the following publication. It includes a detailed description of the algorithms behind the code: 
> __Nicolas Rogeau, Pierre Latteur, Yves Weinand, _An integrated design tool for timber plate structures to generate joints geometry, fabrication toolpath, and robot trajectories_, Automation in Construction, Volume 130, October 2021__
> [https://doi.org/10.1016/j.autcon.2021.103875](https://doi.org/10.1016/j.autcon.2021.103875)

## For users

### Plugin installation
1. Download the file `Manis.ghpy`.
2. Place the file inside Grasshopper Components folder `C:\Users\yourname\AppData\Roaming\Grasshopper\Libraries` or `Grasshopper -> File -> Special folders -> Components folder`.
3. Verify that the file is unblocked: `Right-click on the file -> Properties -> General -> Unblock`.
4. Restart Rhino and open Grasshopper. There should be a new tab in Grasshopper named Manis.

### Plugin structure
... coming soon...

### Example files
... coming soon...

## For developers

### Improving the code
The source code consists of one single python file: `platesjoinery.py`. 
It is not necessary to recompile the Grasshopper plugin when debugging or developing new functions.
Instead, you can test your modifications directly inside a custom Grasshopper python component.
You need to execute the following steps to be able to call the functions from the python file inside the Grasshopper environment: 
1. Download the file `platesjoinery.py`.
2. Place the file inside Rhinoceros IronPython folder `C:\Users\yourname\AppData\Roaming\McNeel\Rhinoceros\7.0\Plug-ins\IronPython\settings\lib`.
3. Verify that the path is correctly specified in Rhino: `Type _EditPythonScript -> Tools -> Options -> Files -> Add to search path (if necessary)`.
4. Restart Rhino and open Grasshopper. You should now be able to import the module `platesjoinery` inside a Grasshopper python component.

### Code structure
The source code is split in 5 classes:
* _PlateModel_: The main class of the solver. A plate model instance is created for each new timber plate structures. Adjacencies and insertion vectors are computed during the instanciation of the plate model. This class also containts methods to create timber joints and generate fabrication toolpath.
* _PlateModule_: A sub-class of the plate model to deal with modular assemblies. For each group of plates specified by the user, a new module is created.
* _Plate_: A sub-class of the plate model containing the information about a single element of the structure. An instance of the plate class contains geometric information such as the plate thickness or the plate contours.
* _Toolbox_: A list of methods extending the Rhino framework. 
* _Basics_: A list of methods independant of the Rhino framework.

### Re-compiling a new version of the plug-in
Once the modifications brought to the source code have been validated, a new version of the plugin can be generated.

1. Download the folder `Grasshopper compilation files`.
2. Open the file `build.py` in an editor and replace the 5 classes with their new version from the updated source code.
3. If necessary, update the parameters and/or the definition of the plugin components (each file corresponds to a single component of the plugin).
4. In Rhino, run the command `_EditPythonScript` and open the file `main.py`.
5. Update the version number of the plugin in the first argument of the function `clr.CompileModules(" Manis.v1.2.3.ghpy"...`
6. Run the file `main.py`. It will create a file `Manis.v1.2.3.ghpy` in the folder `Grasshopper compilation files`.
7. Move the newly created file to the Grasshopper Components folder `C:\Users\yourname\AppData\Roaming\Grasshopper\Libraries` or `Grasshopper -> File -> Special folders -> Components folder`.
8. Restart Rhino and open Grasshopper. The plugin should be updated.

For further information about how to create a custom grasshopper component with python, you can refer to [this tutorial](https://discourse.mcneel.com/t/tutorial-creating-a-grasshopper-component-with-the-python-ghpy-compiler/38552).


