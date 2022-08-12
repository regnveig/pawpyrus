from pawpyrus import *
import json
import unittest

def HashJsonSerializable(Object): return hashlib.sha224(json.dumps(Object).encode('ascii')).hexdigest()

class TestExtractData(unittest.TestCase):

	def test_ExtractData_normal(self):
		Data = ExtractData('PxkGAAB1/Guy/5etlb0oIas6eoaMchEvv8D+aVyFo3agEowsX2VVjUMoTIEfWqsp/HBKboEV7awGCrO3X9eerwa/cR6Psq4vbEXJZWePEh8cHY8gEiLG', 4, 4)
		Hash = HashJsonSerializable(Data)
		Expected = '45b80a6144ad22bae0fd3f867b9c6941b7c5f1e9c3da22b80c5220f7'
		self.assertEqual(Hash, Expected)

class TestTomcatPawprint(unittest.TestCase):

	def test_TomcatPawprint_normal(self):
		String = b'PxkGAAB1/Guy/5etlb0oIas6eoaMchEvv8D+aVyFo3agEowsX2VVjUMoTIEfWqsp/HBKboEV7awGCrO3X9eerwa/cR6Psq4vbEXJZWePEh8cHY8gEiLG'
		Data = TomcatPawprint(String, (18, 34), PawSize = None, ChunkSize = 108, RunIDBlockSize = 4, IndexBlockSize = 4, ErrorCorrection = 1)
		Hash = HashJsonSerializable(Data)
		Expected = 'e4345c696af5389eed656427a2d6ee57916a4cdaa6f3ef5ba8c0dbb1'
		self.assertEqual(Hash, Expected)

class TestKittyPawprint(unittest.TestCase):

	def test_KittyPawprint_normal(self):
		Data = KittyPawprint(3, (102, 300), cv2.aruco.DICT_5X5_50, 7)
		Hash = HashJsonSerializable(Data)
		Expected = 'bf1d0a1cd490c8731073a6b3409743683c59b9ec3c659f6a057e7c6b'
		self.assertEqual(Hash, Expected)
