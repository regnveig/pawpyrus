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
* Faxing digital data

## Installation

The script is pure Python and a part of [PyPI](https://pypi.org/project/pawpyrus), so can be installed via *pip*:

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

Output PDF example you can see [here](https://github.com/regnveig/pawpyrus/blob/main/examples/The_Old_Man_and_the_Sea_encoded.pdf).

## Data Format

Every storaged file has the following parts:

1. **Header (zero) block**. Contains:
	- *Run ID*: 24 bits. Unique number to distinguish blocks origin.
	- *Number of blocks*: 24 bits.
	- *SHA-256 checksum*.
2. **Data blocks**. Contain:
	- *Run ID*: 24 bits.
	- *Data block number*: 24 bits.
	- *Data chunk*: 324 bytes by default.

Number of blocks per page can be specified in the command line.
Other parameters can be changed in the script code.

### Why 324 bytes?

It's the maximal size of QR which can be recognized with my ancient smartphone.
In can be changed in the script code.

## Got a Trouble?

**QR code detectors may fail on one or several blocks.**
This situation is totally normal, although uncomfortable.
I fixed it for now, with two detectors instead of one, but the bug may reappear in some circumstances (if blocks number is big enough, or scans quality is low enough).
That's why I implemented Debug Mode:

```bash
pawpyrus Decode -d "DebugDir" -i "Scan1.jpg" "Scan2.jpg" "Scan3.jpg" -o  "OutputFile"
```

With Debug Mode, you can inspect undetected QR codes, read them manually with any device you have, and create a file with codes contents which may be processed as well:

```bash
pawpyrus Decode "Scan1.jpg" "Scan2.jpg" "Scan3.jpg" -t "UnrecognizedCodes.txt" -o "OutputFile"
```

Output Debug Dir example you can see [here](https://github.com/regnveig/pawpyrus/tree/main/examples/decoder_debug_mode).

If you have any idea how to fix it better, [please help](https://github.com/regnveig/pawpyrus/issues/4).

## Similar Projects

1. [intra2net/paperbackup](https://github.com/intra2net/paperbackup):
Very similar to pawpyrus.
Create a pdf with barcodes to backup text files on paper.
Designed to backup ASCII-armored GnuPG and SSH key files and ciphertext.

2. [Paperback by Olly](https://ollydbg.de/Paperbak/):
Free application that allows you to back up your precious files on the ordinary paper in the form of the oversized bitmaps.
If you have a good laser printer with the 600dpi resolution, you can save up to 500,000 bytes of uncompressed data on the single A4/Letter sheet.
Integrated packer allows for much better data density - up to 3,000,000+ (three megabytes) of C code per page.
[Wikinaut/paperback-cli](https://github.com/Wikinaut/paperback-cli):
Crossplatform, backwards-compatible, command line version of Paperback.

3. [colorsafe/colorsafe](https://github.com/colorsafe/colorsafe):
A data matrix scheme for printing on paper and microfilm.
Inspired by Paperbak, ColorSafe is written in Python and has a flexible specification.
It aims to allow a few Megabytes of data (or more) to be stored on printable media for a worst case scenario backup, for extremely long-term archiving, or just for fun.

4. [Twibright Optar](http://ronja.twibright.com/optar):
Codec for encoding data on paper or free software 2D barcode in other words.
Optar fits 200kB on an A4 page.
A practical level of reliability is ensured using forward error correction code (FEC).
Automated processing of page batches facilitates storage of files larger than 200kB.

5. [Paperkey](https://www.jabberwocky.com/software/paperkey):
It is designed to reduce the data needed to backup a private GnuPG key.

6. [4bitfocus/asc-key-to-qr-code](https://github.com/4bitfocus/asc-key-to-qr-code):
Shell scripts to convert between ascii armor PGP keys and QR codes for paper backup.

## Contact

You can contact me by email: [regnveig@yandex.ru](mailto:regnveig@yandex.ru)
