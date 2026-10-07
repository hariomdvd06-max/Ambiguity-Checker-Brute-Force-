class ParseTreeNode:
    def __init__(self, symbol, production_rule=None, is_terminal=False):
        self.symbol = symbol
        self.children = []
        self.parent = None
        self.production_rule = production_rule
        self.is_terminal = is_terminal
        self.depth = 0
        self.position = 0

    def add_child(self, node):
        node.parent = self
        node.depth = self.depth + 1
        self.children.append(node)

    def remove_child(self, node):
        if node in self.children:
            self.children.remove(node)
            node.parent = None

    def get_all_children(self):
        return self.children

    def get_depth(self):
        return self.depth

    def get_leaf_nodes(self):
        if self.is_terminal or not self.children:
            return [self]
        leaves = []
        for child in self.children:
            leaves.extend(child.get_leaf_nodes())
        return leaves

    def get_path_to_root(self):
        path = []
        curr = self
        while curr:
            path.append(curr)
            curr = curr.parent
        return path

    def get_derivation_sequence(self):
        if self.production_rule:
            seq = [f"{self.symbol} -> {self.production_rule}"]
            for child in self.children:
                seq.extend(child.get_derivation_sequence())
            return seq
        return []

    def to_string(self):
        return self.symbol

    def to_dict(self):
        return {
            'symbol': self.symbol,
            'is_terminal': self.is_terminal,
            'rule': self.production_rule,
            'children': [child.to_dict() for child in self.children]
        }


class ParseTree:
    def __init__(self, root_node):
        self.root = root_node

    def get_root(self):
        return self.root

    def get_height(self):
        def _height(node):
            if not node.children:
                return 0
            return 1 + max(_height(c) for c in node.children)
        return _height(self.root)

    def get_leaf_count(self):
        return len(self.root.get_leaf_nodes())

    def get_node_count(self):
        def _count(node):
            return 1 + sum(_count(c) for c in node.children)
        return _count(self.root)

    def get_leftmost_derivation(self):
        steps = []
        current_frontier = [self.root]
        
        def format_frontier(frontier):
            return ' '.join(node.symbol for node in frontier if node.symbol != 'epsilon')
            
        steps.append(format_frontier(current_frontier))
        
        while True:
            # Find first non-terminal that has children
            first_nt_idx = -1
            for i, node in enumerate(current_frontier):
                if not node.is_terminal and node.children:
                    first_nt_idx = i
                    break
                    
            if first_nt_idx == -1:
                break
                
            # Replace it with its children
            node_to_expand = current_frontier[first_nt_idx]
            current_frontier = current_frontier[:first_nt_idx] + node_to_expand.children + current_frontier[first_nt_idx+1:]
            steps.append(format_frontier(current_frontier))
            
        return steps

    def get_all_derivations(self):
        return self.root.get_derivation_sequence()

    def is_valid_tree(self):
        return self.root is not None

    def get_yield(self):
        return "".join([node.symbol for node in self.root.get_leaf_nodes()])

    def to_ascii_art(self):
        # Implementation via TreeVisualizer is better
        return f"ParseTree(root={self.root.symbol})"

    def to_dict(self):
        return self.root.to_dict()

    def compare_with(self, other_tree):
        return self.get_structural_hash() == other_tree.get_structural_hash()

    def get_structural_hash(self):
        import hashlib
        def _hash_node(node):
            structure = f"{node.symbol}:" + ",".join([_hash_node(c) for c in node.children])
            return hashlib.md5(structure.encode()).hexdigest()
        return _hash_node(self.root)

    def find_ambiguous_nodes(self):
        return []

    def get_production_sequence(self):
        return self.get_all_derivations()

    def visualize(self):
        pass


class TreeVisualizer:
    def __init__(self, tree):
        self.tree = tree

    def render_ascii_tree(self):
        lines = []
        def _traverse(node, prefix="", is_last=True):
            connector = "└── " if is_last else "├── "
            rule_str = f" [{node.production_rule}]" if node.production_rule else ""
            lines.append(f"{prefix}{connector}{node.symbol}{rule_str}")
            
            new_prefix = prefix + ("    " if is_last else "│   ")
            for i, child in enumerate(node.children):
                _traverse(child, new_prefix, i == len(node.children) - 1)
                
        if self.tree and self.tree.root:
            lines.append(self.tree.root.symbol)
            for i, child in enumerate(self.tree.root.children):
                _traverse(child, "", i == len(self.tree.root.children) - 1)
                
        return "\n".join(lines)

    def render_indented_tree(self):
        return self.render_ascii_tree()

    def render_with_production_rules(self):
        return self.render_ascii_tree()

    def render_with_derivation_steps(self):
        return "\n".join(self.tree.get_all_derivations())

    def render_comparison(self, tree2):
        return f"Tree 1 Yield: {self.tree.get_yield()}\nTree 2 Yield: {tree2.get_yield()}"
        
    def generate_tikz(self):
        def _node_to_tikz(node, indent=2):
            ind = " " * indent
            res = f"{ind}node {{{node.symbol}}}"
            if not node.children:
                return res
            for child in node.children:
                res += f"\n{ind}  child {{\n{_node_to_tikz(child, indent + 4)}\n{ind}  }}"
            return res
            
        if not self.tree or not self.tree.root:
            return ""
            
        tikz_str = "\\begin{tikzpicture}[level distance=1.5cm,\n"
        tikz_str += "  level 1/.style={sibling distance=3cm},\n"
        tikz_str += "  level 2/.style={sibling distance=1.5cm},\n"
        tikz_str += "  every node/.style={circle, draw, minimum size=0.6cm}]\n"
        tikz_str += f"  \\{_node_to_tikz(self.tree.root, 2).strip()};\n"
        tikz_str += "\\end{tikzpicture}"
        return tikz_str
        
    def generate_svg(self):
        leaf_counter = [0]
        
        def _traverse(node, depth):
            node.y = depth * 80 + 40
            if not node.children:
                node.x = leaf_counter[0] * 60 + 40
                leaf_counter[0] += 1
            else:
                for c in node.children:
                    _traverse(c, depth + 1)
                node.x = (node.children[0].x + node.children[-1].x) / 2
                
        if not self.tree or not self.tree.root:
            return "<svg></svg>"
            
        _traverse(self.tree.root, 0)
        
        max_x = max(leaf_counter[0] * 60 + 80, 200)
        max_y = (self.tree.get_height() + 1) * 80 + 40
        
        svg_lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{max_x}" height="{max_y}" viewBox="0 0 {max_x} {max_y}">']
        svg_lines.append('<style> text { font-family: monospace; font-size: 14px; text-anchor: middle; fill: #e2e8f0; } line { stroke: #475569; stroke-width: 2; } circle { fill: #0f172a; stroke: #3b82f6; stroke-width: 2; } </style>')
        
        def _draw(node):
            for c in node.children:
                svg_lines.append(f'<line x1="{node.x}" y1="{node.y+15}" x2="{c.x}" y2="{c.y-15}"/>')
                _draw(c)
            svg_lines.append(f'<circle cx="{node.x}" cy="{node.y}" r="15"/>')
            svg_lines.append(f'<text x="{node.x}" y="{node.y+5}">{node.symbol}</text>')
            
        _draw(self.tree.root)
        svg_lines.append('</svg>')
        return "\n".join(svg_lines)

    def colorize_output(self):
        pass

    def export_as_svg(self):
        pass

    def export_as_json(self):
        import json
        return json.dumps(self.tree.to_dict(), indent=2)

    def generate_derivation_sequence(self):
        return self.tree.get_all_derivations()

    def highlight_differences(self, tree2):
        pass

    def add_node_numbers(self):
        pass
