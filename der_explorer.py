from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import BooleanProperty, ListProperty, StringProperty, ObjectProperty, NumericProperty
from kivy.uix.popup import Popup
import os
import solar_analytics
from time import time
import pickle


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    start_path = ObjectProperty(None)

    def set_write_id(self, write_2_id):
        self.write_2_id = write_2_id


class SaveDialog(FloatLayout):
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
        content.set_write_id(write_2_id)
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def write_file_name(self, file, write_2_id):
        for child in self.children:
            if child.id == write_2_id:
                child.ids['text_box'].text = os.path.join(file[0])
        self._popup.dismiss()


class ExplorerPanel(TabbedPanel):
    def __init__(self):
        super(ExplorerPanel, self).__init__()
        self.ids['time_series'].add_data_source()
        self.ids['meta_data'].add_data_source()
        self.ids['inverter_data'].add_data_source()

    def load_data(self):
        t0 = time()
        time_interval, time_series, meta_data, inverter_data = self.get_state()
        data = solar_analytics.get_data_using_file_path_der_explorer(time_interval=time_interval,
                                                                     data_file_path=time_series,
                                                                     meta_data_file_path=meta_data,
                                                                     inverter_data_path=inverter_data)
        print(data)
        print('time to load {}'.format(time() - t0))

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

    def open_save_dialog(self):
        start_path = os.getcwd()
        content = SaveDialog(save=self.save_state, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save data settings", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def save_state(self, path, name):
        path_name = path + '\\' + name
        state = {}
        state['time interval'], state['time series'], state['meta data'], state['inverter data']\
            = self.get_state()
        if path_name[-2:] != ".p":
            pickle.dump(state, open(path_name + ".p", "wb"))
        else:
            pickle.dump(state, open(path_name, "wb"))


class DerExplorerApp(App):
    def build(self):
        return ExplorerPanel()


if __name__ == "__main__":
    DerExplorerApp().run()
