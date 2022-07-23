import base64
import hashlib
import logging
import cv2

def IntFromBase64(Int): return int.from_bytes(base64.b64decode(Int), 'big')

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
