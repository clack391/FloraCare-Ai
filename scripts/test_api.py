import httpx
import os

def test_api():
    url = "http://localhost:8000/diagnose"
    image_path = "test_images/sick_tomato.jpg"
    
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found")
        return

    print(f"Sending {image_path} to {url}...")
    
    files = {'file': open(image_path, 'rb')}
    data = {'location': 'London,UK', 'plant_name': 'API Test Tomato'}
    
    try:
        req = httpx.post(url, files=files, data=data, timeout=60.0)
        print(f"Status: {req.status_code}")
        if req.status_code == 200:
            print("Response JSON Keys:", req.json().keys())
            print("Diagnosis:", req.json().get('diagnosis'))
        else:
            print("Error:", req.text)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_api()
