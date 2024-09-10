import unittest
from json import dumps

from sophios.api.utils.converter import ict_to_clt

from tests.data.label_to_vector import label_to_vector_ict, label_to_vector_clt
from tests.data.ome_conversion import ome_conversion_ict, ome_conversion_clt
from tests.data.czi_extract import czi_extract_ict, czi_extract_clt

class IctToClt(unittest.TestCase):

    def test_label_to_vector_conversion(self):

        result = ict_to_clt(label_to_vector_ict)

        self.assertDictEqual(result, label_to_vector_clt)

    def test_ome_conversion(self):

        result = ict_to_clt(ome_conversion_ict)

        self.assertDictEqual(result, ome_conversion_clt)

    def test_czi_extract_conversion(self):

        result = ict_to_clt(czi_extract_ict)

        self.assertDictEqual(result, czi_extract_clt)
