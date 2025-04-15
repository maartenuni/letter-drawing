#!/usr/bin/env python3

from __future__ import annotations

import gi
import sys
import cairo
import json
import logging
import math
import os.path as p
from image import RecImage
import image
from model import Model


gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Pango", "1.0")
gi.require_version("GObject", "2.0")

from gi.repository import Gtk, Gdk, Pango


class AppWindowMixin:
    """Classes that inherit from Gtk.Widget have a parent,
    some the topmost parent should be an application window.

    in drawimage we would like to update the state of the gui
    when we have changed some parameter. The image might change
    due to this settings and the gui should reflect that.
    """

    def update_app_window(self: Gtk.Widget) -> None:
        """Look in the tree of widgets the top most window and call te
        update() function of that window. All child widgets will be requested
        to update too, and after this the gui should be fresh.
        It is invalid to call this on a widget that hasn't got MyWin as parent (yet).
        """
        appwindow = self.get_app_window()
        if appwindow:
            appwindow.update()
        else:
            logging.warning(
                f"Unable to update appwindow value={appwindow}, does is the parent "
                + "contained in the appwindow?"
            )

    def get_app_window(self: Gtk.Widget()) -> MyWin:
        """Get the toplevel window"""
        parent = self
        while parent and not isinstance(parent, MyWin):
            parent = parent.get_parent()
        return parent


class DrawingWidget(Gtk.DrawingArea):
    """Gives a preview of the rendered drawing"""

    model: Model

    def __init__(self, model: Model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model

        self.set_draw_func(self.draw)

    def draw(self, darea, cr: cairo.Context, width, height):
        surf = self.model.rec_surf.surf

        # set the surface to gray
        cr.set_source_rgb(0.5, 0.5, 0.5)
        cr.paint()

        if surf:
            scale = self.get_width() / self.model.rec_surf.width
            pattern = cairo.SurfacePattern(surf)
            mat = cairo.Matrix()
            mat.scale(1 / scale, 1 / scale)
            pattern.set_matrix(mat)
            cr.set_source(pattern)
            cr.rectangle(0.0, 0.0, width, height)
        else:
            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.rectangle(0.0, 0.0, width, height)
        cr.fill()


class WordGrid(Gtk.Grid):
    """A grid with a number of widgets that controls the
    appearance of the word.
    """

    model: Model
    parent: MyWin

    word_entry: Gtk.Entry  # entry to fill out the word
    font_button: Gtk.FontButton  # to choose the desired font

    def __init__(self, model: Model, parent: MyWin, row_spacing=5, column_spacing=5):
        super().__init__(row_spacing=row_spacing, column_spacing=column_spacing)
        self.model = model
        self.parent = parent

        self.attach(Gtk.Label(label="Word: "), 0, 0, 1, 1)
        self.word_entry = Gtk.Entry()
        buffer = self.word_entry.props.buffer
        if self.model.word:
            buffer.props.text = self.model.word
        buffer.connect("notify::text", self._on_text_changed)
        self.attach(self.word_entry, 1, 0, 1, 1)

        self.font_button = Gtk.FontButton()
        self.font_button.connect("notify::font-desc", self._on_font_set)
        if self.model.font:
            self.font_button.set_font(self.model.font)
        self.attach(self.font_button, 0, 1, 2, 1)

        x_range = image.image_ppi(image.A4_WIDTH, image.DPI)
        y_range = image.image_ppi(image.A4_HEIGHT, image.DPI)

        self.word_x = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            math.floor(-x_range / 2),
            math.floor(x_range / 2),
            1,
        )
        self.word_x.set_draw_value(True)
        self.word_x.set_size_request(150, 150)
        self.word_x.connect("value-changed", self._on_x_scale_changed)
        self.word_x.set_value(self.model.word_x)
        self.word_y = Gtk.Scale.new_with_range(
            Gtk.Orientation.VERTICAL,
            math.floor(-y_range / 2),
            math.floor(y_range / 2),
            1,
        )
        self.word_y.set_size_request(150, 150)
        self.word_y.connect("value-changed", self._on_y_scale_changed)
        self.word_y.set_value(self.model.word_y)
        self.word_y.set_draw_value(True)
        self.attach(Gtk.Label(label="x"), 0, 2, 1, 1)
        self.attach(Gtk.Label(label="y"), 1, 2, 1, 1)
        self.attach(self.word_x, 0, 3, 1, 1)
        self.attach(self.word_y, 1, 3, 1, 1)

    def _on_text_changed(self, entry_buffer: Gtk.EntryBuffer, value):
        """Select a new word to draw along with the drawing"""
        self.model.word = entry_buffer.get_text()
        self.parent.update()

    def _on_font_set(self, button: Gtk.FontButton, value: gobject.GParamSpec):
        """Select a new font"""
        fontdesc = self.model.get_font_desc()
        self.model.font = button.get_font_desc().to_string()
        if not fontdesc or not fontdesc.equal(button.get_font_desc()):
            self.model.set_font_desc(button.get_font_desc())
            self.parent.update()

    def _on_x_scale_changed(self, scale):
        if scale.get_value() != self.model.word_x:
            self.model.word_x = scale.get_value()
            self.parent.update()

    def _on_y_scale_changed(self, scale):
        if scale.get_value() != self.model.word_x:
            self.model.word_y = scale.get_value()
            self.parent.update()


class LetterBox(Gtk.Box, AppWindowMixin):
    """This is the box in the second tab to edit the target letters to present"""

    model: model.Model
    letter_entry: Gtk.Entry
    letter_view: Gtk.ListView

    def __init__(self, model: model.Model):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5.0)
        self.model = model
        self.append(Gtk.Label(label="Words and Letter info"))

        self._setup_font_button()

        self._setup_entry()

        scrolled_window = Gtk.ScrolledWindow()
        self._setup_letter_list()

        scrolled_window.set_child(self.letter_view)
        scrolled_window.set_size_request(200, 400)
        self.append(scrolled_window)

    def _setup_font_button(self):
        """Sets up the font button"""

        def font_set(button: Pango.FontButton, _, self: LetterBox):
            """Called when setting distractor font"""
            font_desc = self.model.get_distractor_font_desc()
            self.model.distractor_font = button.get_font_desc().to_string()
            if not font_desc or not font_desc.equal(button.get_font_desc()):
                self.model.set_distractor_font_desc(button.get_font_desc())
                if self.get_parent() is not None:
                    self.update_app_window()

        font_button = Gtk.FontButton()
        font_button.connect("notify::font-desc", font_set, self)
        if self.model.distractor_font:
            font_button.set_font(self.model.distractor_font)
        self.append(font_button)

    def _setup_entry(self):
        """Setup the entry to fill the content of the letter list"""
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.append(hbox)
        hbox.append(Gtk.Label(label="Enter letters:"))
        self.letter_entry = Gtk.Entry()
        hbox.append(self.letter_entry)
        self.letter_entry.connect("activate", self._letter_entry_activated)

    def _setup_letter_list(self):
        """Sets up the list with distractors"""

        def setup_list_item(factory: Gtk.ListItemFactory, list_item: Gtk.ListItem):
            """Creates a label to display"""
            label = Gtk.Label()
            list_item.set_child(label)

        def bind_list_item(factory: Gtk.ListItemFactory, list_item: Gtk.ListItem):
            """Bind the label to a string from the model"""
            label: Gtk.Label
            label = list_item.get_child()
            model_entry = list_item.get_item()
            label.props.label = model_entry.get_string()

        def handle_key_press(
            controller: Gtk.EventControllerKey,
            keyval: int,
            keycode: int,
            state: Gdk.ModifierType,
            self: LetterBox,
        ):
            """Deletes keys from the distractor list"""
            if keyval == Gdk.KEY_Delete:
                list_model = self.letter_view.get_model()
                selected = list_model.get_selected_item()
                if selected:
                    string = selected.get_string()
                    del self.model.distractors[list_model.get_selected()]
                    list_model.get_model().remove(list_model.get_selected())

        letter_model = Gtk.StringList.new([d.string for d in self.model.distractors])
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", setup_list_item)
        factory.connect("bind", bind_list_item)
        self.letter_view = Gtk.ListView.new(
            Gtk.SingleSelection.new(letter_model), factory
        )
        event_controller = Gtk.EventControllerKey()
        self.letter_view.add_controller(event_controller)
        event_controller.connect("key-pressed", handle_key_press, self)

    def _letter_entry_activated(self, entry: Gtk.Entry):
        """Called on activation of the entry, to add letters to the list of
        distractors"""
        text = entry.get_text()
        entry.set_text("")  # clear it
        if text:
            self.model.add_distractor(text)
            self.letter_view.get_model().get_model().append(text)
            self.update_app_window()


class MyWin(Gtk.ApplicationWindow):
    hbox: Gtk.Box  # horizontally oriented box
    vbox: Gtk.Box  # vertically oriented box
    tab_save_box: Gtk.Box  # the vertically oriented box that contains the tabview and
    # save buttons.
    dwidget: DrawingWidget
    model: Model
    img_label: Gtk.Label
    word_box: Gtk.Box  # box with word parameters
    letter_box: LetterBox  # box that fills the tab with letter info

    image_label_start: str = "Image: "

    def __init__(self, model: Model, *args, **kwargs):
        logging.info("Init window")
        super().__init__(*args, **kwargs)
        self.model = model

        margin = 5

        self.hbox = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            margin_top=margin,
            margin_bottom=margin,
            margin_start=5,
            margin_end=5,
        )
        self.set_child(self.hbox)
        self.hbox.set_spacing(5)

        self.tab_save_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)

        self.hbox.append(self.tab_save_box)

        tabview = Gtk.Notebook()
        self.letter_box = LetterBox(self.model)

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.vbox.set_spacing(5)
        tabview.append_page(self.vbox, Gtk.Label(label="Image"))
        tabview.append_page(self.letter_box, Gtk.Label(label="Letters"))
        self.tab_save_box.append(tabview)

        frame = Gtk.Frame(label="drawing")

        self.dwidget = DrawingWidget(self.model)
        self.dwidget.set_size_request(594, 841)

        frame.set_child(self.dwidget)
        self.hbox.append(frame)

        self.img_label = Gtk.Label(label="", xalign=0.0)
        self.vbox.append(self.img_label)
        self.choose_img_button = Gtk.Button(label="Choose image")
        self.choose_img_button.connect("clicked", self._choose_image)

        self.vbox.append(self.choose_img_button)

        self.vbox.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # image scaling and translation controls
        img_grid = Gtk.Grid()
        self.vbox.append(img_grid)

        self.img_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0.5, 5, 0.1
        )
        self.img_scale.connect("value-changed", self.on_img_scale_changed)
        self.img_tr_x = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, self.model.rec_surf.width, 1
        )
        self.img_tr_x.set_size_request(150, 150)
        self.img_tr_x.set_value(self.model.rec_surf.pars.surf_tr_x)
        self.img_tr_x.connect("value-changed", self.on_tr_x_changed)

        self.img_tr_y = Gtk.Scale.new_with_range(
            Gtk.Orientation.VERTICAL, 0, self.model.rec_surf.height, 1
        )
        self.img_tr_y.set_size_request(150, 150)
        self.img_tr_y.set_value(self.model.rec_surf.pars.surf_tr_y)
        self.img_tr_y.connect("value-changed", self.on_tr_y_changed)

        self.img_scale.props.draw_value = True
        self.img_tr_x.props.draw_value = True
        self.img_tr_y.props.draw_value = True

        # Adding the image controls to a grid
        #                               c, r, w, h
        img_grid.attach(self.img_scale, 0, 1, 2, 1)
        img_grid.attach(Gtk.Label(label="Image scale:"), 0, 0, 2, 1)
        img_grid.attach(Gtk.Label(label="x"), 0, 2, 1, 1)
        img_grid.attach(Gtk.Label(label="y"), 1, 2, 1, 1)
        img_grid.attach(self.img_tr_x, 0, 3, 1, 1)
        img_grid.attach(self.img_tr_y, 1, 3, 1, 1)

        self.vbox.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        self.word_grid = WordGrid(self.model, self)
        self.vbox.append(self.word_grid)

        self.tab_save_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        button = Gtk.Button(label="save")
        button.connect("clicked", self.on_save_clicked)
        self.tab_save_box.append(button)

        # connect the unrealize signal, to save the config
        self.connect("unrealize", self.unrealize)

        self.update()  # the GUI

    def on_img_scale_changed(self, scale):
        img_pars = self.model.rec_surf.pars
        if 1 / scale.get_value() != img_pars.surf_scale_factor:
            img_pars.surf_scale_factor = 1 / scale.get_value()
            # img_pars.estimate_image_pars()
            self.update()

    def on_tr_x_changed(self, scale):
        img_pars = self.model.rec_surf.pars
        if scale.get_value() != img_pars.surf_tr_x:
            img_pars.surf_tr_x = scale.get_value()
            self.update()

    def on_tr_y_changed(self, scale):
        img_pars = self.model.rec_surf.pars
        if scale.get_value() != img_pars.surf_tr_y:
            img_pars.surf_tr_y = scale.get_value()
            self.update()

    def update(self):
        self.model.rec_surf.draw()  # update the drawing
        self.img_label.props.label = self.image_label_start + p.basename(
            self.model.rec_surf.fn
        )

        # get reference to image parameters
        img_pars = self.model.rec_surf.pars

        if 1 / self.img_scale.get_value() != img_pars.surf_scale_factor:
            self.img_scale.set_value(1 / img_pars.surf_scale_factor)

        self.dwidget.queue_draw()

    def _on_open_img(self, dialog: Gtk.Dialog, response: int):
        """Sets the name of the image"""
        if response == Gtk.ResponseType.ACCEPT:
            self.model.path = str(dialog.get_file().get_path())
        dialog.destroy()
        self.update()

    def _choose_image(self, button):
        chooser = Gtk.FileChooserDialog(
            title="Open file", transient_for=self, action=Gtk.FileChooserAction.OPEN
        )
        chooser.add_button("open", Gtk.ResponseType.ACCEPT)
        chooser.add_button("cancel", Gtk.ResponseType.CANCEL)
        chooser.connect("response", self._on_open_img)
        chooser.present()

    def unrealize(self, _):
        self.model.save()

    def on_save_image(self, dialog: Gtk.FileChooserDialog, response: int):
        if response == Gtk.ResponseType.ACCEPT:
            self.update()
            save_path = dialog.get_file().get_path()
            self.model.rec_surf.surf.write_to_png(save_path)
        dialog.destroy()

    def on_save_clicked(self, button: Gtk.Button):
        print(self.on_save_clicked)
        dialog = Gtk.FileChooserDialog(
            title="save-file", transient_for=self, action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_button("save", Gtk.ResponseType.ACCEPT)
        dialog.add_button("cancel", Gtk.ResponseType.CANCEL)
        dialog.connect("response", self.on_save_image)
        dialog.present()


class MyApp(Gtk.Application):
    window: MyWin

    def __init__(self, *args, **kwargs):
        # optionally init Default parameters
        super().__init__(*args, application_id="org.example.letter-drawing", **kwargs)
        self.window = None

    def do_activate(self):
        if not self.window:
            model = Model.from_file() if p.exists(Model.config_name) else Model()
            self.window = MyWin(model, application=self, title="Letter Drawing")

        self.window.present()


def main():
    app = MyApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        recimg = RecImage(sys.argv[1])
        recimg.save()
    else:
        main()
