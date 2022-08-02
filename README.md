Topho
==================

Minimallistic utility for manual image organizing.


Intro
------------------

Having a bunch of images (memes, pictures, videos, etc) in one place, want to organize them into separate folders by their topics (WW3 memes, mlporn..).

Your images are so sophisticated that no automatic organization utilities can be used?

But too lazy to click & drag each file one by one?

Also, don't want to install bloatwares just for this simple task?

`Topho` is right for you!


Install
------------------

### general dependency

`Topho` uses [mpv media player](https://mpv.io/) to view `.gif` and video files.
You need to make command `mpv` available on system path.

Simply download mpv and add it to the `PATH` environment.

### binary

You can find pre-built portable binary of `Topho` at [release page](https://github.com/bivoje/topho/releases/latest), files names  `tohpo_*.zip`.
It is rather big (compared to the source code) but contains every single dependency needed for `Topho`.

Just extract it in any directory you favor then you are set to go.
Substitute `<EXE>` with `path\to\topho\installed\topho.exe` in [Usage](##Usage). (e.g. `C:\Users\John\Downloads\topho_1.0.0_x86-64_win\topho.exe`)

### source

If you decided to run `Tohpo` using python source script for some bizzar reason, you need to get library depencies ready.
There are only one python library required for now.
```
pip install Pillow
```
Note that `Topho` is only tested with `python 3.9.7`, `Pillow 8.4.0` on `Windows 10` with `x86-64` cpu.
Please notify me if any error occures with other configurations.

Then just download the source code
```
git clone https://github.com/bivoje/topho.git
```
... or using whatever method you'd like.

Substitute `<EXE>` with `python path\to\topho\script` in [Usage](##Usage). (e.g. `C:\Users\John\Downloads\topho\topho.py`)


Usage
------------------

`Topho` is minimalistic, providing its central feature.
Its UI design is mainly influenced by `mpv` and `vim`, no widgets, only key-strokes.

Also, for simple interface, you need to invoke the program using commandline with arguments.

#### starting the program
1. Open commandline terminal (e.g. windows powershell).
2. `cd` into the directory where you want organized folders to be.
3. Run command `<EXE> path\of\image\directory\to\organize`

Then a GUI window opens displaying `start_img`.
You can use relative path as well as unix-style indicators (`.`, `..`)

#### GUI window displays
- on the start, it displays `start_img`
- if there's no more files to organize, it displays `end_img`.
- if image file is yet loading, it displays `loading_img`.
- if the file is opened using `mpv` it displays `video_img`.
- if file format is unrecognized, it displays `unrecog_img`.
- if the file could not be read (moved, broken etc), it displays `broken_img`.
- 'current dicision of the image' and 'the name of the file' is on the window's title text.

You can see images at [images](##images).
Note that `loading_img` does not go away by itself. You need to repeatedly press `r` to check it.
Pressing `0`~`9`, `U`, `SPACE` does nothing on `loading_img`, be patient and stick to `r`.
<!-- If you think you are seeing too many `loading_img` -->

#### organizing images
Press `SPACE` to start. From now on, each image of the folder will be displayed and wait for your command.
- `ESC`: quit, without commit. all files will be left untouched. (`q` is not mapped to avoid misusing with `mpv`)
- `c`: quit, commit moving files as specified. unspecified files will be left untouched.
- `r`: reload the image. you can re-open `mpv` using this.
- `0`: skip this image. don't move this one.
- `1` ~ `9`: send the image to folder `i`. (not actually sent, all the file operations are executed when everything is done)
- `u`: undo sending files. previous decision is not forgetten and can be revoked by `U`.
- `U`, `SPACE`: redo sending files. if not previously decided, sent to `0` by default.

#### use case
Suppose you want to organize images in `D:\Pictures\memes` directory, into `C:\users\John\Desktop\memes\0~9`.

You have downloaded `topho_1.0.0_x86-64_win.zip` and extracted to `C:\Users\John\Downloads\topho_1.0.0_x86-64_win`

Open powershell then
```
PS C:\Users\John> cd Desktop\memes
PS C:\Users\John\Desktop\memes> C:\Users\John\Downloads\topho_1.0.0_x86-64_win\topho.exe D:\Pictures\memes
```
After program finishes, all the files from `D:\Pictures\memes` are now moved into `C:\users\John\Desktop\memes\0~9`.

#### more options!
Considering yourself an advanced user, there are several options to be utilized.
```
> topho.exe -h
usage: Topho [-h] [--version] [--dry] [--maxw MAXW] [--maxh MAXH]
             [--frontq_min FQm] [--frontq_max FQM] [--backq_min BQm] [--backq_max BQM]
             source_dir [target_dir]

Minimallistic utility for manual image organizing

positional arguments:
  source_dir        path of image directory to organize
  target_dir        path of directory to store organized images

optional arguments:
  -h, --help        show this help message and exit
  --version, -v     show program's version number and exit
  --dry, -n         don't actually move files, only pretend organizing
  --maxw MAXW       maximum width of image, defaults to screen width * 0.8
  --maxh MAXH       maximum height of image, defaults to screen height * 0.8
  --frontq_min FQm  minimum # of images pre-loaded, increase if forward loading is too slow. default=3
  --frontq_max FQM  maximum # of images kept loaded when un-doing, increase if you frequently undo & redo. default=10
  --backq_min BQm   minimum # of images loaded for un-doing, increase if backward loading is too slow. default=3
  --backq_max BQM   maximum # of images kept loaded after organizing, increase if you frequently undo & redo. default=5
```


Build
------------------

Portable binary version of `Topho` is built using [pyinstaller](https://pyinstaller.org/en/stable/).

```
pip install pyinstaller
pyinstaller .\topho.py
zip distr\topho
```


TODO list
------------------
[v] resize images to fit into screen
[ ] custom rename rules
[ ] delete during organizing
[ ] cancel and quit feature
[ ] handle when dst already exists
[ ] handle when can't load file
[ ] remove loading right before the end


Images
------------------

![start_img](./start.png "start_img")
![end_img](./end.png "end_img")
![loading_img](./loading.jpg "loading_img")
![video_img](./video.png "video_img")
![unrecog_img](./unrecog.jpg "unrecog_img")
![broken_img](./broken.png "broken_img")
