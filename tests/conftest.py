import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class _StubWidget:
    def __init__(self, *a, **kw):
        pass

    def __call__(self, *a, **kw):
        return self

    def __getattr__(self, name):
        return lambda *a, **kw: None

    def grid(self, *a, **kw):
        pass

    def pack(self, *a, **kw):
        pass

    def configure(self, *a, **kw):
        pass

    def config(self, *a, **kw):
        pass

    def insert(self, *a, **kw):
        pass

    def delete(self, *a, **kw):
        pass

    def see(self, *a, **kw):
        pass

    def set(self, *a, **kw):
        pass

    def get(self, *a, **kw):
        return ""

    def yview(self, *a, **kw):
        pass

    def winfo_width(self):
        return 900

    def winfo_height(self):
        return 650

    def protocol(self, *a, **kw):
        pass

    def after(self, ms=0, func=None, *args):
        if ms == 0 and func:
            return func(*args)

    def quit(self):
        pass

    def mainloop(self):
        pass

    def columnconfigure(self, *a, **kw):
        pass

    def rowconfigure(self, *a, **kw):
        pass

    def drop_target_register(self, *a, **kw):
        pass

    def dnd_bind(self, *a, **kw):
        pass

    def tk(self):
        pass


class _Tk(_StubWidget):
    def __getattr__(self, name):
        if name == "splitlist":
            return lambda data: []
        return super().__getattr__(name)


class _StringVar(_StubWidget):
    def __init__(self, *a, **kw):
        self._val = kw.get("value", "")

    def get(self):
        return self._val

    def set(self, v):
        self._val = v


def _ensure_fake_tkinter():
    if "tkinter" in sys.modules and not isinstance(sys.modules["tkinter"], types.ModuleType):
        return

    fake = types.ModuleType("tkinter")
    fake.Tk = _Tk
    fake.Frame = _StubWidget
    fake.StringVar = _StringVar
    fake.Listbox = _StubWidget
    fake.END = "end"
    fake.NORMAL = "normal"
    fake.DISABLED = "disabled"
    fake.W = fake.E = fake.N = fake.S = "w"
    fake.LEFT = "left"
    fake.VERTICAL = "vertical"
    fake.YES = "yes"
    fake.NO = "no"
    sys.modules["tkinter"] = fake

    fake_ttk = types.ModuleType("tkinter.ttk")
    fake_ttk.Frame = _StubWidget
    fake_ttk.LabelFrame = _StubWidget
    fake_ttk.Button = _StubWidget
    fake_ttk.Entry = _StubWidget
    fake_ttk.Label = _StubWidget
    fake_ttk.Scrollbar = _StubWidget
    fake_ttk.Progressbar = _StubWidget
    fake_ttk.Radiobutton = _StubWidget
    sys.modules["tkinter.ttk"] = fake_ttk

    fake_filedialog = types.ModuleType("tkinter.filedialog")
    fake_filedialog.askopenfilenames = lambda *a, **kw: ()
    fake_filedialog.askdirectory = lambda *a, **kw: ""
    sys.modules["tkinter.filedialog"] = fake_filedialog

    fake_messagebox = types.ModuleType("tkinter.messagebox")
    fake_messagebox._last = None
    fake_messagebox._last_args = None

    def _capture(*a):
        fake_messagebox._last = a[0] if a else None
        fake_messagebox._last_args = a

    fake_messagebox.showwarning = _capture
    fake_messagebox.showerror = _capture
    fake_messagebox.showinfo = _capture
    sys.modules["tkinter.messagebox"] = fake_messagebox

    fake_scrolledtext = types.ModuleType("tkinter.scrolledtext")
    fake_scrolledtext.ScrolledText = _StubWidget
    sys.modules["tkinter.scrolledtext"] = fake_scrolledtext


def _ensure_fake_dnd():
    if "tkinterdnd2" in sys.modules and not isinstance(sys.modules["tkinterdnd2"], types.ModuleType):
        return
    fake_dnd = types.ModuleType("tkinterdnd2")
    fake_dnd.DND_FILES = "DND_FILES"
    fake_dnd.TkinterDnD = _Tk
    sys.modules["tkinterdnd2"] = fake_dnd


_ensure_fake_tkinter()
_ensure_fake_dnd()

sys.path.insert(0, str(ROOT))
