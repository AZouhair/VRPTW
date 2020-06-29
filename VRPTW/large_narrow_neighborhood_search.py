import numpy as np, csv, random, operator
import json
import pandas
from operator import itemgetter
import copy
import matplotlib.pyplot as plt
import time



with open('input.json') as f:
  data = json.load(f)
bookings = data["bookings"]
shifts = data["shifts"]
df = pandas.read_csv('travel_times.csv',sep=";")
travel_times = df.set_index('Unnamed: 0').to_numpy()
n = len(bookings)
k = len(shifts)


liste = []
for i,booking in enumerate(bookings, start=1):
    liste.append((i,booking["jobs"][1]["timeWindowBeginDate"]))
booking_sorted = []
for e in sorted(liste, key=itemgetter(1) , reverse = True):
    booking_sorted.append(e[0])


def compatible_shift(booking,shift):
    
    job1 = booking["jobs"][0]
    job2 = booking["jobs"][1]
    
    shift1 = shift["jobs"][0]
    shift2 = shift["jobs"][1]
    
    loc1,loc2 = int(job1["station"][1:]), int(job2["station"][1:])
    
    if job1["timeWindowEndDate"]-travel_times[0,loc1]-shift1["timeDate"] < 0:
        return False
    elif job1["timeWindowBeginDate"]+travel_times[0,loc1]+job1["duration"]+travel_times[loc1,loc2]+travel_times[loc2,0]+job2["duration"]-shift2["timeDate"] > 0:
        return False
    else:
        return True

comp_shift = {}
for i,shift in enumerate(shifts):
    comp_shift[i] = []
    for j in booking_sorted:
        if compatible_shift(bookings[j-1],shift):
            comp_shift[i].append(j)

def feasible_individual(individual):
    for i,element in enumerate(individual):
        if not feasible_route(element, i):
            return False
    return True

def distance(route):
    if not route:
        return 0
    dist = 0
    dist += travel_times[0,int(bookings[(route[0]-1)%n]["jobs"][(route[0]-1)//n]["station"][1:])]
    dist += travel_times[int(bookings[(route[-1]-1)%n]["jobs"][(route[-1]-1)//n]["station"][1:]),0]

    for i,k in zip(route[0:-1], route[1:]):
        loc1= int(bookings[(i-1)%n]["jobs"][(i-1)//n]["station"][1:]) 
        loc2 = int(bookings[(k-1)%n]["jobs"][(k-1)//n]["station"][1:])
        dist += travel_times[loc1,loc2]

    return dist

def max_turnover(route):
    turnover = 0
    for element in route:
        if element in range(1,n+1):
            turnover += bookings[element-1]["price"]
    return turnover

def max_capacity(route):
    maxtemp = 0
    temp = 0
    for element in route:
        if 1 <= element <= n:
            temp += bookings[element-1]["passengers"]
            maxtemp = max(maxtemp, temp)
        elif n+1 <= element <= 2*n:
            temp -= bookings[element-1-n]["passengers"]
    return maxtemp
            
def feasible_route(route,l):
    if not route:
        return True
    
    time_vect = []
    time_begin = shifts[l]["jobs"][0]["timeDate"]
    loc1 = int(bookings[(route[0]-1)%n]["jobs"][(route[0]-1)//n]["station"][1:])
    
    time_window = bookings[(route[0]-1)%n]["jobs"][(route[0]-1)//n]["timeWindowBeginDate"]
    time_vect.append(max(time_begin+travel_times[0,loc1], time_window))
    for i in range(1,len(route)):
        
        time_begin = time_vect[-1]
        
        job1 = bookings[(route[i-1]-1)%n]["jobs"][(route[i-1]-1)//n]
        job2 = bookings[(route[i]-1)%n]["jobs"][(route[i]-1)//n]
        
        d1 = job1["duration"]
        
        loc1 = int(job1["station"][1:])
        loc2 = int(job2["station"][1:])
        
        t12 = travel_times[loc1,loc2]
        
        time_candidate = time_begin+t12+d1
        time_window = [job2["timeWindowBeginDate"],job2["timeWindowEndDate"]]
                       
        if time_candidate >= time_window[1]:
            return False
        elif time_candidate <= time_window[0]:
            time_candidate = time_window[0]  
            
        time_vect.append(time_candidate)
        
        
    for i in range(len(route)):
        if route[i] <= n:
            j = route.index(route[i]+n)
            if (time_vect[j] - time_vect[i]) > bookings[(route[i]-1)%n]["maximumDuration"]:
                return False
            
    shiftend = shifts[l]["jobs"][1]["timeDate"]
    job1 = bookings[(route[-1]-1)%n]["jobs"][(route[-1]-1)//n]
    loc1 = int(job1["station"][1:])
    if time_vect[-1] + travel_times[loc1,0] +job1["duration"]-shiftend > 0:
        return False
    
    return time_vect


def possible_temporal_middle(node1,node2,node3):
    
    job1 = bookings[(node1-1)%n]["jobs"][(node1-1)//n]
    job2 = bookings[(node2-1)%n]["jobs"][(node2-1)//n]
    job3 = bookings[(node3-1)%n]["jobs"][(node3-1)//n]
    
    loc1 = int(job1["station"][1:])
    loc2 = int(job2["station"][1:])
    loc3 = int(job3["station"][1:])
    
    d1 = job1["duration"]
    d2 = job2["duration"]
    d3 = job3["duration"]
    
    t12 = travel_times[loc1,loc2]
    t23 = travel_times[loc2,loc3]
    
    if job1["timeWindowEndDate"]+d1+t12+d2-job2["timeWindowEndDate"] >= 0:
        return False
    elif job1["timeWindowEndDate"]+d1+t12+d2+t23+d3-job3["timeWindowEndDate"] >= 0:
        return False
    else:
        return True
    
    
def possible_temporal_end(node,route,i):
    
    job1 = bookings[(route[-1]-1)%n]["jobs"][(route[-1]-1)//n]
    job2 = bookings[(node-1)%n]["jobs"][(node-1)//n]
    job3 = bookings[(node+n-1)%n]["jobs"][(node+n-1)//n]
    
    d1 = job1["duration"]
    d2 = job2["duration"]
    d3= job3["duration"]
    
    loc1 = int(job1["station"][1:])
    loc2 = int(job2["station"][1:])
    loc3 = int(job3["station"][1:])
    
    t12 = travel_times[loc1,loc2]
    t23 = travel_times[loc2,loc3]
    t30 = travel_times[loc3,0]
    
    time_end = shifts[i]["jobs"][1]["timeDate"]
    
    if job1["timeWindowEndDate"]+d1+t12+d2-job2["timeWindowEndDate"] >= 0:
        return False
    elif job1["timeWindowEndDate"]+d1+t12+d2+t23+d3+t30-time_end >= 0:
        return False
    else:
        return True
    
    
def possible_temporal_begin(node,route,i):
    if not route:
        a = node in comp_shift[i]
        return a
    
    job1 = bookings[(node-1)%n]["jobs"][(node-1)//n]
    job2 = bookings[(route[0]-1)%n]["jobs"][(route[0]-1)//n]
    
    d1 = job1["duration"]
    d2 = job2["duration"]
    
    loc1 = int(job1["station"][1:])
    loc2 = int(job2["station"][1:])
    
    t01 = travel_times[0,1]
    t12 = travel_times[loc1,loc2]
    
    time_begin = shifts[i]["jobs"][0]["timeDate"]
    
    if time_begin+d1+t01-job1["timeWindowEndDate"] >= 0:
        return False
    elif time_begin+d1+t01+t12+d2-job2["timeWindowBeginDate"] >= 0:
        return False
    else:
        return True


def create_shift(stations,l):
    max_turn = shifts[l]['maximumTurnover']
    max_cap = shifts[l]['capacity']
    route = []
    node_disp = [node for node in comp_shift[l] if node in stations]
    if not node_disp:
        return [], stations, []
    
    count = 0
    while not route and count < len(node_disp):
        s = node_disp[count]
        if feasible_route([s,s+n],l):
            route = [s,s+n]
        count += 1
    if not route:
        return [], stations, []

    for node in node_disp:
        
        dist = 10**6 
        for i in range(len(route)):

            resint = route.copy()

            if i == 0 and possible_temporal_begin(node,route,l):

                resint = [node]+resint

                for j in range(i+1,len(route)+1):
                    resint2 = resint.copy()
                    resint2.insert(j, node+n)
                    dist_int = distance(resint)
                    if dist_int <= dist and (max_capacity(resint) <= max_cap) and (max_turnover(resint) <= max_turn) :
                        if feasible_route(resint2,l):
                            dist = dist_int 
                            route = resint2.copy()

            elif i < len(route)-1:
                c1 = possible_temporal_middle(route[i],node,route[i+1])
                c2 = max_capacity(route[:i]+[node]+route[i:]) <= max_cap
                c3 = max_turnover(route[:i]+[node]+route[i:]) <= max_turn

                if c1 and c2 and c3:
                    resint.insert(i, node)
                    for j in range(i+1,len(route)+1):
                        resint2 = resint.copy()
                        resint2.insert(j, node+n)
                        dist_int = distance(resint)
                        if dist_int <= dist:
                            if feasible_route(resint2,l):
                                dist = dist_int 
                                route = resint2.copy()
                                
            elif possible_temporal_end(node,route,l):
                resint.append(node)
                resint.append(node+n)
                dist_int = distance(resint)
                if dist_int <= dist:
                    if feasible_route(resint,l) and (max_capacity(resint) <= max_cap) and (max_turnover(resint) <= max_turn):
                        dist = dist_int 
                        route = resint.copy()

        if node in route:
            node_disp.remove(node)
            
    stations = [s for s in stations if (s in node_disp) or not(s in comp_shift[l])]
    result = [i for n, i in enumerate(route) if i not in route[:n]]
    time_vect = feasible_route(result,l)
    return result, stations, time_vect


def create_individual(comp_shift):
    shifts_range = [(x,len(comp_shift[x])) for x in range(k)]
    individual = [[] for i in range(k)]
    stations = [x for x in range(n+1)]
    for l in sorted(shifts_range, key=itemgetter(1)):
        a = create_shift(stations,l[0])
        individual[l[0]]=[i for n, i in enumerate(a[0]) if i not in a[0][:n]]
        stations = a[1]
    
    return individual


def time_individual(individual):
    res =[]
    for i,element in enumerate(individual):
        res.append(feasible_route(element,i))
    return res


def na_bookings(a):
    stations = [x for x in range(1,n+1)]
    for element in a:
        for x in element:
            if x in booking_sorted:
                stations.remove(x)
    return stations


def fitness(individual):
    d = 0
    e = 0
    for element in individual:
        e += len(element)
        d += distance(element)
    return (e/2)*10000*n-d


def insert_node_route(node,route,l):
    if node not in comp_shift[l]:
        return route
    
    max_turn = shifts[l]['maximumTurnover']
    max_cap = shifts[l]['capacity']
    
    if route == []:
        if possible_temporal_begin(node,route,l):
            return [node,node+n]
    
    res = route
    dist = 10**6
    for i in range(len(route)):
        resint = route.copy()
        
        if i == 0 and possible_temporal_begin(node,route,l):
            
            resint = [node]+resint

            for j in range(i+1,len(route)+1):
                resint2 = resint.copy()
                resint2.insert(j, node+n)
                dist_int = distance(resint)
                if dist_int <= dist and (max_capacity(resint)<= max_cap) and (max_turnover(resint) <= max_turn) :
                    if feasible_route(resint2,l):
                        dist = dist_int 
                        res = resint2.copy()
                    
        elif i < len(route)-1:
            c1 = possible_temporal_middle(route[i],node,route[i+1])
            c2 = max_capacity(route[:i]+[node]+route[i:]) <= max_cap
            c3 = max_turnover(route[:i]+[node]+route[i:]) <= max_turn
            
            if c1 and c2 and c3:
                resint.insert(i, node)
                for j in range(i+1,len(route)+1):
                    resint2 = resint.copy()
                    resint2.insert(j, node+n)
                    dist_int = distance(resint)
                    if dist_int <= dist:
                        if feasible_route(resint2,l):
                            dist = dist_int 
                            res = resint2.copy()
                        
        elif possible_temporal_end(node,route,l):
            resint.append(node)
            resint.append(node+n)
            dist_int = distance(resint)
            if dist_int <= dist:
                if feasible_route(resint,l) and (max_capacity(resint) <= max_cap) and (max_turnover(resint) <= max_turn) :
                    dist = dist_int 
                    res = resint.copy()
    return res

def insert_node_individual(node,individual):
    routes = [x for x in range(k)]
    random.shuffle(routes)
    for i in routes:
        route = individual[i]
        if node in comp_shift[i]:
            resint = insert_node_route(node,route,i)
            if len(resint) != len(route):
                individual[i] = resint
                return individual
    return individual


def generate_neighbor_swap(sol,rate):
    res = copy.deepcopy(sol) 
    for l in range(k):
        for node in res[l]:
            if(random.random() < rate) and (node <= n):
                res[l].remove(node)
                res[l].remove(node+n)          
    stations = na_bookings(res)
    random.shuffle(stations)
    for node in stations:
        res = insert_node_individual(node,res)
    for l,route in enumerate(res):
        nodes = [x for x in booking_sorted if x in route]
        for node in nodes:
            insert_node_route(node,route,l)
    
    stations = na_bookings(res)
    for node in stations:
        res = insert_node_individual(node,res)
    return res


def bookings_distance(individual):
    d = 0
    e = 0
    for element in individual:
        e += len(element)
        d += distance(element)
    return e/2,d



def VNS(temps,m):
    bestSolution = create_individual(comp_shift)
    start_time = time.time()
    while time.time()-start_time <= temps*60:
        f1 = fitness(bestSolution)
        sol = generate_neighbor_swap(bestSolution,0.1)
        f2 = fitness(sol)
        if f2 > 0.995*f1:
            if f2 > f1:
                if feasible_individual(sol):
                        bestSolution = sol 
            for i in range(m):
                f1 = fitness(bestSolution)
                close_sol = generate_neighbor_swap(sol,0.01)
                f3 = fitness(close_sol)
                if f3 > f1:
                    if feasible_individual(close_sol):
                        bestSolution = close_sol 
    return bestSolution


result = VNS(1,20)
output = {}
output["shifts"] = []
output["route_cost"] = int(d)
output["nb_assigned_bookings"] = int(e)/2
for l in range(k):
    dic = {}
    dic["id"] = shifts[l]["id"]
    dic["jobs"] = []
    time_vect = time_individual(result)[l]
    for i,node in enumerate(result[l]):
        b = bookings[(node-1)%n]["jobs"][(node-1)//n]
        dic2 = {}
        dic2["id"] = b["id"]
        dic2["time"] = int(time_vect[i])
        dic["jobs"].append(dic2)
    shift = shifts[l]
    
    dic2 = {}
    dic2["id"] = shift["jobs"][0]["id"]
    dic2["time"] = shift["jobs"][0]["timeDate"]
    dic["jobs"].append(dic2)
    
    dic2 = {}
    dic2["id"] = shift["jobs"][1]["id"]
    dic2["time"] = shift["jobs"][1]["timeDate"]
    dic["jobs"].append(dic2)
    
    output["shifts"].append(dic)
    draft = json.dumps(output)


with open('output.json', 'w') as outfile:
    json.dump(output, outfile)
