''' Unit test for the input parser'''

import unittest
from inputparser import NetworkGraph, InputParser


class TestInputParser(unittest.TestCase):
    def test_import(self):
        # Generate data file
        filename = 'testfile.json'
        NG = NetworkGraph()
        a = NG.add_host()
        b = NG.add_router()
        c = NG.add_host()
        NG.add_link(a, b, rate=4000)
        NG.add_link(b, c, rate=700)
        NG.add_instruction(a, c, 1000000, 1)

        NG.write(filename)

        # Load data file into model
        ip = InputParser()
        ip.load(filename)
        ip.draw()

if __name__ == '__main__':
    unittest.main()
