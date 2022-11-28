import unittest
import pybimi

class TestSvgValidator(unittest.TestCase):
    def test_SvgValidator(self):
        domainArr = [
            'dmarc25.jp',
            'mango.com',
        ]
        for domain in domainArr:
            lv = pybimi.LookupValidator(domain)
            sv = pybimi.SvgValidator(lv.validate().location)
            sv.validate()

        domainArr = [
            'myfritz.net',
        ]
        for domain in domainArr:
            with self.assertRaises(pybimi.BimiFail):
                lv = pybimi.LookupValidator(domain)
                sv = pybimi.SvgValidator(lv.validate().location, pybimi.SvgOptions(maxSizeInBytes=50000))
                sv.validate()

        domainArr = [
            'quizlet.com',
            'drouot.com',
        ]
        for domain in domainArr:
            with self.assertRaises(pybimi.BimiFail):
                lv = pybimi.LookupValidator(domain)
                sv = pybimi.SvgValidator(lv.validate().location)
                sv.validate()
