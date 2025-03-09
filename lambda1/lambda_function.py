import boto3
import requests
from datetime import datetime

S3_BUCKET = "landingcasas"
URL_BASE = "https://casas.mitula.com.co/find?operationType=sell&propertyType=mitula_studio_apartment&geoId=mitula-CO-poblacion-0000014156&text=Bogot%C3%A1%2C++%28Cundinamarca%29&page="

def lambda_handler(event, context):
    s3 = boto3.client("s3")
    fecha = datetime.now().strftime("%Y-%m-%d")
    resultados = []

    for i in range(1, 11):
        url = f"{URL_BASE}{i}"
        
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})  # Simulamos navegador
            
            if response.status_code == 200:
                try:
                    s3.put_object(
                        Bucket=S3_BUCKET,
                        Key=f"{fecha}/pagina_{i}.html",
                        Body=response.text.encode("utf-8"),
                        ContentType="text/html"
                    )
                    resultados.append({"pagina": i, "status": "success"})
                
                except Exception as e:
                    print(f"Error al subir a S3 la página {i}: {e}")
                    resultados.append({"pagina": i, "status": "s3_error", "error": str(e)})
            
            else:
                print(f"Error {response.status_code} en la página {i}")
                resultados.append({"pagina": i, "status": "request_error", "error": response.status_code})

        except requests.RequestException as e:
            print(f"Error en la solicitud HTTP para la página {i}: {e}")
            resultados.append({"pagina": i, "status": "request_fail", "error": str(e)})

    return {"message": "Descarga completada", "detalles": resultados}
