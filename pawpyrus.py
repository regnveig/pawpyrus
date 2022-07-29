__author__ = 'Emil Viesná [regnveig]'
__version__ = 'v0.11'

from more_itertools import sliced
from pyzbar.pyzbar import decode
from qrcode import *
from reportlab.graphics import renderPDF
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg
import argparse
import base64
import bitarray
import cv2
import datetime
import hashlib
import io
import itertools
import logging
import math
import numpy
import os
import secrets
import sys
import tqdm


# -----=====| CONST |=====-----

DATA_CHUNK_SIZE = 108
RUNID_BLOCK_SIZE = 4
INDEX_BLOCK_SIZE = 4
QR_ERROR_CORRECTION = 1
ARUCO_DICTIONARY = cv2.aruco.DICT_5X5_50
MIN_MARKER_PERIMETER_RATE = 0.00001
SPACING_SIZE = 7
COLUMNS_NUM = 6
ROWS_NUM = 8
DOT_SPACING = 3
PDF_PAGE_WIDTH = 210
PDF_PAGE_HEIGHT = 297
PDF_LEFT_MARGIN = 28
PDF_RIGHT_MARGIN = 35
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

def Base64ToHex(String): return hex(Base64ToInt(String))[2:].zfill(math.ceil(len(String) * 6 / 4))


# -----=====| GEOMETRY |=====-----

def FindCenter(CoordBlock):
	return (
		CoordBlock[0][0] + (abs(CoordBlock[0][0] - CoordBlock[2][0]) / 2),
		CoordBlock[0][1] + (abs(CoordBlock[0][1] - CoordBlock[2][1]) / 2)
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

def TomcatPawprint(Data, Coords, PawSize = None):
	WrappedData = Data.ljust(DATA_CHUNK_SIZE, b'=')
	QR = QRCode(error_correction = QR_ERROR_CORRECTION, border = 0)
	QR.add_data(WrappedData)
	QR.make(fit = False)
	Matrix = QR.get_matrix()
	Result = { 'PawSize': len(Matrix) }
	if (PawSize is not None) and (Result['PawSize'] != PawSize): raise RuntimeError(f'Some pawprints have wrong size. Change DATA_CHUNK_SIZE const')
	PixelCoordinates = itertools.product(range(Result['PawSize']), repeat = 2)
	Result['Pixels'] = [ (Coords[0] + X, Coords[1] + Y) for Y, X in PixelCoordinates if Matrix[Y][X] ]
	return Result

def KittyPawprint(ArUcoIndex, Coords):
	Matrix = cv2.aruco.Dictionary_get(ARUCO_DICTIONARY).drawMarker(ArUcoIndex, SPACING_SIZE)
	PixelCoordinates = itertools.product(range(SPACING_SIZE), repeat = 2)
	Result = [ (Coords[0] + X, Coords[1] + Y) for Y, X in PixelCoordinates if Matrix[Y][X] == 0 ]
	return Result


# -----=====| DRAW FUNCTIONS |=====-----

def CreatePixelSheets(Codes):
	# Create output struct
	Result = { 'PawSize': None, 'CellSize': None, 'Pages': list() }
	# Chunk codes to rows and pages
	PageData = list(sliced(list(sliced(Codes, COLUMNS_NUM)), ROWS_NUM))
	for PageNumber, Page in enumerate(PageData):
		# Create page
		PixelSheet = list()
		for Row, Col in tqdm.tqdm(itertools.product(range(ROWS_NUM), range(COLUMNS_NUM)), total = sum([len(item) for item in Page]), desc = f'Create pawprints, page {PageNumber + 1} of {len(PageData)}', ascii = TQDM_STATUSBAR_ASCII):
			try:
				# Create pawprint on the page
				# Align pawprints by ROOT BLOCK pawsize!
				StartX = (SPACING_SIZE * 2) + (0 if Result['CellSize'] is None else Col * Result['CellSize'])
				StartY = (SPACING_SIZE * 2) + (0 if Result['CellSize'] is None else Row * Result['CellSize'])
				Pawprint = TomcatPawprint(Page[Row][Col], (StartX, StartY), PawSize = Result['PawSize'])
				if Result['PawSize'] is None:
					Result['PawSize'] = int(Pawprint['PawSize'])
					Result['CellSize'] = int(Pawprint['PawSize'] + SPACING_SIZE)
				PixelSheet += Pawprint['Pixels']
			except IndexError:
				# If there are no codes left
				break
		# Create grid
		Grid = {
			0: (0, 0),
			1: (Result['CellSize'] * COLUMNS_NUM, 0),
			2: (0, Result['CellSize'] * len(Page)),
			3: (Result['CellSize'], 0)
			}
		for Index, Item in Grid.items(): PixelSheet += KittyPawprint(Index, Item)
		# Create dot margin (beauty, no functionality)
		DotCentering = math.floor(SPACING_SIZE / 2)
		for Y in list(range(SPACING_SIZE + 2, (Result['CellSize'] * len(Page)) - 2, DOT_SPACING)):
			PixelSheet.append((DotCentering, int(Y)))
		for X in (
			list(range(SPACING_SIZE + 2, Result['PawSize'] + SPACING_SIZE - 2, DOT_SPACING)) +
			list(range(Result['PawSize'] + (SPACING_SIZE * 2) + 2, (Result['CellSize'] * COLUMNS_NUM) - 2, DOT_SPACING))
			):
			PixelSheet.append((int(X), DotCentering))
		# Append page
		Result['Pages'].append(PixelSheet)
	# Return
	return Result

def DrawSVG(PixelSheets):
	SvgPages = list()
	DrawingWidth = (COLUMNS_NUM * PixelSheets['CellSize']) - SPACING_SIZE
	PixelSize = (PDF_PAGE_WIDTH - PDF_LEFT_MARGIN - PDF_RIGHT_MARGIN) / DrawingWidth
	for PageNumber, Page in enumerate(PixelSheets['Pages']):
		# Draw page
		SvgPage = [
			f'<svg width="{PDF_PAGE_WIDTH}mm" height="{PDF_PAGE_HEIGHT}mm" viewBox="0 0 {PDF_PAGE_WIDTH} {PDF_PAGE_HEIGHT}" version="1.1" xmlns="http://www.w3.org/2000/svg">',
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

def CreatePDF(Dataset, SvgPages, OutputFileName, JobName):
	CanvasPDF = canvas.Canvas(OutputFileName)
	Timestamp = str(datetime.datetime.now().replace(microsecond = 0))
	for PageNumber, Page in tqdm.tqdm(enumerate(SvgPages), total = len(SvgPages), desc = f'Convert pages to PDF', ascii = TQDM_STATUSBAR_ASCII):
		# Set font
		CanvasPDF.setFont(PDF_FONT_FAMILY, PDF_FONT_SIZE)
		# Convert SVG page
		ObjectPage = svg2rlg(io.StringIO(Page))
		# Captions
		CanvasPDF.drawString(PDF_LEFT_MARGIN * mm, (PDF_TOP_MARGIN - (PDF_LINE_SPACING * 1)) * mm, f'Name: {JobName}')
		CanvasPDF.drawString(PDF_LEFT_MARGIN * mm, (PDF_TOP_MARGIN - (PDF_LINE_SPACING * 2)) * mm, f'{Timestamp}, run ID: {Dataset["RunID"]["hex"]}, {Dataset["Length"]["int"]} blocks, page {PageNumber + 1} of {len(SvgPages)}')
		CanvasPDF.drawString(PDF_LEFT_MARGIN * mm, (PDF_TOP_MARGIN - (PDF_LINE_SPACING * 3)) * mm, f'SHA-256: {Dataset["Hash"]["hex"]}')
		CanvasPDF.drawString(PDF_LEFT_MARGIN * mm, (PDF_TOP_MARGIN - (PDF_LINE_SPACING * 4)) * mm, f'Pawpyrus {__version__}. Available at: https://github.com/regnveig/pawpyrus')
		# Draw pawprints
		renderPDF.draw(ObjectPage, CanvasPDF, PDF_LEFT_MARGIN * mm, - ((PDF_PAGE_HEIGHT - PDF_TOP_MARGIN) + (PDF_LINE_SPACING * 5)) * mm)
		# Newpage
		CanvasPDF.showPage()
	# Save pdf
	CanvasPDF.save()


# -----=====| ENCODE MAIN |=====-----

def EncodeMain(JobName, InputFileName, OutputFileName):
	logging.info(f'Pawpyrus {__version__} Encoder')
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
	Pages = CreatePixelSheets(Dataset['Codes'])
	# Draw SVG
	SvgPages = DrawSVG(Pages)
	# Draw PDF
	CreatePDF(Dataset, SvgPages, OutputFileName, JobName)
	logging.info(f'Job finished')


# -----=====| EXTRACTION |=====-----

def ExtractData(Line):
	Result = {
		'RunID': Base64ToHex(Line[: RUNID_BLOCK_SIZE]),
		'Index': Base64ToInt(Line[RUNID_BLOCK_SIZE : RUNID_BLOCK_SIZE + INDEX_BLOCK_SIZE]),
		'Content': Line[RUNID_BLOCK_SIZE + INDEX_BLOCK_SIZE :]
		}
	return Result

def ExtractMetadata(Content):
	Result = {
		'Length': Base64ToInt(Content[: INDEX_BLOCK_SIZE]),
		'Hash': hex(Base64ToInt(Content[INDEX_BLOCK_SIZE :]))[2:]
		}
	return Result

# -----=====| DETECT & DECODE |=====-----

def ReadPage(FileName):
	# Read and binarize image
	Picture = cv2.imread(FileName, cv2.IMREAD_GRAYSCALE)
	Threshold, Picture = cv2.threshold(Picture, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
	logging.info(f'Image binarized (threshold: {Threshold})')
	# Detect markers
	ArUcoDict = cv2.aruco.Dictionary_get(ARUCO_DICTIONARY)
	ArUcoParams = cv2.aruco.DetectorParameters_create()
	ArUcoParams.minMarkerPerimeterRate = MIN_MARKER_PERIMETER_RATE
	Markers = cv2.aruco.detectMarkers(Picture, ArUcoDict, parameters = ArUcoParams)
	# Check markers
	if Markers is None: raise RuntimeError('No markers were found')
	Markers = { int(Markers[1][item][0]): {'Coords': Markers[0][item][0]} for item in range(len(Markers[1])) }
	if tuple(sorted(Markers.keys())) != (0, 1, 2, 3): raise RuntimeError(f'Wrong markers or lack of markers')
	# Align grid
	MarkerLength = math.dist(Markers[0]['Coords'][0], Markers[0]['Coords'][1])
	for item in Markers: Markers[item]['Center'] = FindCenter(Markers[item]['Coords'])
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
		Fragment = Picture[round(min([y for x, y in Chunk])):round(max([y for x, y in Chunk])), round(min([x for x, y in Chunk])):round(max([x for x, y in Chunk]))]
		Chunks.append(Fragment)
	# Detect and decode
	Codes = list()
	for Chunk in tqdm.tqdm(Chunks, total = len(Chunks), desc = f'Detect QR codes', ascii = TQDM_STATUSBAR_ASCII):
		Code = decode(Chunk)
		if Code: Codes.append(Code[0].data.decode('ascii'))
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
	if len(Extracted) != Metadata['Length']: raise RuntimeError(f'Blocks number is not the same')
	# Check blocks
	MissingBlocks = list()
	for Index in range(1, Metadata['Length']):
		try:
			Extracted[Index]
		except KeyError:
			MissingBlocks.append(str(Index))
		if Extracted[Index]['RunID'] != Header['RunID']: raise RuntimeError(f'Some blocks are not of this header')
		Result.append(Extracted[Index]['Content'])
	if MissingBlocks: raise RuntimeError(f'Some blocks are missing: {"; ".join(MissingBlocks)}')
	# Decode base64
	ResultString = base64.b64decode(''.join(Result))
	# Check hashsum
	if hashlib.sha256(ResultString).hexdigest() != Metadata['Hash']: raise RuntimeError(f'Data damaged (hashes are not the same)')
	# Return
	return ResultString


# -----=====| DECODE MAIN |=====-----

def DecodeMain(InputFileNames, OutputFileName):
	logging.info(f'Pawpyrus {__version__} Decoder')
	logging.info(f'Input File(s): "{", ".join([os.path.realpath(item) for item in InputFileNames])}"')
	logging.info(f'Output File: "{os.path.realpath(OutputFileName)}"')
	Blocks = list()
	for FileName in InputFileNames:
		logging.info(f'Proccesing "{FileName}"')
		Blocks += ReadPage(FileName)
	Result = VerifyAndDecode(Blocks)
	with open(OutputFileName, 'wb') as Out: Out.write(Result)
	logging.info(f'Job finished')

# -----=====| MAIN |=====-----

if __name__ == '__main__':
	EncodeMain(InputFileName = '/mydocs/MyDocs/Cloud/Core/pawpyrus/tests/test_pubkey.gpg', JobName = 'Regnveig\'s Public Key on Paper', OutputFileName = 'tests/.test_pubkey.pdf' )
	#DecodeMain(['/mydocs/MyDocs/Cloud/Core/pawpyrus/tests/test_pawpyrus_scan_600dpi.JPG'], '/mydocs/MyDocs/Cloud/Core/pawpyrus/tests/.test_pawpyrus_decoded_data.asc')
