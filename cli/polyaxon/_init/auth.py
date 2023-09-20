import time
import traceback

from polyaxon._client.impersonate import impersonate
from polyaxon.client import RunClient
from polyaxon.exceptions import PolyaxonClientException, PolyaxonContainerException


def create_auth_context():
    try:
        run_client = RunClient()
    except PolyaxonClientException as e:
        raise PolyaxonContainerException(e)

    retry = 0
    done = False
    exp = None
    while not done and retry <= 3:
        if retry:
            time.sleep(retry**2)
        try:
            impersonate(
                owner=run_client.owner,
                project=run_client.project,
                run_uuid=run_client.run_uuid,
                client=run_client.client,
            )
            print("Auth context initialized.")
            return
        except PolyaxonClientException as e:
            retry += 1
            print("Could not establish connection, retrying ...")
            exp = "Polyaxon auth initializer failed authenticating the operation: {}\n{}".format(
                repr(e), traceback.format_exc()
            )
    run_client.log_failed(reason="AuthContext", message=exp)
    raise PolyaxonContainerException("Init job did not succeed authenticating job.")
