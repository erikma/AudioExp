# WavToMfccFeatures - Converts a wav file into a comma-separated value list
# of Mel-Frequency Cepstral Coefficients.

from python_speech_features import mfcc
from python_speech_features import delta
from python_speech_features import logfbank
import numpy
import scipy.io.wavfile as wav
import sys

if len(sys.argv) < 2:
    print('First param must be a wav file path')
    exit(1)

# Convert the WAV file into monaural samples in a NumPy array.
(rateHz, samples) = wav.read(sys.argv[1])

# Calculate the MFCC features. https://github.com/jameslyons/python_speech_features#mfcc-features
# We keep the defaults: 25ms frame window, 10ms step length, 13 cepstral coefficients calculated,
# 26 filters in the MFCC filterbank, 512-sample FFT calculation size, 0 Hz low frequency,
# rateHz/2 high frequency, 0.97 pre-emphasis filter, 22 lifter on final cepstral coefficients.
# We do activate the appendEnergy feature to replace MFCC coefficient 0 with the log of the frame energy.
# We get back a NumPy array of 13 cepstral coefficients per row (first is the log of the frame total energy)
# by a number of rows matching the number of windows across the steps in the wave samples.
mfccFeatures = mfcc(samples, rateHz, appendEnergy=True)

# Calculate the deltas (first derivative, velocity) as additional feature info. '2' is number of MFCC rows
# before and after the current row whose samples are averaged to get the delta.
mfccDeltas = delta(mfccFeatures, 2)

# Also useful is the delta-delta (second derivative, acceleration) calculated on the deltas.
mfccDeltaDeltas = delta(mfccDeltas, 2)

# Calculate log-MFCC-filterbank features from the original samples.
# We keep the defaults: 25ms frame window, 10ms step length, 26 filters in the MFCC filterbank,
# 512-sample FFT calculation size, 0 Hz low frequency, rateHz/2 high frequency,
# 0.97 pre-emphasis filter, 22 lifter on final cepstral coefficients.
# We get back a NumPy array of 26 log(filterbank) entries. We keep the first 12 per the
# tutorial recommendation.
logFbankFeatures = logfbank(samples, rateHz)
logFbankFeatures = logFbankFeatures[:,1:13]

fullArray = numpy.concatenate([mfccFeatures, mfccDeltas, mfccDeltaDeltas, logFbankFeatures], axis=1)

print('offsetSec,logEnergy,mfcc1,mfcc2,mfcc3,mfcc4,mfcc5,mfcc6,mfcc7,mfcc8,mfcc9,mfcc10,mfcc11,mfcc12,' +
  'dLogEnergy,mfccd1,mfccd2,mfccd3,mfccd4,mfccd5,mfccd6,mfccd7,mfccd8,mfccd9,mfccd10,mfccd11,mfccd12,' +
  'logFbank0,logFbank1,logFbank2,logFbank3,logFbank4,logFbank5,logFbank6,logFbank7,logFbank8,logFbank9,logFbank10,logFbank11,logFbank12')
print(mfccFeatures[1:3,:])
print(mfccDeltas[1:3,:])
print(mfccDeltaDeltas[1:3,:])
print(logFbankFeatures[1:3,:])

print(fullArray[1:10,:])
