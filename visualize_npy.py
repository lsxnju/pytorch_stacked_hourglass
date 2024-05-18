from utils.visualize import *
import numpy as np

array=np.load('/Users/shuixianli/Desktop/dissertation/pytorch_stacked_hourglass/array_3d.npy')


import cv2
import numpy as np

# 示例数据：假设我们有一个 n*14*2 的 NumPy 数组
n = array.shape[0]  # 示例图片数量

# 视频参数
frame_width = 1250  # 图像宽度
frame_height = 720  # 图像高度
fps = 15  # 帧率 (66 ms 间隔约等于 15 FPS)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 编码格式

# 创建视频写入对象
video_writer = cv2.VideoWriter('output_video.mp4', fourcc, fps, (frame_width, frame_height))
skelenton = [[7, 8], [8, 9], [9, 6], [6, 10], [10, 11], [11, 12], [6, 13],[2, 13],
                 [3, 13], [1, 2], [1, 0], [3, 4], [4, 5]]
# 生成每一帧图像并写入视频
for i in range(n):
    # 创建一个空白图像
    img = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
    
    # 获取当前帧的14个点
    points = array[i]
    for sk in skelenton:
        pos1 = (int(points[sk[0]][0]), int(points[sk[0]][1]))
        pos2 = (int(points[sk[1]][0]), int(points[sk[1]][1]))
        if pos1[0] > 0 and pos1[1] > 0 and pos2[0] > 0 and pos2[1] > 0:
            # print(sk)
            cv2.line(img, pos1, pos2,(255, 0, 255), 2, 8)

    # 在图像上绘制点
    for point in points:
        cv2.circle(img, (int(point[0]), int(point[1])), 5, (0, 0, 255), -1)
    print(int(point[0]), int(point[1]))
    # 将帧写入视频
    video_writer.write(img)

# 释放视频写入对象
video_writer.release()

print('视频生成完成')
