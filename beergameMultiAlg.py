import matplotlib.pyplot as pl
from beergameClass import *
import csv


def setup_paras():

    customer_cor = 0.1 * numpy.random.randint(1, 10)
    min_payment = numpy.random.randint(20, 40)
    mean_payment = numpy.random.randint(40, 60)
    scale = numpy.random.randint(1, 30)
    customer_var = numpy.random.randint(0, 20)
    return customer_cor, min_payment, mean_payment, scale, customer_var


def create_chains():
    retailer = {}
    distributor = {}
    manufacturer = {}
    supplier = {}
    return retailer, distributor, manufacturer, supplier


def beergame_simulation(paras, echelons):
    customer_cor, min_payment, mean_payment, scale, customer_var = paras
    retailer, distributor, manufacturer, supplier = echelons
    for n in range(scale):
        retailer[n] = Retailer(paras, 'Retailer %s' % n, [min_payment] * scale, [mean_payment] * scale)
        distributor[n] = Distributor(paras, 'distributor %s' % n, [min_payment] * scale, [mean_payment] * scale)
        manufacturer[n] = Manufacturer(paras, 'manufacturer %s' % n, [min_payment] * scale, [mean_payment] * scale)
        supplier[n] = Supplier(paras, 'supplier %s' % n, [min_payment] * scale, [mean_payment] * scale)

    # ------ initialization ------

    # set up warm-up period
    for n in range(warm_up_period):
        for j in range(scale):
            retailer[j].inventory[n] = customer_mean * scale
            retailer[j].total_demand[n] = customer_mean * scale
            for k in range(scale):
                retailer[j].demand[k][n] = customer_mean
                retailer[j].outgoingShipment[k][n] = customer_mean
            retailer[j].order[n] = customer_mean * scale
            retailer[j].ongoing[n] = customer_mean * scale * (lead_time - 1)
            retailer[j].incomingShipment[n] = customer_mean * scale
            retailer[j].forecast_mean[n] = customer_mean * scale
            retailer[j].forecast_var[n] = customer_var * scale
            distributor[j].inventory[n] = customer_mean * scale
            distributor[j].total_demand[n] = customer_mean * scale
            for k in range(scale):
                distributor[j].demand[k][n] = customer_mean
                distributor[j].outgoingShipment[k][n] = customer_mean
            distributor[j].order[n] = customer_mean * scale
            distributor[j].ongoing[n] = customer_mean * scale * (lead_time - 1)
            distributor[j].incomingShipment[n] = customer_mean * scale
            distributor[j].forecast_mean[n] = customer_mean * scale
            distributor[j].forecast_var[n] = customer_var * scale
            manufacturer[j].inventory[n] = customer_mean * scale
            manufacturer[j].order[n] = customer_mean * scale
            manufacturer[j].ongoing[n] = customer_mean * scale * (lead_time - 1)
            manufacturer[j].incomingShipment[n] = customer_mean * scale
            manufacturer[j].total_demand[n] = customer_mean * scale
            for k in range(scale):
                manufacturer[j].demand[k][n] = customer_mean
                manufacturer[j].outgoingShipment[k][n] = customer_mean
            manufacturer[j].forecast_mean[n] = customer_mean * scale
            manufacturer[j].forecast_var[n] = customer_var * scale
            supplier[j].inventory[n] = customer_mean * scale
            supplier[j].order[n] = customer_mean * scale
            supplier[j].ongoing[n] = customer_mean * scale * (lead_time - 1)
            supplier[j].incomingShipment[n] = customer_mean * scale
            supplier[j].total_demand[n] = customer_mean * scale
            for k in range(scale):
                supplier[j].demand[k][n] = customer_mean
                supplier[j].outgoingShipment[k][n] = customer_mean
            supplier[j].forecast_mean[n] = customer_mean * scale
            supplier[j].forecast_var[n] = customer_var * scale

    # set up random customer demand
    for n in range(warm_up_period, time_period):
        for j in range(scale):
            for k in range(scale):
                retailer[j].demand[k][n] = int(retailer[j].demand[k][n - 1] * customer_cor
                                               + numpy.random.normal(0, customer_var ** 0.5)
                                               + customer_mean * (1 - customer_cor))
            retailer[j].total_demand[n] = sum(retailer[j].demand[:, n])

    # ------ simulation ------

    for n in range(warm_up_period, time_period):
        for j in range(scale):
            # receive shipment from downstream echelon
            temp1 = 0
            temp2 = 0
            temp3 = 0
            for k in range(scale):
                temp1 += distributor[k].outgoingShipment[j][n - int(lead_time / 2)]
                temp2 += manufacturer[k].outgoingShipment[j][n - int(lead_time / 2)]
                temp3 += supplier[k].outgoingShipment[j][n - int(lead_time / 2)]
            retailer[j].incomingShipment[n] = temp1
            distributor[j].incomingShipment[n] = temp2
            manufacturer[j].incomingShipment[n] = temp3
            supplier[j].incomingShipment[n] = supplier[j].order[n - lead_time]
            # decide order amount using exponential smoothing method
            retailer[j].forecast_mean[n] = (forecast_smoothing * retailer[j].total_demand[n - 1]
                                            + (1 - forecast_smoothing) * retailer[j].forecast_mean[n - 1])
            retailer[j].forecast_var[n] = (
                forecast_smoothing * (retailer[j].total_demand[n - 1] - retailer[j].forecast_mean[n]) ** 2
                + (1 - forecast_smoothing) * retailer[j].forecast_var[n - 1])
            retailer[j].orderLevel[n] = int(retailer[j].forecast_mean[n] * (lead_time + 1)
                                            + 1.29 * retailer[j].forecast_var[n] ** 0.5 * (lead_time + 1) ** 0.5)
            retailer[j].ongoing[n] = sum(retailer[j].order[n - lead_time + 1:n])
            if (retailer[j].inventory[n - 1] + retailer[j].incomingShipment[n] - retailer[j].total_backlog[n - 1]
                    + retailer[j].ongoing[n] < retailer[j].orderLevel[n]):
                retailer[j].order[n] = (retailer[j].orderLevel[n] - (retailer[j].inventory[n - 1]
                                                                     + retailer[j].incomingShipment[n] -
                                                                     retailer[j].total_backlog[n - 1]
                                                                     + retailer[j].ongoing[n]))
            else:
                retailer[j].order[n] = 0

            distributor[j].forecast_mean[n] = (forecast_smoothing * distributor[j].total_demand[n - 1]
                                               + (1 - forecast_smoothing) * distributor[j].forecast_mean[n - 1])
            distributor[j].forecast_var[n] = (forecast_smoothing * (distributor[j].total_demand[n - 1]
                                                                    - distributor[j].forecast_mean[n]) ** 2
                                              + (1 - forecast_smoothing) * distributor[j].forecast_var[n - 1])
            distributor[j].orderLevel[n] = int(distributor[j].forecast_mean[n] * (lead_time + 1)
                                               + 1.29 * distributor[j].forecast_var[n] ** 0.5 * (lead_time + 1) ** 0.5)
            distributor[j].ongoing[n] = sum(distributor[j].order[n - lead_time + 1:n])
            if (distributor[j].inventory[n - 1] + distributor[j].incomingShipment[n]
                    - distributor[j].total_backlog[n - 1] + distributor[j].ongoing[n] < distributor[j].orderLevel[n]):
                distributor[j].order[n] = int(distributor[j].orderLevel[n] - (distributor[j].inventory[n - 1]
                                                                              + distributor[j].incomingShipment[n] -
                                                                              distributor[j].total_backlog[n - 1]
                                                                              + distributor[j].ongoing[n]))
            else:
                distributor[j].order[n] = 0

            manufacturer[j].forecast_mean[n] = (forecast_smoothing * manufacturer[j].total_demand[n - 1]
                                                + (1 - forecast_smoothing) * manufacturer[j].forecast_mean[n - 1])
            manufacturer[j].forecast_var[n] = (forecast_smoothing * (manufacturer[j].total_demand[n - 1]
                                                                     - manufacturer[j].forecast_mean[n]) ** 2
                                               + (1 - forecast_smoothing) * manufacturer[j].forecast_var[n - 1])
            manufacturer[j].orderLevel[n] = int(manufacturer[j].forecast_mean[n] * (lead_time + 1)
                                                + 1.29 * manufacturer[j].forecast_var[n] ** 0.5 * (
                                                lead_time + 1) ** 0.5)
            manufacturer[j].ongoing[n] = sum(manufacturer[j].order[n - lead_time + 1:n])
            if (manufacturer[j].inventory[n - 1] + manufacturer[j].incomingShipment[n]
                    - manufacturer[j].total_backlog[n - 1]
                    + manufacturer[j].ongoing[n] < manufacturer[j].orderLevel[n]):
                manufacturer[j].order[n] = (manufacturer[j].orderLevel[n] - (manufacturer[j].inventory[n - 1]
                                                                             + manufacturer[j].incomingShipment[n] -
                                                                             manufacturer[j].total_backlog[n - 1]
                                                                             + manufacturer[j].ongoing[n]))
            else:
                manufacturer[j].order[n] = 0

            supplier[j].forecast_mean[n] = (forecast_smoothing * supplier[j].total_demand[n - 1]
                                            + (1 - forecast_smoothing) * supplier[j].forecast_mean[n - 1])
            supplier[j].forecast_var[n] = (forecast_smoothing * (supplier[j].total_demand[n - 1]
                                                                 - supplier[j].forecast_mean[n]) ** 2
                                           + (1 - forecast_smoothing) * supplier[j].forecast_var[n - 1])
            supplier[j].orderLevel[n] = int(supplier[j].forecast_mean[n] * (lead_time + 1)
                                            + 1.29 * supplier[j].forecast_var[n] ** 0.5 * (lead_time + 1) ** 0.5)
            supplier[j].ongoing[n] = sum(supplier[j].order[n - lead_time + 1:n])
            if (supplier[j].inventory[n - 1] + supplier[j].incomingShipment[n]
                    - supplier[j].total_backlog[n - 1]
                    + supplier[j].ongoing[n] < supplier[j].orderLevel[n]):
                supplier[j].order[n] = (supplier[j].orderLevel[n] - (supplier[j].inventory[n - 1]
                                                                     + supplier[j].incomingShipment[n] -
                                                                     supplier[j].total_backlog[n - 1]
                                                                     + supplier[j].ongoing[n]))
            else:
                supplier[j].order[n] = 0

            # determine the demand for each echelon
            temp1 = 0
            temp2 = 0
            temp3 = 0
            for k in range(scale):
                distributor[j].demand[k][n] = int(retailer[k].order[n - int(lead_time / 2)] / scale)
                manufacturer[j].demand[k][n] = int(distributor[k].order[n - int(lead_time / 2)] / scale)
                supplier[j].demand[k][n] = int(manufacturer[k].order[n - int(lead_time / 2)] / scale)
                temp1 += distributor[j].demand[k][n]
                temp2 += manufacturer[j].demand[k][n]
                temp3 += supplier[j].demand[k][n]
            distributor[j].total_demand[n] = temp1
            manufacturer[j].total_demand[n] = temp2
            supplier[j].total_demand[n] = temp3
            # whether the demand can be satisfied or not
            temp = retailer[j].inventory[n - 1] + retailer[j].incomingShipment[n]
            bl = 0
            for k in range(scale):
                kj = (j + k) % scale
                if temp > retailer[j].backlog[kj][n - 1] + retailer[j].demand[kj][n]:
                    retailer[j].outgoingShipment[kj][n] = \
                        retailer[j].demand[kj][n] + retailer[j].backlog[kj][n - 1]
                    retailer[j].backlog[kj][n] = 0
                    temp -= retailer[j].backlog[kj][n - 1] + retailer[j].demand[kj][n]
                else:
                    retailer[j].outgoingShipment[kj][n] = temp
                    retailer[j].backlog[kj][n] = retailer[j].backlog[kj][n - 1] + retailer[j].demand[kj][n] - temp
                    bl += retailer[j].backlog[kj][n]
                    temp = 0
            retailer[j].inventory[n] = temp
            retailer[j].total_backlog[n] = bl

            temp = distributor[j].inventory[n - 1] + distributor[j].incomingShipment[n]
            bl = 0
            for k in range(scale):
                kj = (j + k) % scale
                if temp > distributor[j].backlog[kj][n - 1] + distributor[j].demand[kj][n]:
                    distributor[j].outgoingShipment[kj][n] = \
                        distributor[j].demand[kj][n] + distributor[j].backlog[kj][n - 1]
                    distributor[j].backlog[kj][n] = 0
                    temp -= distributor[j].backlog[kj][n - 1] + distributor[j].demand[kj][n]
                else:
                    distributor[j].outgoingShipment[kj][n] = temp
                    distributor[j].backlog[kj][n] = distributor[j].backlog[kj][n - 1] + distributor[j].demand[kj][
                        n] - temp
                    bl += distributor[j].backlog[kj][n]
                    temp = 0
            distributor[j].inventory[n] = temp
            distributor[j].total_backlog[n] = bl

            temp = manufacturer[j].inventory[n - 1] + manufacturer[j].incomingShipment[n]
            bl = 0
            for k in range(scale):
                kj = (j + k) % scale
                if temp > manufacturer[j].backlog[kj][n - 1] + manufacturer[j].demand[kj][n]:
                    manufacturer[j].outgoingShipment[kj][n] = \
                        manufacturer[j].demand[kj][n] + manufacturer[j].backlog[kj][n - 1]
                    manufacturer[j].backlog[kj][n] = 0
                    temp -= manufacturer[j].backlog[kj][n - 1] + manufacturer[j].demand[kj][n]
                else:
                    manufacturer[j].outgoingShipment[kj][n] = temp
                    manufacturer[j].backlog[kj][n] = manufacturer[j].backlog[kj][n - 1] + manufacturer[j].demand[kj][
                        n] - temp
                    bl += manufacturer[j].backlog[kj][n]
                    temp = 0
            manufacturer[j].inventory[n] = temp
            manufacturer[j].total_backlog[n] = bl

            temp = supplier[j].inventory[n - 1] + supplier[j].incomingShipment[n]
            bl = 0
            for k in range(scale):
                kj = (j + k) % scale
                if temp > supplier[j].backlog[kj][n - 1] + supplier[j].demand[kj][n]:
                    supplier[j].outgoingShipment[kj][n] = \
                        supplier[j].demand[kj][n] + supplier[j].backlog[kj][n - 1]
                    supplier[j].backlog[kj][n] = 0
                    temp -= supplier[j].backlog[kj][n - 1] + supplier[j].demand[kj][n]
                else:
                    supplier[j].outgoingShipment[kj][n] = temp
                    supplier[j].backlog[kj][n] = supplier[j].backlog[kj][n - 1] + supplier[j].demand[kj][n] - temp
                    bl += supplier[j].backlog[kj][n]
                    temp = 0
            supplier[j].inventory[n] = temp
            supplier[j].total_backlog[n] = bl

            # ------ payment rule ------

            # calculate AR (accounts receivable)
            for m in range(scale):
                retailer[j].accounts_receivable[m][1][n] = retailer[j].outgoingShipment[m][n - int(lead_time / 2)]
                for k in range(1, 11):
                    if 14 * k < retailer[j].min[m]:
                        retailer[j].accounts_receivable[m][k + 1][n] \
                            = retailer[j].accounts_receivable[m][k][n - 1]
                    elif 14 * (k - 1) < retailer[j].min[m]:
                        if (numpy.random.rand() < (
                                    1 - math.exp(-(14 * k - retailer[j].min[m]) ** 2 / retailer[j].lam[m] ** 2))
                                and retailer[j].accounts_receivable[m][k][n - 1] != 0):
                            retailer[j].accounts_receivable[m][k + 1][n] = 0
                            retailer[j].accounts_receivable[m][0][n] += retailer[j].accounts_receivable[m][k][n - 1]
                            retailer[j].daysOut[m].append(14 * (k - 1) + 7)
                        else:
                            retailer[j].accounts_receivable[m][k + 1][n] \
                                = retailer[j].accounts_receivable[m][k][n - 1]
                    else:
                        if (numpy.random.rand() < (
                                    1 - math.exp(
                                        -(2 * ((k - 1) * 14 - retailer[j].min[m]) * 14 + 14 ** 2) / retailer[j].lam[
                                        m] ** 2))
                                and retailer[j].accounts_receivable[m][k][n - 1] != 0):
                            retailer[j].accounts_receivable[m][k + 1][n] = 0
                            retailer[j].accounts_receivable[m][0][n] += retailer[j].accounts_receivable[m][k][n - 1]
                            retailer[j].daysOut[m].append(14 * (k - 1) + 7)
                        else:
                            retailer[j].accounts_receivable[m][k + 1][n] \
                                = retailer[j].accounts_receivable[m][k][n - 1]
                retailer[j].individual_ar[m][0][n] = retailer[j].accounts_receivable[m, 0, n]
                retailer[j].individual_ar[m][1][n] = sum(retailer[j].accounts_receivable[m, 1:3, n])
                retailer[j].individual_ar[m][2][n] = sum(retailer[j].accounts_receivable[m, 3:5, n])
                retailer[j].individual_ar[m][3][n] = sum(retailer[j].accounts_receivable[m, 5:7, n])
                retailer[j].individual_ar[m][4][n] = sum(retailer[j].accounts_receivable[m, 7:9, n])
                retailer[j].individual_ar[m][5][n] = sum(retailer[j].accounts_receivable[m, 9:11, n])
            retailer[j].ar[0][n] = sum(retailer[j].accounts_receivable[:, 0, n])
            retailer[j].ar[1][n] = sum(sum(retailer[j].accounts_receivable[:, 1:3, n]))
            retailer[j].ar[2][n] = sum(sum(retailer[j].accounts_receivable[:, 3:5, n]))
            retailer[j].ar[3][n] = sum(sum(retailer[j].accounts_receivable[:, 5:7, n]))
            retailer[j].ar[4][n] = sum(sum(retailer[j].accounts_receivable[:, 7:9, n]))
            retailer[j].ar[5][n] = sum(sum(retailer[j].accounts_receivable[:, 9:11, n]))

            for m in range(scale):
                distributor[j].accounts_receivable[m][1][n] = distributor[j].outgoingShipment[m][n - int(lead_time / 2)]
                for k in range(1, 11):
                    if 14 * k < distributor[j].min[m]:
                        distributor[j].accounts_receivable[m][k + 1][n] \
                            = distributor[j].accounts_receivable[m][k][n - 1]
                    elif 14 * (k - 1) < distributor[j].min[m]:
                        if (numpy.random.rand() < (
                                    1 - math.exp(-(14 * k - distributor[j].min[m]) ** 2 / distributor[j].lam[m] ** 2))
                                and distributor[j].accounts_receivable[m][k][n - 1] != 0):
                            distributor[j].accounts_receivable[m][k + 1][n] = 0
                            distributor[j].accounts_receivable[m][0][n] += distributor[j].accounts_receivable[m][k][
                                n - 1]
                            distributor[j].daysOut[m].append(14 * (k - 1) + 7)
                        else:
                            distributor[j].accounts_receivable[m][k + 1][n] \
                                = distributor[j].accounts_receivable[m][k][n - 1]
                    else:
                        if (numpy.random.rand() < (
                                    1 - math.exp(
                                        -(2 * ((k - 1) * 14 - distributor[j].min[m]) * 14 + 14 ** 2) /
                                                distributor[j].lam[m] ** 2))
                                and distributor[j].accounts_receivable[m][k][n - 1] != 0):
                            distributor[j].accounts_receivable[m][k + 1][n] = 0
                            distributor[j].accounts_receivable[m][0][n] += distributor[j].accounts_receivable[m][k][
                                n - 1]
                            distributor[j].daysOut[m].append(14 * (k - 1) + 7)
                        else:
                            distributor[j].accounts_receivable[m][k + 1][n] \
                                = distributor[j].accounts_receivable[m][k][n - 1]
                distributor[j].individual_ar[m][0][n] = distributor[j].accounts_receivable[m, 0, n]
                distributor[j].individual_ar[m][1][n] = sum(distributor[j].accounts_receivable[m, 1:3, n])
                distributor[j].individual_ar[m][2][n] = sum(distributor[j].accounts_receivable[m, 3:5, n])
                distributor[j].individual_ar[m][3][n] = sum(distributor[j].accounts_receivable[m, 5:7, n])
                distributor[j].individual_ar[m][4][n] = sum(distributor[j].accounts_receivable[m, 7:9, n])
                distributor[j].individual_ar[m][5][n] = sum(distributor[j].accounts_receivable[m, 9:11, n])
            distributor[j].ar[0][n] = sum(distributor[j].accounts_receivable[:, 0, n])
            distributor[j].ar[1][n] = sum(sum(distributor[j].accounts_receivable[:, 1:3, n]))
            distributor[j].ar[2][n] = sum(sum(distributor[j].accounts_receivable[:, 3:5, n]))
            distributor[j].ar[3][n] = sum(sum(distributor[j].accounts_receivable[:, 5:7, n]))
            distributor[j].ar[4][n] = sum(sum(distributor[j].accounts_receivable[:, 7:9, n]))
            distributor[j].ar[5][n] = sum(sum(distributor[j].accounts_receivable[:, 9:11, n]))

            for m in range(scale):
                manufacturer[j].accounts_receivable[m][1][n] = manufacturer[j].outgoingShipment[m][
                    n - int(lead_time / 2)]
                for k in range(1, 11):
                    if 14 * k < manufacturer[j].min[m]:
                        manufacturer[j].accounts_receivable[m][k + 1][n] \
                            = manufacturer[j].accounts_receivable[m][k][n - 1]
                    elif 14 * (k - 1) < manufacturer[j].min[m]:
                        if (numpy.random.rand() < (
                                    1 - math.exp(-(14 * k - manufacturer[j].min[m]) ** 2 / manufacturer[j].lam[m] ** 2))
                                and manufacturer[j].accounts_receivable[m][k][n - 1] != 0):
                            manufacturer[j].accounts_receivable[m][k + 1][n] = 0
                            manufacturer[j].accounts_receivable[m][0][n] += manufacturer[j].accounts_receivable[m][k][
                                n - 1]
                            manufacturer[j].daysOut[m].append(14 * (k - 1) + 7)
                        else:
                            manufacturer[j].accounts_receivable[m][k + 1][n] \
                                = manufacturer[j].accounts_receivable[m][k][n - 1]
                    else:
                        if (numpy.random.rand() < (
                                    1 - math.exp(
                                        -(2 * ((k - 1) * 14 - manufacturer[j].min[m]) * 14 + 14 ** 2) /
                                            manufacturer[j].lam[m] ** 2))
                                and manufacturer[j].accounts_receivable[m][k][n - 1] != 0):
                            manufacturer[j].accounts_receivable[m][k + 1][n] = 0
                            manufacturer[j].accounts_receivable[m][0][n] += manufacturer[j].accounts_receivable[m][k][
                                n - 1]
                            manufacturer[j].daysOut[m].append(14 * (k - 1) + 7)
                        else:
                            manufacturer[j].accounts_receivable[m][k + 1][n] \
                                = manufacturer[j].accounts_receivable[m][k][n - 1]
                manufacturer[j].individual_ar[m][0][n] = manufacturer[j].accounts_receivable[m, 0, n]
                manufacturer[j].individual_ar[m][1][n] = sum(manufacturer[j].accounts_receivable[m, 1:3, n])
                manufacturer[j].individual_ar[m][2][n] = sum(manufacturer[j].accounts_receivable[m, 3:5, n])
                manufacturer[j].individual_ar[m][3][n] = sum(manufacturer[j].accounts_receivable[m, 5:7, n])
                manufacturer[j].individual_ar[m][4][n] = sum(manufacturer[j].accounts_receivable[m, 7:9, n])
                manufacturer[j].individual_ar[m][5][n] = sum(manufacturer[j].accounts_receivable[m, 9:11, n])
            manufacturer[j].ar[0][n] = sum(manufacturer[j].accounts_receivable[:, 0, n])
            manufacturer[j].ar[1][n] = sum(sum(manufacturer[j].accounts_receivable[:, 1:3, n]))
            manufacturer[j].ar[2][n] = sum(sum(manufacturer[j].accounts_receivable[:, 3:5, n]))
            manufacturer[j].ar[3][n] = sum(sum(manufacturer[j].accounts_receivable[:, 5:7, n]))
            manufacturer[j].ar[4][n] = sum(sum(manufacturer[j].accounts_receivable[:, 7:9, n]))
            manufacturer[j].ar[5][n] = sum(sum(manufacturer[j].accounts_receivable[:, 9:11, n]))

            for m in range(scale):
                supplier[j].accounts_receivable[m][1][n] = supplier[j].outgoingShipment[m][n - int(lead_time / 2)]
                for k in range(1, 11):
                    if 14 * k < supplier[j].min[m]:
                        supplier[j].accounts_receivable[m][k + 1][n] \
                            = supplier[j].accounts_receivable[m][k][n - 1]
                    elif 14 * (k - 1) < supplier[j].min[m]:
                        if (numpy.random.rand() < (
                                    1 - math.exp(-(14 * k - supplier[j].min[m]) ** 2 / supplier[j].lam[m] ** 2))
                                and supplier[j].accounts_receivable[m][k][n - 1] != 0):
                            supplier[j].accounts_receivable[m][k + 1][n] = 0
                            supplier[j].accounts_receivable[m][0][n] += supplier[j].accounts_receivable[m][k][n - 1]
                            supplier[j].daysOut[m].append(14 * (k - 1) + 7)
                        else:
                            supplier[j].accounts_receivable[m][k + 1][n] \
                                = supplier[j].accounts_receivable[m][k][n - 1]
                    else:
                        if (numpy.random.rand() < (
                                    1 - math.exp(
                                        -(2 * ((k - 1) * 14 - supplier[j].min[m]) * 14 + 14 ** 2) / supplier[j].lam[
                                        m] ** 2))
                                and supplier[j].accounts_receivable[m][k][n - 1] != 0):
                            supplier[j].accounts_receivable[m][k + 1][n] = 0
                            supplier[j].accounts_receivable[m][0][n] += supplier[j].accounts_receivable[m][k][n - 1]
                            supplier[j].daysOut[m].append(14 * (k - 1) + 7)
                        else:
                            supplier[j].accounts_receivable[m][k + 1][n] \
                                = supplier[j].accounts_receivable[m][k][n - 1]
                supplier[j].individual_ar[m][0][n] = supplier[j].accounts_receivable[m, 0, n]
                supplier[j].individual_ar[m][1][n] = sum(supplier[j].accounts_receivable[m, 1:3, n])
                supplier[j].individual_ar[m][2][n] = sum(supplier[j].accounts_receivable[m, 3:5, n])
                supplier[j].individual_ar[m][3][n] = sum(supplier[j].accounts_receivable[m, 5:7, n])
                supplier[j].individual_ar[m][4][n] = sum(supplier[j].accounts_receivable[m, 7:9, n])
                supplier[j].individual_ar[m][5][n] = sum(supplier[j].accounts_receivable[m, 9:11, n])
            supplier[j].ar[0][n] = sum(supplier[j].accounts_receivable[:, 0, n])
            supplier[j].ar[1][n] = sum(sum(supplier[j].accounts_receivable[:, 1:3, n]))
            supplier[j].ar[2][n] = sum(sum(supplier[j].accounts_receivable[:, 3:5, n]))
            supplier[j].ar[3][n] = sum(sum(supplier[j].accounts_receivable[:, 5:7, n]))
            supplier[j].ar[4][n] = sum(sum(supplier[j].accounts_receivable[:, 7:9, n]))
            supplier[j].ar[5][n] = sum(sum(supplier[j].accounts_receivable[:, 9:11, n]))

            # ------ forecast cash flow ------

            # we only choose every two periods to forecast
            if n % 2 == 1:
                n2 = int(n / 2)
                # Markov chain
                for k in range(4):
                    if retailer[j].ar[k + 1, n - 2] != 0:
                        retailer[j].pM[k, n2] = (retailer[j].ar[k + 1, n - 2] - retailer[j].ar[k + 2, n]) \
                                                / retailer[j].ar[k + 1, n - 2]
                    else:
                        retailer[j].pM[k, n2] = 0

                    if distributor[j].ar[k + 1, n - 2] != 0:
                        distributor[j].pM[k, n2] = (distributor[j].ar[k + 1, n - 2] - distributor[j].ar[k + 2, n]) \
                                                   / distributor[j].ar[k + 1, n - 2]
                    else:
                        distributor[j].pM[k, n2] = 0

                    if manufacturer[j].ar[k + 1, n - 2] != 0:
                        manufacturer[j].pM[k, n2] = (manufacturer[j].ar[k + 1, n - 2] - manufacturer[j].ar[k + 2, n]) \
                                                    / manufacturer[j].ar[k + 1, n - 2]
                    else:
                        manufacturer[j].pM[k, n2] = 0

                    if supplier[j].ar[k + 1, n - 2] != 0:
                        supplier[j].pM[k, n2] = (supplier[j].ar[k + 1, n - 2] - supplier[j].ar[k + 2, n]) \
                                                / supplier[j].ar[k + 1, n - 2]
                    else:
                        supplier[j].pM[k, n2] = 0
                # Pate-Cornell
                for m in range(scale):
                    retailer[j].eLambda[m][n2] = max(2 * (numpy.mean(retailer[j].daysOut[m])
                                                          - min(retailer[j].daysOut[m])) / math.pi ** 0.5, 0.01)
                    for k in range(0, 4):
                        if (k + 1) * 28 < min(retailer[j].daysOut[m]):
                            retailer[j].pB[m, k, n2] = 0
                        elif k * 28 < min(retailer[j].daysOut[m]):
                            retailer[j].pB[m, k, n2] = 1 - math.exp(-(((k + 1) * 28 - min(retailer[j].daysOut[m]))
                                                                      / retailer[j].eLambda[m][n2]) ** 2)
                        else:
                            retailer[j].pB[m, k, n2] = 1 - math.exp(
                                -(2 * (k * 28 - min(retailer[j].daysOut[m])) * 28 + 28 ** 2)
                                / retailer[j].eLambda[m, n2] ** 2)

                    distributor[j].eLambda[m][n2] = max(2 * (numpy.mean(distributor[j].daysOut[m])
                                                             - min(distributor[j].daysOut[m])) / math.pi ** 0.5, 0.01)
                    for k in range(0, 4):
                        if (k + 1) * 28 < min(distributor[j].daysOut[m]):
                            distributor[j].pB[m, k, n2] = 0
                        elif k * 28 < min(distributor[j].daysOut[m]):
                            distributor[j].pB[m, k, n2] = 1 - math.exp(-(((k + 1) * 28 - min(distributor[j].daysOut[m]))
                                                                         / distributor[j].eLambda[m][n2]) ** 2)
                        else:
                            distributor[j].pB[m, k, n2] = 1 - math.exp(
                                -(2 * (k * 28 - min(distributor[j].daysOut[m])) * 28 + 28 ** 2)
                                / distributor[j].eLambda[m, n2] ** 2)

                    manufacturer[j].eLambda[m][n2] = max(2 * (numpy.mean(manufacturer[j].daysOut[m])
                                                              - min(manufacturer[j].daysOut[m])) / math.pi ** 0.5, 0.01)
                    for k in range(0, 4):
                        if (k + 1) * 28 < min(manufacturer[j].daysOut[m]):
                            manufacturer[j].pB[m, k, n2] = 0
                        elif k * 28 < min(manufacturer[j].daysOut[m]):
                            manufacturer[j].pB[m, k, n2] = 1 - math.exp(
                                -(((k + 1) * 28 - min(manufacturer[j].daysOut[m]))
                                  / manufacturer[j].eLambda[m][n2]) ** 2)
                        else:
                            manufacturer[j].pB[m, k, n2] = 1 - math.exp(
                                -(2 * (k * 28 - min(manufacturer[j].daysOut[m])) * 28 + 28 ** 2)
                                / manufacturer[j].eLambda[m, n2] ** 2)

                    supplier[j].eLambda[m][n2] = max(2 * (numpy.mean(supplier[j].daysOut[m])
                                                          - min(supplier[j].daysOut[m])) / math.pi ** 0.5, 0.01)
                    for k in range(0, 4):
                        if (k + 1) * 28 < min(supplier[j].daysOut[m]):
                            supplier[j].pB[m, k, n2] = 0
                        elif k * 28 < min(supplier[j].daysOut[m]):
                            supplier[j].pB[m, k, n2] = 1 - math.exp(-(((k + 1) * 28 - min(supplier[j].daysOut[m]))
                                                                      / supplier[j].eLambda[m][n2]) ** 2)
                        else:
                            supplier[j].pB[m, k, n2] = 1 - math.exp(
                                -(2 * (k * 28 - min(supplier[j].daysOut[m])) * 28 + 28 ** 2)
                                / supplier[j].eLambda[m, n2] ** 2)

                # exponential smoothing
                for k in range(4):
                    for m in range(scale):
                        retailer[j].pP[m, k, n2] = beta * retailer[j].pM[k, n2] \
                                                   + (1 - beta) * retailer[j].pB[m, k, n2]
                        retailer[j].aP[m, k, n2] = (alpha * retailer[j].pP[m, k, n2]
                                                    + (1 - alpha) * retailer[j].aP[m, k, n2 - 1])
                        retailer[j].aM[m, k, n2] = (alpha * retailer[j].pM[k, n2]
                                                    + (1 - alpha) * retailer[j].aM[m, k, n2 - 1])
                        retailer[j].aB[m, k, n2] = (alpha * retailer[j].pB[m, k, n2]
                                                    + (1 - alpha) * retailer[j].aB[m, k, n2 - 1])
                        distributor[j].pP[m, k, n2] = beta * distributor[j].pM[k, n2] \
                                                        + (1 - beta) * distributor[j].pB[m, k, n2]
                        distributor[j].aP[m, k, n2] = (alpha * distributor[j].pP[m, k, n2]
                                                       + (1 - alpha) * distributor[j].aP[m, k, n2 - 1])
                        distributor[j].aM[m, k, n2] = (alpha * distributor[j].pM[k, n2]
                                                       + (1 - alpha) * distributor[j].aM[m, k, n2 - 1])
                        distributor[j].aB[m, k, n2] = (alpha * distributor[j].pB[m, k, n2]
                                                       + (1 - alpha) * distributor[j].aB[m, k, n2 - 1])
                        manufacturer[j].pP[m, k, n2] = beta * manufacturer[j].pM[k, n2] \
                                                            + (1 - beta) * manufacturer[j].pB[m, k, n2]
                        manufacturer[j].aP[m, k, n2] = (alpha * manufacturer[j].pP[m, k, n2]
                                                        + (1 - alpha) * manufacturer[j].aP[m, k, n2 - 1])
                        manufacturer[j].aM[m, k, n2] = (alpha * manufacturer[j].pM[k, n2]
                                                        + (1 - alpha) * manufacturer[j].aM[m, k, n2 - 1])
                        manufacturer[j].aB[m, k, n2] = (alpha * manufacturer[j].pB[m, k, n2]
                                                        + (1 - alpha) * manufacturer[j].aB[m, k, n2 - 1])
                        supplier[j].pP[m, k, n2] = beta * supplier[j].pM[k, n2] \
                                                   + (1 - beta) * supplier[j].pB[m, k, n2]
                        supplier[j].aP[m, k, n2] = (alpha * supplier[j].pP[m, k, n2]
                                                    + (1 - alpha) * supplier[j].aP[m, k, n2 - 1])
                        supplier[j].aM[m, k, n2] = (alpha * supplier[j].pM[k, n2]
                                                    + (1 - alpha) * supplier[j].aM[m, k, n2 - 1])
                        supplier[j].aB[m, k, n2] = (alpha * supplier[j].pB[m, k, n2]
                                                    + (1 - alpha) * supplier[j].aB[m, k, n2 - 1])
                        
                        # parameter set 2
                        retailer[j].pP2[m, k, n2] = beta2 * retailer[j].pM[k, n2] \
                                                    + (1 - beta2) * retailer[j].pB[m, k, n2]
                        retailer[j].aP2[m, k, n2] = (alpha2 * retailer[j].pP2[m, k, n2]
                                                        + (1 - alpha2) * retailer[j].aP2[m, k, n2 - 1])
                        distributor[j].pP2[m, k, n2] = beta2 * distributor[j].pM[k, n2] \
                                                        + (1 - beta2) * distributor[j].pB[m, k, n2]
                        distributor[j].aP2[m, k, n2] = (alpha2 * distributor[j].pP2[m, k, n2]
                                                     + (1 - alpha2) * distributor[j].aP2[m, k, n2 - 1])
                        manufacturer[j].pP2[m, k, n2] = beta2 * manufacturer[j].pM[k, n2] \
                                                    + (1 - beta2) * manufacturer[j].pB[m, k, n2]
                        manufacturer[j].aP2[m, k, n2] = (alpha2 * manufacturer[j].pP2[m, k, n2]
                                                         + (1 - alpha2) * manufacturer[j].aP2[m, k, n2 - 1])
                        supplier[j].pP2[m, k, n2] = beta2 * supplier[j].pM[k, n2] \
                                                    + (1 - beta2) * supplier[j].pB[m, k, n2]
                        supplier[j].aP2[m, k, n2] = (alpha2 * supplier[j].pP2[m, k, n2]
                                                     + (1 - alpha2) * supplier[j].aP2[m, k, n2 - 1])
                        # parameter set 3
                        retailer[j].pP3[m, k, n2] = beta3 * retailer[j].pM[k, n2] \
                                                    + (1 - beta3) * retailer[j].pB[m, k, n2]
                        retailer[j].aP3[m, k, n2] = (alpha3 * retailer[j].pP3[m, k, n2]
                                                     + (1 - alpha3) * retailer[j].aP3[m, k, n2 - 1])
                        distributor[j].pP3[m, k, n2] = beta3 * distributor[j].pM[k, n2] \
                                                       + (1 - beta3) * distributor[j].pB[m, k, n2]
                        distributor[j].aP3[m, k, n2] = (alpha3 * distributor[j].pP3[m, k, n2]
                                                        + (1 - alpha3) * distributor[j].aP3[m, k, n2 - 1])
                        manufacturer[j].pP3[m, k, n2] = beta3 * manufacturer[j].pM[k, n2] \
                                                        + (1 - beta3) * manufacturer[j].pB[m, k, n2]
                        manufacturer[j].aP3[m, k, n2] = (alpha3 * manufacturer[j].pP3[m, k, n2]
                                                         + (1 - alpha3) * manufacturer[j].aP3[m, k, n2 - 1])
                        supplier[j].pP3[m, k, n2] = beta3 * supplier[j].pM[k, n2] \
                                                    + (1 - beta3) * supplier[j].pB[m, k, n2]
                        supplier[j].aP3[m, k, n2] = (alpha3 * supplier[j].pP3[m, k, n2]
                                                     + (1 - alpha3) * supplier[j].aP3[m, k, n2 - 1])
                        # parameter set 4
                        retailer[j].pP4[m, k, n2] = beta4 * retailer[j].pM[k, n2] \
                                                    + (1 - beta4) * retailer[j].pB[m, k, n2]
                        retailer[j].aP4[m, k, n2] = (alpha4 * retailer[j].pP4[m, k, n2]
                                                     + (1 - alpha4) * retailer[j].aP4[m, k, n2 - 1])
                        distributor[j].pP4[m, k, n2] = beta4 * distributor[j].pM[k, n2] \
                                                       + (1 - beta4) * distributor[j].pB[m, k, n2]
                        distributor[j].aP4[m, k, n2] = (alpha4 * distributor[j].pP4[m, k, n2]
                                                        + (1 - alpha4) * distributor[j].aP4[m, k, n2 - 1])
                        manufacturer[j].pP4[m, k, n2] = beta4 * manufacturer[j].pM[k, n2] \
                                                        + (1 - beta4) * manufacturer[j].pB[m, k, n2]
                        manufacturer[j].aP4[m, k, n2] = (alpha4 * manufacturer[j].pP4[m, k, n2]
                                                         + (1 - alpha4) * manufacturer[j].aP4[m, k, n2 - 1])
                        supplier[j].pP4[m, k, n2] = beta4 * supplier[j].pM[k, n2] \
                                                    + (1 - beta4) * supplier[j].pB[m, k, n2]
                        supplier[j].aP4[m, k, n2] = (alpha4 * supplier[j].pP4[m, k, n2]
                                                     + (1 - alpha4) * supplier[j].aP4[m, k, n2 - 1])
                        # parameter set 5
                        retailer[j].pP5[m, k, n2] = beta5 * retailer[j].pM[k, n2] \
                                                    + (1 - beta5) * retailer[j].pB[m, k, n2]
                        retailer[j].aP5[m, k, n2] = (alpha5 * retailer[j].pP5[m, k, n2]
                                                     + (1 - alpha5) * retailer[j].aP5[m, k, n2 - 1])
                        distributor[j].pP5[m, k, n2] = beta5 * distributor[j].pM[k, n2] \
                                                       + (1 - beta5) * distributor[j].pB[m, k, n2]
                        distributor[j].aP5[m, k, n2] = (alpha5 * distributor[j].pP5[m, k, n2]
                                                        + (1 - alpha5) * distributor[j].aP5[m, k, n2 - 1])
                        manufacturer[j].pP5[m, k, n2] = beta5 * manufacturer[j].pM[k, n2] \
                                                        + (1 - beta5) * manufacturer[j].pB[m, k, n2]
                        manufacturer[j].aP5[m, k, n2] = (alpha5 * manufacturer[j].pP5[m, k, n2]
                                                         + (1 - alpha5) * manufacturer[j].aP5[m, k, n2 - 1])
                        supplier[j].pP5[m, k, n2] = beta5 * supplier[j].pM[k, n2] \
                                                    + (1 - beta5) * supplier[j].pB[m, k, n2]
                        supplier[j].aP5[m, k, n2] = (alpha5 * supplier[j].pP5[m, k, n2]
                                                     + (1 - alpha5) * supplier[j].aP5[m, k, n2 - 1])
                
                # forecast income
                for m in range(scale):
                    retailer[j].forecast_income[n2] += (retailer[j].individual_ar[m, 1, n - 2]
                                                        * retailer[j].aP[m, 0, n2 - 1]
                                                        + retailer[j].individual_ar[m, 2, n - 2]
                                                        * retailer[j].aP[m, 1, n2 - 1]
                                                        + retailer[j].individual_ar[m, 3, n - 2]
                                                        * retailer[j].aP[m, 2, n2 - 1]
                                                        + retailer[j].individual_ar[m, 4, n - 2]
                                                        * retailer[j].aP[m, 3, n2 - 1])
                    retailer[j].forecast_income_mc[n2] += (retailer[j].individual_ar[m, 1, n - 2]
                                                           * retailer[j].aM[m, 0, n2 - 1]
                                                           + retailer[j].individual_ar[m, 2, n - 2]
                                                           * retailer[j].aM[m, 1, n2 - 1]
                                                           + retailer[j].individual_ar[m, 3, n - 2]
                                                           * retailer[j].aM[m, 2, n2 - 1]
                                                           + retailer[j].individual_ar[m, 4, n - 2]
                                                           * retailer[j].aM[m, 3, n2 - 1])
                    retailer[j].forecast_income_Pete[n2] += (retailer[j].individual_ar[m, 1, n - 2]
                                                             * retailer[j].aB[m, 0, n2 - 1]
                                                             + retailer[j].individual_ar[m, 2, n - 2]
                                                             * retailer[j].aB[m, 1, n2 - 1]
                                                             + retailer[j].individual_ar[m, 3, n - 2]
                                                             * retailer[j].aB[m, 2, n2 - 1]
                                                             + retailer[j].individual_ar[m, 4, n - 2]
                                                             * retailer[j].aB[m, 3, n2 - 1])
                    retailer[j].forecast_income2[n2] += (retailer[j].individual_ar[m, 1, n - 2]
                                                         * retailer[j].aP2[m, 0, n2 - 1]
                                                         + retailer[j].individual_ar[m, 2, n - 2]
                                                         * retailer[j].aP2[m, 1, n2 - 1]
                                                         + retailer[j].individual_ar[m, 3, n - 2]
                                                         * retailer[j].aP2[m, 2, n2 - 1]
                                                         + retailer[j].individual_ar[m, 4, n - 2]
                                                         * retailer[j].aP2[m, 3, n2 - 1])
                    retailer[j].forecast_income3[n2] += (retailer[j].individual_ar[m, 1, n - 2]
                                                         * retailer[j].aP3[m, 0, n2 - 1]
                                                         + retailer[j].individual_ar[m, 2, n - 2]
                                                         * retailer[j].aP3[m, 1, n2 - 1]
                                                         + retailer[j].individual_ar[m, 3, n - 2]
                                                         * retailer[j].aP3[m, 2, n2 - 1]
                                                         + retailer[j].individual_ar[m, 4, n - 2]
                                                         * retailer[j].aP3[m, 3, n2 - 1])
                    retailer[j].forecast_income4[n2] += (retailer[j].individual_ar[m, 1, n - 2]
                                                         * retailer[j].aP4[m, 0, n2 - 1]
                                                         + retailer[j].individual_ar[m, 2, n - 2]
                                                         * retailer[j].aP4[m, 1, n2 - 1]
                                                         + retailer[j].individual_ar[m, 3, n - 2]
                                                         * retailer[j].aP4[m, 2, n2 - 1]
                                                         + retailer[j].individual_ar[m, 4, n - 2]
                                                         * retailer[j].aP4[m, 3, n2 - 1])
                    retailer[j].forecast_income5[n2] += (retailer[j].individual_ar[m, 1, n - 2]
                                                         * retailer[j].aP5[m, 0, n2 - 1]
                                                         + retailer[j].individual_ar[m, 2, n - 2]
                                                         * retailer[j].aP5[m, 1, n2 - 1]
                                                         + retailer[j].individual_ar[m, 3, n - 2]
                                                         * retailer[j].aP5[m, 2, n2 - 1]
                                                         + retailer[j].individual_ar[m, 4, n - 2]
                                                         * retailer[j].aP5[m, 3, n2 - 1])

                retailer[j].difference[n2] = abs(retailer[j].ar[0, n - 1] + retailer[j].ar[0, n]
                                                 - retailer[j].forecast_income[n2])
                retailer[j].difference_mc[n2] = abs(retailer[j].ar[0, n - 1] + retailer[j].ar[0, n]
                                                    - retailer[j].forecast_income_mc[n2])
                retailer[j].difference_Pete[n2] = abs(retailer[j].ar[0, n - 1] + retailer[j].ar[0, n]
                                                   - retailer[j].forecast_income_Pete[n2])
                retailer[j].difference2[n2] = abs(retailer[j].ar[0, n - 1] + retailer[j].ar[0, n]
                                                  - retailer[j].forecast_income2[n2])
                retailer[j].difference3[n2] = abs(retailer[j].ar[0, n - 1] + retailer[j].ar[0, n]
                                                  - retailer[j].forecast_income3[n2])
                retailer[j].difference4[n2] = abs(retailer[j].ar[0, n - 1] + retailer[j].ar[0, n]
                                                  - retailer[j].forecast_income4[n2])
                retailer[j].difference5[n2] = abs(retailer[j].ar[0, n - 1] + retailer[j].ar[0, n]
                                                  - retailer[j].forecast_income5[n2])

                for m in range(scale):
                    distributor[j].forecast_income[n2] += (distributor[j].individual_ar[m, 1, n - 2]
                                                           * distributor[j].aP[m, 0, n2 - 1]
                                                           + distributor[j].individual_ar[m, 2, n - 2]
                                                           * distributor[j].aP[m, 1, n2 - 1]
                                                           + distributor[j].individual_ar[m, 3, n - 2]
                                                           * distributor[j].aP[m, 2, n2 - 1]
                                                           + distributor[j].individual_ar[m, 4, n - 2]
                                                           * distributor[j].aP[m, 3, n2 - 1])
                    distributor[j].forecast_income_mc[n2] += (distributor[j].individual_ar[m, 1, n - 2]
                                                              * distributor[j].aM[m, 0, n2 - 1]
                                                              + distributor[j].individual_ar[m, 2, n - 2]
                                                              * distributor[j].aM[m, 1, n2 - 1]
                                                              + distributor[j].individual_ar[m, 3, n - 2]
                                                              * distributor[j].aM[m, 2, n2 - 1]
                                                              + distributor[j].individual_ar[m, 4, n - 2]
                                                              * distributor[j].aM[m, 3, n2 - 1])
                    distributor[j].forecast_income_Pete[n2] += (distributor[j].individual_ar[m, 1, n - 2]
                                                                * distributor[j].aB[m, 0, n2 - 1]
                                                                + distributor[j].individual_ar[m, 2, n - 2]
                                                                * distributor[j].aB[m, 1, n2 - 1]
                                                                + distributor[j].individual_ar[m, 3, n - 2]
                                                                * distributor[j].aB[m, 2, n2 - 1]
                                                                + distributor[j].individual_ar[m, 4, n - 2]
                                                                * distributor[j].aB[m, 3, n2 - 1])
                    distributor[j].forecast_income2[n2] += (distributor[j].individual_ar[m, 1, n - 2]
                                                            * distributor[j].aP2[m, 0, n2 - 1]
                                                            + distributor[j].individual_ar[m, 2, n - 2]
                                                            * distributor[j].aP2[m, 1, n2 - 1]
                                                            + distributor[j].individual_ar[m, 3, n - 2]
                                                            * distributor[j].aP2[m, 2, n2 - 1]
                                                            + distributor[j].individual_ar[m, 4, n - 2]
                                                            * distributor[j].aP2[m, 3, n2 - 1])
                    distributor[j].forecast_income3[n2] += (distributor[j].individual_ar[m, 1, n - 2]
                                                            * distributor[j].aP3[m, 0, n2 - 1]
                                                            + distributor[j].individual_ar[m, 2, n - 2]
                                                            * distributor[j].aP3[m, 1, n2 - 1]
                                                            + distributor[j].individual_ar[m, 3, n - 2]
                                                            * distributor[j].aP3[m, 2, n2 - 1]
                                                            + distributor[j].individual_ar[m, 4, n - 2]
                                                            * distributor[j].aP3[m, 3, n2 - 1])
                    distributor[j].forecast_income4[n2] += (distributor[j].individual_ar[m, 1, n - 2]
                                                            * distributor[j].aP4[m, 0, n2 - 1]
                                                            + distributor[j].individual_ar[m, 2, n - 2]
                                                            * distributor[j].aP4[m, 1, n2 - 1]
                                                            + distributor[j].individual_ar[m, 3, n - 2]
                                                            * distributor[j].aP4[m, 2, n2 - 1]
                                                            + distributor[j].individual_ar[m, 4, n - 2]
                                                            * distributor[j].aP4[m, 3, n2 - 1])
                    distributor[j].forecast_income5[n2] += (distributor[j].individual_ar[m, 1, n - 2]
                                                            * distributor[j].aP5[m, 0, n2 - 1]
                                                            + distributor[j].individual_ar[m, 2, n - 2]
                                                            * distributor[j].aP5[m, 1, n2 - 1]
                                                            + distributor[j].individual_ar[m, 3, n - 2]
                                                            * distributor[j].aP5[m, 2, n2 - 1]
                                                            + distributor[j].individual_ar[m, 4, n - 2]
                                                            * distributor[j].aP5[m, 3, n2 - 1])

                distributor[j].difference[n2] = abs(distributor[j].ar[0, n - 1] + distributor[j].ar[0, n]
                                                    - distributor[j].forecast_income[n2])
                distributor[j].difference_mc[n2] = abs(distributor[j].ar[0, n - 1] + distributor[j].ar[0, n]
                                                       - distributor[j].forecast_income_mc[n2])
                distributor[j].difference_Pete[n2] = abs(distributor[j].ar[0, n - 1] + distributor[j].ar[0, n]
                                                         - distributor[j].forecast_income_Pete[n2])
                distributor[j].difference2[n2] = abs(distributor[j].ar[0, n - 1] + distributor[j].ar[0, n]
                                                    - distributor[j].forecast_income2[n2])
                distributor[j].difference3[n2] = abs(distributor[j].ar[0, n - 1] + distributor[j].ar[0, n]
                                                    - distributor[j].forecast_income3[n2])
                distributor[j].difference4[n2] = abs(distributor[j].ar[0, n - 1] + distributor[j].ar[0, n]
                                                    - distributor[j].forecast_income4[n2])
                distributor[j].difference5[n2] = abs(distributor[j].ar[0, n - 1] + distributor[j].ar[0, n]
                                                    - distributor[j].forecast_income5[n2])

                for m in range(scale):
                    manufacturer[j].forecast_income[n2] += (manufacturer[j].individual_ar[m, 1, n - 2]
                                                            * manufacturer[j].aP[m, 0, n2 - 1]
                                                            + manufacturer[j].individual_ar[m, 2, n - 2]
                                                            * manufacturer[j].aP[m, 1, n2 - 1]
                                                            + manufacturer[j].individual_ar[m, 3, n - 2]
                                                            * manufacturer[j].aP[m, 2, n2 - 1]
                                                            + manufacturer[j].individual_ar[m, 4, n - 2]
                                                            * manufacturer[j].aP[m, 3, n2 - 1])
                    manufacturer[j].forecast_income_mc[n2] += (manufacturer[j].individual_ar[m, 1, n - 2]
                                                               * manufacturer[j].aM[m, 0, n2 - 1]
                                                               + manufacturer[j].individual_ar[m, 2, n - 2]
                                                               * manufacturer[j].aM[m, 1, n2 - 1]
                                                               + manufacturer[j].individual_ar[m, 3, n - 2]
                                                               * manufacturer[j].aM[m, 2, n2 - 1]
                                                               + manufacturer[j].individual_ar[m, 4, n - 2]
                                                               * manufacturer[j].aM[m, 3, n2 - 1])
                    manufacturer[j].forecast_income_Pete[n2] += (manufacturer[j].individual_ar[m, 1, n - 2]
                                                                 * manufacturer[j].aB[m, 0, n2 - 1]
                                                                 + manufacturer[j].individual_ar[m, 2, n - 2]
                                                                 * manufacturer[j].aB[m, 1, n2 - 1]
                                                                 + manufacturer[j].individual_ar[m, 3, n - 2]
                                                                 * manufacturer[j].aB[m, 2, n2 - 1]
                                                                 + manufacturer[j].individual_ar[m, 4, n - 2]
                                                                 * manufacturer[j].aB[m, 3, n2 - 1])
                    manufacturer[j].forecast_income2[n2] += (manufacturer[j].individual_ar[m, 1, n - 2]
                                                             * manufacturer[j].aP2[m, 0, n2 - 1]
                                                             + manufacturer[j].individual_ar[m, 2, n - 2]
                                                             * manufacturer[j].aP2[m, 1, n2 - 1]
                                                             + manufacturer[j].individual_ar[m, 3, n - 2]
                                                             * manufacturer[j].aP2[m, 2, n2 - 1]
                                                             + manufacturer[j].individual_ar[m, 4, n - 2]
                                                             * manufacturer[j].aP2[m, 3, n2 - 1])
                    manufacturer[j].forecast_income3[n2] += (manufacturer[j].individual_ar[m, 1, n - 2]
                                                             * manufacturer[j].aP3[m, 0, n2 - 1]
                                                             + manufacturer[j].individual_ar[m, 2, n - 2]
                                                             * manufacturer[j].aP3[m, 1, n2 - 1]
                                                             + manufacturer[j].individual_ar[m, 3, n - 2]
                                                             * manufacturer[j].aP3[m, 2, n2 - 1]
                                                             + manufacturer[j].individual_ar[m, 4, n - 2]
                                                             * manufacturer[j].aP3[m, 3, n2 - 1])
                    manufacturer[j].forecast_income4[n2] += (manufacturer[j].individual_ar[m, 1, n - 2]
                                                             * manufacturer[j].aP4[m, 0, n2 - 1]
                                                             + manufacturer[j].individual_ar[m, 2, n - 2]
                                                             * manufacturer[j].aP4[m, 1, n2 - 1]
                                                             + manufacturer[j].individual_ar[m, 3, n - 2]
                                                             * manufacturer[j].aP4[m, 2, n2 - 1]
                                                             + manufacturer[j].individual_ar[m, 4, n - 2]
                                                             * manufacturer[j].aP4[m, 3, n2 - 1])
                    manufacturer[j].forecast_income5[n2] += (manufacturer[j].individual_ar[m, 1, n - 2]
                                                             * manufacturer[j].aP5[m, 0, n2 - 1]
                                                             + manufacturer[j].individual_ar[m, 2, n - 2]
                                                             * manufacturer[j].aP5[m, 1, n2 - 1]
                                                             + manufacturer[j].individual_ar[m, 3, n - 2]
                                                             * manufacturer[j].aP5[m, 2, n2 - 1]
                                                             + manufacturer[j].individual_ar[m, 4, n - 2]
                                                             * manufacturer[j].aP5[m, 3, n2 - 1])

                manufacturer[j].difference[n2] = abs(manufacturer[j].ar[0, n - 1] + manufacturer[j].ar[0, n]
                                                     - manufacturer[j].forecast_income[n2])
                manufacturer[j].difference_mc[n2] = abs(manufacturer[j].ar[0, n - 1] + manufacturer[j].ar[0, n]
                                                         - manufacturer[j].forecast_income_mc[n2])
                manufacturer[j].difference_Pete[n2] = abs(manufacturer[j].ar[0, n - 1] + manufacturer[j].ar[0, n]
                                                          - manufacturer[j].forecast_income_Pete[n2])
                manufacturer[j].difference2[n2] = abs(manufacturer[j].ar[0, n - 1] + manufacturer[j].ar[0, n]
                                                      - manufacturer[j].forecast_income2[n2])
                manufacturer[j].difference3[n2] = abs(manufacturer[j].ar[0, n - 1] + manufacturer[j].ar[0, n]
                                                      - manufacturer[j].forecast_income3[n2])
                manufacturer[j].difference4[n2] = abs(manufacturer[j].ar[0, n - 1] + manufacturer[j].ar[0, n]
                                                       - manufacturer[j].forecast_income4[n2])
                manufacturer[j].difference5[n2] = abs(manufacturer[j].ar[0, n - 1] + manufacturer[j].ar[0, n]
                                                       - manufacturer[j].forecast_income5[n2])

                for m in range(scale):
                    supplier[j].forecast_income[n2] += (supplier[j].individual_ar[m, 1, n - 2]
                                                        * supplier[j].aP[m, 0, n2 - 1]
                                                        + supplier[j].individual_ar[m, 2, n - 2]
                                                        * supplier[j].aP[m, 1, n2 - 1]
                                                        + supplier[j].individual_ar[m, 3, n - 2]
                                                        * supplier[j].aP[m, 2, n2 - 1]
                                                        + supplier[j].individual_ar[m, 4, n - 2]
                                                        * supplier[j].aP[m, 3, n2 - 1])
                    supplier[j].forecast_income_mc[n2] += (supplier[j].individual_ar[m, 1, n - 2]
                                                           * supplier[j].aM[m, 0, n2 - 1]
                                                           + supplier[j].individual_ar[m, 2, n - 2]
                                                           * supplier[j].aM[m, 1, n2 - 1]
                                                           + supplier[j].individual_ar[m, 3, n - 2]
                                                           * supplier[j].aM[m, 2, n2 - 1]
                                                           + supplier[j].individual_ar[m, 4, n - 2]
                                                           * supplier[j].aM[m, 3, n2 - 1])
                    supplier[j].forecast_income_Pete[n2] += (supplier[j].individual_ar[m, 1, n - 2]
                                                             * supplier[j].aB[m, 0, n2 - 1]
                                                             + supplier[j].individual_ar[m, 2, n - 2]
                                                             * supplier[j].aB[m, 1, n2 - 1]
                                                             + supplier[j].individual_ar[m, 3, n - 2]
                                                             * supplier[j].aB[m, 2, n2 - 1]
                                                             + supplier[j].individual_ar[m, 4, n - 2]
                                                             * supplier[j].aB[m, 3, n2 - 1])
                    supplier[j].forecast_income2[n2] += (supplier[j].individual_ar[m, 1, n - 2]
                                                         * supplier[j].aP2[m, 0, n2 - 1]
                                                         + supplier[j].individual_ar[m, 2, n - 2]
                                                         * supplier[j].aP2[m, 1, n2 - 1]
                                                         + supplier[j].individual_ar[m, 3, n - 2]
                                                         * supplier[j].aP2[m, 2, n2 - 1]
                                                         + supplier[j].individual_ar[m, 4, n - 2]
                                                         * supplier[j].aP2[m, 3, n2 - 1])
                    supplier[j].forecast_income3[n2] += (supplier[j].individual_ar[m, 1, n - 2]
                                                         * supplier[j].aP3[m, 0, n2 - 1]
                                                         + supplier[j].individual_ar[m, 2, n - 2]
                                                         * supplier[j].aP3[m, 1, n2 - 1]
                                                         + supplier[j].individual_ar[m, 3, n - 2]
                                                         * supplier[j].aP3[m, 2, n2 - 1]
                                                         + supplier[j].individual_ar[m, 4, n - 2]
                                                         * supplier[j].aP3[m, 3, n2 - 1])
                    supplier[j].forecast_income4[n2] += (supplier[j].individual_ar[m, 1, n - 2]
                                                         * supplier[j].aP4[m, 0, n2 - 1]
                                                         + supplier[j].individual_ar[m, 2, n - 2]
                                                         * supplier[j].aP4[m, 1, n2 - 1]
                                                         + supplier[j].individual_ar[m, 3, n - 2]
                                                         * supplier[j].aP4[m, 2, n2 - 1]
                                                         + supplier[j].individual_ar[m, 4, n - 2]
                                                         * supplier[j].aP4[m, 3, n2 - 1])
                    supplier[j].forecast_income5[n2] += (supplier[j].individual_ar[m, 1, n - 2]
                                                         * supplier[j].aP5[m, 0, n2 - 1]
                                                         + supplier[j].individual_ar[m, 2, n - 2]
                                                         * supplier[j].aP5[m, 1, n2 - 1]
                                                         + supplier[j].individual_ar[m, 3, n - 2]
                                                         * supplier[j].aP5[m, 2, n2 - 1]
                                                         + supplier[j].individual_ar[m, 4, n - 2]
                                                         * supplier[j].aP5[m, 3, n2 - 1])

                supplier[j].difference[n2] = abs(supplier[j].ar[0, n - 1] + supplier[j].ar[0, n]
                                                 - supplier[j].forecast_income[n2])
                supplier[j].difference_mc[n2] = abs(supplier[j].ar[0, n - 1] + supplier[j].ar[0, n]
                                                    - supplier[j].forecast_income_mc[n2])
                supplier[j].difference_Pete[n2] = abs(supplier[j].ar[0, n - 1] + supplier[j].ar[0, n]
                                                      - supplier[j].forecast_income_Pete[n2])
                supplier[j].difference2[n2] = abs(supplier[j].ar[0, n - 1] + supplier[j].ar[0, n]
                                                  - supplier[j].forecast_income2[n2])
                supplier[j].difference3[n2] = abs(supplier[j].ar[0, n - 1] + supplier[j].ar[0, n]
                                                  - supplier[j].forecast_income3[n2])
                supplier[j].difference4[n2] = abs(supplier[j].ar[0, n - 1] + supplier[j].ar[0, n]
                                                  - supplier[j].forecast_income4[n2])
                supplier[j].difference5[n2] = abs(supplier[j].ar[0, n - 1] + supplier[j].ar[0, n]
                                                  - supplier[j].forecast_income5[n2])
           
                # use moving average as comparison
                if n2 > forecast_period:
                    retailer[j].forecast_moving[n2] = numpy.mean([retailer[j].ar[0, p - 1] + retailer[j].ar[0, p]
                                                                  for p in range(n2 - forecast_period, n2)])
                    retailer[j].difference_moving[n2] = abs(retailer[j].ar[0, n - 1] + retailer[j].ar[0, n]
                                                            - retailer[j].forecast_moving[n2])
                                                           
                    distributor[j].forecast_moving[n2] = numpy.mean(
                        [distributor[j].ar[0, p - 1] + distributor[j].ar[0, p]
                         for p in range(n2 - forecast_period, n2)])
                    distributor[j].difference_moving[n2] = abs(distributor[j].ar[0, n - 1] + distributor[j].ar[0, n]
                                                            - distributor[j].forecast_moving[n2])
                    
                    manufacturer[j].forecast_moving[n2] = numpy.mean(
                        [manufacturer[j].ar[0, p - 1] + manufacturer[j].ar[0, p]
                         for p in range(n2 - forecast_period, n2)])
                    manufacturer[j].difference_moving[n2] = abs(manufacturer[j].ar[0, n - 1] + manufacturer[j].ar[0, n]
                                                            - manufacturer[j].forecast_moving[n2])
                    supplier[j].forecast_moving[n2] = numpy.mean(
                        [supplier[j].ar[0, p - 1] + supplier[j].ar[0, p]
                         for p in range(n2 - forecast_period, n2)])
                    supplier[j].difference_moving[n2] = abs(supplier[j].ar[0, n - 1] + supplier[j].ar[0, n]
                                                            - supplier[j].forecast_moving[n2])

    echelons_simu = retailer, distributor, manufacturer, supplier
    return echelons_simu


def beergame_plot(echelons):

    retailer, distributor, manufacturer, supplier = echelons
    pl.figure()
    pl.subplot(221)
    pl.plot(retailer[0].inventory, 'r-', label='retailer')
    pl.plot(distributor[0].inventory, 'b-', label='distributor')
    pl.plot(manufacturer[0].inventory, 'g-', label='manufacturer')
    pl.plot(supplier[0].inventory, 'y-', label='supplier')
    pl.title('inventory')
    pl.subplot(222)
    pl.plot(retailer[0].ar[0], 'r-', label='retailer')
    pl.plot(distributor[0].ar[0], 'b-', label='distributor')
    pl.plot(manufacturer[0].ar[0], 'g-', label='manufacturer')
    pl.plot(supplier[0].ar[0], 'y-', label='supplier')
    pl.title('ar[0]')
    pl.subplot(223)
    pl.plot(retailer[0].difference, 'r-', label='retailer')
    pl.plot(distributor[0].difference, 'b-', label='distributor')
    pl.plot(manufacturer[0].difference, 'g-', label='manufacturer')
    pl.plot(supplier[0].difference, 'y-', label='supplier')
    pl.title("Jeep's method -- difference")
    pl.subplot(224)
    pl.plot(retailer[0].difference_moving, 'r-', label='retailer')
    pl.plot(distributor[0].difference_moving, 'b-', label='distributor')
    pl.plot(manufacturer[0].difference_moving, 'g-', label='manufacturer')
    pl.plot(supplier[0].difference_moving, 'y-', label='supplier')
    pl.legend(bbox_to_anchor=(0., -0.3, 1., 0.102), loc=3,
              ncol=2, mode="expand", borderaxespad=0.)
    pl.title("moving average method -- difference")
    pl.show()


def beergame_result(echelons):

    retailer, distributor, manufacturer, supplier = echelons
    # calculate the average error
    print("Jeep1")
    madp_jeep = sum(retailer[0].difference[10:])/sum(retailer[0].ar[0, 20:])
    print(madp_jeep)
    print("Jeep2")
    madp_jeep2 = sum(retailer[0].difference2[10:])/sum(retailer[0].ar[0, 20:])
    print(madp_jeep2)
    print("Jeep3")
    madp_jeep3 = sum(retailer[0].difference3[10:])/sum(retailer[0].ar[0, 20:])
    print(madp_jeep3)
    print("Jeep4")
    madp_jeep4 = sum(retailer[0].difference4[10:])/sum(retailer[0].ar[0, 20:])
    print(madp_jeep4)
    print("Jeep5")
    madp_jeep5 = sum(retailer[0].difference5[10:])/sum(retailer[0].ar[0, 20:])
    print(madp_jeep5)
    print("mc")
    madp_mc = sum(retailer[0].difference_mc[10:]) / sum(retailer[0].ar[0, 20:])
    print(madp_mc)
    print("Pete")
    madp_Pete = sum(retailer[0].difference_Pete[10:]) / sum(retailer[0].ar[0, 20:])
    print(madp_Pete)
    print("Moving average")
    madp_moving = sum(retailer[0].difference_moving[10:]) / sum(retailer[0].ar[0, 20:])
    print(madp_moving)
    madps = madp_jeep, madp_jeep2, madp_jeep3, madp_jeep4, madp_jeep5, madp_mc, madp_Pete, madp_moving
    return madps


def beergame_write(paras, madps):
    # scale, customer_var, customer_cor, min_payment, mean_payment = paras
    # madp_jeep, madp_jeep2, madp_jeep3, madp_jeep4, madp_jeep5, madp_mc, madp_Pete, madp_moving = madps
    myFile = open('machineLearningData.csv', 'a', newline='\n')
    wr = csv.writer(myFile, quoting=csv.QUOTE_ALL)
    wr.writerow([*paras, *madps])
    myFile.close()

if __name__ is "__main__":

    for i in range(250):
        t_customer_cor, t_min_payment, t_mean_payment, t_scale, t_customer_var = setup_paras()
        t_retailer, t_distributor, t_manufacturer, t_supplier = create_chains()
        t_paras = t_customer_cor, t_min_payment, t_mean_payment, t_scale, t_customer_var
        t_echelons = t_retailer, t_distributor, t_manufacturer, t_supplier
        t_echelons = beergame_simulation(t_paras, t_echelons)
        # beergame_plot()
        t_madps = beergame_result(t_echelons)
        beergame_write(t_paras, t_madps)