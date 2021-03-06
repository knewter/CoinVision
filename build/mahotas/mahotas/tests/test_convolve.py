import numpy as np
import mahotas.convolve
import mahotas._filters
from nose.tools import raises

def test_compare_w_ndimage():
    from scipy import ndimage
    A = np.arange(34*340).reshape((34,340))%3
    B = np.ones((3,3), A.dtype)
    for mode in mahotas._filters.modes:
        assert np.all(mahotas.convolve(A, B, mode=mode) == ndimage.convolve(A, B, mode=mode))

def test_22():
    A = np.arange(1024).reshape((32,32))
    B = np.array([
        [0,1],
        [2,3],
        ])
    C = np.array([
        [0,1,0],
        [2,3,0],
        [0,0,0],
        ])
    AB = mahotas.convolve(A,B)
    AC = mahotas.convolve(A,C)
    assert AB.shape == AC.shape
    assert np.all(AB == AC)


@raises(ValueError)
def test_mismatched_dims():
    f = np.arange(128*128, dtype=float).reshape((128,128))
    filter = np.arange(17,dtype=float)-8
    filter **= 2
    filter /= -16
    np.exp(filter,filter)
    mahotas.convolve(f,filter)
