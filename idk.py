
li1 = [1,2,3,4,5,6,7,8,9,]
li2 = [8,9,10.5,12,1,2,3,4]

def compute_distance(x,y):
    return abs(x-y)

def idk(li1,li2,p1,p2,look_ahead):
    minimum = float("inf")
    for i in range(p2,p2 + look_ahead):
        if i > len(li2)-1:
            i = 10 - len(li2)
        if minimum > compute_distance(li1[p1],li2[i]):
            minimum = compute_distance(li1[p1],li2[i])
    return minimum

if __name__ == "__main__":


    cond = True
    p1 = 0
    p2 = 0
    limit = 2
    starting_pointer_p1 = 0
    start = True
    d = dict()
    while True:
        if (p1 == starting_pointer_p1) and (start != True):
            break
        distance = compute_distance(li1[p1],li2[p2])
        if distance > limit:
            #We minus 1 since len is 1 indexed and index is 0
            if p2 == len(li2)-1:
                p2 = 0
                continue
            p2 += 1
        else:
            start = False
            d[p1] = idk(li1,li2,p1,p2,limit*2+1)
            if p1 == len(li1)-1:
                p1 =0
                continue
            p1+= 1
            p2 +=1 
            if p2 == len(li2)-1:
                p2 = 0

