from tkinter import *

from misc import *
from loading_queue import ImageLoadingQueue

class SelectorView:
    def __init__(self, maxw, maxh, run_player, STATIC):
        self.maxw = maxw
        self.maxh = maxh
        self.run_player = run_player

        self.root = Tk()
        self.root.title(f"Topho {VERSION}")

        # FIXME for some reason, can't load image from the main thread... :/
        # default_img = front_queue()[0]
        self.unrecog_img = load_tk_image(STATIC/'unrecognized.png', self.maxw, self.maxh)
        self.loading_img = load_tk_image(STATIC/'loading.png',      self.maxw, self.maxh)
        self.broken_img  = load_tk_image(STATIC/'broken.png',       self.maxw, self.maxh)
        self.video_img   = load_tk_image(STATIC/'video.png',        self.maxw, self.maxh)
        self.start_img   = load_tk_image(STATIC/'start.png',        self.maxw, self.maxh)
        self.end_img     = load_tk_image(STATIC/'end.png',          self.maxw, self.maxh)
        self.lab = Label(image=self.start_img)
        self.lab.grid(row=0,column=1,columnspan=3)

        self.last_key = None
        self.key_released = True
        self.started = False
        self.contd = False

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
                title = "LOADING" # FIXME can we do automatic refresh?
            else:
                img = ret[0]
                title = ('-' if ret[2] is None else str(ret[2])) + " " + ret[1].name

        if img is None: # unrecognized type
            img = self.unrecog_img
        elif not img: # image broken..
            img = self.broken_img
        elif img == 'video':
            img = self.video_img
            self.run_player(ret[1])

        self.lab.config(image=img)
        self.lab.grid(row=0,column=1,columnspan=3)
        self.root.title(title)


    def key_press(self, e):
        if e.char == self.last_key and not self.key_released: return
        self.last_key, self.key_released = e.char, False

        if self.last_key == '\x1b':
            #print("quit")
            self.root.destroy()
            return

        if self.last_key == 'c':
            #print("continue")
            self.contd = True
            self.root.destroy()
            return

        if self.last_key == ' ' and not self.started:
            #print("start")
            self.started = True
            self.show_current()
            return

        if not self.started: return

        elif self.last_key == 'r':
            #print("reload")
            self.show_current()

        elif '0' <= self.last_key and self.last_key <= '9':
            #print("do")
            ret = self.front_queue.get(block=False)
            if ret: # no more data, do nothing
                img, orig_path, _ = ret
                self.back_queue.put((img, orig_path, int(self.last_key)))
            self.show_current()

        elif self.last_key == 'u':
            #print("undo")
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
            #print("redo")
            ret = self.front_queue.get(block=False)
            if ret: # no more data, do nothing
                self.back_queue.put(ret)
            self.show_current()

        elif self.last_key == ' ':
            #print("skip")
            ret = self.front_queue.get(block=False)
            if ret: # no more data, do nothing
                img, orig_path, _ = ret
                self.back_queue.put((img, orig_path, None))
            self.show_current()


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