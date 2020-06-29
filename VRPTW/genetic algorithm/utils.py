import numpy as np, csv, random, operator, matplotlib.pyplot as plt
import json
import pandas
import copy


with open('week_data.json') as f:
  data = json.load(f)

bookings = data["bookings"]
shifts = data["shifts"]
df = pandas.read_csv('travel_times.csv',sep=";")
travel_times = df.set_index('Unnamed: 0').to_numpy()
n = len(bookings)
k = len(shifts)

def compatible_shifts_bookings(bookings,shifts):
    def helper(booking,shift):
        job1 = booking["jobs"][0]
        job2 = booking["jobs"][1]
        
        shift1 = shift["jobs"][0]
        shift2 = shift["jobs"][1]
        
        loc1,loc2 = int(job1["station"][1:]), int(job2["station"][1:])
        
        if job1["timeWindowEndDate"]-travel_times[0,loc1]-shift1["timeDate"] < 0:
            return False
        elif job2["timeWindowBeginDate"]+travel_times[loc2,0]+job2["duration"]-shift2["timeDate"] > 0:
            return False
        else:
            return True

    shifts_dict = {}
    for i,shift in enumerate(shifts):
        shifts_dict[i] = []
        for j, booking in enumerate(bookings, start = 1):
            if helper(booking,shift):
                shifts_dict[i].append(j)
    return shifts_dict



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



def create_base_individual(comp_shift):
    stations = [i for i in range(1,n+1)]
    individual = []
    for l in range(k):
        s = 0
        route = []
        while s not in stations:
            s = random.choice(comp_shift[l])
        stations.remove(s)
        route.append(s)
        route.append(s+n)
        individual.append(route)
    return individual, stations

def max_turnover(route):
    turnover = 0
    for element in route:
        if element in range(1,n):
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
        return [shifts[l]["jobs"][0]["timeDate"],shifts[l]["jobs"][1]["timeDate"]]
    
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


def feasible_individual(individual):
    for i,element in enumerate(individual[0]):
        if not feasible_route(element, i):
            return False
    return True




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
        return True
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



def insert_node_route(node,route,l):
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
                if dist_int <= dist and (max_capacity(resint) <= 4) and  (max_turnover(resint) <= 20000):
                    if feasible_route(resint2,l):
                        dist = dist_int 
                        res = resint2.copy()
                    
        elif i < len(route)-1:
            c1 = possible_temporal_middle(route[i],node,route[i+1])
            c2 = max_capacity(route[:i]+[node]+route[i:]) <= 4
            c3 = max_turnover(route[:i]+[node]+route[i:]) <= 20000
            
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
                if feasible_route(resint,l) and (max_capacity(resint) <= 4) and  (max_turnover(resint) <= 20000):
                    dist = dist_int 
                    res = resint.copy()
    return res



def insert_node_individual(node,individual):
    for i in range(k):
        route = individual[i]
        if node in comp_shift[i]:
            resint = insert_node_route(node,route,i)
            if len(resint) != len(route):
                individual[i] = resint
                return individual
    return individual


def create_individual(comp_shift):
    individual, stations = create_base_individual(comp_shift)
    na_stations =[]
    for node in stations:
        mem = individual.copy()
        individual = insert_node_individual(node,individual)
        if mem == individual:
            na_stations.append(node)
    return individual,na_stations



def repair(child):
    stations = []
    for station in range(1,n+1):
        count = 0
        for l in range(k):
            if station in child[l]:
                if count >= 1:
                    child[l].remove(station)
                    child[l].remove(station+n)
                count +=1
        if count == 0:
            stations.append(station)
            
    na_stations = []
    
    for node in stations:
        mem = child.copy()
        individual = insert_node_individual(node,child)
        if mem == individual:
            na_stations.append(node)
        
    return individual,na_stations




















