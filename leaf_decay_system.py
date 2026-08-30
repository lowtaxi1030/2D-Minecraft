class LeafDecaySystem:

    def update(self): ...

    def is_natural_leaf(self, block_type: str):
        if "leav" not in block_type:
            return False
        if block_type.endswith("_natural"):
            return True
        return False

    def should_decay(self): ...
