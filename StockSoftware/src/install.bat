.\python-3.11.8-amd64.exe InstallAllUsers=1 PrependPath=1 Include_test=0
setx /M path "%path%;C:\Program Files\Python311"
$env:PATH =$env:PATH+";C:\Program Files\Python311"
python3 -m ensurepip --upgrade
pip3 install alpaca-py
pip3 install datetime
pip3 install requests
pip3 install pandas
pip3 install numpy