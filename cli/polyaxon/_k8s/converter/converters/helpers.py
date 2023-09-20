from polyaxon._k8s.converter.converters.job import JobConverter
from polyaxon._k8s.converter.mixins import CleanerMixin, NotifierMixin, TunerMixin
from polyaxon._utils.fqn_utils import get_cleaner_instance, get_cleaner_resource_name


class NotifierConverter(NotifierMixin, JobConverter):
    pass


class TunerConverter(TunerMixin, JobConverter):
    pass


class CleanerConverter(CleanerMixin, JobConverter):
    def get_instance(self):
        return get_cleaner_instance(
            owner=self.owner_name, project=self.project_name, run_uuid=self.run_uuid
        )

    def get_resource_name(self):
        return get_cleaner_resource_name(self.run_uuid)
