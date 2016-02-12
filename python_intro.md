When I was starting to use Python for astronomy I wished there was some straightforward document that would introduce me to everything. This is my attempt at fixing that for future users.


* [First-time Python Setup](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#first-time-python-setup)

* [First-time Programming Introduction](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#first-time-programming-introduction)

* [First-time Python Introduction](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#first-time-python-introduction)
 * [Assigning varibles](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#assigning-variables)
 * [Manipulating variables](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#manipulating variables)
 * [Flow Control in Python](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#flow-control-in-python)
 * [Functions and Objects](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#first-time-python-setup)

* [Time to do Astronomy!](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#time-to-do-astronomy)
 * [Import Statements](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#import-statements)
 * [Constants (sort of)](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#constants-sort-of)
 * [Functions](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#functions)
 * [List comprehension](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#list-comprehension)
 * [FITS I/0](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#fits-io)
 * [NumPy ndarray allocation](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#numpy-ndarray-allocation)
 * [NumPy ndarray indexing and slicing](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#numpy-ndarray-indexing-and-slicing)
 * [NumPy operations over axes](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#numpy-operations-over-axes)
 * [Boolean NumPy ndarrays](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#boolean-numpy-ndarrays)
 * [Why we don't concatenate arrays](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#why-we-dont-concatenate-arrays)
 * [Coordinates through np.mgrid](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#coordinates-through-npmgrid)
 * [To fit or not to fit: scipy.optimize.curve_fit](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#to-fit-or-not-to-fit-scipyoptimizecurve_fit)
 * [Saving data](https://github.com/Saethlin/astrotools/blob/master/python_intro.md#saving-data)

#First-time Python Setup

If you're setting up on a UF linux box, I wrote a [bash script](https://github.com/Saethlin/astrotools/blob/master/setup.sh) just for you. UF does have Python 2.6 and the Anadonca distribution of 2.7 installed on the network, but if you want control over your own installation or want a different version, the bash script will save you a lot of time and frustration. If you use the bash script, you can skip the rest of this section.

First things first; you need the Python interpreter. Python 2.7 is the most compatible for astronomy, but if you only care about the big and well-maintained packages, the most recent version should do just fine though there are all sorts of subtle changes in how the standard libraries are structured that will break scripts from version to version.
https://www.python.org/downloads/

Just Python itself won't get you very far, to download packages you want pip. Open up a terminal and try the command `pip --version` If you get an error, you'll need to install pip. With any luck, your version of Python at least got you easy_install. So `easy_install pip`.

Now you can almost effortlessly get the rest of your packages. The command you want is `pip install some_package_you_want`. For sure you want numpy, scipy, astropy, and matplotlib. So `pip install numpy scipy astropy matplotlib pillow` and go find something to do while you wait.


#First-time programming introduction

If you already have experience with any programming language you can almost certainly skip this section.

For simplicity, think of a computer executing a program as being composed of 3 parts:
* A CPU which does mathematical operations
* RAM (often just called memory), where you can store data during code execution
* A hard drive, where you can store information while code is not executing or if your RAM can't hold everything you're interested in

In astronomy, a typical program looks like this:

1. Read some information off the hard drive and somehow put it in memory
2. Do a lot of calculations
3. Write some new data to the hard drive


1. and 3. are very complicated but easy to automate, so you will find in pretty much any language you use for astronomy that they are very simple for the user.


#First-time Python introduction

You may find it valuable to follow along and execute code as you read, so open a text editor and a terminal to get started. On a UF linux box, you can right-click on the desktop to open a terminal, and enter the command `gedit &`. Save your new text file somewhere with a .py extension. The file can be executed by moving to the directory that contains the file and entering the command `python some_file.py`. On windows, `some_file.py` will suffice.

##Assigning Variables
Python is dynamically typed. Unlike many other languages this is totally fine:
```
i = False
print(i)
i = 0
print(i)
i = 0.
print(i)
i = '0'
print(i)
i = (0,)
print(i)
i = [0]
print(i)
```
Python interprets the first line and asks the memory for space to store a variable, saves the location of that as `i`, and stores the value `False` in the location that `i` corresponds to. The equals sign here is assignment; take whatever is on the right and assign that value to whatever is on the left.

The second line tells Python to go grab something called `i`, and ask it for a string (a bunch of characters) that represents it. The next lines change both the value and the type of the variable `i` from a boolean (True/False, sort of...) to an integer, then to a floating point number, then to a tuple, then to a list.


##Manipulating Variables
Now with some values stored in memory, we can manipulate them.
```
i = 1
print(i+1)
i += 1
print(i)
```
For many operations, Python offers syntax like the `+=`, which makes for some really neat code.

There are a lot of ways to compare values in Python.
```
a = 0
b = 1
print(a > b)
print(a >= b)
print(a == b)
print(a != b)
```

You can also do things like
```
a = 1
b = 0
print(a and b)
print(a or b)
```
All nonzero integer values evaluate to `True` and zero evaluates to `False`.

There are two other ways to compare values, which is with `&` and `|`, which are a bitwise and and or. These become useful in some situations, but mostly typing out `and` and `or` will do the trick.

Python's dynamical typing makes code simpler to read and write but trades off programmer time for CPU time. For astronomy this is often a good deal because you may only need to run something a few times but spend days writing it. The dynamical typing does have a quirk though because it relies on objects.
```
x = []
print(x)
y = x
print(y)
y += ['boo!']
print(y)
print(x)
```
There are two things to note here. Firstly, when using the `+` operator with lists it concatenates instead of adding. Operators mean different things depending on what they're used on, but for the most part they work as expected. Secondly, we get to see another potential downside to Python's dynamical typing. Instead of actually being an empty list, `x` starts off as a pointer to an empty list. The command `y = x` just copies a pointer to `y`.

Python also doesn't have any reserved variable names, so you can do:
```
a = True
False = a
print(True == False)
```
##Flow control in Python

Python (like most other high-level languages) supports the familiar if... then... statement, along with some basic loops. Unlike many other languages though, whitespace is mandatory in Python. Users of Java or C may be familiar with putting semicolons at the end of every line an using soft brackets or braces to indicate code blocks. Python rids itself of such characters in favor of whitespace. To end a line in Python, you must insert a newline character. To indicate a code block, the statement opening it ends with a `:` and the contents of the code block are indented. Tabs or spaces may be used but not mixed and spaces are *strongly* preferred, with 4 spaces used per indentation level. Most text editors can be set up to insert 4 spaces when the tab key is pressed, and to automatically indent when ending an indented line.

The if... then... statement in Python looks very familiar:
`
if test_condition:
    execute_this_code()
    and_this_too()
`
Just return to the indentation level of the `if` to exit the code block.

Python does not support for loops but does support for each loops, which just means that a for loop needs something it can iterate on instead of a variable, test condition, and modification statement. For example:
`
for thing in list_of_things:
    do_the_thing(thing)

If you want to iterate over a bunch of numbers, Python provides `range()` for you.
`
for t in range(100):
    print(t)
`

The same simple syntax applies to while loops:
`
while condition_is_true:
    just_do_it()
`
While loops should be avoided when possible in favor of for loops because they invite infinite loops, where for loops (because they're actually for each loops) almost always end.


##Functions and Objects

Functions are incredibly useful, as they enable the use of optimization/curve fitting.

Python supports object-oriented design, but it does not enforce it. A program isn't required to have objects definitions and call some main function, it can consist of just a list of statements to be executed in the order they appear. While using Python for astronomy it is unlikely that you will need to deal overmuch with objects, you should have some understanding.

Objects should be thought of almost in the same sense as physical objects; they have properties, can be manipulated, and many exist in a hierarchy. The basic unit of object-oriented programming is the class. A class defines a set of fields (or properties or attributes) and methods. An instance of an object is created by calling a constructor for the class, which is special method of the class itself that returns a pointer to a new object, which can then be manipulated. The numpy ndarray is an object you'll encounter a lot in the course of astronomy research.

#Importing Packages


Python has very nice syntax that makes it highly readable, but without packages it isn't useful for data processing. Some packages come with the base installation, like `os` and `sys`. Others need to be installed first. You should already have a small battery of packages, so let's do some astronomy.


#Time to do Astronomy!

You may have noticed by now that I put spaces around all my operators and that you don't have to. You really should though because it improves the readability of your code, which you may come to appreciate heavily later. You really should read the [Python style guide](https://www.python.org/dev/peps/pep-0008/), but just in case you don't, the more salient points are included in the rest of this guide.

You should be able now to read some Python. I have supplied a [sample program](https://github.com/Saethlin/astrotools/blob/master/vectorize_starfield.py) which is heavily commented and does a lot of common astronomy tasks (but is currently untested, as this is still in draft phase). You should read it now, as the rest of this section discusses it.


##Import Statements
It's good practice to open every Python script with a docstring that reminds the reader what this file does. I also use this region to leave myself notes and make short to-do lists.

Next are all your import statements. `__future__` imports come first, then Python standard library imports, then package imports, then local imports. Each section should be separated by a blank line. Python's dynamic typing can get you into serious trouble when importing, which is the origin of the PEP 0008 guidelines. Wildcard imports sound like a good idea, but the problem is that you have NO IDEA what you are getting. You could overwrite the value of True and False or replace some of the basic Python functions like `open()` or `enumerate()`. In addition, using statements like `from scipy.ndimage.filters import laplace` is discouraged because it wouldn't be unreasonable to then do something like `laplace = laplace(image)`, at which point you lose access to the laplace filter and it must be imported again.

##Constants (sort of)
After standard library imports come constants. Proper use of constants is a huge failure in a lot of code written by astronomers. They'll just call a function somewhere with mysterious values passed to it, offering the reader no explanation what the function parameter is, or where that value came from. Is this some sort of generally applicable setting? Is it specific to the data set you used? Putting all your constants at the beginning also makes it easy to adapt your code to new data, since a lot of possible adjustments are obvious.


##Functions
Next are function definitions. Keep in mind that Python is interpreted, not compiled, so the computer actually does not know what is in the lines after what it is executing (though Python does have a *basic* syntax checker). If a function is defined after it is called, the interpreter will arrive at the function call, not have a function to call, throw an exception, crash, and print a stack trace. So while functions could be defined in the midst of all the code, there's little reason to ever do that. Functions also really help to break up code into readable chunks. If there is a set of operations you'll need to do often or even just twice in one script it should be a function. If it's something you do a *lot*, consider saving it in its own script and importing it locally.

##List comprehension
Now comes the bulk of the code. I open vectorize_starfield.py with Python list comprehension. This is syntax uncommon among languages used for astronomy, but it's quite powerful and does exactly what it seems like. Just for clarity, `f.rsplit('.',1)[-1].lower()` breaks up `f` at the rightmost `.`, and makes it all lowercase. It basically extracts the extension from a filename. Python supports negative indexing, with `arr[0]` being the first item in `arr` and `arr[-1]` being the last, and `arr[-2]` being the second last. So `arr[f] == arr[f-len(arr)]`.

##FITS I/O
Now we want to read a FITS file. The call `fits.open(filename)` returns an astropy HDUList, but since the image files I'm using for this are pretty simple I already know that I want the zeroth HDU from the list, and the data that belongs to the HDU. A FITS file in general can have an arbitrary number header/data pairs.

##Numpy ndarray allocation
Now I allocate memory, with `np.empty()`. This doesn't touch the memory, it just identifies a chunk that no other program is using. Initially the array is filled with gibberish, but that's fine because I know I'll be overwriting everything. I want the shape of the array to be `number_of_files,image.shape[0],image.shape[1]`. Python won't let you tack a number onto a tuple, but you can make a new one by concatenating a one-item tuple `(item,)` with the shape tuple. `len()` just returns the length of an object, which is the length of the first axis for arrays. As soon as `fits.open()` is called, the entire file is loaded into memory so might as well copy its data into the first slot in the array.

##NumPy ndarray indexing and slicing
Since I've already read in the first image a bit of time can be saved by starting at the second. The colon syntax works the same as in MatLab, `arr[1:]` is a slice of `arr` starting at the second item, and `arr[:-1]` is without the last item. There's some other cool slicing that can be done like `arr[...,0]` produces a slice of `arr` across all axes but only the zeroth entries on the last. The ellipsis acts like a colon across all axes that would need indexing. Of course these can all be mixed together, so you could write `arr[4:-20,...,1:]`.

##Numpy operations over axes
NumPy offer a lot of cool operations over arrays like `np.max()`, `np.min()`, `np.mean()`, `np.std()`, and `np.median()`. These will all need to be passed the array to compute the function on, unless you call `arr.max()`, which behaves as expected. All these functions have an option argument, `axis`. If no value is passed the function is computed across the entire array. Here I want to compute the value between images so pass axis 0 because that is how to traverse the array from image to image. NumPy's functions that require sorting an array offer another optional argument, overwrite_input. Median requires sorting the values for each pixel, and if you want to maintain the integrity of the images Numpy would need to copy *the entire stack of images* to another location in memory and sort that. Doing so will massively increase memory consumption and even if enough memory is available for the operation, that's a lot of of allocating and copying which takes time.

##Boolean NumPy ndarrays
In order to make use of the Laplacian filter we need to start comparing it to things. The fast way to do this with NumPy arrays is to use statements like `arr > 0` and `arr1 & arr2`, which return a numpy array of boolean type. This is especially powerful because arrays are a way to index arrays. An array can be passed another array of integers and will return the specified entries. Boolean arrays can also be used to index entries and will return all entries where the array has the value `True`. These are also very useful because if they are 2-d they can be saved as an image and examined by eye.

##Why we don't concatenate arrays
The next section uses array concatenation and comparison to find local minima in the laplacian array. Concatenation of arrays should be avoided when possible because it requires allocating more memory. When the images were stacked up before being combined, I could have chosen to build the stack by concatenating the images. Doing so would take an *incredibly* large amount of time because the total memory required for that is 1 image array, then 2 image array, then 3 image array... then n image arrays. In total, that requires allocating memory that scales with the square of the size of each array. If you can know ahead of time how much memory will be required it's best to allocate it all in one shot; in this case memory usage can only scale linearly with the size of each array.

##Coordinates through np.mgrid
Now at line 107 I use one of numpy's index tricks, which returns an array that can be indexed with a boolean array to pull coordinates related to the locations marked True. Some people like to use `np.where()`, but I personally dislike that function since in astronomy there is usually a more elegant way to get coordinates. In this instance, `np.where()` is especially clumsy when we get to fitting stellar PSFs. Coordinate grids also make it very easy to compute distance-based filters, which is what I use to do simple PSF fitting.

##To fit or not to fit: scipy.optimize.curve_fit
The next point of interest is the actual PSF fitting. I use the aperture radius and the aperture boolean mask to grab the parts of the coordinate array and image data to be used for fitting then assemble a few guesses for the Gaussian parameters that describe the PSF, and pass the function, input array to the function, desired output from the function, an array-like data structure of guesses as p0. `scipy.optimie.curve_fit` is a very powerful and useful function but it has some very important quirks that result from the underlying mechanics, the Levenberg–Marquardt algorithm. Firstly, `curve_fit` has some restrictions on the input. The first argument must be a callable that that takes the input data as its first argument and outputs a 1-d array of floats with the same size as the desired output data. The input data can be anything with more entries than the function takes parameters, but the desired output data must be a 1-d array of floats. `curve_fit` proceeds by evaluating the function value at the initial parameters, and if none are given it uses Python's inspect module to find out how many parameters it should pass to the function. The caveat here is that if the function has a `*` attached to one of its arguments- that is, it can take any number of arguments- `curve_fit` cannot determine how many and it must be passed a parameter guess. `curve_fit` then evaluates the gradient around the initial values and uses that value to step toward where the sum of least squares is minimized. This has a few weaknesses. It's possible that the initial parameter guess is really bad and that the numerically evaluated gradient is zero, so the algorithm cannot determine what value to try next. The other problem that you may encounter is that the structure of the input and output data is very complex and that moving based on the gradient doesn't actually step towards the global minimum of the sum of residuals squared. *Both* problems can be solved by providing a better guess.

##Saving data
After fitting the star, save its parameters into the output array, and evaluate its PSF on the aperture for the visual output. Then use `np.save()` to save the numpy array, and `scipy.misc.imsave` which is a PIL (installed as pillow) wrapper.

There are two other options for saving. One is pickling, which is a built-in package that will let you save a Pyobject to a file and read it again later. The second is through shelve, also a built-in package. Shelve has the potential to let you save every variable currently active. While you should try to avoid shelve out of best practices, it has its uses.


#End of Python Introduction

That's pretty much it, you're ready to head out and do some astronomy with Python! If you have any complaints or suggestions for this manual or the sample resources, please post an issue.


#Advanced Python Notes

##Writing faster code

