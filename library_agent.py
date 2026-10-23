"""Core search and route-planning logic for the Intelligent Library Agent.

The module intentionally uses only Python's standard library so that it can be
uploaded to GitHub and run without installing third-party packages.
"""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from collections import deque
from math import hypot
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class Book:
    title: str
    shelf: str
    priority: int = 3
    collection_time: float = 2.0
    available: bool = True


@dataclass
class SearchResult:
    found: bool
    target: str
    path: List[str]
    cost: float
    open_list: List[str]
    closed_list: List[str]
    message: str


class LibraryGraph:
    """Graph model of library sections, aisles and shelves."""

    def __init__(self) -> None:
        self.nodes: Dict[str, Tuple[float, float]] = {
            "Entrance": (60, 260),
            "Fiction": (210, 100),
            "Science": (210, 260),
            "History": (210, 420),
            "Technology": (430, 100),
            "Arts": (430, 420),
            "Fiction-Shelf-A": (350, 60),
            "Fiction-Shelf-B": (350, 140),
            "Science-Shelf-A": (350, 220),
            "Science-Shelf-B": (350, 300),
            "History-Shelf-A": (350, 380),
            "History-Shelf-B": (350, 460),
            "Technology-Shelf-A": (570, 60),
            "Technology-Shelf-B": (570, 140),
            "Arts-Shelf-A": (570, 380),
            "Arts-Shelf-B": (570, 460),
        }
        self.sections = {"Fiction", "Science", "History", "Technology", "Arts"}
        self.adjacency: Dict[str, List[Tuple[str, float]]] = {
            "Entrance": [("Fiction", 4), ("Science", 3), ("History", 4)],
            "Fiction": [("Entrance", 4), ("Fiction-Shelf-A", 2), ("Fiction-Shelf-B", 2), ("Technology", 4)],
            "Science": [("Entrance", 3), ("Science-Shelf-A", 2), ("Science-Shelf-B", 2), ("Technology", 4), ("History", 3)],
            "History": [("Entrance", 4), ("History-Shelf-A", 2), ("History-Shelf-B", 2), ("Arts", 4), ("Science", 3)],
            "Technology": [("Fiction", 4), ("Science", 4), ("Technology-Shelf-A", 2), ("Technology-Shelf-B", 2), ("Arts", 4)],
            "Arts": [("History", 4), ("Technology", 4), ("Arts-Shelf-A", 2), ("Arts-Shelf-B", 2)],
            "Fiction-Shelf-A": [("Fiction", 2)],
            "Fiction-Shelf-B": [("Fiction", 2)],
            "Science-Shelf-A": [("Science", 2)],
            "Science-Shelf-B": [("Science", 2)],
            "History-Shelf-A": [("History", 2)],
            "History-Shelf-B": [("History", 2)],
            "Technology-Shelf-A": [("Technology", 2)],
            "Technology-Shelf-B": [("Technology", 2)],
            "Arts-Shelf-A": [("Arts", 2)],
            "Arts-Shelf-B": [("Arts", 2)],
        }
        self.books: Dict[str, Book] = {
            "The Alchemist": Book("The Alchemist", "Fiction-Shelf-A", 4),
            "Pride and Prejudice": Book("Pride and Prejudice", "Fiction-Shelf-B", 3),
            "A Brief History of Time": Book("A Brief History of Time", "Science-Shelf-A", 5),
            "Clean Code": Book("Clean Code", "Technology-Shelf-A", 5),
            "Artificial Intelligence: A Modern Approach": Book("Artificial Intelligence: A Modern Approach", "Technology-Shelf-B", 5, 3),
            "Sapiens": Book("Sapiens", "History-Shelf-A", 4),
            "India After Gandhi": Book("India After Gandhi", "History-Shelf-B", 3),
            "The Story of Art": Book("The Story of Art", "Arts-Shelf-A", 2),
            "The Design of Everyday Things": Book("The Design of Everyday Things", "Arts-Shelf-B", 4),
        }
        self.closed_sections: Set[str] = set()
        self.unavailable_books: Set[str] = set()
        self.crowded_aisles: Set[str] = set()
        self.restricted_shelves: Set[str] = set()
        self.accessible_only = False
        # These shelves represent locations that require stairs or narrow access.
        # They remain available normally, but are avoided when the user requests
        # an accessibility-first route.
        self.accessibility_limited_shelves = {"Technology-Shelf-B", "Arts-Shelf-B"}
        self.priority_weight = 1.0
        self.crowd_penalty = 2.0

    def reset_disruptions(self) -> None:
        self.closed_sections.clear()
        self.unavailable_books.clear()
        self.crowded_aisles.clear()
        self.restricted_shelves.clear()

    def set_disruptions(
        self,
        closed_sections: Iterable[str] = (),
        unavailable_books: Iterable[str] = (),
        crowded_aisles: Iterable[str] = (),
        restricted_shelves: Iterable[str] = (),
        accessible_only: bool = False,
    ) -> None:
        self.closed_sections = set(closed_sections)
        self.unavailable_books = set(unavailable_books)
        self.crowded_aisles = set(crowded_aisles)
        self.restricted_shelves = set(restricted_shelves)
        self.accessible_only = accessible_only

    def section_for(self, node: str) -> Optional[str]:
        if node in self.sections:
            return node
        for section in self.sections:
            if node.startswith(section + "-"):
                return section
        return None

    def is_blocked(self, node: str) -> bool:
        section = self.section_for(node)
        if section in self.closed_sections:
            return True
        if node in self.restricted_shelves:
            return True
        if self.accessible_only and node in self.accessibility_limited_shelves:
            return True
        return False

    def shelf_is_accessible(self, shelf: str) -> bool:
        return not self.is_blocked(shelf)

    def edge_cost(self, source: str, target: str, distance: float) -> float:
        penalty = self.crowd_penalty if source in self.crowded_aisles or target in self.crowded_aisles else 0
        return distance + penalty

    def neighbors(self, node: str) -> Iterable[Tuple[str, float]]:
        if self.is_blocked(node):
            return []
        return [
            (target, distance)
            for target, distance in self.adjacency.get(node, [])
            if not self.is_blocked(target)
        ]

    def heuristic(self, source: str, target: str) -> float:
        x1, y1 = self.nodes[source]
        x2, y2 = self.nodes[target]
        return hypot(x2 - x1, y2 - y1) / 45

    def book_available(self, title: str) -> bool:
        book = self.books.get(title)
        return bool(book and book.available and title not in self.unavailable_books and self.shelf_is_accessible(book.shelf))

    def _reconstruct(self, parent: Dict[str, Optional[str]], target: str) -> List[str]:
        path: List[str] = []
        current: Optional[str] = target
        while current is not None:
            path.append(current)
            current = parent.get(current)
        return list(reversed(path))

    def bfs_or_dfs(self, title: str, algorithm: str = "BFS", start: str = "Entrance") -> SearchResult:
        book = self.books.get(title)
        if book is None:
            return SearchResult(False, "", [], 0, [], [], f"Book not found in catalogue: {title}")
        if not self.book_available(title):
            return SearchResult(False, book.shelf, [], 0, [], [], f"Book unavailable or its shelf is inaccessible: {title}")

        frontier = deque([start]) if algorithm.upper() == "BFS" else [start]
        parent: Dict[str, Optional[str]] = {start: None}
        distance: Dict[str, float] = {start: 0}
        open_list: List[str] = [start]
        closed_list: List[str] = []

        while frontier:
            current = frontier.popleft() if algorithm.upper() == "BFS" else frontier.pop()
            if current in open_list:
                open_list.remove(current)
            closed_list.append(current)
            if current == book.shelf:
                path = self._reconstruct(parent, current)
                return SearchResult(True, current, path, distance[current], open_list, closed_list, f"{algorithm.upper()} found {title}")

            for neighbor, edge_distance in self.neighbors(current):
                if neighbor not in parent:
                    parent[neighbor] = current
                    distance[neighbor] = distance[current] + edge_distance
                    if algorithm.upper() == "BFS":
                        frontier.append(neighbor)
                    else:
                        frontier.append(neighbor)
                    open_list.append(neighbor)

        return SearchResult(False, book.shelf, [], 0, open_list, closed_list, f"No route to {title} was found")

    def a_star_path(self, start: str, goal: str) -> SearchResult:
        if self.is_blocked(start) or self.is_blocked(goal):
            return SearchResult(False, goal, [], 0, [], [], "The start or destination is blocked")
        frontier: List[Tuple[float, int, str]] = []
        counter = 0
        heappush(frontier, (self.heuristic(start, goal), counter, start))
        parent: Dict[str, Optional[str]] = {start: None}
        g_score = {start: 0.0}
        open_list = [start]
        closed_list: List[str] = []

        while frontier:
            _, _, current = heappop(frontier)
            if current in open_list:
                open_list.remove(current)
            if current in closed_list:
                continue
            closed_list.append(current)
            if current == goal:
                return SearchResult(True, goal, self._reconstruct(parent, current), g_score[current], open_list, closed_list, "A* path found")
            for neighbor, raw_distance in self.neighbors(current):
                tentative = g_score[current] + self.edge_cost(current, neighbor, raw_distance)
                if tentative < g_score.get(neighbor, float("inf")):
                    parent[neighbor] = current
                    g_score[neighbor] = tentative
                    counter += 1
                    heappush(frontier, (tentative + self.heuristic(neighbor, goal), counter, neighbor))
                    if neighbor not in open_list:
                        open_list.append(neighbor)
        return SearchResult(False, goal, [], 0, open_list, closed_list, "A* could not reach the destination")

    def _route_heuristic(self, current: str, remaining: Sequence[str]) -> float:
        if not remaining:
            return 0
        distances = [self.heuristic(current, self.books[title].shelf) for title in remaining]
        return min(distances) + min(self.books[title].collection_time for title in remaining)

    def plan_route(self, titles: Sequence[str], start: str = "Entrance", time_limit: Optional[float] = None) -> dict:
        requested = [title for title in titles if title in self.books]
        unavailable = [title for title in requested if not self.book_available(title)]
        if unavailable:
            return {
                "found": False,
                "order": [],
                "path": [],
                "distance": 0,
                "time": 0,
                "score": 0,
                "open_list": [],
                "closed_list": [],
                "notes": ["These books cannot be included: " + ", ".join(unavailable)],
            }
        if not requested:
            return {"found": False, "order": [], "path": [], "distance": 0, "time": 0, "score": 0, "open_list": [], "closed_list": [], "notes": ["Select at least one book."]}

        # State is (current graph node, remaining book titles).
        initial_remaining = tuple(sorted(requested))
        initial = (start, initial_remaining)
        frontier: List[Tuple[float, int, float, float, Tuple[str, Tuple[str, ...]]]] = []
        counter = 0
        heappush(frontier, (self._route_heuristic(start, initial_remaining), counter, 0.0, 0.0, initial))
        best_score = {initial: 0.0}
        best_time = {initial: 0.0}
        parent: Dict[Tuple[str, Tuple[str, ...]], Tuple[Tuple[str, Tuple[str, ...]], str, List[str], float, float]] = {}
        open_trace: List[str] = [self._state_text(initial)]
        closed_trace: List[str] = []
        goal_state = None

        while frontier:
            _, _, score, elapsed, state = heappop(frontier)
            state_text = self._state_text(state)
            if state_text in open_trace:
                open_trace.remove(state_text)
            if any(state_text == item for item in closed_trace):
                continue
            closed_trace.append(state_text)
            current, remaining = state
            if not remaining:
                goal_state = state
                break
            for title in remaining:
                book = self.books[title]
                path_result = self.a_star_path(current, book.shelf)
                if not path_result.found:
                    continue
                raw_distance = sum(self._raw_distance(a, b) for a, b in zip(path_result.path, path_result.path[1:]))
                travel_time = raw_distance + book.collection_time
                new_time = elapsed + travel_time
                if time_limit is not None and new_time > time_limit:
                    continue
                new_remaining = tuple(item for item in remaining if item != title)
                new_state = (book.shelf, new_remaining)
                # Lower score means a better route. High-priority books receive a discount.
                priority_discount = max(0, 5 - book.priority) * self.priority_weight
                step_score = path_result.cost + book.collection_time + priority_discount
                new_score = score + step_score
                if new_score < best_score.get(new_state, float("inf")):
                    best_score[new_state] = new_score
                    best_time[new_state] = new_time
                    parent[new_state] = (state, title, path_result.path, raw_distance, travel_time)
                    counter += 1
                    estimate = new_score + self._route_heuristic(book.shelf, new_remaining)
                    heappush(frontier, (estimate, counter, new_score, new_time, new_state))
                    new_text = self._state_text(new_state)
                    if new_text not in open_trace:
                        open_trace.append(new_text)

        if goal_state is None:
            reason = "No complete route satisfies the current restrictions"
            if time_limit is not None:
                reason += f" and the {time_limit:g}-unit time limit"
            return {"found": False, "order": [], "path": [], "distance": 0, "time": 0, "score": 0, "open_list": open_trace, "closed_list": closed_trace, "notes": [reason]}

        segments: List[Tuple[str, List[str], float, float]] = []
        state = goal_state
        while state != initial:
            previous, title, segment_path, raw_distance, travel_time = parent[state]
            segments.append((title, segment_path, raw_distance, travel_time))
            state = previous
        segments.reverse()
        full_path: List[str] = [start]
        for _, segment_path, _, _ in segments:
            full_path.extend(segment_path[1:])
        return {
            "found": True,
            "order": [segment[0] for segment in segments],
            "path": full_path,
            "distance": sum(segment[2] for segment in segments),
            "time": sum(segment[3] for segment in segments),
            "score": best_score[goal_state],
            "open_list": open_trace,
            "closed_list": closed_trace,
            "notes": ["A* searched book-order states and selected the lowest-cost complete route."],
        }

    def _raw_distance(self, source: str, target: str) -> float:
        for neighbor, distance in self.adjacency.get(source, []):
            if neighbor == target:
                return distance
        return 0

    @staticmethod
    def _state_text(state: Tuple[str, Tuple[str, ...]]) -> str:
        current, remaining = state
        suffix = ", ".join(remaining) if remaining else "none"
        return f"{current} | remaining: {suffix}"

