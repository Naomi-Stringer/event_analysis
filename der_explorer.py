from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import BooleanProperty, ListProperty, StringProperty, ObjectProperty, NumericProperty
from kivy.uix.popup import Popup
import os


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

    def set_write_id(self, write_2_id):
        self.write_2_id = write_2_id



class Row(BoxLayout):
    button_text = StringProperty("")
    id = ObjectProperty(None)


class SubSetLoader(GridLayout):
    row_count = 0

    def add_data_source(self):
        self.row_count += 1
        self.add_widget(Row(id=str(self.row_count)), index=1)

    def remove_data_source(self, id_2_remove):
        for child in self.children:
            if child.id == id_2_remove:
                self.remove_widget(child)

    def dismiss_popup(self):
        self._popup.dismiss()

    def choose_file(self, write_2_id):
        content = LoadDialog(load=self.write_file_name, cancel=self.dismiss_popup)
        content.set_write_id(write_2_id)
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def write_file_name(self, file, write_2_id):
        for child in self.children:
            if child.id == write_2_id:
                child.ids['text_box'].text = os.path.join(file[0])
        self._popup.dismiss()

class DataLoader(ScrollView):
    pass


class DerExplorerApp(App):
    def build(self):
        return DataLoader()


if __name__ == "__main__":
    DerExplorerApp().run()
