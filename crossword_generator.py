import curses
from curses import wrapper
import os
import time

os.environ.setdefault('ESCDELAY', '25')
dict_dict = {}

# What dictionary to use
dictionary_path = "dictionaries/sv_wikidict.txt"


def load_dict(path):
    # Load dictionary from file
    _words = []
    with open(path, "r") as file:
        for line in file:
            line = line.split(",")
            word = line[0].strip()
            _words.append(word)
            dict_dict[word] = (float(line[1]), int(line[2]))
    return _words


# Load at once
words = load_dict(dictionary_path)


def suggest_word(query, after):
    # Returns list of words that matches query. After parameter searches for n-additional characters
    global words
    counter = 0
    after += 1
    suggested = []
    start_time = time.time()
    while counter < after:
        known = query + [None] * counter
        counter += 1
        for word in words:
            if len(word) == len(known):
                for i, l in enumerate(word):
                    if known[i] is None:
                        pass
                    elif known[i].lower() == l.lower():
                        pass
                    else:
                        break
                else:
                    suggested.append(word)
    return suggested, (time.time()-start_time)*1e3


# Ask user for dimensions
width = int(input("Width: "))
height = int(input("Height: "))

# Start curses
stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(True)


def main(stdscr):
    # Clear screen
    stdscr.clear()
    stdscr.refresh()

    # Initiate window
    win = curses.newwin(height+2, width+2, 0, 0)
    win.box()
    win.move(1, 1)
    win.keypad(True)
    win.refresh()

    # Initiate suggestion color pair
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)

    def _print(s, p, attr=0):
        # Prints s at given position
        op = win.getyx()
        win.move(p[0], p[1])
        try:
            win.addstr(str(s), attr)
        except curses.error:
            pass  # This happens when trying to print off-screen
        win.move(op[0], op[1])

    def select(o):
        if type(o) == tuple:
            o = [o]
        orgpos = win.getyx()
        for pt in o:
            selected.append(pt)
        for pt in selected:
            if pt != orgpos:
                win.chgat(pt[0], pt[1], 1, curses.A_STANDOUT)
        win.move(orgpos[0], orgpos[1])

    def deselect(o):
        if type(o) == tuple:
            o = [o]
        op = win.getyx()
        for pt in o[:]:
            win.chgat(pt[0], pt[1], 1, curses.A_NORMAL)
            selected.remove(pt)
            win.refresh()
        win.move(op[0], op[1])

    k = None
    selected = []
    select_typing = False

    while True:
        k = win.getch()  # Get user action
        if k in [curses.KEY_RIGHT, curses.KEY_LEFT, curses.KEY_DOWN, curses.KEY_UP]:
            deselect(selected)  # Deselect all

        # Move cursor if within bounds:
        if k == curses.KEY_RIGHT:
            if win.getyx()[1] != width:
                win.move(win.getyx()[0], win.getyx()[1]+1)
                select_typing = False
        elif k == curses.KEY_LEFT:
            if win.getyx()[1] != 1:
                win.move(win.getyx()[0], win.getyx()[1]-1)
                select_typing = False
        elif k == curses.KEY_DOWN:
            if win.getyx()[0] != height:
                win.move(win.getyx()[0]+1, win.getyx()[1])
                select_typing = False
        elif k == curses.KEY_UP:
            if win.getyx()[0] != 1:
                win.move(win.getyx()[0]-1, win.getyx()[1])
                select_typing = False
        elif k == 27:  # Escape key to deselect or quit program
            if selected:
                deselect(selected)
            else:
                break
        elif k == 10:
            pass
        elif k in [560, 545, 525, 566]:  # Ctrl + right, left, bottom, up, to select
            select_typing = False
            pos = win.getyx()
            if not selected:
                select(pos)
            if k == 560 and pos[1] != width:
                win.move(pos[0], pos[1] + 1)
            elif k == 545 and pos[1] != 1:
                win.move(pos[0], pos[1] - 1)
            elif k == 525 and pos[0] != height:
                win.move(pos[0]+1, pos[1])
            elif k == 566 and pos[0] != 1:
                win.move(pos[0]-1, pos[1])
            new_pos = win.getyx()
            if new_pos in selected:
                deselect(pos)
            else:
                select(new_pos)

        elif k == ord('\t'):  # Start suggesting words for active selection
            if selected:
                # Build query
                chars = []
                for pc in selected:
                    char = chr(win.inch(pc[0], pc[1]) & 0xFF)
                    if char == ' ' or char == ' ':
                        char = None
                    chars.append(char)
                if None not in chars:
                    continue
                # Query words
                suggested, exec_time = suggest_word(chars, 0)
                # Without alphabetical sort, will be order in file (commonality)
                # suggested.sort()
                _print(str(exec_time)+"ms", (0, 0))

                # If found no suggestions
                if not suggested:
                    win.box()
                    _print("NO SUGGESTION", (height + 1, 1), curses.A_BOLD)
                    continue

                iterated_words = 0
                keep_word = False
                while True:  # Iterate through found words
                    win.box()
                    suggested_word = suggested[iterated_words]
                    # Print on screen in right color, maybe can be done with _print
                    for cp, ch in enumerate(suggested_word):
                        win.move(selected[cp][0], selected[cp][1])
                        if chars[cp] is None:
                            if cp == 0:
                                win.addstr(ch, curses.color_pair(1))
                            else:
                                win.addstr(ch, curses.color_pair(1) | curses.A_STANDOUT)
                    win.move(selected[0][0], selected[0][1])
                    # Print extra info in lower left edge
                    word_rate = int(1/(10**dict_dict[suggested_word][0]))
                    _print(suggested_word+", word rate: 1/"+str(word_rate), (height+1, 1))
                    win.refresh()

                    # Get user key
                    k = win.getch()
                    if k == 10:  # Enter key to break loop and keep word
                        keep_word = True
                    elif k == ord('\t'):  # Tab to get next word
                        iterated_words = (iterated_words+1) % len(suggested)
                        continue
                    elif k == curses.KEY_STAB:  # Shift tab to go back, FIXME
                        iterated_words = (len(suggested) + iterated_words - 1) % len(suggested)
                        continue
                    break

                if keep_word:
                    deselect(selected)
                else:  # Reset to old characters
                    win.box()
                    for cp, ch in enumerate(chars):
                        win.move(selected[cp][0], selected[cp][1])
                        if ch is None:
                            win.addch(" ", curses.A_STANDOUT)
                        else:
                            win.addch(ch, curses.A_STANDOUT)
        elif k == curses.KEY_BACKSPACE or k == curses.KEY_DC:  # Delete all selected
            if selected:
                for cp in selected:
                    win.addch(cp[0], cp[1], " ")
            else:
                win.addstr(" ")
                win.move(win.getyx()[0], win.getyx()[1] - 1)
        elif k is not None:  # Add manually by typing
            try:
                if chr(k).isalnum():
                    if selected:  # Add rolling within selection
                        if not select_typing:
                            select_typing = True
                            win.move(selected[0][0], selected[0][1])
                        if win.getyx() == selected[-1]:
                            select_typing = False
                            win.addstr(chr(k).upper(), curses.A_STANDOUT)
                            win.move(selected[-1][0], selected[-1][1])  # Stay on last if just type last
                        else:
                            win.addstr(chr(k).upper(), curses.A_STANDOUT)
                            win.move(win.getyx()[0], win.getyx()[1]-1)
                            new_pos = selected[selected.index(win.getyx())+1]
                            win.move(new_pos[0], new_pos[1])
                    else:
                        win.addstr(chr(k).upper())
                        win.move(win.getyx()[0], win.getyx()[1]-1)
            except ValueError as e:
                pass

        win.refresh()

    stdscr.refresh()


# Start program
wrapper(main)

# Quit program
curses.nocbreak()
stdscr.keypad(False)
curses.echo()
curses.endwin()