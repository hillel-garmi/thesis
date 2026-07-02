import matplotlib.pyplot as plt
import math

def draw_symmetric_fractal(n, max_depth, highlight_callback=None):
    # 1. Set up the visualization
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)

    # Base colors (Standard material shades)
    color_palette = [
        '#FFA726',  # 1. Orange
        '#8E24AA',  # 2. Purple
        '#29B6F6',  # 3. Blue
        '#D32F2F',  # 4. Red
        '#4CAF50',  # 5. Green
        '#FFCA28',  # 6. Yellow
        '#EC407A'   # 7. Pink
    ]
    
    # Highlight palette: Vibrant "Accent/Neon" shades of the exact same colors.
    # These maintain deep color saturation but crank up the brightness significantly.
    highlight_palette = [
        '#FFAB40',  # 1. Vibrant Orange
        '#E040FB',  # 2. Vibrant Purple
        '#40C4FF',  # 3. Vibrant Cyan/Blue
        '#FF5252',  # 4. Vibrant Red
        '#69F0AE',  # 5. Vibrant Green
        '#FFD740',  # 6. Vibrant Yellow
        '#FF4081'   # 7. Vibrant Hot Pink
    ]

    # 2. Recursive function
    def draw_circle(x, y, R, current_depth, indices):
        # Determine base styling based on depth
        color_idx = (current_depth - 1) % len(color_palette)
        
        # Default styling
        facecolor = color_palette[color_idx]
        edgecolor = 'black'
        line_thickness = max(0.1, 1.5 / current_depth)

        # Highlight styling: Apply the vibrant shade and a crisp white border
        if highlight_callback is not None and highlight_callback(indices):
            facecolor = highlight_palette[color_idx]
            edgecolor = 'white'  
            line_thickness = max(1.0, 3.0 / current_depth)

        # Draw the circle
        circle = plt.Circle(
            (x, y), R,
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=line_thickness
        )
        ax.add_patch(circle)

        # Draw children if we haven't reached max_depth
        if current_depth < max_depth:
            sin_pi_n = math.sin(math.pi / n)
            r = R * (sin_pi_n / (1 + sin_pi_n))
            d = R - r 

            for i in range(n):
                angle = (i * 2 * math.pi / n) - (math.pi / 2)
                cx = x + d * math.cos(angle)
                cy = y + d * math.sin(angle)
                
                # Append the current child's index (i) to the path tuple
                child_indices = indices + (i,)
                
                # Recursively call the next level
                draw_circle(cx, cy, r, current_depth + 1, child_indices)

    # 3. Start drawing at Depth 1
    draw_circle(0.0, 0.0, 1.0, 1, ())

    # 4. Render and Save with a static filename
    # plt.title(f"Interactive Fractal Circles (n = {n}, depth = {max_depth})", fontsize=16, pad=20)
    
    filename = "Zp.png"
    plt.savefig(filename, dpi=300, transparent=True, bbox_inches='tight')
    print(f"Success! Image overwritten and saved as '{filename}'")

# --- EXAMPLES OF CALLBACK FUNCTIONS ---

def highlight_specific_target(indices):
    return indices == (0, 2)

def highlight_depth_three(indices):
    return len(indices) == 2 

def highlight_all_tops(indices):
    return len(indices) > 0 and indices[-1] == 0

# --- RUN THE CODE ---
draw_symmetric_fractal(6, 2)