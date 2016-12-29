import numpy as np


@profile
def last_axis():
    stack = np.empty(image.shape + (nimages,))
    for i in range(nimages):
        stack[..., i] = image
    result = np.median(stack, axis=-1, overwrite_input=True)


@profile
def first_axis():
    stack = np.empty((nimages,) + image.shape)
    for i in range(nimages):
        stack[i] = image
    result = np.median(stack, axis=0, overwrite_input=True)


image = np.random.rand(1024, 1024)
nimages = 100

last_axis()
first_axis()