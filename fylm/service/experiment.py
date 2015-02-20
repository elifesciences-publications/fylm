from fylm.model.experiment import Experiment as ExperimentModel
from fylm.service.errors import terminal_error
import logging
import os
import re
import nd2reader

log = logging.getLogger(__name__)


class Experiment(object):
    def __init__(self):
        self._os = os

    def get_experiment(self, experiment_start_date, base_dir, version):
        experiment = ExperimentModel()
        experiment.version = version

        # set start date
        experiment.start_date = experiment_start_date
        if not experiment.start_date.is_valid:
            terminal_error("Invalid start date: %s (use the format: YYMMDD)" % experiment_start_date)
        log.debug("Experiment start date: %s" % experiment.start_date.clean_date)

        # set the base directory
        if not self._os.path.isdir(base_dir):
            terminal_error("Base directory does not exist: %s" % base_dir)
        experiment.base_dir = base_dir
        log.debug("Experiment base directory: %s" % experiment.base_dir)

        # set the time_periods
        self._find_time_periods(experiment)
        self._build_directories(experiment)
        self._get_nd2_attributes(experiment)
        return experiment

    @staticmethod
    def add_time_period_to_log(experiment, time_period):
        with open(experiment.data_dir + "/experiment.txt", "w+") as f:
            f.write(str(time_period) + "\n")

    def _build_directories(self, experiment):
        """
        Creates all the directories needed for output files.

        Currently works for:
            1. rotation

        """
        # first make all the top-level directories
        subdirs = ["annotation",
                   "fluorescence",
                   "kymograph",
                   "location",
                   "puncta",
                   "registration",
                   "rotation",
                   "timestamp",
                   "movie",
                   "output",
                   "summary"]
        for subdir in subdirs:
            try:
                self._os.makedirs(experiment.data_dir + "/" + subdir)
            except OSError:
                pass

    def _find_time_periods(self, experiment):
        """
        Finds the time_periods of all available ND2 files associated with the experiment.

        """
        regex = re.compile(r"""FYLM-%s-0(?P<index>\d+)\.nd2""" % experiment.start_date.clean_date)
        found = False
        for filename in sorted(self._os.listdir(experiment.base_dir)):
            match = regex.match(filename)
            if match:
                found = True
                index = int(match.group("index"))
                log.debug("time_period: %s" % index)
                experiment.add_time_period(index)
        if not self._read_time_period_log(experiment) and not found:
            log.error("No ND2s available for this experiment!")

    @staticmethod
    def _read_time_period_log(experiment):
        found = False
        try:
            # opening in a+ mode will create the file if it doesn't exist, and we'll just get back no data
            with open(experiment.data_dir + "/experiment.txt", "a+") as f:
                data = f.read(-1)
        except OSError:
            log.debug("No experiment log file found. Perfectly normal.")
        else:
            for time_period in data.split("\n"):
                if time_period and int(time_period) > 0:
                    experiment.add_time_period(int(time_period.strip()))
                    found = True
        return found

    @staticmethod
    def _get_nd2_attributes(experiment):
        # grab the first nd2 file available
        for nd2_filename in experiment.nd2s:
            try:
                nd2 = nd2reader.Nd2(nd2_filename)
            except IOError:
                pass
            else:
                experiment.field_of_view_count = nd2.field_of_view_count
                break
        else:
            terminal_error("Could not get the field of view count. Maybe all the ND2s are missing?")

        return experiment.field_of_view_count is not None