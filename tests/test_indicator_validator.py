import unittest
import pybimi

class TestIndicatorValidator(unittest.TestCase):
    def test_IndicatorValidator(self):
        domainArr = [
            'dmarc25.jp',
            'mango.com',
        ]
        for domain in domainArr:
            lv = pybimi.LookupValidator(domain)
            rec = lv.validate()
            iv = pybimi.IndicatorValidator(rec.location)
            iv.validate()

        domainArr = [
            'myfritz.net',
        ]
        for domain in domainArr:
            with self.assertRaises(pybimi.BimiFail):
                lv = pybimi.LookupValidator(domain)
                rec = lv.validate()
                iv = pybimi.IndicatorValidator(rec.location,
                                               pybimi.IndicatorOptions(maxSizeInBytes=50000))
                iv.validate()

        domainArr = [
            'quizlet.com',
            'drouot.com',
        ]
        for domain in domainArr:
            with self.assertRaises(pybimi.BimiFail):
                lv = pybimi.LookupValidator(domain)
                rec = lv.validate()
                iv = pybimi.IndicatorValidator(rec.location)
                iv.validate()
