# Intelligent Library Search and Book Collection Agent

A Python desktop application that represents a library as a graph, searches for books using BFS/DFS, and generates an efficient route for collecting multiple books using A*.

## Features

- Graph representation of the entrance, sections, aisles and shelves.
- BFS and DFS search for a selected book.
- A* route planning for multiple selected books.
- Priority-aware route scoring.
- Optional user time limit.
- Closed sections, unavailable books, crowded aisles and restricted shelves.
- Accessible-route-only option.
- GUI map showing the selected route and blocked areas.
- Open list and closed list display for search transparency.
- Uses only Python's standard library; no external packages are required.

## Run the project

1. Install Python 3.9 or newer.
2. Open a terminal in this folder.
3. Run:

```bash
python app.py
```

On some systems, use `python3 app.py` instead.

## How to demonstrate it

1. Select **BFS** or **DFS**, choose a book, and click **Find book location**.
2. Select two or more books in the A* list.
3. Optionally enter a time limit such as `35`.
4. Select one or more temporary conditions from the library-condition boxes.
5. Click **Plan multi-book route with A***.
6. Open the **Library map** tab to see the route and the **Search and route details** tab to see the open/closed lists.

## Project structure

```text
intelligent_library_agent/
├── app.py              # Tkinter graphical interface
├── library_agent.py    # Graph, BFS, DFS and A* algorithms
├── test_library_agent.py# Small automated tests
├── README.md           # Setup and usage guide
├── requirements.txt    # Dependency note
└── .gitignore
```

## Algorithm note

The library is a weighted graph. Sections and shelves are nodes, while walking connections are edges. BFS and DFS locate one book. For several books, A* searches states of the form `(current location, remaining books)`. Its score combines walking distance, collection time and priority, while blocked areas are removed from the graph.

## Run the tests

```bash
python -m unittest -v
```

