import matplotlib.pyplot as plt

class TreeNode:
    def __init__(self, depth):
        self.depth = depth
        self.children = []
        self.x = 0.0
        self.y = float(depth)

def draw_nice_structure(nice_tuple, filename="nice_graph.png", horizontal_spacing=1.0):
    """
    Generates an image of a black graph depicting a 'nice' data structure.
    
    Args:
        nice_tuple (tuple): The recursive tuple structure.
        filename (str): The output filename for the generated image.
        horizontal_spacing (float): Distance between adjacent leaf nodes. 
    """
    if not isinstance(nice_tuple, tuple):
        raise ValueError("The input data structure must be a tuple.")

    # 1. Recursive function to parse the tuple into a tree
    def build_tree(tup, depth):
        node = TreeNode(depth)
        for item in tup:
            node.children.append(build_tree(item, depth + 1))
        return node

    roots = [build_tree(member, 0) for member in nice_tuple]

    if not roots:
        fig, ax = plt.subplots()
        ax.axis('off')
        plt.savefig(filename, transparent=True)
        plt.close()
        print(f"Empty structure. Saved blank transparent image to {filename}")
        return

    # 2. Assign horizontal (x) coordinates 
    x_counter = [0.0] 
    
    def assign_coords(node):
        if not node.children:
            node.x = x_counter[0]
            x_counter[0] += horizontal_spacing
        else:
            for child in node.children:
                assign_coords(child)
            node.x = sum(c.x for c in node.children) / len(node.children)

    for root in roots:
        assign_coords(root)

    # 3. Collect point and line data for plotting
    x_vals = []
    y_vals = []
    lines = []

    def collect_data(node):
        x_vals.append(node.x)
        y_vals.append(node.y)
        for child in node.children:
            lines.append(((node.x, child.x), (node.y, child.y)))
            collect_data(child)

    for root in roots:
        collect_data(root)

    # 4. Generate the Plot
    fig, ax = plt.subplots()
    
    for line_x, line_y in lines:
        ax.plot(line_x, line_y, color='black', zorder=1)
        
    ax.scatter(x_vals, y_vals, color='black', zorder=2)

    # -> THE FIX: Force Matplotlib to respect absolute visual scaling <-
    ax.set_aspect('equal')

    ax.axis('off')

    plt.savefig(filename, transparent=True, bbox_inches='tight')
    plt.close()
    
    print(f"Successfully generated graph and saved to {filename}")


# ==========================================
# Example Usage:
# ==========================================
if __name__ == "__main__":
    # sample_nice_data = (
    #     (), 
    #     ((), ()), 
    #     (((),), (), ((), ((),)))
    # )
    sample_nice_data = tuple(() for _ in range(6))
    
    # Now changing this will visibly squeeze or stretch the graph!
    draw_nice_structure(sample_nice_data, "my_nice_structure.png", horizontal_spacing=0.2)