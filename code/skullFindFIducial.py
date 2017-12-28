import numpy as np
from scipy.spatial import cKDTree, distance
from skimage import measure
from sklearn.neighbors import NearestNeighbors
from mayavi import mlab
import matplotlib.pyplot as plt
from skullReconstruct import *

vFiducial = np.array([])
fFiducial = np.array([])
ConstPixelSpacing = (1, 1, 1)


# def rotatePC(vert, normal, theta, phi):
#     rotationMatrix = np.array([[[np.cos(t) * np.cos(p), np.cos(t) * np.sin(p), np.sin(t)],
#                                 [-np.sin(p), np.cos(p), 0],
#                                 [-np.sin(t) * np.cos(p), -np.sin(t) * np.sin(p), np.cos(t)]]
#                                for p, t in zip(phi, theta)], dtype=np.float64)

#     # print rot[0:2]
#     rotatedPatches = np.array([np.matmul(rot, v.T).T for rot,
#                                v in zip(rotationMatrix, vert)])
#     # rotated_normal = np.matmul(rot, normal.T)
#     return rotatedPatches

def apply_affine(A, init_pose):
    m = A.shape[1]
    src = np.ones((m + 1, A.shape[0]))
    src[:m, :] = np.copy(A.T)
    if init_pose is not None:
        src = np.dot(init_pose, src)
    return src[:m, :].T

def find_init_transfo(evec1, evec2):
    e_cross = np.cross(evec1, evec2)
    e_cross1 = e_cross[0]
    e_cross2 = e_cross[1]
    e_cross3 = e_cross[2]
    i = np.identity(3)
    v = np.zeros((3, 3))
    v[1, 0] = e_cross3
    v[2, 0] = -e_cross2
    v[0, 1] = -e_cross3
    v[2, 1] = e_cross1
    v[0, 2] = e_cross2
    v[1, 2] = -e_cross1
    v2 = np.dot(v, v)
    c = np.dot(evec1, evec2)
    # will not work in case angle of rotation is exactly 180 degrees
    R = i + v + (v2 / (1 + c))
    T = np.identity(4)
    T[0:3, 0:3] = R
    T = np.transpose(T)
    R = np.transpose(R)
    #com = [img.resolution[0]*len(img)/2,img.resolution[1]*len(img[0])/2,img.resolution[2]*len(img[0][0])/2]
    [tx, ty, tz] = [0, 0, 0]
    T[0, 3] = tx
    T[1, 3] = ty
    T[2, 3] = tz
    return T

def getNeighborVoxel(pointCloud, points, r):
    kdt = cKDTree(pointCloud)
    neighbor = kdt.query_ball_point(points, r)
    return neighbor

# function to compare point clouds u and v


# def comparePC(u, v):
#     # dist = max(distance.directed_hausdorff(u, v)[0],
#     #            distance.directed_hausdorff(v, u)[0])
#     nbrs = NearestNeighbors(n_neighbors=1, algorithm='kd_tree').fit(v)
#     distances, _ = nbrs.kneighbors(u)
#     cost = np.matmul(distances.T, distances)
#     return cost


def genPHI(patch, size=15):
    res = 1
    size *= res
    if size % 2 == 0:
        size += 1

    center = np.uint8(size / 2)
    patch += (center, center, 0)
    depthMap = np.ones((size, size)) * (-100)

    for i in range(patch.shape[0]):
        depthMap[np.uint8(patch[i, 0] * res), np.uint8(patch[i, 1] * res)] = max(
            (depthMap[np.uint8(patch[i, 0] * res), np.uint8(patch[i, 1] * res)]), (patch[i, 2]))
    depthMap[depthMap == (-100)] = 0
    
    return depthMap

def checkFiducial(pointCloud, poi, normals, neighbor):
    global vFiducial, fFiducial
    start_time = time.time()

    patches = np.array([pointCloud[lst] for lst in neighbor])
    # all patches are translated to origin(or normalised) by subtracting
    # the coordinate of point around which the patch is taken
    normPatches = np.array([patches[i] - poi[i] for i in range(len(poi))])

    if vFiducial.size == 0:
        vFiducial = genFiducialModel(pointCloud, normals)

    """
    phi = np.arctan(normals[:, 1] / normals[:, 0])
    theta = np.arctan(
        np.sqrt(normals[:, 0]**2 + normals[:, 1]**2) / normals[:, 2])
    theta[theta < 0] += np.pi

    alignedPatches = rotatePC(normPatches.copy(), normals.copy(), theta, phi)

    """
    print("---- %s seconds -----" % (time.time() - start_time))

    alignedPatches = []
    for i in range(len(poi)):
        affine_T = find_init_transfo(normals[i], np.array([0, 0, 1]))
        alignedPatches.append(np.array(apply_affine(normPatches[i], affine_T)))
    alignedPatches = np.array(alignedPatches)

    print("---- %s seconds -----" % (time.time() - start_time))

    cost = []

    for i in range(len(poi)):
        if(i % 20 == 0):
            print("ICP: "),
            print(i)
        if(len(alignedPatches[i]) > 50):
            cost.append(
                icp(alignedPatches[i], vFiducial, max_iterations=10)[1])

    print("END OF ICP")

    cost_sorted = np.sort(cost)
    print(cost_sorted)
    print("")
    print("")

    print (str(cost_sorted[0]) + " " + str(cost_sorted[1]) + " " + str(
        cost_sorted[2]) + " " + str(cost_sorted[3]) + " " + str(cost_sorted[4]))

    colormap = np.random.rand(10, 3)
    for i in range(10):
        patch = patches[cost.index(cost_sorted[i])]
        mlab.points3d(patch[:, 0], patch[:, 1], patch[:, 2], color=colormap[i])

    mlab.points3d(pointCloud[::10, 0], pointCloud[::10, 1],
                  pointCloud[::10, 2], color=(1, 0, 0))
    # mlab.quiver3d(0, 0, 0, 0, 0, 1)
    # mlab.quiver3d(0, 0, 0, norm[0], norm[1], norm[2], color=(0, 1, 0))
    mlab.show()


# def checkFiducial(pointCloud, poi, normals, neighbor):
#     global vFiducial, fFiducial

#     patches = np.array([pointCloud[lst] for lst in neighbor])
#     # all patches are translated to origin(or normalised) by subtracting
#     # the coordinate of point around which the patch is taken
#     normPatches = np.array([patches[i] - poi[i] for i in range(len(poi))])

#     if vFiducial.size == 0:
#         vFiducial, fFiducial, _ = genFiducialModel()

#     phi = np.arctan(normals[:, 1] / normals[:, 0])
#     theta = np.arctan(
#         np.sqrt(normals[:, 0]**2 + normals[:, 1]**2) / normals[:, 2])
#     theta[theta < 0] += np.pi

#     alignedPatches = rotatePC(normPatches.copy(), normals.copy(), theta, phi)

#     # cost = np.array([comparePC(vFiducial, alignedPatches[i])
#     #                  for i in range(len(poi))])

#     # i = np.argmin(cost)
#     i=0

#     # print cost[i]

#     patch = alignedPatches[i]
#     print patch.shape

#     # plotting the patch giving minimum cost
#     # mlab.triangular_mesh(
#     #     vFiducial[:, 0], vFiducial[:, 1], vFiducial[:, 2], fFiducial)
#     # mlab.points3d(patch[:, 0],
#     #               patch[:, 1], patch[:, 2])
#     # # mlab.quiver3d(0, 0, 0, 0, 0, 1)
#     # # mlab.quiver3d(0, 0, 0, norm[0], norm[1], norm[2], color=(0, 1, 0))
#     # mlab.show()
