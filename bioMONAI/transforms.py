# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/04_transforms.ipynb.

# %% auto 0
__all__ = ['RandCrop2D', 'RandCropND', 'RandFlip', 'RandRot90']

# %% ../nbs/04_transforms.ipynb 3
from fastai.vision.all import *
from fastai.data.all import *
from monai.transforms import SpatialCrop, Flip, Rotate90

# %% ../nbs/04_transforms.ipynb 7
def _process_sz(size, ndim=3):
    if isinstance(size,int): 
        size=(size,)*ndim
    return fastuple(size)

def _get_sz(x):
    if isinstance(x, tuple): x = x[0]
    if not isinstance(x, Tensor): return fastuple(x.size)
    return fastuple(getattr(x, 'img_size', getattr(x, 'sz', (x.shape[1:])))) # maybe it should swap x and y axes 

# %% ../nbs/04_transforms.ipynb 11
class RandCrop2D(RandTransform):
    "Randomly crop an image to `size`"
    split_idx,order = None,1
    def __init__(self, 
        size:int|tuple, # Size to crop to, duplicated if one value is specified
        lazy = False,   # a flag to indicate whether this transform should execute lazily or not. Defaults to False
        **kwargs
    ):
        size = _process_sz(size, ndim=2)
        store_attr()
        super().__init__(**kwargs)

    def before_call(self, 
        b, 
        split_idx:int # Index of the train/valid dataset
    ):
        "Randomly positioning crop if train dataset else center crop"
        self.orig_sz = _get_sz(b)
        if split_idx: self.ctr = (self.orig_sz)//2
        else:
            wd = self.orig_sz[0] - self.size[0]
            hd = self.orig_sz[1] - self.size[1]
            w_rand = (wd, -1) if wd < 0 else (0, wd)
            h_rand = (hd, -1) if hd < 0 else (0, hd)
            self.ctr = fastuple(random.randint(*w_rand)+self.size[0]//2, random.randint(*h_rand)+self.size[1]//2)

    def encodes(self, x):
        return SpatialCrop(roi_center=self.ctr, roi_size=self.size, lazy=self.lazy)(x)

# %% ../nbs/04_transforms.ipynb 13
class RandCropND(RandTransform):
    """
    Randomly crops an ND image to a specified size.

    This transform randomly crops an ND image to a specified size during training and performs
    a center crop during validation. It supports both 2D and 3D images and videos, assuming
    the first dimension is the batch dimension.

    Args:
        size (int or tuple): The size to crop the image to. this can have any number of dimensions. 
                             If a single value is provided, it will be duplicated for each spatial 
                             dimension, up to a maximum of 3 dimensions.
        **kwargs: Additional keyword arguments to be passed to the parent class.
    """

    split_idx,order = None,1
        
    def __init__(self, size: int | tuple, # Size to crop to, duplicated if one value is specified
                 lazy = False,            # a flag to indicate whether this transform should execute lazily or not. Defaults to False
                 **kwargs):
        size = _process_sz(size)
        store_attr()
        super().__init__(**kwargs)

    def before_call(self, b, split_idx: int):
        "Randomly position crop if train dataset else center crop"
        self.orig_sz = _get_sz(b)
        if split_idx:
            self.tl = tuple((osz - sz) // 2 for osz, sz in zip(self.orig_sz, self.size))
            self.br = tuple((osz + sz) // 2 for osz, sz in zip(self.orig_sz, self.size))
        else:
            tl = [] # top-left corner
            br = [] # bottom-right corner
            # Calculate top-left and bottom-right corner coordinates for random crop
            for osz, sz in zip(self.orig_sz, self.size):
                w_dif = osz - sz
                if w_dif < 0:
                    w_rand = (0, 0) # No random cropping if input size is smaller than crop size
                    sz = osz # Adjust crop size to match input size
                else:
                    w_rand = (0, w_dif)
                rnd = random.randint(*w_rand)
                tl.append(rnd)
                br.append(rnd + sz)
            self.tl = fastuple(*tl)
            self.br = fastuple(*br)

    def encodes(self, x):
        "Apply spatial crop transformation to the input image."
        return SpatialCrop(roi_start=self.tl, roi_end=self.br, lazy=self.lazy)(x)
    

# %% ../nbs/04_transforms.ipynb 16
class RandFlip(RandTransform):
    """
    Randomly flips an ND image over a specified axis.

    """

    split_idx,order = None,1
        
    def __init__(self, 
                 prob = 0.1,            # Probability of flipping
                 spatial_axis = None,   # Spatial axes along which to flip over. Default is None. The default axis=None will flip over all of the axes of the input array. 
                                        # If axis is negative it counts from the last to the first axis. If axis is a tuple of ints, flipping is performed on all of the axes specified in the tuple.
                 ndim = 2,
                 lazy = False,          # Flag to indicate whether this transform should execute lazily or not. Defaults to False
                 **kwargs):
        store_attr()
        super().__init__(**kwargs)

    def before_call(self, b, split_idx: int):
        if split_idx:
            self.flip = 0
        else:
            self.flip = np.random.choice([0, 1], p=[1-self.prob, self.prob])
        if self.spatial_axis is None:
            self.spatial_axis = np.random.choice(np.arange(self.ndim), size=np.random.randint(1, self.ndim+1), replace=False, p=None)
            
    def encodes(self, x):
        if self.flip:
            return Flip(spatial_axis=self.spatial_axis, lazy=self.lazy)(x)
        else:
            return x

# %% ../nbs/04_transforms.ipynb 19
class RandRot90(RandTransform):
    """
    Randomly rotate an ND image by 90 degrees in the plane specified by axes.

    """

    split_idx,order = None,1
        
    def __init__(self, 
                 prob = 0.1,            # Probability of rotating
                 max_k = 3,             # Max number of times to rotate by 90 degrees
                 spatial_axes = (0, 1),   # Spatial axes along which to rotate. Default: (0, 1), this is the first two axis in spatial dimensions.
                 ndim = 2,
                 lazy = False,          # Flag to indicate whether this transform should execute lazily or not. Defaults to False
                 **kwargs):
        store_attr()
        super().__init__(**kwargs)

    def before_call(self, b, split_idx: int):
        if split_idx:
            self.rot90 = 0
        else:
            self.rot90 = np.random.choice([0, 1], p=[1-self.prob, self.prob])
            self.k = 1 + np.random.randint(self.max_k)
        # if self.spatial_axes is None:
        #     self.spatial_axes = np.random.choice(np.arange(self.ndim), size=np.random.randint(1, self.ndim+1), replace=False, p=None)
            
    def encodes(self, x):
        if self.rot90:
            return Rotate90(k=self.k, spatial_axes=self.spatial_axes, lazy=self.lazy)(x)
        else:
            return x