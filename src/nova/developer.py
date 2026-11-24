"""Developer-domain public interface.

Project inspection is implemented as a read-only action in nova.execution.
Code editing, test execution and Git mutations are deliberately not enabled
until dedicated approval-bound adapters are implemented.
"""
from nova.architecture import Domain


DOMAIN = Domain.DEVELOPER
SUPPORTED_COMMANDS = ("inspect project <directory>",)
PLANNED_COMMANDS = ("explain project <directory>", "run tests <directory>", "prepare code change <request>")
