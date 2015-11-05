#!/bin/bash

echo "running network object test"
python ../tests/networkobject_test.py

echo
echo "running event handler test"
python ../tests/eventhandler_test.py

echo
echo "running network creation test"
python ../tests/network_test.py