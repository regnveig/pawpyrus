__author__ = 'Emil Viesná [regnveig]'
__version__ = 'v0.1'

from more_itertools import sliced
from qrcode import *
from reportlab.graphics import renderPDF
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg
import base64
import bitarray
import datetime
import hashlib
import io
import itertools
import logging
import os
import secrets
import tqdm


# -----=====| CONST |=====-----

logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)

CONST = {
	'ChunkSize': 108, # base64 symbols or x6 bits
	'ErrorCorrection': 1, # see qrcode spec
	'ColNum': 6,
	'RowNum': 8,
	'Spacing': 7, # pixels
	'StringSpacing': 5, # mm
	'PixelSize': 0.55, # mm
	'PageWidth': 210, # mm
	'PageHeight': 297, # mm
	'TopMargin': 45, # mm
	'LeftMargin': 27, # mm
	'Font': 'Courier-Bold',
	'FontSize': 10 # pt
	}

def Int2Binary(Int, Bits): return f'{Int:b}'.zfill(Bits)

def IntFromBase64(Int): return int.from_bytes(base64.b64decode(Int), 'big')

def CreatePawprint(Text, StartX, StartY, ChunkSize, ErrorCorrection):
	# Create output struct
	Result = {}
	# Wrap base64 data
	WrappedData = Text.ljust(ChunkSize, b'=')
	# Create QR
	QR = QRCode(error_correction = ErrorCorrection, border = 0)
	QR.add_data(WrappedData)
	QR.make(fit = False)
	# Get QR matrix
	Matrix = QR.get_matrix()
	Result['PawSize'] = len(Matrix)
	# Make pixel coordinates array
	Result['Pixels'] = [ (StartX + CoordX, StartY + CoordY) for CoordY, CoordX in itertools.product(range(Result['PawSize']), range(Result['PawSize'])) if Matrix[CoordY][CoordX] ]
	# Return
	return Result

def CreateDataset(RawData, ChunkSize):
	# Create output struct
	Result = { 'RunID': {}, 'Hash': {}, 'Length': {}, 'Codes': [] }
	# Run ID: unique program run identifier
	Result['RunID']['int'] = secrets.randbits(24)
	Result['RunID']['hex'] = hex(Result['RunID']['int'])[2:]
	Result['RunID']['bin'] = Int2Binary(Result['RunID']['int'], 24)
	# Compute data hash
	Hash = hashlib.sha256(RawData)
	Result['Hash']['hex'] = Hash.hexdigest()
	BitarrayObject = bitarray.bitarray()
	BitarrayObject.frombytes(Hash.digest())
	Result['Hash']['bin'] = BitarrayObject.to01()
	# Encode and chunk raw data
	Codes = list(sliced(base64.b64encode(RawData), ChunkSize))
	# Encode length
	Result['Length']['int'] = int(len(Codes) + 1)
	Result['Length']['bin'] = Int2Binary(Result['Length']['int'], 24)
	# Create Root Block (header)
	RootBlock = bitarray.bitarray(Result['Length']['bin'] + Result['Hash']['bin']).tobytes()
	Codes.insert(0, base64.b64encode(RootBlock))
	# Add block tag: Run ID + block number
	for Index, Content in tqdm.tqdm(enumerate(Codes), total = Result['Length']['int'], desc = 'Create blocks'):
		Index_Binary = Int2Binary(Index, 24)
		BlockTag = bitarray.bitarray(Result['RunID']['bin'] + Index_Binary).tobytes()
		Result['Codes'].append(base64.b64encode(BlockTag) + Content)
	# Return
	return Result

def CreatePages(Codes, ColNum, RowNum, Spacing, ChunkSize, ErrorCorrection):
	# Create output struct
	Result = { 'PawSize': None, 'CellSize': None, 'Pages': list() }
	# Chunk codes to rows and pages
	Chunks = list(sliced(list(sliced(Codes, ColNum)), RowNum))
	for EncodePage in Chunks:
		# Create page
		PawprintsPage = list()
		for Row, Col in tqdm.tqdm(itertools.product(range(RowNum), range(ColNum)), total = len(Codes), desc = 'Create pawprints'):
			try:
				# Create pawprint on the page
				# Align pawprints by ROOT BLOCK pawsize!
				StartX = 0 if Result['CellSize'] is None else Col * Result['CellSize']
				StartY = 0 if Result['CellSize'] is None else Row * Result['CellSize']
				Pawprint = CreatePawprint(EncodePage[Row][Col], StartX, StartY, ChunkSize, ErrorCorrection)
				if Result['PawSize'] is None:
					Result['PawSize'] = int(Pawprint['PawSize'])
					Result['CellSize'] = int(Pawprint['PawSize'] + Spacing)
				PawprintsPage += Pawprint['Pixels']
			except IndexError:
				# If there are no codes left
				break
		Result['Pages'].append(PawprintsPage)
	# Return
	return Result

def DrawPages(Pawprints, ColNum, RowNum, Spacing, PixelSize, PageWidth, PageHeight):
	SvgPages = list()
	for PageNumber, Page in enumerate(Pawprints['Pages']):
		# Draw page
		DrawingWidth = (ColNum * Pawprints['CellSize']) - Spacing
		DrawingHeight = (RowNum * Pawprints['CellSize']) + Spacing + 3
		SvgPage = [
			f'<svg width="{PageWidth}mm" height="{PageHeight}mm" viewBox="0 0 {PageWidth} {PageHeight}" version="1.1" xmlns="http://www.w3.org/2000/svg">',
			f'<path style="fill:#000000;stroke:none;fill-rule:evenodd" d="'
			]
		# Top Line
		Paths = [f'M 0,0 H {DrawingWidth * PixelSize} V {PixelSize} H 0 Z']
		# Add Pixels
		for PixelX, PixelY in tqdm.tqdm(Page, total = len(Page), desc = f'Draw pixels, page {PageNumber + 1} of {len(Pawprints["Pages"])}'):
			PixelAbsX = PixelX * PixelSize
			PixelAbsY = (Spacing + PixelY + 1) * PixelSize
			Paths.append(f'M {PixelAbsX},{PixelAbsY} H {PixelAbsX + PixelSize} V {PixelAbsY + PixelSize} H {PixelAbsX} Z')
		# Bottom Line
		Paths.append(f'M 0,{(DrawingHeight - 1) * PixelSize} H {DrawingWidth * PixelSize} V {DrawingHeight * PixelSize} H 0 Z')
		SvgPage.append(f' '.join(Paths))
		SvgPage.append(f'</svg>')
		# Merge svg
		SvgPages.append('\n'.join(SvgPage))
	return SvgPages

def ExtractBlock(Line):
	Result = {
		'RunID': hex(IntFromBase64(Line[:4]))[2:].zfill(6),
		'Index': IntFromBase64(Line[4:8]),
		'Chunk': str(Line[8:])
		}
	return Result

def ExtractMetadata(HeaderContent):
	Result = {
		'Length': IntFromBase64(HeaderContent[:4]),
		'Hash': base64.b64decode(HeaderContent[4:]).hex()
		}
	return Result

def VerifyAndDecode(QRBlocks):
	Result = []
	# Remove duplicates
	QRBlocksDedup = list(set(QRBlocks))
	# Extract blocks
	Extracted = [ExtractBlock(Line) for Line in QRBlocksDedup]
	# Sort blocks
	Extracted = sorted(Extracted, key = lambda x: x['Index'])
	RootBlock = Extracted[0]
	Metadata = ExtractMetadata(RootBlock['Chunk'])
	if RootBlock['Index'] != 0: raise RuntimeError(f'No root block in input data!')
	for Index in range(1, Metadata['Length']):
		if Extracted[Index]['RunID'] != RootBlock['RunID']: raise RuntimeError(f'Some blocks are not of this header')
		if Extracted[Index]['Index'] != Index: raise RuntimeError(f'Some blocks are missing (number {Index})')
		Result.append(Extracted[Index]['Chunk'])
	ResultString = base64.b64decode(''.join(Result))
	if hashlib.sha256(ResultString).hexdigest() != Metadata['Hash']: raise RuntimeError(f'Data damaged (hashes are not the same)')
	return ResultString

def Data2PDF(InputFileName, JobName, ColNum, RowNum, PixelSize, PageWidth, PageHeight, Spacing, ChunkSize, ErrorCorrection, OutputFileName, Font, FontSize, LeftMargin, TopMargin, StringSpacing):
	logging.info(f'Job Name: {JobName}')
	logging.info(f'Input File: "{os.path.realpath(InputFileName)}"')
	logging.info(f'Output File: "{os.path.realpath(OutputFileName)}"')
	RawData = open(InputFileName, 'rb').read()
	Dataset = CreateDataset(RawData, ChunkSize)
	logging.info(f'Run ID: {Dataset["RunID"]["hex"]}')
	logging.info(f'SHA-256: {Dataset["Hash"]["hex"]}')
	logging.info(f'Blocks: {Dataset["Length"]["int"]}')
	Pages = CreatePages(Dataset['Codes'], ColNum, RowNum, Spacing, ChunkSize, ErrorCorrection)
	SvgPages = DrawPages(Pages, ColNum, RowNum, Spacing, PixelSize, PageWidth, PageHeight)

	CanvasPDF = canvas.Canvas(OutputFileName)
	for PageNumber, Page in tqdm.tqdm(enumerate(SvgPages), total = len(SvgPages), desc = 'Convert pages to PDF'):
		CanvasPDF.setFont(Font, FontSize)
		ObjectPage = svg2rlg(io.StringIO(Page))
		CanvasPDF.drawString(LeftMargin * mm, (PageHeight - TopMargin + (StringSpacing * 3)) * mm, f'Name: {JobName}')
		CanvasPDF.drawString(LeftMargin * mm, (PageHeight - TopMargin + (StringSpacing * 2)) * mm, f'{str(datetime.datetime.now().replace(microsecond=0))}, run ID: {Dataset["RunID"]["hex"]}, {Dataset["Length"]["int"]} blocks, page {PageNumber + 1} of {len(SvgPages)}')
		CanvasPDF.drawString(LeftMargin * mm, (PageHeight - TopMargin + StringSpacing) * mm, f'SHA-256: {Dataset["Hash"]["hex"]}')
		CanvasPDF.drawString(LeftMargin * mm, (PageHeight - (TopMargin + StringSpacing + (((RowNum * Pages['CellSize']) + Spacing + 3) * PixelSize)) ) * mm, f'Pawpyrus {__version__}. Available at: https://github.com/regnveig/pawpyrus')
		renderPDF.draw(ObjectPage, CanvasPDF, LeftMargin * mm, (- TopMargin) * mm)
		CanvasPDF.showPage()
	CanvasPDF.save()
	logging.info(f'Job finished')

if __name__ == '__main__':
	Data2PDF(
		InputFileName = 'tests/test_pubkey.gpg',
		JobName = 'Regnveig\'s Public Key on Paper',
		OutputFileName = 'tests/test_pubkey.pdf',
		**CONST
		)
