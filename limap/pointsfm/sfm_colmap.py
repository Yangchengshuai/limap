from _limap import _base, _pointsfm
from .read_write_model import *

def compute_neighbors(model, n_neighbors, min_triangulation_angle=1.0, neighbor_type="iou"):
    if neighbor_type == "iou":
        neighbors = model.GetMaxIoUImages(n_neighbors, min_triangulation_angle)
    elif neighbor_type == "overlap":
        neighbors = model.GetMaxOverlappingImages(n_neighbors, min_triangulation_angle)
    elif neighbor_type == "dice":
        neighbors = model.GetMaxDiceCoeffImages(n_neighbors, min_triangulation_angle)
    else:
        raise NotImplementedError
    return neighbors

def ComputeNeighbors(colmap_output_path, n_neighbors, min_triangulation_angle=1.0, neighbor_type="iou", sparse_dir="sparse", images_dir="images"):
    model = _pointsfm.SfmModel()
    model.ReadFromCOLMAP(colmap_output_path, sparse_dir, images_dir)

    # get neighbors
    neighbors = compute_neighbors(model, n_neighbors, min_triangulation_angle=min_triangulation_angle, neighbor_type=neighbor_type)
    image_names = model.GetImageNames()
    return neighbors, image_names

# compute neighborhood for a image list sorted as 'image{0:08d}.png'
def ComputeNeighborsSorted(colmap_output_path, n_neighbors, min_triangulation_angle=1.0, neighbor_type="iou", sparse_dir="sparse", images_dir="images"):
    model = _pointsfm.SfmModel()
    model.ReadFromCOLMAP(colmap_output_path, sparse_dir, images_dir)

    # get neighbors
    image_names = model.GetImageNames()
    image_id_list = [int(name[5:-4]) for name in image_names]
    neighbors = compute_neighbors(model, n_neighbors, min_triangulation_angle=min_triangulation_angle, neighbor_type=neighbor_type)

    # map indexes
    n1 = [neighbors[image_id_list.index(k)] for k in range(len(image_id_list))]
    n2 = [[image_id_list[val] for val in neighbor] for neighbor in n1]
    neighbors = n2
    return neighbors

def ComputeRanges(colmap_output_path, range_robust=[0.01, 0.99], k_stretch=1.25, sparse_dir="sparse", images_dir="images"):
    model = _pointsfm.SfmModel()
    model.ReadFromCOLMAP(colmap_output_path, sparse_dir, images_dir)
    ranges = model.ComputeRanges(range_robust, k_stretch)
    return ranges

def ReadInfosFromModel(model, colmap_path, model_path="sparse", image_path="images", max_image_dim=None, check_undistorted=True):
    print("Start loading COLMAP sparse reconstruction.")
    image_names = model.GetImageNames()
    model_path = os.path.join(colmap_path, model_path)
    image_path = os.path.join(colmap_path, image_path)
    if os.path.exists(os.path.join(model_path, "cameras.bin")):
        fname_cameras = os.path.join(model_path, "cameras.bin")
        fname_images = os.path.join(model_path, "images.bin")
        colmap_cameras = read_cameras_binary(fname_cameras)
        colmap_images = read_images_binary(fname_images)
    elif os.path.exists(os.path.join(model_path, "cameras.txt")):
        fname_cameras = os.path.join(model_path, "cameras.txt")
        fname_images = os.path.join(model_path, "images.txt")
        colmap_cameras = read_cameras_text(fname_cameras)
        colmap_images = read_images_text(fname_images)
    else:
        raise ValueError("Error! The model file does not exist at {0}".format(model_path))
    print("Reconstruction loaded. (n_images = {0})".format(len(colmap_images)))

    # read cameras
    cam_dict = {}
    for cam_id, colmap_cam in colmap_cameras.items():
        cam = _base.Camera(colmap_cam.model, colmap_cam.params, cam_id=cam_id, hw=[colmap_cam.height, colmap_cam.width])
        cam_dict[cam_id] = cam

    # read images
    n_images = len(colmap_images)
    camview_dict = {}
    for image_id, colmap_image in colmap_images.items():
        imname = colmap_image.name
        cam_id = colmap_image.camera_id
        camera = cam_dict[cam_id]
        pose = _base.CameraPose(colmap_image.qvec, colmap_image.tvec)
        view = _base.CameraView(camera, pose)
        camview_dict[imname] = view

    # map to the correct order
    imname_list, camviews = [], []
    for imname in image_names:
        imname_list.append(os.path.join(image_path, imname))
        view = camview_dict[imname]
        camviews.append(view)
    return imname_list, camviews

def ReadInfos(colmap_path, model_path="sparse", image_path="images", max_image_dim=None, check_undistorted=True):
    model = _pointsfm.SfmModel()
    model.ReadFromCOLMAP(colmap_path, model_path, image_path)
    return ReadInfosFromModel(model, colmap_path, model_path=model_path, image_path=image_path, max_image_dim=max_image_dim, check_undistorted=check_undistorted)


