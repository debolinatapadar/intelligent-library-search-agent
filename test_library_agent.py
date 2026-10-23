import unittest

from library_agent import LibraryGraph


class LibraryAgentTests(unittest.TestCase):
    def setUp(self):
        self.library = LibraryGraph()

    def test_bfs_finds_book(self):
        result = self.library.bfs_or_dfs("Clean Code", "BFS")
        self.assertTrue(result.found)
        self.assertEqual(result.target, "Technology-Shelf-A")
        self.assertEqual(result.path[0], "Entrance")

    def test_dfs_finds_book(self):
        result = self.library.bfs_or_dfs("The Alchemist", "DFS")
        self.assertTrue(result.found)
        self.assertEqual(result.target, "Fiction-Shelf-A")

    def test_astar_collects_multiple_books(self):
        result = self.library.plan_route(["Clean Code", "Sapiens", "The Alchemist"])
        self.assertTrue(result["found"])
        self.assertEqual(set(result["order"]), {"Clean Code", "Sapiens", "The Alchemist"})
        self.assertGreater(result["distance"], 0)

    def test_closed_section_blocks_book(self):
        self.library.set_disruptions(closed_sections=["Technology"])
        result = self.library.bfs_or_dfs("Clean Code", "BFS")
        self.assertFalse(result.found)

    def test_accessible_mode_avoids_limited_shelf(self):
        self.library.set_disruptions(accessible_only=True)
        result = self.library.bfs_or_dfs("Artificial Intelligence: A Modern Approach", "BFS")
        self.assertFalse(result.found)


if __name__ == "__main__":
    unittest.main()

