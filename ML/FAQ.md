# ML FAQ

## 1) What is edge probability?

In the random graph generator, **edge probability** is the chance that a directed edge from one vertex to another is added.

- If edge probability is `0.30`, then for each possible directed pair `(u, v)` with `u != v`, the generator adds edge `u -> v` with probability `30%`.
- Lower values create sparser graphs (fewer moves available).
- Higher values create denser graphs (more moves available).

In this project, this is controlled by:

- `--edge-prob-min`
- `--edge-prob-max`

For each generated game, a value is sampled in that range and used to build the graph.

## 2) Why is OVPP vertex count always 3?

In this codebase, pawns/colors are fixed to three colors: **Red, Blue, Green**.

OVPP means **One Vertex Per Pawn**, so with 3 pawn colors, OVPP requires exactly 3 vertices.

That is why the generator constrains OVPP to 3 vertices in the current implementation.

If you want OVPP with more than 3 vertices, you would need to generalize the simulator to support a dynamic number of pawn colors (instead of fixed `Red/Blue/Green`).
