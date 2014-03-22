#!/usr/bin/env python

"""
Save/restore widget state information.

Starting point: Thomas Hinkle's (Thomas_Hinkle@alumni.brown.edu)
posting on the pygtk mailing list.
"""

import sys
import copy
import pickle
import os.path

import gtk
import gtk.gdk
import gtk.glade
import gobject

class WidgetSaver:

    """A class to save and load widget properties to/from a
    dictionary. We leave it to whoever hands us the dictionary to save
    the dictionary. dictionary should contain a property name as a key
    and a value as a value. On __init__, we will load these properties
    into the widget and who the widget. Each signal in signals will be
    connected to save_properties"""

    def __init__(self, widget, dictionary=None, signals=None, show=True):
        """Set up a widget saver.

        widget - widget whose state we want to save/restore
        dictionary - keys are properties we want to track, values are
                     defaults (default: don't track any properties)
        signals - signals which should cause the saver to snapshot the
                  widget's state (default: only snapshot on destroy signals)
        show - whether to show the widget at startup (default: True)
        """

        self.w = widget
        if dictionary is None:
            dictionary = {}
        self.dictionary = dictionary
        self.signals = signals or ['destroy']
        self.load_properties()
        for s in self.signals:
            self.w.connect(s, self.save_properties)
        if show: self.w.show()

    def load_properties(self):
        for p,v in self.dictionary.items():
            try:
                self.w.set_property(p,v)
            except TypeError:
                print >> sys.stderr, (self.w, (p, v))
                raise

    def save_properties(self, *args):
        for p in self.dictionary.keys():
            self.dictionary[p] = self.w.get_property(p)
        return False # we don't handle any signals

class WindowSaver(WidgetSaver):
    def __init__(self, widget, dictionary=None, signals=None, show=True):
        """We save the position and state of the window
        in dictionary. The dictionary consists of
        {window_size: widget.get_size(),
         position: widget.get_position(),}"""
        widget.set_gravity(gtk.gdk.GRAVITY_STATIC)
        signals = signals or ['configure-event','delete-event']
        WidgetSaver.__init__(self, widget, dictionary, signals, show)

    def load_properties(self):
        for p,f in ['window_size', self.w.resize],['position',self.w.move]:
            if self.dictionary.has_key(p) and self.dictionary[p]:
                f(*self.dictionary[p])
        
    def save_properties(self, *args):
        self.dictionary['window_size']=self.w.get_size()
        self.dictionary['position']=self.w.get_position()
        return False

# set up a quick preference saver which will save the dictionary
# quick_prefs.config to the config file ~/.testing/positions and
# load from that file on startup
class quick_prefs:
    def __init__(self, fn=None):
        if fn is None:
            self.file = os.path.join('~', '.testing', 'positions')
            self.file = os.path.expanduser(self.file)
        else:
            self.file = fn
        self.config = {}
        self.load()

    def get(self, key, default=None):
        if key not in self.config:
            self.config[key] = default
        return self.config[key]

    def save(self):
        pickle.dump(self.config, open(self.file, 'w'))

    def load(self):
        if os.path.isfile(self.file):
            ifi = open(self.file,'r')
            self.config = pickle.load(ifi)
            return True
        else:
            return False


class GladeSaverManager:
    def __init__(self, wtree, names, prefsfile=None, prefix="", show=True):
        self.init_defaults()
        self.show = show
        self.savers = {}
        self.prefs = quick_prefs(prefsfile)
        self.add_names(wtree, names, prefix)

    def add_names(self, wtree, names, prefix="", show=None):
        if show is None:
            show = self.show
        for name in names:
            w = wtree.get_widget(name)
            self.add_widget(w, name, prefix, show)

    def add_widget(self, w, name, prefix="", show=None):
        if show is None:
            show = self.show
        dflt = self.defaults.get(type(w))
        if dflt is None:
            dflt = (WidgetSaver, {}, None)
            print >> sys.stderr, "Unknown widget type:", type(w)
        cls, props, sigs = dflt
        save_name = "%s.%s" % (prefix, name)
        d = {}
        for k in props:
            d[k] = props[k](w)
        self.savers[save_name] = cls(w, self.prefs.get(save_name, d), sigs,
                                     show)
        
    def save_properties(self):
        for k in self.savers:
            self.savers[k].save_properties()
        self.prefs.save()

    def init_defaults(self):
        self.defaults = {
            gtk.Window:
            (WindowSaver, {}, []),
            gtk.VPaned:
                (WidgetSaver, {'position': gtk.VPaned.get_position}, []),
            gtk.Calendar:
                (WidgetSaver, {'day': self._get_day,
                               'month': self._get_month,
                               'year': self._get_year},
                 ["day-selected", "month-changed", "next-month", "next-year",
                  "prev-month", "prev-year"]),
            gtk.TreeView:
                (WidgetSaver, {}, ["columns-changed"]),
            gtk.TreeViewColumn:
                (WidgetSaver, {"visible": gtk.TreeViewColumn.get_visible},
                 # alas, "width" is not a writable property...
                               #"width": gtk.TreeViewColumn.get_width},
                 None),
            gtk.HPaned:
                (WidgetSaver, {'position': gtk.HPaned.get_position}, []),
            gtk.Button:
                (WidgetSaver, {}, None),
            gtk.CheckButton:
                (WidgetSaver, {'active': gtk.CheckButton.get_active},
                 ['toggled']),
            gtk.ToggleButton:
                (WidgetSaver, {'active': gtk.ToggleButton.get_active},
                 ['toggled']),
            gtk.RadioButton:
                (WidgetSaver, {'active': gtk.RadioButton.get_active},
                 ['toggled']),
            gtk.SpinButton:
                (WidgetSaver, {'value': gtk.SpinButton.get_value},
                 ['change-value', 'value-changed']),
            }

        if gtk.gtk_version >= (2, 4):
            self.defaults[gtk.Expander] = (WidgetSaver,
                                           {'expanded': gtk.Expander.get_expanded},
                                           ['activate'])

    def _get_day(self, w):
        return gtk.Calendar.get_date(w)[2]

    def _get_month(self, w):
        return gtk.Calendar.get_date(w)[1]

    def _get_year(self, w):
        return gtk.Calendar.get_date(w)[0]

if __name__ == '__main__':
    if gtk.gtk_version < (2, 4):
        print >> sys.stderr, "Need gtk >= 2.4 for this demo (uses gtk.Expander)."
        sys.exit(1)

    import random

    def gen_year(*args):
        return random.randrange(2004, 2009)

    def gen_month(*args):
        return random.randrange(1, 13)

    def create_and_fill_model():
        store = gtk.ListStore(int, int)

        # Append some random-ish rows
        for i in range(20):
            store.append((gen_year(), gen_month()))

        return store

    def toggle_year(widget):
        year.set_visible(widget.get_active())

    def toggle_month(widget):
        month.set_visible(widget.get_active())

    def exit(w):
        saver.save_properties()
        gtk.main_quit()

    wtree = gtk.glade.XML("widgetsaver-2.4.glade", 'widgetsaver')
    saver = GladeSaverManager(wtree, [], "widgetsaver.prefs")

    saver.add_names(wtree, ["widgetsaver", "pane", "expander"], prefix="first")
    saver.add_names(wtree, ["check", "tog", "spin", "quit"], prefix="second")
    saver.add_names(wtree, ["rb1", "rb2", "cal"], prefix="third")
    saver.add_names(wtree, ["tv", "chkyr", "chkmonth"], prefix="fourth")

    # glade can't do everything :-(
    tv = wtree.get_widget("tv")
    tv.set_model(create_and_fill_model())

    ren = gtk.CellRendererText()
    year = gtk.TreeViewColumn("Year", ren)
    tv.append_column(year)
    year.add_attribute(ren, 'text', 0)
    year.set_resizable(True)
    saver.add_widget(year, "year", "fourth", False)

    ren = gtk.CellRendererText()
    month = gtk.TreeViewColumn("Month", ren)
    tv.append_column(month)
    month.add_attribute(ren, 'text', 1)
    month.set_resizable(True)
    saver.add_widget(month, "month", "fourth", False)

    cdict = {
        'on_chkyr_toggled': toggle_year,
        'on_chkmonth_toggled': toggle_month
        }
    wtree.signal_autoconnect(cdict)

    toplevel = wtree.get_widget("widgetsaver")
    toplevel.connect('delete-event', exit)
    
    quit = wtree.get_widget("quit")
    quit.connect('clicked', exit)

    gtk.main()
    sys.exit(0)
