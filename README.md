&nbsp;

![Logo](https://github.com/regnveig/pawpyrus/blob/main/logo.svg)

## Description

![PyPI](https://img.shields.io/pypi/v/pawpyrus?style=flat-square)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pawpyrus?style=flat-square)
![PyPI - Status](https://img.shields.io/pypi/status/pawpyrus?style=flat-square)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pawpyrus?style=flat-square)
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/regnveig/pawpyrus/sandbox?style=flat-square)
![GitHub issues](https://img.shields.io/github/issues-raw/regnveig/pawpyrus?style=flat-square)
![GitHub closed issues](https://img.shields.io/github/issues-closed-raw/regnveig/pawpyrus?style=flat-square)
![GitHub](https://img.shields.io/github/license/regnveig/pawpyrus?style=flat-square)
![Keybase PGP](https://img.shields.io/keybase/pgp/regnveig?style=flat-square)

pawpyrus is a minimalist open-source paper data storage based on QR codes and ArUco.
It generates a PDF from any small-sized binary file (recommended size 100kb or less).
Further, the paper data storage can be scanned and decoded (recommended resolution 300dpi or more).

It may be useful for:

* Storing encryption keys, password databases, etc.
* Sending digital info by fax

## Installation

The script is pure Python and a part of PyPI, so can be installed via *pip*:

```bash
python3 -m pip install pawpyrus
```

## Usage

File encoder:

```bash
pawpyrus Encode -n "Description" -i  "InputFile" -o "OutputPDF"
```

File decoder:

```bash
pawpyrus Decode -i "Scan1.jpg" "Scan2.jpg" "Scan3.jpg" -o  "OutputFile"
```

## Got a trouble?

**QR code detector may fail on one or several blocks.**
This situation is totally normal, although uncomfortable.
A crush test with about 500 blocks shows 1 unread block.
That's why I implemented Debug Mode:

```bash
pawpyrus Decode -d "DebugDir" -i "Scan1.jpg" "Scan2.jpg" "Scan3.jpg" -o  "OutputFile"
```

With Debug Mode, you can inspect undetected QR codes, read them manually with any device you have, and create a file with codes contents which may be processed as well:

```bash
pawpyrus Decode "Scan1.jpg" "Scan2.jpg" "Scan3.jpg" -t "UnrecognizedCodes.txt" -o "OutputFile"
```

## Contact

You can contact me by email: [regnveig@yandex.ru](mailto:regnveig@yandex.ru)
