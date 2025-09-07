import io
import urllib.request
from term_image.image import AutoImage
from PIL import Image, ImageOps, ImageDraw

image1_url = "https://img.freepik.com/free-photo/woman-beach-with-her-baby-enjoying-sunset_52683-144131.jpg?size=626&ext=jpg"
image2_url = "https://cdn.fstoppers.com/styles/full/s3/media/2019/12/04/nando-jpeg-quality-050.jpg"

TUI_OPTION_BLOCK_HEIGHT = 100
TUI_NAME_BLOCK_HEIGHT = 50
TUI_BOTTOM_UI_HEIGHT = TUI_NAME_BLOCK_HEIGHT+TUI_OPTION_BLOCK_HEIGHT
# Retreive Images
try:
    with urllib.request.urlopen(image1_url) as response:
        request_response = response.read()
        image1_data = io.BytesIO(request_response)
    with urllib.request.urlopen(image2_url) as response:
        request_response = response.read()
        image2_data = io.BytesIO(request_response)

except Exception as e:
    print(f"Error: {e}")

image1 = Image.open(image1_data)
image1 = image1.resize((int(1920/2), int(1080/2)))
image2 = Image.open(image2_data)
image2 = image2.resize((int(1920/2), int(1080/2)))

# Draw Album Art
combined_height = image1.size[1] if image1.size[1] > image2.size[1] else image2.size[1]
combined_canvas = Image.new(
    "RGB", ((image1.size[0] + image2.size[0]), combined_height))
combined_canvas.paste(image1)
combined_canvas.paste(
    image2, (image1.size[0], 0))

# Draw bottom section
combined_canvas = ImageOps.expand(
    combined_canvas, border=(
        0, 0, 0, TUI_NAME_BLOCK_HEIGHT + TUI_OPTION_BLOCK_HEIGHT),
    fill=(255, 255, 0))

draw = ImageDraw.Draw(combined_canvas)

# Draw Title
draw.text((0, combined_canvas.size[1]-TUI_BOTTOM_UI_HEIGHT),
          "Title1", fill=(0, 0, 255))
draw.text((combined_canvas.size[0]/2,
           combined_canvas.size[1]-TUI_BOTTOM_UI_HEIGHT), "Title2",
          fill=(0, 0, 255))
w = draw.textlength("THIS IS OUR STATUS")
draw.line((combined_canvas.size[0]/2, 0, combined_canvas.size[0]/2,
           combined_canvas.size[1]-TUI_BOTTOM_UI_HEIGHT), 
          fill=128, width=5)
draw.text(((combined_canvas.size[0]/2)-(w/2), 0),
          "THIS IS OUR STATUS", fill=(0, 255, 255), align="center")

draw.line((0, (combined_canvas.size[1] - TUI_BOTTOM_UI_HEIGHT),
           combined_canvas.size[0],
           (combined_canvas.size[1] - TUI_BOTTOM_UI_HEIGHT)),
          fill=128, width=5)

# Draw Options
option_block_height = TUI_OPTION_BLOCK_HEIGHT
option_block_step = TUI_OPTION_BLOCK_HEIGHT/4

w = draw.textlength("Option 1")
draw.text(((combined_canvas.size[0]/2)-(w/2), combined_canvas.size[1]-option_block_height),
          "Option 1", fill=(0, 0, 0), align="center")
w = draw.textlength("Option 2")
option_block_height -= option_block_step
draw.text(((combined_canvas.size[0]/2)-(w/2), combined_canvas.size[1]-option_block_height),
          "Option 2", fill=(0, 0, 0), align="center")
w = draw.textlength("Option 3")
option_block_height -= option_block_step
draw.text(((combined_canvas.size[0]/2)-(w/2), combined_canvas.size[1]-option_block_height),
          "Option 3", fill=(0, 0, 0), align="center")
w = draw.textlength("Option 4")
option_block_height -= option_block_step
draw.text(((combined_canvas.size[0]/2)-(w/2), combined_canvas.size[1]-option_block_height),
          "Option 4", fill=(0, 0, 0), align="center")

term_image = AutoImage(combined_canvas)
print(term_image)
