import sys
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from tkinter import IntVar, LEFT, StringVar, messagebox, BooleanVar
from tkinter.ttk import *

import oead
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


def build_gfx(obj: oead.byml.Hash):
    pass

def build_bnp(obj: oead.byml.Hash):
    tmp_dir = Path(TemporaryDirectory().name)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    (tmp_dir / "logs").mkdir()
    (tmp_dir / "logs" / "map.yml").write_text(
        oead.byml.to_text(
            oead.byml.Hash({
                obj["unit"]: oead.byml.Hash({
                    "Objs": oead.byml.Hash({
                        "mod": oead.byml.Hash({
                            str(obj["obj"]["HashId"].v): obj["obj"]
                        }),
                        "add": oead.byml.Hash(),
                        "del": oead.byml.Array()
                    })
                })
            })
        )
    )
    print(tmp_dir)


def main():
    window = ThemedTk(theme="yaru")
    frame = Frame(window)
    frame.pack(padx=12, pady=8, anchor="w")
    Label(
        frame,
        text="Enter the hash ID of the treasure chest you want to edit,"
        " and the name of the actor you want to place in the chest.",
        justify=LEFT,
        wraplength=260 - 24,
    ).pack(anchor="w")

    Label(frame, text="Treasure Box Hash ID").pack(anchor="w")
    hash_id = StringVar()
    Entry(frame, textvariable=hash_id).pack(anchor="w")
    actor_name = StringVar()
    Label(frame, text="New Actor Name").pack(anchor="w")
    Entry(frame, textvariable=actor_name).pack(anchor="w")

    bnp_mod = BooleanVar()
    Label(frame, text="Mod Type").pack(anchor="w")
    Radiobutton(frame, text="Standalone", variable=bnp_mod, value=False).pack(anchor="w")
    Radiobutton(frame, text="BNP", variable=bnp_mod, value=True).pack(anchor="w")

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
            build_bnp(obj)
        else:
            build_gfx(obj)

    Button(frame, text="Create", command=create).pack(anchor="e")

    window.title("Treasure Swap for BOTW")
    window.configure(bg="white")
    window.mainloop()


if __name__ == "__main__":
    main()