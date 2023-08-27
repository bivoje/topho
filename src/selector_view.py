import tkinter
from tkinter import messagebox
import logging

from misc import *
from loading_queue import ImageLoadingQueue

class SelectorView:
    def __init__(self, maxw, maxh, run_player, dirnames, STATIC):
        self.maxw = maxw
        self.maxh = maxh
        self.run_player = run_player

        self.root = tkinter.Tk()
        self.root.title(f"Topho {VERSION}")

        # FIXME for some reason, can't load image from the main thread... :/
        # default_img = front_queue()[0]
        self.unrecog_img = load_tk_image(STATIC/'unrecognized.png', self.maxw, self.maxh)
        self.loading_img = load_tk_image(STATIC/'loading.png',      self.maxw, self.maxh)
        self.broken_img  = load_tk_image(STATIC/'broken.png',       self.maxw, self.maxh)
        self.video_img   = load_tk_image(STATIC/'video.png',        self.maxw, self.maxh)
        self.start_img   = load_tk_image(STATIC/'start.png',        self.maxw, self.maxh)
        self.end_img     = load_tk_image(STATIC/'end.png',          self.maxw, self.maxh)
        self.lab = tkinter.Label(image=self.start_img)
        self.lab.grid(row=0,column=1,columnspan=3)

        self.last_key = None
        self.key_released = True
        self.started = False
        self.contd = False

        self.check_dirname = self.root.register(check_dirname)
        self.dirnames = dirnames

    def load(self, source_files, qparam):
        self.fqm, self.fqM, self.bqm, self.bqM = qparam
        srcfiles = [(path, None) for path in source_files]
        # queue : [ (image, path, selection) ]; first fed with [(path,selection)]
        self.front_queue = ImageLoadingQueue(srcfiles, self.fqm, self.fqM, lambda path: load_tk_image(path, self.maxw, self.maxh))
        self.back_queue  = ImageLoadingQueue([],       self.bqm, self.bqM, lambda path: load_tk_image(path, self.maxw, self.maxh))

    def show_current(self):
        if not self.started:
            img = self.start_img
            title = f"Topho {VERSION}"
        else:
            ret = self.front_queue.get(block=False, pop=False)
            if ret is None: # no more data
                img = self.end_img
                title = "END"
            elif not ret: # loading
                img = self.loading_img
                title = "LOADING" # TODO can we do automatic refresh?
            else:
                img = ret[0]
                title = ('-' if ret[2] is None else f"{str(ret[2])} {self.dirnames[ret[2]] or ''}") + " " + ret[1].name

        if img is None: # unrecognized type
            img = self.unrecog_img
        elif not img: # image broken..
            img = self.broken_img
        elif img == 'video':
            img = self.video_img
            self.run_player(ret[1]) # type: ignore

        self.lab.config(image=img)
        self.lab.grid(row=0,column=1,columnspan=3)
        self.root.title(title)


    KEY_BINDING_HELP = """ESC,q: quit
SPACE:\tstart,skip
c:\tcontinue
r:\treload
0-9:\tselect
u:\tundo
U:\tredo
d:\ttag
?:\thelp
"""

    def key_press(self, e):
        if e.char == self.last_key and not self.key_released: return
        self.last_key, self.key_released = e.char, False

        done = True

        if self.last_key == '\x1b' or self.last_key == 'q':
            logging.debug("selector_view:" "quit")
            self.root.destroy()

        elif self.last_key == 'c':
            logging.debug("selector_view:" "continue")
            self.contd = True
            self.root.destroy()

        elif self.last_key == ' ' and not self.started:
            logging.debug("selector_view:" "start")
            self.started = True
            self.show_current()

        else:
            done = False

        if not self.started or done: return

        elif self.last_key == '?':
            logging.debug("selector_view:" "bindings")
            messagebox.showinfo("Modal", SelectorView.KEY_BINDING_HELP)

        elif self.last_key == 'r':
            logging.debug("selector_view:" "reload")
            self.show_current()

        elif '0' <= self.last_key and self.last_key <= '9':
            logging.debug("selector_view:" "do")
            ret = self.front_queue.get(block=False)
            if ret: # no more data, do nothing
                img, orig_path, _ = ret
                self.back_queue.put((img, orig_path, int(self.last_key)))
            self.show_current()

        elif self.last_key == 'u':
            logging.debug("selector_view:" "undo")
            ret = self.back_queue.get()
            if ret is None: # at the start
                self.started = False
                self.show_current()
            elif not ret: # loading
                # FIXME
                self.lab.config(image=self.loading_img)
                self.lab.grid(row=0,column=1,columnspan=3)
            else:
                self.front_queue.put(ret)
                self.show_current()

        elif self.last_key == 'U':
            logging.debug("selector_view:" "redo")
            ret = self.front_queue.get(block=False)
            if ret: # no more data, do nothing
                self.back_queue.put(ret)
            self.show_current()

        elif self.last_key == ' ':
            logging.debug("selector_view:" "skip")
            ret = self.front_queue.get(block=False)
            if ret: # no more data, do nothing
                img, orig_path, _ = ret
                self.back_queue.put((img, orig_path, None))
            self.show_current()

        # https://tkdocs.com/shipman/entry.html
        elif self.last_key == 't':
            logging.debug("selector_view:" "tag, dirname")
            win = tkinter.Toplevel(self.root)
            entries = []

            def apply(event=None):
                for i, entry in enumerate(entries):
                    self.dirnames[i] = entry.get()
                win.destroy()

            tkinter.Label(win, text="selection key").grid(row=0, column=0, padx=20, pady=15)
            tkinter.Label(win, text=f"directory name").grid(row=0, column=1, padx=20, pady=15)
            for i in range(10):
                tkinter.Label(win, text=f"{i}:").grid(row=i+1, column=0, padx=20)#, padx=20, pady=15)
                entry = tkinter.Entry(win, width=50)
                entry.grid(row=i, column=1, padx=75)
                entry.insert(0, self.dirnames[i])
                entry.bind('<Key-Return>', apply)
                entry.config(validate='all', validatecommand=(self.check_dirname, '%P'))
                entry.config(state='normal' if i > 0 else 'readonly')
                entries.append(entry)
            tkinter.Button(win, text="Apply", command=apply).grid(row=11, column=0, pady=15)
            tkinter.Button(win, text="Cancel", command=win.destroy).grid(row=11, column=1, pady=15)

            win.wait_visibility()
            win.grab_set()
            win.focus_set()


    def key_release(self, e):
        self.key_released = True


    def run(self):
        self.front_queue.run()
        self.back_queue.run()


        self.root.bind('<KeyPress>', self.key_press)
        self.root.bind('<KeyRelease>', self.key_release)

        self.root.mainloop()

        self.front_queue.quit()
        self.back_queue.quit()

        back_result = self.back_queue.drain()
        back_result.reverse()
        front_result = self.front_queue.drain()

        return back_result + front_result