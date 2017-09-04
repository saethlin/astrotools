import numpy as np


@profile
def list_comp():
    return np.median(np.moveaxis(np.array([image for _ in range(nimages)]), 0, 2), axis=-1)


@profile
def last_axis():
    stack = np.zeros(image.shape + (nimages,))
    for i in range(nimages):
        stack[..., i] = image
    return np.median(stack, axis=-1, overwrite_input=True)


@profile
def first_axis():
    stack = np.zeros((nimages,) + image.shape)
    for i in range(nimages):
        stack[i] = image
    return np.median(stack, axis=0, overwrite_input=True)


image = np.random.rand(1024, 1024)
nimages = 100

print(np.all(last_axis() == list_comp()))
