import pandas as pd

divs = {
        "North": ["VGS", "SEA", "DC", "STL"],
        "South": ["ARL", "ORL", "HOU", "SA"]
        }

urls = {1: ['https://www.xfl.com/games/2302001-VGS-at-ARL',
  'https://www.xfl.com/games/2302002-ORL-at-HOU',
  'https://www.xfl.com/games/2302003-STL-at-SA',
  'https://www.xfl.com/games/2302004-SEA-at-DC'],
 2: ['https://www.xfl.com/games/2302005-STL-at-SEA',
  'https://www.xfl.com/games/2302006-DC-at-VGS',
  'https://www.xfl.com/games/2302007-SA-at-ORL',
  'https://www.xfl.com/games/2302008-ARL-at-HOU'],
 3: ['https://www.xfl.com/games/2302009-SEA-at-VGS',
  'https://www.xfl.com/games/2302010-STL-at-DC',
  'https://www.xfl.com/games/2302011-ORL-at-ARL',
  'https://www.xfl.com/games/2302012-SA-at-HOU'],
 4: ['https://www.xfl.com/games/2302013-HOU-at-ORL',
  'https://www.xfl.com/games/2302014-SA-at-SEA',
  'https://www.xfl.com/games/2302015-ARL-at-STL',
  'https://www.xfl.com/games/2302016-VGS-at-DC'],
 5: ['https://www.xfl.com/games/2302017-HOU-at-SEA',
  'https://www.xfl.com/games/2302018-DC-at-STL',
  'https://www.xfl.com/games/2302019-ORL-at-VGS',
  'https://www.xfl.com/games/2302020-ARL-at-SA'],
 6: ['https://www.xfl.com/games/2302021-SEA-at-ORL',
  'https://www.xfl.com/games/2302022-STL-at-VGS',
  'https://www.xfl.com/games/2302023-SA-at-ARL',
  'https://www.xfl.com/games/2302024-HOU-at-DC'],
 7: ['https://www.xfl.com/games/2302025-SEA-at-ARL',
  'https://www.xfl.com/games/2302026-STL-at-HOU',
  'https://www.xfl.com/games/2302027-SA-at-VGS',
  'https://www.xfl.com/games/2302028-DC-at-ORL'],
 8: ['https://www.xfl.com/games/2302029-VGS-at-STL',
  'https://www.xfl.com/games/2302030-ARL-at-ORL',
  'https://www.xfl.com/games/2302031-HOU-at-SA',
  'https://www.xfl.com/games/2302032-DC-at-SEA'],
 9: ['https://www.xfl.com/games/2302033-VGS-at-HOU',
  'https://www.xfl.com/games/2302034-ORL-at-SA',
  'https://www.xfl.com/games/2302035-ARL-at-DC',
  'https://www.xfl.com/games/2302036-SEA-at-STL'],
 10: ['https://www.xfl.com/games/2302037-ORL-at-STL',
  'https://www.xfl.com/games/2302038-DC-at-SA',
  'https://www.xfl.com/games/2302039-HOU-at-ARL',
  'https://www.xfl.com/games/2302040-VGS-at-SEA']}

divs = {
        "North": ["VGS", "SEA", "DC", "STL"],
        "South": ["ARL", "ORL", "HOU", "SA"]
        }
