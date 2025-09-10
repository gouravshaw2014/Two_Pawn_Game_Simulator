def add_edge(mat, i, j):
    # Add a directed edge from vertex i to vertex j
    mat[i][j] = 1  # Directed graph, only set one direction

def display_matrix(mat):
    # Display the adjacency matrix
    print("Adjacency Matrix for Directed Graph:")
    for row in mat:
        print(" ".join(map(str, row)))

def display_vertex_colors(colors, labels):
    # Display each vertex with its label and color
    print("\nVertex Information:")
    print("Index | Label | Color")
    print("-" * 25)
    for vertex in sorted(colors.keys()):
        print(f"{vertex:5} | {labels.get(vertex, 'No label'):7} | {colors.get(vertex, 'No color')}")

def get_color(colors, vertex):
    # Look up the color of a given vertex
    return colors.get(vertex, "No color")

def set_color(colors, vertex, new_color):
    # Change or set the color of a given vertex
    colors[vertex] = new_color if new_color.strip() else "No color"

def get_label(labels, vertex):
    # Look up the label of a given vertex
    return labels.get(vertex, "No label")

def set_label(labels, vertex, new_label):
    # Change or set the label of a given vertex
    labels[vertex] = new_label if new_label.strip() else "No label"

def create_directed_graph(V):
    """
    Create a directed graph with V vertices, with user input for labels, colors, and edges.
    
    Parameters:
    - V (int): Number of vertices.
    
    Returns:
    - mat (list of lists): Adjacency matrix.
    - colors (dict): Vertex-color mappings.
    - labels (dict): Vertex-label mappings.
    """
    # Initialize adjacency matrix
    mat = [[0] * V for _ in range(V)]
    
    # Initialize dictionaries for labels and colors
    labels = {}
    colors = {}
    
    # Prompt user for vertex labels
    print("Enter a label for each vertex (0 to", V-1, "):")
    for i in range(V):
        label = input(f"Label for vertex {i}: ").strip()
        labels[i] = label if label else f"Vertex{i}"
    
    # Prompt user for vertex colors
    print("\nEnter a color for each vertex (0 to", V-1, "):")
    for i in range(V):
        color = input(f"Color for vertex {i}: ").strip()
        colors[i] = color if color else "No color"
    
    # Prompt user for edges
    edges = []
    print("\nEnter edges as pairs of vertex indices (e.g., '0 1' for edge from 0 to 1).")
    print("Type 'done' or press Enter to finish.")
    while True:
        edge_input = input("Edge (from to): ").strip()
        if edge_input.lower() == "done" or not edge_input:
            break
        try:
            i, j = map(int, edge_input.split())
            if 0 <= i < V and 0 <= j < V:
                edges.append((i, j))
            else:
                print(f"Skipping invalid edge ({i}, {j}): indices out of bounds for V={V}")
        except ValueError:
            print(f"Skipping invalid input '{edge_input}': please enter two integers separated by a space or 'done'")
    
    # Add edges
    for i, j in edges:
        add_edge(mat, i, j)
    
    # Display results
    display_matrix(mat)
    display_vertex_colors(colors, labels)
    
    return mat, colors, labels