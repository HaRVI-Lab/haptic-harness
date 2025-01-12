import matplotlib.pyplot as plt
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

# File name
name = "magnetRing.dxf"

# Read the DXF file
doc = ezdxf.readfile(name)
msp = doc.modelspace()

# Recommended: audit & repair DXF document before rendering
auditor = doc.audit()

# Create the Matplotlib figure and axes
fig = plt.figure()
ax = fig.add_axes([0, 0, 1, 1])

# Set up the rendering context
ctx = RenderContext(doc)

# Customize layer colors to ensure lines are visible
for layer in ctx.layers:
    ctx.layers[layer].color = "#000000"  # Set all layers to black lines

# Set up the Matplotlib backend
out = MatplotlibBackend(ax)

# Set the background color explicitly
ax.set_facecolor("white")

# Render the DXF content
Frontend(ctx, out).draw_layout(msp, finalize=True)

# Save the resulting figure with high resolution
output_file = f"{name[:-3]}png"
fig.savefig(output_file, dpi=300, facecolor="white")  # Ensure white background

print(f"Saved to {output_file}")
