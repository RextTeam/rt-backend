#!/bin/bash
echo "Setupping backend"
cp secret.json.template secret.json
cp data.json.template data.json
python3 -m pip install -r requirements.txt
git clone https://github.com/RextTeam/rt-frontend
git clone https://github.com/RextTeam/rt-lib
mv rt-lib rtlib
cd rtlib
python3 -m pip install -r requirements.txt
cd ..
read input
if [ $input = "y" ] ; then
    nano secret.json
    nano data.json
else
    echo "ok"
fi
echo "Setup was finish"
