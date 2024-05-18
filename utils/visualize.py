import cv2
import numpy as np

def cal_torso(pos_head,pos_pelvis):
    return [pos_pelvis[0]+0.4*(pos_head[0]-pos_pelvis[0]),pos_pelvis[1]+0.4*(pos_head[1]-pos_pelvis[1]),0]

def visualization(img,kpts,mode=0):
    '''
    visualize the skelons on the ariginal img
    '''
    
    if mode ==0:
        color=(255,128,128)
    else:
        color=(0,255,0)
    # skelenton = [[10, 11], [11, 12], [12, 8], [8, 13], [13, 14], [14, 15], [8, 9], [7, 8], [2, 6],
    #              [3, 6], [1, 2], [1, 0], [3, 4], [4, 5],[6,7]]
    # torso 6-8,距离8 0.4
    pos_torso=cal_torso(kpts[8],kpts[6])

    kpts = np.vstack([kpts, np.array(pos_torso)])
    skelenton = [[10, 11], [11, 12], [12, 8], [8, 13], [13, 14], [14, 15], [8, 16],[2, 16],
                 [3, 16], [1, 2], [1, 0], [3, 4], [4, 5]]
    
    points_num = [num for num in range(0,17)]
    for sk in skelenton:
        pos1 = (int(kpts[sk[0]][0]), int(kpts[sk[0]][1]))
        pos2 = (int(kpts[sk[1]][0]), int(kpts[sk[1]][1]))
        if mode ==0:
            if pos1[0] > 0 and pos1[1] > 0 and pos2[0] > 0 and pos2[1] > 0:
                # print(sk)
                cv2.line(img, pos1, pos2, color, 2, 8)
        else:
            if pos1[0] > 0 and pos1[1] > 0 and pos2[0] > 0 and pos2[1] >  0 and kpts[sk[0]][2]>1e-2 and kpts[sk[1]][2]>1e-2:
                # print(sk)
                cv2.line(img, pos1, pos2, color, 2, 8)
    for points in points_num:
        pos = (int(kpts[points][0]),int(kpts[points][1]))
        if mode ==0:
            if pos[0] > 0 and pos[1] > 0 :
                cv2.circle(img, pos,4,(0,0,255),-1) #为肢体点画红色实心圆
                cv2.putText(img, str(points), (pos[0] + 5, pos[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)


        else:
            if pos[0] > 0 and pos[1] > 0 and kpts[points][2]>1e-2 :
                cv2.circle(img, pos,4,(0,0,255),-1) #为肢体点画红色实心圆
    return img