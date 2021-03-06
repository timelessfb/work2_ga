#!usr/bin/env python
# -*- coding:utf-8 -*-

import math
import numpy as np
import random


def check(sr, rbsc, chromosome):
    m = np.size(sr, 0)
    n = np.size(rbsc, 0)
    for i in range(n):
        down_bandwidth = 0
        up_bandwidth = 0
        process = 0
        for j in range(m):
            down_bandwidth += chromosome[j][i] * sr[j][0]
            up_bandwidth += chromosome[j][i] * sr[j][1]
            process += chromosome[j][i] * sr[j][2]
        if down_bandwidth > rbsc[i][0] or up_bandwidth > rbsc[i][1] or process > rbsc[i][2]:
            return False
    return True


# 那么一个个体应该用M * N的数组表示(要求：每一行只有一个1，每一列请求的资源不能超过基站剩余资源)，所有数组应该有L*M*N大小的矩阵表示
def getInitialPopulation(sr, rbsc, populationSize):
    m = np.size(sr, 0)
    n = np.size(rbsc, 0)
    chromosomes_list = []
    for i in range(populationSize):
        # 随机产生一个染色体
        chromosome = np.zeros((m, n), dtype=int)
        rbsc_realtime = np.array(rbsc)
        flag_of_matrix = 1
        # 产生一个染色体矩阵中的其中一行
        for j in range(m):
            # 随机探查,基站数/2 次分配
            flag_of_row = 0
            for k in range(math.ceil(n / 2)):
                bs_of_select = random.randint(0, n - 1)
                if sr[j][0] < rbsc_realtime[bs_of_select][0] and sr[j][1] < rbsc_realtime[bs_of_select][1] and sr[j][
                    2] < rbsc_realtime[bs_of_select][2]:
                    chromosome[j][bs_of_select] = 1
                    rbsc_realtime[bs_of_select][0] -= sr[j][0]
                    rbsc_realtime[bs_of_select][1] -= sr[j][1]
                    rbsc_realtime[bs_of_select][2] -= sr[j][2]
                    flag_of_row = 1
                    break
            # 随机探查失败，则遍历所有基站,找到一个有足够资源可以映射的基站
            if flag_of_row == 0:
                for bs_of_select in range(n):
                    if sr[j][0] < rbsc_realtime[bs_of_select][0] and sr[j][1] < rbsc_realtime[bs_of_select][1] and \
                            sr[j][2] < rbsc_realtime[bs_of_select][2]:
                        chromosome[j][bs_of_select] = 1
                        rbsc_realtime[bs_of_select][0] -= sr[j][0]
                        rbsc_realtime[bs_of_select][1] -= sr[j][1]
                        rbsc_realtime[bs_of_select][2] -= sr[j][2]
                        flag = 1
                        break
            if flag_of_row == 0:
                flag_of_matrix = 0
                break  ##################################

        # 将产生的染色体加入到chromosomes_list中
        if flag_of_matrix == 1:
            chromosomes_list.append(chromosome)
    chromosomes = np.array(chromosomes_list)
    return chromosomes


# 得到个体的适应度值(包括带宽和计算的代价)及每个个体被选择的累积概率
def getFitnessValue(sr, rbsc, chromosomes, delta):
    populations, m, n = np.shape(chromosomes)
    # 定义适应度函数，每一行代表一个染色体的适应度，每行包括四部分，分别为：带宽代价、计算代价、总代价、选择概率、累计概率
    fitness = np.zeros((populations, 6))
    for i in range(populations):
        # 取出来第i个染色体
        rbsc_realtime = np.array(rbsc)
        chromosome = chromosomes[i]
        cost_of_down_bandwidth = 0
        cost_of_up_bandwidth = 0
        cost_of_computing = 0
        for j in range(m):
            for k in range(n):
                if chromosome[j][k] == 1:
                    cost_of_down_bandwidth += sr[j][0] / (rbsc_realtime[k][0] + delta)
                    cost_of_up_bandwidth += sr[j][1] / (rbsc_realtime[k][1] + delta)
                    cost_of_computing += sr[j][2] / (rbsc_realtime[k][2] + delta)
                    rbsc_realtime[k][0] -= sr[j][0]
                    rbsc_realtime[k][1] -= sr[j][1]
                    rbsc_realtime[k][2] -= sr[j][2]
                    break
        fitness[i][0] = cost_of_down_bandwidth
        fitness[i][1] = cost_of_up_bandwidth
        fitness[i][2] = cost_of_computing
        fitness[i][3] = cost_of_down_bandwidth + cost_of_up_bandwidth + cost_of_computing
    # 计算被选择的概率
    sum_of_fitness = 0
    if populations > 1:
        for i in range(populations):
            sum_of_fitness += fitness[i][3]
        for i in range(populations):
            fitness[i][4] = (sum_of_fitness - fitness[i][3]) / ((populations - 1) * sum_of_fitness)
    else:
        fitness[0][4] = 1
    fitness[:, 5] = np.cumsum(fitness[:, 4])
    return fitness


# 选择算子
def selectNewPopulation(chromosomes, cum_probability):
    populations, m, n = np.shape(chromosomes)
    newpopulation = np.zeros((populations, m, n), dtype=int)
    # 随机产生populations个概率值
    randoms = np.random.rand(populations)
    for i, randoma in enumerate(randoms):
        logical = cum_probability >= randoma
        index = np.where(logical == 1)
        # index是tuple,tuple中元素是ndarray
        newpopulation[i, :, :] = chromosomes[index[0][0], :, :]
    return newpopulation
    pass


# 新种群交叉
def crossover(sr, rbsc, population, pc=0.8):
    """
    :param rbsc:
    :param sr:
    :param population: 新种群
    :param pc: 交叉概率默认是0.8
    :return: 交叉后得到的新种群
    """
    # 根据交叉概率计算需要进行交叉的个体个数
    populations, m, n = np.shape(population)
    # m, n = population.shape
    numbers = np.uint8(populations * pc)
    # 确保进行交叉的染色体个数是偶数个
    if numbers % 2 != 0:
        numbers += 1
    # 交叉后得到的新种群
    updatepopulation = np.zeros((populations, m, n), dtype=int)
    # 产生随机索引
    index = random.sample(range(populations), numbers)
    # 不进行交叉的染色体进行复制
    for i in range(populations):
        if not index.__contains__(i):
            updatepopulation[i, :, :] = population[i, :, :]
    # crossover
    while len(index) > 0:
        a = index.pop()
        b = index.pop()
        # 随机探测m/2个位置
        for i in range(math.ceil(m / 2)):
            # 随机产生一个交叉点
            try:
                crossoverPoint = random.sample(range(1, m), 1)
            except:
                print("except in crossover:")
                print(m)
            crossoverPoint = crossoverPoint[0]
            # one-single-point crossover
            updatepopulation[a, 0:crossoverPoint, :] = population[a, 0:crossoverPoint, :]
            updatepopulation[a, crossoverPoint:, :] = population[b, crossoverPoint:, :]
            updatepopulation[b, 0:crossoverPoint, :] = population[b, 0:crossoverPoint, :]
            updatepopulation[b, crossoverPoint:, :] = population[a, crossoverPoint:, :]
            if check(sr, rbsc, updatepopulation[a]) and check(sr, rbsc, updatepopulation[b]):
                break
            else:
                updatepopulation[a, :, :] = population[a, :, :]
                updatepopulation[b, :, :] = population[b, :, :]
    return updatepopulation
    pass


# 染色体变异
def mutation(sr, rbsc, population, pm=0.01):
    """
    :param rbsc:
    :param sr:
    :param population: 经交叉后得到的种群
    :param pm: 变异概率默认是0.01
    :return: 经变异操作后的新种群
    """
    updatepopulation = np.copy(population)
    populations, m, n = np.shape(population)
    # 计算需要变异的基因个数
    gene_num = np.uint8(populations * m * n * pm)
    # 将所有的基因按照序号进行10进制编码，则共有populations * m个基因
    # 随机抽取gene_num个基因进行基本位变异
    mutationGeneIndex = random.sample(range(0, populations * m * n), gene_num)
    # 确定每个将要变异的基因在整个染色体中的基因座(即基因的具体位置)
    for gene in mutationGeneIndex:
        # 确定变异基因位于第几个染色体
        chromosomeIndex = gene // (m * n)
        # 确定变异基因位于当前染色体的第几个基因位
        geneIndex = gene % (m * n)
        # 确定在染色体矩阵哪行
        sr_location = geneIndex // n
        # 确定在染色体矩阵哪行
        bs_location = geneIndex % n
        # mutation
        chromosome = np.array(population[chromosomeIndex])
        if chromosome[sr_location, bs_location] == 0:
            for i in range(n):
                chromosome[sr_location, i] = 0
            chromosome[sr_location, bs_location] = 1
        else:
            chromosome[sr_location, bs_location] = 0
            j = random.randint(0, n - 1)
            chromosome[sr_location, j] = 1
        if check(sr, rbsc, chromosome):
            updatepopulation[chromosomeIndex] = np.copy(chromosome)
    return updatepopulation
    pass


# 得到个体的适应度值(包括带宽和计算的代价)及每个个体被选择的累积概率
def update_rbsc(sr, rbsc, solution):
    m, n = np.shape(solution)
    rbsc_realtime = np.array(rbsc)
    chromosome = solution
    for j in range(m):
        for k in range(n):
            if chromosome[j][k] == 1:
                rbsc_realtime[k][0] -= sr[j][0]
                rbsc_realtime[k][1] -= sr[j][1]
                rbsc_realtime[k][2] -= sr[j][2]
                break
    return rbsc_realtime


def ga(SR, RBSC, max_iter=500, delta=0.0001, pc=0.8, pm=0.01, populationSize=10):
    # 每次迭代得到的最优解
    optimalSolutions = []
    optimalValues = []
    # 得到初始种群编码
    chromosomes = getInitialPopulation(SR, RBSC, populationSize)
    population_num = np.size(chromosomes, 0)
    print("population_num")
    print(population_num)
    if population_num == 0:
        return "failed", -1
    for iteration in range(max_iter):
        # 得到个体适应度值和个体的累积概率
        fitness = getFitnessValue(SR, RBSC, chromosomes, delta)
        # 选择新的种群
        cum_proba = fitness[:, 5]
        try:
            newpopulations = selectNewPopulation(chromosomes, cum_proba)
        except:
            print("except in ga:", population_num, chromosomes, np.size(chromosomes, 0), np.shape(chromosomes))
        # 进行交叉操作
        crossoverpopulation = crossover(SR, RBSC, newpopulations, pc)
        # mutation
        mutationpopulation = mutation(SR, RBSC, crossoverpopulation, pm)
        # 适应度评价
        fitness = getFitnessValue(SR, RBSC, mutationpopulation, delta)
        # 搜索每次迭代的最优解，以及最优解对应的目标函数的取值
        optimalValues.append(np.min(list(fitness[:, 3])))
        index = np.where(fitness[:, 3] == min(list(fitness[:, 3])))
        optimalSolutions.append(mutationpopulation[index[0][0], :, :])
        chromosomes = mutationpopulation
    # 搜索最优解
    optimalValue = np.min(optimalValues)
    print("progress\n")
    print(optimalValues)
    optimalIndex = np.where(optimalValues == optimalValue)
    optimalSolution = optimalSolutions[optimalIndex[0][0]]
    # iter = range(max_iter)
    # plt.plot(iter, optimalValues)
    # plt.show()
    return optimalSolution, optimalValue


if __name__ == '__main__':
    # BSC：base station capacity
    # RBSC: residuary base station capacity
    # SR: slice request
    # 模拟3个基站，每个基站拥有1000的带宽能力，1000的计算能力，size为N
    BSC = np.array([[10, 10, 10], [10, 10, 10], [10, 10, 10]], dtype=np.float)
    # 初始时，只有剩余矩阵就是整个基站的资源
    rbsc = np.array(BSC)
    # 模拟一组切片请求,包含几类，如带宽密集型、计算密集型，size为M
    SR_MODEL = np.array(
        [[1 / 16, 5 / 16, 10 / 16], [1 / 16, 10 / 16, 5 / 16], [5 / 16, 1 / 16, 10 / 16], [5 / 16, 10 / 16, 1 / 16],
         [10 / 16, 1 / 16, 5 / 16], [10 / 16, 5 / 16, 1 / 16]])
    max_iter = 500
    delta = 0.0001
    pc = 0.8
    pm = 0.01
    populationSize = 20
    # 构造10次请求
    request_num = 20
    values = np.zeros((request_num), dtype=np.float)
    solutions = []
    for iter in range(request_num):
        # 随机构造每次请求的切片数
        m = random.randint(8, 10)
        sr = np.zeros((m, 3), dtype=np.float)
        # 构造m个切片请求
        for i in range(m):
            j = random.randint(0, 5)
            sr[i] = SR_MODEL[j]
        print("rbsc:")
        print(rbsc)
        print("sr:")
        print(sr)
        solution, value = ga(sr, rbsc, max_iter, delta, pc, pm, populationSize)
        while solution == "failed" and np.size(sr, 0) >= 2:
            sr = sr[0:np.size(sr, 0) - 1, :]
            try:
                solution, value = ga(sr, rbsc, max_iter, delta, pc, pm, populationSize)
            except:
                print("except in main:", sr)
        if solution == "failed" or np.size(sr, 0) == 0:
            break
        print('最优目标函数值:', value)
        values[iter] = value
        print('solution:')
        print(solution)
        solutions.append(np.copy(solution))
        #################
        print("#################")
        if solution != "failed":
            m, n = np.shape(solution)
            chromosomes = np.zeros((1, m, n))
            chromosomes[0] = solution
            f1 = sum(solution)
            print("number of support each bs:", f1)
            new_rbsc = update_rbsc(sr, rbsc, solution)
            print("new_rbsc:")
            print(new_rbsc)
            f = getFitnessValue(sr, rbsc, chromosomes, delta)
            print(f)
            print("#################")
        #################
        rbsc = update_rbsc(sr, rbsc, solution)
    print("总结果")
    print(values)

    # ##验证
    # m, n = np.shape(solution)
    # chromosomes = np.zeros((1, m, n))
    # chromosomes[0] = solution
    # f1 = sum(solution)
    # print("number of support each bs:", f1)
    # new_rbsc = update_rbsc(SR, RBSC, solution)
    # print("new_rbsc:")
    # print(new_rbsc)
    # f = getFitnessValue(SR, RBSC, chromosomes, delta)
    # print(f)
