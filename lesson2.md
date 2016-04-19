#Lesson 2: Flow control

From lesson 1, you should have some basic familiarity with Python syntax, be comfortable with assigning variables, and using `print()`. You should also be familiar with using astropy to open FITS files. Now we're going to extend those principles to write a basic data reduction program.

##Basic data reduction
In the most general sense, we take 4 types of images: biases, darks, flats, and science images. A bias (or bias frame or bias image) is a zero second exposure that measures the what numbers the detector (in this case a CCD camera) records when no signal is present. A dark frame records what signal the detector picks up from thermal