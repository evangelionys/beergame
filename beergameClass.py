import math
import numpy
from beergameVariables import *

# ------ define class ------


class Component(object):
    def __init__(self, paras):
        customer_cor, min_payment, mean_payment, scale, customer_var = paras
        self.inventory = [0] * time_period
        self.order = [0] * time_period
        self.orderLevel = [0] * time_period
        self.ongoing = [0] * time_period
        self.incomingShipment = [0] * time_period
        self.forecast_mean = [0] * time_period  # forecast the mean of demand using moving average
        self.forecast_var = [0] * time_period
        self.ar = numpy.zeros((6, time_period))  # accounts receivable united by month
        self.pM = numpy.zeros((4, int(time_period / 2)))  # transform prob using Markov Chains
        self.forecast_income = [0] * int(time_period / 2)
        self.forecast_income_mc = [0] * int(time_period / 2)
        self.forecast_income_Pete = [0] * int(time_period / 2)
        self.forecast_moving = [0] * int(time_period / 2)
        self.forecast_income2 = [0] * int(time_period / 2)
        self.forecast_income3 = [0] * int(time_period / 2)
        self.forecast_income4 = [0] * int(time_period / 2)
        self.forecast_income5 = [0] * int(time_period / 2)
        self.difference = [0] * int(time_period / 2)
        self.difference_mc = [0] * int(time_period / 2)
        self.difference_Pete = [0] * int(time_period / 2)
        self.difference_moving = [0] * int(time_period / 2)
        self.difference2 = [0] * int(time_period / 2)
        self.difference3 = [0] * int(time_period / 2)
        self.difference4 = [0] * int(time_period / 2)
        self.difference5 = [0] * int(time_period / 2)
        self.demand = numpy.zeros((scale, time_period))
        self.backlog = numpy.zeros((scale, time_period))
        self.outgoingShipment = numpy.zeros((scale, time_period))
        self.total_backlog = [0] * time_period
        self.total_demand = [0] * time_period
        self.accounts_receivable = numpy.zeros((scale, 12, time_period))  # accounts receivable united by period
        self.individual_ar = numpy.zeros((scale, 6, time_period))
        self.daysOut = [[mean_payment, ] for n in range(scale)]  # payment day
        self.pB = numpy.zeros((scale, 4, int(time_period / 2)))  # transform prob using Bayesian method
        self.pP = numpy.zeros((scale, 4, int(time_period / 2)))  # combined prob
        self.aP = numpy.zeros((scale, 4, int(time_period / 2)))  # smoothed prob
        self.aM = numpy.zeros((scale, 4, int(time_period / 2)))
        self.aB = numpy.zeros((scale, 4, int(time_period / 2)))
        self.pP2 = numpy.zeros((scale, 4, int(time_period / 2)))
        self.aP2 = numpy.zeros((scale, 4, int(time_period / 2)))
        self.pP3 = numpy.zeros((scale, 4, int(time_period / 2)))
        self.aP3 = numpy.zeros((scale, 4, int(time_period / 2)))
        self.pP4 = numpy.zeros((scale, 4, int(time_period / 2)))
        self.aP4 = numpy.zeros((scale, 4, int(time_period / 2)))
        self.pP5 = numpy.zeros((scale, 4, int(time_period / 2)))
        self.aP5 = numpy.zeros((scale, 4, int(time_period / 2)))
        self.eLambda = numpy.zeros((scale, int(time_period / 2)))  # estimated lambda for customers


class Retailer(Component):
    def __init__(self, paras, name, mini, mean):
        Component.__init__(self, paras)
        customer_cor, min_payment, mean_payment, scale, customer_var = paras
        self.name = name
        self.mean = mean  # customer's mean payment day
        self.min = mini  # customer's minimum payment day, range (14, 28)
        self.lam = [0] * scale
        for k in range(scale):
            self.lam[k] = 2 * (self.mean[k] - self.min[k]) / math.pi ** 0.5


class Distributor(Component):
    def __init__(self, paras, name, mini, mean):
        Component.__init__(self, paras)
        customer_cor, min_payment, mean_payment, scale, customer_var = paras
        self.name = name
        self.mean = mean  # customer's mean payment day
        self.min = mini  # customer's minimum payment day, range (14, 28)
        self.lam = [0] * scale
        for k in range(scale):
            self.lam[k] = 2 * (self.mean[k] - self.min[k]) / math.pi ** 0.5


class Manufacturer(Component):
    def __init__(self, paras, name, mini, mean):
        Component.__init__(self, paras)
        customer_cor, min_payment, mean_payment, scale, customer_var = paras
        self.name = name
        self.mean = mean  # customer's mean payment day
        self.min = mini  # customer's minimum payment day, range (14, 28)
        self.lam = [0] * scale
        for k in range(scale):
            self.lam[k] = 2 * (self.mean[k] - self.min[k]) / math.pi ** 0.5


class Supplier(Component):
    def __init__(self, paras, name, mini, mean):
        Component.__init__(self, paras)
        customer_cor, min_payment, mean_payment, scale, customer_var = paras
        self.name = name
        self.mean = mean  # customer's mean payment day
        self.min = mini  # customer's minimum payment day, range (14, 28)
        self.lam = [0] * scale
        for k in range(scale):
            self.lam[k] = 2 * (self.mean[k] - self.min[k]) / math.pi ** 0.5