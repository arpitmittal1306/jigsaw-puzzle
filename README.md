# Jigsaw Puzzle Pro

A desktop jigsaw puzzle game built with Python (`tkinter` + `Pillow`) featuring:
- Responsive full-window layout
- 3x3, 4x4, 5x5 puzzle sizes
- Drag-and-drop tile swapping
- Reference image popup
- Mandatory username before game start
- Game result tracking in CSV

## 1. Prerequisites

- Python 3.9+ installed
- `pip` available

## 2. Project Setup

1. Open terminal in project folder:
```powershell
cd "c:\Users\User\Desktop\AI Learning\Game"
```

2. (Optional but recommended) Create virtual environment:
```powershell
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependency:
```powershell
pip install pillow
```

## 3. Run the Game

```powershell
python main.py
```

## 4. First-Time Start Flow

1. Username popup appears.
2. User must enter username to continue.
3. After username, game opens in maximized window.

## 5. How to Play

- Drag one tile and drop on another position to swap.
- Arrange all tiles in correct order to win.
- Use `Reference` button to open solved-image preview.

## 6. Controls

- `3x3` / `4x4` / `5x5`: change puzzle size
- `Puzzle`: switch puzzle image/theme
- `Reference`: show full reference image
- `Restart`: restart current puzzle

## 7. Game Result Logging

Game results are stored in:
- `game_results.csv`

Every completed/interrupted round writes one record with:
- `username`
- `start_time`
- `end_time`
- `total_time_seconds`
- `size`
- `puzzle`
- `result` (shows `win` only when puzzle is completed)
- `moves`
- `end_reason` (`win`, `restart`, `app_close`, `size_change`, `puzzle_change`)

Note:
- New records are inserted at the top (latest first).

## 8. Optional Local Image

If `image.jpg` exists in project root, it is available as `My Image` puzzle.

## 9. Troubleshooting

- `ModuleNotFoundError: PIL`
  - Run: `pip install pillow`

- Window doesn’t start
  - Confirm Python install: `python --version`
  - Run from project directory where `main.py` exists.
