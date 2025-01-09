import markdown

replacements = {
    "images/hexagonExploded.jpg": "https://github.com/HaRVI-Lab/haptic-harness/raw/main/images/hexagonExploded.jpg",
    "images/flatView.jpg": "https://github.com/HaRVI-Lab/haptic-harness/raw/main/images/flatView.jpg",
    "images/squareExploded.jpg": "https://github.com/HaRVI-Lab/haptic-harness/raw/main/images/squareExploded.jpg",
    "images/anatomyOfTile.jpg": "https://github.com/HaRVI-Lab/haptic-harness/raw/main/images/anatomyOfTile.jpg",
    "images/diagramOne.jpg": "https://github.com/HaRVI-Lab/haptic-harness/raw/main/images/diagramOne.jpg",
}

with open("README.md", "r") as og_file:
    data = og_file.read()

for og, new in replacements.items():
    data = data.replace(og, new)

with open("READMEPY.md", "w") as new_file:
    new_file.write(data)

final_data = ""
with open("README.md", "r") as og_file:
    data2 = og_file.readlines()
for line in data2:
    if any(image in line for image in replacements.keys()):
        continue
    final_data += line
# with open("haptic_harness_generator/instructions.html", "w") as instructions:
#     html_content = markdown.markdown(final_data)
#     instructions.write(html_content)
