import unittest
import pybimi
from cachetools import TTLCache

class TestValidator(unittest.TestCase):
    def test_Validator(self):
        domainArr = [
            'dmarc25.jp',
            'dmarc25.jp',
            # 'mango.com',
        ]
        cache = TTLCache(maxsize=100, ttl=1800)
        for domain in domainArr:
            v = pybimi.Validator(domain, cache=cache)
            v.validate()

        domainArr = [
        #     'account.pinterest.com',
        #     'grubhub.com',
        #     'ap.com',
        ]
        for domain in domainArr:
            with self.assertRaises(pybimi.BimiFail):
                v = pybimi.Validator(domain)
                v.validate()
