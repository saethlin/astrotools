#Lesson 2: Flow control

From lesson 1, you should have some basic familiarity with Python syntax, be comfortable with assigning variables, and using `print()`. You should also be familiar with using astropy to open FITS files. Now we're going to extend those principles to write a basic data reduction program.

In particular, this lesson is about flow control. Previously, all you saw was statements executed in a single file, in the order they appear. This will suffice for simple problems, but often you may want to react to some input, or run some similar code many times or with slight variations.

##Aside: Photometry data reduction
In the most general sense, we take 4 types of images: biases, darks, flats, and science images. A bias (or bias frame or bias image) is a zero second exposure that measures the what numbers the detector (in this case a CCD camera) records when no signal is present. A dark frame is an exposure taken with the camera's shutter closed; and thereby records only thermal electrons, which are produced at some approximately constant rate dependent on temperature and the properites of an individual pixel. A flat frame is an image taken of a uniformly illuminated object. The best way to do this is by taking images of the sky at sunrise and sunset, but sometimes it is done by taking images of a screen inside the telescope dome. Flats measure a combination of the pixel sensetivity variations and how well the detector is illuminated.

In general, the procedure is as follows: Combine bias frames and subtract the combined bias frames from everything. Combine dark frames, and subtract from flats and science images (possibly rescaling to match exposure time). Combine and normalize the flat field images, then divide the science images by the normalized flat. In the most optimal case, this simplifies to `reduced = (science - dark)/(flat/median(flat))`

##Aside: Python lists
Python provides a few simple data structures that I will use often in demonstrations. They are actually quite useful, but incredibly inefficient for processing data compared to numpy ndarrays. The Python list can be constructed using two square brackets and separating values with commas. Anything can go in a list, including other lists. We'll do more with Python's basic data structures later.

#If statements
```
if condition:
    ...
```
Whatever code appears in the `...` will only be executed if `condition` evaluates to `True`. For example:
```
some_values = [4, 5, 'test']
if 'test' in some_values:
    print('found it!')
```
or
```
if 5*6 < 30:
    print('I broke math')
```
While you need to start with an `if`, other statements can follow it. For example:
```
if 'test' in some_values:
    print('found it')
else:
    print('noooooooo')
```
There can also be any number of `elif` statements between an `if` and an `else`, and there need not be an `else` after the last `elif`.

```
test_value = 40
if test_value < 10:
    print('huh')
elif test_value < 20:
    print('interesting')
elif test_value < 30:
    print('something new')
else:
    print('oh well')

print('this always runs')
```
The `if` and `elif` conditions are checked in the order they appear. If any of them evaluate to true, the code in the first true statement's block is run, and program executon skips to the end.

#For loops
```
for item in iterable:
    ...
```
The for loop in Python requires two things: a loop variable and something that is iterable. When the loop starts, the first value of `iterable` is assigned to `item` and the code in the block executes. At the end of the block, the next value in `iterable` is assigned to `item`, and the block runs again, until the end of `iterable` is reached. For example:
```
for filename in os.listdir('.'):
    print(filename)
print(filename)
```
Notice that the last name in the current directory is printed twice here. The loop variable retains the value of the last item in the iterable when the loop exits.

If you are familiar with other programming languages, this loop syntax may seem a bit unusual. This is because Python doesn't have a traditional for loop, instead it only has for each loops. This can be a bit unintuitive for those with other programming backgrounds, and people often fall into traps like:
```
for i in range(len(some_iterable)):
    print(some_iterable[i])
```
Where in Python we can just do
```
for item in some_iterable:
    print(item)
```
If you need to iterate across multiple iterables at once, you can do that using tuple unpacking and `zip` (or `izip`):
```
for name, date in zip(some_names, some_dates):
    print(name, date)
```

##Aside: Tuples and packing/unpacking
Along with lists, Python provides another basic data type, the tuple. Tuples are ordered and iterable like lists, but unlike lists cannot be modified once created. Lists can be appended to, tuples cannot. In the example above, I use `zip` to create another iterable of tuples, then unpack the tuples into name and date. Tuple unpacking can let you do clever things like swap the values of two variables:
```
x = 1
y = 2
x,y = y,x
print(x)
print(y)
```

If you really insist though that you need the indices of of the iterable you are iterating on, Python offers `enumerate`.
```
for f, filename in os.listdir('.'):
    print(f, filename)
```

#While loops
The while loop combines the loop idea with some boolean (true/false) test.

```
number = 1
while number < 10:
    number += 1
    print(number)
```

The danger with while loops is that you can put yourself in a situation where you write something like:
```
while test < 10:
    ...
    test = 5
    ...
    test += 1
```
This loop will never terminate. That's not inherently a bad thing, since Python provides two other keywords for working with loops: `break` and `continue`.

#Break and Continue
If you want to write a loop that runs at least once, you can do this with a while loop and `break`.
```
while True:
    ...
    if test_condition:
        break
```
The break keyword immediately exits the current loop. For example, this is still an infinite loop:
```
while True:
    while True:
        break
```
`continue` skips the rest of that loop iteration. For example:
```
for name in os.listdir('.')
    if name.endswith('.py'):
        continue
    print(name)
```
There is a much better way to accomplish what I just demonstrated with `continue`, but `continue` has very limited uses and I've personally only ever used it when debugging.

##Aside: Indentation
Python _requres_ indentation in a way most languges do not (except for scripting languages). This is known as significant whitespace, and can be a problem in some situations. For example, you can indent with tabs or spaces, but cannot mix them together within a single file. Most text editors can be configured to insert spaces when the tab key is pressed. PyCharm does this by default. Python doesn't specify how much to indent, only that you need to. Indention of 4 space is typical in Python, though some languages prefer 2 or 8. The usual argument is that 2 is not clear enough, and with 8 spaces you can spend a significant fraction of the screen's width on indentation.

#Data processing: Combining images

