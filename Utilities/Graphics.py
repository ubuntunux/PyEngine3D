import numpy as np


# https://github.com/TheRealMJP/SamplePattern/blob/master/SamplePattern.cpp
# Computes a radical inverse with base 2 using crazy bit-twiddling from "Hacker's Delight"
def RadicalInverseBase2(bits):
    bits = (bits << 16) | (bits >> 16)
    bits = ((bits & 0x55555555) << 1) | ((bits & 0xAAAAAAAA) >> 1)
    bits = ((bits & 0x33333333) << 2) | ((bits & 0xCCCCCCCC) >> 2)
    bits = ((bits & 0x0F0F0F0F) << 4) | ((bits & 0xF0F0F0F0) >> 4)
    bits = ((bits & 0x00FF00FF) << 8) | ((bits & 0xFF00FF00) >> 8)
    return float(bits) * 2.3283064365386963e-10


# Returns a single 2D point in a Hammersley sequence of length "numSamples", using base 1 and base 2
def Hammersley2D(sampleIdx, numSamples):
    return float(sampleIdx) / float(numSamples), RadicalInverseBase2(sampleIdx)
