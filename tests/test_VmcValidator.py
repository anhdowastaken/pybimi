import unittest
import pybimi

class TestVmcValidator(unittest.TestCase):
    def test_VmcValidator(self):
        domainArr = [
            'dmarc25.jp',
            'mango.com',
        ]
        for domain in domainArr:
            lv = pybimi.LookupValidator(domain)
            rec = lv.validate()
            vv = pybimi.VmcValidator(vmcUri=rec.authorityEvidenceLocation,
                                     indicatorUri=rec.location,
                                     domain=rec.domain)
            vv.validate()

        domainArr = [
            'account.pinterest.com',
            'grubhub.com',
            'ap.com',
        ]
        for domain in domainArr:
            with self.assertRaises(pybimi.BimiFail):
                lv = pybimi.LookupValidator(domain)
                rec = lv.validate()
                vv = pybimi.VmcValidator(vmcUri=rec.authorityEvidenceLocation,
                                         indicatorUri=rec.location,
                                         domain=rec.domain)
                vv.validate()
