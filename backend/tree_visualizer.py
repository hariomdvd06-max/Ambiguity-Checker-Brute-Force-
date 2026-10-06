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
