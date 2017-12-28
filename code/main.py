# to run this code, install dicom_numpy, pydicom, natsort(on pip),skimage and mayavi

from skullFindSurface import *
from skullReconstruct import *
from skullNormalExtraction import *
from skimage.measure import compare_ssim as ssim
from skullFindFIducialLoya import *
import time
from skimage import filters
from mayavi import mlab
import copy
# from mpl_toolkits.mplot3d import Axes3D
# import matplotlib.pyplot as plt

ConstPixelSpacing = (1, 1, 1)


def main():
    global ConstPixelSpacing
    start_time = time.time()
    # change to required path to dicom folder
    PathDicom = "../../2016.06.27 PVC Skull Model/Sequential Scan/DICOM/PA1/ST1/SE2"

    data = readDicomData(PathDicom)
    print("---- %s seconds -----" % (time.time() - start_time))

    voxelData, ConstPixelSpacing = get3DRecon(data)
    voxelDataThresh = applyThreshold(copy.deepcopy(voxelData))

    print("---- %s seconds -----" % (time.time() - start_time))

    surfaceVoxels = getSurfaceVoxels(voxelDataThresh)
    surfaceVoxelCoord = surfaceVoxels * ConstPixelSpacing
    # only plotting 1/10th of points to speed up rendering
    # the points are represented as spheres hence skull surface may look bubbly
    print("---- %s seconds -----" % (time.time() - start_time))

    # findSurfaceNormals extracts surface normals and also extracts the voxels
    # on the outer edge of the skull
    # hence redefining surfaceVoxels and surfaceVoxelCoord
    surfaceVoxelCoord, normals = findSurfaceNormals(copy.deepcopy(
        surfaceVoxels), voxelData, ConstPixelSpacing)

    surfaceVoxels = surfaceVoxelCoord / ConstPixelSpacing

    # print normals.shape

    print("---- %s seconds -----" % (time.time() - start_time))

    # normals = np.squeeze(normals)
    # visualiseNormals(verts, normals, ConstPixelSpacing, res=100)
    # ------ uncomment this to view surface mesh ----------
    # vert, normals, faces = getSurfaceMesh(voxelData, ConstPixelSpacing)
    # mlab.triangular_mesh(vert[:, 0], vert[:, 1], vert[:, 2], faces)
    # print("---- %s seconds -----" % (time.time() - start_time))

    # i = 100  # decrease this to sample more points
    # point = np.array([104,337,127])
    # neighbor = getNeighborVoxel(surfaceVoxelCoord, point*ConstPixelSpacing, r=5.5)
    # neighbor = np.array(neighbor)
    # # print neighbor.shape
    # # print neighbor
    # patch = surfaceVoxelCoord[neighbor]
    point1 = np.array([104, 337, 127])
    point2 = np.array([150, 430, 91])
    patch, norm = extractFiducialModel(surfaceVoxelCoord, normals, point1)
    patch2,_,_ = genFiducialModel()
    # patch2, _ = extractFiducialModel(surfaceVoxelCoord, normals, point2)
    depthMap1 = genPHI(patch.copy())
    depthMap2 = genPHI(patch2.copy())
    filtered1 = filters.sobel(depthMap1)
    filtered2 = filters.sobel(depthMap2)

    plt.imshow(filtered1)
    plt.show()
    plt.imshow(filtered2)
    plt.show()
    # print ssim(filtered1, filtered2)
    # print norms

    mlab.points3d(patch2[:, 0], patch2[:, 1], patch2[:, 2])
    mlab.points3d(patch[:, 0], patch[:, 1], patch[:, 2], color=(1,0,0))
    mlab.quiver3d(0,0,0,0,0,1)
    # mlab.quiver3d(0,0,0,norm[0],norm[1],norm[2])
    # mlab.points3d(point[0]*ConstPixelSpacing[0],point[1]*ConstPixelSpacing[1],point[2]*ConstPixelSpacing[2], color=(1,0,0))

    # neighbor = getNeighborVoxel(vert, vert[::i], r=6)

    print("---- %s seconds -----" % (time.time() - start_time))

    # checkFiducial(surfaceVoxelCoord,
    #               surfaceVoxelCoord[::i], normals[::i], neighbor)
    # checkFiducial(vert, vert[::i], normals[::i], neighbor)

    # print("---- %s seconds -----" % (time.time() - start_time))
    # mlab.points3d(surfaceVoxelCoord[:, 0], surfaceVoxelCoord[:, 1],
    #               surfaceVoxelCoord[:, 2])
    # -----------------------------------------------------
    # mlab.show()
    # -------- uncomment this to view in matplotlib -----------
    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')
    # ax.scatter(surfaceVoxels[:, 0], surfaceVoxels[:, 1], surfaceVoxels[:, 2])
    # print(time.asctime(time.localtime(time.time())))
    # plt.show()
    mlab.show()


if __name__ == '__main__':
    main()
