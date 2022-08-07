# pawpyrus

![PyPI](https://img.shields.io/pypi/v/pawpyrus?style=flat-square)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pawpyrus?style=flat-square)
![PyPI - Status](https://img.shields.io/pypi/status/pawpyrus?style=flat-square)
![GitHub issues](https://img.shields.io/github/issues/regnveig/pawpyrus?style=flat-square)
![GitHub](https://img.shields.io/github/license/regnveig/pawpyrus?style=flat-square)
![Keybase PGP](https://img.shields.io/keybase/pgp/regnveig?style=flat-square)

pawpyrus is a minimalist opensource paper data storage based on QR codes.
It generates a PDF from any small-sized binary file.
Further, scans of paper data storage can be decoded.

It may be useful for storing encryption keys, password databases, etc.

## Installation

The script is pure Python and a part of PyPI, so can be installed via *pip*:

```bash
python3 -m pip install pawpyrus
```

Or manually:

```bash
git clone https://github.com/regnveig/pawpyrus
cd pawpyrus/dist
python3 -m pip install pawpyrus-2022.8.7-py3-none-any.whl
```

## Usage

Encode file:

```bash
pawpyrus Encode -n "Description" -i  "InputFile" -o "OutputPDF"
```

Decode scans:

```bash
pawpyrus Decode -i "Scan1.jpg" "Scan2.jpg" "Scan3.jpg" -o  "OutputFile"
```

Fair warning:

* Recommended size of file to encode: 100kb or less
* Recommended resolution of scans: 300dpi or more

## Got a trouble?

**QR code detector may fail on one or several blocks.**
This situation is totally normal, although uncomfortable.
That's why I implemented Debug Mode:

```bash
pawpyrus Decode -d "DebugDir" -i "Scan1.jpg" "Scan2.jpg" "Scan3.jpg" -o  "OutputFile"
```

With Debug Mode, you can inspect which QR codes were not detected, read them manually with any device you have, and create a file with codes which may be processed as well:

```bash
pawpyrus Decode "Scan1.jpg" "Scan2.jpg" "Scan3.jpg" -t "UnrecognizedCodes.txt" -o "OutputFile"
```

## Contact

You can contact me by email: [regnveig@yandex.ru](mailto:regnveig@yandex.ru)
