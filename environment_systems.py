from grass_manager import GrassManager
from leaf_decay_system import LeafDecaySystem
from sapling_growth_manager import SaplingGrowthManager
from tree_generator import TreeGenerator

tree_generator = TreeGenerator()

class EnvironmentSystems:
    def __init__(self, chunks):
        self.grass = GrassManager(chunks)
        self.leaf_decay = LeafDecaySystem(chunks)
        self.sapling_growth = SaplingGrowthManager(chunks, tree_generator)

    def update(self):
        self.grass.update()
        decayed_leaves = self.leaf_decay.update()
        self.sapling_growth.update()
        return decayed_leaves
