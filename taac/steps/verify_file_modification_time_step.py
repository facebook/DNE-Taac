# pyre-unsafe

import typing as t

from taac.steps.step import Step
from taac.utils.file_verification_utils import (
    verify_file_modification_time,
)
from taac.test_as_a_config import types as taac_types


class VerifyFileModificationTimeStep(Step[taac_types.BaseInput]):
    STEP_NAME = taac_types.StepName.VERIFY_FILE_MODIFICATION_TIME_STEP
    OPERATING_SYSTEMS = ["EOS"]

    async def run(
        self, input: taac_types.BaseInput, params: t.Dict[str, t.Any]
    ) -> None:
        """
        Verify elapsed_time_since_modified on the device is greater than expected.

        Parameters:
        - file_path (str): Path to file to check modification time (required)
        - expected_last_mod_time (int): Expected modification time in seconds, this
          will do the check elapsed_time_since_modified >= expected_last_mod_time = pass
        """
        file_path = params["file_path"]
        expected_last_mod_time = params["expected_last_mod_time"]

        # Use shared utility function
        result = await verify_file_modification_time(
            driver=self.driver,
            file_path=file_path,
            expected_last_mod_time=expected_last_mod_time,
            logger=self.logger,
        )

        if not result.success:
            self.add_failure(result.message)

        self.raise_failure_if_exists()
