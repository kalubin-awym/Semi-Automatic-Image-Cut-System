# -*- coding: utf-8 -*-
"""
Created on Wed May  8 11:40:13 2019

@author: fredchizhou
"""
import os
import glob
import cv2
import shutil
import numpy as np
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk

# 检测图片是否旋转不匹配
def orientation_check(path):
    from PIL import Image, ExifTags
    img = Image.open(path)
    try:
        for orientation in ExifTags.TAGS.keys() : 
            if ExifTags.TAGS[orientation]=='Orientation' : break 
        exif=dict(img._getexif().items())
        if   exif[orientation] == 3 : 
            img=img.rotate(180, expand = True)
        elif exif[orientation] == 6 : 
            img=img.rotate(270, expand = True)
        elif exif[orientation] == 8 : 
            img=img.rotate(90, expand = True)   
        img.save(path, quality=96)
    except:
        pass

# floodFill算法
def fill_image(image, seedPoint, mask):
    dict = {"Blue": (50, 50, 50), "Green":(50, 30, 50)}
    key = "Blue"
    
    h, w = image.shape[:2]#读取图像的宽和高
    cv2.floodFill(image, mask, seedPoint, (0, 0, 0), dict[key], dict[key], 
                  cv2.FLOODFILL_FIXED_RANGE)
    return image, mask

# 区域抠图
def erease(array, points):
    if len(array.shape) == 2:
        for i in range(len(points)):
            x, y, w, h = points[i][1], points[i][0], points[i][3], points[i][2]
            array[x:x+w, y:y+h] = 0
    else:
        for i in range(array.shape[-1]):
            for j in range(len(points)):
                x, y, w, h = points[j][1], points[j][0], points[j][3], points[j][2]
                array[x:x+w, y:y+h, i] = 0

class Application(Frame):
    def __init__(self, master=None):
        self.file_paths = []
        self.cnt = 0
        self.points = []
        # 图片缩放比例和偏移量
        self.scale = 1
        self.bias = [0, 0]
        
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.rect_points = []
        
        Frame.__init__(self, master)
        self.pack(expand=YES, fill=BOTH)
        self.window_init()
        self.createWidgets()
    
    def window_init(self):
        self.master.title('Semi-Automatic Image-Cut System')
        width, height = self.master.maxsize()
        self.width, self.height = int(width*0.55), int(height*0.75)
        self.master.geometry("{}x{}".format(self.width, self.height))
    
    def get_pic(self, path): 
        orientation_check(path)
        image = Image.open(path)
        if image.size[0] > image.size[1]:
            self.scale = 500 / image.size[0]
            tmp = int(self.scale * image.size[1])
            self.bias = [0, 250 - tmp // 2]
            image = image.resize((500, tmp), Image.ANTIALIAS)
        else:
            self.scale = 500 / image.size[1]
            tmp = int(self.scale * image.size[0])
            self.bias = [250 - tmp // 2, 0]
            image = image.resize((tmp, 500), Image.ANTIALIAS)
        
        self.im = ImageTk.PhotoImage(image)
        self.canvas.delete('pic', 'point', 'rect')
        self.canvas.create_image(250, 250, image=self.im, tags='pic')
    
    ''' 获取文件夹下所有图片路径
    '''
    def get_directory_path(self):
        current_directory = filedialog.askdirectory()
        file_paths = current_directory + "/*.*"
        file_paths = glob.glob(file_paths)
        
        self.cnt = 0 # 计数清零
        self.file_paths = [i for i in file_paths if "png" in i or ".jp" in i]
        self.openEntry.delete(0, END)
        self.openEntry.insert(0, self.file_paths[self.cnt])
        
        self.dst_directory = current_directory
        self.openEntry1.delete(0, END)
        self.openEntry1.insert(0, self.dst_directory)
        # 添加图片
        self.get_pic(self.file_paths[self.cnt])
        
        # 绑定
        self.canvas.bind("<ButtonPress-1>", self.mouse_click)
        # 右键选框p图
        self.canvas.bind("<ButtonPress-3>", self.mouse_get_start_point)
        self.canvas.bind("<B3-Motion>", self.mouse_move)
        self.canvas.bind("<ButtonRelease-3>", self.mouse_release)

    ''' 获取目标文件夹
    '''
    def get_directory_path1(self):
        self.dst_directory = filedialog.askdirectory()
        self.openEntry1.delete(0,END)
        self.openEntry1.insert(0,self.dst_directory)


    ''' 获取单一图片文件路径
    '''        
    def get_file_path(self):
        file_path = filedialog.askopenfilename()
        
        self.cnt = 0
        self.file_paths = [file_path]
        self.openEntry.delete(0, END)
        self.openEntry.insert(0, file_path)
        
        self.dst_directory = file_path[: -len(file_path.split('/')[-1])]
        self.openEntry1.delete(0, END)
        self.openEntry1.insert(0, self.dst_directory)
        
        self.get_pic(file_path)
        # 绑定
        self.canvas.bind("<ButtonPress-1>", self.mouse_click)
        # 右键选框p图
        self.canvas.bind("<ButtonPress-3>", self.mouse_get_start_point)
        self.canvas.bind("<B3-Motion>", self.mouse_move)
        self.canvas.bind("<ButtonRelease-3>", self.mouse_release)
        
    ''' 保存并获取下一张图片路径
    ''' 
    def get_next_path(self):
        if os.path.exists("tmp.png"):
            # 保存图片
            shutil.move("tmp.png", os.path.join(self.dst_directory, self.file_paths[self.cnt].split('\\')[-1].split('.')[0]) + "-final.png")
        else:
            print('该图片未抠图 跳过')
        # 获取下一张
        self.cnt += 1
        self.points = []
        self.rect_points = []
        
        self.canvas.delete('pic', 'point', 'rect')
        if len(self.file_paths) > max(1, self.cnt):
            self.openEntry.delete(0,END)
            self.openEntry.insert(0,self.file_paths[self.cnt])
            self.get_pic(self.file_paths[self.cnt])
        else:
            self.cnt = len(self.file_paths) - 1
            self.openEntry.delete(0,END)
            self.openEntry.insert(0,'本次任务已完成')
            
            self.canvas.unbind("<ButtonPress-1>")
            self.canvas.unbind("<ButtonPress-3>")
            self.canvas.unbind("<B3-Motion>") 
            self.canvas.unbind("<ButtonRelease-3>")
    
    ''' 重新操作
    ''' 
    def reload_pic(self):
        self.points = []
        self.rect_points = []
        
        self.canvas.delete('pic', 'point')
        self.openEntry.delete(0,END)
        self.openEntry.insert(0,self.file_paths[self.cnt])
        self.get_pic(self.file_paths[self.cnt])
        
        
    
    ''' 刷新图片 进行抠图操作
    ''' 
    def refresh_pic(self):
        img = cv2.imread(self.file_paths[self.cnt])
        print(self.file_paths[self.cnt])
        
        h, w = img.shape[:2]
        mask = np.zeros([h+2, w+2], np.uint8)
        mask2 = np.ones(img.shape[:2],np.uint8)
        for i in range(len(self.points)):
            if self.points[i][0] <= h and self.points[i][1] <= w:
                img, mask = fill_image(img, self.points[i], mask)
        
        mask2 *= (1 - mask[1:-1,1:-1])
        #中值滤波去除噪点 medianBlur
        mask2 = cv2.medianBlur(mask2, 9)
        mask2 *= 255
        
        erease(mask2, self.rect_points)
        
        (B, G, R) = cv2.split(img)
        img = cv2.merge([B, G, R, mask2])
        cv2.imwrite("tmp.png", img)
        self.get_pic("tmp.png")
        
            
    ''' 鼠标点击获取坐标
    '''        
    def mouse_click(self, event):
        # event.x 鼠标左键的横坐标
        # event.y 鼠标左键的纵坐标
        x1, y1 = (event.x - 2), (event.y - 2)
        x2, y2 = (event.x + 2), (event.y + 2)
        self.canvas.create_oval(x1, y1, x2, y2, fill='red', tags='point')
        # 保存点坐标
        x_ = int(min(max(0, event.x - self.bias[0]), 500 - self.bias[0]) / self.scale)
        y_ = int(min(max(0, event.y - self.bias[1]), 500 - self.bias[1]) / self.scale)
        self.points.append((x_, y_))
        print([x_, y_])
        
    def mouse_get_start_point(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(event.x, event.y, event.x + 1, event.y + 1, outline='red', tags='rect')
        
    def mouse_move(self, event):
        # expand rectangle as you drag the mouse
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
    
    def mouse_release(self, event):
        # 坐标变换
        self.start_x = int(min(max(0, self.start_x - self.bias[0]), 500 - self.bias[0]) / self.scale)
        self.start_y = int(min(max(0, self.start_y - self.bias[1]), 500 - self.bias[1]) / self.scale)
        x = int(min(max(0, event.x - self.bias[0]), 500 - self.bias[0]) / self.scale)
        y = int(min(max(0, event.y - self.bias[1]), 500 - self.bias[1]) / self.scale)
        
        tmp = [min(self.start_x, x), min(self.start_y, y), abs(self.start_x - x), abs(self.start_y - y)]
        
        self.rect_points.append(tmp)
         
    def createWidgets(self):
        # fm1 标题
        self.fm1 = Frame(self)
        self.titleLabel = Label(self.fm1,text='半自动绿（蓝）幕抠图系统', font=('微软雅黑',16))
        self.titleLabel.pack()
        self.fm1.pack(side=TOP, fill='x', pady=5)
        
        # fm2 打开文件（夹）
        self.fm2 = Frame(self)
        Button(self.fm2, text='打开文件夹', width='12', command=self.get_directory_path).pack(side=LEFT)
        Button(self.fm2, text='打开文件', width='12', command=self.get_file_path).pack(side=LEFT)
        self.openEntry = Entry(self.fm2, width='56')
        self.openEntry.insert(0,"路径中不要包含中文字符")
        self.openEntry.pack(side=LEFT)
        self.fm2.pack(side=TOP)
        
        # fm3
        self.fm3 = Frame(self)
        Button(self.fm3, text='目标文件夹', width='25', command=self.get_directory_path1).pack(side=LEFT)
        self.openEntry1 = Entry(self.fm3, width='56')
        self.openEntry1.insert(0,"默认保存至输入文件路径")
        self.openEntry1.pack(side=LEFT)
        self.fm3.pack(side=TOP)
        
        # fm4
        self.fm4 = Frame(self) 
        self.canvas = Canvas(self.fm4, width = 500, height = 500)#bg = "white"
        bg = Image.open("bg.jpg")
        bg = bg.resize((500, 500), Image.ANTIALIAS)
        self.bg = ImageTk.PhotoImage(bg)
        self.canvas.create_image(250, 250, image=self.bg, tags='bg')
        #self.canvas.bind("<ButtonPress-1>", self.mouse_click)
        #self.canvas.bind("<B3-Motion>", self.mouse_move)
        #self.canvas.bind("<Button-1>", self.mouse_click)
        self.canvas.pack(side=LEFT) 
        self.fm4.pack(side=TOP)
        
        # fm5
        self.fm5 = Frame(self)
        Button(self.fm5, text='重新加载', width='12', command=self.reload_pic).pack(side=LEFT)
        Button(self.fm5, text='删除背景', width='12', command=self.refresh_pic).pack(side=LEFT)
        Button(self.fm5, text='保存/下一张', width='12', command=self.get_next_path).pack(side=LEFT)
        self.fm5.pack(side=TOP)
        
        # fm6
        text = '使用方法：\n1.点击 打开文件夹/打开文件 选择所需抠图的图片或图片文件夹 点击 目标文件夹 选择保存路径 默认路径与输入一致\n'
        text += '2.点击鼠标左键在图片中选择背景点，尽量选择在靠近前景边界周围的一圈背景点\n'
        text += '3.按住鼠标右键在图片中选择需要完整抠图的矩形区域\n'
        text += '4.点击 删除背景 查看预览结果\n5.重复步骤2-4，直至预览结果满意为止\n6.不满意可以点击 刷新 重新抠图\n7.点击 保存/下一张 自动保存结果并进入下一张，直至输出 当前任务已完成 抠图结束'
        text += '\n 注：直接点击 下一张/保存 则忽略当前图片'
        self.fm6 = Frame(self)
        Label(self.fm6, text=text, justify = LEFT, padx = 10).pack(side=LEFT)

        self.fm6.pack(side=TOP)

if __name__=='__main__':
    root = Tk()
    app = Application(root)
    # to do
    root.mainloop()