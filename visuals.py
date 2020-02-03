import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def area_chart(data):
    data = data.pivot(index='ts', columns='s_state', values='power_kW')
    data = data.reset_index()
    fig, ax = plt.subplots()
    for state in [col for col in data.columns if col != 'ts']:
        plt.plot(data['ts'], data[state], label=state)
    plt.legend()
    plt.gcf().autofmt_xdate()
    return fig.canvas


def update_limits(data, lower_limit, upper_limit):
    plt.clf()
    data = data.pivot(index='ts', columns='s_state', values='power_kW')
    data = data.reset_index()
    data = data[data['ts'] > lower_limit]
    data = data[data['ts'] < upper_limit]
    fig, ax = plt.subplots()
    for state in [col for col in data.columns if col != 'ts']:
        plt.plot(data['ts'], data[state], label=state)
        plt.legend()
        plt.gcf().autofmt_xdate()
    return fig.canvas


def empty_fig():
    fig, ax = plt.subplots()
    return fig.canvas