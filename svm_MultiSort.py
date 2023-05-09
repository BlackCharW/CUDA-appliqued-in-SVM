
import random

import numpy as np
from matplotlib import pyplot as plt



def load_data(filename):
    dataset, labels = [], []
    with open(filename, 'r') as f:
        for line in f:
            x,y,lab = [float(i) for i in line.strip().split()]
            dataset.append([x,y])
            labels.append(lab)
    return dataset, labels

def clip(alpha, L, H):
    ''' 修建alpha的值到L和H之间.
    '''
    if alpha < L:
        return L
    elif alpha > H:
        return H
    else:
        return alpha

def select_j(i, m):
    ''' 在m中随机选择除了i之外剩余的数
    '''
    l = list(range(m))
    seq = l[: i] + l[i+1:]
    return random.choice(seq)


def calcEk(alphas,labels,b,k):
    fxk = float(np.multiply())
    
    return Ek







if '__main__' == __name__:
    # 加载训练数据
    dataset, labels = load_data('testSet.txt')
    # 使用简化版SMO算法优化SVM
    alphas, b = simple_smo(dataset, labels, 0.6, 10)
    print(alphas,b)