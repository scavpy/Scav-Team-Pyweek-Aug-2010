"""
 An example level file
"""

example_level = {
    "name":"Example Level",
    "story":["""You find yourself deep in an underground cave
full of hexagons. For some reason."""],
    "start":(1,1),
    "exit":(5,4),
    "monsters":{},
    "hexes": {
        (0,5):"#", (1,5):"#", (2,5):"#", (3,5):"#", (4,5):"#", (5,5):"#",
        (0,4):"#", (1,4):" ", (2,4):" ", (3,4):"#", (4,4):"H13f", (5,4):"X",
        (0,3):"#", (1,3):" ", (2,3):" ", (3,3):" ", (4,3):"H14e", (5,3):"#",
        (0,2):"#", (1,2):" ", (2,2):"H821", (3,2):" ", (4,2):"#", (5,2):"#",
        (0,1):"#", (1,1):"S", (2,1):"H821", (3,1):"H731", (4,1):"H642", (5,1):"#",
        (0,0):"#", (1,0):"#", (2,0):"#", (3,0):"#", (4,0):"#", (5,0):"#",
        },
}





if __name__=='__main__':
    import sys
    import pickle
    pickle.dump(example_level,sys.stdout,-1)
