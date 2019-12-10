# AirDoS

<https://kishanbagaria.com/airdos/>

Thanks to Milan Stute and Alexander Heinrich, for authoring [opendrop](https://github.com/seemoo-lab/opendrop) which powers this exploit.

### Usage

1. Run `brew install libarchive openssl@1.1` if not already installed

2. Set environment variables:

```sh
export LIBARCHIVE=/usr/local/opt/libarchive/lib/libarchive.dylib
export LIBCRYPTO=/usr/local/opt/openssl@1.1/lib/libcrypto.dylib
```

3. Run `pip3 install -r requirements.txt`

4. Run `python3 AirDoS.py`
