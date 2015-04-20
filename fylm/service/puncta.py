from fylm.model.location import LocationSet
from fylm.service.location import LocationSet as LocationService
from fylm.service.image_reader import ImageReader
from fylm.service.annotation import AnnotationSet as AnnotationSetService
from fylm.model.annotation import KymographAnnotationSet
from fylm.model.kymograph import KymographSet
from fylm.service.kymograph import KymographSet as KymographSetService
from fylm.service.base import BaseSetService
from fylm.service.utilities import timer
from fylm.model.constants import Constants
import logging
import trackpy as tp
import skimage.io

log = logging.getLogger(__name__)


class PunctaModel(object):
    def __init__(self):
        self._frames = []
        self.image_slice = None
        self.time_period = None
        self.field_of_view = None
        self.catch_channel_number = None
        self._timestamps = []

    def update_image(self, timestamp):
        self._frames.append(self.image_slice.image_data)
        self._timestamps.append(timestamp)

    @property
    def data(self):
        return self._frames


class PunctaSet(BaseSetService):
    """
    Creates a movie for each catch channel, with every zoom level and fluorescence channel in each frame.
    This works by iterating over the ND2, extracting the image of each channel for all dimensions, and saving
    a PNG file. When every frame has been extracted, we use mencoder to combine the still images into a movie
    and then delete the PNGs.

    The videos end up losing some information so this is mostly just for debugging and for help with annotating
    kymographs when weird things show up, as well as for figures, potentially.

    Previously we had some functionality that would add orange arrows to point out the cell pole positions if the
    annotations had been done. That was removed temporarily when this module was refactored but we intend to add it
    back in soon.

    """
    def __init__(self, experiment):
        super(PunctaSet, self).__init__()
        self._name = "puncta"
        self._experiment = experiment
        self._location_set = LocationSet(experiment)
        LocationService(self._experiment).load_existing_models(self._location_set)
        self._annotation_service = AnnotationSetService(experiment)
        self._annotation = KymographAnnotationSet(experiment)
        kymograph_service = KymographSetService(experiment)
        kymograph_set = KymographSet(experiment)
        kymograph_service.load_existing_models(kymograph_set)
        self._annotation.kymograph_set = kymograph_set

    def save(self, time_period, field_of_view, channel_number):
        """
        Analyzes puncta.

        """
        for location_model in self._location_set.existing:
            if location_model.field_of_view == field_of_view:
                image_slice = location_model.get_image_slice(channel_number)
                if location_model.get_channel_location(channel_number) and image_slice:
                    puncta = PunctaModel()
                    puncta.image_slice = image_slice
                    puncta.field_of_view = location_model.field_of_view
                    puncta.catch_channel_number = channel_number
                    break
        else:
            log.error("No data for that fov/channel!")
            exit()

        image_reader = ImageReader(self._experiment)
        image_reader.field_of_view = field_of_view
        image_reader.time_period = time_period

        for n, image_set in enumerate(image_reader):
            log.debug("FOV %s: %0.2f%%" % (image_reader.field_of_view, 100.0 * float(n) / float(len(image_reader))))
            self._update_image_data(puncta, image_set)
            if n > 5:
                break

        log.debug("\n\n******** TRACKPY TIME ***********\n\n")
        minintensity = 1.0
        ecc_upper_limit = 0.5
        minsize = 5
        test_frames = [int(n) for n in xrange(0, len(puncta.data), 2)]
        log.debug("test frames: %s" % test_frames)

        while True:
            for n, frame in enumerate(test_frames):
                image = puncta.data[frame]
                f = tp.locate(image, 15, 1.0)
                tp.annotate(f[(f['mass'] > minintensity) & (f['ecc'] < ecc_upper_limit) & (f['size'] > minsize)], image)

            done = raw_input("OK? Enter=no, anything else=yes: ")
            log.debug("done: %s" % done)
            if done:
                break
            minintensity = float(raw_input("min intensity (%s): " % minintensity) or minintensity)
            ecc_upper_limit = float(raw_input("ecc_upper_limit (%s): " % ecc_upper_limit) or ecc_upper_limit)
            minsize = int(raw_input("min diameter (%s): " % minsize) or minsize)

        batch = tp.batch(puncta.data, minsize, minintensity)
        for item in batch.iteritems():
            print(item[(item['mass'] > minintensity) & (item['ecc'] < ecc_upper_limit) & (item['size'] > minsize)])


    @staticmethod
    def _update_image_data(puncta, image_set):
        image = image_set.get_image("GFP", 1)
        if image is not None:
            puncta.image_slice.set_image(image)
            puncta.update_image(image_set.timestamp)