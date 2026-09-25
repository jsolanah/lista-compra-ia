import tempfile
import unittest
from pathlib import Path

import src.persistence.list_cache as list_cache


class ListCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "listas.db"
        self.supabase_url = list_cache.SUPABASE_URL
        self.supabase_key = list_cache.SUPABASE_KEY
        list_cache.DB_PATH = self.database_path
        list_cache.SUPABASE_URL = ""
        list_cache.SUPABASE_KEY = ""

    def tearDown(self):
        list_cache.SUPABASE_URL = self.supabase_url
        list_cache.SUPABASE_KEY = self.supabase_key
        self.temp_dir.cleanup()

    def test_same_pdf_uses_same_key(self):
        self.assertEqual(
            list_cache.construir_clave_dieta(b"dieta"),
            list_cache.construir_clave_dieta(b"dieta"),
        )
        self.assertNotEqual(
            list_cache.construir_clave_dieta(b"dieta A"),
            list_cache.construir_clave_dieta(b"dieta B"),
        )

    def test_shared_pdf_is_associated_with_each_user(self):
        clave = list_cache.construir_clave_dieta(b"pdf compartido")
        list_cache.guardar_lista("usuario-a", clave, {"persona": "A"}, "dieta.pdf")
        datos_reutilizados = list_cache.obtener_lista("usuario-b", clave)
        list_cache.guardar_lista("usuario-b", clave, datos_reutilizados, "dieta.pdf")

        self.assertEqual(list_cache.obtener_lista("usuario-a", clave), {"persona": "A"})
        self.assertEqual(list_cache.obtener_lista("usuario-b", clave), {"persona": "A"})
        self.assertEqual(len(list_cache.obtener_dietas_usuario("usuario-b")), 1)

    def test_history_contains_saved_diet(self):
        clave = list_cache.construir_clave_dieta(b"pdf historial")
        datos = {"categorias": [], "plan_semanal": []}
        list_cache.guardar_lista("usuario-a", clave, datos, "dieta.pdf")

        historial = list_cache.obtener_dietas_usuario("usuario-a")

        self.assertEqual(len(historial), 1)
        self.assertEqual(historial[0]["nombre_archivo"], "dieta.pdf")
        self.assertEqual(historial[0]["datos"], datos)


if __name__ == "__main__":
    unittest.main()
