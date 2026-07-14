"""
Convert simulator GameState + game configuration to ML model input features.
Handles encoding of game state into categorical and numeric features.
"""

from typing import Dict, List, Any, Set, Optional, Tuple
import json


class StateConverter:
    """
    Converts GameState + PawnGame config into DataFrame-compatible features.
    
    The ML model was trained on features like:
    - grabbing_rule (categorical)
    - ownership_mechanism (categorical)
    - phase (categorical)
    - chosen_action (categorical)
    - Position features (numeric)
    - Pawn count features (numeric)
    - Graph connectivity features (numeric)
    - etc.
    """

    def __init__(self):
        """Initialize with expected categorical values from training."""
        self.grabbing_rules = {
            'always-grabbing': 'always-grabbing',
            'always-grabbing-or-giving': 'always-grabbing-or-giving',
            'optional-grabbing': 'optional-grabbing',
            'k-grabbing': 'k-grabbing',
        }
        
        self.ownership_mechanisms = {
            'OVPP': 'OVPP',
            'MVPP': 'MVPP',
            'OMVPP': 'OMVPP',
        }
        
        self.phases = {
            'move': 'move',
            'grab': 'grab',
            'grab_or_give': 'grab_or_give',
            'k_grab': 'k_grab',
        }

    def state_to_features(
        self,
        game_engine: Any,
        game_state: Any,
        action: str,
        include_outcome: bool = False,
        outcome: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Convert game state + action to feature dictionary.
        
        Args:
            game_engine: PawnGame instance
            game_state: GameState instance
            action: The action being evaluated (e.g., "move A")
            include_outcome: Whether to include p1_wins label
            outcome: 1 if P1 wins, 0 if P2 wins (only used if include_outcome=True)
            
        Returns:
            Dictionary of features suitable for ML model input
        """
        features = {}
        
        # --- Game Configuration ---
        features['grabbing_rule'] = game_engine.grabbing_rule
        features['ownership_mechanism'] = self._infer_ownership_mechanism(game_engine)
        features['k_grab_limit'] = game_engine.k_grab_limit
        
        # --- Game State ---
        features['phase'] = game_state.phase
        features['current_player'] = game_state.current_player
        features['k_grabs_made'] = game_state.k_grabs_made
        
        # --- Position Features ---
        # Encode positions as vertex indices or symbolic
        features['p1_pos'] = game_state.p1_pos
        features['p2_pos'] = game_state.p2_pos
        
        # --- Pawn Count Features ---
        features['p1_pawn_count'] = len(game_state.p1_pawns)
        features['p2_pawn_count'] = len(game_state.p2_pawns)
        
        # --- Target and Graph Features ---
        features['target_vertex'] = game_engine.target_vertex
        features['graph_size'] = len(game_engine.graph)
        
        # --- Action Being Evaluated ---
        features['chosen_action'] = action
        
        # --- Graph Connectivity (if available) ---
        # Calculate average degree
        try:
            degrees = [len(neighbors) for neighbors in game_engine.graph.values()]
            features['avg_vertex_degree'] = sum(degrees) / len(degrees) if degrees else 0
            features['max_vertex_degree'] = max(degrees) if degrees else 0
            features['total_edges'] = sum(degrees) // 2  # Each edge counted twice
        except:
            features['avg_vertex_degree'] = 0
            features['max_vertex_degree'] = 0
            features['total_edges'] = 0
        
        # --- Distance Features (if path finding available) ---
        try:
            p1_dist = self._shortest_path_length(game_engine.graph, game_state.p1_pos, game_engine.target_vertex)
            p2_dist = self._shortest_path_length(game_engine.graph, game_state.p2_pos, game_engine.target_vertex)
            features['p1_distance_to_target'] = p1_dist if p1_dist >= 0 else game_engine.graph.get('graph_size', 0)
            features['p2_distance_to_target'] = p2_dist if p2_dist >= 0 else game_engine.graph.get('graph_size', 0)
        except:
            features['p1_distance_to_target'] = 0
            features['p2_distance_to_target'] = 0
        
        # --- Outcome (if training) ---
        if include_outcome and outcome is not None:
            features['p1_wins'] = outcome
        
        return features

    def _infer_ownership_mechanism(self, game_engine: Any) -> str:
        """
        Infer ownership mechanism (OVPP, MVPP, OMVPP) from ownership dict.
        
        Rules:
        - OVPP: Each vertex owned by at most 1 pawn, each pawn on 1 vertex
        - MVPP: Each vertex owned by 1 pawn, but pawns on multiple vertices
        - OMVPP: Some vertices owned by multiple pawns
        """
        if not hasattr(game_engine, 'ownership'):
            return 'OVPP'  # Default
        
        ownership = game_engine.ownership
        
        # Check for overlapping ownership (OMVPP)
        all_owned_vertices = set()
        for vertex, pawns in ownership.items():
            pawn_set = pawns if isinstance(pawns, set) else {pawns}
            if len(pawn_set) > 1:
                return 'OMVPP'
            all_owned_vertices.update(pawn_set)
        
        # Check if all vertices are owned (MVPP) or sparse (OVPP)
        unique_pawns = len(all_owned_vertices)
        if unique_pawns == len(ownership):
            return 'OVPP'
        else:
            return 'MVPP'

    def _shortest_path_length(self, graph: Dict[str, List[str]], start: str, end: str) -> int:
        """
        Calculate shortest path length using BFS.
        Returns -1 if no path exists.
        """
        if start == end:
            return 0
        if start not in graph:
            return -1
        
        queue = [(start, 0)]
        visited = {start}
        
        while queue:
            node, dist = queue.pop(0)
            for neighbor in graph.get(node, []):
                if neighbor == end:
                    return dist + 1
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))
        
        return -1

    def features_to_dict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert features dict to a format suitable for pandas DataFrame or sklearn.
        
        Ensures categorical features are strings and numeric features are numeric.
        """
        result = {}
        for key, value in features.items():
            result[key] = value
        return result

    def validate_features(self, features: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate that features match expected format for ML model.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_keys = [
            'grabbing_rule', 'ownership_mechanism', 'phase',
            'chosen_action', 'p1_pawn_count', 'p2_pawn_count'
        ]
        
        for key in required_keys:
            if key not in features:
                return False, f"Missing required feature: {key}"
        
        # Validate categorical values
        if features['grabbing_rule'] not in self.grabbing_rules:
            return False, f"Invalid grabbing_rule: {features['grabbing_rule']}"
        
        if features['ownership_mechanism'] not in self.ownership_mechanisms:
            return False, f"Invalid ownership_mechanism: {features['ownership_mechanism']}"
        
        if features['phase'] not in self.phases:
            return False, f"Invalid phase: {features['phase']}"
        
        return True, ""
