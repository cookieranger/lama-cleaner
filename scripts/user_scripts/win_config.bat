@echo off

set PATH=C:\Windows\System32;%PATH%

@call installer\Scripts\activate.bat

@call conda-unpack

@call conda install -y cudatoolkit=11.3
@call pip3 install torch --extra-index-url https://download.pytorch.org/whl/cu113
@call pip3 install -U lama-cleaner

@call invoke config
