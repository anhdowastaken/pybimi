import unittest
import pybimi

class TestLookupValidator(unittest.TestCase):
    def test_LookupValidator(self):
        domainArr = [
            'mango.com',
            'a.mango.com',
        ]
        for domain in domainArr:
            lv = pybimi.LookupValidator(domain)
            print(lv.validate())

        domainArr = [
            'change.org',
            'e.change.org',
        ]
        for domain in domainArr:
            with self.assertRaises(pybimi.BimiNoPolicy):
                lv = pybimi.LookupValidator(domain)
                print(lv.validate())

        domainArr = [
            'mac.com',
            'me.com',
        ]
        for domain in domainArr:
            with self.assertRaises(pybimi.BimiDeclined):
                lv = pybimi.LookupValidator(domain)
                print(lv.validate())

        domainArr = [
            'news.united.com',
            'pixiv.net',
            'sandalsmailings.com',
            'e.safelite.com',
            'keysso.net',
        ]
        for domain in domainArr:
            with self.assertRaises(pybimi.BimiFail):
                lv = pybimi.LookupValidator(domain)
                print(lv.validate())
