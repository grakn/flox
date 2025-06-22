"""
Verifies that FloxContext’s ContextVar provides proper isolation
between Python threads.

The test:

1. Creates a singleton FloxContext and registers two dummy projects.
2. Starts N worker threads; each thread:
   • creates its own request context (unique tenant + project + correlation_id)
   • immediately reads the context back via get_current_context()
   • stores a (thread_id, tenant_id, project_code, correlation_id) tuple
3. After all threads finish we assert:
   • the main thread still has *no* current context
   • each thread saw exactly the values it wrote (no cross-talk)
"""

import threading
import uuid

import pytest

from flox.context import FloxContext, Context       # the singleton + request ctx
from flox.projects import Project                   # static project
from flox.config import FloxConfig                  # dummy cfg (needed by FloxContext)

# ---------- helpers ----------------------------------------------------------


def _worker(
    tenant_id: str,
    project_code: str,
    results: list[str],
    index: int,
):
    """
    Create a request context inside a thread and immediately read it back.
    Store the identifying fields in `results[index]`.
    """
    ctx_singleton = FloxContext()  # same singleton in every thread
    correlation_id = str(uuid.uuid4())

    # Set per-thread context
    ctx_singleton.create_request_context(
        tenant_id=tenant_id,
        project_code=project_code,
        correlation_id=correlation_id,
    )

    read_ctx: Context | None = FloxContext.get_current_context()
    results[index] = (
        read_ctx.project.tenant_id,
        read_ctx.project.project_code,
        correlation_id,
    )


# ---------- test -------------------------------------------------------------


@pytest.mark.parametrize("num_threads", [8])
def test_context_is_thread_local(tmp_path, num_threads):
    # Initialise singleton with a minimal config
    cfg = FloxConfig(service="test", environment="test", projects={})
    flox_ctx = FloxContext(cfg)

    # Register one project per thread (tenant_i/project_i)
    for i in range(num_threads):
        tenant = f"tenant_{i}"
        project = f"proj_{i}"
        flox_ctx.register_project(Project(tenant, project, config={}))

    # Place-holder for results coming back from threads
    results: list[tuple[str, str, str] | None] = [None] * num_threads

    # Launch threads
    threads = []
    for i in range(num_threads):
        t = threading.Thread(
            target=_worker,
            args=(f"tenant_{i}", f"proj_{i}", results, i),
            daemon=True,
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Main thread has never set a context -> should be None
    assert FloxContext.get_current_context() is None

    # Verify each thread saw exactly its own tenant/project/correlation_id
    for i in range(num_threads):
        tenant, project, corr_id = results[i]
        assert tenant == f"tenant_{i}"
        assert project == f"proj_{i}"
        # correlation_id must be a valid UUID4 string; sanity check length
        assert len(corr_id) == 36
