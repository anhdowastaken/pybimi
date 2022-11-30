# PYBIMI

## 1. Requirements
- JAVA is required to validate the indicator

## 2. Install
- Pull the repository
- Install pybimi via pip:
  ```text
  $ pip install <pybimi_dir>
  ```

## 3. Simple usage
```text
# main.py

import pybimi

domains = [
    'dmarc25.jp',
    'quizlet.com',
    'account.pinterest.com',
    'grubhub.com',
]
for domain in domains:
    v = pybimi.Validator(domain)
    try:
        v.validate()
    except pybimi.BimiError as e:
        print('{}: {}'.format(domain, e))
    else:
        print('{}: OK'.format(domain))
```
```text
$ python main.py
dmarc25.jp: OK
quizlet.com: element "html" not allowed anywhere; expected element "svg" (with xmlns="http://www.w3.org/2000/svg")
account.pinterest.com: the VMC is not valid for account.pinterest.com (valid hostnames include: pinterest.com)
grubhub.com: data from Location and data from Authority Evidence Location are not identical
```
