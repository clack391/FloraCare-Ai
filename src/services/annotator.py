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
                    
                    # Robustness: Ensure x0 < x1 and y0 < y1
                    real_left = min(left, right)
                    real_right = max(left, right)
                    real_top = min(top, bottom)
                    real_bottom = max(top, bottom)
                    
                    # Clamp to image bounds
                    real_left = max(0, min(width, real_left))
                    real_right = max(0, min(width, real_right))
                    real_top = max(0, min(height, real_top))
                    real_bottom = max(0, min(height, real_bottom))

                    # Skip invalid boxes (e.g. 0 width/height)
                    if real_right <= real_left or real_bottom <= real_top:
                        continue
                    
                    # Draw Box
                    draw.rectangle([real_left, real_top, real_right, real_bottom], outline="red", width=3)
                    
                    # Draw Label (Optional background for readability)
                    # draw.text((left, top - 10), obj.name, fill="red") # simple text
                    
            # Return bytes
            out_buffer = io.BytesIO()
            image.save(out_buffer, format=image.format or "JPEG")
            return out_buffer.getvalue()
            
        except Exception as e:
            print(f"Annotation failed: {e}")
            return image_bytes # Fallback to original
