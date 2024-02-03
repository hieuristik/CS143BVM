FREE_FRAMES = [False]*1024

def getFreeFrame():
    for frame_index in range( len(FREE_FRAMES) ):
        if ( not FREE_FRAMES[frame_index] ): return frame_index # frame has not yet been allocated
    return -1

def getNextIndexFromDisk(block_index, disk):
    for index, value in enumerate(disk[block_index]):
        if (value == 0): return index
    return -1


class Disk:
    def __init__(self):
        self.memory = [[0 for _ in range(512)] for _ in range(1024)]
    
    def read_block(self, b, m, PM):
        # copies block D[b] into PM frame starting at location PM[m]
        for index, value in enumerate( self.memory[ b ] ): # loop through disk block and copy contents
            PM[m + index] = value # update PM contents

class PM:
    def __init__(self):
        self.disk = Disk()
        self.memory = [0 for _ in range(524288)]
    
    def initialize(self, file): # initialization from file
        ST_SETUP = None
        PT_SETUP = None
        with open(file, "r") as f:
            lines = f.readlines()
            ST_SETUP = lines[0]
            PT_SETUP = lines[1]
        ST_SETUP = zip(*(iter(ST_SETUP.split()),) * 3)
        PT_SETUP = zip(*(iter(PT_SETUP.split()),) * 3)

        FREE_FRAMES[0] = True                                             # indicate that both frames 0 and 1
        FREE_FRAMES[1] = True                                             # have been allocated for the ST

        for (segment, length, frameNumberOfPageTable) in ST_SETUP:        # Process the first line to create the segment table in physical memory
            self.memory[int(segment)*2] = int(length)                     # length of segment
            self.memory[(int(segment)*2)+1] = int(frameNumberOfPageTable) # if negative, absolute value b is the block number on disk that contains the PT
            if int(frameNumberOfPageTable) > 0: FREE_FRAMES[ int(frameNumberOfPageTable) ] = True  # if frame > 0, PM[frame] contains PT
                                                                                                  # else, Disk[|frame|] contains PT
        for (segment, page, frameNumberOfPage) in PT_SETUP:
            page_table_index = self.memory[(int(segment)*2)+1]

            if ( page_table_index <= 0 ): # PT not resident, stored on Disk
                block_index = page_table_index*-1
                free_index = getNextIndexFromDisk(block_index, self.disk.memory)
                self.disk.memory[block_index][free_index] = int(frameNumberOfPage)
            else:
                self.memory[(page_table_index*512)+int(page)] = int(frameNumberOfPage)
            
            if int(frameNumberOfPage) > 0: FREE_FRAMES[ int(frameNumberOfPage) ] = True # if frame > 0, PM[frame] contains page
                                                                                   # else, Disk[|frame|] contains page
    
    def translate(self, file): # translate VA to PA
        lines = None
        write_lines = list()
        with open(file, "r") as f:
            lines = f.readlines()
        lines = lines[0].split()
        for line in lines:
            s = int(line) >> 18
            w = int(line) & 511
            p = (int(line) >> 9) & 511
            pw = int(line) & 262143
            if pw >= self.memory[2*s]: # VA outside of segment boundary
                write_lines.append( str(-1) + " " )
            if self.memory[(2*s)+1] < 0: # PT not resident, in Disk
                f1 = getFreeFrame()
                FREE_FRAMES[ f1 ] = True
                self.disk.read_block( self.memory[(2*s)+1]*-1, f1*512, self.memory)
                self.memory[ (2*s)+1 ] = f1
            if self.memory[(self.memory[(2*s)+1]*512)+p] < 0: # page not resident, in Disk
                f2 = getFreeFrame()
                FREE_FRAMES[ f2 ] = True
                self.disk.read_block( self.memory[ (self.memory[(2*s)+1] * 512) + p ], f2*512, self.memory )
                self.memory[ (self.memory[(2*s)+1]*512) + p ] = f2
            PA = self.memory[(self.memory[(2*s)+1]*512)+p]*512+w
            write_lines.append(str(PA) + " ")
        with open("output.txt", "w") as outfile:
            outfile.writelines( write_lines )

if __name__ == "__main__":
    try:
        pm = PM()
        opt = input().split()
        pm.initialize(opt[0])
        pm.translate(opt[1])
    except:
        print("Error Occurred While Processing Input")
