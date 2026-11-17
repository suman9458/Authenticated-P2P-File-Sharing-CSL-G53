"""
Generates a crisp, high-resolution SKIT Logo emblem for ReportLab PDF front page.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

fig, ax = plt.subplots(figsize=(4, 4), dpi=300)
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.5, 1.5)
ax.axis('off')

# Outer gear teeth
num_teeth = 28
radius_outer = 1.05
radius_inner = 0.85
crimson = '#B71C1C'
navy = '#1A237E'

for i in range(num_teeth):
    angle = (2 * np.pi / num_teeth) * i
    w = 0.07
    p1 = (radius_inner * np.cos(angle - w), radius_inner * np.sin(angle - w))
    p2 = (radius_outer * np.cos(angle - w*0.6), radius_outer * np.sin(angle - w*0.6))
    p3 = (radius_outer * np.cos(angle + w*0.6), radius_outer * np.sin(angle + w*0.6))
    p4 = (radius_inner * np.cos(angle + w), radius_inner * np.sin(angle + w))
    poly = plt.Polygon([p1, p2, p3, p4], color=crimson)
    ax.add_patch(poly)

# Crimson circular base
circle_base = plt.Circle((0, 0), radius_inner, color=crimson)
ax.add_patch(circle_base)

# White inner disc
circle_white = plt.Circle((0, 0), 0.72, color='white')
ax.add_patch(circle_white)

# Text SKIT
ax.text(0, 0.02, 'SKIT', color=crimson, fontsize=28, fontweight='heavy',
        ha='center', va='center', fontfamily='sans-serif')

# Ribbon banner at bottom
ribbon_box = patches.FancyBboxPatch((-1.05, -1.05), 2.1, 0.32,
                                    boxstyle="round,pad=0.03",
                                    facecolor=navy, edgecolor='#0D47A1', linewidth=1.5)
ax.add_patch(ribbon_box)

# Banner text
ax.text(0, -0.89, 'असतो मा सद्गमय', color='white', fontsize=12, fontweight='bold',
        ha='center', va='center')

plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
plt.savefig('report_assets/skit_logo.png', transparent=True, bbox_inches='tight', pad_inches=0.05)
plt.close()
print("[+] Crisp vector SKIT logo emblem generated.")
