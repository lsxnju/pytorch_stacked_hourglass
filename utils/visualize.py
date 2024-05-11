import cv2

def visualization(img,kpts,mode=0):
    '''
    visualize the skelons on the ariginal img
    '''
    if mode ==0:
        color=(255,128,128)
    else:
        color=(0,255,0)
    skelenton = [[10, 11], [11, 12], [12, 8], [8, 13], [13, 14], [14, 15], [8, 9], [7, 8], [2, 6],
                 [3, 6], [1, 2], [1, 0], [3, 4], [4, 5],[6,7]]
    points_num = [num for num in range(1,16)]
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
        pos = (int(kpts[points-1][0]),int(kpts[points-1][1]))
        if mode ==0:
            if pos[0] > 0 and pos[1] > 0 :
                cv2.circle(img, pos,4,(0,0,255),-1) #为肢体点画红色实心圆
        else:
            if pos[0] > 0 and pos[1] > 0 and kpts[points-1][2]>1e-2 :
                cv2.circle(img, pos,4,(0,0,255),-1) #为肢体点画红色实心圆
    return img