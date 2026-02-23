import unittest
import os
from datadirtest import DataDirTester


class TestComponent(unittest.TestCase):
    def test_functional(self):
        os.environ["KBC_STACKID"] = "connection.keboola.com"

        functional_tests = DataDirTester()
        functional_tests.run()

    def test_functional_types(self):
        os.environ["KBC_STACKID"] = "connection.keboola.com"
        os.environ['KBC_PROJECT_FEATURE_GATES'] = 'queuev2;someotherfeature'
        os.environ["KBC_DATA_TYPE_SUPPORT"] = "authoritative"
        functional_tests = DataDirTester(data_dir="./tests/functional_dtypes")
        functional_tests.run()


if __name__ == "__main__":
    unittest.main()
