import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def area_chart(data):
    data = data.pivot(index='ts', columns='s_state', values='power_kW')
    data = data.reset_index()
    plt.plot(data['ts'], data['NSW'])
    plt.gcf().autofmt_xdate()
    return plt