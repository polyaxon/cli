from datetime import datetime
from typing import Dict, List, Optional

from polyaxon._compiler.resolver.runtime import BaseResolver
from polyaxon._flow import V1IO, V1CloningKind, V1CompiledOperation, V1Operation


def resolve(
    owner_name: str,
    project_name: str,
    project_uuid: str,
    run_name: str,
    run_uuid: str,
    run_path: str,
    compiled_operation: V1CompiledOperation,
    params: Optional[Dict[str, Dict]],
    run=None,
    resolver_cls=None,
    created_at: Optional[datetime] = None,
    compiled_at: Optional[datetime] = None,
    cloning_kind: V1CloningKind = None,
    original_uuid: Optional[str] = None,
    is_independent: bool = True,
):
    resolver_cls = resolver_cls or BaseResolver
    resolver_cls.is_valid(compiled_operation)

    resolver = resolver_cls(
        run=run,
        compiled_operation=compiled_operation,
        owner_name=owner_name,
        project_name=project_name,
        project_uuid=project_uuid,
        run_name=run_name,
        run_path=run_path,
        run_uuid=run_uuid,
        params=params,
        created_at=created_at,
        compiled_at=compiled_at,
        cloning_kind=cloning_kind,
        original_uuid=original_uuid,
        is_independent=is_independent,
    )
    if resolver:
        # If build section is present resolve the build
        if compiled_operation.build:
            return resolver, resolver.resolve_build()
        return resolver, resolver.resolve()


def resolve_hooks(
    owner_name: str,
    project_name: str,
    project_uuid: str,
    run_name: str,
    run_uuid: str,
    run_path: str,
    compiled_operation: V1CompiledOperation,
    params: Optional[Dict[str, Dict]],
    run=None,
    resolver_cls=None,
    created_at: Optional[datetime] = None,
    compiled_at: Optional[datetime] = None,
    cloning_kind: V1CloningKind = None,
    original_uuid: Optional[str] = None,
) -> List[V1Operation]:
    resolver_cls = resolver_cls or BaseResolver
    resolver_cls.is_valid(compiled_operation)

    if run:
        # Add outputs to compiled operation
        compiled_operation.outputs = [
            V1IO.construct(name=k, type=None, value=v, is_optional=True)
            for k, v in (run.outputs or {}).items()
        ]
    return resolver_cls(
        run=run,
        compiled_operation=compiled_operation,
        owner_name=owner_name,
        project_name=project_name,
        project_uuid=project_uuid,
        run_uuid=run_uuid,
        run_name=run_name,
        run_path=run_path,
        params=params,
        compiled_at=compiled_at,
        created_at=created_at,
        cloning_kind=cloning_kind,
        original_uuid=original_uuid,
        is_independent=False,
    ).resolve_hooks()
