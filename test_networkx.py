import networkx as nx
import matplotlib.pyplot as plt

#what we need
#node colouring so that it can be used
#dynamic graph generation
#directional graphs

#show the change of ownership of both player vertices while the game is played

g = nx.Graph()

g.add_edge("A", "B")
g.add_edge("B", "C")
g.add_edge("C", "D")
g.add_edge("A", "D")
g.add_edge("A", "E")

nx.draw(g, with_labels=True)
# plt.savefig("filename.png")
plt.show(block=False)
plt.pause(3)
plt.close() # we dont want to close it unless our next input is fed to the game.

# g.add_edge("E", "C")
nx.draw(g, with_labels=True)
plt.show()