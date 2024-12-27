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
    print(new)
    data = data.replace(og, new)

with open("READMEPY.md", "w") as new_file:
    new_file.write(data)
