#!/bin/bash

echo "running network object test"
python ../src/networkobject_test.py

echo
echo "running event handler test"
python ../src/eventhandler_test.py

echo
echo "running network creation test"
python ../src/network_test.py