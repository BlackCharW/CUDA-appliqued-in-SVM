#smo实现
from fileinput import filename
import pandas as pd

# 辅助函数，在(0,m)区间范围内随机选择一个不等于i的整数
from numpy import *

def load_data(filename):
    dataset, labels = [], []
    with open(filename, 'r') as f:
        for line in f:
            data = [float(i) for i in line.split(' ')]
            dataset.append(data[:-1])
            labels.append(data[-1])
    return dataset, labels



def selectJrand(i,m):
    j=i
    # 注意返回的随机整数不应该等于i
    while (j==i):
        j = int(random.uniform(0,m))
    return j

# 辅助函数，调整数值大于H或小雨L的alpha值
# 为alpha值设定上下限
def clipAlpha(aj,H,L):
    if aj > H: 
        aj = H
    if L > aj:
        aj = L
    return aj

# 辅助函数，对于给定的alpha值，计算E值并返回
def calcEk(oS, k):
    fXk = float(multiply(oS.alphas,oS.labelMat).T*oS.K[:,k] + oS.b)
    Ek = fXk - float(oS.labelMat[k])
    return Ek

# 辅助函数，用来选择第二个alpha值并保证每次优化中采用最大步长
def selectJ(i, oS, Ei):
    maxK = -1; maxDeltaE = 0; Ej = 0

    # 将输入的Ei在误差缓存中设置为已经计算好的
    oS.eCache[i] = [1,Ei]

    # 构建一个非零表
    validEcacheList = nonzero(oS.eCache[:,0].A)[0]
    if (len(validEcacheList)) > 1:
        # 循环查找最大步长的Ej
        for k in validEcacheList:
            if k == i: continue #don't calc for i, waste of time
            Ek = calcEk(oS, k)
            deltaE = abs(Ei - Ek)
            if (deltaE > maxDeltaE):
                maxK = k; maxDeltaE = deltaE; Ej = Ek
        return maxK, Ej
    else:
        # 如果是第一次循环
        # 随机选择一个alpha值，并计算Ej
        j = selectJrand(i, oS.m)
        Ej = calcEk(oS, j)
    return j, Ej

# 辅助函数，当alpha优化后更新误差缓存
def updateEk(oS, k):
    Ek = calcEk(oS, k)
    oS.eCache[k] = [1,Ek]

# 核转换函数，参数为两个数值和一个元组kTup（记录核函数信息）
def kernelTrans(X, A, kTup):
    # 建立列向量
    m,n = shape(X)
    K = mat(zeros((m,1)))

    # 根据不同的核函数类型，给出两种类型的实现
    if kTup[0]=='lin': K = X * A.T
    elif kTup[0]=='rbf':
        for j in range(m):
            deltaRow = X[j,:] - A
            K[j] = deltaRow*deltaRow.T
        K = exp(K/(-1*kTup[1]**2))
    # 无法识别的核函数类型
    else: raise NameError('Houston We Have a Problem -- \
    That Kernel is not recognized')
    return K

# 数据及参数存储
class optStruct:
    def __init__(self,dataMatIn, classLabels, C, toler, kTup):
        
        self.X = dataMatIn
        self.labelMat = classLabels
        self.C = C
        self.tol = toler
        self.m = shape(dataMatIn)[0]
        print("m",self.m)
        self.alphas = mat(zeros((self.m,1)))
        self.b = 0
        self.eCache = mat(zeros((self.m,2))) #first column is valid flag
        self.K = mat(zeros((self.m,self.m)))
        for i in range(self.m):
            print("hdh")
            self.K[:,i] = kernelTrans(self.X, self.X[i,:], kTup)

# 寻找决策边界的优化例程函数
def innerL(i, oS):
    # 根据alpha计算Ei值
    Ei = calcEk(oS, i)

    # 根据误差Ei判断alpha是否可以被优化
    if ((oS.labelMat[i]*Ei < -oS.tol) and (oS.alphas[i] < oS.C)) or ((oS.labelMat[i]*Ei > oS.tol) and (oS.alphas[i] > 0)):
        # 选择第二个alpha值
        j,Ej = selectJ(i, oS, Ei)
        alphaIold = oS.alphas[i].copy(); alphaJold = oS.alphas[j].copy()

        # 保证alpha值范围在0-C区间
        if (oS.labelMat[i] != oS.labelMat[j]):
            L = max(0, oS.alphas[j] - oS.alphas[i])
            H = min(oS.C, oS.C + oS.alphas[j] - oS.alphas[i])
        else:
            L = max(0, oS.alphas[j] + oS.alphas[i] - oS.C)
            H = min(oS.C, oS.alphas[j] + oS.alphas[i])

        if L==H: print ("L==H"); return 0

        # 计算alpha[j]的最优修改量
        eta = 2.0 * oS.K[i,j] - oS.K[i,i] - oS.K[j,j] 
        if eta >= 0: print ("eta>=0"); return 0
        oS.alphas[j] -= oS.labelMat[j]*(Ei - Ej)/eta
        oS.alphas[j] = clipAlpha(oS.alphas[j],H,L)
        updateEk(oS, j) #added this for the Ecache
        if (abs(oS.alphas[j] - alphaJold) < 0.00001): print ("j not moving enough"); return 0

        # 对i进行修改，修改量与j相同，但方向相反
        oS.alphas[i] += oS.labelMat[j]*oS.labelMat[i]*(alphaJold - oS.alphas[j])
        updateEk(oS, i)

        # 计算并设置常数项b
        b1 = oS.b - Ei- oS.labelMat[i]*(oS.alphas[i]-alphaIold)*oS.K[i,i] - oS.labelMat[j]*(oS.alphas[j]-alphaJold)*oS.K[i,j]
        b2 = oS.b - Ej- oS.labelMat[i]*(oS.alphas[i]-alphaIold)*oS.K[i,j]- oS.labelMat[j]*(oS.alphas[j]-alphaJold)*oS.K[j,j]
        if (0 < oS.alphas[i]) and (oS.C > oS.alphas[i]): oS.b = b1
        elif (0 < oS.alphas[j]) and (oS.C > oS.alphas[j]): oS.b = b2
        else: oS.b = (b1 + b2)/2.0

        # alpha被优化则返回1
        return 1

    else: return 0

# 完整的Platt SMO算法
def smoP(dataMatIn, classLabels, C, toler, maxIter,kTup=('lin', 0)):
    # 初始化`optStruct`，将输入参数存入数据对象
    print(dataMatIn)
    oS = optStruct(mat(dataMatIn),mat(classLabels).transpose(),C,toler, kTup)

    # 初始化控制函数退出的变量
    iter = 0
    entireSet = True; alphaPairsChanged = 0
    print("hhh")

    # 进入主体while循环
    # 设置多个循环退出条件，例如迭代达到最大次数或遍历集合后未修改任何alpha值时候退出
    while (iter < maxIter) and ((alphaPairsChanged > 0) or (entireSet)):
        print("ere")
        alphaPairsChanged = 0
        if entireSet:
            # 遍历任何可能的alpha值
            for i in range(oS.m): 
                alphaPairsChanged += innerL(i,oS)
                print ("fullSet, iter: %d i:%d, pairs changed %d" % (iter,i,alphaPairsChanged))
            iter += 1
        else:
            # 遍历非边界值
            nonBoundIs = nonzero((oS.alphas.A > 0) * (oS.alphas.A < C))[0]
            for i in nonBoundIs:
                alphaPairsChanged += innerL(i,oS)
                print ("non-bound, iter: %d i:%d, pairs changed %d" % (iter,i,alphaPairsChanged))
            iter += 1
        # 在完整遍历和非边界值遍历之间来回切换
        if entireSet: entireSet = False
        elif (alphaPairsChanged == 0): entireSet = True  
        print ("iteration number: %d" % iter)
    # 返回常数b及alpha值
    return oS.b,oS.alphas

# 训练算法
def train(dataset,target,kTup=('rbf', 3)):
    # 读取训练数据
    #X_train, X_test, y_train, y_test=train_test_split(dataset,target,test_size=.4,random_state=1)
    dataArr,labelArr = dataset,target

    # Platt SMO算法进行SVM训练，获取b及alpha值
    print('hello1')
    b,alphas = smoP(dataArr, labelArr, 1, 0.001, 2500, kTup)

    # 建立矩阵数据副本
    datMat=mat(dataArr); labelMat = mat(labelArr).transpose()

    # 获得非0的alpha值
    svInd=nonzero(alphas.A>0)[0]

    # 得到所需的支持向量和alpha的类别标签值
    sVs=datMat[svInd] 
    labelSV = labelMat[svInd]
    print ("there are %d Support Vectors" % shape(sVs)[0])

    m,n = shape(datMat)
    errorCount = 0
    # 遍历训练数据
    for i in range(m):
        # 利用核函数进行分类，得到预测结果
        kernelEval = kernelTrans(sVs,datMat[i,:],kTup)
        predict=kernelEval.T * multiply(labelSV,alphas[svInd]) + b

        # 对比预测结果与真实分类，计算错误率
        if sign(predict)!=sign(labelArr[i]): errorCount += 1

    # 输出训练数据的错误率
    print ("the training error rate is: %f" % (float(errorCount)/m))

    return b,alphas

    '''# 读取测试数据
    dataArr,labelArr = X_test,y_test
    errorCount = 0
    datMat=mat(dataArr); labelMat = mat(labelArr).transpose()
    m,n = shape(datMat)

    # 遍历测试数据
    for i in range(m):
        # 利用核函数进行分类，得到预测结果
        kernelEval = kernelTrans(sVs,datMat[i,:],kTup)
        predict=kernelEval.T * multiply(labelSV,alphas[svInd]) + b

        # 对比预测结果与真实分类，计算错误率
        if sign(predict)!=sign(labelArr[i]): errorCount += 1

    # 输出测试错误率
    print ("the test error rate is: %f" % (float(errorCount)/m))'''
    
# ar = []
# for i in range(1,8):
#     for j in range(i+1,8):
#         ar.append([i,j])
# DD = array(ar)

# D=array([[1,2],[1,3],[2,3]])
DD = array([[1,2]])
print(DD)
# A=B=C=D=E=F=G=0
A=B=0
dictclass={}  #用于储存3个分类器的b,alphas

# filename = 'D:\CUDA appliqued in SVM\data_wine\wine.data'
filename = 'D:\CUDA appliqued in SVM\data_shuttle\shuttle.tst'
trainset,trainlabel=load_data(filename)

# print(trainset,trainlabel)
 
for a,c in DD:
    index=concatenate((nonzero(trainlabel==a)[0],nonzero(trainlabel!=a)[0]))
    # print(index)
    target1_raw=array([trainlabel[k] for k in index])
    target1=array([-1 if k!=a else 1 for k in target1_raw])
    trainset_raw=array([trainset[k] for k in index])
    print(target1.shape,trainset_raw.shape)  #(3132,)
    b,alphas=train(trainset_raw,target1)
    dictclass[str(a)+str(c)]=(b,alphas)
print(dictclass)


