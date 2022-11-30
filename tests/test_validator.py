import unittest
import pybimi

class TestValidator(unittest.TestCase):
    def test_Validator(self):
        domainArr = [
            'dmarc25.jp',
            'mango.com',
        ]
        for domain in domainArr:
            v = pybimi.Validator(domain)
            v.validate()

        domainArr = [
            'account.pinterest.com',
            'grubhub.com',
            'ap.com',
        ]
        for domain in domainArr:
            with self.assertRaises(pybimi.BimiFail):
                v = pybimi.Validator(domain)
                v.validate()
