__version__ = '2022.8.7.3'
__repository__ = 'https://github.com/regnveig/pawpyrus'

from more_itertools import sliced #
from pyzbar.pyzbar import decode #
from qrcode import * #
from reportlab.graphics import renderPDF #
from reportlab.lib.units import mm #
from reportlab.pdfgen import canvas #
from svglib.svglib import svg2rlg #
import argparse
import base64
import binascii
import bitarray #
import cv2 # opencv-python + opencv-contrib-python
import datetime
import hashlib
import io
import itertools
import json
import logging
import math
import numpy #
import os
import secrets
import sys
import tqdm #
import uuid

# -----=====| CONST |=====-----

DATA_CHUNK_SIZE = 108
RUNID_BLOCK_SIZE = 4
INDEX_BLOCK_SIZE = 4
QR_ERROR_CORRECTION = 1
ARUCO_DICTIONARY = cv2.aruco.DICT_5X5_50
MIN_MARKER_PERIMETER_RATE = 1e-9
SPACING_SIZE = 7
COLUMNS_NUM = 6
ROWS_NUM = 8
DOT_SPACING = 3
PDF_PAGE_WIDTH = 210
PDF_PAGE_HEIGHT = 297
PDF_LEFT_MARGIN = 30
PDF_RIGHT_MARGIN = 30
PDF_TOP_MARGIN = PDF_PAGE_HEIGHT - 25
PDF_FONT_FAMILY = 'Courier-Bold'
PDF_FONT_SIZE = 10
PDF_LINE_SPACING = 5
TQDM_STATUSBAR_ASCII = '.#'


# -----=====| LOGGING |=====-----

logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)


# -----=====| CONVERSION |=====-----

def Base64ToInt(String): return int.from_bytes(base64.b64decode(String), 'big')

def IntToBinary(Int, Bits): return f'{Int:b}'.zfill(Bits)

def Base64ToHex(String):
	return hex(Base64ToInt(String))[2:].zfill(math.ceil(len(String) * 6 / 4))


# -----=====| GEOMETRY |=====-----

def FindCenter(CoordBlock):
	return (
		CoordBlock[0][0] + ((CoordBlock[2][0] - CoordBlock[0][0]) / 2),
		CoordBlock[0][1] + ((CoordBlock[2][1] - CoordBlock[0][1]) / 2)
		)


# -----=====| DATASET CREATION |=====-----

def CreateDataset(RawData):
	# Create output struct
	Result = { 'RunID': {}, 'Hash': {}, 'Length': {}, 'Codes': [] }
	# Run ID: unique program run identifier
	Result['RunID']['int'] = secrets.randbits(RUNID_BLOCK_SIZE * 6)
	Result['RunID']['hex'] = hex(Result['RunID']['int'])[2:]
	Result['RunID']['bin'] = IntToBinary(Result['RunID']['int'], RUNID_BLOCK_SIZE * 6)
	# Compute data hash
	Hash = hashlib.sha256(RawData)
	Result['Hash']['hex'] = Hash.hexdigest()
	BitarrayObject = bitarray.bitarray()
	BitarrayObject.frombytes(Hash.digest())
	Result['Hash']['bin'] = BitarrayObject.to01()
	# Encode and chunk raw data
	Codes = list(sliced(base64.b64encode(RawData), DATA_CHUNK_SIZE))
	# Encode length
	Result['Length']['int'] = int(len(Codes) + 1)
	Result['Length']['bin'] = IntToBinary(Result['Length']['int'], INDEX_BLOCK_SIZE * 6)
	# Create header
	Header = bitarray.bitarray(Result['Length']['bin'] + Result['Hash']['bin']).tobytes()
	Codes.insert(0, base64.b64encode(Header))
	# Add block tag: Run ID + block number
	for Index, Content in tqdm.tqdm(enumerate(Codes), total = Result['Length']['int'], desc = 'Create blocks', ascii = TQDM_STATUSBAR_ASCII):
		IndexBinary = IntToBinary(Index, INDEX_BLOCK_SIZE * 6)
		BlockTag = bitarray.bitarray(Result['RunID']['bin'] + IndexBinary).tobytes()
		Result['Codes'].append(base64.b64encode(BlockTag) + Content)
	# Return
	return Result


# -----=====| PAWPRINTS |=====-----

def TomcatPawprint(Data, Coords, PawSize = None, ChunkSize = DATA_CHUNK_SIZE, RunIDBlockSize = RUNID_BLOCK_SIZE, IndexBlockSize = INDEX_BLOCK_SIZE, ErrorCorrection = QR_ERROR_CORRECTION):
	WrappedData = Data.ljust(ChunkSize + RunIDBlockSize + IndexBlockSize, b'=')
	QR = QRCode(error_correction = ErrorCorrection, border = 0)
	QR.add_data(WrappedData)
	QR.make(fit = False)
	Matrix = QR.get_matrix()
	Result = { 'PawSize': len(Matrix) }
	if (PawSize is not None) and (Result['PawSize'] != PawSize): raise RuntimeError(f'Some pawprints have wrong size. Change DATA_CHUNK_SIZE const')
	PixelCoordinates = itertools.product(range(Result['PawSize']), repeat = 2)
	Result['Pixels'] = [ (Coords[0] + X, Coords[1] + Y) for Y, X in PixelCoordinates if Matrix[Y][X] ]
	return Result

def KittyPawprint(ArUcoIndex, Coords, Dictionary = ARUCO_DICTIONARY, SpacingSize = SPACING_SIZE):
	Matrix = cv2.aruco.Dictionary_get(Dictionary).drawMarker(ArUcoIndex, SpacingSize)
	PixelCoordinates = itertools.product(range(SpacingSize), repeat = 2)
	Result = [ (Coords[0] + X, Coords[1] + Y) for Y, X in PixelCoordinates if Matrix[Y][X] == 0 ]
	return Result


# -----=====| DRAW FUNCTIONS |=====-----

def CreatePixelSheets(Codes, ColNum, RowNum, SpacingSize = SPACING_SIZE, DotSpacing = DOT_SPACING):
	# Create output struct
	Result = { 'PawSize': None, 'CellSize': None, 'Pages': list() }
	# Chunk codes to rows and pages
	PageData = list(sliced(list(sliced(Codes, ColNum)), RowNum))
	for PageNumber, Page in enumerate(PageData):
		# Create page
		PixelSheet = list()
		for Row, Col in tqdm.tqdm(itertools.product(range(RowNum), range(ColNum)), total = sum([len(item) for item in Page]), desc = f'Create pawprints, page {PageNumber + 1} of {len(PageData)}', ascii = TQDM_STATUSBAR_ASCII):
			try:
				# Create pawprint on the page
				# Align pawprints by ROOT BLOCK pawsize!
				StartX = (SpacingSize * 2) + (0 if Result['CellSize'] is None else Col * Result['CellSize'])
				StartY = (SpacingSize * 2) + (0 if Result['CellSize'] is None else Row * Result['CellSize'])
				Pawprint = TomcatPawprint(Page[Row][Col], (StartX, StartY), PawSize = Result['PawSize'])
				if Result['PawSize'] is None:
					Result['PawSize'] = int(Pawprint['PawSize'])
					Result['CellSize'] = int(Pawprint['PawSize'] + SpacingSize)
				PixelSheet += Pawprint['Pixels']
			except IndexError:
				# If there are no codes left
				break
		# Create grid
		Grid = {
			0: (0, 0),
			1: (Result['CellSize'] * ColNum, 0),
			2: (0, Result['CellSize'] * len(Page)),
			3: (Result['CellSize'], 0)
			}
		for Index, Item in Grid.items(): PixelSheet += KittyPawprint(Index, Item)
		# Create dot margin (beauty, no functionality)
		DotCentering = math.floor(SpacingSize / 2)
		for Y in list(range(SpacingSize + 2, (Result['CellSize'] * len(Page)) - 2, DotSpacing)):
			PixelSheet.append((DotCentering, int(Y)))
		for X in (
			list(range(SpacingSize + 2, Result['PawSize'] + SpacingSize - 2, DotSpacing)) +
			list(range(Result['PawSize'] + (SpacingSize * 2) + 2, (Result['CellSize'] * ColNum) - 2, DotSpacing))
			):
			PixelSheet.append((int(X), DotCentering))
		# Append page
		Result['Pages'].append(PixelSheet)
	# Return
	return Result

def DrawSVG(PixelSheets, ColNum, SpacingSize = SPACING_SIZE, PdfPageWidth = PDF_PAGE_WIDTH, PdfPageHeight = PDF_PAGE_HEIGHT, PdfLeftMargin = PDF_LEFT_MARGIN, PdfRightMargin = PDF_RIGHT_MARGIN):
	SvgPages = list()
	DrawingWidth = (ColNum * PixelSheets['CellSize']) + SpacingSize
	PixelSize = (PdfPageWidth - PdfLeftMargin - PdfRightMargin) / DrawingWidth
	for PageNumber, Page in enumerate(PixelSheets['Pages']):
		# Draw page
		SvgPage = [
			f'<svg width="{PdfPageWidth}mm" height="{PdfPageHeight}mm" viewBox="0 0 {PdfPageWidth} {PdfPageHeight}" version="1.1" xmlns="http://www.w3.org/2000/svg">',
			f'<path style="fill:#000000;stroke:none;fill-rule:evenodd" d="'
			]
		Paths = list()
		# Add Pixels
		for X, Y in tqdm.tqdm(Page, total = len(Page), desc = f'Draw pixels, page {PageNumber + 1} of {len(PixelSheets["Pages"])}', ascii = TQDM_STATUSBAR_ASCII):
			Paths.append(f'M {X * PixelSize},{Y * PixelSize} H {(X + 1) * PixelSize} V {(Y + 1) * PixelSize} H {X * PixelSize} Z')
		SvgPage.append(f' '.join(Paths))
		SvgPage.append(f'</svg>')
		# Merge svg
		SvgPages.append('\n'.join(SvgPage))
	return SvgPages

def CreatePDF(Dataset, SvgPages, OutputFileName, JobName, PdfLeftMargin = PDF_LEFT_MARGIN, PdfTopMargin = PDF_TOP_MARGIN, PdfLineSpacing = PDF_LINE_SPACING, PdfFontFamily = PDF_FONT_FAMILY, PdfFontSize = PDF_FONT_SIZE, PdfPageHeight = PDF_PAGE_HEIGHT):
	CanvasPDF = canvas.Canvas(OutputFileName)
	Timestamp = str(datetime.datetime.now().replace(microsecond = 0))
	for PageNumber, Page in tqdm.tqdm(enumerate(SvgPages), total = len(SvgPages), desc = f'Convert pages to PDF', ascii = TQDM_STATUSBAR_ASCII):
		# Set font
		CanvasPDF.setFont(PdfFontFamily, PdfFontSize)
		# Convert SVG page
		ObjectPage = svg2rlg(io.StringIO(Page))
		# Captions
		CanvasPDF.drawString(PdfLeftMargin * mm, (PdfTopMargin - (PdfLineSpacing * 1)) * mm, f'Name: {JobName}')
		CanvasPDF.drawString(PdfLeftMargin * mm, (PdfTopMargin - (PdfLineSpacing * 2)) * mm, f'{Timestamp}, run ID: {Dataset["RunID"]["hex"]}, {Dataset["Length"]["int"]} blocks, page {PageNumber + 1} of {len(SvgPages)}')
		CanvasPDF.drawString(PdfLeftMargin * mm, (PdfTopMargin - (PdfLineSpacing * 3)) * mm, f'SHA-256: {Dataset["Hash"]["hex"]}')
		CanvasPDF.drawString(PdfLeftMargin * mm, (PdfTopMargin - (PdfLineSpacing * 4)) * mm, f'pawpyrus {__version__}. Available at: {__repository__}')
		# Draw pawprints
		renderPDF.draw(ObjectPage, CanvasPDF, PdfLeftMargin * mm, - ((PdfPageHeight - PdfTopMargin) + (PdfLineSpacing * 5)) * mm)
		# Newpage
		CanvasPDF.showPage()
	# Save pdf
	CanvasPDF.save()


# -----=====| ENCODE MAIN |=====-----

def EncodeMain(JobName, InputFileName, OutputFileName, ColNum, RowNum):
	logging.info(f'pawpyrus {__version__} Encoder')
	logging.info(f'Job Name: {JobName}')
	logging.info(f'Input File: "{os.path.realpath(InputFileName)}"')
	logging.info(f'Output File: "{os.path.realpath(OutputFileName)}"')
	# Read rawdata
	RawData = open(InputFileName, 'rb').read()
	# Create codes dataset
	Dataset = CreateDataset(RawData)
	logging.info(f'Run ID: {Dataset["RunID"]["hex"]}')
	logging.info(f'SHA-256: {Dataset["Hash"]["hex"]}')
	logging.info(f'Blocks: {Dataset["Length"]["int"]}')
	# Create pixelsheets
	Pages = CreatePixelSheets(Dataset['Codes'], ColNum, RowNum)
	# Draw SVG
	SvgPages = DrawSVG(Pages, ColNum)
	# Draw PDF
	CreatePDF(Dataset, SvgPages, OutputFileName, JobName)
	logging.info(f'Job finished')


# -----=====| EXTRACTION |=====-----

def ExtractData(Line, RunIDBlockSize = RUNID_BLOCK_SIZE, IndexBlockSize = INDEX_BLOCK_SIZE):
	Result = {
		'RunID': Base64ToHex(Line[: RunIDBlockSize]),
		'Index': Base64ToInt(Line[RunIDBlockSize : RunIDBlockSize + IndexBlockSize]),
		'Content': Line[RunIDBlockSize + IndexBlockSize :]
		}
	return Result

def ExtractMetadata(Content, IndexBlockSize = INDEX_BLOCK_SIZE):
	Result = {
		'Length': Base64ToInt(Content[: IndexBlockSize]),
		'Hash': hex(Base64ToInt(Content[IndexBlockSize :]))[2:]
		}
	return Result

def DecodeQR(Barcode):
	Result = { 'Contents': None, 'Detected': { } }
	# pyzbar
	Code = decode(Barcode)
	if Code:
		Result['Contents'] = str(Code[0].data.decode('ascii'))
		Result['Detected']['pyzbar'] = True
	else: Result['Detected']['pyzbar'] = False
	# opencv
	detector = cv2.QRCodeDetector()
	Code = detector.detectAndDecode(Barcode)[0]
	if Code:
		if Result['Contents'] is not None: assert Result['Contents'] == Code, f'Different results with different QR decoders? 1 = {Code}, 2 = {Result["Contents"]})?'
		else: Result['Contents'] = str(Code)
		Result['Detected']['opencv'] = True
	else: Result['Detected']['opencv'] = False
	return Result

# -----=====| DETECT & DECODE |=====-----

def ReadPage(FileName, DebugDir, FileIndex, ArUcoDictionary = ARUCO_DICTIONARY, MinMarkerPerimeterRate = MIN_MARKER_PERIMETER_RATE):
	# Read and binarize image
	Picture = cv2.imread(FileName, cv2.IMREAD_GRAYSCALE)
	Threshold, Picture = cv2.threshold(Picture, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
	if DebugDir is not None: DebugArray = cv2.cvtColor(numpy.copy(Picture), cv2.COLOR_GRAY2RGB)
	logging.info(f'Image binarized (threshold: {Threshold})')
	# Detect markers
	ArUcoDict = cv2.aruco.Dictionary_get(ArUcoDictionary)
	ArUcoParams = cv2.aruco.DetectorParameters_create()
	ArUcoParams.minMarkerPerimeterRate = MinMarkerPerimeterRate
	Markers = cv2.aruco.detectMarkers(Picture, ArUcoDict, parameters = ArUcoParams)
	# Check markers
	if Markers is None: raise RuntimeError('No markers were found')
	if DebugDir is not None:
		for item in range(len(Markers[1])):
			for LineStart, LineEnd in ((0, 1), (1, 2), (2, 3), (3, 0)):
				cv2.line(
					DebugArray,
					tuple(int(i) for i in Markers[0][item][0][LineStart]),
					tuple(int(i) for i in Markers[0][item][0][LineEnd]),
					(255, 0, 0),
					4
				)
			cv2.putText(
				DebugArray,
				f'id={Markers[1][item][0]}',
				(int(Markers[0][item][0][0][0]), int(Markers[0][item][0][0][1]) - 20),
				cv2.FONT_HERSHEY_SIMPLEX,
				1.5,
				(0, 255, 0),
				4
			)
	Markers = { int(Markers[1][item][0]): {'Coords': Markers[0][item][0]} for item in range(len(Markers[1])) }
	if tuple(sorted(Markers.keys())) != (0, 1, 2, 3): raise RuntimeError(f'Wrong markers or lack of markers')
	# Align grid
	MarkerLength = math.dist(Markers[0]['Coords'][0], Markers[0]['Coords'][1])
	for item in Markers:
		Markers[item]['Center'] = FindCenter(Markers[item]['Coords'])
	Width = math.dist(Markers[0]['Center'], Markers[1]['Center'])
	Height = math.dist(Markers[0]['Center'], Markers[2]['Center'])
	CellSize = math.dist(Markers[0]['Center'], Markers[3]['Center'])
	ColNum, RowNum = round(Width / CellSize), round(Height / CellSize)
	logging.info(f'Layout detected: {ColNum} x {RowNum}')
	CellSizeX, CellSizeY = Width / ColNum, Height / RowNum
	VectorX = (
		(Markers[1]['Center'][0] - Markers[0]['Center'][0]) / Width,
		(Markers[1]['Center'][1] - Markers[0]['Center'][1]) / Width
		)
	VectorY = (
		(Markers[2]['Center'][0] - Markers[0]['Center'][0]) / Height,
		(Markers[2]['Center'][1] - Markers[0]['Center'][1]) / Height
		)
	for item in Markers:
		Markers[item]['Center'] = (Markers[item]['Center'][0] + (MarkerLength * VectorX[0]), Markers[item]['Center'][1] + (MarkerLength * VectorY[1]))
	# Chunking by grid
	Chunks = list()
	Cells = itertools.product(range(ColNum), range(RowNum))
	for X, Y in Cells:
		CoordStart = Markers[0]['Center']
		FullVectorX = tuple(item * CellSizeX for item in VectorX)
		FullVectorY = tuple(item * CellSizeY for item in VectorY)
		Chunk = [
			[
				CoordStart[0] + (x * FullVectorX[0]) + (y * FullVectorY[0]),
				CoordStart[1] + (x * FullVectorX[1]) + (y * FullVectorY[1])
				]
				for x, y in ((X, Y), (X + 1, Y), (X + 1, Y + 1), (X, Y + 1))
			]
		Xs, Ys = [x for x, y in Chunk], [y for x, y in Chunk]
		Fragment = Picture[round(min(Ys)):round(max(Ys)), round(min(Xs)):round(max(Xs))]
		Chunks.append({
			'Cell': (int(X) + 1, int(Y) + 1),
			'Coords': Chunk,
			'Image': Fragment
			})
	# Detect and decode
	Codes = list()
	for Chunk in tqdm.tqdm(Chunks, total = len(Chunks), desc = f'Detect QR codes', ascii = TQDM_STATUSBAR_ASCII):
		Code = DecodeQR(Chunk['Image'])
		if Code['Contents'] is not None:
			Color = (0, 255, 0)
			Codes.append(Code)
		else: Color = (0, 0, 255)
		if DebugDir is not None:
			if not Code: cv2.imwrite(os.path.join(DebugDir, f'unrecognized.page-{FileIndex}.x-{Chunk["Cell"][0]}.y-{Chunk["Cell"][1]}.jpg'), Chunk['Image'])
			for LineStart, LineEnd in ((0, 1), (1, 2), (2, 3), (3, 0)):
				cv2.line(
					DebugArray,
					tuple(int(i) for i in Chunk['Coords'][LineStart]),
					tuple(int(i) for i in Chunk['Coords'][LineEnd]),
					(255, 0, 0),
					4
				)
			cv2.putText(
				DebugArray,
				f'({Chunk["Cell"][0]},{Chunk["Cell"][1]})',
				(int(Chunk['Coords'][3][0]) + 10, int(Chunk['Coords'][3][1]) - 30),
				cv2.FONT_HERSHEY_SIMPLEX,
				1.5,
				Color,
				4
			)
	if DebugDir is not None: cv2.imwrite(os.path.join(DebugDir, f'page-{FileIndex}.jpg'), DebugArray)
	return Codes

def VerifyAndDecode(QRBlocks):
	Result = list()
	# Extract blocks
	Extracted = [ExtractData(Line) for Line in QRBlocks]
	Extracted = { item['Index']: item for item in Extracted }
	# Check header
	try:
		Header = Extracted[0]
	except KeyError:
		raise RuntimeError(f'No root block in input data!')
	# Extract metadata
	Metadata = ExtractMetadata(Header['Content'])
	logging.info(f'Blocks: {Metadata["Length"]}')
	logging.info(f'SHA-256: {Metadata["Hash"]}')
	# Check blocks
	MissingBlocks = list()
	for Index in range(1, Metadata['Length']):
		try:
			Extracted[Index]
			if Extracted[Index]['RunID'] != Header['RunID']: raise RuntimeError(f'Some blocks are not of this header')
			Result.append(Extracted[Index]['Content'])
		except KeyError:
			MissingBlocks.append(str(Index))
	if MissingBlocks: raise RuntimeError(f'Some blocks are missing: {"; ".join(MissingBlocks)}')
	# Decode base64
	ResultString = base64.b64decode(''.join(Result))
	# Check hashsum
	if hashlib.sha256(ResultString).hexdigest() != Metadata['Hash']: raise RuntimeError(f'Data damaged (hashes are not the same)')
	# Return
	return ResultString


# -----=====| DECODE MAIN |=====-----

def DecodeMain(ImageInput, TextInput, DebugDir, OutputFileName):
	if (not ImageInput) and (TextInput is None): raise ValueError(f'Input is empty: no images, no text!')
	logging.info(f'pawpyrus {__version__} Decoder')
	if DebugDir is not None:
		logging.info(f'DEBUG MODE ON')
		os.mkdir(DebugDir)
	if ImageInput: logging.info(f'Image Input File(s): "{", ".join([os.path.realpath(item) for item in ImageInput])}"')
	if TextInput is not None: logging.info(f'Text Input File: "{os.path.realpath(TextInput)}"')
	logging.info(f'Output File: "{os.path.realpath(OutputFileName)}"')
	AnnotatedBlocks = list()
	for FileIndex, FileName in enumerate(ImageInput):
		logging.info(f'Proccesing "{FileName}"')
		AnnotatedBlocks += ReadPage(FileName, DebugDir, FileIndex + 1)
	if DebugDir is not None:
		DetectionStatistics = {
			'total': len(AnnotatedBlocks),
			'pyzbar_only': [(not block['Detected']['opencv']) and block['Detected']['pyzbar'] for block in AnnotatedBlocks].count(True),
			'opencv_only': [block['Detected']['opencv'] and (not block['Detected']['pyzbar']) for block in AnnotatedBlocks].count(True),
			'both': [block['Detected']['opencv'] and block['Detected']['pyzbar'] for block in AnnotatedBlocks].count(True),
			'neither': [(not block['Detected']['opencv']) and (not block['Detected']['pyzbar']) for block in AnnotatedBlocks].count(True)
			}
		json.dump(DetectionStatistics, open(os.path.join(DebugDir, 'detection_stats.json'), 'wt'), indent = 4)
	Blocks = [block['Contents'] for block in AnnotatedBlocks]
	if TextInput is not None:
		with open(TextInput, 'rt') as TF: Blocks += [ Line[:-1] for Line in TF.readlines() if Line[:-1] != '\n' ]
	if DebugDir is not None:
		with open(os.path.join(DebugDir, 'blocks.txt'), 'wt') as BF: BF.write('\n'.join(Blocks))
	Result = VerifyAndDecode(Blocks)
	with open(OutputFileName, 'wb') as Out: Out.write(Result)
	logging.info(f'Job finished')

## ------======| PARSER |======------

def CreateParser():
	Default_parser = argparse.ArgumentParser(
			formatter_class = argparse.RawDescriptionHelpFormatter,
			description = f'pawpyrus {__version__}: Minimalist paper data storage based on QR codes',
			epilog = f'Bug tracker: https://github.com/regnveig/pawpyrus/issues'
			)
	Default_parser.add_argument ('-v', '--version', action = 'version', version = __version__)
	Subparsers = Default_parser.add_subparsers(title = 'Commands', dest = 'command')
	# Encode parser
	EncodeParser = Subparsers.add_parser('Encode', help=f'Encode data as paper storage PDF file')
	EncodeParser.add_argument('-n', '--name', required = True, type = str, dest = 'JobName', help = f'Job name. Will be printed in page header. Required.')
	EncodeParser.add_argument('-i', '--input', required = True, type = str, dest = 'InputFile', help = f'File to encode. Required.')
	EncodeParser.add_argument('-o', '--output', required = True, type = str, dest = 'OutputFile', help = f'PDF file to save. Required.')
	EncodeParser.add_argument('-c', '--cols', type = int, default = COLUMNS_NUM, dest = 'ColNum', help = f'Columns number. Default = {COLUMNS_NUM}')
	EncodeParser.add_argument('-r', '--rows', type = int, default = ROWS_NUM, dest = 'RowNum', help = f'Rows number. Default = {ROWS_NUM}')
	# Decode parser
	DecodeParser = Subparsers.add_parser('Decode', help=f'Decode data from paper storage scans')
	DecodeParser.add_argument('-i', '--image', nargs = '*', type = str, dest = 'ImageInput', help = f'Paper storage scans to decode.')
	DecodeParser.add_argument('-t', '--text', type = str, default = None, dest = 'TextInput', help = f'Files with lists of QR codes content, gathered manually.')
	DecodeParser.add_argument('-o', '--output', required = True, type = str, dest = 'OutputFile', help = f'File to save decoded data. Required.')
	DecodeParser.add_argument('-d', '--debug-dir', type = str, default = None, dest = 'DebugDir', help = f'Directory where to collect debug data if necessary.')

	return Default_parser

# -----=====| MAIN |=====-----

def main():
	Parser = CreateParser()
	Namespace = Parser.parse_args(sys.argv[1:])
	if Namespace.command == 'Encode':
		EncodeMain(
			InputFileName = Namespace.InputFile,
			JobName = Namespace.JobName,
			OutputFileName = Namespace.OutputFile,
			ColNum = Namespace.ColNum,
			RowNum = Namespace.RowNum
			)
	elif Namespace.command == 'Decode':
		DecodeMain(
			ImageInput = Namespace.ImageInput,
			TextInput = Namespace.TextInput,
			DebugDir = Namespace.DebugDir,
			OutputFileName = Namespace.OutputFile
			)
	else: Parser.print_help()

if __name__ == '__main__': main()
