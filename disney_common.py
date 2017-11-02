import json
import hashlib
import numpy as np
from skopt.space.space import Integer, Space
from config import FIXED_PARAMS, FIXED_RANGES


def FCN(W, Sxi2, L):
    W_star = 1915820.
    return (1 + np.exp(10. * (W - W_star) / W_star)) * (
        1. + Sxi2) if W <= 3e6 else 1e8


def ParseParams(params_string):
    return [float(x) for x in params_string.strip('[]').split(',')]


def StripFixedParams(point):
    stripped_point = []
    pos = 0
    for low, high in FIXED_RANGES:
        stripped_point += point[:low-pos]
        point = point[high-pos:]
        pos = high
    _, high = FIXED_RANGES[-1]
    stripped_point += point[high-pos:]
    return stripped_point


def CreateDiscreteSpace():
    dZgap = 10
    zGap = dZgap / 2  # halflengh of gap
    dimensions = 8 * [
        Integer(170 + zGap, 300 + zGap)  # magnet lengths
        ] + 8 * (
            2 * [
                Integer(10, 100)  # dXIn, dXOut
            ] + 2 * [
                Integer(20, 200)  # dYIn, dYOut
            ] + 2 * [
                Integer(2, 70)  # gapIn, gapOut
            ])
    return Space(StripFixedParams(dimensions))


def AddFixedParams(point):
    _fixed_params = FIXED_PARAMS
    for low, high in FIXED_RANGES:
        point = point[0:low] + _fixed_params[:high-low] + point[low:]
        _fixed_params = _fixed_params[high-low:]
    return point


def create_id(params):
    params_json = json.dumps(params)
    h = hashlib.md5()
    h.update(params_json)
    return h.hexdigest()


def get_bounds():
    dZgap = 10.
    zGap = 0.5 * dZgap  # halflengh of gap
    minimum = 10.
    dXIn = (minimum, 250.)
    dXOut = (minimum, 250.)
    dYIn = (minimum, 250.)
    dYOut = (minimum, 250.)
    gapIn = (2., 100.)
    gapOut = (2., 100.)
    bounds = 6 * [(20. + zGap, 300. + zGap)
                  ] + 8 * [dXIn, dXOut, dYIn, dYOut, gapIn, gapOut]
    return bounds


def in_bounds(vector):
    for element, bound in zip(vector, get_bounds()):
        assert bound[0] <= element <= bound[
            1], '{} is not in bounds [{},{}]'.format(element, *bound)
