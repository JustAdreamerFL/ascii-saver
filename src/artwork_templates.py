"""Curated, editable, offline ASCII artwork starters for Artwork Studio.

All starter artworks are original project assets. A template is inserted as text
and is never saved to the user's artwork library without an explicit Save.
The template titles/styles help users discover different visual approaches,
not just different canvas dimensions.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtworkTemplate:
    key: str
    title: str
    style: str
    description: str
    artwork: str


def _artwork(text: str) -> str:
    # Dedent literal artwork without changing meaningful leading spaces.
    lines = text.strip('\n').splitlines()
    return '\n'.join(lines) + '\n'


TEMPLATES = (
    ArtworkTemplate(
        'horizon', 'Distant Horizon', 'Cinematic · Landscape',
        'A quiet mountain silhouette, sun and negative space.',
        _artwork(r'''
                         .        .
                   .           *
                              _
                .          .-' '-.
                          (   o   )
       .                   '-._.-'
              _         _
         _   / \_   ___/ \_    ___
     ___/ \_/   /\_/       \__/   \___
   _/       _.-'   '-._  _.-'       \  \_
  /______.-'           ''             '-._\

            S O M E W H E R E
                 O U T S I D E
'''),
    ),
    ArtworkTemplate(
        'orbit', 'Orbital Signal', 'Sci-fi · Diagram',
        'Space-age rings and a technical broadcast motif.',
        _artwork(r'''
                .      *       .
           .       _..---.._      +
                 .'  .- -.  '.
        *       /   /  o  \   \      .
               |    \     /    |
        .       \    '---'    /
                 '.         .'
          +        '-.._..-'       *
             .  / /  |  \ \  .
               /_/   |   \_\

       [  SIGNAL RECEIVED  ]
         0  1  0  0  1  1  0
'''),
    ),
    ArtworkTemplate(
        'botanical', 'Quiet Botanical', 'Organic · Illustration',
        'An airy, hand-drawn branch with soft symmetry.',
        _artwork(r'''
                           .
                          / \
                    .    /   \   .
                   ( )--'  |  '--( )
                    '       |     '
              .             |   .
             ( )--.     .---'--( )
              '    \   /       '
                    \ /
                     |       .
                     |   .--( )
                     |  /    '
                     | /
                    /|/
               ____/_|_\____

                 G R O W
'''),
    ),
    ArtworkTemplate(
        'neon', 'Neon Terminal', 'Cyberpunk · Typography',
        'Bold type, geometric borders and a glitchy terminal mood.',
        _artwork(r'''
  +------------------------------------------------+
  |  \ /  /\  /\/\  /\  /\/\  /\  /\  /\  \ /  |
  |                                                |
  |      N E O N  / /  N I G H T                  |
  |                                                |
  |      [ CONNECTED ]     //  2084.11            |
  |      > _                                       |
  |                                                |
  |  //::::::::::::::::::::::::::::::::::::::\\   |
  +------------------------------------------------+
'''),
    ),
    ArtworkTemplate(
        'waves', 'Tidal Lines', 'Minimal · Abstract',
        'Rhythmic, flowing marks with a minimalist editorial feel.',
        _artwork(r'''
               .                 .
         ~~~        ~~~                 ~~~
     .-     -.  .-     -.    .-     -.
  __/         \/         \__/         \__
     \       /  \       /    \       /
  ~~~ '-----' ~~ '-----' ~~~~ '-----' ~~~

                 D R I F T
             between the lines
'''),
    ),
    ArtworkTemplate(
        'city', 'Midnight City', 'Pixel · Architecture',
        'A stylized nocturnal skyline for a wide artwork canvas.',
        _artwork(r'''
      .             *              +        .
                    .
         _    _   _         ___      __
        | |  | | | |       _|   |_   |  |
       _| |_ | |_| |  _   |  []  | _ |  |_
      | []  ||  _  | | |  _| [] []|| || [] |
      |   []|| | | | | |_| |       || ||    |
      |__|__||_|_|_|_|___|_|__|___||_||____|
      ~~~~   ~~~~~   ~~~~   ~~~   ~~~~~~~~

                 AFTER HOURS
'''),
    ),
    ArtworkTemplate(
        'geometry', 'Geometric Pulse', 'Brutalist · Pattern',
        'Strong repetition, symmetry and monochrome structure.',
        _artwork(r'''
   /\      /\      /\      /\      /\
  /  \____/  \____/  \____/  \____/  \
  \  /    \  /    \  /    \  /    \  /
   \/  <>  \/  <>  \/  <>  \/  <>  \/
   /\      /\      /\      /\      /\
  /  \____/  \____/  \____/  \____/  \
  \  /    \  /    \  /    \  /    \  /
   \/      \/      \/      \/      \/

          F O R M  /  F U N C T I O N
'''),
    ),
    ArtworkTemplate(
        'retro', 'Retro Arcade', 'Playful · Pixel',
        'An old-school arcade title and a tiny pixel mascot.',
        _artwork(r'''
   ########################################
   #                                      #
   #        *  A R C A D E  *             #
   #                                      #
   #             .------.                 #
   #            /  o  o  \                #
   #           |    __    |               #
   #            \  '=='  /                #
   #             '------'                 #
   #                                      #
   #       PRESS START > _                #
   #                                      #
   ########################################
'''),
    ),
)


def get_template(key: str) -> ArtworkTemplate:
    """Retrieve only an explicitly bundled template, without file-system input."""
    for template in TEMPLATES:
        if template.key == key:
            return template
    raise KeyError(key)
