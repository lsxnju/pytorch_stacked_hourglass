import time
import cv2
import torch
import tqdm
import os
import numpy as np
import h5py
import copy

from utils.group import HeatmapParser
import utils.img
from utils.visualize import *
import data.MPII.ref as ds

parser = HeatmapParser()

def post_process(det, mat_, trainval, c=None, s=None, resolution=None):
    mat = np.linalg.pinv(np.array(mat_).tolist() + [[0,0,1]])[:2]
    res = det.shape[1:3]
    cropped_preds = parser.parse(np.float32([det]))[0]
    
    if len(cropped_preds) > 0:
        cropped_preds[:,:,:2] = utils.img.kpt_affine(cropped_preds[:,:,:2] * 4, mat) #size 1x16x3
        
    preds = np.copy(cropped_preds)
    ##for inverting predictions from input res on cropped to original image

    if trainval != 'cropped':
        for j in range(preds.shape[1]):
            preds[0,j,:2] = utils.img.transform(preds[0,j,:2], c, s, resolution, invert=1)

    return preds

def inference(img, func, config, c, s):
    """
    forward pass at test time
    calls post_process to post process results
    """
    
    height, width = img.shape[0:2]
    center = (width/2, height/2)
    scale = max(height, width)/200
    res = (config['train']['input_res'], config['train']['input_res'])

    mat_ = utils.img.get_transform(center, scale, res)[:2]
    inp = img/255

    def array2dict(tmp):
        return {
            'det': tmp[0][:,:,:16],
        }

    tmp1 = array2dict(func([inp]))
    tmp2 = array2dict(func([inp[:,::-1]]))

    tmp = {}
    for ii in tmp1:
        tmp[ii] = np.concatenate((tmp1[ii], tmp2[ii]),axis=0)

    det = tmp['det'][0, -1] + tmp['det'][1, -1, :, :, ::-1][ds.flipped_parts['mpii']]
    if det is None:
        return [], []
    det = det/2

    det = np.minimum(det, 1)
    
    return post_process(det, mat_, 'valid', c, s, res)

def mpii_eval(pred, gt, normalizing, num_train, bound=0.5):
    """
    Use PCK with threshold of .5 of normalized distance (presumably head size)
    """

    correct = {'all': {'total': 0, 'ankle': 0, 'knee': 0, 'hip': 0, 'pelvis': 0, 
               'thorax': 0, 'neck': 0, 'head': 0, 'wrist': 0, 'elbow': 0, 
               'shoulder': 0},
               'visible': {'total': 0, 'ankle': 0, 'knee': 0, 'hip': 0, 'pelvis': 0, 
               'thorax': 0, 'neck': 0, 'head': 0, 'wrist': 0, 'elbow': 0, 
               'shoulder': 0},
               'not visible': {'total': 0, 'ankle': 0, 'knee': 0, 'hip': 0, 'pelvis': 0, 
               'thorax': 0, 'neck': 0, 'head': 0, 'wrist': 0, 'elbow': 0, 
               'shoulder': 0}}
    count = copy.deepcopy(correct)
    correct_train = copy.deepcopy(correct)
    count_train = copy.deepcopy(correct)
    idx = 0
    for p, g, normalize in zip(pred, gt, normalizing):
        for j in range(g.shape[1]):
            vis = 'visible'
            if g[0,j,0] == 0: ## not in picture!
                continue
            if g[0,j,2] == 0:
                vis = 'not visible'
            joint = 'ankle'
            if j==1 or j==4:
                joint = 'knee'
            elif j==2 or j==3:
                joint = 'hip'
            elif j==6:
                joint = 'pelvis'
            elif j==7:
                joint = 'thorax'
            elif j==8:
                joint = 'neck'
            elif j==9:
                joint = 'head'
            elif j==10 or j==15:
                joint = 'wrist'
            elif j==11 or j==14:
                joint = 'elbow'
            elif j==12 or j==13:
                joint = 'shoulder'

            if idx >= num_train:
                count['all']['total'] += 1
                count['all'][joint] += 1
                count[vis]['total'] += 1
                count[vis][joint] += 1
            else:
                count_train['all']['total'] += 1
                count_train['all'][joint] += 1    
                count_train[vis]['total'] += 1
                count_train[vis][joint] += 1    
            error = np.linalg.norm(p[0]['keypoints'][j,:2]-g[0,j,:2]) / normalize
            if idx >= num_train:
                if bound > error:
                    correct['all']['total'] += 1
                    correct['all'][joint] += 1
                    correct[vis]['total'] += 1
                    correct[vis][joint] += 1
            else:
                if bound > error:
                    correct_train['all']['total'] += 1
                    correct_train['all'][joint] += 1
                    correct_train[vis]['total'] += 1
                    correct_train[vis][joint] += 1  
        idx += 1
    
    ## breakdown by validation set / training set
    for k in correct:
        print(k, ':')
        for key in correct[k]:
            print('Val PCK @,', bound, ',', key, ':', round(correct[k][key] / max(count[k][key],1), 3), ', count:', count[k][key])
            print('Tra PCK @,', bound, ',', key, ':', round(correct_train[k][key] / max(count_train[k][key],1), 3), ', count:', count_train[k][key])
        print('\n')
            
def get_img(config, num_eval=2958, num_train=300):
    '''
    Load validation and training images
    '''
    input_res = config['train']['input_res']
    output_res = config['train']['output_res']
    val_f = h5py.File(os.path.join(ds.annot_dir, 'valid.h5'), 'r')
    
    tr = tqdm.tqdm( range(0, num_train), total = num_train )
    ## training
    train_f = h5py.File(os.path.join(ds.annot_dir, 'train.h5') ,'r')
    for i in tr:
        path_t = '%s/%s' % (ds.img_dir, train_f['imgname'][i].decode('UTF-8'))        
        
        ## img
        orig_img = cv2.imread(path_t)[:,:,::-1]
        c = train_f['center'][i]
        s = train_f['scale'][i]
        im = utils.img.crop(orig_img, c, s, (input_res, input_res))
        
        ## kp
        kp = train_f['part'][i]
        vis = train_f['visible'][i]
        kp2 = np.insert(kp, 2, vis, axis=1)
        kps = np.zeros((1, 16, 3))
        kps[0] = kp2
        
        ## normalize (to make errors more fair on high pixel imges)
        n = train_f['normalize'][i]
        
        yield kps, im, c, s, n, orig_img[:,:,::-1]
                
    
    tr2 = tqdm.tqdm( range(0, num_eval), total = num_eval )
    ## validation
    for i in tr2:
        path_t = '%s/%s' % (ds.img_dir, val_f['imgname'][i].decode('UTF-8')) 
        
        ## img
        orig_img = cv2.imread(path_t)[:,:,::-1]
        c = val_f['center'][i]
        s = val_f['scale'][i]
        im = utils.img.crop(orig_img, c, s, (input_res, input_res))
        
        ## kp
        kp = val_f['part'][i]
        vis = val_f['visible'][i]
        kp2 = np.insert(kp, 2, vis, axis=1)
        kps = np.zeros((1, 16, 3))
        kps[0] = kp2
        
        ## normalize (to make errors more fair on high pixel imgs)
        n = val_f['normalize'][i]
        
        yield kps, im, c, s, n, orig_img[:,:,::-1]
    

def main():
    from train import init
    print("-"*10+"start_init"+"-"*10)
    func, config = init()

    def runner(imgs):
        return func(0, config, 'inference', imgs=torch.Tensor(np.float32(imgs)))['preds']

    def do(img, c, s):
        print(img.shape,c,s)
        ans = inference(img, runner, config, c, s)
        if len(ans) > 0:
            ans = ans[:,:,:3]

        ## ans has shape N,16,3 (num preds, joints, x/y/visible)
        pred = []
        for i in range(ans.shape[0]):
            pred.append({'keypoints': ans[i,:,:]})
        return pred
    
    print("-"*10+"start_test"+"-"*10)
    gts = []    # groundtruth
    preds = []  # prediction
    normalizing = []    # normalizing
    
    num_eval = config['inference']['num_eval']
    num_train = config['inference']['train_num_eval']
    num_eval=20
    num_train=20
    i=0 # index
    with open(f'log/{time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())}.txt','w') as f:
        for anns, img, c, s, n, oim in get_img(config, num_eval, num_train):
            gts.append(anns)
            f.write(f'i: {i} c: {str(c)} s: {str(s)} shape: {img.shape}\n')

            pred = do(img, c, s)

            preds.append(pred)
            normalizing.append(n)
            img_visual_gt = visualization(oim,anns[0],mode=0)
            cv2.imwrite(f'./img_output/crop/crop_{i}.png',img[:,:,::-1])
            cv2.imwrite(f'./img_output/gt/gt_{i}.png',img_visual_gt)
            img_visual_predict = visualization(img_visual_gt,pred[0]['keypoints'],mode=1)
            cv2.imwrite(f'./img_output/predict/net_{i}.png',img_visual_predict)
            i+=1

    mpii_eval(preds, gts, normalizing, num_train)

def test_owndata(path_dataset):
    from train import init
    print("-"*10+"start_init"+"-"*10)
    func, config = init()

    def runner(imgs):
        return func(0, config, 'inference', imgs=torch.Tensor(np.float32(imgs)))['preds']
    
    def do(img,c,s):

        ans = inference(img, runner, config, c, s)
        if len(ans) > 0:
            ans = ans[:,:,:3]

        ## ans has shape N,16,3 (num preds, joints, x/y/visible)
        pred = []
        for i in range(ans.shape[0]):
            pred.append({'keypoints': ans[i,:,:]})
        return pred

    def get_img_selfmade(config,path_t):
        input_res = config['train']['input_res']
        output_res = config['train']['output_res']
        ## img
        orig_img = cv2.imread(path_t)[:,:,::-1]
        c =[536,288]
        s = 3
        im = utils.img.crop(orig_img, c, s, (input_res, input_res))
        

        return  im, c, s, orig_img[:,:,::-1]
    i=0
    list_pred=[]
    # with open(f'log/selfmadedataset_{time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())}.txt','w') as f:
    for img_file in os.listdir(path_dataset):
        print(img_file)
        img, c, s, oim=get_img_selfmade(config=config, path_t=os.path.join(path_dataset,img_file))

        pred = do(img, c, s)

        pos_torso=cal_torso(pred[0]['keypoints'][8],pred[0]['keypoints'][6])
        kpts = np.vstack([pred[0]['keypoints'], np.array(pos_torso)])
        bool_indices = np.array([True]*6+[False]*2+[True]+[False]+[True]*7)
        list_pred.append( kpts[bool_indices])
        # img_visual_gt = visualization(oim,pred[0]['keypoints'],mode=0)
        # cv2.imwrite(f'./img_output/predict_selfmade/selfmade_{i}.png',img_visual_gt)
        i+=1
    array_3d = np.array(list_pred)

    # 保存到.npy文件
    np.save('array_3d.npy', array_3d)

    
if __name__ == '__main__':
    # main()
    path_dataset=r'/Users/shuixianli/Desktop/dissertation/pytorch_stacked_hourglass/data/selfmade'
    test_owndata(path_dataset)
    