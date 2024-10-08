import os.path
#from data.base_dataset import BaseDataset, get_params, get_transform, normalize
from can_virtual_staining_for_high_thorughout_screening_generalize.src.can_virtual_staining_for_high_thorughout_screening_generalize.data.base_dataset import BaseDataset, get_params, get_transform, normalize
from data.image_folder import make_dataset
from PIL import Image
import numpy as np
import torch


class AlignedDataset(BaseDataset):
    def initialize(self, opt):
        self.opt = opt
        self.root = opt.dataroot

        # Input A (Brightfield images)
        self.dir_A = os.path.join(opt.dataroot,f'{opt.phase}_A') 
        self.A_paths = sorted(make_dataset(self.dir_A))

        # Input B (Real images)
        if opt.isTrain or opt.phase == 'val':
         
            self.dir_B = os.path.join(opt.dataroot,f'{opt.phase}_B')#opt.target, f'{opt.phase}')
            self.B_paths = sorted(make_dataset(self.dir_B))
      
        # instance maps
        if not opt.no_instance:
            self.dir_inst = os.path.join(opt.dataroot, opt.phase + '_inst')
            self.inst_paths = sorted(make_dataset(self.dir_inst))

        # load precomputed instance-wise encoded features
        if opt.load_features:
            self.dir_feat = os.path.join(opt.dataroot, opt.phase + '_feat')
            print('----------- loading features from %s ----------' % self.dir_feat)
            self.feat_paths = sorted(make_dataset(self.dir_feat))
        self.dataset_size = len(self.A_paths)

    def __getitem__(self, index):
        # Input A (Brightfield images)
        A_path = self.A_paths[index]
        A = Image.open(A_path)
        params = get_params(self.opt, A.size)
        if self.opt.label_nc == 0:
            transform_A = get_transform(self.opt, params)
            A_tensor = transform_A(A.convert('F').point(lambda p: p*(1/65535)))
        else:
            transform_A = get_transform(self.opt, params, method=Image.NEAREST, normalize=False)
            A_tensor = transform_A(A) * 255.0

        # Input B (real images)
        B_tensor = inst_tensor = feat_tensor = 0
        if self.opt.isTrain or self.opt.use_encoded_image:
            B_path = self.B_paths[index]
            B = Image.open(B_path).convert('F')
            transform_B = get_transform(self.opt, params)
            B_tensor = transform_B(B.point(lambda p: p*(1/65535)))

        ### if using instance maps
        if not self.opt.no_instance:
            inst_path = self.inst_paths[index]
            inst = Image.open(inst_path)
            inst_tensor = transform_A(inst)

            if self.opt.load_features:
                feat_path = self.feat_paths[index]
                feat = Image.open(feat_path).convert('RGB')
                norm = normalize()
                feat_tensor = norm(transform_A(feat))

        input_dict = {'label': A_tensor, 'inst': inst_tensor, 'image': B_tensor,
                      'feat': feat_tensor, 'path': A_path}

        return input_dict

    def __len__(self):
        return len(self.A_paths) // self.opt.batchSize * self.opt.batchSize

    def name(self):
        return "HTS Dataset"
