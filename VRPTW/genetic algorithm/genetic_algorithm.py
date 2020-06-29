from utils import *
import copy
import random
import copy

def initialPopulation(popSize):
    pop = []
    while len(pop)< popSize:
        a = create_individual(comp_shift)
        pop.append(a)
    return pop


def fitness(individual):
    d, e = 0, 0
    for element in individual[0]:
        e += len(element)
        d += distance(element)
    return (e/2)*10000*n-d


def rankPopulation(population):
    fitnessResults = []
    for i, individual in enumerate(population):
        fitnessResults.append((i,fitness(individual) ))
    fitnessResults.sort(key = operator.itemgetter(1),reverse = True)
    return fitnessResults


def selection(popRanked, eliteSize):
    selectionResults = []
    popRankedNorm = []
    normalization = 0
    for element in popRanked:
        normalization += element[1]
    for element in popRanked:
        popRankedNorm.append( (element[0], element[1]/normalization))
    selectionResults.extend(popRankedNorm[0:eliteSize])
    while len(selectionResults) < len(popRanked):
        r, resint, i = random.random(), 0, 0
        while resint <= r:
            resint += popRankedNorm[i][1]
            i += 1
        selectionResults.append(popRankedNorm[i-1])
    selectionResults.sort(key = operator.itemgetter(1),reverse = True)
    return selectionResults


def matingPool(population, selectionResults):
    matingpool = []
    for element in selectionResults:
        matingpool.append(population[element[0]])
    return matingpool


def breed(p1, p2):
    parent1 = copy.deepcopy(p1)
    parent2 = copy.deepcopy(p2)
    child = []
    child = parent1[0][:int(2*k/3)]+parent2[0][int(2*k/3):]
    return repair(child)


def mutate(individual, mutationRate):
    mutant = individual[0]
    for l in range(k):
        for element in mutant[l]:
            if(random.random() < mutationRate) and element <= n:
                mutant[l].remove(element)
                mutant[l].remove(element+n)          
                mutant = insert_node_individual(element,mutant)
    return repair(mutant)


def mutatePopulation(population, mutationRate,eliteSize):
    popRanked = rankPopulation(population)
    mutatedPop = []
    for i in range(eliteSize):
        mutatedPop.append(population[popRanked[i][0]])
    for i in range(eliteSize, len(population)):
        mutatedInd = mutate(population[popRanked[i][0]], mutationRate)
        mutatedPop.append(mutatedInd)
    return mutatedPop


def nextGeneration(currentGen, eliteSize, mutationRate):
    popRanked = rankPopulation(currentGen)
    selectionResults = selection(popRanked, eliteSize)
    matingpool = matingPool(currentGen, selectionResults)
    children = breedPopulation(matingpool, eliteSize)
    nextGeneration = mutatePopulation(children, mutationRate, eliteSize)
    return nextGeneration


def geneticAlgorithmPlot(popSize, eliteSize, mutationRate, generations):
    pop = initialPopulation(popSize)
    progress = []
    progress.append(rankPopulation(pop)[0][1])
    sol = []
    
    for i in range(0, generations):
        if i%100 == 0:
            print('generation',i)
        pop = nextGeneration(pop, eliteSize, mutationRate)
        progress.append(rankPopulation(pop)[0][1])
        sol.append(pop[rankPopulation(pop)[0][0]])
    return progress , sol


