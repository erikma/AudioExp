from python_speech_features import mfcc
from python_speech_features import delta
from python_speech_features import logfbank
import numpy
import scipy.io.wavfile as wav
import sys

class MfccWavLoader:
    """
    Loads a wav file and processes it, serving the resulting NumPy arrays for use
    in matching or training.
    """

    logFbankHeader = 'logFbank0,logFbank1,logFbank2,logFbank3,logFbank4,logFbank5,logFbank6,logFbank7,logFbank8,logFbank9,logFbank10,logFbank11'
    mfccHeader = 'mfcc1,mfcc2,mfcc3,mfcc4,mfcc5,mfcc6,mfcc7,mfcc8,mfcc9,mfcc10,mfcc11,mfcc12,mfcc13'
    mfccDerivativeHeader = 'mfccd1,mfccd2,mfccd3,mfccd4,mfccd5,mfccd6,mfccd7,mfccd8,mfccd9,mfccd10,mfccd11,mfccd12,mfccd13'
    mfcc2ndDerivativeHeader = 'mfcc2d1,mfcc2d2,mfcc2d3,mfcc2d4,mfcc2d5,mfcc2d6,mfcc2d7,mfcc2d8,mfcc2d9,mfcc2d10,mfcc2d11,mfcc2d12,mfcc2d13'

    def __init__(self, wavPath, mfccMaxRangeHz=None, produceLogFbank=False, produceFirstDerivative=False, produceSecondDerivative=False):
        self.wavPath = wavPath
        self.producedLogFbank = produceLogFbank

        # Convert the WAV file into monaural samples in a NumPy array.
        (rateHz, samples) = wav.read(wavPath)
        print("Loaded", wavPath, rateHz, "Hz")
        self.rateHz = rateHz

        # Calculate the MFCC features. https://github.com/jameslyons/python_speech_features#mfcc-features
        # We keep the defaults: 25ms frame window, 10ms step length, 13 cepstral coefficients calculated,
        # 26 filters in the MFCC filterbank, 512-sample FFT calculation size, 0 Hz low frequency,
        # rateHz/2 high frequency, 0.97 pre-emphasis filter, 22 lifter on final cepstral coefficients.
        # We avoid the appendEnergy parameter to ensure our use of convolutional filters over the 2D array
        # of MFCCs across time can find patterns in comparably scaled numbers.
        # We get back a NumPy array of 13 cepstral coefficients per row by a number of rows matching
        # the number of windows across the steps in the wave samples.
        self.mfccFeatures = mfcc(samples, rateHz, highfreq=mfccMaxRangeHz)

        if produceFirstDerivative:
            # Calculate the deltas (first derivative, velocity) as additional feature info. '2' is number of MFCC rows
            # before and after the current row whose samples are averaged to get the delta. 13 columns.
            self.mfccDeltas = delta(self.mfccFeatures, 2)

            if produceSecondDerivative:
                # Also useful is the delta-delta (second derivative, acceleration) calculated on the deltas. 13 columns.
                self.mfccDeltaDeltas = delta(self.mfccDeltas, 2)

        # Now that we're done with derivatives, normalize the original MFCC coefficients (but not the
        # energy column 0).
        # This is the same algorithm each frame of the MFCCs of an input sound stream
        # will need to use to match against these normalized values, producing far better results.
        self.normalizeMfccArray(self.mfccFeatures)

        if produceLogFbank:
            # Calculate log-MFCC-filterbank features from the original samples.
            # We keep the defaults: 25ms frame window, 10ms step length, 26 filters in the MFCC filterbank,
            # 512-sample FFT calculation size, 0 Hz low frequency, rateHz/2 high frequency,
            # 0.97 pre-emphasis filter, 22 lifter on final cepstral coefficients.
            # We get back a NumPy array of 26 log(filterbank) entries. We keep the first 12 per the
            # tutorial recommendation (later banks measure fast-changing harmonics in the high frequencies).
            logFbankFeatures = logfbank(samples, rateHz)
            self.logFbankFeatures = logFbankFeatures[:,1:13]
            self.fullFeatureArray = numpy.stack([ self.logFbankFeatures ], axis=-1)
            self.csvHeader = MfccWavLoader.logFbankHeader

        else:
            toStack = [ self.mfccFeatures ]
            self.csvHeader = MfccWavLoader.mfccHeader
            if produceFirstDerivative:
                toStack.append(self.mfccDeltas)
                self.csvHeader += "," + MfccWavLoader.mfccDerivativeHeader
                if produceSecondDerivative:
                    toStack.append(self.mfccDeltaDeltas)
                    self.csvHeader += "," + MfccWavLoader.mfcc2ndDerivativeHeader

            # Nx13xM
            self.fullFeatureArray = numpy.stack(toStack, axis=-1)

    def writeFullFeatureArrayToCsvStream(self, outStream):
        numpy.savetxt(sys.stdout, self.fullFeatureArray, delimiter=',', header=self.csvHeader, comments='')

    def normalizeMfccArray(self, mfccs):
        # Per http://www.cs.toronto.edu/%7Efritz/absps/waibelTDNN.pdf : Subtract from each coefficient
        # the average coefficient energy computed over all frames, then normalize each coefficient
        # to lie in [-1, 1]. This is the same algorithm each frame of the MFCCs of an input sound stream
        # will need to run to match against these normalized values, and produces far better results.
        avg = numpy.average(mfccs)
        numpy.subtract(mfccs, avg)
        mfccs /= numpy.max(numpy.abs(mfccs))
