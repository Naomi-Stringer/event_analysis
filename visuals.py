import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def area_chart(data):
    data = data.pivot(index='ts', columns='s_state', values='power_kW')
    chart = data.plot.area()
    return chart