"""
  Sounds:
  Currently using pygame for the sounds, but could use pyglet
  later if we can get the fucking thing to load a .ogg without
  segfaulting.
"""

try:
    from pygame import mixer
    mixer.init()
except ImportError:
    mixer = None


music_files = {
    "title":"subterranean.ogg",
    }

sound_files = {
    "crack":"crack.ogg",
    "squelch":"squelch.ogg",
    "roar":"roar.ogg",
    "pain":"ow.ogg",
}

def music_start(key)
