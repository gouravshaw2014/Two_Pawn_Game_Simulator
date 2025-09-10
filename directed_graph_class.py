class Vertex:
    def __init__(self, index, color="No color", label=None):
        self.index = index  # Vertex index (e.g., 0, 1, 2)
        self.color = color  # Vertex color
        self.label = label if label and label.strip() else f"Vertex{index}"  # Vertex label

    def get_color(self):
        # Return the color of the vertex
        return self.color

    def set_color(self, new_color):
        # Set or update the color of the vertex
        self.color = new_color if new_color.strip() else "No color"

    def get_label(self):
        # Return the label of the vertex
        return self.label

    def set_label(self, new_label):
        # Set or update the label of the vertex
        self.label = new_label if new_label.strip() else f"Vertex{self.index}"

def add_edge(mat, i, j):
    # Add a directed edge from vertex i to vertex j
    mat[i][j] = 1  # Directed graph, only set one direction

def display_matrix(mat):
    # Display the adjacency matrix
    print("Adjacency Matrix for Directed Graph:")
    for row in mat:
        print(" ".join(map(str, row)))

def display_vertex_colors(vertices):
    # Display each vertex with its label and color
    print("\nVertex Information:")
    print("Index | Label | Color")
    print("-" * 25)
    for vertex in vertices:
        print(f"{vertex.index:5} | {vertex.label:7} | {vertex.color}")

def create_directed_graph(V):
    """
    Create a directed graph with V vertices, with user input for labels, colors, and edges.
    
    Parameters:
    - V (int): Number of vertices.
    
    Returns:
    - mat (list of lists): Adjacency matrix.
    - vertices (list): List of Vertex objects.
    """
    # Initialize adjacency matrix
    mat = [[0] * V for _ in range(V)]
    
    # Initialize vertices list with user input for labels
    vertices = []
    print("Enter a label for each vertex (0 to", V-1, "):")
    for i in range(V):
        label = input(f"Label for vertex {i}: ").strip()
        vertices.append(Vertex(i, label=label))
    
    # Prompt user for vertex colors
    print("\nEnter a color for each vertex (0 to", V-1, "):")
    for i in range(V):
        color = input(f"Color for vertex {i}: ").strip()
        vertices[i].set_color(color)
    
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
    display_vertex_colors(vertices)
    
    return mat, vertices