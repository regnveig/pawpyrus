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

class TestKittyPawprint(unittest.TestCase):

	def test_KittyPawprint_normal(self):
		Data = KittyPawprint(3, (102, 300), cv2.aruco.DICT_5X5_50, 7)
		Hash = HashJsonSerializable(Data)
		Expected = 'bf1d0a1cd490c8731073a6b3409743683c59b9ec3c659f6a057e7c6b'
		self.assertEqual(Hash, Expected)
