import boto3
import csv
import io
from bs4 import BeautifulSoup
from datetime import datetime

def extract_data_from_html(html_content):
    """Extrae datos relevantes de un archivo HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    listings = soup.find_all("div", class_="listing-card__content")
    
    data = []
    for listing in listings:
        try:
            title = listing.find("span", class_="title").text.strip()
            
            price = listing.find("span", class_="price__actual")
            price = price.text.strip() if price else None

            location = listing.find("div", class_="listing-card__location__geo")
            location = location.text.strip() if location else None

            rooms = listing.find("p", {"data-test": "bedrooms"})
            rooms = rooms.text.strip() if rooms else None

            bathrooms = listing.find("p", {"data-test": "bathrooms"})
            bathrooms = bathrooms.text.strip() if bathrooms else None

            area = listing.find("p", {"data-test": "floor-area"})
            area = area.text.strip() if area else None

            pub_info = listing.find("p", class_="listing-card__information__bottom__published-date-and-agency")
            pub_date, agency = (pub_info.text.strip().split(" en ") if pub_info else (None, None))

            data.append({
                "Título": title,
                "Precio": price,
                "Ubicación": location,
                "Habitaciones": rooms,
                "Baños": bathrooms,
                "Área": area,
                "Fecha Publicación": pub_date,
                "Agencia": agency
            })
        except Exception as e:
            print("Error procesando un listado:", e)
    
    return data

def procesar_html(event, context):
    s3 = boto3.client('s3')
    bucket_name = "landingcasas"
    output_bucket = "casas-final-bg"
    
    # Obtener la carpeta con la fecha desde el evento
    record = event['Records'][0]
    s3_object_key = record['s3']['object']['key']
    
    # Extraer la carpeta (fecha) desde la clave del objeto
    folder_name = s3_object_key.split('/')[0]  # Se asume que el formato es "YYYY-MM-DD/archivo.html"
    
    output_filename = f"{folder_name}.csv"  # Usamos la misma fecha para el CSV
    
    all_data = []
    
    # Listar todos los archivos HTML en la carpeta correspondiente
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=f"{folder_name}/")
    if "Contents" not in response:
        print(f"No hay archivos en la carpeta {folder_name}")
        return
    
    for obj in response["Contents"]:
        html_file_key = obj["Key"]
        print(f"Procesando archivo: {html_file_key}")
        
        # Descargar el archivo HTML desde S3
        try:
            response = s3.get_object(Bucket=bucket_name, Key=html_file_key)
            html_content = response['Body'].read().decode('utf-8')
        except Exception as e:
            print(f"Error al descargar {html_file_key}: {e}")
            continue
        
        # Extraer datos del HTML
        extracted_data = extract_data_from_html(html_content)
        print(f"Datos extraídos: {len(extracted_data)} registros.")
        
        if extracted_data:
            all_data.extend(extracted_data)
    
    if not all_data:
        print("No hay datos para guardar.")
        return
    
    # Crear CSV en memoria
    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=all_data[0].keys())
    writer.writeheader()
    writer.writerows(all_data)
    
    # Subir CSV a S3
    try:
        s3.put_object(
            Bucket=output_bucket,
            Key=f"{folder_name}/{output_filename}",
            Body=csv_buffer.getvalue().encode('utf-8-sig'),
            ContentType='text/csv; charset=utf-8'
        )
        print(f"Archivo guardado en {output_bucket}/{folder_name}/{output_filename}")
    except Exception as e:
        print(f"Error al subir el archivo CSV: {e}")
