import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Agregar el directorio raíz de lambda1 al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lambda_function import lambda_handler  # Ahora sí debería encontrarlo


class TestLambdaScraping(unittest.TestCase):

    @patch("boto3.client")  # Mock para evitar conexión real a AWS
    @patch("requests.get")  # Mock para evitar llamadas reales a la web
    def test_lambda_handler_success(self, mock_requests_get, mock_boto3_client):
        """Prueba que el Lambda maneja correctamente 10 descargas exitosas y las guarda en S3"""

        # Simula una respuesta de requests.get con código 200 y HTML falso
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>Mock HTML</html>"
        mock_requests_get.return_value = mock_response

        # Simula el cliente S3
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        # Ejecuta la función lambda
        respuesta = lambda_handler({}, {})

        # Verifica que se hicieron 10 llamadas a requests.get
        self.assertEqual(mock_requests_get.call_count, 10)

        # Verifica que S3 recibió 10 archivos
        self.assertEqual(mock_s3.put_object.call_count, 10)

        # Verifica que la respuesta del Lambda es correcta
        self.assertEqual(respuesta["message"], "Descarga completada")

    @patch("boto3.client")
    @patch("requests.get")
    def test_lambda_handler_requests_fail(self, mock_requests_get, mock_boto3_client):
        """Prueba que la función maneja fallos en requests.get correctamente"""

        # Simula un fallo en requests.get (por ejemplo, error 500 en la web)
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_requests_get.return_value = mock_response

        # Simula el cliente S3
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        # Ejecuta la función lambda
        respuesta = lambda_handler({}, {})

        # Verifica que requests.get fue llamado 10 veces, pero que S3 no recibió archivos
        self.assertEqual(mock_requests_get.call_count, 10)
        self.assertEqual(mock_s3.put_object.call_count, 0)

    @patch("boto3.client")
    @patch("requests.get")
    def test_lambda_handler_s3_fail(self, mock_requests_get, mock_boto3_client):
        """Prueba que el Lambda maneja errores de S3 sin fallar completamente"""

        # Simula una respuesta exitosa de requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>Mock HTML</html>"
        mock_requests_get.return_value = mock_response

        # Simula un fallo en S3 (por ejemplo, error al guardar el archivo)
        mock_s3 = MagicMock()
        mock_s3.put_object.side_effect = Exception("Error en S3")
        mock_boto3_client.return_value = mock_s3

        # Ejecuta la función lambda
        respuesta = lambda_handler({}, {})

        # Verifica que requests.get se llamó 10 veces
        self.assertEqual(mock_requests_get.call_count, 10)

        # Verifica que S3 intentó guardar 10 archivos (aunque falló)
        self.assertEqual(mock_s3.put_object.call_count, 10)


if __name__ == "__main__":
    unittest.main()
