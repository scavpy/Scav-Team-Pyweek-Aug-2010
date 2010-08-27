"""
  Sounds:
  Currently using pygame for the sounds, but could use pyglet
  later if we can get the fucking thing to load a .ogg without
  segfaulting.
"""
import os

try:
    from pygame import mixer
except ImportError:
    mixer = None


music_files = {
    "title":"subterranean.ogg",
    "gameplay":"honeycomb.ogg"
    }

sound_files = {
    "crack":"crack.ogg",
    "squelch":"squelch.ogg",
    "roar":"roar.ogg",
    "pain":"ow.ogg",
    "chime":"chime.ogg",
    "chamber":"chamber.ogg",
    "ring":"ring.ogg",
    "crunch":"crunch.ogg",
    "munch":"munching.ogg",
    "bellow":"foghorn.ogg",
    "rumble":"rumble.ogg",
}

sounds = {}

def filepath(f):
    return os.path.join("data","sound",f)

def music_start(name):
    if not mixer:
        return
    f = music_files.get(name)
    if f:
        mixer.music.load(filepath(f))
        mixer.music.play(-1)

def music_fade(ms):
    if not mixer:
        return
    mixer.music.fadeout(ms)

def play(name):
    s = sounds.get(name)
    if s:
        s.play()

def init():
    if not mixer:
        return
    mixer.init()
    for k,f in sound_files.items():
        sounds[k] = mixer.Sound(filepath(f))
