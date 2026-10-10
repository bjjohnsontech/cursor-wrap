# cursor-wrap

Wraps the mouse cursor around the edges of a multi-monitor layout in Hyprland. Push the cursor off the right edge of the rightmost monitor and it appears at the left edge of the leftmost monitor, and vice versa. That lets you move sideways from any monitor to any other.

Built for Omarchy (Arch Linux) on Hyprland 0.55+.

## How it works

Hyprland has no built-in cursor wrap-around, and its event socket doesn't report pointer motion. The script polls instead:

1. Every 20 ms it asks Hyprland for the cursor position (`j/cursorpos`) over the IPC socket.
2. If the cursor is at the far-right edge, it jumps to just inside the far-left edge, and the reverse.
3. Every 5 seconds it re-reads the monitor layout (`j/monitors`), so plugging in or rearranging monitors needs no restart.

The jump uses the Lua dispatcher `hl.dsp.cursor.move({ x, y })`. The Y position is preserved. Talking to the socket directly avoids spawning `hyprctl` and `jq` on every poll, which keeps CPU use negligible.

## Requirements

- Hyprland 0.55 or newer (Lua config and Lua dispatchers)
- Python 3.9+ (standard library only, nothing to install)
- Must run inside the Hyprland session (needs `XDG_RUNTIME_DIR` and `HYPRLAND_INSTANCE_SIGNATURE`)

## Install

```bash
mkdir -p ~/.local/bin
cp cursor-wrap.py ~/.local/bin/cursor-wrap.py
chmod +x ~/.local/bin/cursor-wrap.py
```

Test it by hand first:

```bash
~/.local/bin/cursor-wrap.py &
```

Push the cursor off the right edge of the right-most monitor. It should reappear on the left edge of the left-most one.

To check that the dispatcher syntax works on your Hyprland version:

```bash
hyprctl dispatch 'hl.dsp.cursor.move({ x = 100, y = 100 })'
```

## Autostart

Add this to `~/.config/hypr/autostart.lua` (or to whichever user Lua file your config uses for autostart):

```lua
o.launch_on_start("~/.local/bin/cursor-wrap.py")
end)
```

Then run `hyprctl reload` and `hyprctl configerrors` to check for errors. `hyprland.start` only fires at session start, so launch the script manually once, or log out and back in.

## Configuration

Settings are constants at the top of the script:

| Constant | Default | Meaning |
|---|---|---|
| `POLL` | `0.02` | Seconds between cursor checks. Raise to `0.03`-`0.05` to use less CPU; a very fast flick may overshoot the edge by a few pixels. |
| `LAYOUT_REFRESH` | `5.0` | Seconds between monitor layout re-reads. |
| `EDGE` | `3` | Pixels of slack at each edge, so fractional scaling can't cause a missed trigger. |

## Rotated and scaled monitors

Hyprland reports `width` and `height` as the unrotated panel size. For monitors with an odd `transform` value (1, 3, 5, 7 are the 90° and 270° rotations), the script swaps width and height before computing the right edge. Width is also divided by `scale` to get the logical size. Without the swap, a rotated monitor at the right edge makes the script look for the edge in the wrong place, so wrapping works in one direction only.

## Troubleshooting

**Nothing happens.** Run the script in a terminal without `&` to see any traceback. The usual cause is a missing `HYPRLAND_INSTANCE_SIGNATURE`, which happens when it's launched from outside the Hyprland session.

**Wraps left but not right (or the reverse).** Check the monitor geometry:

```bash
hyprctl cursorpos
hyprctl monitors -j | jq '.[] | {name, x, y, width, height, scale, transform}'
```

Push the cursor hard against the right edge and compare its X value with `x + width/scale` of the rightmost monitor (using `height` instead of `width` if `transform` is odd). If they differ by more than a few pixels, the edge calculation is wrong for your layout.

**Two copies fighting.** If you previously ran a bash version, stop it with `pkill -f cursor-wrap.sh` and remove its autostart entry.

## Limitations

- Monitors with different heights: the cursor keeps its Y value, and Hyprland clamps it onto the target monitor, so it may land slightly off from where it left.
- Games that capture or lock the pointer may not work well with it.
- The script wraps only the outer left and right edges. Vertical layouts are not handled.

## Stopping it

```bash
pkill -f cursor-wrap.py
```

## TODO
- add vertical code
- create small config window for Constants and Direction selection
- turn into omarchy plugin