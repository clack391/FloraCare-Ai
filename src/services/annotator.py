from PIL import Image, ImageDraw, ImageFont
import io
from typing import List, Optional
from src.models.schemas import PlantImageAnalysis

class Annotator:
    @staticmethod
    def draw_boxes(image_bytes: bytes, analysis: PlantImageAnalysis) -> bytes:
        """
        Draws bounding boxes on the image for each detected object.
        Returns the annotated image as bytes.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            draw = ImageDraw.Draw(image)
            width, height = image.size
            
            # Draw each box
            for obj in analysis.detected_objects:
                if obj.box_2d:
                    # Normalized [ymin, xmin, ymax, xmax] 0-1000
                    ymin, xmin, ymax, xmax = obj.box_2d
                    
                    # Convert to pixels
                    left = (xmin / 1000) * width
                    top = (ymin / 1000) * height
                    right = (xmax / 1000) * width
                    bottom = (ymax / 1000) * height
                    
                    # Draw Box
                    draw.rectangle([left, top, right, bottom], outline="red", width=3)
                    
                    # Draw Label (Optional background for readability)
                    # draw.text((left, top - 10), obj.name, fill="red") # simple text
                    
            # Return bytes
            out_buffer = io.BytesIO()
            image.save(out_buffer, format=image.format or "JPEG")
            return out_buffer.getvalue()
            
        except Exception as e:
            print(f"Annotation failed: {e}")
            return image_bytes # Fallback to original
