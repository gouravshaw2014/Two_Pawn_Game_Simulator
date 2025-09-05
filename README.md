# 🎮 Two Pawn Game Simulator

A **pawn-based reachability game simulator** inspired by *A Game of Pawns* (CONCUR 2023).  
The simulator models a pawn game with multiple variants of **pawn ownership** and **grabbing mechanisms**, allowing exploration of game dynamics, strategy outcomes, and player interactions.

---

## 📖 Game Definition

A pawn game with `d ∈ ℕ` pawns is defined as:


- **V = V₁ ∪ … ∪ V<sub>d</sub>** → Vertex sets partitioned among pawns.  
- **E** → Edges representing possible moves (turn-based).  
- **T** → Target vertices. Player 1 wins if they reach any vertex in `T`.  
- **M** → Mechanism for exchanging pawns.  

👉 Strategies are **memoryless** (sufficient for reachability objectives).  
👉 The pawns a player controls upon reaching `T` do **not** affect victory.  

---

## 🧩 Classes of Pawn Games

1. **OVPP (One Vertex Per Pawn)**  
   - One-to-one correspondence between pawns and vertices.  
   - `|V| = d` and each `Vj` is a singleton.  

2. **MVPP (Multiple Vertices Per Pawn)**  
   - Each pawn may own multiple vertices.  
   - `V₁, …, Vd` forms a **partition** of `V`.  

3. **OMVPP (Overlapping Multiple Vertices Per Pawn)**  
   - A vertex can be owned by **multiple pawns**.  
   - `Vi ∩ Vj ≠ ∅` for `i ≠ j`.  

---

## 🔄 Pawn Exchange Mechanisms (M)

The simulator supports multiple rules for **grabbing/giving pawns**:

1. **Optional Grabbing**  
   - After Player `i` moves, Player `−i` *may* grab one of Player `i`’s pawns.

2. **Always Grabbing**  
   - After Player `i` moves, Player `−i` *must* grab one pawn.  
   - Ensures Player `i` always controls at least one pawn initially.

3. **Always Grabbing or Giving**  
   - After Player `i` moves, Player `−i` must **either** grab one of Player `i`’s pawns **or** give them a pawn.

4. **k-Grabbing**  
   - Player 1 can grab from Player 2 up to `k` times per play.  
   - Configuration includes a counter `r` for remaining grabs.  

---

## ⚙️ Features

- Simulates **turn-based pawn games** with different grabbing modes.  
- Supports **OVPP, MVPP, OMVPP** ownership structures.  
- Tracks **configurations**:  
  - Position of pawns  
  - Ownership sets  
  - Remaining grabs (for k-grabbing)  
- Visual/CLI-based playthrough of moves.  

---
