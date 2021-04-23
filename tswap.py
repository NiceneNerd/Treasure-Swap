import sys
import os
from base64 import urlsafe_b64encode
from json import dumps, loads
from pathlib import Path
from platform import system
from shutil import rmtree
from tempfile import TemporaryDirectory
from tkinter import *
from tkinter import messagebox, filedialog, font
from tkinter.ttk import *
from webbrowser import open_new_tab

import oead
import py7zr
from ttkthemes import ThemedTk


def load_db():
    return oead.byml.from_binary(
        oead.yaz0.decompress(
            open(
                os.path.join(
                    getattr(
                        sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))
                    ),
                    "boxes.sbyml",
                ),
                "rb",
            ).read()
        )
    )


def build_gfx(obj: oead.byml.Hash, be: bool):
    unit = tuple(obj["unit"].split("_"))
    stock_dir: Path
    try:
        set_path = (
            Path(os.path.expandvars("%LOCALAPPDATA%")) / "bcml" / "settings.json"
            if system() == "Windows"
            else Path.home() / ".config" / "bcml"
        )
        assert set_path.exists()
        settings = loads(set_path.read_text("utf-8"))
        if be:
            assert settings["dlc_dir"]
            stock_dir = Path(settings["dlc_dir"])
        else:
            assert settings["dlc_dir_nx"]
            stock_dir = Path(settings["dlc_dir_nx"])
    except ImportError:
        messagebox.showerror(
            "Error", "BCML with DLC support is required to build a standalone mod"
        )
        return
    out_dir = Path(filedialog.askdirectory(title="Select Mod Folder")) / (
        "aoc/0010" if be else "01007EF00011F001/romfs"
    )
    map_path = Path("Map") / "MainField" / unit[0] / f"{obj['unit']}.smubin"
    out: Path = out_dir / map_path
    mu: oead.byml.Hash
    if out.exists():
        res = messagebox.askyesno(
            title=f"Map Exists",
            message=f"The map unit {obj['unit']} already exists in your mod."
            "Do you want to update it?",
        )
        if not res:
            return
        mu = oead.byml.from_binary(oead.yaz0.decompress(out.read_bytes()))
    else:
        mu = oead.byml.from_binary(
            oead.yaz0.decompress((stock_dir / map_path).read_bytes())
        )
    # Binary search
    a = 0
    b = len(mu["Objs"]) - 1
    needle_hash = obj["obj"]["HashId"].v
    while a <= b:
        m = int((a + b) / 2)
        hash_id = mu["Objs"][m]["HashId"].v
        if needle_hash < hash_id:
            b = m - 1
        elif needle_hash > hash_id:
            a = m + 1
        else:
            mu["Objs"][m] = obj["obj"]
            break
    else:
        messagebox.showerror(
            "Error", f"Treasure chest with hash ID {needle_hash} not found in {unit}."
        )
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out_pack = out_dir / "Pack" / "AocMainField.pack"
    out_pack.parent.mkdir(parents=True, exist_ok=True)
    out_pack.write_bytes(b"")
    out.write_bytes(oead.yaz0.compress(oead.byml.to_binary(mu, be)))
    messagebox.showinfo("Done", "Mod created succesfully!")


def build_bnp(parent, obj: oead.byml.Hash, be: bool):
    tmp_dir = Path(TemporaryDirectory().name)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    (tmp_dir / "logs").mkdir()
    (tmp_dir / "logs" / "map.yml").write_text(
        oead.byml.to_text(
            oead.byml.Hash(
                {
                    obj["unit"]: oead.byml.Hash(
                        {
                            "Objs": oead.byml.Hash(
                                {
                                    "mod": oead.byml.Hash(
                                        {str(obj["obj"]["HashId"].v): obj["obj"]}
                                    ),
                                    "add": oead.byml.Hash(),
                                    "del": oead.byml.Array(),
                                }
                            )
                        }
                    )
                }
            )
        )
    )
    bnp_dialog = BnpDialog(parent)
    parent.wait_window(bnp_dialog.top)
    meta = bnp_dialog.meta
    meta["platform"] = "wiiu" if be else "switch"
    (tmp_dir / "info.json").write_text(dumps(meta, indent=4))
    out = filedialog.asksaveasfilename(
        title="Save BNP", filetype=(("BNP archives", "*.bnp"), ("All files", "*.*"))
    )
    with py7zr.SevenZipFile(out, "w") as bnp:
        bnp.write(tmp_dir / "info.json", arcname="info.json")
        bnp.write(tmp_dir / "logs" / "map.yml", arcname="logs/map.yml")
    messagebox.showinfo("Done", "BNP created succesfully!")
    rmtree(tmp_dir, ignore_errors=True)


def main():
    window = ThemedTk(theme="yaru")
    frame = Frame(window)
    frame.pack(anchor="w")
    Label(
        frame,
        text="Enter the hash ID of the treasure chest you want to edit,"
        " and the name of the actor you want to place in the chest.",
        justify=LEFT,
        wraplength=260 - 24,
    ).pack(padx=12, pady=(8, 0), anchor="w")
    lnk_obj = Label(
        frame,
        text="BOTW Object Map on ZeldaMods",
        foreground="blue",
        cursor="hand2",
        font=font.Font(underline=True, size=9),
    )
    lnk_obj.pack(padx=12, pady=4, anchor="w")
    lnk_obj.bind("<Button-1>", lambda _: open_new_tab("https://objmap.zeldamods.org/"))
    Label(frame, text="Treasure Box Hash ID").pack(padx=12, pady=4, anchor="w")
    hash_id = StringVar()
    Entry(frame, textvariable=hash_id).pack(padx=12, pady=4, anchor="w", fill="x")
    actor_name = StringVar()
    Label(frame, text="New Actor Name").pack(padx=12, pady=4, anchor="w")
    Entry(frame, textvariable=actor_name).pack(padx=12, pady=4, fill="x", anchor="w")

    bnp_mod = BooleanVar()
    Label(frame, text="Mod Type").pack(padx=12, pady=4, anchor="w")
    Radiobutton(frame, text="Standalone", variable=bnp_mod, value=False).pack(
        padx=12, pady=0, anchor="w"
    )
    Radiobutton(frame, text="BNP", variable=bnp_mod, value=True).pack(
        padx=12, pady=0, anchor="w"
    )
    Label(frame, text="Platform").pack(padx=12, pady=4, anchor="w")
    wiiu_var = BooleanVar()
    Radiobutton(frame, text="Switch", variable=wiiu_var, value=False).pack(
        padx=12, pady=0, anchor="w"
    )
    Radiobutton(frame, text="Wii U", variable=wiiu_var, value=True).pack(
        padx=12, pady=0, anchor="w"
    )

    def create():
        if not hash_id.get():
            messagebox.showerror("Error", "You must provide a hash ID.")
            return
        try:
            hash_str = str(int(hash_id.get(), 16))
        except:
            messagebox.showerror(
                "Error", "Hash ID must be a valid hexademical string (e.g. 0x002bcdae)."
            )
            return
        if not actor_name.get():
            messagebox.showerror("Error", "You must provide an actor name.")
            return
        actor_str = actor_name.get()

        db = load_db()
        try:
            obj = db[hash_str]
        except KeyError:
            messagebox.showerror(
                "Error",
                "Hash ID not found. Are you sure this is a treasure chest in the base game?",
            )
            return
        obj["obj"]["!Parameters"]["DropActor"] = actor_str
        if bnp_mod.get():
            build_bnp(window, obj, be=wiiu_var.get())
        else:
            build_gfx(obj, be=wiiu_var.get())
        actor_name.set("")
        hash_id.set("")
        bnp_mod.set(False)
        wiiu_var.set(False)

    Button(frame, text="Create", command=create).pack(padx=12, pady=8, anchor="e")

    window.title("Treasure Swap")
    window.iconphoto(
        False,
        PhotoImage(
            file=os.path.join(
                getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))),
                "tswap.png",
            )
        ),
    )
    window.configure(bg="white")
    window.resizable(False, False)
    window.mainloop()


class BnpDialog:
    def __init__(self, parent) -> None:
        top = self.top = Toplevel(parent)
        top.title("Create BNP")
        Label(top, text="Mod name:").pack(anchor="w", padx=4, pady=4)
        self.name_var = StringVar()
        Entry(top, textvariable=self.name_var).pack(
            anchor="w", fill="x", padx=4, pady=4
        )
        Label(top, text="Mod description:").pack(anchor="w", padx=4, pady=4)
        self.desc_var = StringVar()
        Entry(top, textvariable=self.desc_var).pack(
            anchor="w", fill="x", padx=4, pady=4
        )
        Button(top, text="OK", command=self.submit).pack(anchor="e", padx=4, pady=4)

    def submit(self):
        self.meta = {
            "name": self.name_var.get(),
            "desc": self.desc_var.get(),
            "url": "",
            "image": "",
            "version": "1.0.0",
            "depends": [],
            "options": {},
            "id": urlsafe_b64encode(
                f"{self.name_var.get()}==1.0.0".encode("utf8")
            ).decode("utf8"),
        }
        self.top.destroy()


if __name__ == "__main__":
    main()
