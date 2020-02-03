from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.tabbedpanel import TabbedPanel
import matplotlib
matplotlib.use('module://kivy.garden.matplotlib.backend_kivy')
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.popup import Popup
import os
import solar_analytics
from time import time
import pickle
import visuals
import sys
import kivy
from datetime import datetime


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    start_path = ObjectProperty(None)

    def set_write_id(self, write_2_id):
        self.write_2_id = write_2_id


class SaveDialog_D(FloatLayout):
    save = ObjectProperty(None)
    cancel = ObjectProperty(None)
    text_input = ObjectProperty(None)


class Row(BoxLayout):
    button_text = StringProperty("")
    id = ObjectProperty(None)


class SubSetLoader(GridLayout):
    row_count = 0

    def add_data_source(self):
        self.row_count += 1
        self.add_widget(Row(id=str(self.row_count)), index=1)
        self.height = self.row_count * 30 + 40

    def remove_data_source(self, id_2_remove):
        for child in self.children:
            if child.id == id_2_remove:
                self.remove_widget(child)
        self.row_count -= 1
        self.height = self.row_count * 30 + 40

    def dismiss_popup(self):
        self._popup.dismiss()

    def choose_file(self, write_2_id, row):
        start_path = row.ids['text_box'].text
        if start_path == '':
            start_path = os.getcwd()
        content = LoadDialog(load=self.write_file_name, cancel=self.dismiss_popup, start_path=start_path)
        self.write_2_id = write_2_id
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def write_file_name(self, file):
        for child in self.children:
            if child.id == self.write_2_id:
                child.ids['text_box'].text = os.path.join(file)
        self._popup.dismiss()


class ExplorerPanel(TabbedPanel):
    def __init__(self):
        super(ExplorerPanel, self).__init__()

    def load_data(self):
        t0 = time()
        time_interval, time_series, meta_data, inverter_data = self.get_state()
        data = solar_analytics.get_data_using_file_path_der_explorer(time_interval=time_interval,
                                                                     data_file_path=time_series,
                                                                     meta_data_file_path=meta_data,
                                                                     inverter_data_path=inverter_data)
        data = solar_analytics.data_filter(data)
        self.data = solar_analytics.aggregate_data(data)
        self.ids['graph_grid'].remove_widget(self.ids['graph_grid'].children[1])
        canvas = visuals.area_chart(self.data)
        self.ids['graph_grid'].add_widget(canvas, index=1)
        self.switch_to(self.ids['data_viewer'])
        self.ids['lower_limit'].text = self.data['ts'].min().isoformat().replace('T', ' ')
        self.ids['upper_limit'].text = self.data['ts'].max().isoformat().replace('T', ' ')
        print(data)
        print('time to load {}'.format(time() - t0))

    def update_x_limits(self, lower_limit, upper_limit):
        print('hi')
        self.ids['graph_grid'].remove_widget(self.ids['graph_grid'].children[1])
        lower_limit = datetime.strptime(lower_limit, '%Y-%m-%d %H:%M:%S')
        upper_limit = datetime.strptime(upper_limit, '%Y-%m-%d %H:%M:%S')
        canvas = visuals.update_limits(self.data, lower_limit, upper_limit)
        self.ids['graph_grid'].add_widget(canvas, index=1)

    def get_state(self):
        time_interval = None
        for name, value in self.ids.items():
            if name in ['s5', 's30', 's60']:
                if value.active:
                    time_interval = int(name[1:])
        for child in self.ids['time_series'].children:
            if child.id == '1':
                time_series = child.ids['text_box'].text
        for child in self.ids['meta_data'].children:
            if child.id == '1':
                meta_data = child.ids['text_box'].text
        for child in self.ids['inverter_data'].children:
            if child.id == '1':
                inverter_data = child.ids['text_box'].text
        return time_interval, time_series, meta_data, inverter_data

    def dismiss_popup(self):
        self._popup.dismiss()

    def dismiss_popup_save(self):
        self._popup_save.dismiss()

    def open_save_dialog(self):
        content = SaveDialog_D(save=self.save_state, cancel=self.dismiss_popup_save)
        self._popup_save = Popup(title="Save data settings", content=content, size_hint=(0.9, 0.9))
        self._popup_save.open()

    def open_load_dialog(self):
        start_path = os.getcwd()
        content = LoadDialog(load=self.load_state, cancel=self.dismiss_popup, start_path=start_path)
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def save_state(self, path_name):
        state = {}
        state['time interval'], state['time series'], state['meta data'], state['inverter data']\
            = self.get_state()
        if path_name[-2:] != ".p":
            with open(path_name + ".p", 'wb') as handle:
                pickle.dump(state, handle, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            with open(path_name, 'wb') as handle:
                pickle.dump(state, handle, protocol=pickle.HIGHEST_PROTOCOL)
        self.dismiss_popup()

    def load_state(self, path_name):
        with open(path_name, 'rb') as handle:
            state = pickle.load(handle)
        for name, value in self.ids.items():
            if name in ['s5', 's30', 's60']:
                value.active = False
        if state['time interval'] is not None:
            self.ids['s' + str(state['time interval'])].active = True
        for child in self.ids['time_series'].children:
            if child.id == '1':
                child.ids['text_box'].text = state['time series']
        for child in self.ids['meta_data'].children:
            if child.id == '1':
                child.ids['text_box'].text = state['meta data']
        for child in self.ids['inverter_data'].children:
            if child.id == '1':
                child.ids['text_box'].text = state['inverter data']
        self.dismiss_popup()


class DerExplorerApp(App):
    def build(self):
        window = ExplorerPanel()
        window.ids['time_series'].add_data_source()
        window.ids['meta_data'].add_data_source()
        window.ids['inverter_data'].add_data_source()
        window.ids['graph_grid'].add_widget(visuals.empty_fig(), index=1)
        return window

def resourcePath():
    '''Returns path containing content - either locally or in pyinstaller tmp file'''
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS)

    return os.path.join(os.path.abspath("."))

if __name__ == "__main__":
    kivy.resources.resource_add_path(resourcePath())
    DerExplorerApp().run()
