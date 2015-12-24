from asciimatics.widgets import Frame, ListBox, Layout, Label, Divider, Text, \
    Button, TextBox
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
import sys
import sqlite3


class ContactModel(object):
    def __init__(self):
        # Create a database in RAM
        self._db = sqlite3.connect(':memory:')
        self._db.row_factory = sqlite3.Row

        # Create the basic contact table.
        self._db.cursor().execute('''
            CREATE TABLE contacts(
                id INTEGER PRIMARY KEY,
                name TEXT,
                phone TEXT,
                address TEXT,
                email TEXT,
                notes TEXT)
        ''')
        self._db.commit()

        # Current contact when editing.
        self.current_id = None

    def add(self, contact):
        self._db.cursor().execute('''
            INSERT INTO contacts(name, phone, address, email, notes)
            VALUES(:name, :phone, :address, :email, :notes)''',
                                  contact)
        self._db.commit()

    def get_summary(self):
        return self._db.cursor().execute(
            "SELECT name, id from contacts").fetchall()

    def get_contact(self, contact_id):
        return self._db.cursor().execute(
            "SELECT * from contacts where id=?", str(contact_id)).fetchone()

    def get_current_contact(self):
        if self.current_id is None:
            return {}
        else:
            return self.get_contact(self.current_id)

    def update_current_contact(self, details):
        if self.current_id is None:
            self.add(details)
        else:
            self._db.cursor().execute('''
                UPDATE contacts SET name=:name, phone=:phone, address=:address,
                email=:email, notes=:notes WHERE id=:id''',
                                      details)
            self._db.commit()

    def delete_contact(self, contact_id):
        self._db.cursor().execute('''
            DELETE FROM contacts WHERE id=:id''', {"id": contact_id})
        self._db.commit()


class ListView(Frame):
    def __init__(self, screen, model):
        super(ListView, self).__init__(screen,
                                       screen.height * 2 // 3,
                                       screen.width * 2 // 3,
                                       on_load=self._reload_list)
        # Save off the model that accesses the contacts database.
        self._model = model

        # Create the form for displaying the list of contacts.
        self._list_view = ListBox(
            10, model.get_summary(), name="contacts", on_select=self._on_pick)
        self._edit_button = Button("Edit", self._edit)
        self._delete_button = Button("Delete", self._delete)
        layout = Layout([100])
        self.add_layout(layout)
        layout.add_widget(Label("Contact list:"))
        layout.add_widget(Divider())
        layout.add_widget(self._list_view)
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Add", self._add), 0)
        layout2.add_widget(self._edit_button, 1)
        layout2.add_widget(self._delete_button, 2)
        layout2.add_widget(Button("Quit", self._quit), 3)
        self.fix()

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None
        self._delete_button.disabled = self._list_view.value is None

    def _reload_list(self):
        self._list_view.options = self._model.get_summary()
        self._model.current_id = None

    def _add(self):
        self._model.current_id = None
        raise NextScene()

    def _edit(self):
        self.save()
        self._model.current_id = self.data["contacts"]
        raise NextScene()

    def _delete(self):
        self.save()
        self._model.delete_contact(self.data["contacts"])
        self._reload_list()

    def _quit(self):
        raise StopApplication("User pressed quit")


class ContactView(Frame):
    def __init__(self, screen, model):
        super(ContactView, self).__init__(screen,
                                          screen.height * 2 // 3,
                                          screen.width * 2 // 3)
        # Save off the model that accesses the contacts database.
        self._model = model

        # Create the form for displaying the list of contacts.
        layout = Layout([100])
        self.add_layout(layout)
        layout.add_widget(Text("Name:", "name"))
        layout.add_widget(Text("Address:", "address"))
        layout.add_widget(Text("Phone number:", "phone"))
        layout.add_widget(Text("Email address:", "email"))
        layout.add_widget(TextBox(5, "Notes:", "notes", as_string=True))
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        self.fix()

    def reset(self):
        self.data = self._model.get_current_contact()
        super(ContactView, self).reset()

    def _ok(self):
        self.save()
        self._model.update_current_contact(self.data)
        raise NextScene()

    def _cancel(self):
        raise NextScene()


def demo(screen):

    scenes = [
        Scene([ListView(screen, contacts)], -1),
        Scene([ContactView(screen, contacts)], -1)
    ]

    screen.play(scenes, stop_on_resize=True)

contacts = ContactModel()
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True)
        sys.exit(0)
    except ResizeScreenError:
        pass