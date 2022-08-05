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

`Topho` uses [mpv media player](https://mpv.io/) to view `.gif` and video files. Please install it beforehand.

If have made command `mpv` available on commandline (by modifying `PATH` environment variable), `Topho` can find it itself.
Otherwise, you have to specify the path in the option `--mpv path/to/mpv/exe` like (`topho.exe <other options> --mpv C:\Users\John\Downloads\mpv-x86_64-20220320-git-f871294\mpv.exe`)

### binary

You can find pre-built portable binary of `Topho` at [release page](https://github.com/bivoje/topho/releases/latest), files named as `tohpo_*.zip`.
It is rather big (compared to the source code) but contains every single dependency needed for `Topho` to run.

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
usage: Topho [-h] [--version] [--dry] [--keep] [--maxw MAXW] [--maxh MAXH]
             [--name_format NAMEF] [--test_names [TEST_NAMES ...]] [--logfile LOGFILE] [--mpv MPVPATH]
             [--frontq_min FQm] [--frontq_max FQM] [--backq_min BQm] [--backq_max BQM]
             source_dir [target_dir]

Minimallistic utility for manual image organizing

positional arguments:
  source_dir            path of image directory to organize
  target_dir            path of directory to store organized images, defaults to current directory, created if not exists (default: None)

optional arguments:
  -h, --help            show this help message and exit
  --version, -v         show program's version number and exit
  --dry, -n             don't actually move files, only pretend organizing (default: False)
  --keep, --copy        keep the original files (copy, not move) (default: False)
  --maxw MAXW           maximum width of image, defaults to screen width * 0.8 (default: 1536)
  --maxh MAXH           maximum height of image, defaults to screen height * 0.8 (default: 864)
  --name_format NAMEF   python style formatstring for moved file names, see <NAMEF> section (default: {name})
  --test_names [TEST_NAMES ...]
                        if provided, apply name_format on this filename, print then exits (default: None)
  --logfile LOGFILE     path to log file where unmoved file list will be written (default: topholog.txt)
  --mpv MPVPATH         path to invoke mpv player executable (default: mpv.exe)
  --frontq_min FQm      minimum # of images pre-loaded, increase if forward loading is too slow (default: 3)
  --frontq_max FQM      maximum # of images kept loaded when un-doing, increase if you frequently undo & redo (default: 10)
  --backq_min BQm       minimum # of images loaded for un-doing, increase if backward loading is too slow (default: 3)
  --backq_max BQM       maximum # of images kept loaded after organizing, increase if you frequently undo & redo (default: 5)

NAMEF:
    You can describe new name for moved file using python style formating.
    For example, giving --name_format="{index}th-image-{name}__{size}bytes"
    converts "nyancat.gif" to "1th-image-nyancat__1038bytes.gif".
    See following sections for available formatting options and variables.

NAMEF variables:
    index    :int  - enumeration, starting from 0
    name     :str  - original name of the file
    size     :int  - size of the file in bytes
    hier     :slice- list of parent directories from source_dir, inclusive
    created  :time - file creation time
    modified :time - file modification time
    accessed :time - file access time
    dup      :dup  - enumeration among duplicated names, starting from 0

NAMEF formatting:
    Before anything, note that only attribute access is allowed for variables,
    which means "{index*2}" is cannot be done. So we provide some attribute
    extension for ease of handling variables.

    For integer type, additional arithmetic attributes are provided as well
    as basic integer formatting syntax. You can do (asssuming index=9)
    - .p<n>, .t<n> for addition
      "{index.p20}" == '29'
    - .m<n> for subtraction
      "{index.m10}" == '-1'
    - .x<n>, .X<n> for multiplication
      "{index.x3}" == '27'
    - .d<n> for integer division
      "{index.d2}" == '4'
    - mixture of all
      "{index.p3.x2.4}" == '6'
    - with integer format_spec
      "{index.p3.x2.4:+03}" == '+006'

    For slice type, start-end slicing attributes are provided. format spec can be
    preceded with a seperator as '<sep>!<spec>' which will be used to join slice elements.
    If spereator is omitted, it defaults to '' or '\' for 'hier' variable.
    <spec> is basic python formatter, applys element-wisely. Each formatted result
    then joined by <sep>. string types are simliar to slice type but <spec> applys to
    the whole string. You can do (assuming name=asdf)
    - ._<n> for starting index, same as str[n:]
      "{slice._2}" == 'df'
    - .__<m> for ending index, same as str[:m]
      "{slice.__3}" == 'asd'
    - ._<n>_<m> to take range [n, m), same as str[n:m]
      "{name._1_3}" == 'sd'
    - indexing from behind, use 'm' prefix instead of '-' to indicate negative
      "{name._1_m1}" == 'sd'
    - complex mixture example
      "=={name._3:#^7}---" == '==##asd##---'

    'hier' is slice variable consisting of directory names from source_dir to
    the file. '' element is at the end to add trailing seperator.
    Assume source_dir = 'images' and filepath is 'images\source\dir\y.png', then
    hier == ['images', 'source', 'dir', ''] and name == y.png,
    - simpy using with {name} to get filepath (from source_dir)
      "{hier}{name}" == 'images\source\dir\y.png'
    - use custome seperator with custom elem-wize formatting
      "{hier:-!:_<5}{name}" == 'images-source-dir__-y.png'
    - remove trailing seperator by slicing
      "{hier._1_m1}_{name}" == 'source\dir_y.png'

    For time types, you can use strftime format in format_spec region.
    See https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
    for more detailed explanations. Examples follows..
    - default formatting shows iso-8601 date
      "{created}" == '2022-08-02'
    - by specifying 'iso' as format you get full iso-8601 representation
      "{created:iso}" == '2022-08-02T07:23:45+0900'
    - accessing 'utc' attribute gives datetime in UTC
      "{created.utc:iso}" == '2022-08-01T22:23:45+0000'
    - all attributes of python datatime struct supported
      "{created.day:03}" == '002'
    - strftime style formatting
      "{created:%Y_%S}" == '2022_45'

    'dup' type is similar to 'int' type, all arithmetic attbributes are
    provided but has extended format spec. Normal integer format spec
    is may preceeded by enclosure specifier of format "<prefix>!<suffix>!".
    If enclosure specifier exists dup acts in hermit mode, expose itself
    (and enclosure) only if dup > 0.
    For example, if there are only 1 file created on 2022-08-02, the
    formatstring "{created}{dup.x2.m2:==(!)!0^3}" simply yields '2022-08-02'.
    But if there are 4 of them, they will be renamed as (in sorted order)
    '2022-08-02==(-20)', '2022-08-02', '2022-08-02==(020)' '2022-08-02==(040)'.
    Note that hermit mode depends on result 'dup.x2.m2' not the original 'dup'.
    If format_spec is empty, you can omit trailing '!', like "{dup:(!)}"
```

#### Examples
```
> .\topho.exe images this/dir/right/here --name_format '{hier._m2:_!}{name}' --test_names small\1.png mid\4.png big\extra\space.jpg
this\dir\right\here\small_1.png
this\dir\right\here\mid_4.png
this\dir\right\here\extra_space.jpg
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
[v] custom rename rules
[ ] source directory recursive, target sub-directory???
[ ] safe & powerful custom rename rules (string->int operation, index+size etc)
[ ] delete during organizing
[ ] trashcan (can contain duplicated names.. & keep sources; restore)
[v] cancel and quit feature
[v] handle when dst already exists
[v] handle when can't load file
[ ] remove loading right before the end
[ ] backward loading handling
[v] accept mpv executable path
[ ] support other viewer programs & passing-over options
[ ] load from error log
[ ] save in mid progress feature (in cases like out of disk space etc?)
[ ] add message "SPACE to start", "'c' to commit" to start.png & end.png

Images
------------------

![start_img](./start.png "start_img")
![end_img](./end.png "end_img")
![loading_img](./loading.png "loading_img")
![video_img](./video.png "video_img")
![unrecog_img](./unrecognized.png "unrecog_img")
![broken_img](./broken.png "broken_img")