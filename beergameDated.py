import numpy
import matplotlib.pyplot as pl
import math
import csv

# ------ Parameters setting ------

'''
N: total simulation period
t: lead time in each echelon
ft: moving average forecast period
p: sale price per unit in each echelon
alpha: smoothing parameter for exponential smoothing in Corcoran's matrix
c_m: mean of customer's demand
c_v: variance of customer's demand
N_w: warm-up period
'''

N = 50
t = [4] * 4
ft = 6
p = [5] * 5
alpha = 0.8
beta = 0.2
c_m = 100
c_v = 10
N_w = 10

minDays = 10
meanReliable = 40
'''
inv: inventory level
bo: backlog amount

d: demand (incoming order received from the customer this week)
o: order (order placed to the supplier this week)
ins: incoming shipment received from the supplier
outs: outgoing shipment sent to the customer
s: order-up-to level
fm: mean value of the past period's demands
fv: variance of the past period's demands
oo: ongoing orders

p: sale price of the unit
ar: accounts receivable

tp: transform probability
ap: transform probability after exponential smoothing
fi: forecasting incomes
'''

inv = numpy.zeros((4, N))
d = numpy.zeros((4, N))
o = numpy.zeros((4, N))
bo = numpy.zeros((4, N))
oo = numpy.zeros((4, N))
s = numpy.zeros((4, N))
fv = numpy.zeros((4, N))
fm = numpy.zeros((4, N))
ins = numpy.zeros((4, N))
outs = numpy.zeros((4, N))
ar = numpy.zeros((4, N, 20))
r = numpy.zeros((4, N, 5))
pM = numpy.zeros((4, N, 3))
pB = numpy.zeros((4, N, 3))
pp = numpy.zeros((4, N, 3))
ap = numpy.zeros((4, N, 3))
fi = numpy.zeros((4, N))
e = numpy.zeros((4, N))

eLambda = numpy.zeros((4, N))
daysOut = [[30, ]]*4


# ------ initialization ------
'''
set warm-up periods
d[0, n] as random customer's demand
'''

for n in range(N_w, N):
    d[0, n] = int(numpy.random.normal(c_m, c_v))
for j in range(4):
    for n in range(N_w):
        inv[j, n] = 100
        o[j, n] = 100
        d[j, n] = 100
        ins[j, n] = 100
        outs[j, n] = 100
        oo[j, n] = 300

# ------ simulation ------

n = N_w
while n < N - 1:
    for j in range(4):
        if j != 3:
            ins[j, n] = outs[j + 1, n - int(t[j] / 2)]  # receive shipment
        else:
            ins[j, n] = o[j, n - t[j]]  # supplier gets its order
        if j != 0:
            d[j, n] = o[j - 1, n - int(t[j - 1] / 2)]  # upstream echelon gets the order from downstream echelon
        if inv[j, n - 1] - bo[j, n - 1] + ins[j, n] >= d[j, n]:
            outs[j, n] = d[j, n] + bo[j, n - 1]
            bo[j, n] = 0
            inv[j, n] = inv[j, n - 1] - bo[j, n - 1] + ins[j, n] - d[j, n]  # when the demand can be satisfied
        else:
            outs[j, n] = inv[j, n - 1] + ins[j, n]
            inv[j, n] = 0
            bo[j, n] = d[j, n] - (inv[j, n - 1] - bo[j, n - 1] + ins[j, n])  # when the demand can't be satisfied

        fore = d[j, n - ft + 1:n]  # select the periods we use in forecasting
        fm[j, n] = numpy.mean(fore)
        fv[j, n] = numpy.std(fore)
        s[j, n] = int(fm[j, n] * (t[j] + 1) + 1.29 * fv[j, n] * (t[j] + 1) ** 0.5)  # decide order-up-to level
        oo[j, n] = sum(o[j, n - t[j] + 1:n])
        if inv[j, n] - bo[j, n] + oo[j, n] < s[j, n]:
            o[j, n] = s[j, n] - inv[j, n] - oo[j, n] + bo[j, n]  # need to order
        else:
            o[j, n] = 0


# ------ payment rule ------

# calculate AR (accounts receivable)
        if j != 0:
            ar[j, n, 1] = ins[j - 1, n] * p[j]
        else:
            ar[j, n, 1] = outs[j, n] * p[j]

        delta = 2 * (meanReliable - minDays) / math.pi ** 0.5
        if numpy.random.rand() < (1 - math.exp(-((14 - minDays) / delta) ** 2)) and ar[j, n-1, 1] != 0:
            ar[j, n, 2] = 0
            ar[j, n, 0] += ar[j, n-1, 1]
            daysOut[j].append(10)
        else:
            ar[j, n, 2] = ar[j, n-1, 1]
        for k in range(2, 19):
            if (numpy.random.rand() < (1 - math.exp(-(2 * ((k - 1) * 14 - minDays) * 14 + 14 ** 2) / delta ** 2)) and
                    ar[j, n-1, k] != 0):
                ar[j, n, k + 1] = 0
                ar[j, n, 0] += ar[j, n-1, k]
                daysOut[j].append(14*(k-1)+7)
            else:
                ar[j, n, k + 1] = ar[j, n-1, k]

        r[j, n, 0] = ar[j, n, 0]        # summary AR by period
        r[j, n, 1] = sum(ar[j, n, 1:3])
        r[j, n, 2] = sum(ar[j, n, 3:5])
        r[j, n, 3] = sum(ar[j, n, 5:7])
        r[j, n, 4] = sum(ar[j, n, 7:9])

# ------ forecast cashflow ------

        if n % 2 == 1:
            # Markov chain
            for k in range(3):
                if r[j, n-2, k+1] != 0:
                    pM[j, n, k] = (r[j, n-2, k+1] - r[j, n, k+2]) / r[j, n-2, k+1]
                else:
                    pM[j, n, k] = 0

            # Bayesian
            eLambda[j, n] = 2*(numpy.mean(daysOut[j])-minDays)/math.pi**0.5
            pB[j, n, 0] = 1-math.exp(-((30-minDays)/eLambda[j, n])**2)
            for k in range(1, 3):
                pB[j, n, k] = 1-math.exp((-(2*k*30-minDays)*30+30**2)/eLambda[j, n]**2)

            # exponential smoothing
            for k in range(3):
                pp[j, n, k] = beta*pM[j, n, k]+(1-beta)*pB[j, n, k]
                ap[j, n, k] = alpha*pp[j, n, k]+(1-alpha)*ap[j, n-1, k]

            fi[j, n] = r[j, n-2, 1] * ap[j, n, 0] + r[j, n-2, 2] * ap[j, n, 1] + r[j, n-2, 3] * ap[j, n, 2]
            if (r[j, n-1, 0]+r[j, n, 0]) != 0:
                e[j, n] = abs((r[j, n-1, 0]+r[j, n, 0]-fi[j, n])/(r[j, n-1, 0]+r[j, n, 0]))
            else:
                e[j, n] = None

    n += 1

theFile = open('test.txt', 'w')

'''
for echelon in pB:
    theFile.write("echelon: \n")
    for period in echelon:
        theFile.write("period \n")
        for state in period:
            theFile.write("%s, " % state)
        theFile.write("\n")

for echelon in e:
    theFile.write("echelon: \n")
    for period in echelon:
        theFile.write("period \n")
        theFile.write("%s, " % period)
        theFile.write("\n")
'''

theFile.close()

myFile = open('result.csv', 'w', newline='\n')
wr = csv.writer(myFile, quoting=csv.QUOTE_ALL)
for j in range(4):
    wr.writerow(['inventory', 'echelon', '%s' %j])
    wr.writerow(inv[j])
    wr.writerow(['demand', ''])
    wr.writerow(d[j])
    wr.writerow(['order', ''])
    wr.writerow(o[j])
    wr.writerow(['back-order', ''])
    wr.writerow(bo[j])
    wr.writerow(['ongoing order', ''])
    wr.writerow(oo[j])
    wr.writerow(['incoming shipment', ''])
    wr.writerow(ins[j])
    wr.writerow(['outgoing shipment', ''])
    wr.writerow(outs[j])
    wr.writerow(['order up to level', ''])
    wr.writerow(s[j])
    wr.writerow(['forecasted mean', ''])
    wr.writerow(fm[j])
    wr.writerow(['forecasted variance', ''])
    wr.writerow(fv[j])
    wr.writerow(['accounts receivable', ''])
    wr.writerows(ar[j])
    wr.writerow(['summary of ar', ''])
    wr.writerows(r[j])
    wr.writerow(['markov chain', ''])
    wr.writerows(pM[j])
    wr.writerow(['bayesian', ''])
    wr.writerows(pB[j])
    wr.writerow(['smoothed', ''])
    wr.writerows(ap[j])
    wr.writerow(['forecast income', ''])
    wr.writerow(fi[j])
    wr.writerow(['error', ''])
    wr.writerow(e[j])
    wr.writerow(['estimated lambda', ''])
    wr.writerow(eLambda[j])

myFile.close()

'''

for j in range(4):
    pl.plot(r[j, :, 0], 'r-', r[j, :, 1], 'b-', r[j, :, 2], 'g-',r[j, :, 3], 'y-')

    pl.title("%dth echelon" % j)
    pl.show()

theFile = open('test.txt', 'w')

for echelon in r:
    theFile.write("echelon: \n")
    for period in echelon:
        theFile.write("period \n")
        for state in period:
            theFile.write("%s, " % state)
        theFile.write("\n")


eMean = 22
eMin = 10
delta =2*(eMean-eMin)/math.pi**0.5
pe = 1 - math.e**(-((30-eMin)/delta)**2)
'''
