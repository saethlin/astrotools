#Lesson 2: Flow control

From lesson 1, you should have some basic familiarity with Python syntax, be comfortable with assigning variables, and using `print()`. You should also be familiar with using astropy to open FITS files. Now we're going to extend those principles to write a basic data reduction program.

In particular, this lesson is about flow control. Previously, all you saw was statements executed in a single file, in the order they appear. This will suffice for simple problems, but often you may want to react to some input, or run some similar code many times or with slight variations.

##Interjection: Photometry data reduction
In the most general sense, we take 4 types of images: biases, darks, flats, and science images. A bias (or bias frame or bias image) is a zero second exposure that measures the what numbers the detector (in this case a CCD camera) records when no signal is present. A dark frame is an exposure taken with the camera's shutter closed; and thereby records only thermal electrons, which are produced at some approximately constant rate dependent on temperature and the properites of an individual pixel. A flat frame is an image taken of a uniformly illuminated object. The best way to do this is by taking images of the sky at sunrise and sunset, but sometimes it is done by taking images of a screen inside the telescope dome. Flats measure a combination of the pixel sensetivity variations and how well the detector is illuminated.

In general, the procedure is as follows: Combine bias frames and subtract the combined bias frames from everything. Combine dark frames, and subtract from flats and science images (possibly rescaling to match exposure time). Combine and normalize the flat field images, then divide the science images by the normalized flat. In the most optimal case, this simplifies to `reduced = (science - dark)/(flat/median(flat))`

# If statements
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
.