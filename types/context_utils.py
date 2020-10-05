class ViewRegion():
    def __init__(self, region):
        self._width = region.width
        self._height = region.height

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

class ViewContext():

    def __init__(self, context):
        self._region_3d = context.space_data.region_3d
        self._view_rot = self._region_3d.view_rotation.copy()
        self._view_mat = self._region_3d.view_matrix.copy()
        self._pers_mat = self._region_3d.perspective_matrix.copy()

        self._view_pers = self._region_3d.view_perspective
        self._is_perspective = self._region_3d.is_perspective
        self._region = ViewRegion(context.region)

    @property
    def region(self):
        return self._region

    @property
    def region_3d(self):
        return self._region_3d

    @property
    def view_rotation(self):
        return self._view_rot

    @property
    def view_perspective(self):
        return self._view_pers

    @property
    def perspective_matrix(self):
        return self._pers_mat

    @property
    def view_matrix(self):
        return self._view_mat

    @property
    def is_perspective(self):
        return self._is_perspective