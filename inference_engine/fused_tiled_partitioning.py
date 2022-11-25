import numpy as np

# Fused Tiled Partitioning
class Tile():
    def __init__(self):
        self.top_left_x = 0
        self.top_left_y = 0
        self.bottom_right_x = 0
        self.bottom_right_y = 0
        self.Nidx = 0
        self.Midx = 0

    def width(self):
        return self.bottom_right_x - self.top_left_x + 1

    def height(self):
        return self.bottom_right_y - self.top_left_y + 1

    def __repr__(self):
        return f"({self.top_left_x}, {self.top_left_y}) -- ({self.bottom_right_x}, {self.bottom_right_y})"

def grid(width, height, N, M, i, j):
    """
    Partitions the rectangle widthxheight into NxM tiles.
    Returns the coordinates
    of the tile ixj, as top left (x,y) and bottom right (x, y)

    Tile indices (i,j) are 0 indexed
    """
    t = Tile()

    t.Nidx = i
    t.Midx = j

    t.top_left_x = int(j*width/M)
    t.top_left_y = int(i*height/N)

    t.bottom_right_x = int(t.top_left_x + width/M - 1)
    t.bottom_right_y = int(t.top_left_y + height/N - 1)

    return t

def traversal(next_tile, Wl, Hl, Fl, Sl, i, j):
    """
    Computes the input shape of the previous layer tile based on the current tile,
    and the characteristics of the previous layer.
    """
    t = Tile()

    t.Nidx = i
    t.Midx = j

    t.top_left_x = int(max(0, Sl[0]*next_tile.top_left_x-np.floor(Fl/2)))
    t.top_left_y = int(max(0, Sl[1]*next_tile.top_left_y-np.floor(Fl/2)))

    t.bottom_right_x = int(min(Sl[0]*next_tile.bottom_right_x+np.floor(Fl/2), Wl-1))
    t.bottom_right_y = int(min(Sl[1]*next_tile.bottom_right_y+np.floor(Fl/2), Hl-1))

    return t

def FTP(model_metadata, N, M):
  """
  Performs Fused Tile Partitioning on the given model, creating a grid of NxM,
  N on the vertical, M on the horizontal. Based on the DeepThings algorithm.

  Parameters:
  N,M   -- vertical and horizontal partitions for the model input. Should lead
           to an integral split.
  """
  num_layers = len(model_metadata)
  W_L = model_metadata[-1]['output_shape'][2]
  H_L = model_metadata[-1]['output_shape'][1]
  tiles = [[[None for j in range(M)] for i in range(N)] for l in range(num_layers+1)]
  for i in range(N):
    for j in range(M):
      tiles[num_layers][i][j] = grid(W_L, H_L, N, M, i, j)
      # Perform backward traversal to determine the tile config for previous layers
      for l in range(num_layers, 0, -1):
        W_l = model_metadata[l-1]['output_shape'][2]
        H_l = model_metadata[l-1]['output_shape'][1]
        S_l = model_metadata[l-1]['strides'] # Stride of conv filter
        F_l = model_metadata[l-1]['kernel_shape'][0] # Size of conv filter
        tiles[l-1][i][j] = traversal(tiles[l][i][j], W_l, H_l, F_l, S_l, i, j)
  return tiles

def get_first_partition(input_data, model_metadata, N, M):
    tiles = FTP(model_metadata, N, M)
    tile = tiles[0][0][0]
    return input_data[:,tile.top_left_x:tile.bottom_right_x+1,
                    tile.top_left_y:tile.bottom_right_y+1,:]

def get_partition_details(input_data, model_metadata, N, M):
    tiles = FTP(model_metadata, N, M)
    # Only keep the first layer and flatten
    tiles_list = [t for row in tiles[0] for t in row]
    return tiles_list

def get_partition_data(tile, input_data):
    """
    Retrieve from the input data the values corresponding to a partition
    """
    return input_data[:,tile.top_left_y:tile.bottom_right_y+1,
                    tile.top_left_x:tile.bottom_right_x+1,:]

