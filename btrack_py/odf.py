import numpy as np
import scipy as sp

class ODF:
    def __init__(self, hop_size = 512, frame_size = 1024, odf_type=None, window=('kaiser',2.4)):
        self.hop_size = hop_size
        self.frame_size = frame_size

