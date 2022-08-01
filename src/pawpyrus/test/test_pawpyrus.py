import unittest
import json
from pawpyrus.pawpyrus import *

class Test_Base64ToInt(unittest.TestCase):

	def test_normal(self):
		self.assertEqual(Base64ToInt('Ab12'), 114038)

	def test_notbase64(self):
		self.assertRaises(ValueError, Base64ToInt, 'Ab1!')

	def test_notstring(self):
		self.assertRaises(TypeError, Base64ToInt, 0)
		self.assertRaises(TypeError, Base64ToInt, True)
		self.assertRaises(TypeError, Base64ToInt, None)
		self.assertRaises(TypeError, Base64ToInt, 6.2)
		self.assertRaises(TypeError, Base64ToInt, [4])
		self.assertRaises(TypeError, Base64ToInt, {12: 't'})
		self.assertRaises(TypeError, Base64ToInt, (1, 2))

class Test_IntToBinary(unittest.TestCase):

	def test_normal(self):
		self.assertEqual(IntToBinary(3081, 24), '000000000000110000001001')

	def test_negativeint(self):
		self.assertRaises(ValueError, IntToBinary, -1, 24)

	def test_notint(self):
		self.assertRaises(TypeError, IntToBinary, 'hello', 24)
		self.assertRaises(TypeError, IntToBinary, True, 24)
		self.assertRaises(TypeError, IntToBinary, None, 24)
		self.assertRaises(TypeError, IntToBinary, 6.2, 24)
		self.assertRaises(TypeError, IntToBinary, [4], 24)
		self.assertRaises(TypeError, IntToBinary, {12: 't'}, 24)
		self.assertRaises(TypeError, IntToBinary, (1, 2), 24)

	def test_bitsnotint(self):
		self.assertRaises(TypeError, IntToBinary, 0, 'hello')
		self.assertRaises(TypeError, IntToBinary, 0, True)
		self.assertRaises(TypeError, IntToBinary, 0, None)
		self.assertRaises(TypeError, IntToBinary, 0, 6.2)
		self.assertRaises(TypeError, IntToBinary, 0, [4])
		self.assertRaises(TypeError, IntToBinary, 0, {12: 't'})
		self.assertRaises(TypeError, IntToBinary, 0, (1, 2))

	def test_negativebits(self):
		self.assertRaises(ValueError, IntToBinary, 0, -1)

	def test_bitsoverflow(self):
		self.assertRaises(ValueError, IntToBinary, 1000, 2)

class Test_Base64ToHex(unittest.TestCase):

	def test_normal(self):
		self.assertEqual(Base64ToHex('Ab12'), '01bd76')

	def test_notbase64(self):
		self.assertRaises(ValueError, Base64ToHex, 'Ab1!')

	def test_notstring(self):
		self.assertRaises(TypeError, Base64ToInt, 0)
		self.assertRaises(TypeError, Base64ToInt, True)
		self.assertRaises(TypeError, Base64ToInt, None)
		self.assertRaises(TypeError, Base64ToInt, 6.2)
		self.assertRaises(TypeError, Base64ToInt, [4])
		self.assertRaises(TypeError, Base64ToInt, {12: 't'})
		self.assertRaises(TypeError, Base64ToInt, (1, 2))

class Test_FindCenter(unittest.TestCase):

	def test_normal(self):
		self.assertEqual(FindCenter(numpy.array([numpy.array([numpy.float32(0), numpy.float32(0)]), numpy.array([numpy.float32(3), numpy.float32(0)]), numpy.array([numpy.float32(3), numpy.float32(4)]), numpy.array([numpy.float32(0), numpy.float32(4)])])), (1.5, 2.0))

class Test_ExtractData(unittest.TestCase):

	def test_normal(self):
		self.assertEqual(json.dumps(ExtractData('PxkGAAAe0XvadZWXJgUAl7Ztew+qJMHY2+fOZ8il58HgfT4Yaknujv15tA9M8jgZbPRAQn8lVb9A/iX9JQGTNvFmxOMLmyFPKj3sYhJhD0xUu182v8Lm')), '{"RunID": "3f1906", "Index": 30, "Content": "0XvadZWXJgUAl7Ztew+qJMHY2+fOZ8il58HgfT4Yaknujv15tA9M8jgZbPRAQn8lVb9A/iX9JQGTNvFmxOMLmyFPKj3sYhJhD0xUu182v8Lm"}')

	def test_notbase64(self):
		self.assertRaises(ValueError, ExtractData, 'P-xkGAAAe0XvadZWXJgUAl7Ztew+qJMHY2+fOZ8il58HgfT4Yaknujv15tA9M8jgZbPRAQn8lVb9A/iX9JQGTNvFmxOMLmyFPKj3sYhJhD0xUu182v8Lm')

class Test_ExtractMetadata(unittest.TestCase):

	def test_normal(self):
		self.assertEqual(json.dumps(ExtractMetadata('AAI5xAM3jayqfDP1NqXh2IDfGU7z88IO0JbyEGtb4rU+QaA=============================================================')), '{"Length": 569, "Hash": "c403378dacaa7c33f536a5e1d880df194ef3f3c20ed096f2106b5be2b53e41a0"}')

class Test_TomcatPawprint(unittest.TestCase):

	def test_normal(self):
		self.assertEqual(json.dumps(TomcatPawprint(b'hello', (10, 2), ChunkSize = 5, RunIDBlockSize = 4, IndexBlockSize = 4, ErrorCorrection = 1)), '{"PawSize": 21, "Pixels": [[10, 2], [11, 2], [12, 2], [13, 2], [14, 2], [15, 2], [16, 2], [20, 2], [21, 2], [22, 2], [24, 2], [25, 2], [26, 2], [27, 2], [28, 2], [29, 2], [30, 2], [10, 3], [16, 3], [18, 3], [19, 3], [20, 3], [22, 3], [24, 3], [30, 3], [10, 4], [12, 4], [13, 4], [14, 4], [16, 4], [20, 4], [21, 4], [22, 4], [24, 4], [26, 4], [27, 4], [28, 4], [30, 4], [10, 5], [12, 5], [13, 5], [14, 5], [16, 5], [18, 5], [19, 5], [22, 5], [24, 5], [26, 5], [27, 5], [28, 5], [30, 5], [10, 6], [12, 6], [13, 6], [14, 6], [16, 6], [19, 6], [22, 6], [24, 6], [26, 6], [27, 6], [28, 6], [30, 6], [10, 7], [16, 7], [18, 7], [21, 7], [24, 7], [30, 7], [10, 8], [11, 8], [12, 8], [13, 8], [14, 8], [15, 8], [16, 8], [18, 8], [20, 8], [22, 8], [24, 8], [25, 8], [26, 8], [27, 8], [28, 8], [29, 8], [30, 8], [19, 9], [10, 10], [11, 10], [12, 10], [13, 10], [14, 10], [16, 10], [17, 10], [18, 10], [21, 10], [23, 10], [25, 10], [27, 10], [29, 10], [10, 11], [11, 11], [14, 11], [17, 11], [19, 11], [20, 11], [22, 11], [23, 11], [24, 11], [26, 11], [27, 11], [28, 11], [30, 11], [10, 12], [12, 12], [13, 12], [15, 12], [16, 12], [17, 12], [18, 12], [19, 12], [22, 12], [23, 12], [25, 12], [27, 12], [28, 12], [29, 12], [12, 13], [13, 13], [14, 13], [15, 13], [17, 13], [18, 13], [20, 13], [21, 13], [22, 13], [27, 13], [28, 13], [12, 14], [14, 14], [16, 14], [17, 14], [21, 14], [23, 14], [24, 14], [26, 14], [30, 14], [18, 15], [21, 15], [23, 15], [24, 15], [26, 15], [27, 15], [30, 15], [10, 16], [11, 16], [12, 16], [13, 16], [14, 16], [15, 16], [16, 16], [18, 16], [22, 16], [23, 16], [25, 16], [28, 16], [29, 16], [10, 17], [16, 17], [19, 17], [20, 17], [21, 17], [22, 17], [27, 17], [28, 17], [29, 17], [10, 18], [12, 18], [13, 18], [14, 18], [16, 18], [18, 18], [19, 18], [20, 18], [21, 18], [23, 18], [24, 18], [26, 18], [29, 18], [30, 18], [10, 19], [12, 19], [13, 19], [14, 19], [16, 19], [18, 19], [19, 19], [21, 19], [23, 19], [24, 19], [26, 19], [27, 19], [10, 20], [12, 20], [13, 20], [14, 20], [16, 20], [18, 20], [19, 20], [20, 20], [22, 20], [23, 20], [25, 20], [28, 20], [10, 21], [16, 21], [18, 21], [19, 21], [21, 21], [22, 21], [26, 21], [27, 21], [28, 21], [10, 22], [11, 22], [12, 22], [13, 22], [14, 22], [15, 22], [16, 22], [18, 22], [19, 22], [20, 22], [21, 22], [23, 22], [24, 22], [26, 22], [29, 22]]}')

class Test_KittyPawprint(unittest.TestCase):

	def test_normal(self):
		self.assertEqual(json.dumps(KittyPawprint(3, (18, 50), Dictionary = cv2.aruco.DICT_5X5_50, SpacingSize = 7)), '[[18, 50], [19, 50], [20, 50], [21, 50], [22, 50], [23, 50], [24, 50], [18, 51], [20, 51], [21, 51], [22, 51], [23, 51], [24, 51], [18, 52], [19, 52], [20, 52], [24, 52], [18, 53], [19, 53], [20, 53], [22, 53], [24, 53], [18, 54], [19, 54], [24, 54], [18, 55], [20, 55], [24, 55], [18, 56], [19, 56], [20, 56], [21, 56], [22, 56], [23, 56], [24, 56]]')

if __name__ == '__main__':
	unittest.main()
